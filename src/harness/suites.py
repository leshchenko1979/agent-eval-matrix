from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

from harness.cases import load_cases_by_names
from harness.load_tooling import load_tool_functions
from harness.models import CaseSet, EditCase, ExperimentVariant, SuiteConfig, ToolSet


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected YAML mapping")
    return data


def load_tool_set(path: Path, experiments_dir: Path) -> ToolSet:
    data = _load_yaml(path)
    return ToolSet.model_validate(data)


def load_case_set(path: Path) -> CaseSet:
    data = _load_yaml(path)
    return CaseSet.model_validate(data)


def load_suite(path: Path) -> SuiteConfig:
    data = _load_yaml(path)
    return SuiteConfig.model_validate(data)


def suite_display_name(suite_path: Path, suite: SuiteConfig) -> str:
    if suite.name:
        return suite.name
    return suite_path.stem


def _registry_yaml_dir(experiments_dir: Path, subdir: str) -> Path:
    return experiments_dir / subdir


def build_tool_set_registry(experiments_dir: Path) -> dict[str, ToolSet]:
    root = _registry_yaml_dir(experiments_dir, "tool_sets")
    registry: dict[str, ToolSet] = {}
    if not root.is_dir():
        return registry
    for path in sorted(root.glob("*.yaml")):
        tool_set = load_tool_set(path, experiments_dir)
        if tool_set.name in registry:
            raise ValueError(f"Duplicate tool set name {tool_set.name!r}")
        registry[tool_set.name] = tool_set
    return registry


def _build_case_set_registry(experiments_dir: Path) -> dict[str, CaseSet]:
    root = _registry_yaml_dir(experiments_dir, "case_sets")
    registry: dict[str, CaseSet] = {}
    if not root.is_dir():
        return registry
    for path in sorted(root.glob("*.yaml")):
        case_set = load_case_set(path)
        if case_set.name in registry:
            raise ValueError(f"Duplicate case set name {case_set.name!r}")
        registry[case_set.name] = case_set
    return registry


def variant_from_tool_set(
    tool_set: ToolSet, model_id: str, experiments_dir: Path
) -> ExperimentVariant:
    tools = load_tool_functions(tool_set.tools, experiments_dir)
    return ExperimentVariant(
        tooling_name=tool_set.name,
        model_id=model_id,
        system_prompt=tool_set.system_prompt,
        tools=tools,
    )


def resolve_case_names(
    suite: SuiteConfig, case_set_registry: dict[str, CaseSet]
) -> list[str]:
    names: list[str] = list(suite.matrix.cases)
    for ref in suite.matrix.case_sets:
        case_set = case_set_registry.get(ref)
        if case_set is None:
            raise ValueError(f"Unknown case set {ref!r}")
        names.extend(case_set.cases)
    seen: set[str] = set()
    unique: list[str] = []
    for name in names:
        if name not in seen:
            seen.add(name)
            unique.append(name)
    if not unique:
        raise ValueError(
            "Suite matrix must specify at least one case via cases or case_sets"
        )
    return unique


class ResolvedSuite(BaseModel):
    suite_name: str
    suite_path: str
    variants: list[ExperimentVariant]
    cases: list[EditCase]


def resolve_suite(
    suite_path: Path,
    experiments_dir: Path,
    cases_dir: Path,
) -> ResolvedSuite:
    suite_path = suite_path.resolve()
    experiments_dir = experiments_dir.resolve()
    suite = load_suite(suite_path)

    tool_set_registry = build_tool_set_registry(experiments_dir)
    case_set_registry = _build_case_set_registry(experiments_dir)

    variants: list[ExperimentVariant] = []
    for tool_set_name in suite.matrix.tool_sets:
        tool_set = tool_set_registry.get(tool_set_name)
        if tool_set is None:
            raise ValueError(f"Unknown tool set {tool_set_name!r}")
        for model_id in suite.matrix.models:
            variants.append(variant_from_tool_set(tool_set, model_id, experiments_dir))

    case_names = resolve_case_names(suite, case_set_registry)
    cases = load_cases_by_names(cases_dir, case_names)

    return ResolvedSuite(
        suite_name=suite_display_name(suite_path, suite),
        suite_path=str(suite_path),
        variants=variants,
        cases=cases,
    )


class MatrixRootConfig(BaseModel):
    default_suite: str = Field(default="suites/full.yaml")

    def resolve_default_suite_path(self, experiments_dir: Path) -> Path:
        path = Path(self.default_suite)
        if not path.is_absolute():
            path = experiments_dir / path
        return path.resolve()
