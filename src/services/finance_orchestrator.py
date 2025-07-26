from typing import AsyncGenerator
from .query_service import QueryService
from .schema_service import SchemaService
from .streaming_service import StreamingService


class FinanceQueryOrchestrator:
    """Orquestador principal - coordina todos los servicios - SRP"""
    
    def __init__(
        self, 
        query_service: QueryService,
        schema_service: SchemaService,
        streaming_service: StreamingService
    ):
        self.query_service = query_service
        self.schema_service = schema_service
        self.streaming_service = streaming_service
    
    async def process_query(self, user_query: str) -> AsyncGenerator[str, None]:
        """Procesa una consulta completa"""
        try:
            # 1. Obtener esquema
            schema = self.schema_service.get_table_schema()
            
            # 2. Generar SQL
            sql = await self.query_service.generate_sql(user_query, schema)
            
            # Verificar si hubo error en generación SQL
            if "ERROR:" in sql:
                async for chunk in self.streaming_service.stream_error(sql):
                    yield chunk
                return
            
            # 3. Ejecutar query
            results = await self.query_service.execute_query(sql)
            
            # 4. Generar respuesta
            response = await self.query_service.generate_response(user_query, sql, results)
            
            # 5. Stream completo
            async for chunk in self.streaming_service.stream_query_process(
                user_query, sql, results, response
            ):
                yield chunk
                
        except Exception as e:
            async for chunk in self.streaming_service.stream_error(str(e)):
                yield chunk