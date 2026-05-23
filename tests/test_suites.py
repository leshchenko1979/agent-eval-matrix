from pathlib import Path

import pytest
from pydantic import ValidationError

from harness.suites import load_suite, resolve_suite

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ROOT / "experiments"
CASES = EXPERIMENTS / "cases"


def test_resolve_suite_ci() -> None:
    resolved = resolve_suite(EXPERIMENTS / "suites" / "ci.yaml", EXPERIMENTS, CASES)
    assert resolved.suite_name == "ci"
    assert len(resolved.variants) == 1
    assert resolved.variants[0].tooling_name == "baseline"
    assert len(resolved.cases) == 2
    assert resolved.variants[0].variant_id == "baseline/minimax-m2.7"
    assert len(resolved.variants[0].tools) == 5


def test_resolve_suite_full() -> None:
    resolved = resolve_suite(EXPERIMENTS / "suites" / "full.yaml", EXPERIMENTS, CASES)
    assert resolved.suite_name == "full"
    assert len(resolved.variants) == 4
    assert len(resolved.cases) == 5
    assert len(resolved.variants) * len(resolved.cases) == 20


def test_resolve_suite_hashline_hypotheses() -> None:
    resolved = resolve_suite(
        EXPERIMENTS / "suites" / "hashline_hypotheses.yaml", EXPERIMENTS, CASES
    )
    assert resolved.suite_name == "hashline_hypotheses"
    assert len(resolved.variants) == 5
    assert len(resolved.cases) == 10
    assert len(resolved.variants) * len(resolved.cases) == 50
    toolings = {v.tooling_name for v in resolved.variants}
    assert toolings == {
        "opencrabs_original",
        "opencrabs_h1_docs",
        "opencrabs_h3_collision",
        "opencrabs_h2_fuzzy",
        "baseline",
    }


def test_suite_requires_matrix() -> None:
    with pytest.raises(ValidationError):
        load_suite(EXPERIMENTS / "matrix.yaml")
