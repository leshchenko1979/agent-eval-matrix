from __future__ import annotations

from pydantic_ai import RunContext

from gategrid.contrib.file_edit.bundled.tooling.baseline import read_file as _read_file
from gategrid.contrib.file_edit.deps import FileEditDeps


def read_file(ctx: RunContext[FileEditDeps], file_path: str) -> str:
    """Read the full contents of a file (workspace-relative path)."""
    return _read_file(ctx, file_path)
