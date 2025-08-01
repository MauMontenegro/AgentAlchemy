from asyncio import as_completed 
import json
from datetime import date
from functools import lru_cache
from typing import List, Dict, Type, Any

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import Field, create_model, BaseModel

from src.agents.ocr import OcrAgent
from src.schemas.schemas import OcrAgentState
from src.logger import logger
from src.routers.auth_route import get_current_user
from src.models.models import User

# Constants
SUPPORTED_FIELD_TYPES: Dict[str, Type] = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": List[Any],
    "dict": dict,
    "date": date
}

# File type validation
SUPPORTED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf"
}

# Cache for dynamic models
@lru_cache(maxsize=32)
def get_cached_dynamic_model(schema_dict: frozenset) -> type[BaseModel]:
    """Get or create a cached dynamic Pydantic model."""
    return build_dynamic_model(dict(schema_dict))

def get_python_type(type_string: str) -> Type:
    """Convert string type representation to Python type."""
    return SUPPORTED_FIELD_TYPES.get(type_string.lower(), str)

def create_initial_state(file: bytes, schema: type[BaseModel]) -> OcrAgentState:
    """Create initial state for OCR processing."""
    return OcrAgentState(
        file=file,
        extracted_text=None,
        schema=schema,
        structured=None
    )

async def process_single_file(
    file_data: Dict[str, Any], 
    DynamicSchema: type[BaseModel], 
    agent: OcrAgent
) -> Dict[str, Any]:
    """Process a single file with error handling and logging."""
    try:
        logger.debug(f"Processing file: {file_data['filename']}")
        
        if file_data["content_type"] not in SUPPORTED_CONTENT_TYPES:
            return {
                "file": file_data["filename"],
                "error": f"Unsupported file type: {file_data['content_type']}"
            }

        initial_state = create_initial_state(file_data["bytes"], DynamicSchema)
        logger.info(f"Running OCR agent on {file_data['filename']}")        
        final_state = await agent.graph.ainvoke(initial_state)
        return {
            "file": file_data["filename"],
            "structured": final_state["structured"]
        }
        
    except Exception as e:
        logger.exception(f"Error processing {file_data['filename']}")
        return {
            "file": file_data["filename"],
            "error": f"Processing failed: {str(e)}"
        }

def build_dynamic_model(schema_dict: Dict) -> type[BaseModel]:
    """Build a dynamic Pydantic model from a schema dictionary."""
    logger.debug("Building dynamic model")
    fields = {}
    
    for field_name, (type_str, required, description) in schema_dict.items():
        py_type = get_python_type(type_str)
        default = ... if required else None
        field_def = Field(default, description=description)
        fields[field_name] = (py_type, field_def)
        
    return create_model("DynamicSchema", **fields)

router = APIRouter()

@router.post("/extract")
async def extract_text(
    files: List[UploadFile] = File(...),
    schema: str = Form(...),
    current_user:User=Depends(get_current_user)
) -> StreamingResponse:
    """
    Stream OCR results per file with improved concurrency and error handling.
    
    Args:
        files: List of uploaded files for OCR processing
        schema: JSON string defining the expected output schema
        
    Returns:
        StreamingResponse: NDJSON stream of processing results
    """
    _=current_user
    if not files:
        raise HTTPException(status_code=400, detail="No files were provided")

    # Parse and validate schema
    try:
        schema_dict = json.loads(schema)
        if not isinstance(schema_dict, dict):
            raise ValueError("Schema must be a JSON object")
    except (json.JSONDecodeError, ValueError) as e:
        return StreamingResponse(
            iter([json.dumps({"error": f"Invalid schema: {str(e)}"}) + "\n"]),
            media_type="application/x-ndjson"
        )

    # Create dynamic model from schema (cached)
    try:
        schema_key = frozenset((k, tuple(v) if isinstance(v, list) else v) 
                             for k, v in schema_dict.items())
        DynamicSchema = get_cached_dynamic_model(schema_key)
    except Exception as e:
        logger.exception("Failed to create dynamic model from schema")
        return StreamingResponse(
            iter([json.dumps({"error": f"Invalid schema format: {str(e)}"}) + "\n"]),
            media_type="application/x-ndjson"
        )

    # Read all files into memory (consider streaming for large files)
    file_data = []
    error_responses = []
    
    for file in files:
        try:
            content = await file.read()
            if not content:
                raise ValueError("Empty file")
                
            file_data.append({
                "filename": file.filename or "unnamed_file",
                "content_type": file.content_type or "application/octet-stream",
                "bytes": content
            })
        except Exception as e:
            error_msg = f"Error reading file {file.filename}: {str(e)}"
            logger.error(error_msg)
            error_responses.append({
                "file": file.filename or "unnamed_file",
                "error": f"Failed to read file: {str(e)}"
            })

    # Create agent instance (consider making this a singleton)
    agent = OcrAgent()
    
    # Process files concurrently
    tasks = [
        process_single_file(file, DynamicSchema, agent)
        for file in file_data
    ]

    # Stream results as they complete
    async def stream_results():
        # First yield any file reading errors
        for error in error_responses:
            yield json.dumps(error) + "\n"
            
        # Then process the files that were read successfully
        if file_data:
            tasks = [
                process_single_file(file, DynamicSchema, agent)
                for file in file_data
            ]
            
            for future in as_completed(tasks):
                try:
                    result = await future
                    yield json.dumps(result) + "\n"
                except Exception as e:
                    logger.exception("Unexpected error in result streaming")
                    yield json.dumps({
                        "error": f"Unexpected error: {str(e)}"
                    }) + "\n"

    # Create and return the streaming response
    return StreamingResponse(
        stream_results(),
        media_type="application/x-ndjson"
    )
