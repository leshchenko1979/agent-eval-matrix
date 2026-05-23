from __future__ import annotations

import argparse
import asyncio
import logging
import uuid
from pathlib import Path

import yaml
from dotenv import load_dotenv

from harness.models import ExperimentVariant
from harness.observability import get_commit_sha, setup_observability
from harness.report import new_matrix_report, print_summary, write_aggregate_report
from harness.suites import MatrixRootConfig, resolve_suite
from harness.task import evaluate_case

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS = ROOT / "experiments"
DEFAULT_MATRIX = EXPERIMENTS / "matrix.yaml"
DEFAULT_CASES = EXPERIMENTS / "cases"


def load_matrix_root(path: Path) -> MatrixRootConfig:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        data = {}
    return MatrixRootConfig.model_validate(data)


def filter_variants(
    variants: list[ExperimentVariant], variant_filter: str | None
) -> list[ExperimentVariant]:
    if not variant_filter:
        return variants
    return [v for v in variants if v.variant_id == variant_filter]


async def run_matrix(
    suite_path: Path,
    cases_path: Path,
    variant_filter: str | None = None,
    trace: bool = False,
) -> int:
    setup_observability()
    load_dotenv(ROOT / ".env")

    suite_path = suite_path.resolve()
    resolved = resolve_suite(suite_path, EXPERIMENTS, cases_path.resolve())
    variants = filter_variants(resolved.variants, variant_filter)
    if not variants:
        raise ValueError(f"No variants matched filter: {variant_filter!r}")

    run_id = str(uuid.uuid4())[:8] if trace else None
    report = new_matrix_report(
        commit_sha=get_commit_sha(),
        suite_path=resolved.suite_path,
        suite_name=resolved.suite_name,
        cases_path=str(cases_path),
    )

    logger.info(
        "Running suite %s: %d variants x %d cases",
        resolved.suite_name,
        len(variants),
        len(resolved.cases),
    )

    for variant in variants:
        for case in resolved.cases:
            logger.info("Evaluating %s / %s", variant.variant_id, case.name)
            result = await evaluate_case(case, variant, run_id=run_id)
            report.results.append(result)

    write_aggregate_report(report)
    print_summary(report)

    failed = sum(1 for r in report.results if not r.passed)
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run file-editing eval matrix")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="Run evaluation suite")
    run_parser.add_argument(
        "--suite",
        type=Path,
        default=None,
        help="Path to suite YAML (default from experiments/matrix.yaml)",
    )
    run_parser.add_argument(
        "--matrix",
        type=Path,
        default=DEFAULT_MATRIX,
        help="Path to matrix.yaml (default_suite pointer)",
    )
    run_parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_CASES,
        help="Path to cases directory",
    )
    run_parser.add_argument(
        "--variant",
        type=str,
        default=None,
        help="Run single variant id, e.g. baseline/minimax-m2.7",
    )
    run_parser.add_argument(
        "--trace",
        action="store_true",
        help="Write JSONL trace events under reports/traces/",
    )

    args = parser.parse_args(argv)
    if args.command == "run":
        suite_path = args.suite
        if suite_path is None:
            root = load_matrix_root(args.matrix.resolve())
            suite_path = root.resolve_default_suite_path(EXPERIMENTS)
        code = asyncio.run(
            run_matrix(
                suite_path=suite_path,
                cases_path=args.cases,
                variant_filter=args.variant,
                trace=args.trace,
            )
        )
        raise SystemExit(code)


if __name__ == "__main__":
    main()
