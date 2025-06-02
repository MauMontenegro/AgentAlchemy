from langgraph.graph import START,END,StateGraph
from src.schemas.schemas import AgentState
from src.nodes.research_nodes import (
    generate_rss_feed_url,    
    retrieve_articles_metadata,
    retrieve_articles_text,
    select_top_urls,
    summarize_articles_parallel,
    format_results,
    articles_text_decision,
    extract_topics_bias,
    state_of_art
)

class ResearchAgent():
    def __init__(self):
        self.state = AgentState   
        self.graph = self._build_graph()      
    
    def _build_graph(self):
        # Init Agent Graph
        workflow= StateGraph(self.state)        

        # Add Nodes to Graph
        #workflow.add_node("generate_params",generate_newsapi_params)
        workflow.add_node("generate_params",generate_rss_feed_url)
        workflow.add_node("fetch_metadata",retrieve_articles_metadata)
        workflow.add_node("articles_text",retrieve_articles_text)
        workflow.add_node("top_urls",select_top_urls)
        workflow.add_node("summarize",summarize_articles_parallel)
        workflow.add_node("format",format_results)
        workflow.add_node("analysis",extract_topics_bias)
        workflow.add_node("stateofart",state_of_art)
        
        # Flow of the graph       
        workflow.add_edge(START,"generate_params")
        workflow.add_edge("generate_params","fetch_metadata")
        workflow.add_edge("fetch_metadata","articles_text")
        workflow.add_conditional_edges(
            "articles_text",
            articles_text_decision,
            {
                "generate_newsapi_params": "generate_params",
                "select_top_urls":"top_urls",
                "END": END
            }          
        )
        workflow.add_edge("top_urls","summarize")
        workflow.add_edge("summarize","analysis")
        workflow.add_edge("analysis","stateofart")
        workflow.add_edge("stateofart","format")
        workflow.add_edge("format",END)

        return workflow.compile()
    
