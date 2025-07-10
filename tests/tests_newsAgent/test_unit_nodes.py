from datetime import datetime
from types import SimpleNamespace

import pytest
import re

from unittest.mock import patch,Mock,MagicMock

from src.nodes.research_nodes import generate_rss_feed_url,retrieve_articles_metadata,retrieve_articles_text,select_top_urls
from src.schemas.schemas import AgentState

@pytest.fixture
def create_initial_state():
    """
    Generates an initial empty state of the agent graph
    """
    query = "Juegos basados por turnos"
    num_searches_remaining = 1
    num_articles_tldr = 3    
    state={
        "news_query": query,
        "languages":["es"],
        "countries":["MX"],
        "sources":[],
        "num_articles_tldr": num_articles_tldr,
        "urls":[],
        
        "num_searches_remaining": num_searches_remaining,
        "newsapi_params": {},
        "past_searches": [],
        "articles_metadata": [],
        "scraped_urls": [],        
        "potential_articles": [],
        "tldr_articles": [],
        "formatted_results": "No articles with text found.", 
        "report":"",
        "mode": 'simple'      
    }

    return state

def test_rss_url_no_sources(create_initial_state):
    state = create_initial_state
    updated_state = generate_rss_feed_url(state)

    assert "urls" in updated_state
    assert len(updated_state["urls"])==1
    assert "Juegos+basados+por+turnos" in updated_state["urls"][0]
    assert "&gl=MX&ceid=MX:es" in updated_state["urls"][0]

def test_rss_url_with_sources(create_initial_state):
    state = create_initial_state
    state["sources"] = ["ign.com", "pcgamer.com"]
    updated_state = generate_rss_feed_url(state)

    assert len(updated_state["urls"]) == 2
    assert "site%3Aign.com" in updated_state["urls"][0]
    assert "site%3Apcgamer.com" in updated_state["urls"][1]


# Test retrieve articles metadata
@pytest.fixture
def rss_state(create_initial_state):
    create_initial_state["urls"] = ["https://example.com/fake_rss"]
    return create_initial_state

def clean_description(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

@patch("src.nodes.research_nodes.feedparser.parse")
def test_retrieve_articles_metadata(mock_parse, rss_state):
    # Set max_feed_entries in the test state
    rss_state["max_feed_entries"] = 10
    rss_state["past_searches"] = []  # Ensure past_searches is empty

    # Create a mock feed entry
    fixed_datetime = datetime(2024, 6, 5, 15, 0, 0)
    mock_entry = SimpleNamespace(
        title="Test Title",
        link="https://example.com/article1",
        published_parsed = fixed_datetime.timetuple(),
        description="<p>This is a <b>test</b> description.</p>"
        )

    # Create a proper mock feed response
    mock_feed = SimpleNamespace(
        entries=[mock_entry],
        bozo=False,  # Important: Set bozo to False to indicate no parsing error
        bozo_exception=None,
        feed={}  # Add required feed attribute
    )   
    mock_parse.return_value = mock_feed
    # Run the node
    updated_state = retrieve_articles_metadata(rss_state)

    # Validate the result
    assert len(updated_state["articles_metadata"]) == 1
    article = updated_state["articles_metadata"][0]
    assert article["title"] == "Test Title"
    assert article["link"] == "https://example.com/article1"
    assert article["description"] == "This is a test description."
    assert article["pubDate"].startswith("2024-06-05T15:00")


# Testing text extract from urls
@pytest.fixture
def scraper_state(create_initial_state):    
    create_initial_state["articles_metadata"] = [
            {
                "title": "Test Article",
                "link": "https://news.google.com/test-article",
                "pubDate": "2025-06-05T15:00:00",
                "description": "Sample description"
            }
        ]
    
    return create_initial_state

@patch("src.nodes.research_nodes.requests.get")
@patch("src.nodes.research_nodes.gnewsdecoder")
def test_retrieve_articles_text(mock_decoder,mock_get,scraper_state):
    mock_decoder.return_value = {"decoded_url":"https://example.com/article"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = b"<html><body><p>This is the article content</p></body></html>"
    mock_get.return_value = mock_response

    # Run the function
    updated_state = retrieve_articles_text(scraper_state)

    # Assertions
    assert len(updated_state["potential_articles"]) == 1
    article = updated_state["potential_articles"][0]

    assert article["title"] == "Test Article"
    assert article["url"] == "https://example.com/article"
    assert "This is the article content" in article["text"]
    assert article["date"] == "2025-06-05T15:00:00"
    assert "https://example.com/article" in updated_state["scraped_urls"]


# Test retrieve top urls
@pytest.fixture
def top_urls_state(create_initial_state):
    create_initial_state["potential_articles"] = [
        {
            "title": "A",
            "url": "https://example.com/article-a",
            "description": "Description A",
            "text": "Full text A",
            "date": "2025-06-05"
        },
        {
            "title": "B",
            "url": "https://example.com/article-b",
            "description": "Description B",
            "text": "Full text B",
            "date": "2025-06-04"
        }
    ]
    create_initial_state["news_query"] = "Example query"
    create_initial_state["num_articles_tldr"] = 1
    return create_initial_state

@patch("src.nodes.research_nodes.ChatBedrockConverse")
@patch("src.nodes.research_nodes.os.getenv", return_value="test-model")
def test_select_top_urls(mock_getenv, mock_llm_class, top_urls_state):
    # Mock LLM output
    mock_llm_instance = MagicMock()
    mock_llm_instance.invoke.return_value.content = "https://example.com/article-b"
    mock_llm_class.return_value = mock_llm_instance

    updated_state = select_top_urls(top_urls_state)

    # Assert only the matching article is selected
    assert len(updated_state["tldr_articles"]) == 1
    assert updated_state["tldr_articles"][0]["url"] == "https://example.com/article-b"