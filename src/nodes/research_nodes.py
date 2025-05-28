import os
import re
from datetime import datetime
import requests

from dateutil import parser

from dotenv import load_dotenv

from bs4 import BeautifulSoup
from newsapi import NewsApiClient
from langchain_aws import ChatBedrockConverse
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from src.schemas.schemas import AgentState,NewsApiParams,ArticleAnalysis

load_dotenv()

def generate_newsapi_params(state: AgentState) -> AgentState:
    """Generate Newsapi parameters based on the query string"""

    # Instantiate LLM model
    model = os.getenv("REASONING_MODEL")
    llm = ChatBedrockConverse(model=model,temperature=0)    

    # Define the structure of the LLM output
    newsapi_parser = JsonOutputParser(pydantic_object=NewsApiParams)

    today_date = datetime.now().strftime("%Y-%m-%d")

    # Retrieve the list of past search params
    past_searches = state["past_searches"]

    # Retrieve the number of searches remaining
    num_searches_remaining = state["num_searches_remaining"]

    # Retrieve the users query
    news_query = state["news_query"]

    template = """
    Today is {today_date}.

    Create a param dict for the News API based on the user query:
    {query}

    These searches have already been made. Loosen the search terms to get more results.
    {past_searches}
    
    Following these formatting instructions:
    {format_instructions}

    Including this one, you have {num_searches_remaining} searches remaining.
    If this is your last search, use all news sources and a 30 days search range.
    """

    # Create a prompt template to create the newsapi parameters
    prompt_template = PromptTemplate(
        template=template,
        variables={"today":today_date,"query":news_query,"past_searches":past_searches,"num_searches_remaining":num_searches_remaining},
        partial_variables={"format_instructions":newsapi_parser.get_format_instructions()}
    )

    # Create the prompt chain
    chain = prompt_template | llm | newsapi_parser

    result = chain.invoke({"query": news_query, "today_date": today_date, "past_searches": past_searches, "num_searches_remaining": num_searches_remaining})

    # update the state
    state["newsapi_params"] = result

    return state



def retrieve_articles_metadata(state:AgentState)->AgentState:
    """Use the NewsApi parameters to make the API call"""

    newsapi_params = state["newsapi_params"]
    state['num_searches_remaining'] -=1

    try:
        # Create Newsapi client object
        newsapi = NewsApiClient(api_key=os.getenv("NEWSAPI_API_KEY"))

        articles = newsapi.get_everything(**newsapi_params)
        
        state["past_searches"].append(newsapi_params)

        scraped_urls = state["scraped_urls"]

        new_articles = []
        for article in articles["articles"]:
            if article["url"] not in scraped_urls and len(state["potential_articles"]) + len(new_articles) <= state["num_articles_tldr"]:
                new_articles.append(article)               

        state["articles_metadata"] = new_articles

    except Exception as e:
        print(f"Error: {e}")
    
    return state

def retrieve_articles_text(state:AgentState) -> AgentState:
    """Scrapper to retrieve article text"""

    articles_metadata = state["articles_metadata"]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    }

    potential_articles = []

    for article in articles_metadata:        
        url = article['url']
        date = article['publishedAt']

        # use beautiful soup to extract the article content
        # TODO: Agregar un exception si la request no se realizó exitosamente
        response = requests.get(url, headers=headers,timeout=60)
        
        # check if the request was successful
        if response.status_code == 200:
            # parse the HTML content
            soup = BeautifulSoup(response.content, 'html.parser')

            # find the article content
            text = soup.get_text(strip=True)

            # append article dict to list
            potential_articles.append({"title": article["title"], "url": url, "description": article["description"], "text": text,"date":date})

            # append the url to the processed urls
            state["scraped_urls"].append(url)

    # append the processed articles to the state
    state["potential_articles"].extend(potential_articles)

    return state

def select_top_urls(state:AgentState) -> AgentState:
    """Based on article texts, choose the top-k articles to summarize"""

    # Instantiate LLM model
    model = os.getenv("REASONING_MODEL")    
    llm = ChatBedrockConverse(model=model,temperature=0)   

    news_query = state["news_query"]

    num_articles_tldr = state["num_articles_tldr"]

    potential_articles = state["potential_articles"]

    formatted_metadata = "\n".join([f"{article['url']}\n{article['description']}\n" for article in potential_articles])

    prompt = f"""
    Based on the user news query:
    {news_query}

    Reply with a list of strings of up to {num_articles_tldr} relevant urls.
    Don't add any urls that are not relevant or aren't listed specifically.
    {formatted_metadata}
    """

    result = llm.invoke(prompt).content

    # TODO: Mejorar pattern matching con librerias
    url_pattern = r'(https?://[^\s",]+)'

    urls = re.findall(url_pattern, result)

    tldr_articles = [article for article in potential_articles if article['url'] in urls]   

    state["tldr_articles"] = tldr_articles

    return state

