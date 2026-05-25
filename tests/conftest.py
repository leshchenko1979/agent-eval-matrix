"""Pytest configuration."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLING_DIR = ROOT / "examples" / "opencrabs" / "tooling"

# examples/opencrabs/tooling hosts `opencrabs` and `fuzzy` packages (one tool per file).
if str(TOOLING_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLING_DIR))
