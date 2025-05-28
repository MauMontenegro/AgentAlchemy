from fastapi import APIRouter
from src.schemas.schemas import AgentRequest,AgentResponse
from src.agents.research import ResearchAgent

router= APIRouter()

def create_initial_state(query:str,num_articles:int):
    """
    Generates an initial state
    """    
    num_searches_remaining = 1
       
    state={
        "news_query": query,
        "num_searches_remaining": num_searches_remaining,
        "newsapi_params": {},
        "past_searches": [],
        "articles_metadata": [],
        "scraped_urls": [],
        "num_articles_tldr": num_articles,
        "potential_articles": [],
        "tldr_articles": [],
        "formatted_results": "No articles with text found.",       
    }
    return state

@router.post("/agent",response_model=AgentResponse)
async def agent_call(request:AgentRequest):
    agent = ResearchAgent()
    state = create_initial_state(request.query,request.articles)
    final_state = await agent.graph.ainvoke(state)

    return final_state["formatted_results"]
