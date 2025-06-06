import os
import re
from datetime import datetime
import requests
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote_plus

from dateutil import parser

from dotenv import load_dotenv

import feedparser

from googlenewsdecoder import gnewsdecoder

from bs4 import BeautifulSoup

from langchain_aws import ChatBedrockConverse
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from src.schemas.schemas import AgentState,ArticleAnalysis

load_dotenv()

def generate_rss_feed_url(state: AgentState)->AgentState:
    """Generate RSS feed URLs based on the user's query and source preferences."""
    
    query = state["news_query"]   
    country = state["countries"]
    sources = state["sources"]

    base_url = "https://news.google.com/rss/search?q={query}&gl={country}&ceid={country}:es"
    
    # Generate the RSS feed URL
    urls_by_source = []    
    if sources:        
        for source in sources:
            query_with_source = f' site:{source}'
            encoded_query = quote_plus(query_with_source)
            url = base_url.format(query=encoded_query,country=country[0])
            urls_by_source.append(url)
    else:            
        encoded_query = quote_plus(query)        
        url = base_url.format(query=encoded_query,country=country[0])
        urls_by_source.append(url)   

    state["urls"] = urls_by_source    
    return state

def clean_description(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def retrieve_articles_metadata(state:AgentState)-> AgentState:
    """Retrieve metadata for each url feed created"""

    urls = state["urls"]
    max_feed_articles = 10

    articles = []
    # Traverse trough different feeds    
    for url in urls:      
        feed = feedparser.parse(url)        
        for entry in feed.entries[:max_feed_articles]:
            if entry.link in state["past_searches"]:
                continue
            state["past_searches"].append(entry.link)
            
            metadata = {
                "title": getattr(entry, "title", ""),
                "link": getattr(entry, "link", ""),
                "pubDate": datetime(*entry.published_parsed[:6]).isoformat() if getattr(entry, "published_parsed", None) else "",
                "description": clean_description(getattr(entry, "description", ""))
            }    
                 
            articles.append(metadata)
   
    state["articles_metadata"] = articles   
    
    return state

# Function That will be distributed among threads
def scrape_article(article):
    try:
        HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'}
        real_url = gnewsdecoder(article['link'])["decoded_url"]
        response = requests.get(real_url, headers=HEADERS, timeout=15)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'lxml')  # Uses lxml parser
            text = soup.get_text(strip=True)

            return {
                "title": article["title"],
                "url": real_url,
                "description": article["description"],
                "text": text,
                "date": article["pubDate"]
            }, real_url
    except Exception as e:
        print(f"Error fetching {article['link']}: {e}")
    
    return None, None

def retrieve_articles_text(state: AgentState) -> AgentState:
    articles_metadata = state["articles_metadata"]
    potential_articles = []
    scraped_urls = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(scrape_article, articles_metadata)

    for article_data, url in results:
        if article_data:
            potential_articles.append(article_data)
            scraped_urls.append(url)

    state["potential_articles"].extend(potential_articles)
    state["scraped_urls"].extend(scraped_urls)
    return state

def select_top_urls(state:AgentState) -> AgentState:
    """Based on article texts, choose the top-k articles to summarize"""
    print("Selecting Top Urls")
    # Instantiate LLM model
    model = os.getenv("REASONING_MODEL")    
    llm = ChatBedrockConverse(model=model,temperature=0)   

    news_query = state["news_query"]

    num_articles_tldr = state["num_articles_tldr"]

    potential_articles = state["potential_articles"]

    formatted_metadata = "\n".join([f"{article['url']}\n{article['description']}\n" for article in potential_articles])
    print(formatted_metadata)

    prompt = f"""
    Based on the user news query:
    {news_query}

    Reply with a list of strings of up to {num_articles_tldr} relevant urls.
    Don't add any urls that are not relevant or aren't listed specifically.
    {formatted_metadata}
    """

    result = llm.invoke(prompt).content
    print(result)
    # TODO: Mejorar pattern matching con librerias
    url_pattern = r'(https?://[^\s",]+)'

    urls = re.findall(url_pattern, result)

    tldr_articles = [article for article in potential_articles if article['url'] in urls]   

    print(urls)

    state["tldr_articles"] = tldr_articles   

    return state

