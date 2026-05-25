from __future__ import annotations

from gategrid.models.baseline import Baseline
from gategrid.models.cell import CellKey, CellResult
from gategrid.models.report import ReportFingerprint


def build_fingerprint(
    matrix_name: str,
    cells: list[CellResult],
    *,
    case_ids: list[str] | None = None,
    profile_ids: list[str] | None = None,
) -> ReportFingerprint:
    """Build fingerprint from cells or explicit matrix axes (full grid when sampling)."""
    resolved_profiles = profile_ids or sorted({c.key.profile_id for c in cells})
    resolved_cases = case_ids or sorted({c.key.case_id for c in cells})
    return ReportFingerprint(
        matrix_name=matrix_name,
        profile_ids=sorted(resolved_profiles),
        case_ids=sorted(resolved_cases),
    )


def fingerprint_matches(a: ReportFingerprint, b: ReportFingerprint) -> bool:
    return (
        a.matrix_name == b.matrix_name
        and a.profile_ids == b.profile_ids
        and a.case_ids == b.case_ids
    )


def intersection_keys(
    report_cells: list[CellResult],
    baseline_cell_keys: set[str],
) -> list[CellKey]:
    return [
        cell.key
        for cell in report_cells
        if Baseline.cell_dict_key(cell.key) in baseline_cell_keys
    ]
