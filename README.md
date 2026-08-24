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
py scripts/build_manifests.py --split
py scripts/build_manifests.py --check

# Apply one resource at a time.
tregistry apply -f manifests/resources/agents/swe.yaml
tregistry apply -f manifests/resources/skills/test.yaml
tregistry apply -f manifests/resources/mcp-servers/github-mcp.yaml
tregistry apply -f manifests/resources/mcp-servers/figma-mcp.yaml

# Or apply complete catalog payload.
tregistry apply -f manifests/core.yaml --dry-run
tregistry apply -f manifests/core.yaml
tregistry get agents
tregistry get skills
tregistry get mcp-servers
tregistry get plugins
```

Open tregistry frontend after apply. Catalog rows should show 6 agents, 9 skills, 5 MCP servers, and 1 plugin in `default/latest`.

`manifests/resources/` contains one independently applicable YAML file per
agent, skill, MCP server, and plugin. This keeps installation, rollback, and
verification separate by resource.

## Install skills independently

`scripts/skill_workflow.py` discovers every file in
`manifests/resources/skills/`; it does not maintain a second hardcoded skill
list. It validates each manifest's `SKILL.md` body, then can apply and install
each skill as its own tregistry operation.

```powershell
# Validate every discovered skill without registry writes.
py scripts/skill_workflow.py

# Validate every registry apply without writing catalog state.
py scripts/skill_workflow.py --dry-run

# Print exact commands for one skill.
py scripts/skill_workflow.py --install --print-commands --skill test --target claude --scope global

# Apply and install one skill independently.
py scripts/skill_workflow.py --install --skill test --target claude --scope global

# Apply and install every discovered skill independently.
py scripts/skill_workflow.py --install --target claude --scope global
```

Use `--skill <name>` repeatedly to select several skills. Replace `test` with
any filename stem under `manifests/resources/skills/`. Current tregistry skill
installation targets Claude; Codex currently supports MCP installation, not a
skills directory. To use another tregistry executable, set
`TREGISTRY_COMMAND` or pass `--tregistry-command`.

## Rebuild check

`manifests/core.yaml` is generated. Update payload files first, then run:

```powershell
py scripts/build_manifests.py
py scripts/build_manifests.py --check
```

## Compatibility boundary

Agents and skills store complete Markdown bodies, so Claude global install can write them directly. Codex host bridge currently supports MCP only. `security-scanner` is catalog-only until an SSE server listens on `http://localhost:8765/sse`; `drawio-mcp` and `diagram-design-mcp` use package metadata for independent registry installation. The diagram adapter source and tests remain under `mcp/diagram-design-python/`.

Source trees remain untouched. Rollback: delete applied `latest` artifacts with `tregistry delete`, or apply prior manifest version.
