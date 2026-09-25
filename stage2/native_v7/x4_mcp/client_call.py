"""One native MCP stdio tool call used by the X4 software-engineering host."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _decode_result(result):
    structured = getattr(result, "structured_content", None)
    if structured is not None:
        return structured
    texts = [getattr(item, "text", None) for item in (getattr(result, "content", None) or [])]
    texts = [text for text in texts if isinstance(text, str)]
    if len(texts) == 1:
        try:
            return json.loads(texts[0])
        except json.JSONDecodeError:
            return texts[0]
    return texts


async def invoke(*, checkout, tool, arguments, observer_root=None, capture_prefix="mcp"):
    proxy_args = [
        "-m",
        "stage2.native_v7.x4_mcp.wire_proxy",
        "--capture-prefix",
        capture_prefix,
    ]
    if observer_root:
        proxy_args += ["--observer-root", observer_root]
    proxy_args += [
        "--",
        sys.executable,
        "-m",
        "stage2.native_v7.x4_mcp.server",
        "--checkout",
        checkout,
    ]
    params = StdioServerParameters(
        command=sys.executable,
        args=proxy_args,
        env=dict(os.environ),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            initialized = await session.initialize()
            listed = await session.list_tools()
            names = {item.name for item in listed.tools}
            if tool not in names:
                raise RuntimeError(f"MCP server did not advertise tool {tool!r}: {sorted(names)}")
            result = await session.call_tool(tool, arguments=arguments)
            return {
                "tool": tool,
                "result": _decode_result(result),
                "protocol_version": getattr(session, "protocol_version", None),
                "server_name": getattr(getattr(initialized, "server_info", None), "name", None),
            }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", required=True)
    parser.add_argument("--tool", required=True)
    parser.add_argument("--arguments-json", default="{}")
    parser.add_argument("--observer-root")
    parser.add_argument("--capture-prefix", default="mcp")
    args = parser.parse_args()
    arguments = json.loads(args.arguments_json)
    if not isinstance(arguments, dict):
        raise SystemExit("arguments must be a JSON object")
    result = asyncio.run(
        invoke(
            checkout=args.checkout,
            tool=args.tool,
            arguments=arguments,
            observer_root=args.observer_root,
            capture_prefix=args.capture_prefix,
        )
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
