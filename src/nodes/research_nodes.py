import os
import multiprocessing
import re
import logging
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

from src.schemas.schemas import AgentState,ArticleAnalysis,ArticleBulletSummary

# Configure logging to display on console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

load_dotenv()

def generate_rss_feed_url(state: AgentState)-> AgentState:
    """Generate RSS feed URLs based on the user's query and source preferences."""    
    try:
        query = state.get("news_query", "")
        if not query:
            logging.error("Missing required news_query in state")
            state["urls"] = []
            return state
            
        country = state.get("countries", ["MX"])
        if not country:
            logging.warning("No country specified, defaulting to MX")
            country = ["MX"]
            
        sources = state.get("sources", [])
        
        # Search news in $country$ with "es" prefered language. RSS get news based on country language first.
        base_url = "https://news.google.com/rss/search?q={query}&gl={country}&ceid={country}:es"    
        urls_by_source = []
    except Exception as e:
        logging.error(f"Error preparing RSS feed parameters: {str(e)}")
        state["urls"] = []
        return state
    if sources:        
        for source in sources:
            query_with_source = f'{query} site:{source}'
            encoded_query = quote_plus(query_with_source)
            url = base_url.format(query=encoded_query,country=country[0])
            urls_by_source.append(url)
    else:            
        encoded_query = quote_plus(query)        
        url = base_url.format(query=encoded_query,country=country[0])
        urls_by_source.append(url)   

    state["urls"] = urls_by_source    
    return state

def retrieve_articles_metadata(state: AgentState) -> AgentState:
    """Retrieve metadata for each url feed created"""
    # Function entry logging
    logging.info("Starting article metadata retrieval")
    
    try:
        # Validate input state
        if not state.get("urls"):
            logging.warning("No URLs provided for metadata retrieval")
            state["articles_metadata"] = []
            return state
            
        urls = state["urls"]
        logging.info(f"Processing {len(urls)} RSS feed URLs")
        
        max_feed_articles = state.get("max_feed_entries")
        all_articles = []
        total_processed = 0
        total_new = 0
        
        for url_index, url in enumerate(urls):
            try:
                logging.debug(f"Parsing feed {url_index+1}/{len(urls)}: {url}")
                feed = feedparser.parse(url)
                
                # Check if parsing was successful
                if feed.get('bozo_exception'):
                    logging.warning(f"Error parsing feed at {url}: {feed.bozo_exception}")
                    continue
                    
                # Check if feed has entries
                if not feed.entries:
                    logging.info(f"No entries found in feed at {url}")
                    continue
                
                logging.debug(f"Found {len(feed.entries)} entries in feed")                
                 
                total_processed += len(feed.entries[len(state["past_searches"]):max_feed_articles+len(state["past_searches"])])
                    
                # Filter entries not already in past_searches. If its a retry move index + 10
                new_entries = [entry for entry in feed.entries[len(state["past_searches"]):max_feed_articles+len(state["past_searches"])] 
                              if entry.link not in state["past_searches"]]
                
                if not new_entries:
                    logging.debug(f"No new entries found in feed at {url}")
                    continue
                    
                logging.debug(f"Found {len(new_entries)} new entries in feed")
                total_new += len(new_entries)
            except Exception as e:
                logging.error(f"Exception while processing feed at {url}: {str(e)}", exc_info=True)
                continue
            
            # Create metadata for all new entries at once
            new_metadata = [
                {
                    "title": getattr(entry, "title", ""),
                    "link": getattr(entry, "link", ""),
                    "pubDate": datetime(*entry.published_parsed[:6]).isoformat() 
                              if getattr(entry, "published_parsed", None) else "",
                    "description": clean_description(getattr(entry, "description", ""))
                }
                for entry in new_entries
            ]
            
            # Update past_searches in batch
            state["past_searches"].extend([entry.link for entry in new_entries])
            
            # Add all new metadata at once
            all_articles.extend(new_metadata)
       
        # Log summary of results
        state["articles_metadata"] = all_articles
        logging.info(f"Article metadata retrieval complete: processed {total_processed} entries, found {len(all_articles)} new articles")
        
        return state
        
    except Exception as e:
        logging.error(f"Unexpected error in retrieve_articles_metadata: {str(e)}", exc_info=True)
        # Ensure we always return a valid state
        if "articles_metadata" not in state:
            state["articles_metadata"] = []
        return state

