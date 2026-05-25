from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from gategrid.executor import run_matrix_sync
from gategrid.validate import validate_matrix

REPO_ROOT = Path(__file__).resolve().parents[1]
OPENCRABS_ROOT = REPO_ROOT / "examples" / "opencrabs"
SMOKE_MATRIX = OPENCRABS_ROOT / "matrices" / "hashline-smoke.yaml"


def test_validate_hashline_smoke() -> None:
    result = validate_matrix(SMOKE_MATRIX, root=OPENCRABS_ROOT)
    assert result.ok, result.errors


def test_run_hashline_smoke_mock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GATEGRID_HOME", str(tmp_path / ".gategrid"))
    outcome = run_matrix_sync(SMOKE_MATRIX, eval_root=OPENCRABS_ROOT)
    report = outcome.report
    assert len(report.cells) == 1
    cell = report.cells[0]
    assert cell.key.case_id == "indent_collision"
    assert cell.passed
    art = cell.attempts[0].artifact
    assert art is not None
    assert art.evaluators.get("file_content_match") is True
    assert cell.metrics.get("turns") == 0


def test_cli_hashline_smoke_subprocess(tmp_path: Path) -> None:
    home = tmp_path / ".gategrid"
    env = os.environ.copy()
    env["GATEGRID_HOME"] = str(home)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    env["GATEGRID_EVAL_ROOT"] = str(OPENCRABS_ROOT)
    for args in (
        ["validate", "--matrix", str(SMOKE_MATRIX), "--root", str(OPENCRABS_ROOT)],
        ["run", "--matrix", str(SMOKE_MATRIX), "--root", str(OPENCRABS_ROOT)],
    ):
        proc = subprocess.run(
            [sys.executable, "-m", "gategrid.cli", *args],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
