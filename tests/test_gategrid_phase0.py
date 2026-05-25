from __future__ import annotations

import json
from pathlib import Path

import pytest

from gategrid.baseline_ops import report_to_baseline, write_baseline
from gategrid.cli import main
from gategrid.executor import MatrixRunError, run_matrix_sync
from gategrid.gate import run_gate
from gategrid.io import load_baseline, load_report, save_json
from gategrid.models.artifact import RunArtifact
from gategrid.models.baseline import Baseline
from gategrid.models.cell import CellKey, CellResult
from gategrid.models.gate_config import (
    GateConfig,
    GateLimits,
    GateRegression,
    RegressionBounds,
)
from gategrid.models.report import MatrixReport
from gategrid.version import SCHEMA_VERSION
from gategrid.fixtures.sample import mcp_shaped_artifact, sample_report

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_V1 = REPO_ROOT / "schemas" / "v1"
EXAMPLES = SCHEMAS_V1 / "examples"


def test_schema_version_constant() -> None:
    assert SCHEMA_VERSION == 1


def test_run_artifact_evaluators_round_trip() -> None:
    art = mcp_shaped_artifact()
    art.evaluators["file_content_match"] = {
        "pass": False,
        "message": "differs",
        "detail": "--- a\n+++ b",
    }
    raw = json.loads(art.model_dump_json())
    restored = RunArtifact.model_validate(raw)
    assert restored.evaluators["file_content_match"]["pass"] is False

    art_pass = mcp_shaped_artifact()
    art_pass.evaluators["file_content_match"] = True
    restored_pass = RunArtifact.model_validate(json.loads(art_pass.model_dump_json()))
    assert restored_pass.evaluators["file_content_match"] is True


def test_run_artifact_tools_called_round_trip() -> None:
    art = mcp_shaped_artifact()
    raw = json.loads(art.model_dump_json())
    restored = RunArtifact.model_validate(raw)
    assert restored.tools_called == {"search_contacts": 1}


def test_report_baseline_gate_round_trip(tmp_path: Path) -> None:
    report = sample_report()
    report_path = tmp_path / "report.json"
    save_json(report_path, report)
    loaded = load_report(report_path)
    assert loaded.pass_rate == report.pass_rate

    baseline = report_to_baseline(
        loaded, "telegram-mcp-stdio", mean_keys={"turns", "tokens_spent"}
    )
    baseline_path = write_baseline(baseline, home=tmp_path)
    assert baseline_path.is_file()

    config = GateConfig(
        baseline="telegram-mcp-stdio",
        regression=GateRegression(
            baseline="telegram-mcp-stdio",
            bounds={
                "overall": RegressionBounds(pass_rate_min_delta=-0.5),
                "like_for_like": RegressionBounds(
                    pass_rate_min_delta=-0.5,
                    max_regressed_cells=0,
                ),
            },
        ),
        limits={"overall": GateLimits(pass_rate_min=0.5)},
    )
    assert run_gate(loaded, load_baseline(baseline_path), config).passed

    regressed = sample_report(pass_second=False)
    save_json(tmp_path / "bad.json", regressed)
    outcome = run_gate(
        load_report(tmp_path / "bad.json"),
        load_baseline(baseline_path),
        config,
    )
    assert not outcome.passed


def test_gate_metric_mean_min_and_max() -> None:
    report = sample_report()
    report.overall = report.overall or __import__(
        "gategrid.aggregates", fromlist=["compute_overall"]
    ).compute_overall(report.cells, mean_keys=["accuracy", "turns"])
    report.overall.metrics["accuracy"] = 0.95
    report.overall.metrics["turns"] = 2.0

    baseline_report = sample_report()
    baseline = report_to_baseline(
        baseline_report,
        "telegram-mcp-stdio",
        mean_keys=["accuracy", "turns"],
    )
    baseline.overall.metrics["accuracy"] = 0.98
    baseline.overall.metrics["turns"] = 1.5

    config = GateConfig(
        baseline="telegram-mcp-stdio",
        limits={
            "overall": GateLimits(
                metric_mean_max={"turns": 3.0},
                metric_mean_min={"accuracy": 0.9},
            )
        },
        regression=GateRegression(
            baseline="telegram-mcp-stdio",
            bounds={
                "overall": RegressionBounds(
                    metric_mean_max_delta={"turns": 1.0},
                    metric_mean_min_delta={"accuracy": -0.1},
                )
            },
        ),
    )
    outcome = run_gate(report, baseline, config)
    assert outcome.passed
    names = {c.name for c in outcome.checks}
    assert "limits.overall.accuracy_min" in names
    assert "limits.overall.turns_max" in names


