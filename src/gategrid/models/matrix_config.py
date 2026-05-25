from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from gategrid.models.gate_config import GateConfig


class SampleConfig(BaseModel):
    max_cells: int | None = None
    share: float | None = None
    seed: int = 0
    always_include_tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_sample_bounds(self) -> SampleConfig:
        if self.max_cells is not None and self.max_cells < 1:
            raise ValueError("run.sample.max_cells must be >= 1 when set")
        if self.share is not None and not (0.0 < self.share <= 1.0):
            raise ValueError("run.sample.share must be in (0, 1] when set")
        if self.max_cells is None and self.share is None:
            raise ValueError("run.sample requires max_cells and/or share")
        return self


class RunConfig(BaseModel):
    max_retries: int = 0
    sample: SampleConfig | None = None


class MatrixConfig(BaseModel):
    name: str | None = None
    cases: list[str] = Field(default_factory=list)
    case_sets: list[str] = Field(default_factory=list)
    profiles: list[str] = Field(default_factory=list)
    models: list[str] = Field(default_factory=list)
    gate: GateConfig | None = None
    run: RunConfig = Field(default_factory=RunConfig)

    @model_validator(mode="after")
    def require_cases_and_axes(self) -> MatrixConfig:
        if not self.cases and not self.case_sets:
            raise ValueError("matrix must include cases and/or case_sets")
        if not self.profiles:
            raise ValueError("matrix must include profiles")
        if not self.models:
            raise ValueError("matrix must include models")
        return self
