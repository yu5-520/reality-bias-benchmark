#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
M=ROOT/"docs/submission/nmi/NMI_Manuscript_v0.17_PUBLIC_RAW.md"
META=ROOT/"configs/nmi_p8_portal_metadata_template_v1.json"
CONTRACT=ROOT/"configs/nmi_submission_contract_v1.19.json"
MANIFEST=ROOT/"manifests/nmi_p8h2_public_frozen_raw_final_export_2026-09-21_v1.json"
RELEASE_MANIFEST=ROOT/"evidence/frozen_raw/release_manifest_v1.json"
SUMS=ROOT/"evidence/frozen_raw/SHA256SUMS_v1.txt"

REPO="https://github.com/yu5-520/reality-bias-benchmark"
RAW="https://github.com/yu5-520/reality-bias-benchmark/releases/tag/frozen-raw-evidence-v1"

def req(v,msg):
    if not v:
        raise SystemExit("NMI_P8H2_VALIDATION_FAILED: "+msg)

m=M.read_text(encoding="utf-8")
meta=json.loads(META.read_text(encoding="utf-8"))
contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
release=json.loads(RELEASE_MANIFEST.read_text(encoding="utf-8"))
sums=[x for x in SUMS.read_text(encoding="utf-8").splitlines() if x.strip()]

req(REPO in m, "public repository URL missing from manuscript")
req(RAW in m, "frozen raw release URL missing from manuscript")
req("24 historical evidence archives" in m, "raw release accounting missing")
req("completed frozen evidence is public" in m, "frozen/public distinction missing")
req("results/raw/" not in m, "runtime directory internals should not replace release surface")
req(meta["complete_if_applicable"]["repository_public_url"]==REPO, "metadata repository URL")
req(meta["complete_if_applicable"]["frozen_raw_release_url"]==RAW, "metadata frozen raw release URL")
req(meta["complete_if_applicable"]["frozen_raw_release_tag"]=="frozen-raw-evidence-v1", "metadata release tag")
req(meta["complete_if_applicable"]["archive_doi_or_immutable_identifier"] is None, "archive DOI must remain null")
req(release["artifact_count"]==24, "release manifest artifact count")
req(len(sums)==24, "SHA256 registry row count")
req(contract["status"]=="NMI_P8H_2_PUBLIC_FROZEN_RAW_COMPLETE_PORTAL_READY", "contract status")
req(contract["public_research_surface"]["frozen_raw_public_asset_count"]==24, "contract public raw count")
req(contract["public_research_surface"]["immutability_validation"]=="PASS", "immutability validation")
req(contract["final_submission_sources"]["manuscript"].endswith("NMI_Manuscript_v0.17_PUBLIC_RAW.md"), "final manuscript binding")
req(contract["final_export"]["workflow_run_id"]==35573108686, "final export run")
req(contract["final_export"]["visual_qa"]=="PASS_DOCX_AND_PDF", "final visual QA")
req(contract["scientific_freeze"]["raw_evidence_mutation"] is False, "raw evidence mutation boundary")
req(contract["portal_ready"] is True, "portal readiness")
req(manifest["status"]=="PUBLIC_FROZEN_RAW_COMPLETE_PORTAL_READY", "export manifest status")
req(manifest["frozen_raw_release"]["asset_count"]==24, "export manifest raw count")
req(manifest["frozen_raw_release"]["immutability_status"]=="PASS", "export manifest immutability")
req(manifest["visual_qa"]["docx"]=="PASS", "DOCX visual QA")
req(manifest["visual_qa"]["pdf"]=="PASS", "PDF visual QA")
req(manifest["portal_ready"] is True, "manifest portal readiness")

print("NMI_P8H2_VALIDATION=PASS")
print("FROZEN_RAW_PUBLIC_ASSETS=24")
print("FROZEN_RAW_IMMUTABILITY=PASS")
print("DOCX_VISUAL_QA=PASS")
print("PDF_VISUAL_QA=PASS")
print("PORTAL_READY=true")
print("NEXT_ACTION=NMI_PORTAL_UPLOAD")
