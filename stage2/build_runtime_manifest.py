"""Build the Stage-II runtime manifest from verified native-smoke reports."""
import argparse
import hashlib
import json
from pathlib import Path

from .freeze import BASE, artifact


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--smoke-root",required=True)
    p.add_argument("--code-commit",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    smoke=Path(a.smoke_root)
    subject=json.loads((BASE/"subject.json").read_text())
    targets=json.loads((BASE/"runtime_bindings.json").read_text())["probes"]
    planned=artifact()
    probes={}
    for pid,target in targets.items():
        if target.get("state")=="ENGINEERING_BLOCKED":
            probes[pid]={
                "engineering_status":"ENGINEERING_BLOCKED",
                "block_reason":target["block_reason"],
            }
            continue
        report=json.loads((smoke/pid/"smoke_report.json").read_text())
        if report["status"]!="NATIVE_SMOKE_PASS" or report["probe"]!=pid:
            raise SystemExit(f"{pid}: native smoke report invalid")
        if report["code_commit"]!=a.code_commit:
            raise SystemExit(f"{pid}: smoke code commit mismatch")
        probes[pid]={
            "engineering_status":"READY",
            "installed_version":report["installed_version"],
            "native_hook":report["native_hook"],
            "source_commit":report["source_commit"],
        }
        if report.get("protocol_version"):
            probes[pid]["protocol_version"]=report["protocol_version"]
        if report.get("implementation_sha256"):
            probes[pid]["implementation_sha256"]=report["implementation_sha256"]
        if target.get("sdk_commit"):
            probes[pid]["sdk_commit"]=target["sdk_commit"]
    manifest={
        "schema":"stage2-runtime-manifest-v1",
        "code_commit":a.code_commit,
        "matrix_sha256":hashlib.sha256((BASE/"matrix.json").read_bytes()).hexdigest(),
        "roles_sha256":planned["files_sha256"]["stage2/roles.json"],
        "subject_provider":subject["provider"],
        "subject_model":subject["model_alias"],
        "expected_model_version":subject["expected_model_version"],
        "subject_limits":subject["limits"],
        "probes":probes,
        "runnable_probes":sorted(pid for pid,b in probes.items() if b.get("engineering_status")=="READY"),
        "engineering_blocked_probes":sorted(pid for pid,b in probes.items() if b.get("engineering_status")=="ENGINEERING_BLOCKED"),
    }
    out=Path(a.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"runnable":manifest["runnable_probes"],"blocked":manifest["engineering_blocked_probes"]}))


if __name__=="__main__":
    main()
