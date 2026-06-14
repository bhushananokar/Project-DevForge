"""Data models for the Todo application."""

from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field, asdict
import uuid


@dataclass
class TodoItem:
    """A single todo item."""

    title: str
    description: str = ""
    status: str = "pending"  # pending | completed
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    VALID_STATUSES = ("pending", "completed")

    def mark_completed(self) -> None:
        """Mark the todo as completed."""
        self.status = "completed"
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def mark_pending(self) -> None:
        """Mark the todo as pending."""
        self.status = "pending"
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def update(self, *, title: Optional[str] = None,
               description: Optional[str] = None) -> None:
        """Update title and/or description."""
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TodoItem":
        """Create a TodoItem from a dictionary."""
        return cls(**data)
