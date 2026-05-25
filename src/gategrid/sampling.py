"""Matrix cell sampling for PR-sized runs."""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass

from gategrid.cases import CaseRecord
from gategrid.models.cell import CellKey
from gategrid.models.matrix_config import SampleConfig


@dataclass(frozen=True)
class SamplingPlan:
    """Full grid keys and the subset selected for execution."""

    all_keys: list[CellKey]
    selected_keys: list[CellKey]
    skipped_keys: list[CellKey]
    seed: int


def sample_seed_from_ref(matrix_name: str, ref: str) -> int:
    """Derive a stable int seed from matrix name and CI ref (e.g. GITHUB_SHA)."""
    digest = hashlib.sha256(f"{matrix_name}:{ref}".encode()).hexdigest()
    return int(digest[:8], 16)


def sampling_budget(total_cells: int, sample: SampleConfig) -> int:
    """How many cells to execute this run."""
    if total_cells <= 0:
        return 0
    caps: list[int] = [total_cells]
    if sample.max_cells is not None:
        caps.append(sample.max_cells)
    if sample.share is not None:
        caps.append(max(1, math.ceil(sample.share * total_cells)))
    return min(caps)


def select_cell_keys(
    all_keys: list[CellKey],
    case_registry: dict[str, CaseRecord],
    sample: SampleConfig,
) -> SamplingPlan:
    """Select cells per architecture-vision sampling rules."""
    if not all_keys:
        return SamplingPlan([], [], [], sample.seed)

    budget = sampling_budget(len(all_keys), sample)
    if budget >= len(all_keys):
        return SamplingPlan(all_keys, list(all_keys), [], sample.seed)

    tag_set = set(sample.always_include_tags)
    pinned: list[CellKey] = []
    pool: list[CellKey] = []
    seen_pinned: set[tuple[str, str, str]] = set()

    for key in all_keys:
        record = case_registry.get(key.case_id)
        tags = record.tags if record is not None else []
        if tag_set and any(t in tag_set for t in tags):
            tup = key.as_tuple()
            if tup not in seen_pinned:
                pinned.append(key)
                seen_pinned.add(tup)
        else:
            pool.append(key)

    selected: list[CellKey] = list(pinned)
    selected_set = {k.as_tuple() for k in selected}
    remaining = budget - len(selected)

    if remaining > 0 and pool:
        rng = random.Random(sample.seed)
        shuffled = list(pool)
        rng.shuffle(shuffled)
        for key in shuffled:
            if remaining <= 0:
                break
            if key.as_tuple() not in selected_set:
                selected.append(key)
                selected_set.add(key.as_tuple())
                remaining -= 1

    if len(selected) > budget:
        selected = selected[:budget]

    selected_tuples = {k.as_tuple() for k in selected}
    skipped = [k for k in all_keys if k.as_tuple() not in selected_tuples]
    return SamplingPlan(all_keys, selected, skipped, sample.seed)
