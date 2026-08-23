from io import StringIO
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import context_saver
from context_saver import compact_text
import rtk_adapter
from rtk_adapter import init_command, rewrite_command


class ContextSaverTests(unittest.TestCase):
    def test_supported_host_setup(self):
        self.assertEqual(rtk_adapter.SUPPORTED_HOSTS, ("copilot", "claude", "codex"))
        self.assertEqual(init_command("copilot"), ["context-saver-rtk", "init", "-g", "--copilot"])
        self.assertEqual(init_command("claude"), ["context-saver-rtk", "init", "-g"])
        self.assertEqual(init_command("codex"), ["context-saver-rtk", "init", "-g", "--codex"])

    def test_rejects_unknown_host(self):
        with self.assertRaises(ValueError):
            init_command("unsupported")

    def test_maps_known_commands(self):
        self.assertEqual(rewrite_command(["git", "status"]), ["context-saver-rtk", "git", "status"])
        self.assertEqual(rewrite_command(["rg", "TODO", "."]), ["context-saver-rtk", "grep", "TODO", "."])
        self.assertEqual(rewrite_command(["grep", "TODO", "."]), ["context-saver-rtk", "grep", "TODO", "."])
        self.assertEqual(rewrite_command(["find", "."]), ["context-saver-rtk", "find", "."])
        self.assertEqual(rewrite_command(["ls", "."]), ["context-saver-rtk", "ls", "."])
        self.assertEqual(rewrite_command(["pytest", "-q"]), ["context-saver-rtk", "pytest", "-q"])
        self.assertEqual(rewrite_command(["ruff", "check", "."]), ["context-saver-rtk", "ruff", "check", "."])
        self.assertEqual(rewrite_command(["cat", "README.md"]), ["context-saver-rtk", "read", "README.md"])

    def test_preserves_risky_or_unknown_commands(self):
        self.assertEqual(rewrite_command(["rg", "-n", "TODO", "."]), ["rg", "-n", "TODO", "."])
        self.assertEqual(rewrite_command(["find", "-name", "*.py"]), ["find", "-name", "*.py"])
        self.assertEqual(rewrite_command(["cat", "one", "two"]), ["cat", "one", "two"])
        self.assertEqual(rewrite_command(["custom-tool", "--version"]), ["custom-tool", "--version"])

    def test_rejects_empty_command(self):
        with self.assertRaises(ValueError):
            rewrite_command([])

    def test_run_dry_run_strips_separator_and_prints_rewrite(self):
        output = StringIO()
        with patch("rtk_adapter.sys.stdout", output):
            result = rtk_adapter.main(["run", "--dry-run", "--", "git", "status"])
        self.assertEqual(result, 0)
        self.assertEqual(output.getvalue(), "context-saver-rtk git status\n")

    def test_run_falls_back_when_rtk_is_missing(self):
        with patch("rtk_adapter._rtk_path", return_value=None), patch("rtk_adapter._run", return_value=7) as run:
            with patch("rtk_adapter.sys.stderr", new_callable=StringIO) as error:
                result = rtk_adapter.main(["run", "--", "git", "status"])
        self.assertEqual(result, 7)
        run.assert_called_once_with(["git", "status"])
        self.assertIn("rtk unavailable", error.getvalue())

    def test_run_propagates_rtk_exit_code(self):
        with patch("rtk_adapter._rtk_path", return_value="C:\\bin\\rtk.exe"), patch(
            "rtk_adapter._run", return_value=3
        ) as run:
            result = rtk_adapter.main(["run", "--", "git", "status"])
        self.assertEqual(result, 3)
        run.assert_called_once_with(["context-saver-rtk", "git", "status"])

    def test_check_reports_missing_rtk(self):
        with patch("rtk_adapter._rtk_path", return_value=None), patch(
            "rtk_adapter.sys.stderr", new_callable=StringIO
        ) as error:
            result = rtk_adapter.main(["check"])
        self.assertEqual(result, 1)
        self.assertIn("rtk not found", error.getvalue())

    def test_check_runs_version_binary(self):
        completed = type("Completed", (), {"returncode": 0})()
        with patch("rtk_adapter._rtk_path", return_value="C:\\bin\\rtk.exe"), patch(
            "rtk_adapter.subprocess.run", return_value=completed
        ) as run:
            result = rtk_adapter.main(["check"])
        self.assertEqual(result, 0)
        run.assert_called_once_with(["C:\\bin\\rtk.exe", "--version"], check=False)

    def test_compact_mode_removes_filler_but_keeps_key_terms(self):
        source = "The system is actually really ready for the next step."
        result = compact_text(source, mode="full")
        self.assertIn("system", result)
        self.assertIn("ready", result)
        self.assertNotIn("actually", result)
        self.assertNotIn("really", result)

    def test_compact_mode_preserves_code_urls_and_quoted_strings(self):
        source = (
            "The result is useful.\n"
            "Visit https://example.com/the-path.\n"
            "Error: \"KEEP_THIS_ERROR\".\n"
            "```python\n"
            "print('the exact code')\n"
            "```\n"
        )
        result = compact_text(source, mode="ultra")
        self.assertIn("https://example.com/the-path.", result)
        self.assertIn('"KEEP_THIS_ERROR"', result)
        self.assertIn("```python\nprint('the exact code')\n```", result)

    def test_compact_mode_keeps_command_and_error_lines_exact(self):
        source = "$ git status --short\nError: file not found\nThe output is noisy.\n"
        result = compact_text(source, mode="ultra")
        self.assertIn("$ git status --short\n", result)
        self.assertIn("Error: file not found\n", result)
        self.assertIn("output noisy.\n", result)

    def test_compact_mode_rejects_unknown_mode(self):
        with self.assertRaises(ValueError):
            compact_text("text", mode="unknown")

    def test_compact_cli_reads_stdin(self):
        output = StringIO()
        with patch("context_saver.sys.stdin", StringIO("The output is actually noisy.\n")), patch(
            "context_saver.sys.stdout", output
        ):
            result = context_saver.main(["compact", "--mode", "full"])
        self.assertEqual(result, 0)
        self.assertIn("output noisy", output.getvalue())


if __name__ == "__main__":
    unittest.main()
