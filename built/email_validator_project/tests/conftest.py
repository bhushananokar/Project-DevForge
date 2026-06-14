"""Pytest configuration – ensures the app package is on sys.path."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "app"
_ROOT = _SRC.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