def summarize_articles_parallel(state:AgentState)-> AgentState:
    """Summarize the articles based on full text in parallel."""
    tldr_articles = state["tldr_articles"]
    model = os.getenv("REASONING_MODEL")    
    llm = ChatBedrockConverse(model=model,temperature=0)
    prompt = """
    Create a * bulleted summarizing tldr for the article:
    {text}

    Follow this exact format:
    {title}
    {url}
    * tl;dr bulleted summary
    * use bullet points for each sentence
    """

    # iterate over the selected articles and collect summaries synchronously
    for i,_ in enumerate(tldr_articles):
        text = tldr_articles[i]["text"]
        title = tldr_articles[i]["title"]
        url = tldr_articles[i]["url"]
        
        # invoke the llm synchronously
        result = llm.invoke(prompt.format(title=title, url=url, text=text))
        tldr_articles[i]["summary"] = result.content

    state["tldr_articles"] = tldr_articles

    return state

def extract_topics_bias(state:AgentState)->AgentState:
    """Extract the main topics of the news and political bias."""

    tldr_articles = state["tldr_articles"]
    model = os.getenv("REASONING_MODEL")
    llm = ChatBedrockConverse(model=model,temperature=0)    
    analysis_parser = JsonOutputParser(pydantic_object=ArticleAnalysis)

    template = """
    You are a political media analysis assistant. Your task is to analyze the following news article to:

    1. Identify the main topics or entities discussed.
    2. Detect if the article presents any political bias.
    3. Explain the reasoning behind the detected bias.
    4. Determine if the article is written as humor, parody, or satire.

    ### Use the following checklist to detect bias:
    - Is the article heavily opinionated or one-sided?
    - Does it rely on unsupported or unsubstantiated claims?
    - Does it present cherry-picked facts that support only one outcome?
    - Does it disguise opinions as facts?
    - Does it use extreme or emotionally charged language?
    - Does it attempt to persuade without factual evidence?
    - Is the author anonymous or lacks subject-matter expertise?
    - Is the article written as humor, parody, or satire?
    - Is it promotional in disguise?

    If the article is clearly written as humor, parody, or satire, classify the bias as `"humor"`.

    You must return a param dict object with the following formatting:
    {format_instructions}

    News Article:
    {text}

    """
    # iterate over the selected articles and extract topics and bias
    for i,_ in enumerate(tldr_articles):
      
        prompt_template = PromptTemplate(
        template=template,
        variables={"text":tldr_articles[i]["text"]},
        partial_variables={"format_instructions":analysis_parser.get_format_instructions()}
        )

        chain = prompt_template | llm | analysis_parser
        
        result = chain.invoke({"text":tldr_articles[i]["text"]})
        tldr_articles[i]["topics"] = result["topics"]
        tldr_articles[i]["bias"] = result["bias"]
        tldr_articles[i]["bias_explanation"] = result["bias_explanation"]
    
    state["tldr_articles"] = tldr_articles

    print("New function testing")
    print(tldr_articles)
    return state

def format_results(state: AgentState) -> AgentState:
    """Format the results for display."""
    # load a list of past search queries
    past_queries = [newsapi["q"] for newsapi in state["past_searches"]]
    tldr_articles = state["tldr_articles"]

    formatted_summaries = []
    for article in tldr_articles:
        lines = article["summary"].strip().split("\n")
        title = lines[0]
        url = lines[1]
        date = article.get('date','missing')
        bullets = [line.strip("* ").strip() for line in lines[2:] if line.startswith("*")]

        formatted_summaries.append({
            "title": title,
            "url": url,
            "bullets": bullets,
            "date": parser.parse(date),
            "topics":article.get('topics'),
            "bias": article.get('bias'),
            "bias_explanation":article.get('bias_explanation'),
        })

    state["formatted_results"] = {
        "header": f"Top {len(tldr_articles)} articulo(s) encontrados para los siguientes términos de búsqueda: {', '.join(past_queries)}",
        "summaries": formatted_summaries,
    }

    return state

# Decision Edges
def articles_text_decision(state: AgentState) -> str:
    """Check results of retrieve_articles_text to determine next step."""
    if state["num_searches_remaining"] == 0:
        # if no articles with text were found return END
        if len(state["potential_articles"]) == 0:
            state["formatted_results"] = "No articles with text found."
            return "END"
        # if some articles were found, move on to selecting the top urls
        else:
            return "select_top_urls"
    else:
        # if the number of articles found is less than the number of articles to summarize, continue searching
        if len(state["potential_articles"]) < state["num_articles_tldr"]:
            return "generate_newsapi_params"
        # otherwise move on to selecting the top urls
        else:
            return "select_top_urls"