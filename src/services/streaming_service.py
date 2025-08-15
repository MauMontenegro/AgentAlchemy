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
            print(f"[STREAMING] Starting stream_query_process with response length: {len(response)}")
            print(f"[STREAMING] Results count: {len(results)}")
            
            # Step 1: SQL Generation
            step1 = self._format_step('generating_sql', 'Convirtiendo pregunta a SQL...')
            print(f"[STREAMING] Step 1: {step1[:100]}...")
            yield step1
            await asyncio.sleep(0.1)
            
            # Step 2: Query Execution  
            step2 = self._format_step('executing_query', 'Ejecutando consulta SQL...', sql)
            print(f"[STREAMING] Step 2: {step2[:100]}...")
            yield step2
            await asyncio.sleep(0.1)
            
            # Step 3: Response Generation
            step3 = self._format_step('generating_response', 'Generando respuesta...')
            print(f"[STREAMING] Step 3: {step3[:100]}...")
            yield step3
            await asyncio.sleep(0.1)
            
            # Step 4: Stream response content
            print(f"[STREAMING] About to stream content: {response[:100]}...")
            chunk_count = 0
            async for chunk in self._stream_content(response):
                chunk_count += 1
                print(f"[STREAMING] Content chunk {chunk_count}: {chunk[:50]}...")
                yield chunk
            print(f"[STREAMING] Streamed {chunk_count} content chunks")
            
            # Final data with cleaned results
            cleaned_results = self._clean_results_for_streaming(results)
            final_data = self._format_data({
                'raw_data': cleaned_results, 
                'sql_query': sql, 
                'row_count': len(results)
            })
            print(f"[STREAMING] Final data: {final_data[:100]}...")
            yield final_data
            
            done_msg = "data: [DONE]\n\n"
            print(f"[STREAMING] Done message: {done_msg}")
            yield done_msg
            print(f"[STREAMING] Stream completed successfully")
            
        except Exception as e:
            print(f"[STREAMING] Error in stream_query_process: {str(e)}")
            error_msg = f"data: {json.dumps({'error': 'Streaming error: ' + str(e)})}\n\n"
            yield error_msg
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
        try:
            for i in range(0, len(content), self.chunk_size):
                chunk = content[i:i + self.chunk_size]
                formatted_chunk = f"data: {json.dumps({'content': chunk})}\n\n"
                print(f"[STREAMING] Yielding content chunk: {formatted_chunk[:50]}...")
                yield formatted_chunk
                await asyncio.sleep(0.02)
        except Exception as e:
            print(f"[STREAMING] Error in _stream_content: {str(e)}")
            raise
    
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