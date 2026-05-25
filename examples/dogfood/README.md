# Dogfood integrations

Gategrid spikes on external repos — tracked in [docs/roadmap/research/dogfood-notes.md](../../docs/roadmap/research/dogfood-notes.md).

## In this monorepo

| Spike | Location | Notes |
| ----- | -------- | ----- |
| OpenCrabs hashline | [examples/opencrabs/](../opencrabs/) | `hashline-smoke` / `hashline-gate` / `hashline-bench` (Spike C) — see [README](../opencrabs/README.md) |
| Gategrid smoke / MCP / CI | [examples/gategrid/](../gategrid/) | `smoke`, `mcp-gate-mock`, `ci-gate-mock`, `ci-gate-pr-mock` |
| File-edit batteries | [examples/file_edit/](../file_edit/) | Minimal `contrib/file_edit` path |

**CI productization:** [docs/guides/ci.md](../../docs/guides/ci.md) — PR `gate`, `main` baseline refresh, `run.sample`. This repo runs [`.github/workflows/gategrid-ci.yml`](../../.github/workflows/gategrid-ci.yml) against [examples/gategrid/ci/baselines/demo.json](../gategrid/ci/baselines/demo.json).

## External repos (planned)

1. [ai-antispam](https://github.com/leshchenko1979/ai-antispam) — Spike B
2. [fast-mcp-telegram](https://github.com/leshchenko1979/fast-mcp-telegram) — Spike A

Each target repo uses an `evals/` tree at repo root: `matrices/`, `profiles/`, `models/`, `.gategrid/`. Optional `cases/` for custom `@case` handlers; file-edit spikes can use **builtin** batteries (see [examples/opencrabs/](../opencrabs/) and [examples/file_edit/](../file_edit/)).
