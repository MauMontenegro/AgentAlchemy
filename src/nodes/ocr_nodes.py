import os
from dotenv import load_dotenv
from langchain_aws import ChatBedrockConverse
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from src.services.ocr_service import textract_service
from src.schemas.schemas import OcrAgentState
from src.logger import logger


def ocr_step(state:OcrAgentState)->OcrAgentState:
    """
    OCR Step: Extract text from images using OCR.
    
    Args:
        state: The current state of the agent
        
    Returns:
        The updated state with extracted text
    """
    logger.debug("Starting OCR step")
    try:
        extracted_text = textract_service(state['file'])    
        state["extracted_text"] = extracted_text
        return state
    except Exception as e:
        logger.error(f"Error in OCR step: {e}")       
        raise e
    
def build_pydantic_schema(state:OcrAgentState)->OcrAgentState:
    """
    Build Pydantic Schema: Create a Pydantic schema for the extracted text.

    Args:
        state: The current state of the agent

    Returns:
        The updated state with the Pydantic schema
    """
    logger.debug("Starting Pydantic schema step")
    try:
        load_dotenv()
        parser = JsonOutputParser(pydantic_object=state["schema"])
        prompt = PromptTemplate(
            template="Extract the following information from the text: {text}\n{format_instructions}",
            input_variables=["text"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        model = os.getenv("REASONING_MODEL")
        llm = ChatBedrockConverse(model=model, temperature=0)
        chain = prompt | llm | parser
        state["structured"] = chain.invoke({"text": state["extracted_text"]})
        return state
    except Exception as e:
        logger.error(f"Error in Pydantic schema step: {e}")
        raise e      