from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.table import Table

from langchain_core.messages import HumanMessage,SystemMessage

from src.agents.research import ResearchAgent
from src.tools.search_tool import tavily_web_search

console = Console()

def main():
    console.print("[bold magenta]🔎 Intelligent Research Agent[/bold magenta]")
    topic = Prompt.ask("¿Qué vamos a investigar hoy?")    
    
    system_prompt = """
    Eres un agente inteligente. Usa siempre las herramientas disponibles cuando la información no esté en tu contexto.
    Si el usuario pide información sobre eventos actuales, como noticias o estado actual de algo, usa la herramienta `tavily_web_search`.
    No inventes información actual. No respondas tú si puedes usar una herramienta.
    """
    
    agent = ResearchAgent().get()
    
    console.print("\n[italic]📡 Recopilando información, espera un momento...[/italic]\n")
    messages=[
        SystemMessage(content=system_prompt),
        HumanMessage(content=topic),
    ]    
    result = agent.invoke({"messages":messages})
    
    response =result["messages"][-1].content

    print(response)   

if __name__ == "__main__":
    main()
