# Bench matrix analysis

How to read **benchmark** matrix results (`*-bench.yaml`) without treating them like **CI gates**. For PR workflows, baselines, and regression bounds, see [CI and regression gates](ci.md).

**Product context:** [architecture-vision.md](../roadmap/engineering/architecture-vision.md) (three levels of pass) · [ADR 0007](../adr/0007-gategrid-phase5-ci-productization.md)

---

## Matrix roles

| Role | YAML pattern | Purpose |
| ---- | ------------ | ------- |
| **Smoke** | Small case list, often `mock` model | Fast sanity — no secrets |
| **Gate** | `gate:` block, usually one profile | PR / `main` regression vs baseline |
| **Bench** | Many profiles, **no** `gate:` | Research — compare tool variants |

**Do not block PRs on bench `pass_rate`.** Bench matrices explore variance across profiles; gates enforce regression on a frozen subset.

Example: [hashline-gate.yaml](../../examples/opencrabs/matrices/hashline-gate.yaml) (gate) vs [hashline-bench.yaml](../../examples/opencrabs/matrices/hashline-bench.yaml) (bench). Commands: [examples/opencrabs/README.md](../../examples/opencrabs/README.md).

---

## Analyst checklist

After `gategrid run --matrix …`:

1. Open `.gategrid/reports/*_matrix.json` (or `GATEGRID_HOME/reports/`).
2. Read top-level **`run_max_retries`** and confirm **attempts per cell** (length of `attempts[]`) — one attempt per cell when `run_max_retries` is 0.
3. Build a **profile × case** pass view from `cells[].key` and `cells[].passed` (headline `overall.pass_rate` can hide cell flips).
4. **Classify failures** via `cells[].error` and attempt artifacts:
   - **Eval** — e.g. `file_content_match`, gate evaluator messages
   - **Infra** — HTTP 429 / rate limits (not a tool-design regression)
   - **Tool budget** — e.g. `Tool 'read_file' exceeded max retries` (adapter-internal, not Gategrid `run.max_retries`)
5. Note **`flaky_suspect`** only when `run.max_retries > 0` and attempts disagree.
6. For hypothesis matrices, compare each variant to a **reference profile** (OpenCrabs hashline: `opencrabs_original`).

Verdict labels for the hashline study (**Supported / Rejected / Inconclusive / Mixed**) live in [hashline_hypothesis_report.md §2–§3](../reports/hashline/hashline_hypothesis_report.md#2-quick-reference-for-implementers) — do not invent a parallel rubric here.

---

## Retry layers

Three different mechanisms are often confused:

| Layer | Config | Meaning |
| ----- | ------ | ------- |
| **Cell flake retry** | Matrix `run.max_retries` | Gategrid re-runs the **whole cell** until a gate attempt passes or retries exhaust; sets `flaky_suspect` when attempts disagree |
| **Tool retry** | Runtime adapter (e.g. pydantic-ai) | Retries **inside** one cell attempt — shows up in `error` / tool messages, not in `run_max_retries` |
| **Statistical replication** | Phase [6.9](../roadmap/engineering/v1-implementation-checklist.md#phase-6--post-v1-defer) (not in v1) | N **independent** bench runs per cell — not the same as `max_retries` |

**Bench research** often uses `run.max_retries: 0` for a strict single sample per cell. **CI gate** matrices may set `run.max_retries: 1+` for eval flake — see [Flake vs cost control](ci.md#flake-vs-cost-control).

### OpenCrabs example (May 2026 stability rerun)

[hashline-bench.yaml](../../examples/opencrabs/matrices/hashline-bench.yaml) has no `run:` block → default **`run_max_retries: 0`**. Report [2026-05-25T102351.0_matrix.json](../../.gategrid/reports/2026-05-25T102351.0_matrix.json): 50 cells, one attempt each, no `flaky_suspect`. Run-to-run variance vs the published report is **single-trajectory LLM noise**, not cell-level retries.

Stability comparison (artifact paths, per-profile failures, H2 second-run note): [hashline_hypothesis_report.md §10 Run stability](../reports/hashline/hashline_hypothesis_report.md#run-stability).

---

## Future replication

Independent bench runs (N≥2) before upstream “supported/rejected” claims are **manual** until Phase **6.9** (*Statistical cell replication*). Until then, treat **one bench JSON as a hypothesis generator**, not proof. Compare runs by diffing cell `passed` bits (product helper planned as checklist **6.11**).

---

## Related

| Topic | Doc |
| ----- | --- |
| CI, baselines, LFL, sampling | [ci.md](ci.md) |
| OpenCrabs matrices | [examples/opencrabs/README.md](../../examples/opencrabs/README.md) |
| Hashline report | [docs/reports/hashline/README.md](../reports/hashline/README.md) |
| Coding invariants | [CODE.md](../../CODE.md#bench-vs-gate-analytics) |
