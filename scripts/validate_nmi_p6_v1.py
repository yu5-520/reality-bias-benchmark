#!/usr/bin/env python3
from __future__ import annotations
import gzip
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LEGACY = ROOT / "results/r8_trajectory_first_second_audit_v0_1/trajectory_second_audit_records.jsonl.gz"
RECOVERED = ROOT / "results/r8_trajectory_first_second_audit_recovered_v0_2/trajectory_second_audit_records.jsonl.gz"
ORIGINAL_MANIFEST = ROOT / "manifests/r8_trajectory_first_second_audit_repository_freeze_2026-09-20_v0_2.json"
CONTRACT = ROOT / "configs/nmi_submission_contract_v1.14.json"
LOCATORS = ROOT / "configs/nmi_release_locator_registry_v1.json"
MANUSCRIPT = ROOT / "docs/submission/nmi/NMI_Manuscript_v0.13.md"

def req(v, msg):
    if not v:
        raise SystemExit("NMI_P6_VALIDATION_FAILED: " + msg)

def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def git_blob_sha(b: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()

legacy = LEGACY.read_bytes()
req(len(legacy) == 14999, f"legacy size {len(legacy)}")
req(sha256(legacy) == "c047ae222f6bd4a58e57c109d9c573b0180e0fa3ea5c48ad4f49857098deb508", "legacy sha changed")
req(git_blob_sha(legacy) == "2f0b3690c19394425221e0c4a6f75d79ac34464e", "legacy git blob changed")
try:
    gzip.decompress(legacy)
except Exception:
    pass
else:
    req(False, "historical malformed gzip unexpectedly changed/readable")

raw = RECOVERED.read_bytes()
req(len(raw) == 90834, f"recovered size {len(raw)}")
req(sha256(raw) == "d8e51328f23ff6619fef5dce37f5768de319d16c3be0e7b478d27c7b614d9957", "recovered compressed sha")
req(git_blob_sha(raw) == "bdab2569753a7734c84ce4f203551cbbbafa566c", "recovered git blob")
plain = gzip.decompress(raw)
req(len(plain) == 629892, f"uncompressed size {len(plain)}")
req(sha256(plain) == "f4b1ee053d47fb3fe5b681831acd37469549af0f741660b81e28fb0df54f3e61", "uncompressed sha")
records = sum(1 for line in plain.splitlines() if line.strip())
req(records == 141, f"record count {records}")

om = json.loads(ORIGINAL_MANIFEST.read_text(encoding="utf-8"))
declared = om["outputs"]["full_records_gzip"]
req(declared["compressed_sha256"] == sha256(raw), "recovered != original frozen compressed hash")
req(declared["uncompressed_sha256"] == sha256(plain), "recovered != original frozen uncompressed hash")
req(declared["uncompressed_size_bytes"] == len(plain), "recovered != original frozen uncompressed size")

c = json.loads(CONTRACT.read_text(encoding="utf-8"))
req(c["status"] == "NMI_P6_COMPLETE_HANDOFF_TO_P7", "contract status")
req(c["p6_completion"]["legacy_defective_object_retained"] is True, "legacy retained")
req(c["p6_completion"]["legacy_overwritten"] is False, "legacy overwrite guard")
req(c["p6_completion"]["canonical_recovered_git_blob"] == git_blob_sha(raw), "contract recovered blob")
req(c["next_gate"] == "NMI_P7_FINAL_EDITORIAL_AND_FORMAT_COMPLIANCE", "P7 handoff")

loc = json.loads(LOCATORS.read_text(encoding="utf-8"))
req(loc["canonical_r8_records"]["canonical_git_blob"] == git_blob_sha(raw), "locator recovered blob")
req(loc["boundaries"]["combined_150_is_prevalence_denominator"] is False, "denominator guard")
req(loc["boundaries"]["cross_model_robustness_established"] is False, "cross-model guard")

m = MANUSCRIPT.read_text(encoding="utf-8")
req("NMI-P6 v0.13 / reproducibility and release freeze" in m, "manuscript status")
req("## Data availability" in m, "data availability")
req("## Code availability" in m, "code availability")
req("public immutable archival release identifier will be added when that release is created" in m, "no invented archive id")

def wc(x: str) -> int:
    x = re.sub(r"\[[^\]]+\]", " ", x)
    x = re.sub(r"`[^`]*`", " ", x)
    return len(re.findall(r"[A-Za-z0-9À-ɏ'-]+", x))

a0 = m.index("## Abstract") + len("## Abstract")
sep = m.index("---", a0)
mm = m.index("## Methods", sep)
aw = wc(m[a0:sep])
mw = wc(m[sep+3:mm])
req(aw == 147, f"abstract {aw}")
req(mw == 2930, f"main text {mw}")

for p in [
    ROOT / ".p6_staging/r8_recovered.b64.part00",
    ROOT / ".p6_staging/r8_recovered.b64.part01",
    ROOT / ".p6_staging/r8_recovered.b64.micro00",
]:
    req(not p.exists(), f"staging file remains: {p}")

print("NMI_P6_VALIDATION=PASS")
print("LEGACY_DEFECT_RETAINED=true")
print("RECOVERED_GZIP_BYTES=90834")
print("RECOVERED_RECORDS=141")
print("RECOVERED_COMPRESSED_SHA256=d8e51328f23ff6619fef5dce37f5768de319d16c3be0e7b478d27c7b614d9957")
print("RECOVERED_UNCOMPRESSED_SHA256=f4b1ee053d47fb3fe5b681831acd37469549af0f741660b81e28fb0df54f3e61")
print("NEXT_GATE=NMI_P7_FINAL_EDITORIAL_AND_FORMAT_COMPLIANCE")
