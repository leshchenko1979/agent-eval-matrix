"""Register baseline builtin tools (requires pydantic-ai when tools are loaded)."""

from __future__ import annotations

from gategrid.contrib.file_edit.bundled.tooling import baseline
from gategrid.contrib.file_edit.tools import register_builtin_tool


def register_bundled_tools() -> None:
    register_builtin_tool("ls", baseline.ls)
    register_builtin_tool("glob", baseline.glob_tool)
    register_builtin_tool("grep", baseline.grep)
    register_builtin_tool("read_file", baseline.read_file)
    register_builtin_tool("str_replace", baseline.str_replace)
