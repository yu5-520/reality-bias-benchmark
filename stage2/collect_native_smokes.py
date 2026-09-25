"""Aggregate seven Stage-II native smoke receipts without turning blockers into substitutes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .evidence import check_capture

PROBES = [f"X{i}" for i in range(1, 8)]
ALLOWED = {"NATIVE_SMOKE_PASS", "ENGINEERING_BLOCKED"}


def collect(root: Path) -> dict:
    statuses = {}
    status_paths = {}
    for path in root.rglob("status.json"):
        row = json.loads(path.read_text())
        probe = row.get("probe")
        if probe in statuses:
            raise ValueError(f"duplicate status for {probe}")
        statuses[probe] = row
        status_paths[probe] = path
    missing = sorted(set(PROBES) - set(statuses))
    if missing:
        raise ValueError("missing native smoke receipts: " + ", ".join(missing))
    for probe in PROBES:
        row = statuses[probe]
        if row.get("status") not in ALLOWED:
            raise ValueError(f"{probe}: invalid status {row.get('status')}")
        if row["status"] == "NATIVE_SMOKE_PASS":
            count = check_capture(status_paths[probe].parent)
            if count < 2:
                raise ValueError(f"{probe}: passed native smoke has too few events")
        elif not row.get("reason"):
            raise ValueError(f"{probe}: ENGINEERING_BLOCKED requires an explicit reason")
    passed = [p for p in PROBES if statuses[p]["status"] == "NATIVE_SMOKE_PASS"]
    blocked = [p for p in PROBES if statuses[p]["status"] == "ENGINEERING_BLOCKED"]
    return {
        "schema": "stage2-native-gate-summary-v1",
        "passed": passed,
        "blocked": blocked,
        "pass_count": len(passed),
        "blocked_count": len(blocked),
        "all_probes_accounted_for": True,
        "subject_execution_authorized": False,
        "statuses": [statuses[p] for p in PROBES],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    summary = collect(Path(args.root))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
