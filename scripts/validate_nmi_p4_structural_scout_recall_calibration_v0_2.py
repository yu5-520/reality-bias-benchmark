#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(p): return json.loads((ROOT/p).read_text())
def req(v,m):
    if not v: raise SystemExit("NMI_P4_SCOUT_CALIBRATION_VALIDATION_FAILED: "+m)

s=load("results/nmi_p4_structural_scout_recall_calibration_v0_2/summary.json")
m=load("manifests/nmi_p4_structural_scout_recall_attack_2026-09-20_v0_2.json")

req(s["population"]["heldout_natural_trajectories"]==90,"n=90")
req(s["narrow_b2"]["P"]["captured"]==4 and s["narrow_b2"]["P"]["later_supported"]==13,"P 4/13")
req(s["narrow_b2"]["R"]["captured"]==9 and s["narrow_b2"]["R"]["later_supported"]==12,"R 9/12")
req(s["narrow_b2"]["union"]["captured"]==10 and s["narrow_b2"]["union"]["later_unique_P_or_R_supported"]==13,"union 10/13")
req(abs(s["narrow_b2"]["union"]["conditional_miss_percent"]-23.0769)<1e-4,"union miss")
req(s["broad_triage"]["later_positive_post_late_packet_coverage"]=="13/13","broad proxy")
req(s["r8_source_integrity"]["recovered_frozen_external_package"]["matches_frozen_manifest"] is True,"recovered R8")
req(s["r8_source_integrity"]["repository_object"]["matches_manifest"] is False,"repo integrity defect")
req(s["scientific_boundary"]["prevalence_claim"] is False,"prevalence guard")
req(m["execution_boundary"]["new_subject_runs"]==0,"no runs")
req(m["execution_boundary"]["new_semantic_adjudication"] is False,"no new semantic adjudication")
print("NMI_P4_SCOUT_CALIBRATION_VALIDATION=PASS")
print("B2_UNION_CAPTURE=10/13")
print("B2_UNION_MISS_PERCENT=23.0769")
print("P_CAPTURE=4/13")
print("R_CAPTURE=9/12")
print("BROAD_POST_LATE_PROXY=13/13")
print("R8_EXTERNAL_RECOVERY_MATCHES_MANIFEST=true")
