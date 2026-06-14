"""
LLM service — backed by OpenAI.

Whisper-1       : audio transcription
gpt-4o          : vision (handwritten notes / diagrams)
gpt-4o-mini     : text synthesis (transcript cleaning, prompt generation)
"""

import base64
import json
import os
import re
from pathlib import Path

from openai import OpenAI

VISION_MODEL = "gpt-4o"
TEXT_MODEL   = "gpt-4o-mini"
AUDIO_MODEL  = "whisper-1"

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set")
        _client = OpenAI(api_key=api_key)
    return _client


# ── Audio transcription ───────────────────────────────────────────────────────

def transcribe_audio(file_bytes: bytes, filename: str) -> dict:
    client = get_client()

    transcription = client.audio.transcriptions.create(
        file=(filename, file_bytes),
        model=AUDIO_MODEL,
        response_format="verbose_json",
    )

    return {
        "text": transcription.text,
        "language": getattr(transcription, "language", None),
        "duration": getattr(transcription, "duration", None),
    }


# ── Image / handwritten note analysis ────────────────────────────────────────

def analyze_image(file_bytes: bytes, filename: str) -> dict:
    client = get_client()

    ext = Path(filename).suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png",  ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_map.get(ext, "image/jpeg")
    b64 = base64.b64encode(file_bytes).decode()
    data_url = f"data:{mime_type};base64,{b64}"

    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {
                        "type": "text",
                        "text": (
                            "You are analyzing an image that may contain handwritten notes, "
                            "diagrams, drawings, or sketches related to software development.\n\n"
                            "Provide a structured analysis with three sections:\n\n"
                            "1. EXTRACTED TEXT: Transcribe ALL visible text verbatim.\n\n"
                            "2. VISUAL DESCRIPTION: Describe all diagrams, flowcharts, wireframes, "
                            "or architecture sketches in detail.\n\n"
                            "3. TECHNICAL ELEMENTS: List all technical items identified — "
                            "component names, API endpoints, database tables, user flows, "
                            "data structures, algorithms.\n\n"
                            "Be thorough — this will be used to reconstruct the full technical intent."
                        ),
                    },
                ],
            }
        ],
        max_tokens=2048,
    )

    raw = response.choices[0].message.content or ""
    extracted_text    = _extract_section(raw, "EXTRACTED TEXT")
    visual_description = _extract_section(raw, "VISUAL DESCRIPTION")
    tech_section       = _extract_section(raw, "TECHNICAL ELEMENTS")
    technical_elements = [
        line.lstrip("•-*0123456789. ").strip()
        for line in tech_section.splitlines()
        if line.strip()
    ]

    return {
        "extracted_text": extracted_text,
        "visual_description": visual_description,
        "technical_elements": technical_elements,
        "raw_analysis": raw,
    }


# ── Meeting transcript cleaning ───────────────────────────────────────────────

def clean_transcript(raw_transcript: str) -> dict:
    client = get_client()

    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert at processing meeting transcripts and extracting "
                    "technical requirements for software development. "
                    "Clean up the transcript, remove filler words, and identify "
                    "all actionable technical decisions made."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Process this meeting transcript:\n\n{raw_transcript}\n\n"
                    "Return two sections:\n\n"
                    "CLEANED TRANSCRIPT:\n"
                    "<Clean, readable version with filler words removed and key decisions highlighted>\n\n"
                    "KEY POINTS:\n"
                    "<Bullet-point list of every technical decision, requirement, feature, "
                    "constraint, or open question mentioned>"
                ),
            },
        ],
        max_tokens=4096,
    )

    raw = response.choices[0].message.content or ""
    cleaned = _extract_section(raw, "CLEANED TRANSCRIPT")
    key_points_text = _extract_section(raw, "KEY POINTS")
    key_points = [
        line.lstrip("•-*0123456789. ").strip()
        for line in key_points_text.splitlines()
        if line.strip()
    ]

    return {"cleaned_transcript": cleaned, "key_points": key_points}


# ── Coding agent prompt synthesis ─────────────────────────────────────────────

