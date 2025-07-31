from abc import ABC, abstractmethod
from typing import Dict, List, Any, AsyncGenerator
import json
import os
from langchain_aws import ChatBedrockConverse
from google.cloud import bigquery


class QueryService(ABC):
    """Abstracción para servicios de consulta - DIP"""
    
    @abstractmethod
    async def generate_sql(self, query: str, schemas: Dict[str, List[Dict]], relationships: Dict = None) -> str:
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
    
    async def generate_sql(self, query: str, schemas: Dict[str, List[Dict]], relationships: Dict = None) -> str:
        from datetime import datetime
        print(f"[SQL GENERATION] Starting SQL generation for query: {query}")
        print(f"[SQL GENERATION] Using tables: {list(schemas.keys())}")
        
        template = self._get_multi_table_sql_template()
        prompt = template.format(
            query=query, 
            esquemas=self._format_schemas_for_prompt(schemas),
            relaciones=self._format_relationships_for_prompt(relationships or {}),
            fecha=datetime.now().strftime("%Y-%m-%d")
        )
        
        print(f"[SQL GENERATION] Prompt length: {len(prompt)} characters")
        print(f"[SQL GENERATION] Relationships being used:")
        print(self._format_relationships_for_prompt(relationships or {}))
        print(f"[SQL GENERATION] Calling LLM...")
        
        response = await self.llm_client.ainvoke(prompt)
        
        print(f"[SQL GENERATION] LLM response received")
        print(f"[SQL GENERATION] Raw SQL: {response.content[:200]}...")
        
        sql = self._clean_sql(response.content.strip())
        print(f"[SQL GENERATION] Final SQL: {sql}")
        # Verificar si el SQL contiene nombres de tabla incorrectos
        if 'sipp-app:' in sql:
            print(f"[SQL GENERATION] WARNING: SQL contains incorrect table format with colon")
        return sql
    
    async def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        print(f"[QUERY EXECUTION] Executing SQL: {sql[:100]}...")
        try:
            query_job = self.bq_client.query(sql)
            print(f"[QUERY EXECUTION] Query job created, waiting for results...")
            results = query_job.result()
            result_list = [dict(row) for row in results]
            print(f"[QUERY EXECUTION] Query completed, {len(result_list)} rows returned")
            return result_list
        except Exception as e:
            print(f"[QUERY EXECUTION] Error: {str(e)}")
            raise
    
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
    
    def _get_multi_table_sql_template(self) -> str:
        return """
        Eres un experto en SQL y BigQuery. Tu tarea es convertir preguntas en lenguaje natural a consultas SQL válidas para BigQuery.

        IMPORTANTE:
        - Solo devuelve la consulta SQL, sin explicaciones adicionales
        - Usa sintaxis válida de BigQuery
        - Si no puedes generar una consulta SQL válida, responde "ERROR: No puedo convertir esta pregunta a SQL"
        - Limita los resultados a un máximo de 100 filas usando LIMIT 100
        - USA EXACTAMENTE los nombres de tabla especificados en las relaciones
        - La fecha actual es: {fecha}
        
        TABLAS DISPONIBLES:
        {esquemas}
        
        RELACIONES ENTRE TABLAS (USA ESTOS NOMBRES EXACTOS):
        {relaciones}
        
        INSTRUCCIONES OBLIGATORIAS:
        - USA EXACTAMENTE los nombres de tabla mostrados en las relaciones
        - Para IngresosClientes usa: `sipp-app.Tableros.IgresosClientes`
        - Para vis_CarteraClientes usa: `sipp-app.Tableros.vis_CarteraClientes`
        - Para Vis_Ventas usa: `sipp-app.Tableros.Vis_Ventas`
        - Usa aliases: v, c, i respectivamente

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
    
    def _format_schemas_for_prompt(self, schemas: Dict[str, List[Dict]]) -> str:
        """Formatea los esquemas para el prompt"""
        formatted = []
        for table_name, schema in schemas.items():
            table_info = f"\n{table_name}:\n"
            for field in schema:
                table_info += f"  - {field['name']} ({field['type']}): {field['description']}\n"
            formatted.append(table_info)
        return "\n".join(formatted)
    
    def _format_relationships_for_prompt(self, relationships: Dict) -> str:
        """Formatea las relaciones para el prompt"""
        if not relationships or 'relationships' not in relationships:
            return "No hay relaciones definidas"
        
        formatted = []
        tables_info = relationships.get('tables', {})
        
        for rel in relationships['relationships']:
            from_table = rel['from_table']
            to_table = rel['to_table']
            join_condition = rel['join_condition']
            
            from_full = tables_info.get(from_table, {}).get('full_name', from_table)
            to_full = tables_info.get(to_table, {}).get('full_name', to_table)
            
            formatted.append(f"- {from_table} -> {to_table}: {join_condition}")
            formatted.append(f"  FROM `{from_full}` v LEFT JOIN `{to_full}` {to_table[0].lower()} ON {join_condition}")
        
        return "\n".join(formatted)
    
    def _clean_sql(self, sql: str) -> str:
        if sql.startswith('```sql'):
            sql = sql.replace('```sql', '').replace('```', '').strip()
        elif sql.startswith('```'):
            sql = sql.replace('```', '').strip()
        return sql