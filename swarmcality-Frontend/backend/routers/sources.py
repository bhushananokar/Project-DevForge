from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from models.notebook import Notebook
from models.source import Source
from models.user import User
from services import groq_service
from services.auth_service import get_current_user
from services.prompt_builder import (
    inputs_from_audio,
    inputs_from_image,
    inputs_from_transcript,
    inputs_from_youtube,
    inputs_from_text,
)
from services.youtube_service import get_transcript

router = APIRouter(prefix="/notebooks", tags=["sources"])

MAX_AUDIO_BYTES = 25 * 1024 * 1024
MAX_IMAGE_BYTES = 20 * 1024 * 1024


# ── shared helpers ────────────────────────────────────────────────────────────

async def _get_owned_notebook(notebook_id: str, user: User) -> Notebook:
    try:
        nb = await Notebook.get(notebook_id)
    except Exception:
        nb = None
    if not nb or nb.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notebook not found.")
    return nb


async def _save_source(nb: Notebook, user: User, processed_input, metadata: dict = {}) -> Source:
    source = Source(
        notebook_id=nb.id,
        user_id=user.id,
        type=processed_input.input_type.value,
        source_label=processed_input.source_label,
        content=processed_input.content,
        metadata=metadata,
    )
    await source.insert()
    nb.updated_at = datetime.now(timezone.utc)
    await nb.save()
    return source


def _source_out(s: Source) -> dict:
    return {
        "id": str(s.id),
        "type": s.type,
        "source_label": s.source_label,
        "metadata": s.metadata,
        "created_at": s.created_at.isoformat(),
    }


# ── list sources ──────────────────────────────────────────────────────────────

@router.get("/{notebook_id}/sources")
async def list_sources(notebook_id: str, user: User = Depends(get_current_user)):
    nb = await _get_owned_notebook(notebook_id, user)
    sources = await Source.find(Source.notebook_id == nb.id).sort("created_at").to_list()
    return [_source_out(s) for s in sources]


# ── add audio ─────────────────────────────────────────────────────────────────

@router.post("/{notebook_id}/sources/audio", status_code=status.HTTP_201_CREATED)
async def add_audio_source(
    notebook_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    nb = await _get_owned_notebook(notebook_id, user)
    file_bytes = await file.read()
    if len(file_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio file exceeds 25 MB limit.")
    try:
        result = groq_service.transcribe_audio(file_bytes, file.filename or "audio.mp3")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Whisper transcription failed: {e}")

    processed = inputs_from_audio(result["text"], file.filename or "audio")
    metadata = {
        k: result.get(k)
        for k in ("language", "duration")
        if result.get(k) is not None
    }
    source = await _save_source(nb, user, processed, metadata)
    return _source_out(source)


# ── add image ─────────────────────────────────────────────────────────────────

@router.post("/{notebook_id}/sources/image", status_code=status.HTTP_201_CREATED)
async def add_image_source(
    notebook_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    nb = await _get_owned_notebook(notebook_id, user)
    file_bytes = await file.read()
    if len(file_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image file exceeds 20 MB limit.")
    try:
        result = groq_service.analyze_image(file_bytes, file.filename or "image.jpg")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Vision analysis failed: {e}")

    processed = inputs_from_image(result, file.filename or "image")
    source = await _save_source(nb, user, processed, {"technical_elements": result["technical_elements"]})
    return _source_out(source)


# ── add YouTube ───────────────────────────────────────────────────────────────

class YouTubeBody(BaseModel):
    url: str


@router.post("/{notebook_id}/sources/youtube", status_code=status.HTTP_201_CREATED)
async def add_youtube_source(
    notebook_id: str,
    body: YouTubeBody,
    user: User = Depends(get_current_user),
):
    nb = await _get_owned_notebook(notebook_id, user)
    try:
        result = get_transcript(body.url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Transcript fetch failed: {e}")

    processed = inputs_from_youtube(result)
    source = await _save_source(nb, user, processed, {"video_id": result["video_id"], "language": result.get("language")})
    return _source_out(source)


# ── add transcript ────────────────────────────────────────────────────────────

class TranscriptBody(BaseModel):
    text: str
    label: str = "meeting-transcript"


@router.post("/{notebook_id}/sources/transcript", status_code=status.HTTP_201_CREATED)
async def add_transcript_source(
    notebook_id: str,
    body: TranscriptBody,
    user: User = Depends(get_current_user),
):
    nb = await _get_owned_notebook(notebook_id, user)
    if not body.text.strip():
        raise HTTPException(status_code=422, detail="Transcript text cannot be empty.")
    try:
        result = groq_service.clean_transcript(body.text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Transcript processing failed: {e}")

    processed = inputs_from_transcript(result["cleaned_transcript"], result["key_points"], body.label)
    source = await _save_source(nb, user, processed, {"key_points": result["key_points"]})
    return _source_out(source)


# ── add plain text ────────────────────────────────────────────────────────────

class TextBody(BaseModel):
    text: str
    label: str = "context"


@router.post("/{notebook_id}/sources/text", status_code=status.HTTP_201_CREATED)
async def add_text_source(
    notebook_id: str,
    body: TextBody,
    user: User = Depends(get_current_user),
):
    nb = await _get_owned_notebook(notebook_id, user)
    if not body.text.strip():
        raise HTTPException(status_code=422, detail="Text cannot be empty.")

    processed = inputs_from_text(body.text, body.label)
    source = await _save_source(nb, user, processed)
    return _source_out(source)


# ── add PDF ───────────────────────────────────────────────────────────────────

MAX_PDF_BYTES = 50 * 1024 * 1024  # 50 MB


@router.post("/{notebook_id}/sources/pdf", status_code=status.HTTP_201_CREATED)
async def add_pdf_source(
    notebook_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """
    Upload a PDF. Text is extracted client-side via pypdf (no external API call needed).
    Supports text-layer PDFs; scanned-only PDFs will return minimal text.
    Max 50 MB.
    """
    nb = await _get_owned_notebook(notebook_id, user)
    file_bytes = await file.read()
    if len(file_bytes) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF exceeds 50 MB limit.")

    try:
        import io
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages_text.append(f"[Page {i + 1}]\n{text.strip()}")

        if not pages_text:
            raise HTTPException(
                status_code=422,
                detail="No extractable text found in this PDF. Scanned PDFs without a text layer are not supported.",
            )

        full_text = "\n\n".join(pages_text)
        page_count = len(reader.pages)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PDF parsing error: {e}")

    from models.schemas import ProcessedInput, InputType
    processed = ProcessedInput(
        input_type=InputType.text,
        source_label=file.filename or "document.pdf",
        content=f"[PDF — {page_count} pages]\n{full_text}",
    )
    # Override type to "pdf" after creating the ProcessedInput
    source = Source(
        notebook_id=nb.id,
        user_id=user.id,
        type="pdf",
        source_label=processed.source_label,
        content=processed.content,
        metadata={"page_count": page_count},
    )
    await source.insert()
    nb.updated_at = datetime.now(timezone.utc)
    await nb.save()
    return _source_out(source)


# ── delete source ─────────────────────────────────────────────────────────────

@router.delete("/{notebook_id}/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    notebook_id: str,
    source_id: str,
    user: User = Depends(get_current_user),
):
    nb = await _get_owned_notebook(notebook_id, user)
    try:
        source = await Source.get(source_id)
    except Exception:
        source = None
    if not source or source.notebook_id != nb.id:
        raise HTTPException(status_code=404, detail="Source not found.")
    await source.delete()
    nb.updated_at = datetime.now(timezone.utc)
    await nb.save()
