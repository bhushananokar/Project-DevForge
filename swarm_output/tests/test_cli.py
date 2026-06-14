"""Unit tests for CLI module."""

import pytest
from unittest.mock import MagicMock

from todo.cli import (
    main,
    build_parser,
    _format_item,
    cmd_add,
    cmd_list,
    cmd_complete,
    cmd_pend,
    cmd_delete,
    cmd_update,
    cmd_get,
)
from todo.models import TodoItem


class TestFormatItem:
    """Tests for the _format_item helper."""

    def test_pending_no_description(self):
        item = TodoItem(title="Test", id="abc123")
        result = _format_item(item)
        assert "[abc123]" in result
        assert "\u25cb" in result
        assert "Test" in result

    def test_completed_with_description(self):
        item = TodoItem(
            title="Done",
            description="well done",
            status="completed",
            id="xyz",
        )
        result = _format_item(item)
        assert "\u2713" in result
        assert "Done" in result
        assert "well done" in result


class TestCLI:
    """Integration-style tests for CLI commands."""

    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage."""
        return MagicMock()

    def test_main_no_command_shows_help(self, capsys):
        """Running with no command prints help."""
        exit_code = main([])
        out = capsys.readouterr().out
        assert "usage:" in out or "positional arguments:" in out
        assert exit_code == 0

    def test_main_invalid_command(self, capsys):
        """Invalid command shows help and exits 1."""
        with pytest.raises(SystemExit):
            main(["bogus"])

    def test_cmd_add(self, mock_storage, capsys):
        """cmd_add creates a todo and prints it."""
        mock_storage.add.return_value = TodoItem(title="Hello", id="abc")
        exit_code = cmd_add(
            mock_storage, MagicMock(title="Hello", description="World")
        )
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "Added:" in out
        assert "Hello" in out
        mock_storage.add.assert_called_once()

    def test_cmd_list_empty(self, mock_storage, capsys):
        """cmd_list with no items."""
        mock_storage.list_all.return_value = []
        exit_code = cmd_list(mock_storage, MagicMock(status=None))
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "No todos found." in out

    def test_cmd_list_with_items(self, mock_storage, capsys):
        """cmd_list with items."""
        items = [
            TodoItem(title="A", id="1"),
            TodoItem(title="B", id="2"),
        ]
        mock_storage.list_all.return_value = items
        exit_code = cmd_list(mock_storage, MagicMock(status=None))
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "Todos (2):" in out
        assert "A" in out
        assert "B" in out

    def test_cmd_complete_success(self, mock_storage, capsys):
        """cmd_complete finds the item."""
        mock_storage.complete.return_value = TodoItem(
            title="Done", id="x", status="completed"
        )
        exit_code = cmd_complete(mock_storage, MagicMock(id="x"))
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "Completed:" in out

    def test_cmd_complete_not_found(self, mock_storage, capsys):
        """cmd_complete when item doesn't exist."""
        mock_storage.complete.return_value = None
        exit_code = cmd_complete(mock_storage, MagicMock(id="x"))
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "not found" in err

    def test_cmd_pend_success(self, mock_storage, capsys):
        """cmd_pend finds the item."""
        mock_storage.pend.return_value = TodoItem(
            title="Reopened", id="r", status="pending"
        )
        exit_code = cmd_pend(mock_storage, MagicMock(id="r"))
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "Reopened:" in out

    def test_cmd_pend_not_found(self, mock_storage, capsys):
        """cmd_pend when item doesn't exist."""
        mock_storage.pend.return_value = None
        exit_code = cmd_pend(mock_storage, MagicMock(id="x"))
        assert exit_code == 1

    def test_cmd_delete_success(self, mock_storage, capsys):
        """cmd_delete removes the item."""
        mock_storage.delete.return_value = True
        exit_code = cmd_delete(mock_storage, MagicMock(id="d"))
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "Deleted" in out

    def test_cmd_delete_not_found(self, mock_storage, capsys):
        """cmd_delete when item doesn't exist."""
        mock_storage.delete.return_value = False
        exit_code = cmd_delete(mock_storage, MagicMock(id="d"))
        assert exit_code == 1

    def test_cmd_update_success(self, mock_storage, capsys):
        """cmd_update changes the item."""
        mock_storage.update.return_value = TodoItem(
            title="Updated", id="u"
        )
        exit_code = cmd_update(
            mock_storage,
            MagicMock(id="u", title="Updated", description=None),
        )
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "Updated:" in out

    def test_cmd_update_not_found(self, mock_storage, capsys):
        """cmd_update when item doesn't exist."""
        mock_storage.update.return_value = None
        exit_code = cmd_update(
            mock_storage,
            MagicMock(id="x", title="X", description=None),
        )
        assert exit_code == 1

    def test_cmd_get_success(self, mock_storage, capsys):
        """cmd_get shows full details."""
        mock_storage.get.return_value = TodoItem(
            title="Detail",
            description="Full desc",
            id="g",
        )
        exit_code = cmd_get(mock_storage, MagicMock(id="g"))
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "Detail" in out
        assert "Full desc" in out
        assert "Status:" in out
        assert "Created:" in out
        assert "Updated:" in out

    def test_cmd_get_not_found(self, mock_storage, capsys):
        """cmd_get when item doesn't exist."""
        mock_storage.get.return_value = None
        exit_code = cmd_get(mock_storage, MagicMock(id="x"))
        assert exit_code == 1


class TestArgParser:
    """Tests for the argument parser configuration."""

    def test_parser_add(self):
        parser = build_parser()
        args = parser.parse_args(
            ["add", "Buy milk", "-d", "from store"]
        )
        assert args.command == "add"
        assert args.title == "Buy milk"
        assert args.description == "from store"

    def test_parser_list(self):
        parser = build_parser()
        args = parser.parse_args(["list"])
        assert args.command == "list"
        assert args.status is None

    def test_parser_list_filtered(self):
        parser = build_parser()
        args = parser.parse_args(["list", "-s", "completed"])
        assert args.command == "list"
        assert args.status == "completed"

    def test_parser_complete(self):
        parser = build_parser()
        args = parser.parse_args(["complete", "abc123"])
        assert args.command == "complete"
        assert args.id == "abc123"

    def test_parser_pend(self):
        parser = build_parser()
        args = parser.parse_args(["pend", "abc123"])
        assert args.command == "pend"
        assert args.id == "abc123"

    def test_parser_delete(self):
        parser = build_parser()
        args = parser.parse_args(["delete", "abc123"])
        assert args.command == "delete"
        assert args.id == "abc123"

    def test_parser_update(self):
        parser = build_parser()
        args = parser.parse_args(
            ["update", "abc", "-t", "New Title", "-d", "New Desc"]
        )
        assert args.command == "update"
        assert args.id == "abc"
        assert args.title == "New Title"
        assert args.description == "New Desc"

    def test_parser_get(self):
        parser = build_parser()
        args = parser.parse_args(["get", "abc123"])
        assert args.command == "get"
        assert args.id == "abc123"

    def test_parser_storage_option(self):
        parser = build_parser()
        args = parser.parse_args(
            ["--storage", "/tmp/test.json", "list"]
        )
        assert args.storage == "/tmp/test.json"
