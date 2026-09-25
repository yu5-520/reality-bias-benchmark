"""Transparent stdio tee used only to observe MCP wire bytes.

The proxy does not parse, rewrite, delay intentionally, or synthesize protocol messages.
It relays exact newline-delimited bytes between the official MCP client and server and
optionally writes byte-identical copies outside the task checkout.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import threading
from pathlib import Path


def _copy_lines(source, destination, capture=None):
    try:
        while True:
            line = source.readline()
            if not line:
                break
            if capture is not None:
                capture.write(line)
                capture.flush()
                os.fsync(capture.fileno())
            destination.write(line)
            destination.flush()
    except (BrokenPipeError, OSError):
        pass
    finally:
        try:
            destination.close()
        except Exception:
            pass


def relay(command, observer_root=None, capture_prefix="mcp"):
    observer = Path(observer_root) if observer_root else None
    if observer is not None:
        observer.mkdir(parents=True, exist_ok=True)
        c2s = (observer / f"{capture_prefix}.client_to_server.bin").open("xb")
        s2c = (observer / f"{capture_prefix}.server_to_client.bin").open("xb")
        serr = (observer / f"{capture_prefix}.server_stderr.bin").open("xb")
    else:
        c2s = s2c = serr = None

    proc = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
    )
    assert proc.stdin is not None and proc.stdout is not None and proc.stderr is not None

    threads = [
        threading.Thread(
            target=_copy_lines,
            args=(sys.stdin.buffer, proc.stdin, c2s),
            daemon=True,
        ),
        threading.Thread(
            target=_copy_lines,
            args=(proc.stdout, sys.stdout.buffer, s2c),
            daemon=True,
        ),
        threading.Thread(
            target=_copy_lines,
            args=(proc.stderr, sys.stderr.buffer, serr),
            daemon=True,
        ),
    ]
    for thread in threads:
        thread.start()
    returncode = proc.wait()
    for thread in threads[1:]:
        thread.join(timeout=2)
    for stream in (c2s, s2c, serr):
        if stream is not None and not stream.closed:
            stream.close()
    return returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observer-root")
    parser.add_argument("--capture-prefix", default="mcp")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SystemExit("wire proxy requires a server command")
    raise SystemExit(relay(command, args.observer_root, args.capture_prefix))


if __name__ == "__main__":
    main()
