#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/reports/2026-09-26/StageII_General_Chapter_Process_Reality_Methodology_and_Hypotheses_v1.md"
REGISTRY = ROOT / "configs/stage2_general_chapter_claim_registry_v1.json"
STANDARD = ROOT / "docs/reporting/process_reality_report_standard_v1_9.md"
PLAN = ROOT / "docs/R_Plan_v7.31.md"

EXPECTED = {
    "GC-M1","GC-M2","GC-M3","GC-M4","GC-M5",
    "GC-H1a","GC-H1b","GC-H1c",
    "GC-H2a","GC-H2b","GC-H2c",
    "GC-H3a","GC-H3b","GC-H3c",
}

def require(cond, message):
    if not cond:
        raise SystemExit(message)

def main():
    report = REPORT.read_text()
    standard = STANDARD.read_text()
    plan = PLAN.read_text()
    registry = json.loads(REGISTRY.read_text())

    require(registry["schema"] == "stage2-general-chapter-claim-registry-v1", "registry schema mismatch")
    require(registry["version"] == "1.0", "registry version mismatch")
    require(registry["natural_matrix"] == {"cells": 21, "reruns": 0, "state": "CLOSED"}, "natural matrix contract mismatch")
    require(registry["contrasts"]["c3_c4"] == "UNSPENT_NOT_REQUIRED", "contrast boundary mismatch")

    ids = [row["id"] for row in registry["claims"]]
    require(len(ids) == len(set(ids)), "duplicate claim IDs")
    require(set(ids) == EXPECTED, f"claim ID set mismatch: {sorted(set(ids) ^ EXPECTED)}")

    for claim_id in EXPECTED:
        require(claim_id in report, f"{claim_id} absent from General Chapter")

    require("child citation != circular proof" in report, "anti-circularity statement missing")
    require("Outcome convergence does not imply process equivalence" in report, "process/endpoint invariant missing")
    require("Memory manages information availability; a Common Pool manages shared operational reality." in report, "Common Pool boundary missing")
    require("C3/C4" in report and "does not authorize" in report, "authorization boundary missing")

    require("Anti-circularity rule" in standard, "v1.9 anti-circularity rule missing")
    require("Relation to Stage-II General Chapter" in standard, "child-report relation block missing")
    require("GENERAL CHAPTER v1.0 FROZEN" in plan, "v7.31 plan freeze missing")
    require("C3/C4 UNSPENT AND NOT REQUIRED" in plan, "v7.31 contrast boundary missing")

    hypothesis = [c for c in registry["claims"] if c["class"] == "RESEARCH_HYPOTHESIS"]
    require(any(c["status"] == "NOT_ESTABLISHED" for c in hypothesis), "hypothesis boundary collapsed")
    require(any(c["status"] == "SUPPORTED_CANDIDATE" for c in hypothesis), "supported-candidate hypothesis layer missing")

    print("PASS: Stage-II General Chapter v1.0 and forward child-report contract are internally consistent")

if __name__ == "__main__":
    main()
