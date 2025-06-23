import traceback
import boto3
from fastapi import HTTPException

def textract_service(image_bytes:bytes)-> dict:
    session = boto3.Session(profile_name="default")
    textract_agent = session.client("textract")

    try:
        extracted_text = []
        response = textract_agent.detect_document_text(Document={"Bytes": image_bytes})
        for item in response["Blocks"]:
            if item["BlockType"] == "LINE" or item["BlockType"] == "WORD":
                extracted_text.append(item["Text"])
             
        return extracted_text

    except boto3.exceptions.Boto3Error as e:
        raise HTTPException(
            status_code=500, detail=f"AWS Textract error: {str(e)}"
        ) from e
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Unexpected error: {str(e)}"
        ) from e