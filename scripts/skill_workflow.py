"""Validate and independently install every skill manifest."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_DIR = ROOT / "manifests" / "resources" / "skills"
_NAME_RE = re.compile(r"^  name: ([A-Za-z0-9._-]+)$", re.MULTILINE)


@dataclass(frozen=True)
class SkillManifest:
    name: str
    path: Path
    text: str


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...]
    body: str


def discover_skills(manifest_dir: Path = DEFAULT_MANIFEST_DIR) -> list[SkillManifest]:
    """Discover skill manifests from disk; never maintain a second skill list."""
    paths = sorted(manifest_dir.glob("*.yaml"))
    if not paths:
        raise FileNotFoundError(f"no skill manifests found in {manifest_dir}")

    manifests: list[SkillManifest] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        match = _NAME_RE.search(text)
        manifests.append(SkillManifest(match.group(1) if match else path.stem, path, text))
    return manifests


def select_skills(skills: list[SkillManifest], names: list[str] | None) -> list[SkillManifest]:
    """Select requested skills while preserving requested order."""
    if not names:
        return skills
    by_name = {skill.name: skill for skill in skills}
    missing = [name for name in names if name not in by_name]
    if missing:
        raise ValueError("unknown skill(s): " + ", ".join(missing))
    return [by_name[name] for name in names]


def _extract_body(text: str) -> str:
    marker = "  body: |"
    if marker not in text:
        return ""
    lines = text.splitlines()
    start = lines.index(marker) + 1
    body_lines = [line[4:] if line.startswith("    ") else line for line in lines[start:]]
    return "\n".join(body_lines).rstrip() + "\n"


def validate_skill(skill: SkillManifest) -> ValidationResult:
    """Confirm registry manifest contains a complete standalone SKILL.md body."""
    text = skill.text or skill.path.read_text(encoding="utf-8")
    errors: list[str] = []

    if text.count("apiVersion: registry.agentify/v1alpha1") != 1:
        errors.append("must contain exactly one registry apiVersion")
    if not re.search(r"^kind: Skill$", text, re.MULTILINE):
        errors.append("kind must be Skill")
    name_match = _NAME_RE.search(text)
    if not name_match:
        errors.append("metadata.name is missing")
    elif name_match.group(1) != skill.name:
        errors.append(f"metadata.name {name_match.group(1)!r} differs from {skill.name!r}")
    if skill.path.stem != skill.name:
        errors.append("filename must match metadata.name")

    body = _extract_body(text)
    if not body.strip():
        errors.append("spec.body is empty")
    elif not body.startswith("---\n"):
        errors.append("body must start with SKILL.md frontmatter")
    elif "\n---\n" not in body:
        errors.append("SKILL.md frontmatter is unterminated")

    return ValidationResult(not errors, tuple(errors), body)


def commands_for(
    skill: SkillManifest,
    *,
    target: str = "claude",
    scope: str = "global",
    tregistry_command: str = "tregistry",
    dry_run: bool = False,
) -> list[list[str]]:
    """Return independent apply/install commands for one skill."""
    apply = [tregistry_command, "apply", "-f", str(skill.path)]
    if dry_run:
        apply.append("--dry-run")
    install = [
        tregistry_command,
        "install",
        "skill",
        skill.name,
        "--target",
        target,
        "--scope",
        scope,
    ]
    return [apply, install]


def _run(command: list[str]) -> int:
    print("$ " + " ".join(command))
    return subprocess.run(command, check=False).returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest-dir", type=Path, default=DEFAULT_MANIFEST_DIR)
    parser.add_argument("--skill", action="append", dest="skill_names", help="select one skill; repeatable")
    parser.add_argument("--target", choices=("claude",), default="claude")
    parser.add_argument("--scope", choices=("global", "project"), default="global")
    parser.add_argument("--apply", action="store_true", help="apply each skill manifest to tregistry")
    parser.add_argument("--install", action="store_true", help="apply and install each skill independently")
    parser.add_argument("--dry-run", action="store_true", help="validate each apply without writing")
    parser.add_argument("--print-commands", action="store_true", help="print commands without running them")
    parser.add_argument(
        "--tregistry-command",
        default=os.environ.get("TREGISTRY_COMMAND", "tregistry"),
        help="tregistry executable (default: tregistry)",
    )
    args = parser.parse_args(argv)

    if args.dry_run and args.install:
        parser.error("--dry-run cannot be combined with --install")
    if args.dry_run:
        args.apply = True

    try:
        skills = select_skills(discover_skills(args.manifest_dir), args.skill_names)
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))
    failures = 0
    for skill in skills:
        result = validate_skill(skill)
        if not result.ok:
            print(f"FAIL {skill.name}: " + "; ".join(result.errors))
            failures += 1
            continue
        print(f"OK   {skill.name}: standalone SKILL.md body")

        if not (args.apply or args.install or args.print_commands):
            continue
        commands = commands_for(
            skill,
            target=args.target,
            scope=args.scope,
            tregistry_command=args.tregistry_command,
            dry_run=args.dry_run,
        )
        if args.print_commands:
            for command in commands[: 2 if args.install else 1]:
                print("  " + " ".join(command))
        if args.print_commands:
            continue
        commands_to_run = commands[: 2 if args.install else 1]
        for command in commands_to_run:
            if _run(command) != 0:
                failures += 1
                print(f"FAIL {skill.name}: command returned non-zero")
                break

    print(f"Checked {len(skills)} skills; failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
