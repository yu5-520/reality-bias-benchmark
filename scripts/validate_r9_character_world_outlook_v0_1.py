#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    return json.loads((ROOT / path).read_text())

def require(cond, msg):
    if not cond:
        raise SystemExit("R9_CHARACTER_WORLD_OUTLOOK_VALIDATION_FAILED: " + msg)

cfg = load("configs/r9_character_world_process_reality_outlook_v0.1.json")
man = load("manifests/r9_character_world_outlook_2026-09-20_v0_1.json")

require(cfg["status"] == "APPLICATION_OUTLOOK_CONCEPTUAL_INSTANTIATION", "status")
require(cfg["creates_new_top_level_branch"] is False, "must remain business-deployment sub-branch")
require(cfg["top_level_outlook_branch"] == "BUSINESS_DEPLOYMENT_PERSISTENT_OPERATIONAL_REALITY", "outlook branch")
require(cfg["scientific_boundary"]["new_subject_evidence"] is False, "no new subject evidence")
require(cfg["scientific_boundary"]["formal_cpr_adjudication"] is False, "no formal CPR adjudication")
require(man["evidence_boundary"]["new_subject_runs"] == 0, "subject runs")
require(man["evidence_boundary"]["provider_calls"] == 0, "provider calls")
require(man["evidence_boundary"]["evaluator_calls"] == 0, "evaluator calls")
require(man["evidence_boundary"]["raw_evidence_mutation"] is False, "raw evidence mutation")

for path in [
    man["parent_r9_report"],
    man["application_note"],
    man["config"],
    man["change_note"],
]:
    require((ROOT / path).exists(), "missing " + path)

print("R9_CHARACTER_WORLD_OUTLOOK_VALIDATION=PASS")
print("OUTLOOK_BRANCH=BUSINESS_DEPLOYMENT_PERSISTENT_OPERATIONAL_REALITY")
print("SYSTEM_PAIR=CHARACTER_SYSTEM<->WORLD_SOCIAL_SYSTEM")
print("NEW_EXPERIMENTAL_EVIDENCE=false")
print("FORMAL_CPR_ADJUDICATION=false")
