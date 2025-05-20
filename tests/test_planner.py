from src.nodes.planner_node import build_model
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

def test_model_availability():
    """
    Test Model availability
    """
    messages=[
        ("system","Eres un asistente de traducción. Traduce la oración del usuario en inglés a idioma Español."),
        ("human","I love programming.")
    ]
    planner = build_model()
    result = planner.invoke(messages)
    assert result.content.lower().split() == ["me","encanta","programar."]

def test_react_agent_conversation():
    """
    Test ReAct agent conversation capability without adding tools.
    """
    system_prompt = "Eres un asistente de traducción. Traduce la oración del usuario en inglés a idioma Español."
    human_prompt= {"messages":[{"role":"user","content":"I love programming."}]}
    planner = build_planner(system=system_prompt)
    result = planner.invoke(human_prompt)    
    assert "encanta" in result["messages"][-1].content.lower().split()

def test_react_agent_tool_calling():
    """
    Tes ReAct capability to call tools(counting letters tool).
    """
    human_prompt = {
        "messages": [{"role": "user", "content": "¿Cuántas letras tiene la palabra programación?"}]
    }
     
    @tool
    def fake_lenght_tool(input:str)->str:
        "Regresa la  longitud del texto ingresado"
        return str(len(input))
    
    tools =[fake_lenght_tool]
    planner = build_planner(system="Eres un asistente que puede usar herramientas.",tools=tools)

    result = planner.invoke(human_prompt)
    output = result["messages"][-1].content.lower()    
    assert "12" in output or "doce" in output, f"Expected length output in result: {output}"

def test_react_agent_tool_tavily():
    from src.tools.search_tool import tavily_web_search
    human_prompt = {
        "messages": [{"role": "user", "content": "Quiero las noticias más relevantes respecto a la guerra en Ucrania"}]
    }
    tools=[tavily_web_search]
    planner = build_planner(system="Eres un asistente de investigación que puede usar herramientas.",tools=tools)
    result = planner.invoke(human_prompt)
    output = result["messages"][-1].content.lower()
    print(output)
    assert isinstance(result,str)  
   


