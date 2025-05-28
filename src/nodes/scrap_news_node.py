import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from langchain_aws import ChatBedrockConverse
from langchain_core.prompts import PromptTemplate
from src.schemas.schemas import ScraperAgentState

load_dotenv()

def scrap_article(state:ScraperAgentState):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    }

    urls = state["url"]    
    for url in urls:
        try:        
            response = requests.get(url, headers=headers, timeout=60)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract title
                title_tag = soup.find('title')
                title = title_tag.get_text(strip=True) if title_tag else "No title found"

                # Try to find main content in article or similar tags
                article = soup.find('article')
                if article:
                    content = article.get_text(separator='\n', strip=True)
                else:
                    # Fallback: use main or body content heuristically
                    paragraphs = soup.find_all('p')
                    content = '\n'.join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50)

                state["text"].append(content)                

                state["title"] = title             
               
            else:
                return {"error": f"Request failed with status code {response.status_code}"}
            
        except Exception as e:
            return {"error": str(e)}
    return state
        
def summarize_article(state:ScraperAgentState)->ScraperAgentState:    
    # Instantiate LLM model
    model = os.getenv("REASONING_MODEL")
    llm = ChatBedrockConverse(model=model,temperature=0)   
    
    template = """   
    A continuación se te proporciona un artículo y su título. Tu tarea es analizarlo críticamente y 
    devolver la información en formato Markdown.
    Identifica y lista los puntos más relevantes del artículo en formato de viñetas (-), destacando hechos,
    afirmaciones clave o datos relevantes.

    Redacta un resumen conciso que explique el contenido general del artículo.

    Elabora una opinión crítica sobre el artículo. Esto puede incluir:

        - Fortalezas y debilidades en la argumentación.

        - Sesgos o limitaciones en la información presentada.

        - Coherencia y claridad del texto.

        - Implicaciones del contenido (sociales, políticas, científicas, etc.).

    Usa el siguiente formato Markdown para estructurar tu respuesta:

    ## Puntos Relevantes
    - [Punto importante 1]
    - [Punto importante 2]
    - ...

    ## Opinión Crítica
    [Evaluación crítica del artículo con observaciones claras, argumentadas y bien redactadas]

    Título del Artículo: {title}
    Artículo:{text}
    """

    prompt_template = PromptTemplate(
        template=template,
        variables={"title":state["title"],"text":state["text"]}        
    )

    chain = prompt_template | llm 

    result = chain.invoke({"title":state["title"],"text":state["text"]})

    state["summary"] = result.content

    return state

def select_summary_type(state:ScraperAgentState):
    if len(state["text"])>1 and len(state["text"])<=2:
        return "comparative"
    else:
        return "summarize"

def comparative_articles(state:ScraperAgentState)->ScraperAgentState:

    # Instantiate LLM model
    model = os.getenv("REASONING_MODEL")
    llm = ChatBedrockConverse(model=model,temperature=0)   

    template = """
    A continuación se presentan dos documentos de diferentes fuentes. Tu tarea es:

    Leer ambos textos con atención.

    Compararlos y contrastarlos, identificando similitudes, diferencias, enfoques complementarios o contrapuestos.

    Elaborar un resumen conjunto que:

        Condense las ideas principales de ambos documentos.

        Señale claramente de cuál documento proviene cada parte del resumen (usa etiquetas como [Fuente A] o [Fuente B]).

        Destaque cualquier punto en el que ambos documentos estén de acuerdo o en desacuerdo.

    Documento A:
    {text_1}

    Documento B:
    {text_2}

    Formato de salida esperado:

    Resumen Comparativo:
    [Resumen claro y estructurado, incluyendo referencias entre corchetes como [Fuente A] o [Fuente B]]

    Similitudes:

        [Punto en común] ([Fuente A] y [Fuente B])

    Diferencias o Contrastes:

        [Punto de diferencia] ([Fuente A] vs. [Fuente B])
    """

    prompt_template = PromptTemplate(
        template=template,
        variables={"text_1":state["text"][0],"text_2":state["text"][1]}        
    )

    chain = prompt_template | llm 

    result = chain.invoke({"text_1":state["text"][0],"text_2":state["text"][1]})

    state["summary"] = result.content

    return state