# Compile the regex pattern once at module level
HTML_TAG_PATTERN = re.compile('<.*?>')

def clean_description(raw_html):    
    cleantext = re.sub(HTML_TAG_PATTERN, '', raw_html)
    return cleantext

def retrieve_articles_text(state: AgentState) -> AgentState:
    """
    Retrieve full text content for article metadata using parallel processing.
    
    Args:
        state: The current agent state containing articles_metadata
        
    Returns:
        Updated agent state with retrieved article content
    """
    logging.info(f"Starting to retrieve text for {len(state['articles_metadata'])} articles")    
    
    # Get concurrency from environment variable or calculate based on CPU cores
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS",
    min(32, multiprocessing.cpu_count() * 4)  # Default: 4x CPU cores, max 32
    ))
    
    articles_metadata = state["articles_metadata"]
    retrieved_articles = []
    retrieved_urls = []
    
    # Process articles in parallel
    futures = []
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        # Submit tasks and collect futures
        futures = [executor.submit(scrape_article, article) for article in articles_metadata]
        
    # Process results
    success_count = 0
    failure_count = 0
    for future in futures:
        try:
            # Get result, handling any exceptions that occurred during execution
            article_data, url = future.result(timeout=10)  # 10 second timeout for retrieving results
            if article_data:
                retrieved_articles.append(article_data)
                retrieved_urls.append(url)
                success_count += 1
            else:
                failure_count += 1
        except Exception as e:
            logging.error(f"Error processing article: {str(e)}")
            failure_count += 1    
            
    # Log results
    logging.info(f"Article retrieval complete: {success_count} successful, {failure_count} failed")
    
    # Update state
    state["potential_articles"].extend(retrieved_articles)
    logging.info(f"State updated: {len(retrieved_articles)} new articles added")
    state["scraped_urls"].extend(retrieved_urls)
    state["max_feed_entries"]= state["num_articles_tldr"] - len(state["potential_articles"])
    logging.info
    state["num_searches_remaining"] -= 1
    
    logging.info(f"State updated: {len(retrieved_articles)} new articles added, {state['num_searches_remaining']} searches remaining")
    
    return state

# Function That will be distributed among threads
def scrape_article(article):
    try:
        HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'}
        real_url = gnewsdecoder(article['link'])["decoded_url"]
        response = requests.get(real_url, headers=HEADERS, timeout=20)

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

def sanitize_prompt_input(text):
    """Sanitize text to prevent prompt injection attacks."""
    if text is None:
        return ""
    # Remove control characters and normalize whitespace
    sanitized = re.sub(r'[\r\n\t]+', ' ', str(text))
    # Additional sanitization could be added here
    return sanitized

