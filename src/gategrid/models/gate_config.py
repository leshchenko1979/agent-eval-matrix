from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class RegressionBounds(BaseModel):
    pass_rate_min_delta: float | None = None
    metric_mean_min_delta: dict[str, float] = Field(default_factory=dict)
    metric_mean_max_delta: dict[str, float] = Field(default_factory=dict)
    max_regressed_cells: int | None = None


class GateLimits(BaseModel):
    pass_rate_min: float | None = None
    metric_mean_min: dict[str, float] = Field(default_factory=dict)
    metric_mean_max: dict[str, float] = Field(default_factory=dict)
    max_regressed_cells: int | None = None


class GateRegression(BaseModel):
    baseline: str
    bounds: dict[str, RegressionBounds] = Field(
        default_factory=dict,
        description="Keys: overall, like_for_like",
    )
    min_like_for_like_share: float | None = Field(
        default=None,
        description=(
            "Min fraction of baseline cells in like-for-like intersection "
            "(0, 1]; default 1.0 when bounds.like_for_like is set"
        ),
    )

    @model_validator(mode="after")
    def validate_min_like_for_like_share(self) -> GateRegression:
        if self.min_like_for_like_share is None:
            return self
        share = self.min_like_for_like_share
        if not (0.0 < share <= 1.0):
            raise ValueError(
                "gate.regression.min_like_for_like_share must be in (0, 1]"
            )
        return self


class GateConfig(BaseModel):
    baseline: str
    regression: GateRegression | None = None
    limits: dict[str, GateLimits] = Field(
        default_factory=dict,
        description="Keys: overall, like_for_like",
    )


def metric_keys_from_gate(gate: GateConfig | None) -> set[str]:
    """Union of metric keys referenced in any gate bound dict."""
    if gate is None:
        return set()
    keys: set[str] = set()
    if gate.regression is not None:
        for bounds in gate.regression.bounds.values():
            keys.update(bounds.metric_mean_min_delta)
            keys.update(bounds.metric_mean_max_delta)
    for limits in gate.limits.values():
        keys.update(limits.metric_mean_min)
        keys.update(limits.metric_mean_max)
    return keys
