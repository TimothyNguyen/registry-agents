---
name: diagram-design-mcp
version: 0.1.0
description: |
  Local MCP provider for diagram-design. Exposes diagram type discovery,
  reference guidance, Mermaid and draw.io extraction, and generated HTML
  validation over stdio. Supports GitHub Copilot CLI, Claude Code, and Codex.
agents: [diagram-design, swe, qa-agent]
mcp: diagram-design-mcp
trigger: diagram mcp|diagram tool|mermaid extract|drawio extract|diagram validate
---

# Diagram Design MCP

Install editable from `mcp/diagram-design-python/`, then launch
`diagram-design-mcp`. Configure host MCP settings for stdio transport.

The provider delegates parsing and validation to bundled scripts under
`skills/diagram-design/scripts/`. Set `DIAGRAM_DESIGN_SKILL_DIR` if registry
deployment places skill outside this checkout.