def summarize_articles_parallel(state:AgentState)-> AgentState:
    """Summarize the articles based on full text in parallel."""
    tldr_articles = state["tldr_articles"]
    model = os.getenv("REASONING_MODEL")    
    llm = ChatBedrockConverse(model=model,temperature=0)
    language = state["languages"][0]

    prompt = """
    Create a * bulleted summarizing tldr for the article only in {language} language:
    {text}

    Follow this exact format:
    {title}
    {url}
    * tl;dr bulleted summary
    * use bullet points for each sentence
    """
    

    # Iterate over the selected articles and collect summaries synchronously
    for i,_ in enumerate(tldr_articles):
        text = tldr_articles[i]["text"]
        title = tldr_articles[i]["title"]
        url = tldr_articles[i]["url"]
        
        
        # invoke the llm synchronously
        result = llm.invoke(prompt.format(title=title, url=url, text=text,language=language))
        tldr_articles[i]["summary"] = result.content

    state["tldr_articles"] = tldr_articles

    return state

def extract_topics_bias(state:AgentState)->AgentState:
    """Extract the main topics of the news and political bias."""
    tldr_articles = state["tldr_articles"]
    model = os.getenv("REASONING_MODEL")
    llm = ChatBedrockConverse(model=model,temperature=0)    
    analysis_parser = JsonOutputParser(pydantic_object=ArticleAnalysis)
    language = state["languages"][0]
    
    template = """
    You are a political media analysis assistant. Your task is to analyze the following news article to:
    1. Identify the main topics or entities discussed.
    2. Detect if the article presents any political bias.
    3. Explain the reasoning behind the detected bias in {language} language.
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
    for i, _ in enumerate(tldr_articles):
        prompt_template = PromptTemplate(
            template=template,
            input_variables=["text", "language"],  # Changed from 'variables' to 'input_variables'
            partial_variables={"format_instructions": analysis_parser.get_format_instructions()}
        )
        chain = prompt_template | llm | analysis_parser
        
        # Pass both text and language when invoking
        result = chain.invoke({
            "text": tldr_articles[i]["text"],
            "language": language
        })
        
        tldr_articles[i]["topics"] = result["topics"]
        tldr_articles[i]["bias"] = result["bias"]
        tldr_articles[i]["bias_explanation"] = result["bias_explanation"]
   
    state["tldr_articles"] = tldr_articles
   
    return state

def state_of_art(state:AgentState)->AgentState:
    """Make a State of the art based on the topic and reviewed news"""
    
    tldr_articles = state["tldr_articles"]
    query = state["news_query"]

    if state["mode"]=="advanced":
        model = os.getenv("REASONING_MODEL")
        llm = ChatBedrockConverse(model=model,temperature=0)   
        language = state["languages"][0]
        bloque_articulos =""

        for i, art in enumerate(tldr_articles, 1):
            bloque_articulos += f"""Artículo {i}:
            Título: {art['title']}
            Tendencia política: {art['bias']}
            Contenido: {art['text']}
            ---
            """

        prompt = f"""
        Eres un analista experto en medios de comunicación y actualidad global. Tu tarea es redactar un informe de contexto en idioma {language},basado en un conjunto de noticias recuperados de la web al buscar la siguiente consulta.

        Consulta:
        {query}

        Recibirás un conjunto de noticias relevantes que abordan distintas perspectivas y hechos recientes relacionados con el tema en cuestión. A partir de estas noticias, deberás redactar un informe completo y objetivo que incluya:

        1. **Panorama Actual**: Describe el estado actual del tema, incluyendo hechos clave, eventos recientes, actores involucrados, y opiniones predominantes.

        2. **Tendencias o posibles escenarios futuros**: Menciona las tendencias que se vislumbran, predicciones basadas en el comportamiento reciente, posibles cambios sociales, económicos, políticos o tecnológicos relacionados con el tema.

        3. **Debates, controversias o polarización**: Si hay posturas encontradas, políticas enfrentadas o conflictos en la narrativa, describe las posiciones principales.

        4. **Conclusión final**: Resume el estado general del tema, su importancia y las posibles implicancias a futuro.

        Debes redactar con un tono periodístico, profesional y accesible para un lector general. No repitas el contenido textual de las noticias, sino sintetiza y analiza la información.Incluye siempre
        información de cada artículo. Además brinda las referencias necesarias de los artículos de donde tomes la información utilizando el número del artículo encerrado entre corchetes. Dame el informe en formato Markdown.

        Noticias:
        {bloque_articulos}

        """
        result = llm.invoke(prompt).content
    else:
        result="No se genera un estado del arte en el modo simple."

    state["report"] = result
    
    return state

def format_results(state: AgentState) -> AgentState:
    """Format the results for display."""
    # load a list of past search queries
    past_queries = state["news_query"]
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
        "header": f"Top {len(tldr_articles)} articulo(s) encontrados para los siguientes términos de búsqueda: {(past_queries)}",
        "summaries": formatted_summaries,
        "report":state["report"]
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