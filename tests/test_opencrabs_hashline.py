"""Unit tests for opencrabs hashline engine."""

from __future__ import annotations

from opencrabs.hashline import (
    apply_hashline_edits,
    format_read_hashline,
    hash_all_lines,
    hash_line,
)


def test_hash_line_deterministic() -> None:
    assert hash_line("hello world") == hash_line("hello world")
    assert len(hash_line("x")) == 2


def test_apply_hashline_replace() -> None:
    content = "line one\nline two\nline three"
    hashes = hash_all_lines(content)
    pos = f"2#{hashes[1][1]}"
    new, err = apply_hashline_edits(
        content, [{"op": "replace", "pos": pos, "lines": "LINE TWO"}]
    )
    assert err is None
    assert new is not None
    assert "LINE TWO" in new
    assert "line two" not in new


def test_format_read_hashline_empty_hash_collisions() -> None:
    content = "    pass\n    pass\n    ok\n"
    out = format_read_hashline(content, 1, collision_format="empty_hash")
    assert "  |    pass" in out
    assert "COLLISION|" not in out
