from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_aws import ChatBedrockConverse
import asyncio
import os
import json

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

@router.post("/chat")
async def chat_endpoint(request: QueryRequest):
    try:
        query = request.query
        print(f"Received query: {query}")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Initialize the chat
        chat = ChatBedrockConverse(
            model_id=os.getenv("REASONING_MODEL")
        )

        template = """
        Eres un agente conversacional que responde de manera cordial a la pregunta del usuario.    
        Pregunta:
        {query}
        """
        
        async def generate():
            try:
                # Get the complete response
                response = await chat.ainvoke(template.format(query=query))
                
                # Stream the response in chunks
                chunk_size = 10
                for i in range(0, len(response.content), chunk_size):
                    chunk = response.content[i:i + chunk_size]
                    # Format as SSE
                    data = json.dumps({"content": chunk})
                    yield f"data: {data}\n\n"
                    # Small delay to simulate streaming
                    await asyncio.sleep(0.01)
                    
                # Send a final message to indicate completion
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                print(f"Error in generate: {str(e)}")
                error_data = json.dumps({"error": str(e)})
                yield f"data: {error_data}\n\n"
                yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
            }
        )
        
    except Exception as e:
        print(f"Error in chat_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))