from __future__ import annotations

from pydantic_ai import RunContext

from gategrid.contrib.file_edit.bundled.tooling.baseline import grep as _grep
from gategrid.contrib.file_edit.deps import FileEditDeps


def grep(ctx: RunContext[FileEditDeps], pattern: str, file_path: str) -> list[str]:
    return _grep(ctx, pattern, file_path)
