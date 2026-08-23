"""Build tregistry-compatible YAML from checked-in registry payloads."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "manifests"
OUTPUT = MANIFEST_DIR / "core.yaml"
RESOURCE_DIR = MANIFEST_DIR / "resources"

AGENTS = ("swe", "spec-agent", "security", "qa-agent", "orchestrate", "diagram-design")
SKILLS = (
    "using-agent-skills",
    "systematic-debugging",
    "test",
    "review",
    "verification-before-completion",
    "commit",
    "book-to-skill",
    "context-saver",
    "diagram-design",
)


def _frontmatter(body: str) -> dict[str, str]:
    """Read small subset of SKILL.md frontmatter needed by registry specs."""
    lines = body.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    try:
        end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return {}

    values: dict[str, str] = {}
    index = 1
    while index < end:
        line = lines[index]
        match = re.match(r"^([A-Za-z0-9_-]+):(?:\s+(.*))?$", line)
        if not match:
            index += 1
            continue
        key, value = match.group(1), (match.group(2) or "").strip()
        if value == "|":
            parts: list[str] = []
            index += 1
            while index < end and (lines[index].startswith("  ") or not lines[index]):
                parts.append(lines[index][2:] if lines[index].startswith("  ") else "")
                index += 1
            values[key] = "\n".join(parts).strip()
            continue
        values[key] = value.strip('"\'')
        index += 1
    return values


def _quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _body_field(body: str) -> list[str]:
    lines = ["  body: |"]
    lines.extend(f"    {line}" if line else "" for line in body.rstrip("\n").splitlines())
    return lines


def _document(kind: str, name: str, title: str, description: str, spec_lines: list[str]) -> list[str]:
    lines = [
        "apiVersion: registry.agentify/v1alpha1",
        f"kind: {kind}",
        "metadata:",
        f"  name: {name}",
        "  namespace: default",
        "  tag: latest",
        "spec:",
        f"  title: {_quoted(title)}",
        f"  description: {_quoted(description)}",
    ]
    lines.extend(spec_lines)
    return lines


def _agent_or_skill(kind: str, name: str, source: Path) -> list[str]:
    body = source.read_text(encoding="utf-8")
    meta = _frontmatter(body)
    description = meta.get("description", f"{name} {kind.lower()} from tstack agent-pack.")
    title = meta.get("name", name)
    return _document(
        kind,
        name,
        title,
        description.splitlines()[0],
        _body_field(body),
    )


def build() -> str:
    documents: list[list[str]] = []

    for name in AGENTS:
        documents.append(_agent_or_skill("Agent", name, ROOT / "agents" / f"{name}.md"))

    for name in SKILLS:
        documents.append(_agent_or_skill("Skill", name, ROOT / "skills" / name / "SKILL.md"))

    documents.append(
        _document(
            "MCPServer",
            "security-scanner",
            "security-scanner",
            "Checkov, Semgrep, Bandit, and ASH security scanning MCP server.",
            [
                "  remote:",
                "    type: sse",
                "    url: http://localhost:8765/sse",
            ],
        )
    )
    documents.append(
        _document(
            "MCPServer",
            "github-mcp",
            "github-mcp",
            "GitHub MCP server for repository, issue, pull request, Actions, and security workflows.",
            [
                "  remote:",
                "    type: http",
                "    url: https://api.githubcopilot.com/mcp/",
            ],
        )
    )
    documents.append(
        _document(
            "MCPServer",
            "figma-mcp",
            "figma-mcp",
            "Figma MCP server for design context, code generation, and design-system workflows.",
            [
                "  remote:",
                "    type: http",
                "    url: https://mcp.figma.com/mcp",
            ],
        )
    )
    documents.append(
        _document(
            "MCPServer",
            "drawio-mcp",
            "drawio-mcp",
            "Local Draw.io-compatible MCP server for opening XML, CSV, and Mermaid diagrams.",
            [
                "  source:",
                "    package:",
                "      origin:",
                "        type: pypi",
                "        identifier: drawio-mcp",
                "        pypi:",
                "          version: \"2.0.0\"",
                "          server_name: drawio-mcp",
                "      launch:",
                "        command: drawio-mcp",
                "      transport:",
                "        type: stdio",
            ],
        )
    )
    documents.append(
        _document(
            "MCPServer",
            "diagram-design-mcp",
            "diagram-design-mcp",
            "Local stdio MCP adapter for diagram-design type guidance, source extraction, and HTML validation.",
            [
                "  source:",
                "    package:",
                "      origin:",
                "        type: pypi",
                "        identifier: diagram-design-mcp",
                "        pypi:",
                "          version: \"0.1.0\"",
                "          server_name: diagram-design-mcp",
            ],
        )
    )

    documents.append(
        _document(
            "Plugin",
            "agent-pack",
            "agent-pack",
            "Enterprise-safe agent skills, agents, workflows, adapters, and tool providers.",
            [
                "  harnesses:",
                "    - claude",
                "    - codex",
                "    - copilot",
                "  source:",
                "    type: git",
                "    git:",
                "      repository:",
                "        url: https://github.com/TimothyNguyen/tstack",
                "        branch: main",
                "        subfolder: agent-pack",
            ],
        )
    )

    return "\n---\n".join("\n".join(document) for document in documents) + "\n"


def _split_documents(rendered: str) -> dict[Path, str]:
    """Map each generated registry document to an independently applicable file."""
    result: dict[Path, str] = {}
    for document in rendered.rstrip("\n").split("\n---\n"):
        kind_match = re.search(r"^kind: ([A-Za-z]+)$", document, re.MULTILINE)
        name_match = re.search(r"^  name: ([A-Za-z0-9._-]+)$", document, re.MULTILINE)
        if not kind_match or not name_match:
            raise ValueError("generated document missing kind or metadata.name")
        kind = kind_match.group(1)
        plural = {
            "Agent": "agents",
            "Skill": "skills",
            "MCPServer": "mcp-servers",
            "Plugin": "plugins",
        }.get(kind)
        if plural is None:
            raise ValueError(f"unsupported generated kind: {kind}")
        result[RESOURCE_DIR / plural / f"{name_match.group(1)}.yaml"] = document + "\n"
    return result


def _write_split_documents(rendered: str, *, check: bool) -> int:
    expected = _split_documents(rendered)
    existing = set(RESOURCE_DIR.glob("**/*.yaml")) if RESOURCE_DIR.exists() else set()
    stale = existing - set(expected)
    if check:
        for path, content in expected.items():
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                print(f"stale: {path}")
                return 1
        if stale:
            print(f"stale: {sorted(stale)[0]}")
            return 1
        print(f"ok: {RESOURCE_DIR} ({len(expected)} resources)")
        return 0

    for path, content in expected.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    for path in stale:
        path.unlink()
    print(f"wrote: {RESOURCE_DIR} ({len(expected)} resources)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when generated output is stale")
    parser.add_argument(
        "--split",
        action="store_true",
        help="also write one independently applicable YAML manifest per resource",
    )
    args = parser.parse_args()
    rendered = build()
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != rendered:
            print(f"stale: {OUTPUT}")
            return 1
        print(f"ok: {OUTPUT}")
        return _write_split_documents(rendered, check=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(rendered, encoding="utf-8", newline="\n")
    resource_count = rendered.count("\n---\n") + 1
    print(f"wrote: {OUTPUT} ({resource_count} resources)")
    if args.split:
        return _write_split_documents(rendered, check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
