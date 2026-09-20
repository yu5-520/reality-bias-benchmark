#!/usr/bin/env python3
import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def req(v,m):
    if not v: raise SystemExit("NMI_P4_FA03_VALIDATION_FAILED: "+m)
m=(ROOT/"docs/submission/nmi/NMI_Manuscript_v0.8.md").read_text(encoding="utf-8")
c=json.loads((ROOT/"configs/nmi_submission_contract_v1.9.json").read_text(encoding="utf-8"))
fa=c["p4_foundational_attacks"]["FA03_recursive_monitor_repair_governance"]
req("recursive governance problem" in m,"recursive problem")
req("detection != authority" in m,"detection guard")
req("monitor read access != repair write access" in m,"read/write separation")
req(fa["control_layer_risk_is_real"] is True,"risk")
req(fa["detection_equals_authority"] is False,"detection")
req(fa["monitor_read_access_equals_repair_write_access"] is False,"readwrite")
req(fa["semantic_verdict_equals_repair_authorization"] is False,"verdictauth")
req(fa["repair_authorization_equals_global_write_authority"] is False,"globalwrite")
req(fa["reentry_equals_renewed_authority"] is False,"reentry")
req(fa["repair_authority_gate_empirically_validated"] is False,"outlook")
a0=m.index("## Abstract")+len("## Abstract"); sep=m.index("---",a0); mm=m.index("## Methods",sep)
def wc(x):
    x=re.sub(r"\[[^\]]+\]|\`[^\`]*\`"," ",x)
    return len(re.findall(r"[A-Za-z0-9À-ɏ'-]+",x))
aw=wc(m[a0:sep]); mw=wc(m[sep+3:mm])
req(aw==147,f"abstract {aw}"); req(3290<=mw<3500,f"main {mw}")
print("NMI_P4_FA03_VALIDATION=PASS")
print(f"ABSTRACT_WORDS={aw}")
print(f"MAIN_TEXT_BEFORE_METHODS={mw}")
print("DETECTION_EQUALS_AUTHORITY=false")
print("MONITOR_READ_EQUALS_REPAIR_WRITE=false")
print("REPAIR_GLOBAL_WRITE_AUTHORITY=false")
print("REENTRY_EQUALS_RENEWED_AUTHORITY=false")
print("REPAIR_AUTHORITY_GATE_EMPIRICALLY_VALIDATED=false")
