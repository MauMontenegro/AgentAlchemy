from dotenv import load_dotenv

from src.tools.search_tool import tavily_web_search

load_dotenv()

def test_tavily_search_returns_results():
    """
        Test Tavily API web search tool by asserting a correct format response
        and answer.        
    """
    query= "Cuál es la Capital de Argentina"
    result = tavily_web_search.invoke(query)   
    # Tavily returns a list of dicts with "content" and url keys
    assert isinstance(result,dict)
    assert "results" in result
    assert isinstance(result["results"],list)
    assert len(result["results"]) > 0
    
    # Ensures every result contains content and a url
    first_result = result["results"][0]
    assert "content" in first_result
    assert "url" in first_result

    # Search the correct answer in the content
    contents = [res["content"] for res in result["results"]]
    assert any("Buenos Aires" in content for content in contents)
