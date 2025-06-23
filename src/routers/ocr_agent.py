import json
from datetime import datetime
from fastapi import APIRouter,Depends,File,UploadFile,Form,HTTPException
from pydantic import Field
from typing import List,Dict, Type, Any
from src.schemas.schemas import OCRResponse
from src.agents.ocr import OcrAgent

from pydantic import create_model
from typing import Any

from src.schemas.schemas import OcrAgentState

from src.logger import logger

# Constants should be UPPER_CASE and clearly named
SUPPORTED_FIELD_TYPES: Dict[str, Type] = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": List[Any],
    "dict": dict,
    "date": datetime
}

def get_python_type(type_string: str) -> Type:
    """Convert string type representation to Python type."""
    return SUPPORTED_FIELD_TYPES.get(type_string, str)

def create_initial_state(file:bytes,schema:dict)->OcrAgentState:
    state=OcrAgentState(
        file=file,
        extracted_text=None,
        schema=schema,
        structured=None
    )
    return state

router = APIRouter()

@router.post("/extract",response_model=OCRResponse)
async def extract_text(
    files:List[UploadFile]=File(...),
    schema:str=Form(...)):
    
    """
    Extract text from images using OCR.
    
    Args:
        request: The OCR request containing image files and schema
        
    Returns:
        OCRResponse: The extracted text from the images
    """
    
    if not files:
        logger.error("No files were provided")
        raise HTTPException(status_code=400, detail="No files were provided")
    

    for file in files:
        logger.debug(f"File: {file.filename}, Content-Type: {file.content_type}, Size: {file.size} bytes")
        if file.content_type not in ["image/jpeg", "image/png", "application/pdf"]:
            logger.error(f"Unsupported file type: {file.content_type}")
            raise HTTPException(
            status_code=400, detail="Only JPEG, PNG, and PDF files are allowed."
            )
        file_bytes = await file.read()

        logger.debug("Convirtiendo schema a formato:dict")
        try:
            schema_dict= json.loads(schema)
        except json.JSONDecodeError:
            return OCRResponse(structured={"error": "Invalid JSON schema"})
        
        logger.debug("Creando esquema dinámico")   
        fields={}
        for field_name,(type_str,required,description) in schema_dict.items():
            py_type = get_python_type(type_str)
            default = ... if required else None
            field_def = Field(default,description=description)
            fields[field_name]=(py_type,field_def)    
        
        DynamicSchema = create_model("DynamicSchema", **fields)    

        logger.debug("Creando estado inicial")
        initial_state = create_initial_state(file_bytes, DynamicSchema)
        
        agent = OcrAgent()

        logger.debug("Iniciando agente" )
        final_state = await agent.graph.ainvoke(initial_state)
        
        logger.debug(f"Estructura de respuesta: {final_state['structured']}")
        return OCRResponse(structured=final_state["structured"])