from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from src.services.dependency_factory import DependencyFactory

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

@router.post("/query")
async def query_endpoint(request: QueryRequest):
    """Endpoint simplificado que delega toda la lógica al orquestador"""
    try:
        if not request.query:
            raise HTTPException(status_code=400, detail="Se requiere una pregunta para continuar")
        
        # Crear orquestador con todas las dependencias
        orchestrator = DependencyFactory.create_finance_orchestrator()
        
        # Procesar query y retornar stream
        return StreamingResponse(
            orchestrator.process_query(request.query),
            media_type="text/event-stream",
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
            }
        )
        
    except Exception as e:
        print(f"Error in query_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))