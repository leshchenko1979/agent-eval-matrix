from __future__ import annotations

import os
from pathlib import Path


def gategrid_home(cwd: Path | None = None) -> Path:
    if env := os.environ.get("GATEGRID_HOME"):
        return Path(env).expanduser().resolve()
    root = cwd or Path.cwd()
    return (root / ".gategrid").resolve()


def _root(home: Path | None) -> Path:
    return home if home is not None else gategrid_home()


def baselines_dir(home: Path | None = None) -> Path:
    return _root(home) / "baselines"


def reports_dir(home: Path | None = None) -> Path:
    return _root(home) / "reports"


def baseline_path(profile_id: str, home: Path | None = None) -> Path:
    return baselines_dir(home) / f"{profile_id}.json"


def traces_dir(home: Path | None = None) -> Path:
    return _root(home) / "traces"


def path_under_home(path: Path, home: Path | None = None) -> bool:
    try:
        path.resolve().relative_to(_root(home).resolve())
        return True
    except ValueError:
        return False


def resolve_baseline_file(
    profile_id: str,
    *,
    baseline: Path | None = None,
    baseline_from_artifact: Path | None = None,
    home: Path | None = None,
) -> Path:
    """Resolve baseline JSON path from explicit file, artifact dir, or home."""
    if baseline is not None and baseline_from_artifact is not None:
        raise ValueError("use only one of baseline= or baseline_from_artifact=")

    if baseline is not None:
        path = baseline.expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"baseline not found: {path}")
        return path

    if baseline_from_artifact is not None:
        root = baseline_from_artifact.expanduser().resolve()
        if root.is_file():
            return root
        nested = root / "baselines" / f"{profile_id}.json"
        if nested.is_file():
            return nested
        flat = root / f"{profile_id}.json"
        if flat.is_file():
            return flat
        raise FileNotFoundError(
            f"baseline for profile {profile_id!r} not found under artifact {root} "
            f"(tried {nested.name} and {flat.name})"
        )

    path = baseline_path(profile_id, home)
    if not path.is_file():
        raise FileNotFoundError(f"baseline not found: {path}")
    return path


def ensure_home(home: Path | None = None) -> Path:
    """Create `.gategrid/` subdirs (baselines, reports, traces) if missing."""
    root = _root(home)
    for sub in ("baselines", "reports", "traces"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root
