# CI and regression gates

Gategrid does not run CI for you — you wire GitHub Actions (or any runner) to `gategrid run` and `gategrid gate`. Artifacts live under `.gategrid/` or `GATEGRID_HOME`.

**Product context:** [README-pitch-draft.md](../roadmap/product/README-pitch-draft.md) · [architecture-vision.md](../roadmap/engineering/architecture-vision.md) · [ADR 0007](../adr/0007-gategrid-phase5-ci-productization.md)

---

## PR vs main

| Job | Commands | Baseline |
| --- | -------- | -------- |
| **PR** | `run` → `gate` | Committed fixture or artifact from latest `main` — **never** `baseline update` |
| **`main`** | full `run` → `gate` → `baseline update` | Refresh golden under `$GATEGRID_HOME/baselines/<profile>.json`; upload or commit |

Use the **same gate matrix** on PR and `main` (one profile per lane). Benchmark matrices (many profiles, no `gate:`) are for research only — see [examples/opencrabs/matrices/hashline-bench.yaml](../../examples/opencrabs/matrices/hashline-bench.yaml). They do **not** define PR pass/fail; never block merges on bench `pass_rate`. How to read bench JSON (profile×case grid, retries, infra vs eval failures): [bench-analysis.md](bench-analysis.md).

---

## Three layers of pass

1. **Cell** — all `gate` evaluators pass on ≥1 attempt (`run.max_retries` for flake).
2. **Regression** — overall and/or like-for-like vs baseline (`gate.regression.bounds`).
3. **Limits** — hard floors on **this run** (`gate.limits`) when PR env may differ from `main`.

---

## Overall vs like-for-like

- **Overall** — aggregates over all **executed** cells in the report.
- **Like-for-like** — only cell keys present in **both** the report and the baseline file.

On **`main`**, run the **full** grid (no `run.sample`) and refresh the baseline.

On **PR**, prefer:

- `run.sample` to cap cell count (see below), and
- **`like_for_like` regression only** on sampled matrices — do not use `overall` regression bounds on PR samples (overall on a subset is not comparable to a full-grid baseline).

Fingerprint mismatch (matrix name, profiles, or case ids) emits a **warning** when `gate.regression` is configured; like-for-like still runs.

### Like-for-like representativeness

When a matrix defines `gate.regression.bounds.like_for_like`, gate computes:

```text
like_for_like_share = |cells in both report and baseline| / |baseline cells|
```

- **`gate.regression.min_like_for_like_share`** — minimum share in `(0, 1]`. If omitted, **defaults to 1.0** (every baseline cell must appear in the report).
- Check **`regression.like_for_like.intersection_share`** must pass before pass-rate / metric regression on the LFL subset.
- **PR matrices with `run.sample`** should set an explicit lower minimum (e.g. `0.5` in `ci-gate-pr-mock.yaml`) when the PR run is not expected to cover the full baseline grid.
- Wrong `model_id` (or `--model` override vs baseline) → share **0** → gate fails (no silent pass).

---

## Flake vs cost control

| Config | Purpose |
| ------ | ------- |
| `run.max_retries` | Re-run the **same cell** until a gate attempt passes (use on LLM matrices; mock CI often uses `0`). |
| `run.sample` | Run a **subset of cells** (`max_cells`, `share`, `seed`, `always_include_tags`). |

**Not the same** as Phase 6 [statistical replication](../roadmap/engineering/v1-implementation-checklist.md#phase-6--post-v1-defer) or [wall-time budget](../roadmap/engineering/v1-implementation-checklist.md#phase-6--post-v1-defer).

---

## Baseline sources

| Source | Path | When |
| ------ | ---- | ---- |
| Runtime | `$GATEGRID_HOME/baselines/<profile>.json` | Local / `main` job after `baseline update` |
| Committed fixture | e.g. `examples/gategrid/ci/baselines/demo.json` | Fork PRs, offline gate |
| CI artifact | `baselines/<profile>.json` at artifact root | Same-repo PR via `gate --baseline-from-artifact` |

**Regen fixture:** run full grid → `baseline update --matrix … --profile …` → copy JSON into `ci/baselines/`.

---

## Example workflow (mock, no API keys)

This repo ships [`.github/workflows/gategrid-ci.yml`](../../.github/workflows/gategrid-ci.yml):

- **test** — scoped pytest + `validate`
- **gate-pr** — `ci-gate-mock` + gate vs committed baseline
- **baseline-main** — refresh baseline artifact on `main` push

```yaml
env:
  GATEGRID_HOME: ${{ github.workspace }}/.gategrid-ci
  GATEGRID_EVAL_ROOT: examples/gategrid

- run: uv run gategrid run --matrix examples/gategrid/matrices/ci-gate-mock.yaml --root examples/gategrid
- run: uv run gategrid gate --matrix examples/gategrid/matrices/ci-gate-mock.yaml \
      --baseline examples/gategrid/ci/baselines/demo.json
```

PR sampling example: [examples/gategrid/matrices/ci-gate-pr-mock.yaml](../../examples/gategrid/matrices/ci-gate-pr-mock.yaml). Set `run.sample.seed` in YAML for reproducibility; optional env-derived hashing (`sample_seed_from_ref`) is documented in ADR 0007 for future CI wiring.

---

## Tiered CI (this monorepo)

| Tier | Trigger | What runs |
| ---- | ------- | --------- |
| **Demo** | every PR / push | pytest phases 0–5, `ci-gate-mock` gate |
| **Smoke** | `workflow_dispatch` | hashline-smoke (needs pydantic-ai extra) |
| **Full** | `workflow_dispatch` | hashline-bench / live MCP (secrets required) |

Copy [`.github/workflows/gategrid.yml.example`](../../.github/workflows/gategrid.yml.example) into your repo and adjust matrices.
