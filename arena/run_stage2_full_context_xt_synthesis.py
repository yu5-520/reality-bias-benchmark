#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from adapters.deepseek_chat import chat_completion, extract_content

GROUPS=["G2","G3","G4","G5"]
MECH_STATUS={"RECURRENT","PARTIAL_RECURRENCE","SINGLE_REALIZATION","NOT_ESTABLISHED"}

def digest(raw:bytes)->str: return hashlib.sha256(raw).hexdigest()

def parse_json_text(text):
    text=text.strip()
    try: return json.loads(text)
    except Exception:
        marker=chr(96)*3
        for part in text.split(marker):
            p=part.strip()
            if p.startswith("json"): p=p[4:].strip()
            try: return json.loads(p)
            except Exception: pass
        raise

def add_usage(dst,src):
    for k,v in (src or {}).items():
        if isinstance(v,(int,float)) and not isinstance(v,bool):
            dst[k]=dst.get(k,0)+v

def cost_usd(usage,cfg):
    p=cfg["pricing_snapshot_usd_per_million_tokens"]["peak"]
    hit=float(usage.get("prompt_cache_hit_tokens",0) or 0)
    miss=float(usage.get("prompt_cache_miss_tokens",0) or 0)
    prompt=float(usage.get("prompt_tokens",0) or 0)
    out=float(usage.get("completion_tokens",0) or 0)
    if hit+miss<=0: miss=prompt
    return (hit*p["input_cache_hit"]+miss*p["input_cache_miss"]+out*p["output"])/1_000_000

