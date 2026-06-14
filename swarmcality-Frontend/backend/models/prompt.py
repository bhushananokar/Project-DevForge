from datetime import datetime, timezone
from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel


class GeneratedPrompt(Document):
    notebook_id: PydanticObjectId
    user_id: PydanticObjectId
    prompt: str
    summary: str
    estimated_complexity: str  # low / medium / high
    input_sources: list[str]
    target_agent: str = "Claude Code"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "generated_prompts"
        indexes = [IndexModel([("notebook_id", ASCENDING)])]
