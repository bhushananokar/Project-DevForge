from fastapi import APIRouter, UploadFile, File, HTTPException
from models.schemas import AudioTranscriptionResponse, ProcessedInput
from services import groq_service
from services.prompt_builder import inputs_from_audio

router = APIRouter(prefix="/process", tags=["process"])

ALLOWED_AUDIO_TYPES = {
    "audio/mpeg", "audio/mp4", "audio/wav", "audio/x-wav",
    "audio/webm", "audio/ogg", "audio/flac", "audio/m4a",
    "audio/x-m4a", "video/mp4", "video/webm",
}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB — Groq Whisper limit


@router.post("/audio", response_model=AudioTranscriptionResponse)
async def process_audio(file: UploadFile = File(...)):
    """
    Upload an audio or video file. Returns a Whisper transcription via Groq Cloud.
    Supported formats: mp3, mp4, wav, webm, ogg, flac, m4a (max 25 MB).
    """
    content_type = file.content_type or ""
    if content_type not in ALLOWED_AUDIO_TYPES:
        # also accept if extension matches even if content-type is wrong
        ext = (file.filename or "").rsplit(".", 1)[-1].lower()
        if ext not in {"mp3", "mp4", "wav", "webm", "ogg", "flac", "m4a"}:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type '{content_type}'. Upload mp3, mp4, wav, webm, ogg, flac, or m4a.",
            )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(file_bytes) // (1024*1024)} MB). Maximum is 25 MB.",
        )

    try:
        result = groq_service.transcribe_audio(file_bytes, file.filename or "audio.mp3")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq Whisper error: {str(e)}")

    return AudioTranscriptionResponse(
        source=file.filename or "uploaded_audio",
        transcription=result["text"],
        duration_seconds=result.get("duration"),
        language=result.get("language"),
    )


@router.post("/audio/as-input", response_model=ProcessedInput)
async def process_audio_as_input(file: UploadFile = File(...)):
    """Same as /process/audio but returns a ProcessedInput ready for /generate."""
    resp = await process_audio(file)
    return inputs_from_audio(resp.transcription, resp.source)
