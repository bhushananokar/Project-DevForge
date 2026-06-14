from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from models.schemas import TranscriptCleanResponse, ProcessedInput
from services import groq_service
from services.prompt_builder import inputs_from_transcript

router = APIRouter(prefix="/process", tags=["process"])


class TranscriptRequest(BaseModel):
    text: str
    label: str = "meeting-transcript"


@router.post("/transcript", response_model=TranscriptCleanResponse)
async def process_transcript(body: TranscriptRequest):
    """
    Submit raw meeting transcript text (copy-pasted from Zoom, Teams, Otter.ai, etc.).
    Returns a cleaned version and a bullet list of extracted technical decisions.
    """
    if not body.text.strip():
        raise HTTPException(status_code=422, detail="Transcript text cannot be empty.")

    if len(body.text) > 200_000:
        raise HTTPException(
            status_code=413,
            detail="Transcript too long (max ~200k characters). Split it into parts.",
        )

    try:
        result = groq_service.clean_transcript(body.text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq processing error: {str(e)}")

    return TranscriptCleanResponse(
        source=body.label,
        cleaned_transcript=result["cleaned_transcript"],
        key_points=result["key_points"],
    )


@router.post("/transcript/as-input", response_model=ProcessedInput)
async def process_transcript_as_input(body: TranscriptRequest):
    """Same as /process/transcript but returns a ProcessedInput ready for /generate."""
    resp = await process_transcript(body)
    return inputs_from_transcript(resp.cleaned_transcript, resp.key_points, resp.source)
