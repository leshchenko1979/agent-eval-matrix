from __future__ import annotations

from pydantic_ai import RunContext

from harness import tools
from harness.models import FileEditDeps


def glob_tool(ctx: RunContext[FileEditDeps], pattern: str) -> list[str]:
    """Find files matching a glob pattern (e.g. '**/*.py')."""
    return tools.glob_tool(ctx, pattern)
