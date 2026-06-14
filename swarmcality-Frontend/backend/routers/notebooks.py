from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from models.notebook import Notebook
from models.source import Source
from models.prompt import GeneratedPrompt
from models.user import User
from services.auth_service import get_current_user

router = APIRouter(prefix="/notebooks", tags=["notebooks"])


class NotebookCreate(BaseModel):
    name: str
    description: str = ""


class NotebookUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


def _notebook_out(nb: Notebook, source_count: int = 0) -> dict:
    return {
        "id": str(nb.id),
        "name": nb.name,
        "description": nb.description,
        "source_count": source_count,
        "created_at": nb.created_at.isoformat(),
        "updated_at": nb.updated_at.isoformat(),
    }


@router.get("")
async def list_notebooks(user: User = Depends(get_current_user)):
    notebooks = await Notebook.find(Notebook.user_id == user.id).sort("-updated_at").to_list()
    result = []
    for nb in notebooks:
        count = await Source.find(Source.notebook_id == nb.id).count()
        result.append(_notebook_out(nb, count))
    return result


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_notebook(body: NotebookCreate, user: User = Depends(get_current_user)):
    nb = Notebook(user_id=user.id, name=body.name.strip(), description=body.description.strip())
    await nb.insert()
    return _notebook_out(nb)


@router.get("/{notebook_id}")
async def get_notebook(notebook_id: str, user: User = Depends(get_current_user)):
    nb = await _get_owned(notebook_id, user)
    sources = await Source.find(Source.notebook_id == nb.id).sort("created_at").to_list()
    latest_prompt = await GeneratedPrompt.find(
        GeneratedPrompt.notebook_id == nb.id
    ).sort("-created_at").first_or_none()

    return {
        **_notebook_out(nb, len(sources)),
        "sources": [_source_out(s) for s in sources],
        "latest_prompt": _prompt_out(latest_prompt) if latest_prompt else None,
    }


@router.patch("/{notebook_id}")
async def update_notebook(
    notebook_id: str, body: NotebookUpdate, user: User = Depends(get_current_user)
):
    nb = await _get_owned(notebook_id, user)
    if body.name is not None:
        nb.name = body.name.strip()
    if body.description is not None:
        nb.description = body.description.strip()
    nb.updated_at = datetime.now(timezone.utc)
    await nb.save()
    return _notebook_out(nb)


@router.delete("/{notebook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notebook(notebook_id: str, user: User = Depends(get_current_user)):
    nb = await _get_owned(notebook_id, user)
    await Source.find(Source.notebook_id == nb.id).delete()
    await GeneratedPrompt.find(GeneratedPrompt.notebook_id == nb.id).delete()
    await nb.delete()


# ── helpers ──────────────────────────────────────────────────────────────────

async def _get_owned(notebook_id: str, user: User) -> Notebook:
    try:
        nb = await Notebook.get(notebook_id)
    except Exception:
        nb = None
    if not nb or nb.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notebook not found.")
    return nb


def _source_out(s: Source) -> dict:
    return {
        "id": str(s.id),
        "type": s.type,
        "source_label": s.source_label,
        "metadata": s.metadata,
        "created_at": s.created_at.isoformat(),
    }


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
