#!/usr/bin/env python3
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M = ROOT / "docs/submission/nmi/NMI_Manuscript_v0.14.md"
COVER = ROOT / "docs/submission/nmi/NMI_Cover_Letter_v0.2.md"
SUPP = ROOT / "docs/submission/nmi/NMI_Supplementary_Information_v0.2.md"
CHECK = ROOT / "docs/submission/nmi/NMI_P7_Editorial_Format_Checklist_v1.md"
MANUAL = ROOT / "docs/submission/nmi/NMI_P7_Manual_Submission_Fields_v1.md"
CONTRACT = ROOT / "configs/nmi_submission_contract_v1.15.json"

def req(v, msg):
    if not v:
        raise SystemExit("NMI_P7_VALIDATION_FAILED: " + msg)

def wc(x: str) -> int:
    x = re.sub(r"\[[^\]]+\]", " ", x)
    return len(re.findall(r"[A-Za-z0-9À-ɏ'-]+", x))

m = M.read_text(encoding="utf-8")
cover = COVER.read_text(encoding="utf-8")
supp = SUPP.read_text(encoding="utf-8")
check = CHECK.read_text(encoding="utf-8")
manual = MANUAL.read_text(encoding="utf-8")
contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

req(m.startswith("# Process reality in multi-agent AI systems"), "title")
for forbidden in [
    "Manuscript status:",
    "Target:",
    "Citation status:",
    "Figure status:",
    "Reproducibility status:",
]:
    req(forbidden not in m, f"internal metadata remains: {forbidden}")
req("[L" not in m, "provisional citation key remains")
req("## Introduction" not in m, "Introduction heading must be absent")

abs_start = m.index("## Abstract") + len("## Abstract")
intro_start = m.index("\nMulti-agent AI systems are increasingly", abs_start)
results = m.index("## Results")
discussion = m.index("## Discussion")
methods = m.index("## Methods")
data = m.index("## Data availability")
code = m.index("## Code availability")
refs_start = m.index("## References")
fig_start = m.index("## Figure legends")

req(abs_start < intro_start < results < discussion < methods < data < code < refs_start < fig_start, "section order")

abstract = m[abs_start:intro_start]
main = m[intro_start:methods]
req(wc(abstract) == 147, f"abstract words {wc(abstract)}")
req(wc(abstract) <= 150, "abstract exceeds 150")
req(not re.search(r"\[\d", abstract), "abstract contains numbered citation")
req(wc(main) == 2942, f"main words {wc(main)}")
req(wc(main) <= 3500, "main text exceeds 3500")

results_text = m[results:discussion]
discussion_text = m[discussion:methods]
methods_text = m[methods:data]
req(len(re.findall(r"(?m)^### ", results_text)) >= 5, "Results topical subheadings")
req(not re.search(r"(?m)^### ", discussion_text), "Discussion must not contain subheadings")
req(len(re.findall(r"(?m)^### ", methods_text)) >= 5, "Methods topical subheadings")

refs = re.findall(r"(?m)^\d+\. ", m[refs_start:fig_start])
req(len(refs) == 12, f"references {len(refs)}")
legends = re.findall(r"(?m)^\*\*Figure [1-5] \|", m[fig_start:])
req(len(legends) == 5, f"figure legends {len(legends)}")
for i in range(1, 6):
    req(re.search(rf"Fig\. {i}(?:[a-z])?", main), f"missing Fig. {i} callout")
req(len(legends) <= 6, "display item limit")

req("## Data availability" in m, "Data availability")
req("## Code availability" in m, "Code availability")
req("### AI systems and human responsibility" in methods_text, "LLM-use disclosure")
req("Corresponding author name" in cover, "manual signature placeholder")
req("Supplementary Note 8" in supp, "supplement assembled")
req("Combined semantic-audit inventory" in supp and "**150**" in supp, "supplement evidence geometry")
req("10 / 13" in supp and "23.0769%" in supp, "structural calibration")
req("29" in supp and "25 persistence outcomes" in supp, "R5 accounting")
req("wave-4-cf726639de1d" in supp, "R7 canonical cases")
req("MANUAL METADATA REQUIRED BEFORE PORTAL SUBMISSION" in manual, "manual metadata guard")
req("PENDING actual archive creation" in check, "archive ID guard")

req(contract["status"] == "NMI_P7_COMPLETE_HANDOFF_TO_P8", "contract status")
req(contract["p7_completion"]["portal_ready"] is False, "portal-ready must remain false")
req(contract["scientific_freeze"]["new_subject_runs"] == 0, "new subject runs")
req(contract["scientific_freeze"]["provider_calls"] == 0, "provider calls")
req(contract["scientific_freeze"]["evaluator_calls"] == 0, "evaluator calls")
req(contract["scientific_freeze"]["new_semantic_adjudication"] is False, "semantic adjudication")
req(contract["next_gate"] == "NMI_P8_PRE_SUBMISSION_REVALIDATION_AND_EXPORT", "P8 handoff")

print("NMI_P7_VALIDATION=PASS")
print("ABSTRACT_WORDS=147")
print("MAIN_TEXT_BEFORE_METHODS=2942")
print("REFERENCES=12")
print("MAIN_FIGURES=5")
print("SUPPLEMENT=ASSEMBLED_V0.2")
print("PORTAL_READY=false")
print("NEXT_GATE=NMI_P8_PRE_SUBMISSION_REVALIDATION_AND_EXPORT")
