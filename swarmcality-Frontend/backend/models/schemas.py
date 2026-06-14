from pydantic import BaseModel, HttpUrl
from typing import Optional
from enum import Enum


class InputType(str, Enum):
    audio = "audio"
    image = "image"
    youtube = "youtube"
    transcript = "transcript"
    text = "text"
    pdf = "pdf"


class ProcessedInput(BaseModel):
    input_type: InputType
    source_label: str  # filename, URL, or "transcript"
    content: str       # extracted text or description


class AudioTranscriptionResponse(BaseModel):
    source: str
    transcription: str
    duration_seconds: Optional[float] = None
    language: Optional[str] = None


class ImageAnalysisResponse(BaseModel):
    source: str
    extracted_text: str
    visual_description: str
    technical_elements: list[str]


class YouTubeTranscriptResponse(BaseModel):
    url: str
    video_id: str
    title: Optional[str] = None
    transcript: str
    language: Optional[str] = None


class TranscriptCleanResponse(BaseModel):
    source: str
    cleaned_transcript: str
    key_points: list[str]


class GeneratePromptRequest(BaseModel):
    inputs: list[ProcessedInput]
    target_agent: Optional[str] = None  # e.g. "Claude Code", "Cursor", "Devin"
    additional_context: Optional[str] = None


class GeneratePromptResponse(BaseModel):
    prompt: str
    summary: str
    input_sources: list[str]
    estimated_complexity: str  # low / medium / high


class FullGenerateRequest(BaseModel):
    youtube_urls: Optional[list[str]] = None
    transcript_text: Optional[str] = None
    additional_context: Optional[str] = None
    target_agent: Optional[str] = "Claude Code"
