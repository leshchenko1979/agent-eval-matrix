# LLM File-Editing Eval Harness

Evaluation harness for a **pure file-editing** pydantic-ai agent. **Tool sets** and **case sets** are YAML libraries; each **suite** file declares a `matrix:` (tool_sets × models × cases). Per-tool code lives under `experiments/tooling/` (one function per `.py`).

## Setup

```bash
cd harness_test
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# Set MINIMAX_API_KEY
```

## Run

**Full suite** (default from [`experiments/matrix.yaml`](experiments/matrix.yaml)):

```bash
python -m harness.matrix run
```

**CI / smoke suite:**

```bash
python -m harness.matrix run --suite experiments/suites/ci.yaml
```

**Single variant:**

```bash
python -m harness.matrix run --variant baseline/minimax-m2.7
```

**One case:**

```bash
python -m harness.evals run --case add_docstring
python -m harness.evals run --case add_docstring --tool-set minimal
```

**JSONL traces** (no Logfire):

```bash
python -m harness.matrix run --trace
```

## Suite format

[`experiments/suites/full.yaml`](experiments/suites/full.yaml):

```yaml
matrix:
  tool_sets:
    - baseline
    - minimal
    - strict/verbose
    - opencrabs_original
  models:
    - minimax-m2.7
  case_sets:
    - all
```

Suite `name` is optional (defaults to the file stem, e.g. `ci.yaml` → `ci`).

## Tool set format

[`experiments/tool_sets/baseline.yaml`](experiments/tool_sets/baseline.yaml) — prompt + list of per-tool `.py` paths (no bundling in Python):

```yaml
name: baseline
system_prompt: |
  You are a precise file editing agent...
tools:
  - tooling/harness/ls.py
  - tooling/harness/read_file.py
  # ...
```

## New tool set

1. Add one-tool modules under `experiments/tooling/` (delegate to [`src/harness/tools.py`](src/harness/tools.py) or opencrabs helpers).
2. Create `experiments/tool_sets/my_set.yaml` with `name`, `system_prompt`, and `tools:`.
3. Reference `my_set` in a suite `matrix.tool_sets` list.

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `MINIMAX_API_KEY` | — | Required for MiniMax |
| `OPENAI_BASE_URL` | `https://api.minimax.io/v1` | OpenAI-compatible endpoint |
| `HARNESS_MODEL` | `MiniMax-M2.7` | Model name |
| `LOGFIRE_TOKEN` | — | Optional cloud traces |

Use workspace-relative paths in tool calls (e.g. `app.py`). The harness normalizes absolute paths inside the sandbox.

## Reports

- Aggregate JSON: `reports/{timestamp}_{sha}_matrix.json`
- Optional traces: `reports/traces/{run_id}.jsonl`

## CI

`.github/workflows/evals.yml` — set `MINIMAX_API_KEY` secret; optional `LOGFIRE_TOKEN`.
