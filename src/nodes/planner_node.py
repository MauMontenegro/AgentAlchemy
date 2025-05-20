import os
from dotenv import load_dotenv

from langchain_aws import ChatBedrockConverse
from src.schemas.schemas import AgentState

load_dotenv()

def build_model():
    """
    Build llm model based on user configuration
    """
    model = os.getenv("REASONING_MODEL")
    llm = ChatBedrockConverse(model=model,temperature=0)
    return llm

from src.tools.search_tool import tavily_web_search
def research_node(state:AgentState):
    llm=build_model()
    tools = [tavily_web_search]
    llm_with_tools = llm.bind_tools(tools)

    result = llm_with_tools.invoke(state["messages"])
    print(result)
    return {"messages":[result]}
    

