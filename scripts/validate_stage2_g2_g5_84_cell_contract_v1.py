#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCH = ROOT / "configs/stage2_g2_g5_84_cell_natural_block_launch_contract_v1.json"
HORIZON = ROOT / "configs/stage2_g2_g5_logical_decision_horizon_v1.json"
POLICY = ROOT / "configs/stage2_g2_g5_execution_and_evaluation_policy_v2.json"


def require(cond, msg):
    if not cond:
        raise SystemExit(msg)


def main():
    launch = json.loads(LAUNCH.read_text())
    horizon = json.loads(HORIZON.read_text())
    policy = json.loads(POLICY.read_text())

    require(launch["cell_count"] == 84, "launch contract must contain 84 cells")
    require(len(launch["cells"]) == 84, "launch cell list length mismatch")
    require(launch["first_attempt_only"] is True, "first-attempt-only not frozen")
    require(launch["no_B_until_all_84_A_sealed"] is True, "B gate not frozen")
    require(horizon["common_ceiling"] == 64, "common logical-decision ceiling must be 64")
    require(horizon["subject_model_parameters_unchanged"] is True, "model parameters changed with horizon")
    require(policy["natural_phase"]["all_84_before_any_B"] is True, "policy does not enforce 84 A before B")

    groups = Counter(row["group_id"] for row in launch["cells"])
    systems = Counter(row["system_id"] for row in launch["cells"])
    tasks = Counter(row["task_id"] for row in launch["cells"])
    require(groups == Counter({"G2":21,"G3":21,"G4":21,"G5":21}), f"group counts differ: {groups}")
    require(systems == Counter({f"X{i}":12 for i in range(1,8)}), f"system counts differ: {systems}")
    require(tasks == Counter({"T1":28,"T2":28,"T3":28}), f"task counts differ: {tasks}")

    seen = set()
    for expected_order, row in enumerate(launch["cells"], start=1):
        require(row["order"] == expected_order, "launch order is not contiguous")
        key = (row["group_id"], row["cell_id"])
        require(key not in seen, f"duplicate cell {key}")
        seen.add(key)
        require(row["natural_attempt_index"] == 1, f"{key}: natural attempt index is not 1")
        require(row["logical_decision_ceiling"] == 64, f"{key}: horizon differs from 64")
        require(row["repair_actions_during_A"] == 0, f"{key}: repair action admitted during A")
        expected_root = f"stage2/replication_v2/{row['group_id']}/natural_A/{row['cell_id']}"
        require(row["output_root"] == expected_root, f"{key}: output root differs")
        require(row["audit_raw_bundle_manifest"] == expected_root + "/audit_raw_bundle_manifest.json", f"{key}: audit manifest path differs")
        require(row["monitor_runtime_bundle_manifest"] == expected_root + "/monitor_runtime_bundle_manifest.json", f"{key}: monitor manifest path differs")

    mappings = horizon["mappings"]
    require(set(mappings) == {f"X{i}" for i in range(1,8)}, "horizon mapping must cover X1-X7")
    require(mappings["X1"]["counter"] == "CountingModelClient.create_calls", "X1 logical-decision counter changed")
    require("PassiveActionTapProvider.total_records" in mappings["X2"]["counter"], "X2 provider counter missing")
    require("turns_used" in mappings["X3"]["counter"], "X3 turn accounting missing")
    for x in ("X4","X5","X6","X7"):
        require(mappings[x]["counter"] == "PassiveActionTapProvider.total_records", f"{x} provider counter changed")

    print("Stage-II G2-G5 84-cell launch contract validation PASS")
    print("4 groups x 21 natural cells: PASS")
    print("64 logical decisions per cell: PASS")
    print("model parameters unchanged: PASS")
    print("audit/monitor manifest paths separated: PASS")
    print("no B before all 84 A sealed: PASS")


if __name__ == "__main__":
    main()
