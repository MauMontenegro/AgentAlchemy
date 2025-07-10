import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from src.schemas.schemas import AgentRequest, AgentResponse
from src.agents.research import ResearchAgent
from src.routers.auth_route import get_current_user, oauth2_scheme
from src.models.models import User

# Configure logging
logger = logging.getLogger(__name__)

# Create router with appropriate responses
router = APIRouter(
    responses={404: {"description": "Not found"}}
)

def create_initial_state(
    query: str,
    num_articles: int,
    source: Optional[List[str]] = None,
    country: Optional[List[str]] = None,
    language: Optional[List[str]] = None,
    mode: str = "simple"
) -> Dict[str, Any]:
    """
    Generates an initial state for the news agent.
    
    Args:
        query: Search query for news articles
        num_articles: Number of articles to retrieve and summarize
        source: Optional list of news sources to filter by
        country: Optional list of countries to filter news by
        language: Optional list of languages to filter news by
        mode: Agent operation mode ('simple' or 'advanced')
        
    Returns:
        Dictionary containing the initial state for the news agent
    """    
    num_searches_remaining = 2
    max_feed_entries = 10
       
    state = {
        "news_query": query,
        "languages": language or ["es"],
        "countries": country or ["MX"],
        "sources": source or [],
        "num_articles_tldr": num_articles,
        "urls": [],        
        "num_searches_remaining": num_searches_remaining,
        "newsapi_params": {},
        "past_searches": [],
        "articles_metadata": [],
        "scraped_urls": [],
        "max_feed_entries":max_feed_entries,        
        "potential_articles": [],
        "tldr_articles": [],
        "formatted_results": "No articles with text found.", 
        "report": "",
        "mode": mode      
    }
    return state

@router.post("/agent", response_model=AgentResponse, summary="Process news search request")
async def agent_call(request: AgentRequest, current_user: User = Depends(get_current_user)):
    """
    Process a news search request and return summarized articles.
    
    Args:
        request: The news search request parameters
        current_user: The authenticated user (injected by dependency)
        
    Returns:
        Formatted results with article summaries
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        # Validate user is authenticated
        if not current_user:
            logger.error("Authentication failed: No user provided")
            raise HTTPException(status_code=401, detail="Authentication required")
            
        logger.info(f"Processing news request for query: {request.query} by user: {current_user.username}")
        agent = ResearchAgent()
        
        state = create_initial_state(
            request.query,
            request.articles,
            request.source,
            request.country,
            request.language,
            request.mode
        )
        
        final_state = await agent.graph.ainvoke(state)

        if not final_state.get("tldr_articles"):            
            logger.warning(f"No articles found for query: {request.query}")
            return AgentResponse(
                header="No articles found",
                summaries=[],
                report="No state of the art"
            )
        
        logger.info(f"Successfully processed news request for query: {request.query}")
        
        # Make sure we return the correct format expected by AgentResponse
        if isinstance(final_state["formatted_results"], dict) and all(key in final_state["formatted_results"] for key in ["header", "summaries", "report"]):
            return final_state["formatted_results"]
        else:
            # If formatted_results is not already in the correct format, create a proper AgentResponse
            return AgentResponse(
                header=f"Results for: {request.query}",
                summaries=final_state.get("tldr_articles", []),
                report=final_state.get("report", "")
            )
    except HTTPException as he:
        # Re-raise HTTP exceptions without modification
        logger.error(f"HTTP error in news request: {str(he)}")
        raise
    except Exception as e:
        logger.error(f"Error processing news request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.post("/agent-test", response_model=AgentResponse, summary="Test endpoint for news search without authentication")
async def agent_call_test(request: AgentRequest):
    """
    Test endpoint for processing a news search request without authentication.
    Use this for testing when authentication issues occur.
    
    Args:
        request: The news search request parameters
        
    Returns:
        Formatted results with article summaries
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        logger.info(f"Processing test news request for query: {request.query}")
        agent = ResearchAgent()
        
        state = create_initial_state(
            request.query,
            request.articles,
            request.source,
            request.country,
            request.language,
            request.mode
        )
        
        final_state = await agent.graph.ainvoke(state)

        if not final_state.get("tldr_articles"):            
            logger.warning(f"No articles found for query: {request.query}")
            return AgentResponse(
                header="No articles found",
                summaries=[],
                report="No state of the art"
            )
        
        logger.info(f"Successfully processed test news request for query: {request.query}")
        
        # Make sure we return the correct format expected by AgentResponse
        if isinstance(final_state["formatted_results"], dict) and all(key in final_state["formatted_results"] for key in ["header", "summaries", "report"]):
            return final_state["formatted_results"]
        else:
            # If formatted_results is not already in the correct format, create a proper AgentResponse
            return AgentResponse(
                header=f"Results for: {request.query}",
                summaries=final_state.get("tldr_articles", []),
                report=final_state.get("report", "")
            )
    except Exception as e:
        logger.error(f"Error processing test news request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

