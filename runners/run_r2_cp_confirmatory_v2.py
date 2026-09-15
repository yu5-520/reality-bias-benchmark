#!/usr/bin/env python3
import argparse, concurrent.futures, hashlib, json, os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runners.run_r2_confirmatory_v2 import load_jsonl, generate_trace, expand_trace, TRACE_FAMILIES, HARD_CONDITIONS
from runners.run_r2_real import subject_messages, sha256_file

def skey(s): return f"{s['item_id']}|{s['trial']}|{s['family']}"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--benchmark',default='benchmark/r2_primary_mapping_items_v0.7_final_candidate.jsonl')
    ap.add_argument('--config',default='configs/models/deepseek_r2_confirmatory_v1.3.json')
    ap.add_argument('--repeats',type=int,default=3); ap.add_argument('--max-workers',type=int,default=6)
    ap.add_argument('--trace-retries',type=int,default=2); ap.add_argument('--out',required=True)
    a=ap.parse_args()
    cp=ROOT/a.config; condp=ROOT/'conditions/r2_conditions_v0.3.json'; bp=ROOT/a.benchmark
    config=json.loads(cp.read_text(encoding='utf-8')); conditions=json.loads(condp.read_text(encoding='utf-8'))['conditions']
    items={x['item_id']:x for x in load_jsonl(bp) if x['bias'] in ('C','P')}
    if len(items)!=8: raise SystemExit(f'Expected 8 frozen C/P items, found {len(items)}')
    for item in items.values():
        b=subject_messages(item,conditions['baseline'])
        for hard in HARD_CONDITIONS[1:]:
            if subject_messages(item,conditions[hard])!=b: raise SystemExit(f'Condition leakage: {hard} {item["item_id"]}')
    specs=[]
    for item in items.values():
        for trial in range(1,a.repeats+1):
            for family,(rep,targets) in TRACE_FAMILIES.items():
                specs.append({'item_id':item['item_id'],'trial':trial,'family':family,'representative_condition':rep,'target_conditions':targets})
    expanded=[{'item_id':s['item_id'],'trial':s['trial'],'condition':c,'family':s['family']} for s in specs for c in s['target_conditions']]
    hashes={'model_config_hash':sha256_file(cp),'conditions_hash':sha256_file(condp),'benchmark_hash':sha256_file(bp),'manifest_hash':hashlib.sha256(json.dumps(expanded,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); out.unlink(missing_ok=True)
    cache=out.with_name(out.stem+'_trace_cache.jsonl'); cache.unlink(missing_ok=True)
    traces={}; failures=[]
    pending=list(specs)
    for attempt in range(1,a.trace_retries+2):
        if not pending: break
        failures=[]
        workers=a.max_workers if attempt==1 else min(2,a.max_workers)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex, cache.open('a',encoding='utf-8') as cf:
            futs={ex.submit(generate_trace,s,config,conditions,items,hashes):s for s in pending}
            for n,f in enumerate(concurrent.futures.as_completed(futs),1):
                s=futs[f]
                try:
                    t=f.result(); traces[skey(s)]=t; cf.write(json.dumps(t,ensure_ascii=False)+'\n'); cf.flush()
                    print(f"[attempt {attempt}] OK {skey(s)}",flush=True)
                except Exception as e:
                    failures.append((s,repr(e))); print(f"[attempt {attempt}] ERROR {skey(s)}: {e}",file=sys.stderr,flush=True)
        pending=[s for s,_ in failures]
    if pending:
        ep=out.with_suffix(out.suffix+'.errors.json'); ep.write_text(json.dumps([{'spec':s,'error':e} for s,e in failures],ensure_ascii=False,indent=2),encoding='utf-8')
        raise SystemExit(f'{len(pending)} unique trace(s) failed after retry budget; cache preserved at {cache}')
    records=[]
    for s in specs: records.extend(expand_trace(traces[skey(s)],conditions))
    records.sort(key=lambda r:(r['bias'],r['item_id'],r['condition'],r['trial']))
    if len(records)!=168 or len({r['shared_trace_id'] for r in records})!=72: raise SystemExit('Unexpected C/P matrix cardinality')
    with out.open('w',encoding='utf-8') as f:
        for r in records: f.write(json.dumps(r,ensure_ascii=False)+'\n')
    print('Completed 72 unique C/P traces -> 168 condition cells',flush=True)
if __name__=='__main__': main()
