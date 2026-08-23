# registry-agents

Portable, tregistry-compatible catalog payloads for core agent-pack assets.

Contents:

- `agents/`: SWE, spec, security, QA, orchestration, and diagram-design agent bodies.
- `skills/`: startup, debugging, testing, review, verification, commit, book-to-skill, context-saver, and diagram-design skills.
- `mcp/`: security-scanner, GitHub, Figma, local Draw.io-compatible, and diagram-design MCP metadata/providers.
- `plugins/`: agent-pack plugin metadata and registry snapshot.
- `manifests/core.yaml`: generated multi-document upload payload.

## Upload

From this directory:

```powershell
python scripts/build_manifests.py --split
python scripts/build_manifests.py --check

# Apply one resource at a time.
tregistry apply -f manifests/resources/agents/swe.yaml
tregistry apply -f manifests/resources/skills/test.yaml
tregistry apply -f manifests/resources/mcp-servers/github-mcp.yaml
tregistry apply -f manifests/resources/mcp-servers/figma-mcp.yaml

# Or apply complete catalog payload.
tregistry apply -f manifests/core.yaml --dry-run
tregistry apply -f manifests/core.yaml
uv run tregistry get agents
uv run tregistry get skills
uv run tregistry get mcp-servers
uv run tregistry get plugins
```

Open tregistry frontend after apply. Catalog rows should show 6 agents, 9 skills, 5 MCP servers, and 1 plugin in `default/latest`.

`manifests/resources/` contains one independently applicable YAML file per
agent, skill, MCP server, and plugin. This keeps installation, rollback, and
verification separate by resource.

## Rebuild check

`manifests/core.yaml` is generated. Update payload files first, then run:

```powershell
python scripts/build_manifests.py
python scripts/build_manifests.py --check
```

## Compatibility boundary

Agents and skills store complete Markdown bodies, so Claude global install can write them directly. Codex host bridge currently supports MCP only. `security-scanner` is catalog-only until an SSE server listens on `http://localhost:8765/sse`; `drawio-mcp` and `diagram-design-mcp` use package metadata for independent registry installation. The diagram adapter source and tests remain under `mcp/diagram-design-python/`.

Source trees remain untouched. Rollback: delete applied `latest` artifacts with `tregistry delete`, or apply prior manifest version.
