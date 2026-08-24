"""Dependency-free context compaction."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


COMPACT_MODES = ("lite", "full", "ultra")
_FILLER_WORDS = re.compile(r"\b(?:a|an|the|just|really|basically|simply|actually)\b", re.IGNORECASE)
_AUXILIARY_VERBS = re.compile(r"\b(?:is|are|was|were|being)\b", re.IGNORECASE)
_PROTECTED = re.compile(
    r"`[^`\n]+`|https?://\S+|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'"
)
_EXACT_LINE = re.compile(r"^(?:Error|Traceback|FAIL(?:URE)?|WARNING):", re.IGNORECASE)


def _compact_line(line: str, mode: str) -> str:
    newline = "\n" if line.endswith("\n") else ""
    body = line[:-1] if newline else line
    stripped = body.strip()
    if not stripped or stripped.startswith(("$ ", "PS> ", ">>> ")) or _EXACT_LINE.match(stripped):
        return line

    protected: list[str] = []

    def save(match: re.Match[str]) -> str:
        protected.append(match.group(0))
        return f"\x00{len(protected) - 1}\x00"

    body = _PROTECTED.sub(save, body)
    body = re.sub(r"\s+", " ", body).strip()
    if mode != "lite":
        body = re.sub(r"\bin order to\b", "to", body, flags=re.IGNORECASE)
        body = _FILLER_WORDS.sub("", body)
        body = _AUXILIARY_VERBS.sub("", body)
    if mode == "ultra":
        body = re.sub(r"\bleads to\b", "→", body, flags=re.IGNORECASE)
        body = re.sub(r"\band\b", "&", body, flags=re.IGNORECASE)
    body = re.sub(r"\s+([,.!?;:])", r"\1", body)
    body = re.sub(r" {2,}", " ", body).strip()
    for index, value in enumerate(protected):
        body = body.replace(f"\x00{index}\x00", value)
    return body + newline


def compact_text(text: str, mode: str = "full") -> str:
    """Compact prose while preserving fenced code and exact-value lines."""
    if mode not in COMPACT_MODES:
        raise ValueError(f"unsupported compact mode: {mode}")

    output: list[str] = []
    in_fence = False
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            output.append(line)
        elif in_fence:
            output.append(line)
        else:
            output.append(_compact_line(line, mode))
    return "".join(output)


def _compact(path: str | None, mode: str) -> int:
    source = Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()
    output = compact_text(source, mode=mode)
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8")
    sys.stdout.write(output)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compact prose without external dependencies.")
    compact_parser = parser.add_subparsers(dest="action", required=True).add_parser(
        "compact", help="compact prose while preserving protected content"
    )
    compact_parser.add_argument("--mode", choices=COMPACT_MODES, default="full")
    compact_parser.add_argument("path", nargs="?")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    return _compact(args.path, args.mode)


if __name__ == "__main__":
    raise SystemExit(main())
