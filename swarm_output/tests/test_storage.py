"""Unit tests for TodoStorage."""

import os
import tempfile
import pytest
from todo.models import TodoItem
from todo.storage import TodoStorage


class TestTodoStorage:
    """Tests for the JSON file storage layer."""

    @pytest.fixture
    def tmpfile(self):
        """Create a temporary JSON file for testing."""
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(path)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def storage(self, tmpfile):
        """Create a storage instance backed by a temp file."""
        return TodoStorage(filepath=tmpfile)

    def test_init_creates_file(self, tmpfile):
        """Storage initialisation creates the JSON file."""
        assert not os.path.exists(tmpfile)
        TodoStorage(filepath=tmpfile)
        assert os.path.exists(tmpfile)

    def test_add_and_list(self, storage):
        """Add items and list them."""
        item = storage.add(TodoItem(title="Task 1"))
        items = storage.list_all()
        assert len(items) == 1
        assert items[0].id == item.id
        assert items[0].title == "Task 1"

    def test_list_empty(self, storage):
        """Listing when no items exist returns an empty list."""
        assert storage.list_all() == []

    def test_list_filter_status(self, storage):
        """Listing with a status filter."""
        storage.add(TodoItem(title="Pending task"))
        completed = storage.add(TodoItem(title="Done task"))
        storage.complete(completed.id)

        pending = storage.list_all(status="pending")
        done = storage.list_all(status="completed")

        assert len(pending) == 1
        assert pending[0].title == "Pending task"
        assert len(done) == 1
        assert done[0].title == "Done task"

    def test_get_existing(self, storage):
        """Get an existing todo by ID."""
        item = storage.add(TodoItem(title="Find me"))
        found = storage.get(item.id)
        assert found is not None
        assert found.id == item.id
        assert found.title == "Find me"

    def test_get_nonexistent(self, storage):
        """Get a non-existent todo returns None."""
        assert storage.get("nonexistent") is None

    def test_update_existing(self, storage):
        """Update an existing todo."""
        item = storage.add(
            TodoItem(title="Old title", description="Old desc")
        )
        updated = storage.update(
            item.id, title="New title", description="New desc"
        )
        assert updated is not None
        assert updated.title == "New title"
        assert updated.description == "New desc"

        fetched = storage.get(item.id)
        assert fetched.title == "New title"

    def test_update_nonexistent(self, storage):
        """Update a non-existent todo returns None."""
        assert storage.update("nope", title="X") is None

    def test_update_partial(self, storage):
        """Update only one field."""
        item = storage.add(TodoItem(title="Old", description="Old"))
        storage.update(item.id, title="Title only")
        fetched = storage.get(item.id)
        assert fetched.title == "Title only"
        assert fetched.description == "Old"

    def test_complete(self, storage):
        """Mark a todo as completed."""
        item = storage.add(TodoItem(title="To complete"))
        result = storage.complete(item.id)
        assert result is not None
        assert result.status == "completed"
        assert storage.get(item.id).status == "completed"

    def test_complete_nonexistent(self, storage):
        """Complete a non-existent todo returns None."""
        assert storage.complete("nope") is None

    def test_pend(self, storage):
        """Mark a completed todo back to pending."""
        item = storage.add(
            TodoItem(title="To reopen", status="completed")
        )
        result = storage.pend(item.id)
        assert result is not None
        assert result.status == "pending"
        assert storage.get(item.id).status == "pending"

    def test_pend_nonexistent(self, storage):
        """Pend a non-existent todo returns None."""
        assert storage.pend("nope") is None

    def test_delete_existing(self, storage):
        """Delete an existing todo."""
        item = storage.add(TodoItem(title="Delete me"))
        assert storage.delete(item.id) is True
        assert storage.get(item.id) is None
        assert storage.list_all() == []

    def test_delete_nonexistent(self, storage):
        """Delete a non-existent todo returns False."""
        assert storage.delete("nope") is False

    def test_count_all(self, storage):
        """Count all todos."""
        storage.add(TodoItem(title="A"))
        storage.add(TodoItem(title="B"))
        assert storage.count() == 2

    def test_count_by_status(self, storage):
        """Count todos filtered by status."""
        c = storage.add(TodoItem(title="C"))
        storage.complete(c.id)
        storage.add(TodoItem(title="D"))
        assert storage.count(status="completed") == 1
        assert storage.count(status="pending") == 1

    def test_data_persists_to_disk(self, storage, tmpfile):
        """Data survives across storage instances."""
        storage.add(TodoItem(title="Persistent"))
        # Create a new storage instance pointing at the same file
        storage2 = TodoStorage(filepath=tmpfile)
        items = storage2.list_all()
        assert len(items) == 1
        assert items[0].title == "Persistent"

    def test_corrupt_file_is_handled(self, tmpfile):
        """A corrupt JSON file is treated as empty."""
        with open(tmpfile, "w") as f:
            f.write("this is not valid json{{{")
        storage = TodoStorage(filepath=tmpfile)
        assert storage.list_all() == []

    def test_environment_variable_path(self, monkeypatch, tmpfile):
        """Storage respects TODO_STORAGE_PATH env var."""
        monkeypatch.setenv("TODO_STORAGE_PATH", tmpfile)
        storage = TodoStorage(filepath=None)
        storage.add(TodoItem(title="Env test"))
        assert os.path.exists(tmpfile)
