import json
import sys
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from diagram_design_mcp import server  # noqa: E402


class DiagramDesignMcpTests(unittest.TestCase):
    def test_types_are_complete(self):
        self.assertEqual(len(server.TYPES), 39)
        self.assertIn("flowchart", server.TYPES)
        self.assertIn("database-schema", server.TYPES)

    def test_tools_list_exposes_expected_tools(self):
        response = server._dispatch({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertEqual(
            names,
            {
                "diagram_design_types",
                "diagram_design_guidance",
                "diagram_design_extract_mermaid",
                "diagram_design_extract_drawio",
                "diagram_design_validate_html",
            },
        )

    def test_mermaid_extraction_returns_ir(self):
        result = server._call(
            "diagram_design_extract_mermaid",
            {"source": "flowchart LR\n  A[Start] --> B[End]"},
        )
        payload = json.loads(result["content"][0]["text"])
        self.assertEqual(payload["diagrams_total"], 1)
        self.assertEqual(payload["diagrams"][0]["edges"][0]["source"], "A")


if __name__ == "__main__":
    unittest.main()
