#!/usr/bin/env python3
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

M = ROOT / "docs/submission/nmi/NMI_Manuscript_v0.14.md"
COVER = ROOT / "docs/submission/nmi/NMI_Cover_Letter_v0.3.md"
LIVE = ROOT / "docs/submission/nmi/NMI_Official_Submission_Requirements_2026-09-21.md"
META = ROOT / "configs/nmi_p8_portal_metadata_template_v1.json"
CONTRACT = ROOT / "configs/nmi_submission_contract_v1.16.json"
STATUS = ROOT / "docs/submission/nmi/NMI_P8_Status_v1.md"
SUPP = ROOT / "docs/submission/nmi/NMI_Supplementary_Information_v0.3.md"
FIGINV = ROOT / "docs/submission/nmi/NMI_P8_Figure_Asset_Inventory_v1.md"

def req(v, msg):
    if not v:
        raise SystemExit("NMI_P8_VALIDATION_FAILED: " + msg)

def wc(x: str) -> int:
    x = re.sub(r"\[[^\]]+\]", " ", x)
    return len(re.findall(r"[A-Za-z0-9À-ɏ'-]+", x))

m = M.read_text(encoding="utf-8")
cover = COVER.read_text(encoding="utf-8")
live = LIVE.read_text(encoding="utf-8")
meta = json.loads(META.read_text(encoding="utf-8"))
contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
status = STATUS.read_text(encoding="utf-8")
supp = SUPP.read_text(encoding="utf-8")
figinv = FIGINV.read_text(encoding="utf-8")

abs_start = m.index("## Abstract") + len("## Abstract")
intro_start = m.index("\nMulti-agent AI systems are increasingly", abs_start)
methods = m.index("## Methods")
abstract_words = wc(m[abs_start:intro_start])
main_words = wc(m[intro_start:methods])

req(abstract_words == 147 and abstract_words <= 150, f"abstract words {abstract_words}")
req(main_words == 2942 and main_words <= 3500, f"main words {main_words}")
req("## Introduction" not in m, "introduction heading present")
req("## Results" in m, "Results missing")
req("## Discussion" in m, "Discussion missing")
req("## Methods" in m, "Methods missing")
req(len(re.findall(r"(?m)^\*\*Figure [1-5] \|", m)) == 5, "figure legends != 5")
req(len(re.findall(r"(?m)^\d+\. ", m[m.index("## References"):m.index("## Figure legends")])) == 12, "references != 12")
req("### AI systems and human responsibility" in m, "LLM disclosure missing")

for s in [
    "main text: up to **3,500 words**",
    "abstract: up to **150 words**",
    "display items: up to **6**",
    "Introduction without heading",
    "double-anonymized peer review",
    "Competing interests",
]:
    req(s in live, f"live requirement snapshot missing: {s}")

for s in [
    "Related manuscripts under consideration or in press elsewhere",
    "Prior discussions with a Nature Machine Intelligence editor",
    "Peer-review model",
    "Competing interests",
    "CORRESPONDING AUTHOR",
]:
    req(s in cover, f"cover completion field missing: {s}")

req(meta["status"] == "AWAITING_HUMAN_VERIFICATION", "metadata template status")
required = meta["required_before_final_export"]
req(all(v is None for v in required.values()), "required human fields unexpectedly populated")
req(meta["guards"]["guess_identity"] is False, "identity guess guard")
req(meta["guards"]["infer_peer_review_mode"] is False, "review-mode inference guard")
req(meta["guards"]["invent_archive_identifier"] is False, "archive invention guard")

req(contract["status"] == "NMI_P8_AUTOMATED_PREFLIGHT_COMPLETE_WAITING_HUMAN_METADATA", "contract status")
req(contract["p8"]["live_requirement_revalidation"] == "PASS", "live revalidation status")
req(contract["p8"]["portal_ready"] is False, "portal_ready must be false")
req(contract["p8"]["final_export_status"] == "BLOCKED_ON_VERIFIED_HUMAN_METADATA", "export block")
req(contract["scientific_freeze"]["new_subject_runs"] == 0, "subject run boundary")
req(contract["scientific_freeze"]["provider_calls"] == 0, "provider call boundary")
req(contract["scientific_freeze"]["evaluator_calls"] == 0, "evaluator call boundary")
req(contract["scientific_freeze"]["new_semantic_adjudication"] is False, "semantic adjudication boundary")
req("FINAL EXPORT CORRECTLY BLOCKED ON HUMAN METADATA" in status, "status wording")
req("Supplementary Figure plan" not in supp, "unmaterialized supplementary figure plan remains")
req("Supplementary material boundary" in supp, "supplement material boundary missing")
req(contract["p8"]["supplement"].endswith("NMI_Supplementary_Information_v0.3.md"), "contract supplement binding")
req(contract["p8"]["unmaterialized_supplementary_figure_promises_removed"] is True, "supplement cleanup flag")
req(contract["p8"]["figure_inventory"].endswith("NMI_P8_Figure_Asset_Inventory_v1.md"), "figure inventory binding")
req(figinv.count("docs/submission/nmi/figures/p5/Fig") == 5, "main figure asset inventory != 5")
req(contract["next_action"] == "NMI_P8H_METADATA_BIND_AND_FINAL_EXPORT", "next human gate")

print("NMI_P8_REVALIDATION=PASS")
print("ABSTRACT_WORDS=147")
print("MAIN_TEXT_BEFORE_METHODS=2942")
print("MAIN_FIGURES=5")
print("REFERENCES=12")
print("LIVE_REQUIREMENTS_RECHECKED=2026-09-21")
print("PORTAL_READY=false")
print("SUPPLEMENT=v0.3_NO_UNMATERIALIZED_FIGURE_PLAN")
print("MAIN_FIGURE_ASSETS=5")
print("FINAL_EXPORT_STATUS=BLOCKED_ON_VERIFIED_HUMAN_METADATA")
print("NEXT_GATE=NMI_P8H_METADATA_BIND_AND_FINAL_EXPORT")
