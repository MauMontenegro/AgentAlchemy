from fastapi import APIRouter
from src.schemas.schemas import AgentRequest,AgentResponse
from src.agents.research import ResearchAgent

router= APIRouter()

def create_initial_state(query:str,num_articles:int,source:list[str]=None,country:list[str]=[""],language:list[str]=[""],mode:str="simple"):
    """
    Generates an initial state
    """    
    num_searches_remaining = 1
       
    state={
        "news_query": query,
        "languages":language or ["es"],
        "countries":country or ["MX"],
        "sources":source or [],
        "num_articles_tldr": num_articles,
        "urls":[],
        
        "num_searches_remaining": num_searches_remaining,
        "newsapi_params": {},
        "past_searches": [],
        "articles_metadata": [],
        "scraped_urls": [],        
        "potential_articles": [],
        "tldr_articles": [],
        "formatted_results": "No articles with text found.", 
        "report":"",
        "mode": mode      
    }
    return state

@router.post("/agent",response_model=AgentResponse)
async def agent_call(request:AgentRequest):
    agent = ResearchAgent()
    print(request.source)
    state = create_initial_state(request.query,request.articles,request.source,request.country,request.language,request.mode)
    final_state = await agent.graph.ainvoke(state)

    if not final_state.get("tldr_articles"):
        return AgentResponse(
            header="No articles found",
            summaries=[],
            report="No state of the art"
        )
    
    return final_state["formatted_results"]
