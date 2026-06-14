from datetime import datetime, timezone
from beanie import Document
from pydantic import Field
from pymongo import ASCENDING, IndexModel


class User(Document):
    email: str
    name: str
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
        indexes = [IndexModel([("email", ASCENDING)], unique=True)]
