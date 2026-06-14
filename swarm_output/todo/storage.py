"""JSON file storage for Todo items."""

import json
import os
from pathlib import Path
from typing import List, Optional

from .models import TodoItem


DEFAULT_STORAGE_PATH = os.path.join(os.path.expanduser("~"), ".todos.json")


class TodoStorage:
    """Manages persistence of TodoItems in a JSON file."""

    def __init__(self, filepath: Optional[str] = None) -> None:
        self.filepath = filepath or os.environ.get(
            "TODO_STORAGE_PATH", DEFAULT_STORAGE_PATH
        )
        self._ensure_file()

    def _ensure_file(self) -> None:
        """Create the storage file if it doesn't exist."""
        path = Path(self.filepath)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("[]", encoding="utf-8")

    def _read_all(self) -> list[dict]:
        """Read all todos from the JSON file."""
        try:
            content = Path(self.filepath).read_text(encoding="utf-8")
            return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_all(self, items: list[dict]) -> None:
        """Write all todos to the JSON file."""
        path = Path(self.filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(items, indent=2), encoding="utf-8")

    def list_all(self, status: Optional[str] = None) -> List[TodoItem]:
        """List all todos, optionally filtered by status."""
        data = self._read_all()
        items = [TodoItem.from_dict(d) for d in data]
        if status:
            items = [i for i in items if i.status == status]
        return items

    def get(self, todo_id: str) -> Optional[TodoItem]:
        """Get a single todo by ID."""
        data = self._read_all()
        for d in data:
            if d.get("id") == todo_id:
                return TodoItem.from_dict(d)
        return None

    def add(self, item: TodoItem) -> TodoItem:
        """Add a new todo item."""
        data = self._read_all()
        data.append(item.to_dict())
        self._write_all(data)
        return item

    def update(self, todo_id: str, *, title: Optional[str] = None,
               description: Optional[str] = None) -> Optional[TodoItem]:
        """Update an existing todo's title/description."""
        data = self._read_all()
        for d in data:
            if d["id"] == todo_id:
                item = TodoItem.from_dict(d)
                item.update(title=title, description=description)
                d.update(item.to_dict())
                self._write_all(data)
                return item
        return None

    def complete(self, todo_id: str) -> Optional[TodoItem]:
        """Mark a todo as completed."""
        data = self._read_all()
        for d in data:
            if d["id"] == todo_id:
                item = TodoItem.from_dict(d)
                item.mark_completed()
                d.update(item.to_dict())
                self._write_all(data)
                return item
        return None

    def pend(self, todo_id: str) -> Optional[TodoItem]:
        """Mark a todo as pending."""
        data = self._read_all()
        for d in data:
            if d["id"] == todo_id:
                item = TodoItem.from_dict(d)
                item.mark_pending()
                d.update(item.to_dict())
                self._write_all(data)
                return item
        return None

    def delete(self, todo_id: str) -> bool:
        """Delete a todo by ID. Returns True if deleted, False if not found."""
        data = self._read_all()
        filtered = [d for d in data if d["id"] != todo_id]
        if len(filtered) == len(data):
            return False
        self._write_all(filtered)
        return True

    def count(self, status: Optional[str] = None) -> int:
        """Count todos, optionally filtered by status."""
        return len(self.list_all(status=status))
