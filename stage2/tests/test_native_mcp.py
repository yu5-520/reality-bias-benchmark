import asyncio
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from stage2.evidence import NativeCapture, check_capture
from stage2.workspace import new_workspace


@unittest.skipUnless(importlib.util.find_spec("mcp"), "pinned MCP SDK unavailable")
class MCPNativeSmoke(unittest.TestCase):
    def test_stdio_server_resource_tool_and_write(self):
        from stage2.mcp_workspace import MCPWorkspace

        async def smoke(root):
            capture = NativeCapture(root / "raw", "X4", "NON_SUBJECT_MCP_SMOKE",
                                    {"probe": "X4", "source_commit": "5f5440bb26a62e2cf3440b92da5a667efa03b267",
                                     "sdk_commit": "f1b6589088534632fef92238ee9750951e3c0185"})
            checkout = new_workspace(root / "checkout")
            workspace = MCPWorkspace(checkout, capture)
            await workspace.open()
            try:
                self.assertEqual(workspace.client.protocol_version, "2026-07-28")
                readme, _ = await workspace.read_file("README.md", "release_lead", "task:T1")
                self.assertIn("Checkout sample", readme)
                names, _ = await workspace.list_files("qa", "task:T1")
                self.assertIn("versions/before/server.py", names)
                change, _ = await workspace.write_file("web/app.js", "console.log('smoke');", "frontend", "task:T2")
                self.assertNotEqual(change["before_sha256"], change["after_sha256"])
                tests, _ = await workspace.run_tests("qa", "task:T2")
                self.assertEqual(tests["returncode"], 0)
            finally:
                await workspace.close()
            self.assertEqual(check_capture(root / "raw"), 10)
            records = [json.loads(line) for line in (root / "raw/events.jsonl").read_text().splitlines()]
            self.assertIn("resource_read", [row["operation"] for row in records])
            self.assertIn("tool_call", [row["operation"] for row in records])

        with tempfile.TemporaryDirectory() as directory:
            asyncio.run(smoke(Path(directory)))