def validate(obj,x,t,payload):
    if not isinstance(obj,dict) or obj.get("schema")!="stage2-full-context-xt-cohort-synthesis-v1":
        raise ValueError("cohort schema mismatch")
    if obj.get("x_id")!=x or obj.get("task_id")!=t: raise ValueError("cohort identity mismatch")
    included=payload["included_groups"]; excluded=payload["excluded_groups"]
    if obj.get("included_groups")!=included or obj.get("excluded_groups")!=excluded:
        raise ValueError("cohort membership mismatch")
    source={r["group_id"]:r for r in payload["cell_audits"]}
    seen=set()
    for row in obj.get("group_topologies") or []:
        g=row.get("group_id")
        if g not in source or g in seen: raise ValueError("bad group_topologies membership")
        seen.add(g)
        src=source[g]["audit"]["dynamic_topology"]
        if row.get("cell_audit_ref")!=f"{g}-{x}-{t}": raise ValueError("bad cell audit ref")
        if row.get("topology_class")!=src.get("topology_class"): raise ValueError("cohort changed topology class")
        if bool(row.get("closed_loop"))!=bool(src.get("closed_loop")): raise ValueError("cohort changed closure")
        if bool(row.get("self_reinforcing"))!=bool(src.get("self_reinforcing")): raise ValueError("cohort changed reinforcement")
        if set(row.get("dimensions_present") or [])!=set(src.get("dimensions_present") or []): raise ValueError("cohort changed dimensions")
    if seen!=set(included): raise ValueError("not all included groups represented")
    for m in obj.get("recurring_mechanism_families") or []:
        gs=m.get("groups") or []
        if any(g not in included for g in gs): raise ValueError("mechanism group outside cohort")
        if m.get("status") not in MECH_STATUS: raise ValueError("bad recurrence status")
        if m.get("status")=="RECURRENT" and len(set(gs))<2: raise ValueError("recurrent requires >=2 groups")
        if m.get("status")=="SINGLE_REALIZATION" and len(set(gs))!=1: raise ValueError("single realization mismatch")
    return obj

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cell-audit",required=True)
    ap.add_argument("--prompt",required=True)
    ap.add_argument("--model-config",required=True)
    ap.add_argument("--authorization",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    root=Path(a.cell_audit); out=Path(a.out)
    (out/"xt_cohorts").mkdir(parents=True,exist_ok=True)
    (out/"provider_raw_xt").mkdir(parents=True,exist_ok=True)
    prompt=Path(a.prompt).read_text()
    cfg=json.loads(Path(a.model_config).read_text())
    auth=json.loads(Path(a.authorization).read_text())
    cell_summary=json.loads((root/"cell_audit_summary.json").read_text())
    assert cell_summary["completed_cells"]==80 and not cell_summary["errors"]
    assert cell_summary["monitor_runtime_bundle_read"] is False
    assert cell_summary["blind_reference_labels_read"] is False

    by_xt={}
    for p in sorted((root/"cells").glob("G*-X*-T*.json")):
        row=json.loads(p.read_text())
        key=row["cell_id"]
        by_xt.setdefault(key,[]).append(row)
    if len(by_xt)!=21: raise SystemExit(f"expected 21 X-T cohorts, got {len(by_xt)}")

    usage=dict(cell_summary.get("aggregate_usage") or {})
    calls=int(cell_summary.get("provider_call_count") or 0)
    max_spend=float(auth["evaluator"]["max_spend_usd"])
    reserve=float((auth.get("validator_recovery") or {}).get("unaccounted_prevalidation_call_reserve_usd",0) or 0)
    effective_spend_ceiling=max_spend-reserve
    errors=[]; done=[]
    for xnum in range(1,8):
        for tnum in range(1,4):
            x=f"X{xnum}"; t=f"T{tnum}"; key=f"{x}-{t}"
            cells=sorted(by_xt[key],key=lambda r:r["group_id"])
            included=[r["group_id"] for r in cells]
            excluded=[g for g in GROUPS if g not in included]
            payload={
              "schema":"stage2-full-context-xt-cohort-input-v1",
              "x_id":x,"task_id":t,
              "included_groups":included,"excluded_groups":excluded,
              "stochastic_replication_rule":"Compare mechanism topology without requiring exact path/order replication; do not estimate prevalence.",
              "cell_audits":[{"group_id":r["group_id"],"full_id":r["full_id"],"audit":r["audit"]} for r in cells]
            }
            target=out/"xt_cohorts"/f"{key}.json"
            raw_target=out/"provider_raw_xt"/f"{key}.json"
            if target.is_file():
                obj=json.loads(target.read_text())["synthesis"]
                validate(obj,x,t,payload)
                rawmeta=json.loads(raw_target.read_text()) if raw_target.is_file() else {}
                add_usage(usage,rawmeta.get("usage") or {}); calls+=int(rawmeta.get("provider_call_count",0) or 0)
                done.append({"xt":key,"resumed":True})
                print(json.dumps({"xt":key,"resumed":True,"cost_usd":round(cost_usd(usage,cfg),6)},sort_keys=True),flush=True)
                continue
            try:
                if cost_usd(usage,cfg)>=effective_spend_ceiling: raise RuntimeError("effective tracked spend ceiling reached")
                response=chat_completion(
                    cfg,
                    [{"role":"system","content":prompt},{"role":"user","content":json.dumps(payload,ensure_ascii=False,separators=(",",":"))}],
                    evaluator=True,response_format_json=True
                )
                raw=extract_content(response)
                obj=validate(parse_json_text(raw),x,t,payload)
                n=1+int(response.get("_json_format_retry_count",0) or 0)
                calls+=n; add_usage(usage,response.get("usage") or {})
                if cost_usd(usage,cfg)>effective_spend_ceiling: raise RuntimeError("effective tracked spend ceiling exceeded")
                wrapper={
                  "schema":"stage2-full-context-xt-cohort-record-v1",
                  "x_id":x,"task_id":t,"included_groups":included,"excluded_groups":excluded,
                  "monitor_runtime_bundle_read":False,"blind_reference_labels_read":False,
                  "synthesis":obj,"provider":{"model":response.get("model"),"provider_call_count":n}
                }
                target.write_text(json.dumps(wrapper,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
                raw_target.write_text(json.dumps({
                  "model":response.get("model"),"response_id":response.get("id"),
                  "usage":response.get("usage") or {},"provider_call_count":n,
                  "json_format_retry_count":n-1,"raw_text":raw
                },ensure_ascii=False,indent=2,sort_keys=True)+"\n")
                done.append({"xt":key,"resumed":False})
                print(json.dumps({"xt":key,"cost_usd":round(cost_usd(usage,cfg),6)},sort_keys=True),flush=True)
            except Exception as exc:
                errors.append({"xt":key,"error":repr(exc)}); break
        if errors: break

    summary={
      "schema":"stage2-full-context-xt-synthesis-summary-v1",
      "requested_cohorts":21,"completed_cohorts":len(done),"errors":errors,
      "provider_call_count_total":calls,"aggregate_usage_total":usage,
      "estimated_cost_usd_peak_total":cost_usd(usage,cfg),"max_spend_usd":max_spend,
      "effective_tracked_spend_ceiling_usd":effective_spend_ceiling,"recovery_budget_reserve_usd":reserve,
      "monitor_runtime_bundle_read":False,"blind_reference_labels_read":False,
      "subject_calls":0,"subject_reruns":0,"repair_calls":0,"monitor_evaluation":False,
      "cell_audit_summary_sha256":digest((root/"cell_audit_summary.json").read_bytes()),
      "prompt_sha256":digest(prompt.encode()),"cohorts":done
    }
    (out/"xt_synthesis_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"completed_cohorts":len(done),"provider_calls_total":calls,
                      "estimated_cost_usd_peak_total":summary["estimated_cost_usd_peak_total"]},sort_keys=True))
    if errors or len(done)!=21: raise SystemExit("X-T synthesis incomplete; partial outputs preserved")

if __name__=="__main__": main()
