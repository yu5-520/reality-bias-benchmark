#!/usr/bin/env python3
from __future__ import annotations
import json, re, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"configs/nmi_submission_contract_v1.20.json"
MANIFEST=ROOT/"manifests/nmi_p9c_evidence_forward_final_export_2026-09-21_v1.json"
STATUS=ROOT/"docs/submission/nmi/NMI_P9C_Final_Status_v1.md"
MANUSCRIPT="docs/submission/nmi/NMI_Manuscript_v0.18_EVIDENCE_FORWARD_WORKING.md"
SUPPLEMENT="docs/submission/nmi/NMI_Supplementary_Information_v0.4_EVIDENCE_FORWARD_WORKING.md"
BUILDER="scripts/build_nmi_p9c_submission.py"
EXPORT_REF="be9ef05aedcd8bcad8caf7bea9058bc6925f6512"

def req(x,msg):
    if not x: raise SystemExit("NMI_P9C_FINAL_VALIDATION_FAILED: "+msg)

def blob(ref,path):
    return subprocess.check_output(["git","rev-parse",f"{ref}:{path}"],cwd=ROOT,text=True).strip()

def wc(text):
    return len(re.findall(r"\b[\w%+./'’-]+\b",text,flags=re.UNICODE))

def main():
    c=json.loads(CONTRACT.read_text())
    m=json.loads(MANIFEST.read_text())
    st=STATUS.read_text()
    ms=(ROOT/MANUSCRIPT).read_text()

    req(c["status"]=="NMI_P9C_EVIDENCE_FORWARD_PORTAL_READY","contract status")
    req(c["portal_ready"] is True,"portal ready")
    req(c["final_export"]["workflow_run_id"]==35586067844,"workflow run")
    req(c["final_export"]["artifact_id"]==10632576016,"artifact id")
    req(c["final_export"]["artifact_digest"]=="sha256:b02147e4ebf832d5d69c8b02902eae75e18e59b46f323317ad7996629dc16ab3","artifact digest")
    req(c["scientific_core"]["frozen_counts"]=={"C":3,"P":23,"R":18},"frozen counts")
    req(c["scientific_freeze"]["new_subject_runs"]==0,"subject rerun")
    req(c["scientific_freeze"]["provider_calls"]==0,"provider calls")
    req(c["scientific_freeze"]["evaluator_calls"]==0,"evaluator calls")
    req(c["scientific_freeze"]["raw_evidence_mutation"] is False,"raw mutation")
    req(c["scientific_freeze"]["frozen_count_change"] is False,"count mutation")

    req(m["status"]=="EVIDENCE_FORWARD_COMPLETE_PORTAL_READY","manifest status")
    req(m["visual_qa"]["status"]=="PASS","visual QA")
    req(m["visual_qa"]["docx_render_inspected_pages"]=={"manuscript":16,"supplement":10,"cover_letter":1},"docx page QA")
    req(m["visual_qa"]["pdf_rendered_pages"]=={"manuscript":16,"supplement":10,"cover_letter":1},"pdf page QA")
    req(m["frozen_results"]=={"C":3,"P":23,"R":18},"manifest counts")

    # Exported scientific sources must be unchanged since the successful export commit.
    for path in [MANUSCRIPT,SUPPLEMENT,BUILDER,"configs/nmi_p9c_figure_source_spec_v1.json"]:
        req(blob("HEAD",path)==blob(EXPORT_REF,path),f"export source changed after artifact build: {path}")

    abs_text=ms[ms.index("## Abstract")+len("## Abstract"):ms.index("\n\nMulti-agent AI systems are commonly")]
    main_text=ms[ms.index("\n\nMulti-agent AI systems are commonly"):ms.index("## Methods")]
    req(wc(abs_text)==145,f"abstract count {wc(abs_text)}")
    req(wc(main_text)==3389,f"main count {wc(main_text)}")
    req(len(re.findall(r"\*\*Figure [1-5] \|",ms))==5,"figure legends")
    req("NMI_P9C_EVIDENCE_FORWARD_PORTAL_READY" in st,"status token")

    print("NMI_P9C_FINAL_VALIDATION=PASS")
    print("PORTAL_READY=TRUE")
    print("WORKFLOW_RUN=35586067844")
    print("ARTIFACT_ID=10632576016")
    print("ABSTRACT_WORDS=145")
    print("MAIN_TEXT_WORDS=3389")
    print("DOCX_QA=16+10+1_PASS")
    print("PDF_QA=16+10+1_PASS")
    print("FROZEN_COUNTS=C3_P23_R18")
    print("NEXT_ACTION=NMI_PORTAL_UPLOAD")

if __name__=="__main__":
    main()
