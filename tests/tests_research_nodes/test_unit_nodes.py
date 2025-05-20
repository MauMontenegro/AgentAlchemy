import pytest
from src.nodes.research_nodes import generate_newsapi_params,retrieve_articles_metadata,retrieve_articles_text,select_top_urls,summarize_articles_parallel,format_results
from src.schemas.schemas import AgentState

@pytest.fixture
def create_initial_state():
    """
    Generates an initial empty state
    """
    query = "Juegos basados por turnos"
    num_searches_remaining = 1
    num_articles_tldr = 3    
    state={
        "news_query": query,
        "num_searches_remaining": num_searches_remaining,
        "newsapi_params": {},
        "past_searches": [],
        "articles_metadata": [],
        "scraped_urls": [],
        "num_articles_tldr": num_articles_tldr,
        "potential_articles": [],
        "tldr_articles": [],
        "formatted_results": "No articles with text found."
    }

    return state

def test_newsapi_params_output(create_initial_state):
    """Test the parameters generation for the newsapi"""
    state = create_initial_state
    result_state = generate_newsapi_params(state)   

    assert isinstance(result_state,dict)
    assert state["newsapi_params"] != None

def test_newsapi_retrieve_articles(create_initial_state):
    """Test the retrieval of articles by the newsapi api"""
    state = create_initial_state
    result_state = generate_newsapi_params(state)
    result_state = retrieve_articles_metadata(result_state)
   
    assert len(result_state["articles_metadata"]) > 0 

def test_scrap_articles(create_initial_state):
    """Test the existence of scrapped articles"""
    state = create_initial_state
    result_state = generate_newsapi_params(state)
    result_state = retrieve_articles_metadata(result_state)
    result_state = retrieve_articles_text(result_state)    

    assert result_state["potential_articles"] != None

def test_select_top_articles(create_initial_state):
    state = create_initial_state
    result_state = generate_newsapi_params(state)
    result_state = retrieve_articles_metadata(result_state)
    result_state = retrieve_articles_text(result_state)
    result_state = select_top_urls(result_state)
    
    assert result_state["tldr_articles"] != None

def test_formated_news(create_initial_state):
    state = create_initial_state
    result_state = generate_newsapi_params(state)
    result_state = retrieve_articles_metadata(result_state)
    result_state = retrieve_articles_text(result_state)
    result_state = select_top_urls(result_state)
    result_state = summarize_articles_parallel(result_state)
    result_state = format_results(result_state)

    print(result_state["formatted_results"])

    assert result_state["formatted_results"] != None