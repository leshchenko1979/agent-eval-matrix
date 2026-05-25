from __future__ import annotations

from pydantic_ai import RunContext

from gategrid.contrib.file_edit.bundled.tooling.baseline import ls as _ls
from gategrid.contrib.file_edit.deps import FileEditDeps


def ls(ctx: RunContext[FileEditDeps], path: str = ".") -> list[str]:
    return _ls(ctx, path)
