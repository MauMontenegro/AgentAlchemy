from langgraph.graph import START,END,StateGraph
from src.schemas.schemas import ScraperAgentState
from src.nodes.scrap_news_node import (
    scrap_article,summarize_article,comparative_articles,select_summary_type
)

class ScrapAgent():
    def __init__(self):
        self.state = ScraperAgentState   
        self.graph = self._build_graph()      
    
    def _build_graph(self):
        # Init Agent Graph
        workflow= StateGraph(self.state)        

        # Add Nodes to Graph
        workflow.add_node("scrap",scrap_article)
        workflow.add_node("summarize",summarize_article)
        workflow.add_node("comparative",comparative_articles)

        workflow.add_edge(START,"scrap")
        workflow.add_conditional_edges("scrap",select_summary_type)       
        workflow.add_edge("summarize",END)
        workflow.add_edge("comparative",END)

        return workflow.compile()
    
