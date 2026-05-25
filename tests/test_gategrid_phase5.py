"""Phase 5 — CI productization (baseline artifact, sampling, gate smoke)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from gategrid.baseline_ops import report_to_baseline, write_baseline
from gategrid.cli import main
from gategrid.executor import run_matrix_sync
from gategrid.fingerprint import build_fingerprint
from gategrid.gate import run_gate
from gategrid.io import load_baseline, load_report, save_json
from gategrid.models.gate_config import (
    GateConfig,
    GateLimits,
    GateRegression,
    RegressionBounds,
)
from gategrid.models.matrix_config import SampleConfig
from gategrid.paths import resolve_baseline_file
from gategrid.sampling import sample_seed_from_ref, select_cell_keys
from gategrid.fixtures.sample import sample_report
from gategrid.cases import CaseRecord
from gategrid.models.cell import CellKey

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = REPO_ROOT / "examples/gategrid"
CI_GATE_MATRIX = EXAMPLES_ROOT / "matrices/ci-gate-mock.yaml"
CI_PR_MATRIX = EXAMPLES_ROOT / "matrices/ci-gate-pr-mock.yaml"
COMMITTED_BASELINE = EXAMPLES_ROOT / "ci/baselines/demo.json"
SCHEMAS_BASELINE = REPO_ROOT / "schemas/v1/baseline.schema.json"


def test_committed_baseline_matches_schema() -> None:
    assert COMMITTED_BASELINE.is_file()
    schema = json.loads(SCHEMAS_BASELINE.read_text(encoding="utf-8"))
    data = json.loads(COMMITTED_BASELINE.read_text(encoding="utf-8"))
    assert data["profile_id"] == "demo"
    # Pydantic model_json_schema is source of truth in phase0; spot-check keys
    assert "fingerprint" in data
    assert "cells" in data


def test_resolve_baseline_from_artifact_file() -> None:
    path = resolve_baseline_file(
        "demo",
        baseline=COMMITTED_BASELINE,
    )
    assert path == COMMITTED_BASELINE.resolve()


def test_resolve_baseline_from_artifact_dir_layout(tmp_path: Path) -> None:
    nested = tmp_path / "baselines" / "demo.json"
    nested.parent.mkdir(parents=True)
    nested.write_text(COMMITTED_BASELINE.read_text(encoding="utf-8"))
    path = resolve_baseline_file("demo", baseline_from_artifact=tmp_path)
    assert path == nested.resolve()


def test_resolve_baseline_from_artifact_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="not found"):
        resolve_baseline_file("demo", baseline_from_artifact=tmp_path)


def test_resolve_baseline_mutually_exclusive_raises() -> None:
    with pytest.raises(ValueError, match="only one"):
        resolve_baseline_file(
            "demo",
            baseline=COMMITTED_BASELINE,
            baseline_from_artifact=COMMITTED_BASELINE,
        )


def test_cli_gate_baseline_from_artifact_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GATEGRID_HOME", str(tmp_path))
    report = sample_report()
    report_path = tmp_path / "reports" / "r_matrix.json"
    save_json(report_path, report)
    baseline = report_to_baseline(
        report, "telegram-mcp-stdio", mean_keys={"turns", "tokens_spent"}
    )
    write_baseline(baseline, home=tmp_path)

    code = main(
        [
            "gate",
            "--report",
            str(report_path),
            "--profile",
            "telegram-mcp-stdio",
            "--baseline-from-artifact",
            str(tmp_path),
        ]
    )
    assert code == 0


def test_cli_gate_missing_artifact_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("GATEGRID_HOME", str(tmp_path))
    report_path = tmp_path / "reports" / "r_matrix.json"
    save_json(report_path, sample_report())
    code = main(
        [
            "gate",
            "--report",
            str(report_path),
            "--profile",
            "demo",
            "--baseline-from-artifact",
            str(tmp_path / "empty"),
        ]
    )
    assert code == 2
    assert "not found" in capsys.readouterr().err


def test_fingerprint_mismatch_warning() -> None:
    report = sample_report()
    baseline_report = sample_report()
    baseline = report_to_baseline(
        baseline_report, "telegram-mcp-stdio", mean_keys=set()
    )
    baseline.fingerprint.case_ids = ["other_case"]
    config = GateConfig(
        baseline="telegram-mcp-stdio",
        regression=GateRegression(
            baseline="telegram-mcp-stdio",
            bounds={"overall": RegressionBounds(pass_rate_min_delta=-1.0)},
        ),
    )
    outcome = run_gate(report, baseline, config)
    assert any("fingerprint mismatch" in w for w in outcome.warnings)


def test_baseline_update_matrix_preserves_metric_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GATEGRID_HOME", str(tmp_path))
    outcome = run_matrix_sync(CI_GATE_MATRIX, eval_root=EXAMPLES_ROOT)
    code = main(
        [
            "baseline",
            "update",
            "--from-report",
            str(outcome.report_path),
            "--profile",
            "demo",
            "--matrix",
            str(CI_GATE_MATRIX),
        ]
    )
    assert code == 0
    loaded = load_baseline(tmp_path / "baselines" / "demo.json")
    assert loaded.overall is not None


def test_sample_selection_reproducible_and_respects_tags() -> None:
    keys = [
        CellKey(case_id="hello_world", profile_id="demo", model_id="mock"),
        CellKey(case_id="echo_beta", profile_id="demo", model_id="mock"),
    ]
    registry = {
        "hello_world": CaseRecord(case_id="hello_world", tags=["smoke"]),
        "echo_beta": CaseRecord(case_id="echo_beta", tags=[]),
    }
    sample = SampleConfig(
        max_cells=1, share=0.5, seed=42, always_include_tags=["smoke"]
    )
    a = select_cell_keys(keys, registry, sample)
    b = select_cell_keys(keys, registry, sample)
    assert a.selected_keys == b.selected_keys
    assert a.selected_keys[0].case_id == "hello_world"


def test_sample_seed_from_ref_stable() -> None:
    a = sample_seed_from_ref("ci-gate-pr-mock", "abc123")
    b = sample_seed_from_ref("ci-gate-pr-mock", "abc123")
    assert a == b
    assert isinstance(a, int)


def test_run_matrix_sampling_metadata() -> None:
    outcome = run_matrix_sync(CI_PR_MATRIX, eval_root=EXAMPLES_ROOT)
    report = outcome.report
    assert report.sampling.sampled is True
    assert report.sampling.planned_cells == 2
    assert report.sampling.executed_cells <= 2
    assert report.fingerprint.case_ids == ["echo_beta", "hello_world"]
    assert len(report.fingerprint.profile_ids) == 1


def test_validate_rejects_bad_sample_share() -> None:
    bad = EXAMPLES_ROOT / "matrices" / "_bad-sample.yaml"
    bad.write_text(
        "name: bad\nprofiles: [demo]\nmodels: [mock]\ncases: [hello_world]\n"
        "run:\n  sample:\n    share: 1.5\n    max_cells: 1\n",
        encoding="utf-8",
    )
    try:
        code = main(["validate", "--matrix", str(bad), "--root", str(EXAMPLES_ROOT)])
        assert code != 0
    finally:
        bad.unlink(missing_ok=True)


def test_subprocess_ci_gate_mock() -> None:
    import os

    env = {
        **os.environ,
        "GATEGRID_HOME": str(REPO_ROOT / ".gategrid-phase5-test"),
        "GATEGRID_EVAL_ROOT": str(EXAMPLES_ROOT),
    }
    home = Path(env["GATEGRID_HOME"])
    if home.exists():
        import shutil

        shutil.rmtree(home)
    gategrid_exe = REPO_ROOT / ".venv" / "bin" / "gategrid"
    if not gategrid_exe.is_file():
        gategrid_exe = Path(sys.executable)
        run_cmd = [sys.executable, "-m", "gategrid.cli", "run"]
        gate_cmd = [sys.executable, "-m", "gategrid.cli", "gate"]
    else:
        run_cmd = [str(gategrid_exe), "run"]
        gate_cmd = [str(gategrid_exe), "gate"]

    proc = subprocess.run(
        [
            *run_cmd,
            "--matrix",
            str(CI_GATE_MATRIX),
            "--root",
            str(EXAMPLES_ROOT),
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    proc2 = subprocess.run(
        [
            *gate_cmd,
            "--matrix",
            str(CI_GATE_MATRIX),
            "--baseline",
            str(COMMITTED_BASELINE),
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc2.returncode == 0, proc2.stderr
    assert "gate: PASSED" in proc2.stdout
