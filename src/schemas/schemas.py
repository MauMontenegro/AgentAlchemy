from typing import TypedDict,Annotated,List,Literal
from pydantic import BaseModel,Field,HttpUrl
from datetime import datetime

class AgentState(TypedDict):
    news_query: Annotated[str, "Input query to extract news search parameters from."]
    num_searches_remaining: Annotated[int, "Number of articles to search for."]
    newsapi_params: Annotated[dict, "Structured argument for the News API."]
    past_searches: Annotated[List[dict], "List of search params already used."]
    articles_metadata: Annotated[list[dict], "Article metadata response from the News API"]
    scraped_urls: Annotated[List[str], "List of urls already scraped."]
    num_articles_tldr: Annotated[int, "Number of articles to create TL;DR for."]
    potential_articles: Annotated[List[dict[str, str, str]], "Article with full text to consider summarizing."]
    tldr_articles: Annotated[List[dict[str, str, str]], "Selected article TL;DRs."]
    formatted_results: Annotated[str, "Formatted results to display."]
  

class ScraperAgentState(TypedDict):
    url: Annotated[List,"Url of the article, doc or news to scrap"]
    title: Annotated[str,"Title of the url article"]
    text: Annotated[List,"List of Body Texts of the articles"]
    summary: Annotated[str,"Summary of Article"]   

class NewsApiParams(BaseModel):
    """Parameters needed to do a NEWSAPI search"""
    q: str = Field(description ="User Query")
    #sources: str =Field(description="comma-separated list of sources from: 'abc-news,abc-news-au,associated-press,australian-financial-review,axios,bbc-news,bbc-sport,bloomberg,business-insider,cbc-news,cbs-news,cnn,financial-post,fortune'")
    from_param: str = Field(description="date in format 'YYYY-MM-DD' Two days ago minimum. Extend up to 30 days on second and subsequent requests.")
    to: str = Field(description="date in format 'YYYY-MM-DD' today's date unless specified")
    language: str = Field(description="language of articles 'es' unless specified one of ['ar', 'de', 'en', 'es', 'fr', 'he', 'it', 'nl', 'no', 'pt', 'ru', 'se', 'ud', 'zh']")
    sort_by: str = Field(description="sort by 'relevancy', 'popularity', or 'publishedAt', by default is 'publishedAt'")

class AgentRequest(BaseModel):
    query : str = Field(description="User query to search for news")
    agent_type: str = Field(description="Type of agent selected for task")
    model:str = Field(description="Selected model to use as LLM")
    articles:int = Field(description="Number of articles to summarize",gt=0,le=10)

class ArticleSummary(BaseModel):
    title: str
    url: HttpUrl
    bullets: List[str]
    date: datetime
    topics: List[str]
    bias: Literal["center", "left", "right", "humor"]
    bias_explanation: str
    
class ArticleAnalysis(BaseModel):
    topics: List[str] = Field(description="Main topics or entities in the news article.")
    bias: Literal["center", "left", "right", "humor"] = Field(description="Detected political bias.")
    bias_explanation: str = Field(description="Explanation for the detected political bias.")

class AgentResponse(BaseModel):
    header: str
    summaries: List[ArticleSummary]

class ScrapAgentRequest(BaseModel):
    urls:List[HttpUrl]

class ScrapAgentResponse(BaseModel):
    summary:str = Field(description="Summary of the article")


