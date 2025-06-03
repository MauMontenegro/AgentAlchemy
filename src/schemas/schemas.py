from typing import TypedDict,Annotated,List,Literal,Optional
from pydantic import BaseModel,Field,HttpUrl
from datetime import datetime

class AgentState(TypedDict):
    news_query: Annotated[str, "Input query to extract news search parameters from."]
    languages: Annotated[List[str],"News languages"]
    countries:Annotated[List[str],"News Countries"]
    sources: Annotated[List[str],"News Sources"]
    num_articles_tldr: Annotated[int, "Number of articles to create TL;DR for."]
    urls: Annotated[List[str],"Urls to scrap."]

    num_searches_remaining: Annotated[int, "Number of articles to search for."]
    newsapi_params: Annotated[dict, "Structured argument for the News API."]
    past_searches: Annotated[List[dict], "List of search params already used."]
    articles_metadata: Annotated[list[dict], "Article metadata response from the News API"]
    scraped_urls: Annotated[List[str], "List of urls already scraped."]    
    potential_articles: Annotated[List[dict[str, str, str]], "Article with full text to consider summarizing."]
    tldr_articles: Annotated[List[dict[str, str, str]], "Selected article TL;DRs."]
    formatted_results: Annotated[str, "Formatted results to display."]
    report: Annotated[str,"Final State of the art report"]
    mode :Annotated[str,"Agent Mode:simple or advanced"]
  

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
    # Required Fields
    query : str = Field(description="User query to search for news")
    articles:int = Field(description="Number of articles to summarize",gt=0,le=10)

    # Agent Mode
    mode:str=Field(description="News agent mode")

    # Optional fields
    source: Optional[List[str]] = Field(None, description="Specific news source domain (e.g. 'bbc.com')")
    language: Optional[List[str]] = Field(None, description="Language code for news filtering (e.g. 'es', 'en')")
    country: Optional[List[str]] = Field(None, description="Country code for news filtering (e.g. 'VE', 'US')")

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
    report:str

class ScrapAgentRequest(BaseModel):
    urls:List[HttpUrl]

class ScrapAgentResponse(BaseModel):
    summary:str = Field(description="Summary of the article")


