from abc import ABC, abstractmethod
from typing import Dict, List, Any, AsyncGenerator
import json
import os
from langchain_aws import ChatBedrockConverse
from google.cloud import bigquery


class QueryService(ABC):
    """Abstracción para servicios de consulta - DIP"""
    
    @abstractmethod
    async def generate_sql(self, query: str, schemas: Dict[str, List[Dict]], relationships: Dict = None, business_context: str = None) -> str:
        pass
    
    @abstractmethod
    async def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def generate_response(self, query: str, sql: str, results: List[Dict], additional_context: str = None) -> str:
        pass


class BigQueryService(QueryService):
    """Implementación concreta para BigQuery - SRP"""
    
    def __init__(self, bq_client: bigquery.Client, llm_client: ChatBedrockConverse):
        self.bq_client = bq_client
        self.llm_client = llm_client
    
    async def generate_sql(self, query: str, schemas: Dict[str, List[Dict]], relationships: Dict = None, business_context: str = None) -> str:
        from datetime import datetime
        print(f"[SQL GENERATION] Starting SQL generation for query: {query}")
        print(f"[SQL GENERATION] Using tables: {list(schemas.keys())}")
        
        template = self._get_multi_table_sql_template()
        prompt = template.format(
            query=query, 
            esquemas=self._format_schemas_for_prompt(schemas),
            relaciones=self._format_relationships_for_prompt(relationships or {}),
            fecha=datetime.now().strftime("%Y-%m-%d"),
            business_context=business_context or ""
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
        print(f"[RESPONSE GENERATION] Starting response generation")
        print(f"[RESPONSE GENERATION] Query: {query}")
        print(f"[RESPONSE GENERATION] Results count: {len(results)}")
        
        # Limpiar y simplificar resultados para evitar problemas con datetime y objetos complejos
        cleaned_results = self._clean_results_for_llm(results)
        print(f"[RESPONSE GENERATION] Cleaned results: {cleaned_results[:500]}...")
        
        template = self._get_response_template()
        formatted_results = json.dumps(cleaned_results[:5], indent=2, ensure_ascii=False) if cleaned_results else "Sin resultados"
        
        prompt = template.format(
            original_query=query,
            sql_query=sql,
            results=formatted_results,
            row_count=len(results)
        )
        
        print(f"[RESPONSE GENERATION] Prompt length: {len(prompt)}")
        print(f"[RESPONSE GENERATION] Calling LLM for response...")
        
        try:
            response = await self.llm_client.ainvoke(prompt)
            print(f"[RESPONSE GENERATION] LLM response received")
            print(f"[RESPONSE GENERATION] Response content: {response.content[:200]}...")
            print(f"[RESPONSE GENERATION] Response length: {len(response.content)}")
            return response.content
        except Exception as e:
            print(f"[RESPONSE GENERATION] Error calling LLM: {str(e)}")
            # Fallback response
            return self._create_fallback_response(query, results)
    
    def _get_multi_table_sql_template(self) -> str:
        return """
        Eres un experto en SQL y BigQuery. Tu tarea es convertir preguntas en lenguaje natural a consultas SQL válidas para BigQuery.

        IMPORTANTE:
        - Solo devuelve la consulta SQL, sin explicaciones adicionales
        - Usa sintaxis válida de BigQuery
        - Si no puedes generar una consulta SQL válida, responde "ERROR: No puedo convertir esta pregunta a SQL"
        - Limita los resultados a un máximo de 20 filas usando LIMIT 20
        - USA EXACTAMENTE los nombres de tabla especificados en las relaciones
        - USA SOLO los nombres de campos que aparecen en los esquemas proporcionados
        - NO inventes nombres de campos, usa únicamente los listados en cada tabla
        - La fecha actual es: {fecha}
        
        TABLAS DISPONIBLES:
        {esquemas}
        
        RELACIONES ENTRE TABLAS (USA ESTOS NOMBRES EXACTOS):
        {relaciones}
        
        INSTRUCCIONES OBLIGATORIAS:
        - USA EXACTAMENTE los nombres de tabla mostrados en las relaciones
        - USA SOLO los nombres de campos listados en los esquemas de arriba
        - NO uses campos que no estén en la lista de esquemas
        - Para IngresosClientes usa: `sipp-app.Tableros.IgresosClientes`
        - Para vis_CarteraClientes usa: `sipp-app.Tableros.vis_CarteraClientes`
        - Para Vis_Ventas usa: `sipp-app.Tableros.Vis_Ventas`
        - Usa aliases: v, c, i respectivamente
        - VALIDA que cada campo usado existe en el esquema correspondiente

        CONTEXTO DE REGLAS DE NEGOCIO:
        {business_context}

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
    
    def _clean_results_for_llm(self, results: List[Dict]) -> List[Dict]:
        """Limpia los resultados para evitar problemas con el LLM"""
        import datetime
        
        cleaned = []
        for result in results:
            clean_result = {}
            for key, value in result.items():
                if isinstance(value, (datetime.datetime, datetime.date)):
                    clean_result[key] = str(value)
                elif value is None:
                    clean_result[key] = "N/A"
                elif isinstance(value, (int, float, str, bool)):
                    clean_result[key] = value
                else:
                    clean_result[key] = str(value)
            cleaned.append(clean_result)
        return cleaned
    
    def _create_fallback_response(self, query: str, results: List[Dict]) -> str:
        """Crea una respuesta de fallback cuando el LLM falla"""
        if not results:
            return "No se encontraron resultados para tu consulta."
        
        result = results[0]
        response_parts = [f"Encontré {len(results)} resultado(s) para tu consulta: '{query}'"]
        
        # Extraer campos más relevantes
        key_fields = ['nb_Cliente', 'im_Total', 'nb_Producto', 'fh_movimiento', 'de_Estatus']
        for field in key_fields:
            if field in result and result[field] is not None:
                response_parts.append(f"- {field}: {result[field]}")
        
        return "\n".join(response_parts)