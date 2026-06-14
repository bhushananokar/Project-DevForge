from datetime import datetime, timezone
from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel


class Notebook(Document):
    user_id: PydanticObjectId
    name: str
    description: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "notebooks"
        indexes = [IndexModel([("user_id", ASCENDING)])]
