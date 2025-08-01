import json
from fastapi.responses import StreamingResponse
from langchain_aws import ChatBedrockConverse
import os
import dotenv
from dotenv import load_dotenv

load_dotenv()

async def chat_bedrock(query: str):
    """Call bedrock model and answer user query"""
    # Initialize the chat with only the required parameters
    chat = ChatBedrockConverse(
        model_id=os.getenv("REASONING_MODEL")
    )

    messages = [
    ("system", "You are a helpful translator. Translate the user sentence to French."),
    ("human", query)]   
    
    try:
        # Call invoke with the formatted template
        response = await chat.ainvoke(messages)   
        
        # Send the response in SSE format
        def generate():
            # Send response in chunks
            chunk_size = 10  # Adjust chunk size as needed
            for i in range(0, len(response.content), chunk_size):
                chunk = response.content[i:i + chunk_size]
                # Format as SSE 
                data = json.dumps({"content": chunk})
                yield f"data: {data}\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
            
    except Exception as e:
        print(f"Error in chat_bedrock: {str(e)}")
        raise