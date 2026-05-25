from __future__ import annotations

from pydantic_ai import RunContext

from gategrid.contrib.file_edit.bundled.tooling.baseline import str_replace as _str_replace
from gategrid.contrib.file_edit.deps import FileEditDeps


def str_replace(
    ctx: RunContext[FileEditDeps], file_path: str, old_str: str, new_str: str
) -> str:
    return _str_replace(ctx, file_path, old_str, new_str)
