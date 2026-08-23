# Diagram Design MCP

Local stdio MCP adapter for `skills/diagram-design/`. No third-party runtime
dependency. Exposes diagram type discovery, reference guidance, Mermaid and
draw.io extraction, and generated-HTML validation.

## Run

```powershell
python -m diagram_design_mcp.server
```

Set `DIAGRAM_DESIGN_SKILL_DIR` when skill files are outside this repository.

## Tools

- `diagram_design_types` — list supported visual types.
- `diagram_design_guidance` — return core guidance and one matching reference.
- `diagram_design_extract_mermaid` — parse Mermaid source into diagram IR.
- `diagram_design_extract_drawio` — parse draw.io/XML source into diagram IR.
- `diagram_design_validate_html` — run bundled accessibility and safety checks.

Transport: MCP JSON-RPC over stdin/stdout. Diagnostics go to stderr.
