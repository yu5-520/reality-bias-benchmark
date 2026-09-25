"""Separate-process MCP 2026-07-28 checkout tool/resource server."""
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path


def create_server(root):
    from mcp.server.mcpserver import MCPServer
    from pydantic import BaseModel

    class WriteResult(BaseModel):
        path: str
        written: int

    class TestResult(BaseModel):
        returncode: int
        stdout: str
        stderr: str

    root = Path(root).resolve(strict=True)
    app = MCPServer("Stage-II Checkout", version="stage2-mcp-checkout-v1")

    def path_for(path):
        if not isinstance(path, str) or not path or Path(path).is_absolute():
            raise ValueError("relative path required")
        dest = (root / path).resolve()
        if dest == root or not dest.is_relative_to(root) or dest.is_symlink():
            raise ValueError("path leaves checkout")
        return dest

    @app.resource("checkout://readme", mime_type="text/markdown")
    def project_readme() -> str:
        return path_for("README.md").read_text(encoding="utf-8")

    @app.tool(name="list_files")
    def list_files() -> list[str]:
        return sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()
                      and not p.is_symlink() and "__pycache__" not in p.parts)

    @app.tool(name="read_file")
    def read_file(path: str) -> str:
        value = path_for(path).read_bytes()
        if len(value) > 262144:
            raise ValueError("file too large")
        return value.decode("utf-8")

    @app.tool(name="write_file", structured_output=True)
    def write_file(path: str, content: str) -> WriteResult:
        if len(content.encode()) > 262144:
            raise ValueError("content too large")
        dest = path_for(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        return WriteResult(path=path, written=len(content.encode("utf-8")))

    @app.tool(name="run_tests", structured_output=True)
    def run_tests() -> TestResult:
        result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                                cwd=root, text=True, capture_output=True, timeout=20, check=False)
        return TestResult(returncode=result.returncode, stdout=result.stdout[-30000:],
                          stderr=result.stderr[-30000:])

    return app


if __name__ == "__main__":
    checkout = os.environ.get("STAGE2_CHECKOUT")
    if not checkout:
        raise SystemExit("STAGE2_CHECKOUT is required")
    asyncio.run(create_server(checkout).run_stdio_async())
