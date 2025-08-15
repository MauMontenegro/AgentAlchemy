import os
from langchain_aws import ChatBedrockConverse
from google.cloud import bigquery
from google.oauth2 import service_account

from .query_service import BigQueryService
from .schema_service import SchemaFactory
from .streaming_service import StreamingService
from .finance_orchestrator import FinanceQueryOrchestrator
from .intent_service import IntentAnalysisService
from .business_rules_service import BusinessRulesService
from .bquery_db import BigQueryConfig


class DependencyFactory:
    """Factory para crear todas las dependencias - DIP + Factory Pattern"""
    
    @staticmethod
    def create_finance_orchestrator() -> FinanceQueryOrchestrator:
        """Crea el orquestador con todas sus dependencias"""
        
        # Crear cliente BigQuery
        bq_client = DependencyFactory._create_bigquery_client()
        
        # Crear cliente LLM
        llm_client = ChatBedrockConverse(
            model_id=os.getenv("REASONING_MODEL")
        )
        
        # Crear servicios
        query_service = BigQueryService(bq_client, llm_client)
        schema_service = SchemaFactory.create_schema_service("multi_table")
        streaming_service = StreamingService(chunk_size=20)
        intent_service = IntentAnalysisService(llm_client)
        business_rules_service = BusinessRulesService()
        
        # Crear orquestador
        return FinanceQueryOrchestrator(
            query_service=query_service,
            schema_service=schema_service,
            streaming_service=streaming_service,
            intent_service=intent_service,
            business_rules_service=business_rules_service
        )
    
    @staticmethod
    def _create_bigquery_client() -> bigquery.Client:
        """Crea cliente BigQuery usando configuración existente"""
        config = BigQueryConfig()
        credentials_json = config.get_credentials_dict()
        credentials = service_account.Credentials.from_service_account_info(
            credentials_json,
            scopes=['https://www.googleapis.com/auth/bigquery']
        )
        
        return bigquery.Client(
            credentials=credentials,
            project=credentials_json['project_id']
        )