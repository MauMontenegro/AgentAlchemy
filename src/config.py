from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
import os

class Settings(BaseSettings):
    # Database
    db_user: str = Field(..., env="DB_USER")
    db_password: str = Field(..., env="DB_PASSWORD")
    db_host: str = Field(..., env="DB_HOST")
    db_port: str = Field(default="5432", env="DB_PORT")
    db_name: str = Field(..., env="DB_NAME")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # AWS/LLM
    reasoning_model: str = Field(..., env="REASONING_MODEL")
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    
    # API Keys
    newsapi_key: Optional[str] = Field(None, env="NEWSAPI_KEY")
    newsapi_api_key: Optional[str] = Field(None, env="NEWSAPI_API_KEY")
    tavily_api_key: Optional[str] = Field(None, env="TAVILY_API_KEY")
    
    # GCP Settings
    gcp_project_id: Optional[str] = Field(None, env="GCP_PROJECT_ID")
    gcp_private_key_id: Optional[str] = Field(None, env="GCP_PRIVATE_KEY_ID")
    gcp_private_key: Optional[str] = Field(None, env="GCP_PRIVATE_KEY")
    gcp_client_email: Optional[str] = Field(None, env="GCP_CLIENT_EMAIL")
    gcp_client_id: Optional[str] = Field(None, env="GCP_CLIENT_ID")
    
    # Admin Settings
    admin_user: Optional[str] = Field(None, env="ADMIN_USER")
    admin_password: Optional[str] = Field(None, env="ADMIN_PASSWORD")
    admin_email: Optional[str] = Field(None, env="ADMIN_EMAIL")
    
    # App Settings
    debug: bool = Field(default=False, env="DEBUG")
    cors_origins: List[str] = Field(
        default=[
            "https://saip-petroil.vercel.app",
            "http://localhost:5173"
        ],
        env="CORS_ORIGINS"
    )
    
    @property
    def database_url(self) -> str:
        from urllib.parse import quote_plus
        encoded_password = quote_plus(self.db_password)
        return f"postgresql+asyncpg://{self.db_user}:{encoded_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

settings = Settings()