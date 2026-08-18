# registry-agents

Portable, tregistry-compatible catalog payloads for core agent-pack assets.

Contents:

- `agents/`: SWE, spec, security, QA, orchestration agent bodies.
- `skills/`: startup, debugging, testing, review, verification, and commit skills.
- `mcp/`: security-scanner and drawio MCP source metadata.
- `plugins/`: agent-pack plugin metadata and registry snapshot.
- `manifests/core.yaml`: generated multi-document upload payload.

## Upload

From this directory:

```powershell
python scripts/build_manifests.py
uv run tregistry apply -f manifests/core.yaml --dry-run
uv run tregistry apply -f manifests/core.yaml
uv run tregistry get agents
uv run tregistry get skills
uv run tregistry get mcp-servers
uv run tregistry get plugins
```

Open tregistry frontend after apply. Catalog rows should show 5 agents, 6 skills, 2 MCP servers, and 1 plugin in `default/latest`.

## Rebuild check

`manifests/core.yaml` is generated. Update payload files first, then run:

```powershell
python scripts/build_manifests.py
python scripts/build_manifests.py --check
```

## Compatibility boundary

Agents and skills store complete Markdown bodies, so Claude global install can write them directly. Codex host bridge currently supports MCP only. `security-scanner` is catalog-only until an SSE server listens on `http://localhost:8765/sse`; `drawio-mcp` is installable through its PyPI package metadata.

Source trees remain untouched. Rollback: delete applied `latest` artifacts with `tregistry delete`, or apply prior manifest version.
