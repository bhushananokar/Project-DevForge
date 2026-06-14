from fastapi import APIRouter, UploadFile, File, HTTPException
from models.schemas import ImageAnalysisResponse, ProcessedInput
from services import groq_service
from services.prompt_builder import inputs_from_image

router = APIRouter(prefix="/process", tags=["process"])

ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("/image", response_model=ImageAnalysisResponse)
async def process_image(file: UploadFile = File(...)):
    """
    Upload a photo of handwritten notes, a whiteboard, or a drawing.
    Returns extracted text, visual description, and identified technical elements
    via Groq vision model.
    Supported formats: jpg, png, gif, webp (max 20 MB).
    """
    content_type = file.content_type or ""
    if content_type not in ALLOWED_IMAGE_TYPES:
        ext = (file.filename or "").rsplit(".", 1)[-1].lower()
        if ext not in {"jpg", "jpeg", "png", "gif", "webp"}:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type '{content_type}'. Upload jpg, png, gif, or webp.",
            )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(file_bytes) // (1024*1024)} MB). Maximum is 20 MB.",
        )

    try:
        result = groq_service.analyze_image(file_bytes, file.filename or "image.jpg")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq vision error: {str(e)}")

    return ImageAnalysisResponse(
        source=file.filename or "uploaded_image",
        extracted_text=result["extracted_text"],
        visual_description=result["visual_description"],
        technical_elements=result["technical_elements"],
    )


@router.post("/image/as-input", response_model=ProcessedInput)
async def process_image_as_input(file: UploadFile = File(...)):
    """Same as /process/image but returns a ProcessedInput ready for /generate."""
    resp = await process_image(file)
    return inputs_from_image(
        {
            "extracted_text": resp.extracted_text,
            "visual_description": resp.visual_description,
            "technical_elements": resp.technical_elements,
        },
        resp.source,
    )
