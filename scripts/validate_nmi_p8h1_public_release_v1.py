#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
M=ROOT/"docs/submission/nmi/NMI_Manuscript_v0.16_PUBLIC.md"
META=ROOT/"configs/nmi_p8_portal_metadata_template_v1.json"
CONTRACT=ROOT/"configs/nmi_submission_contract_v1.18.json"
MANIFEST=ROOT/"manifests/nmi_p8h1_public_release_final_export_2026-09-21_v1.json"
STATUS=ROOT/"docs/submission/nmi/NMI_P8H_1_Final_Status_v1.md"

URL="https://github.com/yu5-520/reality-bias-benchmark"

def req(v,msg):
    if not v:
        raise SystemExit("NMI_P8H1_VALIDATION_FAILED: "+msg)

m=M.read_text(encoding="utf-8")
meta=json.loads(META.read_text(encoding="utf-8"))
contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
status=STATUS.read_text(encoding="utf-8")

req("## Data availability" in m, "Data availability missing")
req("## Code availability" in m, "Code availability missing")
req(m.count(URL) >= 2, "public repository URL not bound in Data/Code Availability")
for stale in [
    "submission repository remains private",
    "controlled access can be provided",
    "Editors and reviewers can be provided controlled access",
]:
    req(stale not in m, "stale private-repository language remains")
req("immutable archival DOI has not yet been assigned" in m, "DOI boundary missing")
req(meta["complete_if_applicable"]["repository_public_url"]==URL,"metadata public repository URL")
req(meta["complete_if_applicable"]["archive_doi_or_immutable_identifier"] is None,"archive DOI must remain null")
req(meta["repository_release_status"]=="PUBLIC_GITHUB_NO_IMMUTABLE_ARCHIVE_DOI_YET","metadata release status")
req(contract["status"]=="NMI_P8H_1_PUBLIC_RELEASE_SYNC_COMPLETE_PORTAL_READY","contract status")
req(contract["repository_release"]["visibility"]=="public","contract visibility")
req(contract["repository_release"]["url"]==URL,"contract public URL")
req(contract["repository_release"]["immutable_archive_identifier"] is None,"contract archive identifier")
req(contract["final_submission_sources"]["manuscript"].endswith("NMI_Manuscript_v0.16_PUBLIC.md"),"contract manuscript")
req(contract["portal_ready"] is True,"portal ready")
req(contract["scientific_freeze"]["new_subject_runs"]==0,"subject run boundary")
req(contract["scientific_freeze"]["new_semantic_adjudication"] is False,"semantic adjudication boundary")
req(manifest["status"]=="PUBLIC_RELEASE_SYNC_COMPLETE_PORTAL_READY","manifest status")
req(manifest["repository"]["visibility"]=="public","manifest visibility")
req(manifest["repository"]["url"]==URL,"manifest URL")
req(manifest["visual_qa"]["docx_render"]=="PASS","DOCX visual QA")
req(manifest["visual_qa"]["pdf_render"]=="PASS","PDF visual QA")
req("PUBLIC REPOSITORY SYNC COMPLETE / PORTAL READY" in status,"status wording")

print("NMI_P8H1_PUBLIC_RELEASE_VALIDATION=PASS")
print("REPOSITORY_VISIBILITY=public")
print("PUBLIC_REPOSITORY_URL="+URL)
print("IMMUTABLE_ARCHIVE_DOI=not_assigned")
print("DOCX_VISUAL_QA=PASS")
print("PDF_VISUAL_QA=PASS")
print("PORTAL_READY=true")
print("NEXT_ACTION=NMI_PORTAL_UPLOAD")
