"""
File Upload API Endpoints
"""
import logging
from typing import Dict
from fastapi import APIRouter, UploadFile, File, HTTPException
from werkzeug.utils import secure_filename

from app.services.document_service import DocumentService
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize document service
document_service = DocumentService()


@router.post("/file")
async def upload_file(file: UploadFile = File(...)) -> Dict:
    """
    Upload a PDF or PPTX file and extract questions from it
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file extension
        allowed_extensions = {'.pdf', '.pptx'}
        file_ext = '.' + file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Save file
        filename = secure_filename(file.filename)
        file_path = settings.UPLOAD_FOLDER / filename
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"File uploaded: {filename}")
        
        # Extract text and generate questions
        questions = await document_service.process_document(file_path)
        
        return {"questions": questions}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
