# OpenCrabs hashline example

Full **Gategrid** eval tree for the OpenCrabs file-editing hypothesis study: five profile variants × ten cases, OpenCrabs-style Python tools, and optional reference/fuzzy tooling.

**Report:** [docs/hashline_hypothesis_report.md](../../docs/hashline_hypothesis_report.md) · **Framework:** [README.md](../../README.md)

## Run

```bash
# From repo root
uv sync --extra dev --extra pydantic-ai

# Smoke (mock, no API key)
gategrid run --matrix examples/opencrabs/matrices/hashline-smoke.yaml --root examples/opencrabs

# Gate / bench (MiniMax — set MINIMAX_API_KEY)
gategrid run --matrix examples/opencrabs/matrices/hashline-gate.yaml --root examples/opencrabs
gategrid run --matrix examples/opencrabs/matrices/hashline-bench.yaml --root examples/opencrabs
```

Or set `GATEGRID_EVAL_ROOT=examples/opencrabs` and pass matrix paths relative to that root.

## Layout

| Path | Role |
| ---- | ---- |
| [matrices/](matrices/) | `hashline-smoke`, `hashline-gate`, `hashline-bench`, parity matrices |
| [profiles/](profiles/) | `opencrabs_original`, H1–H3 variants, `baseline` reference |
| [models/](models/) | `mock.yaml`, `minimax-m2.7.yaml` |
| [cases/](cases/) | `@case` registration + [cases/yaml/](cases/yaml/) task bodies |
| [tooling/opencrabs/](tooling/opencrabs/) | Ported OpenCrabs tools (one function per file) |
| [adapters/](adapters/) | `file_edit` runtime adapter |

**Tooling rules:** No `SYSTEM_PROMPT` / `TOOLS` bundles in `.py` files. Profile lists tool paths under `data.tools`.

## vs `examples/file_edit/`

[examples/file_edit/](../file_edit/) uses **builtin** hashline cases from `gategrid.contrib.file_edit.bundled`. This tree uses **custom** cases, OpenCrabs tooling, and hypothesis profiles for upstream comparison.
