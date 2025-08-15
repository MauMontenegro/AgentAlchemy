from typing import AsyncGenerator
from .query_service import QueryService
from .schema_service import SchemaService
from .streaming_service import StreamingService
from .intent_service import IntentAnalysisService
from .business_rules_service import BusinessRulesService


class FinanceQueryOrchestrator:
    """Orquestador principal - coordina todos los servicios - SRP"""
    
    def __init__(
        self, 
        query_service: QueryService,
        schema_service: SchemaService,
        streaming_service: StreamingService,
        intent_service: IntentAnalysisService = None,
        business_rules_service: BusinessRulesService = None
    ):
        self.query_service = query_service
        self.schema_service = schema_service
        self.streaming_service = streaming_service
        self.intent_service = intent_service
        self.business_rules_service = business_rules_service or BusinessRulesService()
    
    async def process_query(self, user_query: str) -> AsyncGenerator[str, None]:
        """Procesa una consulta completa con soporte multi-tabla"""
        try:
            # 1. Aplicar reglas de negocio
            business_rules_result = self.business_rules_service.apply_business_rules(user_query)
            processed_query = business_rules_result["transformed_query"]
            business_context = self.business_rules_service.get_business_context(business_rules_result)
            
            # 2. Obtener esquemas relevantes usando análisis de intención
            relevant_schemas = await self.schema_service.get_relevant_schemas(processed_query, self.intent_service)
            relationships = self.schema_service.get_table_relationships()
            
            # 3. Generar SQL con múltiples tablas y reglas de negocio
            sql = await self.query_service.generate_sql(
                processed_query, 
                relevant_schemas, 
                relationships,
                business_context
            )
            
            # Aplicar filtros SQL de reglas de negocio
            business_filters = self.business_rules_service.get_sql_filters(business_rules_result)
            if business_filters and "WHERE" in sql:
                sql = sql.replace("WHERE", f"WHERE 1=1 {business_filters} AND")
            elif business_filters:
                sql = sql.rstrip(';') + f" WHERE 1=1 {business_filters};"
            
            # Verificar si hubo error en generación SQL
            if "ERROR:" in sql:
                async for chunk in self.streaming_service.stream_error(sql):
                    yield chunk
                return
            
            # 4. Corregir EXTRACT en campos string de fecha
            sql = self._fix_date_extracts(sql)
            
            # 5. Ejecutar query
            try:
                results = await self.query_service.execute_query(sql)
            except Exception as e:
                # Handle any BigQuery or SQL errors with specific details
                error_details = str(e)
                print(f"[ORCHESTRATOR] Caught error during query execution: {error_details}")
                
                # Extract meaningful error message for user
                if "not found" in error_details.lower():
                    error_msg = f"Error en la consulta: {error_details}. Por favor, verifica los nombres de las columnas o tablas."
                elif "extract" in error_details.lower() and "string" in error_details.lower():
                    error_msg = "Error: Las fechas están almacenadas como texto. La consulta necesita ser reformulada para trabajar con fechas en formato string."
                elif "invalid" in error_details.lower():
                    error_msg = f"Consulta inválida: {error_details}. Por favor, reformula tu pregunta."
                else:
                    error_msg = f"Error en la base de datos: {error_details}"
                
                async for chunk in self.streaming_service.stream_error(error_msg):
                    yield chunk
                return
            
            # 6. Generar respuesta
            print(f"[ORCHESTRATOR] About to generate response with {len(results)} results")
            print(f"[ORCHESTRATOR] First result sample: {results[0] if results else 'No results'}")
            
            response = await self.query_service.generate_response(
                user_query, sql, results
            )
            print(f"[ORCHESTRATOR] Generated response: {response[:200]}...")
            
            # 7. Stream completo
            print(f"[ORCHESTRATOR] Starting streaming process")
            chunk_count = 0
            try:
                async for chunk in self.streaming_service.stream_query_process(
                    user_query, sql, results, response
                ):
                    chunk_count += 1
                    print(f"[ORCHESTRATOR] Yielding chunk {chunk_count}: {chunk[:100]}...")
                    yield chunk
                print(f"[ORCHESTRATOR] Streaming completed successfully with {chunk_count} chunks")
            except Exception as streaming_error:
                print(f"[ORCHESTRATOR] Streaming error: {str(streaming_error)}")
                # Yield error message to frontend
                error_chunk = f"data: {{\"error\": \"Streaming failed: {str(streaming_error)}\"}}\n\n"
                yield error_chunk
                yield "data: [DONE]\n\n"
                
        except Exception as e:
            print(f"[ORCHESTRATOR] Main process error: {str(e)}")
            try:
                async for chunk in self.streaming_service.stream_error(str(e)):
                    yield chunk
            except Exception as stream_error:
                print(f"[ORCHESTRATOR] Error streaming error message: {str(stream_error)}")
                # Fallback error response
                yield f"data: {{\"error\": \"Process failed: {str(e)}\"}}\n\n"
                yield "data: [DONE]\n\n"
    
    def _fix_date_extracts(self, sql: str) -> str:
        """Convierte funciones de fecha en campos string a formato válido"""
        import re
        
        # Campos de fecha que son string
        date_fields = ['fh_Documento', 'fh_Vencimiento', 'fh_Registro']
        
        for field in date_fields:
            # EXTRACT(MONTH FROM field) -> CAST(SUBSTR(field, 6, 2) AS INT64)
            sql = re.sub(
                rf'EXTRACT\(MONTH FROM {field}\)',
                f'CAST(SUBSTR({field}, 6, 2) AS INT64)',
                sql, flags=re.IGNORECASE
            )
            
            # EXTRACT(YEAR FROM field) -> CAST(SUBSTR(field, 1, 4) AS INT64)
            sql = re.sub(
                rf'EXTRACT\(YEAR FROM {field}\)',
                f'CAST(SUBSTR({field}, 1, 4) AS INT64)',
                sql, flags=re.IGNORECASE
            )
            
            # Reemplazar PARSE_DATETIME con formato y campo
            sql = re.sub(
                rf'PARSE_DATETIME\([^,]+,\s*{field}\)',
                f'DATE(COALESCE(SAFE.PARSE_TIMESTAMP(\'%Y-%m-%dT%H:%M:%E*S\', {field}), SAFE.PARSE_TIMESTAMP(\'%Y-%m-%d %H:%M:%E*S\', {field})))',
                sql, flags=re.IGNORECASE
            )
            
            # También manejar con alias de tabla
            sql = re.sub(
                rf'PARSE_DATETIME\([^,]+,\s*c\.{field}\)',
                f'DATE(COALESCE(SAFE.PARSE_TIMESTAMP(\'%Y-%m-%dT%H:%M:%E*S\', c.{field}), SAFE.PARSE_TIMESTAMP(\'%Y-%m-%d %H:%M:%E*S\', c.{field})))',
                sql, flags=re.IGNORECASE
            )
            
            # EXTRACT anidado con PARSE_DATETIME
            sql = re.sub(
                rf'EXTRACT\((MONTH|YEAR) FROM PARSE_DATETIME\({field}[^)]+\)\)',
                lambda m: f'CAST(SUBSTR({field}, {"6, 2" if m.group(1).upper() == "MONTH" else "1, 4"}) AS INT64)',
                sql, flags=re.IGNORECASE
            )
        
        return sql