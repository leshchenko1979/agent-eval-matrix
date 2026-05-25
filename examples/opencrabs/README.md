# OpenCrabs hashline example

Full **Gategrid** eval tree for the OpenCrabs file-editing hypothesis study: five profile variants × ten cases, OpenCrabs-style Python tools, and optional reference/fuzzy tooling.

**Report:** [docs/reports/hashline/hashline_hypothesis_report.md](../../docs/reports/hashline/hashline_hypothesis_report.md) · **CI:** [docs/guides/ci.md](../../docs/guides/ci.md) · **Bench analysis:** [docs/guides/bench-analysis.md](../../docs/guides/bench-analysis.md) · **Framework:** [README.md](../../README.md)

Run from this directory with `--root .`, or from the repo root with `--root examples/opencrabs` (or `GATEGRID_EVAL_ROOT=examples/opencrabs`).

```bash
cd examples/opencrabs
# From repo root first: uv sync --extra dev --extra pydantic-ai
```

## Matrices

| Matrix | API key | Role |
| ------ | ------- | ---- |
| [hashline-smoke.yaml](matrices/hashline-smoke.yaml) | No (`mock`) | One case, fast sanity — [CI tier: dispatch](../../.github/workflows/gategrid-ci.yml) |
| [hashline-gate.yaml](matrices/hashline-gate.yaml) | Yes (`MINIMAX_API_KEY`) | **Gate** — one profile, `gate.baseline`, regression bounds |
| [hashline-bench.yaml](matrices/hashline-bench.yaml) | Yes | **Benchmark** — five profiles, full case set, no `gate:` |
| [parity-*.yaml](matrices/) | Yes | Single-case parity runs (optional) |

Case ids for bench/gate sets come from the **builtin** hashline battery (`gategrid.contrib.file_edit.bundled` / `case_sets: [hashline_hypotheses]`). Smoke lists explicit `cases:`.

## Gate vs benchmark

| | **Gate** (`hashline-gate`) | **Benchmark** (`hashline-bench`) |
| - | -------------------------- | -------------------------------- |
| Profiles | One (`opencrabs_original`) | Five (H1–H3 + `baseline` + original) |
| Baseline / PR block | `gate.baseline` + regression | Reports only — no PR gate |
| CI in this repo | Manual / nightly (needs API key) | Research runs, not in default PR workflow |

How to analyze bench results (retries, cell-level stability, failure types): [docs/guides/bench-analysis.md](../../docs/guides/bench-analysis.md). Published hashline stability notes: [report §10 Run stability](../../docs/reports/hashline/hashline_hypothesis_report.md#run-stability).

Mock CI for regression gating without secrets lives in [examples/gategrid/](../gategrid/) (`ci-gate-mock.yaml`).

## Run

### Smoke (no API key)

```bash
uv run gategrid validate --matrix matrices/hashline-smoke.yaml --root .
uv run gategrid run --matrix matrices/hashline-smoke.yaml --root .
```

From repo root:

```bash
uv run gategrid run --matrix examples/opencrabs/matrices/hashline-smoke.yaml --root examples/opencrabs
```

### Gate (MiniMax)

```bash
export MINIMAX_API_KEY=...
uv run gategrid validate --matrix matrices/hashline-gate.yaml --root .
uv run gategrid run --matrix matrices/hashline-gate.yaml --root .
REPORT=$(ls -t "${GATEGRID_HOME:-../../.gategrid}"/reports/*_matrix.json | head -1)
uv run gategrid gate --matrix matrices/hashline-gate.yaml --root . \
  --report "$REPORT" \
  --profile opencrabs_original
```

First-time baseline (after a good full gate run on `main`):

```bash
uv run gategrid baseline update --from-report "$REPORT" \
  --profile opencrabs_original \
  --matrix matrices/hashline-gate.yaml
```

Baselines live under `.gategrid/baselines/opencrabs_original.json` (gitignore reports; commit baseline if your team gates on it). PR workflow pattern: [docs/guides/ci.md](../../docs/guides/ci.md) (`gate --baseline-from-artifact` for `main` artifacts).

### Benchmark (MiniMax)

```bash
export MINIMAX_API_KEY=...
uv run gategrid run --matrix matrices/hashline-bench.yaml --root .
```

No `baseline update` on bench matrices — compare profiles from report JSON under `.gategrid/reports/`.

## Using another model

Default live preset is `minimax-m2.7`. To try another provider without editing bench YAML:

```bash
cp models/_template.yaml models/my-claude.yaml   # from examples/gategrid/models/_template.yaml
# edit api_key_env, model_name, base_url, provider

export ANTHROPIC_API_KEY=...
uv run gategrid validate --matrix matrices/hashline-bench.yaml --root . --model my-claude
uv run gategrid run --matrix matrices/hashline-bench.yaml --root . --model my-claude
```

[`openai-mini.yaml`](models/openai-mini.yaml) is included for OpenAI-compatible hosts. **Gate note:** [hashline-gate.yaml](matrices/hashline-gate.yaml) uses `overall` regression only today; [like-for-like representativeness](../../docs/guides/ci.md#like-for-like-representativeness) applies when a matrix defines `bounds.like_for_like`. Wrong `--model` vs baseline `model_id` fails `intersection_share` on gated matrices.

## Layout

| Path | Role |
| ---- | ---- |
| [matrices/](matrices/) | `hashline-smoke`, `hashline-gate`, `hashline-bench`, parity matrices |
| [profiles/](profiles/) | `opencrabs_original`, H1–H3 variants, `baseline` reference |
| [models/](models/) | `mock.yaml`, `minimax-m2.7.yaml`, `openai-mini.yaml` |
| [tooling/opencrabs/](tooling/opencrabs/) | Ported OpenCrabs tools (one function per file) |
| [adapters/file_edit.py](adapters/file_edit.py) | `PydanticAiFileEditAdapter` runtime |

**Tooling rules:** No `SYSTEM_PROMPT` / `TOOLS` bundles in `.py` files. Profile lists tool paths under `data.tools` and prompts under `data.system_prompt`.

## vs `examples/gategrid/` and `examples/file_edit/`

| Tree | Use when |
| ---- | -------- |
| [examples/gategrid/](../gategrid/) | Mock CI gate, MCP smoke, PR `run.sample` demo |
| [examples/file_edit/](../file_edit/) | Minimal file-edit path; same builtin cases, one profile |
| **This tree** | Full hashline hypothesis bench + live MiniMax gate |

## Dogfood index

[examples/dogfood/README.md](../dogfood/README.md) · Spike C notes: [docs/roadmap/research/dogfood-notes.md](../../docs/roadmap/research/dogfood-notes.md)
