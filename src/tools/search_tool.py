from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from langchain_core.tools import tool

load_dotenv()

@tool
def tavily_web_search(query):
    """
    Usa esta herramienta para buscar noticias recientes en internet.    
    """
    tavily_tool = TavilySearch(
        max_results=3,
        topic="news",        
        chunks_per_source=3,
        days=7,        
    )
    results = tavily_tool.invoke({"query":query})      
    return results

@tool
def newsapi_web_search(query):
    """
    Usa esta herramienta para buscar noticias recientes en internet.  
    """