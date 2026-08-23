import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_manifests.py"
SPEC = importlib.util.spec_from_file_location("build_manifests", SCRIPT)
assert SPEC and SPEC.loader
build_manifests = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_manifests)


class BuildManifestsTests(unittest.TestCase):
    def test_split_output_has_one_file_per_resource(self):
        parts = build_manifests._split_documents(build_manifests.build())

        self.assertEqual(len(parts), 21)
        self.assertEqual(sum(path.parts[-2] == "agents" for path in parts), 6)
        self.assertEqual(sum(path.parts[-2] == "skills" for path in parts), 9)
        self.assertEqual(sum(path.parts[-2] == "mcp-servers" for path in parts), 5)
        self.assertEqual(sum(path.parts[-2] == "plugins" for path in parts), 1)

        for path, document in parts.items():
            self.assertEqual(document.count("apiVersion: registry.agentify/v1alpha1"), 1)
            self.assertIn(f"  name: {path.stem}", document)

    def test_github_and_figma_mcp_endpoints_are_present(self):
        rendered = build_manifests.build()

        self.assertIn("name: github-mcp", rendered)
        self.assertIn("url: https://api.githubcopilot.com/mcp/", rendered)
        self.assertIn("name: figma-mcp", rendered)
        self.assertIn("url: https://mcp.figma.com/mcp", rendered)


if __name__ == "__main__":
    unittest.main()
