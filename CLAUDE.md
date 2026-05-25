# Gategrid

**Product:** [Gategrid](docs/roadmap/product/README-pitch-draft.md) — matrix eval runner with git-native CI gates.

**User-facing pitch:** [README.md](README.md). Roadmap: [docs/roadmap/engineering/v1-implementation-checklist.md](docs/roadmap/engineering/v1-implementation-checklist.md).

## Setup

```bash
uv sync --extra dev
gategrid --version
gategrid validate --matrix examples/gategrid/matrices/smoke.yaml
gategrid run --matrix examples/gategrid/matrices/smoke.yaml
pytest tests/test_gategrid_phase0.py tests/test_gategrid_phase1.py \
 tests/test_gategrid_phase2.py tests/test_gategrid_phase3.py \
 tests/test_gategrid_phase4.py tests/test_gategrid_cli_output.py \
 tests/test_gategrid_phase5.py tests/test_gategrid_spike_c.py
```

For hashline / LLM dogfood and full exit tests: `uv sync --extra dev --extra pydantic-ai`.

`run` / `validate` accept `--model <id>` to override matrix `models:` (presets under `eval_root/models/`). See [examples/gategrid/README.md](examples/gategrid/README.md#using-another-model).

Artifacts live under `.gategrid/` (`GATEGRID_HOME` overrides). ADRs: [docs/adr/](docs/adr/). **Coding principles:** [CODE.md](CODE.md) — reread before implementation (after plan approval); update after post-impl review ([implementation workflow](.cursor/rules/gategrid-phase-workflow.mdc)).

## OpenCrabs example (`examples/opencrabs/`)

Hashline hypothesis matrices (Spike C). Not part of `pip install gategrid`; use `--root examples/opencrabs` or `GATEGRID_EVAL_ROOT=examples/opencrabs`.

```bash
gategrid validate --matrix examples/opencrabs/matrices/hashline-smoke.yaml --root examples/opencrabs
gategrid run --matrix examples/opencrabs/matrices/hashline-smoke.yaml --root examples/opencrabs
pytest tests/test_gategrid_spike_c.py tests/test_gategrid_file_edit_batteries.py
```

| Path | Role |
| ---- | ---- |
| `examples/opencrabs/matrices/` | `hashline-smoke`, `hashline-gate` (CI gate), `hashline-bench` (research) — [README](examples/opencrabs/README.md) |
| `examples/opencrabs/profiles/` | `runtime_adapter` + `data.system_prompt` / `data.tools` |
| `examples/opencrabs/models/` | Model presets (`mock`, `minimax-m2.7`, `openai-mini`); bench with `--model <id>` |
| Builtin cases | `gategrid.contrib.file_edit.bundled` (same ids as [examples/file_edit/](examples/file_edit/)) |
| `examples/opencrabs/tooling/opencrabs/` | OpenCrabs-style tools (one tool per file) |
| `examples/opencrabs/adapters/` | `file_edit` runtime adapter |

**Tooling rules:** No `SYSTEM_PROMPT`, `TOOLS`, or `register(agent)` bundles in `.py` files. Paths in cases are workspace-relative.

## Examples

| Path | Role |
| ---- | ---- |
| `examples/gategrid/` | Minimal Gategrid smoke (mock) + MCP gate example (`mcp-gate`, `mcp-gate-mock`) |
| `examples/file_edit/` | File-edit contrib sample |
| `examples/opencrabs/` | OpenCrabs hashline benchmark (full tooling port) |

## Hashline hypothesis matrix

5 profile variants × 10 cases (4 small + 6 large). Pass/fail = file content match via `contrib/file_edit`.

```bash
gategrid run --matrix examples/opencrabs/matrices/hashline-bench.yaml --root examples/opencrabs
```

**Bench analysis:** [docs/guides/bench-analysis.md](docs/guides/bench-analysis.md) (how to read bench JSON vs CI gates).

**Report:** [docs/reports/hashline/hashline_hypothesis_report.md](docs/reports/hashline/hashline_hypothesis_report.md). Regenerate figures: `uv sync --extra report` then `uv run python docs/reports/hashline/_build_report_viz.py` (set `GATEGRID_REPORT_JSON` to a `.gategrid/reports/*.json` from a bench run).

**DX vs competitors (OpenCrabs):** [docs/roadmap/research/spike-dx-competitive-analysis.md](docs/roadmap/research/spike-dx-competitive-analysis.md) — required for all spikes; minimal path is [examples/file_edit/](examples/file_edit/), not full opencrabs tree.

## Observability

- Default: stdout + `.gategrid/reports/`
- Logfire: `LOGFIRE_TOKEN`, `send_to_logfire='if-token-present'` on pydantic-ai runs
