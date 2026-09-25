"""Transparent HTTP-body relay for external observation of X3 A2A JSON-RPC."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path


def _write_once(path, data):
    with Path(path).open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def build_app(*, backend, observer_root, role):
    import httpx
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.routing import Route

    root = Path(observer_root)
    root.mkdir(parents=True, exist_ok=False)
    serial = {"value": 0}
    lock = asyncio.Lock()

    async def relay(request: Request):
        body = await request.body()
        query = request.url.query
        target = backend.rstrip("/") + request.url.path
        if query:
            target += "?" + query
        headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in {"host", "content-length", "connection"}
        }
        async with httpx.AsyncClient(timeout=180, trust_env=False) as client:
            upstream = await client.request(
                request.method,
                target,
                content=body,
                headers=headers,
            )
            response_body = upstream.content
        async with lock:
            serial["value"] += 1
            seq = serial["value"]
            prefix = f"{seq:04d}-{request.method.lower()}"
            _write_once(root / f"{prefix}-request.bin", body)
            _write_once(root / f"{prefix}-response.bin", response_body)
            metadata = {
                "sequence": seq,
                "role": role,
                "method": request.method,
                "path": request.url.path,
                "request_sha256": hashlib.sha256(body).hexdigest(),
                "response_sha256": hashlib.sha256(response_body).hexdigest(),
                "status_code": upstream.status_code,
            }
            _write_once(
                root / f"{prefix}-meta.json",
                (json.dumps(metadata, sort_keys=True) + "\n").encode(),
            )
        response_headers = {
            key: value
            for key, value in upstream.headers.items()
            if key.lower() not in {"content-length", "transfer-encoding", "connection"}
        }
        return Response(
            content=response_body,
            status_code=upstream.status_code,
            headers=response_headers,
        )

    return Starlette(
        routes=[
            Route("/{path:path}", relay, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]),
            Route("/", relay, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]),
        ]
    )


def main():
    import uvicorn

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", required=True)
    parser.add_argument("--observer-root", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--port", required=True, type=int)
    args = parser.parse_args()
    uvicorn.run(
        build_app(backend=args.backend, observer_root=args.observer_root, role=args.role),
        host="127.0.0.1",
        port=args.port,
        log_level="error",
        access_log=False,
    )


if __name__ == "__main__":
    main()
