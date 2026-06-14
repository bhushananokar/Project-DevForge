"""CLI entry point for the Todo application."""

import argparse
import sys
from typing import Optional

from .models import TodoItem
from .storage import TodoStorage


def _format_item(item: TodoItem) -> str:
    """Format a single todo for display."""
    status_icon = "✓" if item.status == "completed" else "○"
    desc = f" -- {item.description}" if item.description else ""
    return f"[{item.id}] {status_icon} {item.title}{desc}"


def cmd_add(storage: TodoStorage, args: argparse.Namespace) -> int:
    """Handle the 'add' command."""
    item = TodoItem(title=args.title, description=args.description or "")
    storage.add(item)
    print(f"Added: {_format_item(item)}")
    return 0


def cmd_list(storage: TodoStorage, args: argparse.Namespace) -> int:
    """Handle the 'list' command."""
    status = args.status if hasattr(args, 'status') else None
    items = storage.list_all(status=status)
    if not items:
        print("No todos found.")
        return 0
    print(f"Todos ({len(items)}):")
    for item in items:
        print(f"  {_format_item(item)}")
    return 0


def cmd_complete(storage: TodoStorage, args: argparse.Namespace) -> int:
    """Handle the 'complete' command."""
    item = storage.complete(args.id)
    if item is None:
        print(f"Error: Todo '{args.id}' not found.", file=sys.stderr)
        return 1
    print(f"Completed: {_format_item(item)}")
    return 0


def cmd_pend(storage: TodoStorage, args: argparse.Namespace) -> int:
    """Handle the 'pend' command."""
    item = storage.pend(args.id)
    if item is None:
        print(f"Error: Todo '{args.id}' not found.", file=sys.stderr)
        return 1
    print(f"Reopened: {_format_item(item)}")
    return 0


def cmd_delete(storage: TodoStorage, args: argparse.Namespace) -> int:
    """Handle the 'delete' command."""
    ok = storage.delete(args.id)
    if not ok:
        print(f"Error: Todo '{args.id}' not found.", file=sys.stderr)
        return 1
    print(f"Deleted todo '{args.id}'.")
    return 0


def cmd_update(storage: TodoStorage, args: argparse.Namespace) -> int:
    """Handle the 'update' command."""
    item = storage.update(
        args.id, title=args.title, description=args.description
    )
    if item is None:
        print(f"Error: Todo '{args.id}' not found.", file=sys.stderr)
        return 1
    print(f"Updated: {_format_item(item)}")
    return 0


def cmd_get(storage: TodoStorage, args: argparse.Namespace) -> int:
    """Handle the 'get' command."""
    item = storage.get(args.id)
    if item is None:
        print(f"Error: Todo '{args.id}' not found.", file=sys.stderr)
        return 1
    print(_format_item(item))
    print(f"  Status:      {item.status}")
    print(f"  Description: {item.description or '(none)'}")
    print(f"  Created:     {item.created_at}")
    print(f"  Updated:     {item.updated_at}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="todo",
        description="A simple CLI todo app with JSON storage.",
    )
    parser.add_argument(
        "--storage", default=None,
        help="Path to JSON storage file (default: ~/.todos.json)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # add
    p_add = subparsers.add_parser("add", help="Add a new todo")
    p_add.add_argument("title", help="Title of the todo")
    p_add.add_argument("-d", "--description", default="", help="Optional description")

    # list
    p_list = subparsers.add_parser("list", help="List todos")
    p_list.add_argument(
        "-s", "--status", choices=["pending", "completed"],
        default=None, help="Filter by status"
    )

    # complete
    p_complete = subparsers.add_parser("complete", help="Mark a todo as completed")
    p_complete.add_argument("id", help="ID of the todo to complete")

    # pend
    p_pend = subparsers.add_parser("pend", help="Mark a todo as pending (reopen)")
    p_pend.add_argument("id", help="ID of the todo to reopen")

    # delete
    p_delete = subparsers.add_parser("delete", help="Delete a todo")
    p_delete.add_argument("id", help="ID of the todo to delete")

    # update
    p_update = subparsers.add_parser("update", help="Update a todo")
    p_update.add_argument("id", help="ID of the todo to update")
    p_update.add_argument("-t", "--title", default=None, help="New title")
    p_update.add_argument("-d", "--description", default=None, help="New description")

    # get
    p_get = subparsers.add_parser("get", help="Get details of a todo")
    p_get.add_argument("id", help="ID of the todo")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point. Returns exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    storage = TodoStorage(filepath=args.storage)

    command_map = {
        "add": cmd_add,
        "list": cmd_list,
        "complete": cmd_complete,
        "pend": cmd_pend,
        "delete": cmd_delete,
        "update": cmd_update,
        "get": cmd_get,
    }

    handler = command_map.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(storage, args)


if __name__ == "__main__":
    sys.exit(main())