def _lfl_gate_config(
    *,
    min_share: float | None = None,
) -> GateConfig:
    regression = GateRegression(
        baseline="telegram-mcp-stdio",
        bounds={
            "like_for_like": RegressionBounds(pass_rate_min_delta=-0.5),
        },
    )
    if min_share is not None:
        regression.min_like_for_like_share = min_share
    return GateConfig(baseline="telegram-mcp-stdio", regression=regression)


def test_gate_like_for_like_intersection_share_full() -> None:
    report = sample_report()
    baseline = report_to_baseline(
        report, "telegram-mcp-stdio", mean_keys={"turns", "tokens_spent"}
    )
    outcome = run_gate(report, baseline, _lfl_gate_config())
    assert outcome.passed
    assert any(
        c.name == "regression.like_for_like.intersection_share" and c.passed
        for c in outcome.checks
    )


def test_gate_like_for_like_intersection_share_empty_fails() -> None:
    report = sample_report()
    baseline = report_to_baseline(
        report, "telegram-mcp-stdio", mean_keys={"turns", "tokens_spent"}
    )
    for cell in report.cells:
        cell.key = CellKey(
            case_id="unbaselined_case",
            profile_id="telegram-mcp-stdio",
            model_id="gpt-4o-mini",
        )
    outcome = run_gate(report, baseline, _lfl_gate_config())
    assert not outcome.passed
    share_check = next(
        c
        for c in outcome.checks
        if c.name == "regression.like_for_like.intersection_share"
    )
    assert not share_check.passed
    assert "0/2 cells" in share_check.message


def test_gate_like_for_like_intersection_share_below_min_fails() -> None:
    report = sample_report()
    baseline = report_to_baseline(
        report, "telegram-mcp-stdio", mean_keys={"turns", "tokens_spent"}
    )
    report.cells = report.cells[:1]
    outcome = run_gate(report, baseline, _lfl_gate_config(min_share=0.75))
    assert not outcome.passed
    share_check = next(
        c
        for c in outcome.checks
        if c.name == "regression.like_for_like.intersection_share"
    )
    assert not share_check.passed


def test_gate_like_for_like_intersection_share_default_min_is_one() -> None:
    report = sample_report()
    baseline = report_to_baseline(
        report, "telegram-mcp-stdio", mean_keys={"turns", "tokens_spent"}
    )
    report.cells = report.cells[:1]
    outcome = run_gate(report, baseline, _lfl_gate_config())
    assert not outcome.passed


def test_gate_regression_min_like_for_like_share_invalid() -> None:
    with pytest.raises(ValueError, match="min_like_for_like_share"):
        GateRegression(
            baseline="p",
            min_like_for_like_share=1.5,
            bounds={"like_for_like": RegressionBounds()},
        )


def test_cli_run_not_ready() -> None:
    assert main(["run", "--matrix", "evals/matrices/x.yaml"]) == 2


def test_executor_raises_on_missing_matrix() -> None:
    with pytest.raises(MatrixRunError):
        run_matrix_sync(Path("x.yaml"))


def test_cli_gate_integration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
        ]
    )
    assert code == 0


@pytest.mark.parametrize(
    ("model", "stem"),
    [
        (MatrixReport, "matrix-report"),
        (Baseline, "baseline"),
        (RunArtifact, "run-artifact"),
        (CellResult, "cell-result"),
    ],
)
def test_json_schema_files_exist_and_match_model(model: type, stem: str) -> None:
    path = SCHEMAS_V1 / f"{stem}.schema.json"
    assert path.is_file(), f"missing {path}"
    schema = json.loads(path.read_text(encoding="utf-8"))
    assert schema == model.model_json_schema()


def test_example_json_validates() -> None:
    report = load_report(EXAMPLES / "matrix-report.example.json")
    assert report.matrix_name == "telegram-mcp-gate"
    baseline = load_baseline(EXAMPLES / "baseline.example.json")
    assert baseline.profile_id == "telegram-mcp-stdio"
