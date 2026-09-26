from __future__ import annotations

import argparse
import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from stage2.native_v7.x3_a2a.service import build_app
from stage2.r7_checkpoint_v1.a2a_adapter import CheckpointableRoleRuntime
from stage2.r7_checkpoint_v1.common import digest


class SidecarCheckpointRoleRuntime(CheckpointableRoleRuntime):
    """Stage-II-owned A2A role service with out-of-band state snapshots.

    The sidecar file is not an A2A route or message. It is written only by the
    experiment-owned service application before serving and after one complete
    role-call returns.
    """

    def __init__(self, *, checkpoint_state_file, **kwargs):
        self.checkpoint_state_file = Path(checkpoint_state_file)
        super().__init__(**kwargs)
        self._persist_checkpoint("SERVICE_READY")

    def _persist_checkpoint(self, boundary: str):
        state = self.save_stage2_state()
        payload = {
            "schema": "RB-STAGE2-R7-G1-A2A-ROLE-SIDECAR-v1",
            "role": self.role,
            "boundary": boundary,
            "state": state,
            "state_sha256": digest(state),
        }
        self.checkpoint_state_file.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=".stage2-r7-a2a-sidecar-",
            dir=self.checkpoint_state_file.parent,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=False, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, self.checkpoint_state_file)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    async def execute_payload(self, payload: dict[str, Any]):
        result = await super().execute_payload(payload)
        self._persist_checkpoint("ROLE_CALL_RETURN")
        return result


def main():
    import uvicorn

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True)
    parser.add_argument("--checkout", required=True)
    parser.add_argument("--directory-file", required=True)
    parser.add_argument("--public-url", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--mode", choices=["subject", "scripted"], default="subject")
    parser.add_argument("--script-file")
    parser.add_argument("--checkpoint-state-file", required=True)
    parser.add_argument("--max-turns", type=int)
    args = parser.parse_args()

    runtime = SidecarCheckpointRoleRuntime(
        role=args.role,
        checkout=args.checkout,
        directory_file=args.directory_file,
        mode=args.mode,
        script_file=args.script_file,
        checkpoint_state_file=args.checkpoint_state_file,
        max_turns=args.max_turns,
    )
    app = build_app(runtime=runtime, public_url=args.public_url)
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=args.port,
        log_level="error",
        access_log=False,
    )


if __name__ == "__main__":
    main()