def generate_coding_prompt(
    collected_inputs: list[dict],
    target_agent: str = "Claude Code",
    additional_context: str | None = None,
    base_prompt: str | None = None,
) -> dict:
    client = get_client()

    inputs_block = "\n\n".join(
        f"--- SOURCE: {inp['source_label']} (type: {inp['input_type']}) ---\n{inp['content']}"
        for inp in collected_inputs
    )

    if additional_context:
        inputs_block += f"\n\n--- ADDITIONAL CONTEXT ---\n{additional_context}"

    base_section = ""
    if base_prompt and base_prompt.strip():
        base_section = f"""
---

The user has provided a BASE PROMPT with their own requirements and constraints.
You MUST incorporate and build upon this — it takes priority over any inferences you make:

BASE PROMPT:
{base_prompt.strip()}
"""

    system_prompt = f"""You are an expert software architect and technical writer specializing in \
creating precise, comprehensive prompts for AI coding agents like {target_agent}.

Your job is to synthesize raw, messy inputs (audio transcriptions, handwritten notes, \
meeting discussions, YouTube tutorials, PDFs, etc.) into a single, perfectly structured \
coding agent prompt that contains EVERYTHING the agent needs to implement the project \
correctly on the first attempt.

The output prompt must be detailed, unambiguous, and technically precise."""

    user_prompt = f"""Below are the raw inputs from various sources describing a software project or feature:

{inputs_block}
{base_section}
---

Synthesize all of the above into a single, comprehensive coding agent prompt.

Structure your output EXACTLY as follows:

## PROJECT OVERVIEW
<2-3 sentences describing what is being built and its core purpose>

## TECHNICAL STACK
<Languages, frameworks, libraries, databases, APIs — infer from context or recommend>

## ARCHITECTURE & DESIGN
<System architecture, component structure, data flow, key design decisions>

## DETAILED REQUIREMENTS

### Functional Requirements
<Numbered list of every feature and behavior the system must have>

### Non-Functional Requirements
<Performance, security, scalability, UX constraints>

## IMPLEMENTATION TASKS
<Ordered, numbered list of specific steps the coding agent should follow.
Each task must be concrete enough that the agent knows exactly what file to create/modify>

## DATA MODELS & SCHEMAS
<All data structures, database schemas, API contracts, or type definitions needed>

## API / INTERFACE SPECIFICATION
<All endpoints with inputs/outputs/errors — or UI component specs if frontend>

## EDGE CASES & CONSTRAINTS
<Known edge cases to handle, things to avoid, gotchas from the source material>

## SUCCESS CRITERIA
<How to verify the implementation is correct and complete>

---

After the full prompt, add a short JSON block:
```json
{{
  "summary": "<one sentence summary>",
  "estimated_complexity": "<low|medium|high>",
  "input_sources": [<list of source labels used>]
}}
```"""

    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        max_tokens=8192,
        temperature=0.3,
    )

    full_response = response.choices[0].message.content or ""

    prompt_text = full_response
    summary    = "Coding agent prompt generated from multimodal inputs."
    complexity = "medium"
    sources    = [inp["source_label"] for inp in collected_inputs]

    json_match = re.search(r"```json\s*(\{.*?\})\s*```", full_response, re.DOTALL)
    if json_match:
        try:
            meta       = json.loads(json_match.group(1))
            summary    = meta.get("summary", summary)
            complexity = meta.get("estimated_complexity", complexity)
            sources    = meta.get("input_sources", sources)
            prompt_text = full_response[: json_match.start()].strip()
        except json.JSONDecodeError:
            pass

    return {
        "prompt": prompt_text,
        "summary": summary,
        "estimated_complexity": complexity,
        "input_sources": sources,
    }


# ── helpers ───────────────────────────────────────────────────────────────────

def _extract_section(text: str, section_name: str) -> str:
    pattern = rf"(?:^|\n)[#\d.\s]*{re.escape(section_name)}[:\s]*\n(.*?)(?=\n[#\d.\s]*[A-Z][A-Z\s]+[:\n]|$)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text.strip()
