from __future__ import annotations

from pydantic_ai import RunContext

from gategrid.contrib.file_edit.bundled.tooling.baseline import glob_tool as _glob_tool
from gategrid.contrib.file_edit.deps import FileEditDeps


def glob_tool(ctx: RunContext[FileEditDeps], pattern: str) -> list[str]:
    return _glob_tool(ctx, pattern)
