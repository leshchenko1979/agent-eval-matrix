from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gategrid import __version__
from gategrid.baseline_ops import update_baseline_from_report
from gategrid.cli_output import (
    format_gate_check,
    format_matrix_run_errors,
    print_run_outcome,
)
from gategrid.executor import MatrixRunError, run_matrix_sync
from gategrid.gate import run_gate
from gategrid.io import load_baseline, load_matrix_config, load_report
from gategrid.paths import reports_dir, resolve_baseline_file
from gategrid.validate import validate_matrix


def _cmd_run(args: argparse.Namespace) -> int:
    matrix_path = Path(args.matrix)
    root = Path(args.root) if args.root else None
    model_filter = args.model or None
    try:
        outcome = run_matrix_sync(
            matrix_path,
            eval_root=root,
            case_filter=args.case,
            model_filter=model_filter,
        )
    except MatrixRunError as exc:
        print(format_matrix_run_errors(exc.errors), file=sys.stderr)
        return 2
    except Exception as exc:
        print(format_matrix_run_errors([str(exc)]), file=sys.stderr)
        return 2

    matrix_yaml_models: list[str] | None = None
    if model_filter:
        matrix_yaml_models = list(load_matrix_config(matrix_path).models)
    print_run_outcome(
        outcome,
        matrix_path=matrix_path,
        eval_root=root,
        case_filter=args.case,
        model_filter=model_filter,
        matrix_yaml_models=matrix_yaml_models,
        verbose=args.verbose,
    )
    if all(c.passed for c in outcome.report.cells):
        return 0
    return 1


def _cmd_gate(args: argparse.Namespace) -> int:
    report_path = Path(args.report) if args.report else _latest_report()
    if report_path is None:
        print("no report found; pass --report", file=sys.stderr)
        return 2

    report = load_report(report_path)
    config = None
    if args.matrix:
        config = load_matrix_config(Path(args.matrix)).gate

    profile_id = args.profile
    if config is not None:
        profile_id = profile_id or config.baseline

    if not profile_id:
        print("profile required: --profile or matrix gate.baseline", file=sys.stderr)
        return 2

    try:
        baseline_file = resolve_baseline_file(
            profile_id,
            baseline=Path(args.baseline) if args.baseline else None,
            baseline_from_artifact=(
                Path(args.baseline_from_artifact)
                if args.baseline_from_artifact
                else None
            ),
        )
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    gate_config = config
    if gate_config is None:
        from gategrid.models.gate_config import (
            GateConfig,
            GateRegression,
            RegressionBounds,
        )

        gate_config = GateConfig(
            baseline=profile_id,
            regression=GateRegression(
                baseline=profile_id,
                bounds={
                    "overall": RegressionBounds(pass_rate_min_delta=-0.02),
                    "like_for_like": RegressionBounds(pass_rate_min_delta=-0.01),
                },
            ),
        )

    outcome = run_gate(
        report,
        load_baseline(baseline_file),
        gate_config,
        profile_id=profile_id,
    )
    for w in outcome.warnings:
        print(f"warning: {w}")
    for check in outcome.checks:
        print(format_gate_check(check))

    if outcome.passed:
        print("gate: PASSED")
        return 0
    print("gate: FAILED", file=sys.stderr)
    return 1


def _cmd_validate(args: argparse.Namespace) -> int:
    root = Path(args.root) if args.root else None
    outcome = validate_matrix(
        Path(args.matrix),
        root=root,
        emit_conventions=args.verbose,
        model_filter=args.model or None,
    )
    if outcome.ok:
        print("validate: OK")
        return 0
    for err in outcome.errors:
        print(f"error: {err}", file=sys.stderr)
    print("validate: FAILED", file=sys.stderr)
    return 1


def _cmd_baseline_update(args: argparse.Namespace) -> int:
    matrix_path = Path(args.matrix) if args.matrix else None
    path = update_baseline_from_report(
        Path(args.from_report),
        args.profile,
        matrix_path=matrix_path,
    )
    print(f"baseline updated: {path}")
    return 0


def _latest_report() -> Path | None:
    directory = reports_dir()
    if not directory.is_dir():
        return None
    candidates = sorted(
        directory.glob("*_matrix.json"), key=lambda p: p.stat().st_mtime
    )
    if not candidates:
        candidates = sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None


_CLI_EPILOG = """\
artifacts live under .gategrid/ (or GATEGRID_HOME).

  validate   check matrix YAML and eval tree
  run        execute cases × profiles × models
  gate       compare a report to a baseline
  baseline   write baselines from reports

run/validate --model <id> overrides matrix models (preset under eval_root/models/).

Put -v/--verbose before the subcommand for case/evaluator id hints on stderr.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gategrid",
        epilog=_CLI_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print case/evaluator id conventions to stderr",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    val_p = sub.add_parser("validate", help="validate matrix and referenced YAML")
    val_p.add_argument("--matrix", required=True, help="path to matrix YAML")
    val_p.add_argument(
        "--root",
        help="eval project root (default: GATEGRID_EVAL_ROOT or parent of matrices/)",
    )
    val_p.add_argument(
        "--model",
        action="append",
        metavar="ID",
        help="override matrix models with these preset id(s) from eval_root/models/",
    )
    val_p.set_defaults(func=_cmd_validate)

    run_p = sub.add_parser("run", help="run matrix eval grid")
    run_p.add_argument("--matrix", required=True, help="path to matrix YAML")
    run_p.add_argument(
        "--root",
        help="eval project root (default: GATEGRID_EVAL_ROOT or parent of matrices/)",
    )
    run_p.add_argument(
        "--case",
        help="run a single case id only (partial matrix; gate fingerprint caveat)",
    )
    run_p.add_argument(
        "--model",
        action="append",
        metavar="ID",
        help="override matrix models with these preset id(s) from eval_root/models/",
    )
    run_p.set_defaults(func=_cmd_run)

    gate_p = sub.add_parser("gate", help="compare report to baseline")
    gate_p.add_argument(
        "--report", help="report JSON (default: latest in .gategrid/reports)"
    )
    baseline_group = gate_p.add_mutually_exclusive_group()
    baseline_group.add_argument(
        "--baseline", help="baseline JSON (default: .gategrid/baselines/<profile>.json)"
    )
    baseline_group.add_argument(
        "--baseline-from-artifact",
        help="directory or file from CI artifact (baselines/<profile>.json or <profile>.json)",
    )
    gate_p.add_argument("--matrix", help="matrix YAML for gate config")
    gate_p.add_argument(
        "--profile", help="profile id (default: gate.baseline from matrix)"
    )
    gate_p.set_defaults(func=_cmd_gate)

    base_p = sub.add_parser("baseline", help="baseline operations")
    base_sub = base_p.add_subparsers(dest="baseline_cmd", required=True)
    update_p = base_sub.add_parser("update", help="write baseline from report")
    update_p.add_argument("--from-report", required=True)
    update_p.add_argument("--profile", required=True)
    update_p.add_argument(
        "--matrix",
        help="matrix YAML for gate metric keys in baseline overall.metrics",
    )
    update_p.add_argument(
        "--root",
        help="eval project root (unused for update; reserved for parity with run/gate)",
    )
    update_p.set_defaults(func=_cmd_baseline_update)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
