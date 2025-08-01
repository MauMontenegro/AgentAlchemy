from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from langchain_aws import ChatBedrockConverse

from .config import settings
from .services.query_service import BigQueryService
from .services.schema_service import SchemaFactory
from .services.streaming_service import StreamingService
from .services.intent_service import IntentAnalysisService
from .services.finance_orchestrator import FinanceQueryOrchestrator

class Container(containers.DeclarativeContainer):
    """Dependency injection container"""
    
    # Configuration
    config = providers.Object(settings)
    
    # Database
    engine = providers.Singleton(
        create_async_engine,
        url=config.provided.database_url,
        echo=config.provided.debug
    )
    
    session_factory = providers.Singleton(
        async_sessionmaker,
        bind=engine,
        expire_on_commit=False
    )
    
    # LLM Client
    llm_client = providers.Singleton(
        ChatBedrockConverse,
        model_id=config.provided.reasoning_model
    )
    
    # Services
    streaming_service = providers.Factory(
        StreamingService,
        chunk_size=20
    )
    
    intent_service = providers.Factory(
        IntentAnalysisService,
        llm_client=llm_client
    )
    
    # Orchestrators
    finance_orchestrator = providers.Factory(
        FinanceQueryOrchestrator,
        streaming_service=streaming_service,
        intent_service=intent_service
    )