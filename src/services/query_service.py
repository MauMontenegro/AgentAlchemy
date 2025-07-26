from abc import ABC, abstractmethod
from typing import Dict, List, Any, AsyncGenerator
import json
import os
from langchain_aws import ChatBedrockConverse
from google.cloud import bigquery


class QueryService(ABC):
    """Abstracción para servicios de consulta - DIP"""
    
    @abstractmethod
    async def generate_sql(self, query: str, schema: List[Dict]) -> str:
        pass
    
    @abstractmethod
    async def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def generate_response(self, query: str, sql: str, results: List[Dict]) -> str:
        pass


class BigQueryService(QueryService):
    """Implementación concreta para BigQuery - SRP"""
    
    def __init__(self, bq_client: bigquery.Client, llm_client: ChatBedrockConverse):
        self.bq_client = bq_client
        self.llm_client = llm_client
    
    async def generate_sql(self, query: str, schema: List[Dict]) -> str:
        template = self._get_sql_template()
        response = await self.llm_client.ainvoke(
            template.format(query=query, esquema=schema)
        )
        return self._clean_sql(response.content.strip())
    
    async def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        query_job = self.bq_client.query(sql)
        results = query_job.result()
        return [dict(row) for row in results]
    
    async def generate_response(self, query: str, sql: str, results: List[Dict]) -> str:
        template = self._get_response_template()
        response = await self.llm_client.ainvoke(
            template.format(
                original_query=query,
                sql_query=sql,
                results=json.dumps(results[:10], indent=2) if results else "Sin resultados",
                row_count=len(results)
            )
        )
        return response.content
    
    def _get_sql_template(self) -> str:
        return """
        Eres un experto en SQL y BigQuery. Tu tarea es convertir preguntas en lenguaje natural a consultas SQL válidas para BigQuery.

        IMPORTANTE:
        - Solo devuelve la consulta SQL, sin explicaciones adicionales
        - Usa sintaxis válida de BigQuery
        - Si no puedes generar una consulta SQL válida, responde "ERROR: No puedo convertir esta pregunta a SQL"
        - La tabla se llama 'Vis_Ventas' y está en el dataset 'Tableros' del proyecto 'sipp-app'
        - Usa el formato: FROM `sipp-app.Tableros.Vis_Ventas`
        - Limita los resultados a un máximo de 100 filas usando LIMIT 100
        - Utiliza el siguiente esquema de la tabla: {esquema}

        Pregunta del usuario: {query}
        
        SQL:
        """
    
    def _get_response_template(self) -> str:
        return """
        Basándote en los siguientes resultados de la consulta SQL, proporciona una respuesta clara y útil al usuario.

        Pregunta original: {original_query}
        SQL ejecutado: {sql_query}
        Resultados obtenidos: {results}
        Número de filas: {row_count}

        Proporciona una respuesta conversacional que explique los resultados de manera clara y profesional.
        """
    
    def _clean_sql(self, sql: str) -> str:
        if sql.startswith('```sql'):
            sql = sql.replace('```sql', '').replace('```', '').strip()
        elif sql.startswith('```'):
            sql = sql.replace('```', '').strip()
        return sql