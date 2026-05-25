# Dogfood spike diary

Personal log for [Gategrid](../product/README-pitch-draft.md) spikes (**order: OpenCrabs → ai-antispam → fast-mcp-telegram**):

1. [opencrabs](https://github.com/leshchenko1979/opencrabs)
2. [ai-antispam](https://github.com/leshchenko1979/ai-antispam)
3. [fast-mcp-telegram](https://github.com/leshchenko1979/fast-mcp-telegram)

Checklist: [v1-implementation-checklist.md#dogfooding-spikes](../engineering/v1-implementation-checklist.md#dogfooding-spikes) · [Spike → contrib](../engineering/v1-implementation-checklist.md#spike--contrib) · **[Spike DX analysis](spike-dx-competitive-analysis.md)** (required)

**Per spike:** (1) **DX kickoff** brief in this file before coding past smoke — see [spike brief template](spike-dx-competitive-analysis.md#spike-brief-template). (2) **Contrib promotion:** what stayed in `evals/` vs **`gategrid.contrib`**. (3) **DX close:** measured LOC + Task A/B/C winners → [decision log](spike-dx-competitive-analysis.md#decision-log).

---

## Go / no-go (fill when D.8)

| Criterion | Met? | Notes |
| --------- | ---- | ----- |
| PR-style `gate` trustworthy | | |
| Git baseline simpler than alternatives | | |
| New case under 30 min | | |
| Gate caught real regression | | |

**Decision:** _go / narrow / pause_ — _date_

---

## Spike C — OpenCrabs (1st)

### DX analysis (close — 2026-05-25)

| Task | Winner | Notes |
| ---- | ------ | ----- |
| A — first green cell | Tie: Gategrid [examples/file_edit/](../../../examples/file_edit/) vs pydantic-evals one-file Dataset | OpenCrabs smoke is not the minimal path |
| B — 5×10 bench | promptfoo / pydantic-evals for **orchestration** | ~1.5k LOC is **tooling under test**, not framework |
| C — regression gate | **Gategrid** | `hashline-gate` + `gate` + baselines |

Full write-up: [spike-dx-competitive-analysis.md#spike-c--opencrabs-retroactive-2026-05](spike-dx-competitive-analysis.md#spike-c--opencrabs-retroactive-2026-05).

**Layout:** [examples/opencrabs/](../../../examples/opencrabs/) in this monorepo (consumer repos use repo-root `evals/`).

**Policy:** Gategrid-only for **gated** results (`gategrid run` / `baseline update` / `gate` only). Legacy `experiments/` + `agent_eval_matrix` removed 2026-05 ([teardown L.1–L.4](../engineering/v1-implementation-checklist.md#legacy-teardown-after-spike-c)).

| Promoted to framework | Stays in example tree |
| --------------------- | --------------------- |
| `gategrid.models.env`, `gategrid.integrations.pydantic_ai`, `contrib.file_edit` (sandbox, session, `file_content_match`, **batteries**: hashline cases + baseline tools, `load_file_edit_tools`, profile `data` helpers) | `adapters/file_edit.py`, OpenCrabs tooling + fuzzy stack, opencrabs profiles, matrices |

**Smoke (no API key):** `gategrid run --matrix examples/opencrabs/matrices/hashline-smoke.yaml --root examples/opencrabs`.

| Date | Command / matrix | Result | Verdict |
| ---- | ---------------- | ------ | ------- |
| 2026-05-24 | `hashline-smoke` (mock) + pytest `test_gategrid_spike_c` | 1/1 pass | smoke OK |
| 2026-05-24 | `hashline-gate` (minimax, 4 cases) | 4/4 pass | [report](../../.gategrid/reports/2026-05-24T194019.9_matrix.json) |
| 2026-05-24 | `baseline update` + `gate` on that report | gate exit 0 | C.3 OK |
| 2026-05-24 | C.4 regression drill (bad report → gate exit 1, good → 0) | PASS / FAIL as expected | C.4 OK |
| 2026-05-24 | Parity: `indent_collision`, `add_docstring_large` vs legacy | both cells: legacy==gategrid `passed` | D.4 parity OK |
| 2026-05-24 | `hashline-bench` (5×10, minimax, ~8.7 min) | 44/50 pass; 2×429 rate limit, 4×`rename_symbol_large` gate fail — [report](../../.gategrid/reports/2026-05-24T195718.2_matrix.json) | C.6 run OK (not all green) |
| 2026-05-25 | `hashline-bench` `-v` (5×10, minimax, ~16 min) | 44/50; `run_max_retries: 0`; no 429s; different failing cells vs May 24 / published report — [report](../../.gategrid/reports/2026-05-25T102351.0_matrix.json); stability [§10](../../reports/hashline/hashline_hypothesis_report.md#run-stability) | C.6/C.7 — aggregate pass rate noisy |

Notes:

- **Roadmap — 429 handling:** MiniMax returned HTTP 429 on 2/50 `hashline-bench` cells (infra, not eval logic). Tracked as **ADOPT-020** / [Phase 6.8](../engineering/v1-implementation-checklist.md#phase-6--post-v1-defer) — transport-level retry + backoff at LLM boundary, separate from `run.max_retries`.
- **Contrib candidates:** _e.g. file_edit sandbox/tools, opencrabs tool adapter — promote when API stable_
- Tooling and profiles live in [`examples/opencrabs/`](../../../examples/opencrabs/); case bodies are **builtin** contrib batteries (duplicate `cases/yaml/` removed 2026-05-25).
- Report / upstream doc: [hashline_hypothesis_report.md](../../reports/hashline/hashline_hypothesis_report.md) — §10 run stability; bench analysis [guide](../../guides/bench-analysis.md).
- **C.6/C.7:** bench headline 44/50 can repeat while **cells flip** — use profile×case attribution and `run_max_retries`, not one JSON verdict.

---

## Spike B — ai-antispam (2nd)

### DX analysis kickoff — 2026-05-25

- **Doc:** [spike-dx-competitive-analysis.md](spike-dx-competitive-analysis.md)
- **Task A:** One `@case` (ham or spam fixture) + `mock` model; `spam-smoke` matrix; gate evaluator checks `metrics.expected_label` (no live LLM).
- **Task B:** Curated **~15** fixtures from [ai-antispam `tests/`](https://github.com/leshchenko1979/ai-antispam/tree/main/tests) (integration + handler samples) × **1** gate profile (`classifier-candidate`); optional **bench** matrix with 2 prompt/model variants (no PR gate on bench).
- **Task C:** `spam-gate.yaml` — one profile, `gate.baseline: classifier-candidate`, local `baseline update` + `gate`; CI workflow after [Phase 5](../engineering/v1-implementation-checklist.md#phase-5--ci-productization). **B.7:** deliberate mis-label run → gate exit 1.
- **Domain vs orchestration:** **Domain** — `is_spam` + `SpamClassificationContext` + fixture payloads (stay in ai-antispam `src/`). **Orchestration** — `evals/` adapter (~80 LOC), `@case` registrations, label `@evaluator`, 2–3 matrix YAML, profiles/models (~120 LOC est.).
- **Expected Task B winner:** **DeepEval** or **pydantic-evals** for a flat pytest-style classifier suite; **Gategrid** if we need profile × model grid + same gate path as OpenCrabs.
- **Gategrid wedge:** Task **C** — git baseline on classification pass rate / label agreement; matrix runner for “prompt A vs B on same fixture set” without Confident AI.

Full table: [spike-dx-competitive-analysis.md#spike-b--ai-antispam](spike-dx-competitive-analysis.md#spike-b--ai-antispam).

| Date | Command | Result | Verdict |
| ---- | ------- | ------ | ------- |
| | | | |

Notes:

- Fixtures source: `tests/` in ai-antispam
- Deliberate regression experiment (B.7):

---

## Spike A — fast-mcp-telegram (3rd)

### DX analysis kickoff — 2026-05-25

- **Doc:** [spike-dx-competitive-analysis.md](spike-dx-competitive-analysis.md)
- **Task A:** Reuse [examples/gategrid/matrices/mcp-gate-mock.yaml](../../../examples/gategrid/matrices/mcp-gate-mock.yaml) pattern; add **telegram-smoke** in target repo with **mock** or stub MCP (no Saved Messages write). Document test-account policy for live cells.
- **Task B:** **~5–8** `@case` prompts (discovery, `get_messages`, dry-run send) × **1** profile (`telegram-mcp-stdio`, `profile.data.mcp` from [ADR 0006](../../adr/0006-gategrid-phase4-mcp-path.md) Path B) × 1 model; optional second profile for HTTP bridge vs stdio bench only.
- **Task C:** `telegram-gate` matrix + committed baseline; PR via `workflow_dispatch` + secrets (`TELEGRAM_*`, bearer token) until Phase 5 PR gate workflow lands.
- **Domain vs orchestration:** **Domain** — MCP server in [fast-mcp-telegram](https://github.com/leshchenko1979/fast-mcp-telegram) (unchanged). **Orchestration** — `evals/adapters/` Path B loop (~100 LOC), cases, matrices (~150 LOC est.); reuse `gategrid.contrib.mcp`.
- **Expected Task B winner:** **mcp-eval** for tool-sequence / OTEL assertions on real MCP; **Gategrid** for cases × models grid + git gate.
- **Gategrid wedge:** Task **C** + matrix expansion; contrib MCP config already shipped — spike proves Path B on production Telegram MCP.
- **mcp-eval (hypothesis):** Task A faster with `@task` + `Expect.tools.was_called` (~50 LOC); Task B strong on trace assertions; weak on per-profile baseline JSON in git.

Full table: [spike-dx-competitive-analysis.md#spike-a--fast-mcp-telegram](spike-dx-competitive-analysis.md#spike-a--fast-mcp-telegram).

| Date | Command | Result | Verdict |
| ---- | ------- | ------ | ------- |
| | | | |

Notes:

- Test account / Saved Messages only for writes
- CI: secrets / workflow_dispatch

---

## Blockers

| Repo | Blocker | Workaround |
| ---- | ------- | ---------- |
