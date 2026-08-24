"""Small Python adapter that routes common commands through RTK."""

from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
from collections.abc import Sequence


SUPPORTED_HOSTS = ("copilot", "claude", "codex")
RTK_COMMAND = "context-saver-rtk"
_UPSTREAM_COMMAND = "rtk"

_INIT_FLAGS = {
    "copilot": ("-g", "--copilot"),
    "claude": ("-g",),
    "codex": ("-g", "--codex"),
}

# Keep mapping conservative. Unknown commands pass through unchanged.
_RTK_COMMANDS = {
    "git": "git",
    "rg": "grep",
    "grep": "grep",
    "find": "find",
    "cat": "read",
    "ls": "ls",
    "pytest": "pytest",
    "ruff": "ruff",
}


def init_command(host: str) -> list[str]:
    """Return RTK's global setup command for one supported host."""
    try:
        flags = _INIT_FLAGS[host]
    except KeyError as error:
        raise ValueError(f"unsupported host: {host}") from error
    return [RTK_COMMAND, "init", *flags]


def rewrite_command(command: Sequence[str]) -> list[str]:
    """Rewrite a safe, known command to its RTK equivalent."""
    argv = list(command)
    if not argv:
        raise ValueError("command cannot be empty")

    executable = argv[0].lower()
    rtk_command = _RTK_COMMANDS.get(executable)
    if rtk_command is None:
        return argv

    # Flags can change command semantics. Preserve native execution until
    # caller explicitly chooses a known RTK form.
    if executable in {"rg", "grep", "find", "ls"} and any(arg.startswith("-") for arg in argv[1:]):
        return argv
    if executable == "cat" and len(argv) != 2:
        return argv

    return [RTK_COMMAND, rtk_command, *argv[1:]]


def _rtk_path() -> str | None:
    return shutil.which(RTK_COMMAND) or shutil.which(_UPSTREAM_COMMAND)


def _display(argv: Sequence[str]) -> str:
    return shlex.join(list(argv))


def _run(argv: Sequence[str]) -> int:
    return subprocess.run(list(argv), check=False).returncode


def _check() -> int:
    rtk = _rtk_path()
    if rtk is None:
        print("rtk not found on PATH", file=sys.stderr)
        return 1
    result = subprocess.run([rtk, "--version"], check=False)
    return result.returncode


def _init(host: str, dry_run: bool) -> int:
    command = init_command(host)
    if dry_run:
        print(_display(command))
        return 0
    if _rtk_path() is None:
        print("rtk not found on PATH", file=sys.stderr)
        return 1
    return _run(command)


def _run_command(command: Sequence[str], dry_run: bool) -> int:
    argv = list(command)
    if argv and argv[0] == "--":
        argv = argv[1:]
    if not argv:
        print("run requires command", file=sys.stderr)
        return 2

    rewritten = rewrite_command(argv)
    if dry_run:
        print(_display(rewritten))
        return 0

    if rewritten[:1] == [RTK_COMMAND] and _rtk_path() is None:
        print("rtk unavailable; running native command", file=sys.stderr)
        rewritten = argv
    return _run(rewritten)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Route supported shell commands through RTK.")
    subparsers = parser.add_subparsers(dest="action", required=True)

    subparsers.add_parser("check", help="check that RTK is installed")

    init_parser = subparsers.add_parser("init", help="configure RTK for one supported host")
    init_parser.add_argument("--host", choices=SUPPORTED_HOSTS, required=True)
    init_parser.add_argument("--dry-run", action="store_true")

    run_parser = subparsers.add_parser("run", help="run one command through RTK when safely mapped")
    run_parser.add_argument("--dry-run", action="store_true")
    run_parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.action == "check":
        return _check()
    if args.action == "init":
        return _init(args.host, args.dry_run)
    return _run_command(args.command, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
