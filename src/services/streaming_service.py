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
        try:
            # Stream SQL query
            yield f"data: {json.dumps({'sql_query': sql})}\n\n"
            await asyncio.sleep(0.1)
            
            # Stream response content in chunks
            async for chunk in self._stream_content(response):
                yield chunk
            
            # Stream raw data if available
            if results:
                cleaned_results = self._clean_results_for_streaming(results)
                yield f"data: {json.dumps({'raw_data': cleaned_results})}\n\n"
            
            # End stream
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Streaming error: {str(e)}'})}\n\n"
            yield "data: [DONE]\n\n"
    
    async def stream_error(self, error: str) -> AsyncGenerator[str, None]:
        """Stream de errores"""
        yield self._format_error(self._get_friendly_error(error))
        yield "data: [DONE]\n\n"
    
    def _format_error(self, error: str) -> str:
        return f"data: {json.dumps({'error': error})}\n\n"
    
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
    
    def _clean_results_for_streaming(self, results: List[Dict]) -> List[Dict]:
        """Limpia los resultados para el streaming al frontend"""
        import datetime
        
        cleaned = []
        for result in results:
            clean_result = {}
            for key, value in result.items():
                if isinstance(value, (datetime.datetime, datetime.date)):
                    clean_result[key] = str(value)
                elif value is None:
                    clean_result[key] = None
                else:
                    clean_result[key] = value
            cleaned.append(clean_result)
        return cleaned