def select_top_urls(state:AgentState) -> AgentState:
    """Based on article texts, choose the top-k articles to summarize"""   
    
    model = os.getenv("REASONING_MODEL")
    if not model:
        logging.error("REASONING_MODEL environment variable not set")
        return state        
    try:
        llm = ChatBedrockConverse(model=model, temperature=0)       
        news_query = state.get("news_query", "")
        news_query = sanitize_prompt_input(news_query) 
        num_articles_tldr = state.get("num_articles_tldr", 3)  # Default to 3 if not specified
        potential_articles = state.get("potential_articles", [])
        
        if not potential_articles:
            logging.warning("No potential articles available for selection")
            state["tldr_articles"] = []
            return state
            
        # Sanitize each article description and URL before joining
        sanitized_metadata = []
        for article in potential_articles:
            safe_url = sanitize_prompt_input(article.get('url', ''))
            safe_description = sanitize_prompt_input(article.get('description', ''))
            sanitized_metadata.append(f"{safe_url}\n{safe_description}")
            
        formatted_metadata = "\n".join(sanitized_metadata)
        
        # Use a template with clear separation between instructions and user input
        prompt = f"""
        Based on the user news query:
        <query>
        {news_query}
        </query>

        Reply with a list of strings of up to {num_articles_tldr} relevant urls.
        Don't add any urls that are not relevant or aren't listed specifically.
        Add only valid urls.
        
        <article_metadata>
        {formatted_metadata}
        </article_metadata>
        """
        
        result = llm.invoke(prompt).content
        
        # Extract URLs from the result
        url_pattern = r'(https?://[^\s",]+)'
        urls = re.findall(url_pattern, result)
        
        if not urls:
            logging.warning("No URLs found in LLM response or not relevant urls found")
            
        # Filter articles that match the extracted URLs
        tldr_articles = [article for article in potential_articles 
                        if article.get('url', '') in urls]
        
        if not tldr_articles:
            logging.warning("No articles matched the selected URLs")
            
        # Update state
        state["tldr_articles"] = tldr_articles
        logging.info(f"Selected {len(tldr_articles)} articles for summarization")
        
    except Exception as e:
        logging.error(f"Error in select_top_urls: {e}")
        # Ensure tldr_articles exists even if there's an error
        if "tldr_articles" not in state:
            state["tldr_articles"] = []
    
    return state


def summarize_articles_parallel(state:AgentState)-> AgentState:
    """Summarize the articles based on full text in parallel."""
    
    tldr_articles = state["tldr_articles"]
    model = os.getenv("REASONING_MODEL")    
    llm = ChatBedrockConverse(model=model,temperature=0)
    bullet_parser = JsonOutputParser(pydantic_object=ArticleBulletSummary)
    language = state["languages"][0]

    template = """
    Create a * bulleted summarizing tldr for the article using {language} language. Translate if it is neccesary.

    Article:
    {text}
    
    This is the title of the new:{title}
    This is the url of the new:{url}

    You must return a param dict object with the following formatting:
    {format_instructions}

    Each * bullet must be in a new line
    """
    
    # Iterate over the selected articles and collect summaries synchronously
    for i,_ in enumerate(tldr_articles):
        text = tldr_articles[i]["text"]
        title = tldr_articles[i]["title"]
        url = tldr_articles[i]["url"]
        
        # invoke the llm synchronously
        prompt_template = PromptTemplate(
            template=template,
            input_variables=["text", "language","title","url"],
            partial_variables={"format_instructions": bullet_parser.get_format_instructions()}
        )
        chain = prompt_template | llm | bullet_parser
        
        try:
            # Pass both text and language when invoking
            result = chain.invoke({
                "text": text,
                "language": language,
                "title": title,
                "url": url
            })
            tldr_articles[i]["summary"] = result
        except Exception as e:
            logging.error(f"Error summarizing article {i} ({title}): {e}")
            # Provide a fallback summary
            tldr_articles[i]["summary"] = {
                "title": title,
                "url": url,
                "bullet_summary": "* Unable to generate summary due to an error."
            }
        
    state["tldr_articles"] = tldr_articles
    
    return state

