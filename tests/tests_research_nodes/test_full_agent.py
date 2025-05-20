import pytest

from src.agents.research import ResearchAgent

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

@pytest.mark.asyncio
async def test_full_research_agent(create_initial_state):
    research_agent = ResearchAgent()
    state = create_initial_state
    result = await research_agent.graph.ainvoke(state)
    print(result["formatted_results"]["summaries"][0])
    assert result["formatted_results"] != None
    