from datetime import datetime, timezone
from typing import Literal
from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel

SourceType = Literal["audio", "image", "youtube", "transcript", "text", "pdf"]


class Source(Document):
    notebook_id: PydanticObjectId
    user_id: PydanticObjectId
    type: SourceType
    source_label: str
    content: str  # processed/extracted text
    metadata: dict = Field(default_factory=dict)  # duration, video_id, etc.
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "sources"
        indexes = [
            IndexModel([("notebook_id", ASCENDING)]),
            IndexModel([("user_id", ASCENDING)]),
        ]
