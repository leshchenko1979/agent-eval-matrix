# harness_test — LLM file-editing eval harness

## Purpose

Matrix evals over **cases** (YAML) × **tool sets** (YAML) × **models** (presets in `config.py`). Suites declare the runnable `matrix:`; tool sets hold `system_prompt` + `tools:` paths; each `.py` under `tooling/` exports one tool function.

## Run locally

```bash
source .venv/bin/activate
pip install -e ".[dev]"
# .env: MINIMAX_API_KEY

python -m harness.matrix run
python -m harness.matrix run --suite experiments/suites/ci.yaml
python -m harness.evals run --case add_docstring --tool-set baseline
python -m harness.matrix run --variant strict/verbose/minimax-m2.7
```

## Layout

- `experiments/tool_sets/` — agent prompts + tool path lists (YAML only bundling)
- `experiments/case_sets/` — named case lists
- `experiments/suites/` — required `matrix:` block per runnable suite
- `experiments/cases/` — case content (one YAML per case)
- `experiments/tooling/harness/` — thin wrappers over `harness.tools` (one tool per file)
- `experiments/tooling/opencrabs/` — OpenCrabs-style tools (one tool per file)
- `experiments/matrix.yaml` — `default_suite:` pointer only
- `src/harness/` — loader, sandbox, suites resolver, matrix CLI

## Tooling rules

- **No** `SYSTEM_PROMPT`, `TOOLS`, or `register(agent)` bundles in `.py` files.
- **Harness tools**: `tooling/harness/*.py` → `harness.tools`.
- **OpenCrabs tools**: `tooling/opencrabs/*.py`; composed via `tool_sets/opencrabs_original.yaml`.

## Paths

- Models should use **workspace-relative** paths (`app.py`).
- `harness.sandbox` canonicalizes macOS `/private/var` vs `/var` and accepts absolutes inside the workspace.

## Models

- Presets in `src/harness/config.py` (`MODEL_PRESETS`).
- Suite `matrix.models` lists preset keys (e.g. `minimax-m2.7`).

## Hashline hypothesis suite

Isolated OpenCrabs variants (H1 doc fix, H2 fuzzy `str_replace`, H3 empty-hash collisions) vs `opencrabs_original` and `baseline`:

```bash
python -m harness.matrix run --suite experiments/suites/hashline_hypotheses.yaml
```

**10 cases** (4 small + 6 large ~100–150 lines): indent traps, ambiguous replace, hash collisions, docstring insert, rename — **50 matrix runs** (5 variants × 10 cases).

Pass/fail is still **file content match** only; `print_summary` adds hypothesis deltas, H4 pass rates by `language:python` / `language:yaml`, and `size:large` vs small buckets.

**Report for OpenCrabs upstream:** [docs/hashline_hypothesis_report.md](docs/hashline_hypothesis_report.md) (prose), [docs/hashline_hypothesis_report.ipynb](docs/hashline_hypothesis_report.ipynb) (charts). Index: [docs/README.md](docs/README.md). Regenerate figures: `pip install -e ".[report]"` then `python docs/_build_report_viz.py`.

## Run metrics (comparison only; pass/fail = file match)

- **turns** — `RunUsage.requests` from `agent.run()` (LLM rounds, not `tool_calls`)
- **tokens_spent** — sum of canonical `RunUsage` token fields + `details` (not `total_tokens`)
- **tool_failures** — sum of `metrics` keys ending in `_failures` from harness tools
- **duration_ms** — pydantic-evals `task_duration` on the report row
- Raw span/tool counters remain in `CaseResult.metrics` for debugging

## Observability

- Default: stdout + `reports/*.json`
- Logfire: `LOGFIRE_TOKEN`, `send_to_logfire='if-token-present'`
- `--trace` → `reports/traces/*.jsonl`
