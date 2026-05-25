# Dogfood integrations

Gategrid spikes on external repos — tracked in [docs/roadmap/dogfood-notes.md](../../docs/roadmap/dogfood-notes.md).

## In this monorepo

| Spike | Location | Status |
| ----- | -------- | ------ |
| OpenCrabs hashline | [examples/opencrabs/](../opencrabs/) | Complete (Spike C) |
| MCP gate (mock) | [examples/gategrid/](../gategrid/) | Example |
| File-edit batteries | [examples/file_edit/](../file_edit/) | Example |

## External repos (planned)

1. [ai-antispam](https://github.com/leshchenko1979/ai-antispam) — Spike B
2. [fast-mcp-telegram](https://github.com/leshchenko1979/fast-mcp-telegram) — Spike A

Each target repo uses the same layout as [examples/opencrabs/](../opencrabs/): `evals/` at repo root with `matrices/`, `profiles/`, `models/`, `cases/`, `.gategrid/`.
