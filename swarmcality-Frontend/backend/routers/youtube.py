from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from models.schemas import YouTubeTranscriptResponse, ProcessedInput
from services.youtube_service import get_transcript
from services.prompt_builder import inputs_from_youtube

router = APIRouter(prefix="/process", tags=["process"])


class YouTubeRequest(BaseModel):
    url: str


class YouTubeBatchRequest(BaseModel):
    urls: list[str]


@router.post("/youtube", response_model=YouTubeTranscriptResponse)
async def process_youtube(body: YouTubeRequest):
    """
    Fetch the transcript/captions from a YouTube video URL.
    Works with auto-generated and manual captions.
    Falls back to auto-translated English if no English captions are available.
    """
    try:
        result = get_transcript(body.url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Transcript fetch error: {str(e)}")

    return YouTubeTranscriptResponse(
        url=result["url"],
        video_id=result["video_id"],
        transcript=result["transcript"],
        language=result.get("language"),
    )


@router.post("/youtube/batch", response_model=list[YouTubeTranscriptResponse])
async def process_youtube_batch(body: YouTubeBatchRequest):
    """Fetch transcripts for multiple YouTube URLs at once."""
    results = []
    errors = []
    for url in body.urls:
        try:
            result = get_transcript(url)
            results.append(
                YouTubeTranscriptResponse(
                    url=result["url"],
                    video_id=result["video_id"],
                    transcript=result["transcript"],
                    language=result.get("language"),
                )
            )
        except (ValueError, Exception) as e:
            errors.append(f"{url}: {str(e)}")

    if errors and not results:
        raise HTTPException(status_code=422, detail={"errors": errors})

    return results


@router.post("/youtube/as-input", response_model=ProcessedInput)
async def process_youtube_as_input(body: YouTubeRequest):
    """Same as /process/youtube but returns a ProcessedInput ready for /generate."""
    try:
        result = get_transcript(body.url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Transcript fetch error: {str(e)}")
    return inputs_from_youtube(result)
