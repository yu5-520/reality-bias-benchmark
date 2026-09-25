"""Official MCP stdio server exposing the frozen checkout operations for X4."""
from __future__ import annotations

import argparse
import json

from mcp.server.mcpserver import MCPServer

from stage2.native_v7.software_host_v1 import HostCheckout


def build_server(checkout):
    workspace = HostCheckout(checkout)
    server = MCPServer(
        "stage2-x4-checkout",
        description="Frozen Stage-II software checkout exposed through the official MCP protocol.",
    )

    @server.tool()
    def list_files() -> str:
        """List regular files in the frozen task checkout."""
        return json.dumps(workspace.list_files(), ensure_ascii=False, sort_keys=True)

    @server.tool()
    def read_file(path: str) -> str:
        """Read one UTF-8 file from the task checkout by relative path."""
        return json.dumps(workspace.read_file(path), ensure_ascii=False)

    @server.tool()
    def write_file(path: str, content: str) -> str:
        """Replace one UTF-8 checkout file using the frozen bounded write semantics."""
        return json.dumps(workspace.write_file(path, content), ensure_ascii=False, sort_keys=True)

    @server.tool()
    def run_tests() -> str:
        """Run the frozen checkout unit-test command."""
        return json.dumps(workspace.run_tests(), ensure_ascii=False, sort_keys=True)

    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", required=True)
    args = parser.parse_args()
    build_server(args.checkout).run(transport="stdio")


if __name__ == "__main__":
    main()
