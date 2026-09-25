"""MCP SDK client boundary for checkout resource reads and tool operations."""
import hashlib
import json
import os
import sys

from .evidence import canonical_bytes
from .workspace import CodeWorkspace


class MCPWorkspace(CodeWorkspace):
    def __init__(self, root, capture):
        if capture.probe != "X4":
            raise ValueError("MCP checkout requires X4")
        super().__init__(root, capture)
        self.serial = 0

    async def open(self):
        from mcp import Client
        from mcp.client.stdio import StdioServerParameters
        env = {"PATH": os.getenv("PATH", ""), "STAGE2_CHECKOUT": str(self.root),
               "PYTHONPATH": str(__import__("pathlib").Path(__file__).resolve().parent.parent)}
        server = StdioServerParameters(command=sys.executable, args=["-m", "stage2.mcp_checkout_server"],
                                       cwd=str(self.root), env=env)
        self._context = Client(server, mode="2026-07-28")
        self.client = await self._context.__aenter__()
        if self.client.protocol_version != "2026-07-28":
            raise ValueError("wrong MCP protocol version")
        listed = await self.client.list_tools()
        names = {item.name for item in listed.tools}
        if names != {"list_files", "read_file", "write_file", "run_tests"}:
            raise ValueError("MCP tool registry mismatch")

    async def close(self):
        if hasattr(self, "_context"):
            await self._context.__aexit__(None, None, None)

    def _native(self, operation, raw, actor, source, parents, phase, suffix, status="success"):
        self.serial += 1
        row = self.capture.capture(
            event_id=f"mcp-{self.serial}", operation=operation, phase=phase,
            native_locator=f"mcp:{suffix}", hook_id="mcp.Client.v2.2.0",
            raw=raw, actor=actor, source_id=source, carrier_id=f"mcp:{suffix}:{self.serial}",
            carrier_type="mcp-resource" if operation == "resource_read" else "mcp-tool",
            parent_ids=parents, status=status)
        return row["event_id"]

    async def _call(self, name, args, actor, source, parents):
        sent = self._native("tool_call", canonical_bytes({"name": name, "arguments": args}),
                            actor, source, parents, "emitted", name)
        result = await self.client.call_tool(name, args)
        returned = self._native("tool_call", result.model_dump_json().encode(), actor, source,
                                (sent,), "returned", name, "error" if result.is_error else "success")
        if result.is_error:
            raise ValueError(f"MCP {name} returned an error: {result.content}")
        return result, returned

    async def list_files(self, actor, source, parents=()):
        result, event = await self._call("list_files", {}, actor, source, parents)
        value = result.structured_content
        if isinstance(value, dict) and "result" in value:
            value = value["result"]
        if not isinstance(value, list):
            raise ValueError("unexpected MCP file list shape")
        return value, event

    async def read_file(self, path, actor, source, parents=()):
        self._path(path)
        if path == "README.md":
            requested = self._native("resource_read", canonical_bytes({"uri": "checkout://readme"}),
                                     actor, source, parents, "emitted", "resources/read")
            response = await self.client.read_resource("checkout://readme")
            event = self._native("resource_read", response.model_dump_json().encode(), actor, source,
                                 (requested,), "returned", "resources/read")
            return response.contents[0].text, event
        result, event = await self._call("read_file", {"path": path}, actor, source, parents)
        value = result.structured_content
        if isinstance(value, dict) and "result" in value:
            value = value["result"]
        if not isinstance(value, str):
            raise ValueError("unexpected MCP file content shape")
        return value, event

    async def write_file(self, path, content, actor, source, parents=()):
        target = self._path(path)
        before = target.read_bytes() if target.exists() else b""
        _, event = await self._call("write_file", {"path": path, "content": content}, actor, source, parents)
        after = target.read_bytes()
        if after != content.encode():
            raise ValueError("MCP server file write was not observed on disk")
        changed = self._record("file_change", after, path, actor,
                               f"{source};previous_sha256={hashlib.sha256(before).hexdigest()}",
                               (event,), phase="executed")
        return {"path": path, "before_sha256": hashlib.sha256(before).hexdigest(),
                "after_sha256": hashlib.sha256(after).hexdigest()}, changed["event_id"]

    async def run_tests(self, actor, source, parents=()):
        result, event = await self._call("run_tests", {}, actor, source, parents)
        value = result.structured_content
        if isinstance(value, dict) and "result" in value:
            value = value["result"]
        if not isinstance(value, dict) or "returncode" not in value:
            raise ValueError("unexpected MCP test result shape")
        tested = self._record("test_run", canonical_bytes(value), "tests/", actor, source,
                              (event,), status="success" if value["returncode"] == 0 else "error")
        return value, tested["event_id"]
