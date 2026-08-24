"""Small dependency-free MCP stdio adapter for diagram-design."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


TYPES = [
    "architecture", "it-state", "flowchart", "sequence", "state-machine",
    "er-data-model", "timeline", "swimlane", "quadrant", "radar-spider",
    "polar-chart", "loop-flywheel", "nested", "tree", "org-chart",
    "layer-stack", "venn", "pyramid-funnel", "treemap", "bar", "line",
    "gantt", "scatter", "high-level", "process", "medallion", "data-flow",
    "dp-integration", "dp-security-matrix", "sankey", "fishbone", "wardley-map",
    "kanban", "user-journey", "deployment", "dependency-graph", "uml-class",
    "story-map", "database-schema",
]


def skill_root() -> Path:
    configured = os.environ.get("DIAGRAM_DESIGN_SKILL_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[3] / "skills" / "diagram-design"


def _text(path: Path, limit: int = 32_000) -> str:
    return path.read_text(encoding="utf-8")[:limit]


def _reference(root: Path, diagram_type: str | None) -> Path | None:
    if not diagram_type:
        return None
    slug = diagram_type.strip().lower().replace(" ", "-").replace("/", "-")
    if any(part in slug for part in ("..", "\\")):
        raise ValueError("diagram type contains invalid path characters")
    candidate = root / "references" / f"type-{slug}.md"
    return candidate if candidate.is_file() else None


def _run_extractor(root: Path, script: str, suffix: str, source: str) -> str:
    script_path = root / "scripts" / script
    if not script_path.is_file():
        raise FileNotFoundError(f"missing bundled extractor: {script_path}")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=suffix, delete=False) as handle:
        handle.write(source)
        input_path = Path(handle.name)
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), str(input_path), "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "extractor failed")
        return result.stdout
    finally:
        input_path.unlink(missing_ok=True)


def _validate_html(root: Path, html: str) -> dict[str, Any]:
    script = root / "scripts" / "self_check.py"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".html", delete=False) as handle:
        handle.write(html)
        input_path = Path(handle.name)
    try:
        result = subprocess.run(
            [sys.executable, str(script), str(input_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        )
        return {"valid": result.returncode == 0, "exit_code": result.returncode, "output": (result.stdout + result.stderr).strip()}
    finally:
        input_path.unlink(missing_ok=True)


def _content(text: str, structured: dict[str, Any] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"content": [{"type": "text", "text": text}]}
    if structured is not None:
        result["structuredContent"] = structured
    return result


def _tools() -> list[dict[str, Any]]:
    return [
        {"name": "diagram_design_types", "description": "List supported diagram types.", "inputSchema": {"type": "object", "properties": {}}},
        {"name": "diagram_design_guidance", "description": "Return core diagram-design guidance and an optional type reference.", "inputSchema": {"type": "object", "properties": {"diagram_type": {"type": "string"}}, "additionalProperties": False}},
        {"name": "diagram_design_extract_mermaid", "description": "Extract Mermaid source into structured diagram IR.", "inputSchema": {"type": "object", "required": ["source"], "properties": {"source": {"type": "string"}}, "additionalProperties": False}},
        {"name": "diagram_design_extract_drawio", "description": "Extract draw.io/XML source into structured diagram IR.", "inputSchema": {"type": "object", "required": ["source"], "properties": {"source": {"type": "string"}}, "additionalProperties": False}},
        {"name": "diagram_design_validate_html", "description": "Validate generated diagram HTML with bundled checks.", "inputSchema": {"type": "object", "required": ["html"], "properties": {"html": {"type": "string"}}, "additionalProperties": False}},
    ]


def _call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    root = skill_root()
    if name == "diagram_design_types":
        return _content(json.dumps({"types": TYPES}, indent=2), {"types": TYPES})
    if name == "diagram_design_guidance":
        diagram_type = arguments.get("diagram_type")
        reference = _reference(root, diagram_type)
        text = "# Core guidance\n\n" + _text(root / "SKILL.md")
        if diagram_type:
            text += f"\n\n# Requested type: {diagram_type}\n\n"
            text += _text(reference) if reference else "No exact type reference found; use nearest existing type."
        return _content(text)
    if name == "diagram_design_extract_mermaid":
        return _content(_run_extractor(root, "mermaid_extract.py", ".mmd", str(arguments["source"])))
    if name == "diagram_design_extract_drawio":
        return _content(_run_extractor(root, "drawio_extract.py", ".drawio", str(arguments["source"])))
    if name == "diagram_design_validate_html":
        result = _validate_html(root, str(arguments["html"]))
        return _content(json.dumps(result, indent=2), result)
    raise ValueError(f"unknown tool: {name}")


def _dispatch(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")
    if method in {"notifications/initialized", "notifications/cancelled"}:
        return None
    if method == "initialize":
        params = request.get("params") or {}
        return {"jsonrpc": "2.0", "id": request_id, "result": {"protocolVersion": params.get("protocolVersion", "2025-03-26"), "capabilities": {"tools": {}}, "serverInfo": {"name": "diagram-design-mcp", "version": "0.1.0"}}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": _tools()}}
    if method == "tools/call":
        try:
            params = request.get("params") or {}
            return {"jsonrpc": "2.0", "id": request_id, "result": _call(params["name"], params.get("arguments") or {})}
        except Exception as error:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": str(error)}}
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"method not found: {method}"}}


def main() -> int:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            response = _dispatch(json.loads(line))
            if response is not None:
                sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError as error:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(error)}}) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
