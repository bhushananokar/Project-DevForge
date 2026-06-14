"""Unit tests for TodoItem model."""

import time
from todo.models import TodoItem


class TestTodoItem:
    """Tests for the TodoItem data class."""

    def test_create_minimal(self):
        """Create a todo with only a title."""
        item = TodoItem(title="Buy milk")
        assert item.title == "Buy milk"
        assert item.description == ""
        assert item.status == "pending"
        assert len(item.id) == 12
        assert item.created_at is not None
        assert item.updated_at is not None

    def test_create_with_description(self):
        """Create a todo with title and description."""
        item = TodoItem(title="Buy milk", description="2% from Safeway")
        assert item.title == "Buy milk"
        assert item.description == "2% from Safeway"
        assert item.status == "pending"

    def test_id_uniqueness(self):
        """Each todo gets a unique ID."""
        ids = {TodoItem(title=f"Task {i}").id for i in range(100)}
        assert len(ids) == 100

    def test_mark_completed(self):
        """Marking an item as completed."""
        item = TodoItem(title="Test")
        old_updated = item.updated_at
        time.sleep(0.001)
        item.mark_completed()
        assert item.status == "completed"
        assert item.updated_at != old_updated

    def test_mark_pending(self):
        """Marking an item back to pending."""
        item = TodoItem(title="Test", status="completed")
        old_updated = item.updated_at
        time.sleep(0.001)
        item.mark_pending()
        assert item.status == "pending"
        assert item.updated_at != old_updated

    def test_update_title_only(self):
        """Update just the title."""
        item = TodoItem(title="Old")
        old_updated = item.updated_at
        time.sleep(0.001)
        item.update(title="New")
        assert item.title == "New"
        assert item.updated_at != old_updated

    def test_update_description_only(self):
        """Update just the description."""
        item = TodoItem(title="Test", description="Old desc")
        old_updated = item.updated_at
        time.sleep(0.001)
        item.update(description="New desc")
        assert item.description == "New desc"
        assert item.title == "Test"
        assert item.updated_at != old_updated

    def test_update_both(self):
        """Update both title and description."""
        item = TodoItem(title="Old T", description="Old D")
        item.update(title="New T", description="New D")
        assert item.title == "New T"
        assert item.description == "New D"

    def test_update_none_does_nothing(self):
        """Calling update with no args changes nothing."""
        item = TodoItem(title="Test")
        old_title = item.title
        old_desc = item.description
        item.update()
        assert item.title == old_title
        assert item.description == old_desc

    def test_to_dict(self):
        """Serialization to dict."""
        item = TodoItem(title="Test", description="Desc")
        d = item.to_dict()
        assert d["title"] == "Test"
        assert d["description"] == "Desc"
        assert d["status"] == "pending"
        assert "id" in d
        assert "created_at" in d
        assert "updated_at" in d

    def test_from_dict(self):
        """Deserialization from dict."""
        original = TodoItem(title="Test", description="Desc")
        restored = TodoItem.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.title == original.title
        assert restored.description == original.description
        assert restored.status == original.status
