from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Annotated, Optional
import json

from models.schemas import (
    GeneratePromptRequest,
    GeneratePromptResponse,
    ProcessedInput,
    InputType,
)
from services import groq_service
from services import youtube_service
from services.prompt_builder import (
    build_inputs_payload,
    inputs_from_audio,
    inputs_from_image,
    inputs_from_youtube,
    inputs_from_transcript,
    inputs_from_text,
)

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("/prompt", response_model=GeneratePromptResponse)
async def generate_prompt(body: GeneratePromptRequest):
    """
    Core endpoint. Accepts a list of already-processed inputs
    (from /process/* endpoints) and returns a detailed coding agent prompt.

    Workflow:
    1. Call /process/audio, /process/image, /process/youtube, /process/transcript
       (use the /as-input variants to get ProcessedInput objects directly)
    2. Collect all ProcessedInput objects
    3. POST them here as { "inputs": [...], "target_agent": "Claude Code" }
    """
    if not body.inputs:
        raise HTTPException(status_code=422, detail="At least one input is required.")

    payload = build_inputs_payload(body.inputs)

    try:
        result = groq_service.generate_coding_prompt(
            collected_inputs=payload,
            target_agent=body.target_agent or "Claude Code",
            additional_context=body.additional_context,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq generation error: {str(e)}")

    return GeneratePromptResponse(
        prompt=result["prompt"],
        summary=result["summary"],
        input_sources=result["input_sources"],
        estimated_complexity=result["estimated_complexity"],
    )


@router.post("/full", response_model=GeneratePromptResponse)
async def generate_full(
    audio_files: Annotated[list[UploadFile], File()] = [],
    image_files: Annotated[list[UploadFile], File()] = [],
    youtube_urls: Annotated[Optional[str], Form()] = None,   # JSON array string
    transcript_text: Annotated[Optional[str], Form()] = None,
    additional_context: Annotated[Optional[str], Form()] = None,
    target_agent: Annotated[str, Form()] = "Claude Code",
):
    """
    All-in-one convenience endpoint. Upload everything in one multipart request.

    Form fields:
    - audio_files: one or more audio/video files (Whisper transcription)
    - image_files: one or more image files (handwritten notes, diagrams)
    - youtube_urls: JSON array of YouTube URLs, e.g. '["https://youtu.be/xxx"]'
    - transcript_text: raw meeting transcript (plain text)
    - additional_context: any free-text context
    - target_agent: name of the coding agent (default: "Claude Code")

    Returns the assembled coding agent prompt.
    """
    collected: list[ProcessedInput] = []
    errors: list[str] = []

    # --- Audio files ---
    for f in audio_files:
        if not f.filename:
            continue
        try:
            file_bytes = await f.read()
            result = groq_service.transcribe_audio(file_bytes, f.filename)
            collected.append(inputs_from_audio(result["text"], f.filename))
        except Exception as e:
            errors.append(f"Audio '{f.filename}': {e}")

    # --- Image files ---
    for f in image_files:
        if not f.filename:
            continue
        try:
            file_bytes = await f.read()
            result = groq_service.analyze_image(file_bytes, f.filename)
            collected.append(inputs_from_image(result, f.filename))
        except Exception as e:
            errors.append(f"Image '{f.filename}': {e}")

    # --- YouTube URLs ---
    if youtube_urls:
        try:
            urls: list[str] = json.loads(youtube_urls)
        except json.JSONDecodeError:
            # Accept a single bare URL too
            urls = [youtube_urls.strip()]

        for url in urls:
            try:
                result = youtube_service.get_transcript(url)
                collected.append(inputs_from_youtube(result))
            except Exception as e:
                errors.append(f"YouTube '{url}': {e}")

    # --- Meeting transcript ---
    if transcript_text and transcript_text.strip():
        try:
            result = groq_service.clean_transcript(transcript_text)
            collected.append(
                inputs_from_transcript(
                    result["cleaned_transcript"],
                    result["key_points"],
                )
            )
        except Exception as e:
            errors.append(f"Transcript processing: {e}")

    # --- Additional context (raw text) ---
    if additional_context and additional_context.strip():
        collected.append(inputs_from_text(additional_context))

    if not collected:
        detail = "No inputs could be processed."
        if errors:
            detail += " Errors: " + "; ".join(errors)
        raise HTTPException(status_code=422, detail=detail)

    try:
        result = groq_service.generate_coding_prompt(
            collected_inputs=build_inputs_payload(collected),
            target_agent=target_agent,
            additional_context=None,  # already included above
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq generation error: {str(e)}")

    response = GeneratePromptResponse(
        prompt=result["prompt"],
        summary=result["summary"],
        input_sources=result["input_sources"],
        estimated_complexity=result["estimated_complexity"],
    )

    # Attach non-fatal errors as a header so clients can inspect them
    # (FastAPI Response object not needed — returned via response_model)
    return response
