from fastapi import APIRouter,Depends
from src.schemas.schemas import ScrapAgentRequest, ScrapAgentResponse
from src.agents.scrap import ScrapAgent
from src.routers.auth_route import get_current_user
from src.models.models import User

router= APIRouter()

def create_initial_state(urls:list):
    """
    Generates an initial state
    """       
    state={
       "url":urls,
       "title":"",
       "text":[],
       "summary":"",
    }

    return state

@router.post("/scrap",response_model=ScrapAgentResponse)
async def agent_scrap_call(request:ScrapAgentRequest,current_user:User=Depends(get_current_user)):
    
    state=create_initial_state(urls=request.urls)
    agent = ScrapAgent()
    final_state = await agent.graph.ainvoke(state)

    return {"summary":final_state["summary"]}