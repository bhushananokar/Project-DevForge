from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from models.notebook import Notebook
from models.prompt import GeneratedPrompt
from models.source import Source
from models.user import User
from services import groq_service
from services.auth_service import get_current_user
from services.prompt_builder import build_inputs_payload, inputs_from_text
from models.schemas import ProcessedInput, InputType

router = APIRouter(prefix="/notebooks", tags=["prompts"])


class GenerateRequest(BaseModel):
    target_agent: str = "Claude Code"
    additional_context: str | None = None
    base_prompt: str | None = None  # user's own starting prompt / constraints


def _prompt_out(p: GeneratedPrompt) -> dict:
    return {
        "id": str(p.id),
        "prompt": p.prompt,
        "summary": p.summary,
        "estimated_complexity": p.estimated_complexity,
        "input_sources": p.input_sources,
        "target_agent": p.target_agent,
        "created_at": p.created_at.isoformat(),
    }


async def _get_owned_notebook(notebook_id: str, user: User) -> Notebook:
    try:
        nb = await Notebook.get(notebook_id)
    except Exception:
        nb = None
    if not nb or nb.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notebook not found.")
    return nb


@router.get("/{notebook_id}/prompts")
async def list_prompts(notebook_id: str, user: User = Depends(get_current_user)):
    nb = await _get_owned_notebook(notebook_id, user)
    prompts = (
        await GeneratedPrompt.find(GeneratedPrompt.notebook_id == nb.id)
        .sort("-created_at")
        .to_list()
    )
    return [_prompt_out(p) for p in prompts]


@router.get("/{notebook_id}/prompts/{prompt_id}")
async def get_prompt(
    notebook_id: str, prompt_id: str, user: User = Depends(get_current_user)
):
    nb = await _get_owned_notebook(notebook_id, user)
    try:
        p = await GeneratedPrompt.get(prompt_id)
    except Exception:
        p = None
    if not p or p.notebook_id != nb.id:
        raise HTTPException(status_code=404, detail="Prompt not found.")
    return _prompt_out(p)


@router.post("/{notebook_id}/prompts/generate", status_code=status.HTTP_201_CREATED)
async def generate_prompt(
    notebook_id: str,
    body: GenerateRequest,
    user: User = Depends(get_current_user),
):
    nb = await _get_owned_notebook(notebook_id, user)

    sources = await Source.find(Source.notebook_id == nb.id).sort("created_at").to_list()
    if not sources:
        raise HTTPException(
            status_code=422,
            detail="No sources in this notebook. Add at least one source before generating.",
        )

    # Build ProcessedInput list from stored sources
    processed = [
        ProcessedInput(
            input_type=InputType(s.type),
            source_label=s.source_label,
            content=s.content,
        )
        for s in sources
    ]

    if body.additional_context:
        processed.append(inputs_from_text(body.additional_context, "additional-context"))

    payload = build_inputs_payload(processed)

    try:
        result = groq_service.generate_coding_prompt(
            collected_inputs=payload,
            target_agent=body.target_agent,
            base_prompt=body.base_prompt,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq generation error: {e}")

    p = GeneratedPrompt(
        notebook_id=nb.id,
        user_id=user.id,
        prompt=result["prompt"],
        summary=result["summary"],
        estimated_complexity=result["estimated_complexity"],
        input_sources=result["input_sources"],
        target_agent=body.target_agent,
    )
    await p.insert()
    return _prompt_out(p)