def extract_topics_bias(state: AgentState) -> AgentState:
    """
    Extract the main topics and analyze political bias of news articles.
    
    Args:
        state: Agent state containing articles to analyze
        
    Returns:
        Updated state with topic and bias analysis
        
    Raises:
        ValueError: If required configuration or articles are missing
    """
    # Validate required state
    if not state.get("tldr_articles"):
        logging.warning("No articles available for analysis")
        return state

    # Get configuration with validation
    model = os.getenv("REASONING_MODEL")
    if not model:
        logging.error("REASONING_MODEL environment variable not set")
        return state
     
    # Initialize analysis components
    try:
        llm = ChatBedrockConverse(model=model, temperature=0)
        analysis_parser = JsonOutputParser(pydantic_object=ArticleAnalysis)
        language = state.get("languages", ["en"])[0]  # Default to English if not specified
        tldr_articles=state["tldr_articles"]
    except Exception as e:
        logging.error(f"Failed to initialize analysis components: {e}")
        return state
   
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
    
    # Iterate over the selected articles and extract topics and bias
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
        
        try:
            # Safely access result dictionary keys with get() method
            tldr_articles[i]["topics"] = result.get("topics", [])
            tldr_articles[i]["bias"] = result.get("bias", "unknown")
            tldr_articles[i]["bias_explanation"] = result.get("bias_explanation", "No explanation available")
        except (KeyError, TypeError, IndexError) as e:
            logging.error(f"Error updating article {i} with analysis results: {e}")
            # Set default values if an error occurs
            tldr_articles[i]["topics"] = []
            tldr_articles[i]["bias"] = "error"
            tldr_articles[i]["bias_explanation"] = f"Error during analysis: {str(e)}"

   
    state["tldr_articles"] = tldr_articles
    
    return state

def state_of_art(state: AgentState) -> AgentState:
    """Generate a state-of-the-art report based on analyzed articles."""
    
    tldr_articles = state.get("tldr_articles", [])
    query = state.get("news_query", "")
    mode = state.get("mode", "simple")
    
    if mode == "advanced" and tldr_articles:
        try:
            # Get configuration
            model = os.getenv("REASONING_MODEL")
            language = state.get("languages", ["en"])[0]
            
            # Build articles block using list comprehension and join
            article_blocks = []
            for i, art in enumerate(tldr_articles, 1):
                article_block = f"""Artículo {i}:
                Título: {art.get('title', 'No title')}
                Tendencia política: {art.get('bias', 'Unknown')}
                Contenido: {art.get('text', 'No content')}
                ---"""
                article_blocks.append(article_block)
            
            articles_text = "\n".join(article_blocks)
            
            # Create LLM instance
            llm = ChatBedrockConverse(model=model, temperature=0)
            
            # Use a separate template variable for better readability
            report_template = f"""
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
            {articles_text}
            """
            
            # Generate report
            result = llm.invoke(report_template).content
            logging.info(f"Generated state-of-art report with {len(tldr_articles)} articles")
        except Exception as e:
            logging.error(f"Error generating state-of-art report: {e}")
            result = f"Error generating report: {str(e)}"
    else:
        # Use language-appropriate message
        language = state.get("languages", ["en"])[0]
        if language.lower().startswith("es"):
            result = "No se genera un estado del arte en el modo simple."
        else:
            result = "State-of-art report is not generated in simple mode."

    state["report"] = result
    return state


def format_results(state: AgentState) -> AgentState:
    """Format the results for display."""
    # load a list of past search queries
    past_queries = state["news_query"]
    tldr_articles = state["tldr_articles"]    
    formatted_summaries = []
    for article in tldr_articles:
              
        lines = article["summary"]["bullet_summary"].strip().split("\n")
        
        title = article["summary"]["title"]
        url = article["summary"]["url"]
        date = article.get('date','missing')         
        bullets = [line.strip("* ").strip() for line in lines if line.startswith("*")]
        
        formatted_summaries.append({
            "title": title,
            "url": url,
            "bullets": bullets,
            "date": parser.parse(date),
            "topics":article.get('topics'),
            "bias": article.get('bias'),
            "bias_explanation":article.get('bias_explanation'),
        })
    
    # Sort formatted_summaries by date in descending order (newest first)
    formatted_summaries.sort(key=lambda x: x["date"], reverse=True)

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
        if len(state["scraped_urls"]) == 0:
            state["formatted_results"] = "No articles with text found."
            return "END"        
        else:
            return "enough_articles"
    else:       
        if len(state["scraped_urls"]) < state["num_articles_tldr"]:
            return "not_enough_articles"        
        else:
            return "enough_articles"