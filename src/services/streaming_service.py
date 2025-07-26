from typing import AsyncGenerator, Dict, Any, List
import json
import asyncio


class StreamingService:
    """Servicio para manejo de streaming responses - SRP"""
    
    def __init__(self, chunk_size: int = 20):
        self.chunk_size = chunk_size
    
    async def stream_query_process(
        self, 
        query: str, 
        sql: str, 
        results: List[Dict[str, Any]], 
        response: str
    ) -> AsyncGenerator[str, None]:
        """Stream del proceso completo de query"""
        
        # Step 1: SQL Generation
        yield self._format_step('generating_sql', 'Convirtiendo pregunta a SQL...')
        
        # Step 2: Query Execution  
        yield self._format_step('executing_query', 'Ejecutando consulta SQL...', sql)
        
        # Step 3: Response Generation
        yield self._format_step('generating_response', 'Generando respuesta...')
        
        # Step 4: Stream response content
        async for chunk in self._stream_content(response):
            yield chunk
        
        # Final data
        yield self._format_data({
            'raw_data': results, 
            'sql_query': sql, 
            'row_count': len(results)
        })
        yield "data: [DONE]\n\n"
    
    async def stream_error(self, error: str) -> AsyncGenerator[str, None]:
        """Stream de errores"""
        yield self._format_error(self._get_friendly_error(error))
        yield "data: [DONE]\n\n"
    
    def _format_step(self, step: str, message: str, sql: str = None) -> str:
        data = {'step': step, 'message': message}
        if sql:
            data['sql'] = sql
        return f"data: {json.dumps(data)}\n\n"
    
    def _format_error(self, error: str) -> str:
        return f"data: {json.dumps({'error': error})}\n\n"
    
    def _format_data(self, data: Dict) -> str:
        return f"data: {json.dumps(data)}\n\n"
    
    async def _stream_content(self, content: str) -> AsyncGenerator[str, None]:
        for i in range(0, len(content), self.chunk_size):
            chunk = content[i:i + self.chunk_size]
            yield f"data: {json.dumps({'content': chunk})}\n\n"
            await asyncio.sleep(0.02)
    
    def _get_friendly_error(self, error: str) -> str:
        """Convierte errores técnicos en mensajes amigables"""
        if "Table" in error and "not found" in error:
            return "No se encontró la tabla especificada. Verifica que el nombre de la tabla sea correcto."
        elif "Syntax error" in error:
            return "Error de sintaxis en la consulta SQL generada. Intenta reformular tu pregunta."
        elif "Permission denied" in error:
            return "No tienes permisos para acceder a los datos solicitados."
        return f"Error ejecutando la consulta: {error}"