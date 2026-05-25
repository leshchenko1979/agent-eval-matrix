# Gategrid example eval tree

Minimal layout for `gategrid validate`, `run`, `gate`, and `baseline update` (Phase 2–5).

**Run from this directory** (`examples/gategrid`) with `--root .` below. From the repo root, prefix matrix paths with `examples/gategrid/` and use `--root examples/gategrid` (or set `GATEGRID_EVAL_ROOT=examples/gategrid`).

```bash
cd examples/gategrid
uv sync --extra dev   # from repo root if needed
```

## Matrices

| Matrix | API key | Role |
| ------ | ------- | ---- |
| [smoke.yaml](matrices/smoke.yaml) | No | Quick grid smoke |
| [mcp-gate-mock.yaml](matrices/mcp-gate-mock.yaml) | No | MCP adapter smoke (`provider: mock`) — no `gate:` block |
| [mcp-gate.yaml](matrices/mcp-gate.yaml) | Yes | Live LLM + stdio MCP server |
| [ci-gate-mock.yaml](matrices/ci-gate-mock.yaml) | No | Full grid + `gate:` vs committed baseline (CI default) |
| [ci-gate-pr-mock.yaml](matrices/ci-gate-pr-mock.yaml) | No | PR sampling (`run.sample`) + like-for-like gate only |

Case ids default to `@case` function names (see stderr `qualify=` line).

## Smoke (no API key)

```bash
uv run gategrid validate --matrix matrices/smoke.yaml --root .
uv run gategrid run --matrix matrices/smoke.yaml --root .
```

From repo root:

```bash
uv run gategrid validate --matrix examples/gategrid/matrices/smoke.yaml
uv run gategrid run --matrix examples/gategrid/matrices/smoke.yaml
```

## MCP gate (mock — CI / offline)

Uses `PydanticAiMcpAdapter` with `provider: mock` (no subprocess MCP server). Benchmark-style matrix only — regression gating lives in `ci-gate-mock.yaml`.

```bash
uv sync --extra dev --extra pydantic-ai --extra mcp
uv run gategrid validate --matrix matrices/mcp-gate-mock.yaml --root .
uv run gategrid run --matrix matrices/mcp-gate-mock.yaml --root .
```

## MCP gate (live — LLM + stdio server)

You own side effects: the profile spawns `server/calc_server.py` as a subprocess. Gategrid does not start docker, databases, or production Telegram sessions.

```bash
uv sync --extra dev --extra pydantic-ai --extra mcp
export OPENAI_API_KEY=...
uv run gategrid validate --matrix matrices/mcp-gate.yaml --root .
uv run gategrid run --matrix matrices/mcp-gate.yaml --root .
```

Profile MCP config lives under **`data`** (see `profiles/mcp-candidate.yaml`):

- `data.mcp` — `transport: stdio`, `command`, `args` (paths relative to eval root)
- `data.env_pass_through` — env **names** only; values from the process environment

Optional remote transport: `transport: streamable_http` + `url` (see `gategrid.contrib.mcp.McpProfileConfig`).

## CI gate (mock, no API key)

Full grid for `main` / baseline refresh; same matrix on PR in [`.github/workflows/gategrid-ci.yml`](../../.github/workflows/gategrid-ci.yml).

```bash
uv run gategrid validate --matrix matrices/ci-gate-mock.yaml --root .
uv run gategrid run --matrix matrices/ci-gate-mock.yaml --root .
REPORT=$(ls -t "${GATEGRID_HOME:-.gategrid}"/reports/*_matrix.json | head -1)
uv run gategrid gate --matrix matrices/ci-gate-mock.yaml --root . \
  --report "$REPORT" \
  --baseline ci/baselines/demo.json
```

**PR sampling** ([ci-gate-pr-mock.yaml](matrices/ci-gate-pr-mock.yaml)): subset of cells; use **like-for-like** regression only (no `overall` regression bounds on a sample).

```bash
uv run gategrid validate --matrix matrices/ci-gate-pr-mock.yaml --root .
uv run gategrid run --matrix matrices/ci-gate-pr-mock.yaml --root .
```

**Regen committed baseline** (`ci/baselines/demo.json`):

```bash
uv run gategrid run --matrix matrices/ci-gate-mock.yaml --root .
REPORT=$(ls -t "${GATEGRID_HOME:-.gategrid}"/reports/*_matrix.json | head -1)
uv run gategrid baseline update --from-report "$REPORT" --profile demo \
  --matrix matrices/ci-gate-mock.yaml
cp "${GATEGRID_HOME:-.gategrid}"/baselines/demo.json ci/baselines/demo.json
```

CI recipes, sampling rules, and artifact layout: [docs/guides/ci.md](../../docs/guides/ci.md) · [ADR 0007](../../docs/adr/0007-gategrid-phase5-ci-productization.md).

## Gate vs benchmark

| | Gate | Benchmark |
| - | ---- | --------- |
| Profiles | One per matrix | Many |
| `gate:` / baseline | Yes — PR blocks on regression | No PR gate |
| Example here | `ci-gate-mock.yaml` | — |
| OpenCrabs | [hashline-gate.yaml](../opencrabs/matrices/hashline-gate.yaml) | [hashline-bench.yaml](../opencrabs/matrices/hashline-bench.yaml) |

OpenCrabs run commands: [examples/opencrabs/README.md](../opencrabs/README.md).

## Using another model

Matrices pin a `models:` list; presets live under `models/<id>.yaml`.

| Goal | Command / file |
| ---- | -------------- |
| Offline smoke | Use matrices with `mock` (default here) |
| Try your API once | Copy [`models/_template.yaml`](models/_template.yaml) → `models/my-model.yaml`, then `gategrid run --matrix … --root . --model my-model` |
| Persistent switch | Edit matrix `models:` or keep `--model` in scripts |
| Same preset, different endpoint | `{PREFIX}_MODEL` / `{PREFIX}_BASE_URL` from `api_key_env` — **not** for CI regression vs `main` baseline |

**Gate:** baselines are keyed by `model_id`. Do not `gate` a report from `--model` against a baseline built with the matrix default model. When the matrix uses `gate.regression.bounds.like_for_like`, gate requires [like-for-like representativeness](../../docs/guides/ci.md#like-for-like-representativeness) (default: all baseline cells must appear in the report).

```bash
uv run gategrid validate --matrix matrices/smoke.yaml --root . --model mock
uv run gategrid run --matrix matrices/mcp-gate.yaml --root . --model openai-mini
```

## Layout

- `matrices/` — matrix YAML (`profiles`, `models`, `cases` / `case_sets`, optional `gate`, `run.sample`)
- `ci/baselines/` — committed golden JSON for CI / forks
- `profiles/` — profile YAML (`runtime_adapter`; optional `data` for adapter-specific keys)
- `models/` — model presets
- `case_sets/` — named lists of **case ids**
- `cases/` — Python package with **`@case`** handlers (not legacy `EditCase` YAML)
- `evaluators/` — Python package with **`@evaluator`** (`gate` / `metric` tags)
- `adapters/` — example `RuntimeAdapter` implementations
- `server/` — minimal stdio MCP server for the MCP example

Set `GATEGRID_EVAL_ROOT` to this directory when invoking from the repo root.
