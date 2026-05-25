# ADR 0007: Gategrid Phase 5 — CI productization

**Status:** accepted (2026-05-25)

## Context

Phases 0–4 froze schemas, executor, evaluators, and MCP examples. Phase 5 wires **git-native CI**: PR `gate`, `main` baseline refresh, PR cell sampling, and copy-paste workflows — without legacy harness or cloud baselines.

## Decisions

| Topic | Decision |
| ----- | -------- |
| PR baseline | `gate --baseline-from-artifact PATH` resolves file, `PATH/baselines/<profile>.json`, or `PATH/<profile>.json` |
| Committed fixture | Repo may ship golden JSON (e.g. `examples/gategrid/ci/baselines/`) for forks; runtime baselines still under `$GATEGRID_HOME` |
| `baseline update` | `--matrix` passes `metric_keys_from_gate` into baseline `overall.metrics` |
| PR workflow | Never `baseline update` on PR; `main` may upload artifact (no auto-commit by default) |
| `run.sample` | Seeded subset; `always_include_tags`; budget `min(max_cells, ceil(share × total))` when both set |
| Fingerprint when sampling | Full matrix `case_ids` + `profiles`; aggregates only over **executed** cells |
| PR regression on sample | Matrices with `run.sample` should use **`like_for_like` bounds only** — not `overall` regression vs full-grid baseline |
| LFL representativeness | `gate.regression.min_like_for_like_share` in `(0, 1]`; when `bounds.like_for_like` is set, effective minimum **1.0** if omitted. Share = \|intersection\| / \|baseline.cells\|. Failing check `regression.like_for_like.intersection_share` before other LFL regression checks. PR matrices with sampling set an explicit lower share (e.g. `0.5` in `ci-gate-pr-mock`) |
| Seed from CI ref | Hash `sha256(matrix:ref)` to int — not raw `GITHUB_SHA` string |
| Flake | Document `run.max_retries` for LLM; mock CI uses retries only where needed |
| Deferred | [6.9](../roadmap/engineering/v1-implementation-checklist.md#phase-6--post-v1-defer) statistical replication; [6.10](../roadmap/engineering/v1-implementation-checklist.md#phase-6--post-v1-defer) `run.max_wall_time_s`; `gate.regression.scope` YAML field; gate-time re-runs; marketplace Action |

## Examples

| Matrix | Role |
| ------ | ---- |
| `examples/gategrid/matrices/ci-gate-mock.yaml` | Full grid gate + limits (CI) |
| `examples/gategrid/matrices/ci-gate-pr-mock.yaml` | PR sample + LFL regression only |
| `examples/opencrabs/matrices/hashline-gate.yaml` | Live gate dogfood |
| `examples/opencrabs/matrices/hashline-bench.yaml` | Multi-profile benchmark (no gate) |

## Consequences

- `docs/guides/ci.md` is the CI hub; README links here instead of duplicating sampling spec.
- Phase 5 tests in `tests/test_gategrid_phase5.py`; workflow `gategrid-ci.yml` uses scoped pytest.

## See also

- [0001-gategrid-phase0-schemas-cli-gate.md](0001-gategrid-phase0-schemas-cli-gate.md)
- [v1-implementation-checklist.md](../roadmap/engineering/v1-implementation-checklist.md)
