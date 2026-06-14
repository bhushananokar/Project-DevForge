"""
Assembles ProcessedInput objects into the payload for generate_coding_prompt.
Keeps routers thin — all aggregation logic lives here.
"""
from models.schemas import ProcessedInput, InputType


def build_inputs_payload(inputs: list[ProcessedInput]) -> list[dict]:
    """Convert ProcessedInput Pydantic models to plain dicts for groq_service."""
    return [
        {
            "input_type": inp.input_type.value,
            "source_label": inp.source_label,
            "content": inp.content,
        }
        for inp in inputs
    ]


def inputs_from_audio(transcription: str, filename: str) -> ProcessedInput:
    return ProcessedInput(
        input_type=InputType.audio,
        source_label=filename,
        content=f"[Audio transcription]\n{transcription}",
    )


def inputs_from_image(analysis: dict, filename: str) -> ProcessedInput:
    parts = []
    if analysis.get("extracted_text"):
        parts.append(f"Extracted text:\n{analysis['extracted_text']}")
    if analysis.get("visual_description"):
        parts.append(f"Visual description:\n{analysis['visual_description']}")
    if analysis.get("technical_elements"):
        joined = "\n".join(f"- {el}" for el in analysis["technical_elements"])
        parts.append(f"Technical elements identified:\n{joined}")
    return ProcessedInput(
        input_type=InputType.image,
        source_label=filename,
        content="\n\n".join(parts),
    )


def inputs_from_youtube(transcript_data: dict) -> ProcessedInput:
    return ProcessedInput(
        input_type=InputType.youtube,
        source_label=transcript_data["url"],
        content=f"[YouTube transcript — video {transcript_data['video_id']}]\n{transcript_data['transcript']}",
    )


def inputs_from_transcript(cleaned: str, key_points: list[str], label: str = "meeting-transcript") -> ProcessedInput:
    kp_block = "\n".join(f"- {kp}" for kp in key_points)
    content = f"[Meeting transcript]\n{cleaned}"
    if kp_block:
        content += f"\n\nKey decisions & requirements extracted:\n{kp_block}"
    return ProcessedInput(
        input_type=InputType.transcript,
        source_label=label,
        content=content,
    )


def inputs_from_text(text: str, label: str = "additional-context") -> ProcessedInput:
    return ProcessedInput(
        input_type=InputType.text,
        source_label=label,
        content=text,
    )
