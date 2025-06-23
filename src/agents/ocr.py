from langgraph.graph import START,END,StateGraph
from src.schemas.schemas import OcrAgentState
from src.nodes.ocr_nodes import (
    ocr_step,
    build_pydantic_schema,
)

class OcrAgent():
    def __init__(self):
        self.state = OcrAgentState   
        self.graph = self._build_graph()      
    
    def _build_graph(self):
        # Init Agent Graph
        workflow= StateGraph(self.state)        

        # Add Nodes to Graph       
        workflow.add_node("ocr",ocr_step)
        workflow.add_node("build_schema",build_pydantic_schema)       
        
        # Flow of the graph       
        workflow.add_edge(START,"ocr")
        workflow.add_edge("ocr","build_schema") 
        workflow.add_edge("build_schema",END)
        return workflow.compile()