import re
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    NoTranscriptFound,
    TranscriptsDisabled,
    CouldNotRetrieveTranscript,
)

_api = YouTubeTranscriptApi()


def extract_video_id(url: str) -> str:
    match = re.search(r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})", url)
    if match:
        return match.group(1)
    raise ValueError(f"Could not extract a YouTube video ID from: {url}")


def get_transcript(url: str) -> dict:
    """
    Fetch transcript for a YouTube video using youtube-transcript-api 1.x.
    Tries English first, falls back to any available language auto-translated to English.
    """
    video_id = extract_video_id(url)

    try:
        transcript_list = _api.list(video_id)

        try:
            transcript = transcript_list.find_transcript(["en", "en-US", "en-GB"])
            lang = "en"
        except NoTranscriptFound:
            available = list(transcript_list)
            if not available:
                raise ValueError(f"No transcripts available for video {video_id}.")
            try:
                transcript = available[0].translate("en")
                lang = f"{available[0].language_code} (auto-translated)"
            except Exception:
                # Translation not available — use the raw transcript
                transcript = available[0]
                lang = available[0].language_code

        # 1.x returns FetchedTranscript whose snippets have a .text attribute
        fetched = transcript.fetch()
        full_text = " ".join(re.sub(r"\s+", " ", snippet.text) for snippet in fetched).strip()

        return {
            "video_id": video_id,
            "url": url,
            "transcript": full_text,
            "language": lang,
            "entry_count": len(fetched),
        }

    except TranscriptsDisabled:
        raise ValueError(
            f"Transcripts are disabled for video '{video_id}'. "
            "The video owner has turned off captions."
        )
    except NoTranscriptFound:
        raise ValueError(
            f"No transcript found for video '{video_id}'. "
            "Try a video with auto-generated or manual captions."
        )
    except CouldNotRetrieveTranscript as e:
        raise ValueError(f"Could not retrieve transcript: {e}")
