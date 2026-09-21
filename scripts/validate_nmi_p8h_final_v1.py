#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
M=ROOT/"docs/submission/nmi/NMI_Manuscript_v0.15_STANDARD.md"
C=ROOT/"docs/submission/nmi/NMI_Cover_Letter_v0.4_FINAL.md"
S=ROOT/"docs/submission/nmi/NMI_Supplementary_Information_v0.3.md"
META=ROOT/"configs/nmi_p8_portal_metadata_template_v1.json"
CONTRACT=ROOT/"configs/nmi_submission_contract_v1.17.json"
MANIFEST=ROOT/"manifests/nmi_p8h_final_export_2026-09-21_v1.json"

def req(v,msg):
    if not v:
        raise SystemExit("NMI_P8H_FINAL_VALIDATION_FAILED: "+msg)

m=M.read_text(encoding="utf-8")
c=C.read_text(encoding="utf-8")
s=S.read_text(encoding="utf-8")
meta=json.loads(META.read_text(encoding="utf-8"))
contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))

for x in ["Yeyu Zheng","Independent Researcher, Jiangxi, China","zhengyeyu520@gmail.com"]:
    req(x in m, f"manuscript identity missing: {x}")
    req(x in c, f"cover identity missing: {x}")

req("The author declares no competing interests." in m, "manuscript competing interests")
req("Related manuscripts under consideration or in press elsewhere:** None." in c, "related manuscripts disclosure")
req("Prior discussions with a Nature Machine Intelligence editor about this work:** None." in c, "prior editor disclosure")
req("Standard single-anonymized peer review." in c, "review mode disclosure")
req("Supplementary Figure plan" not in s, "planning-only supplementary figure promise remains")
req("wave-3-56ee79f97f54" in s and "43 descendants recomputed" in s, "R7 supplement case content")
req(meta["status"]=="VERIFIED_HUMAN_METADATA_BOUND","metadata status")
req(meta["required_before_final_export"]["peer_review_mode"]=="STANDARD","peer review metadata")
req(meta["required_before_final_export"]["author_name_publication_form"]=="Yeyu Zheng","author metadata")
req(meta["required_before_final_export"]["corresponding_author_email"]=="zhengyeyu520@gmail.com","email metadata")
req(contract["status"]=="NMI_P8H_FINAL_EXPORT_COMPLETE_PORTAL_READY","contract status")
req(contract["portal_ready"] is True,"portal ready")
req(contract["final_export"]["workflow_run_id"]==35564194467,"final workflow binding")
req(contract["final_export"]["visual_qa"]=="PASS","visual QA")
req(manifest["status"]=="FINAL_EXPORT_COMPLETE_PORTAL_READY","manifest status")
req(manifest["portal_ready"] is True,"manifest portal ready")
req(manifest["visual_qa"]["manuscript_pages"]==13,"manuscript page count")
req(manifest["visual_qa"]["supplement_pages"]==4,"supplement page count")
req(manifest["visual_qa"]["cover_letter_pages"]==1,"cover page count")

print("NMI_P8H_FINAL_VALIDATION=PASS")
print("AUTHOR=Yeyu Zheng")
print("PEER_REVIEW_MODE=STANDARD_SINGLE_ANONYMIZED")
print("VISUAL_QA=PASS")
print("PORTAL_READY=true")
print("NEXT_ACTION=NMI_PORTAL_UPLOAD")
