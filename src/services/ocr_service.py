import traceback
import boto3
import io
from fastapi import HTTPException
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

def textract_service(image_bytes: bytes) -> dict:
    session = boto3.Session(profile_name="default")
    textract_agent = session.client("textract")

    try:
        # Check if document is multi-page PDF
        if _is_multipage_pdf(image_bytes):
            return _process_multipage_document(textract_agent, image_bytes)
        else:
            return _process_single_page(textract_agent, image_bytes)

    except boto3.exceptions.Boto3Error as e:
        raise HTTPException(
            status_code=500, detail=f"AWS Textract error: {str(e)}"
        ) from e
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Unexpected error: {str(e)}"
        ) from e

def _is_multipage_pdf(file_bytes: bytes) -> bool:
    """Check if the file is a multi-page PDF"""
    return file_bytes.startswith(b'%PDF')

def _process_single_page(textract_client, image_bytes: bytes) -> list:
    """Process single page document"""
    extracted_text = []
    response = textract_client.detect_document_text(Document={"Bytes": image_bytes})
    for item in response["Blocks"]:
        if item["BlockType"] == "LINE" or item["BlockType"] == "WORD":
            extracted_text.append(item["Text"])
    return extracted_text

def _process_multipage_document(textract_client, pdf_bytes: bytes) -> list:
    """Process multi-page PDF using PyMuPDF"""
    if not fitz:
        # Fallback to single page processing
        return _process_single_page(textract_client, pdf_bytes)
    
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        all_extracted_text = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            img_bytes = pix.tobytes("png")
            
            page_text = _process_single_page(textract_client, img_bytes)
            all_extracted_text.extend([f"[Page {page_num + 1}]"] + page_text)
        
        doc.close()
        return all_extracted_text
        
    except Exception as e:
        return _process_single_page(textract_client, pdf_bytes)