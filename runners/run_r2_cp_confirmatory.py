#!/usr/bin/env python3
import argparse, concurrent.futures, hashlib, json, os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from runners.run_r2_confirmatory_v2 import (
    load_jsonl, generate_trace, expand_trace, TRACE_FAMILIES,
    HARD_CONDITIONS
)
from runners.run_r2_real import subject_messages, sha256_file


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--benchmark',default='benchmark/r2_primary_mapping_items_v0.7_final_candidate.jsonl')
    ap.add_argument('--repeats',type=int,default=3)
    ap.add_argument('--max-workers',type=int,default=6)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()

    config_path=ROOT/'configs/models/deepseek_r2_wave1.json'
    conditions_path=ROOT/'conditions/r2_conditions_v0.3.json'
    benchmark_path=ROOT/args.benchmark
    config=json.loads(config_path.read_text(encoding='utf-8'))
    conditions=json.loads(conditions_path.read_text(encoding='utf-8'))['conditions']
    all_items=load_jsonl(benchmark_path)
    items={x['item_id']:x for x in all_items if x['bias'] in ('C','P')}
    if len(items)!=8:
        raise SystemExit(f'Expected 8 frozen C/P items, found {len(items)}')

    for item in items.values():
        baseline_messages=subject_messages(item,conditions['baseline'])
        for hard in HARD_CONDITIONS[1:]:
            if subject_messages(item,conditions[hard])!=baseline_messages:
                raise SystemExit(f'Condition leakage: {hard} differs from baseline for {item["item_id"]}')

    specs=[]
    for item in items.values():
        for trial in range(1,args.repeats+1):
            for family,(representative,targets) in TRACE_FAMILIES.items():
                specs.append({
                    'item_id':item['item_id'],
                    'trial':trial,
                    'family':family,
                    'representative_condition':representative,
                    'target_conditions':targets,
                })
    expanded_manifest=[
        {'item_id':s['item_id'],'trial':s['trial'],'condition':c,'family':s['family']}
        for s in specs for c in s['target_conditions']
    ]
    hashes={
        'model_config_hash':sha256_file(config_path),
        'conditions_hash':sha256_file(conditions_path),
        'benchmark_hash':sha256_file(benchmark_path),
        'manifest_hash':hashlib.sha256(json.dumps(expanded_manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
    }

    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);out.unlink(missing_ok=True)
    errors=[];traces=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs={ex.submit(generate_trace,spec,config,conditions,items,hashes):spec for spec in specs}
        for n,fut in enumerate(concurrent.futures.as_completed(futs),1):
            spec=futs[fut]
            try:
                trace=fut.result();traces.append(trace)
                print(f"[{n}/{len(specs)} traces] OK {spec['item_id']} {spec['family']} t{spec['trial']}",flush=True)
            except Exception as e:
                errors.append({'spec':spec,'error':repr(e)})
                print(f"[{n}/{len(specs)} traces] ERROR {spec}: {e}",file=sys.stderr,flush=True)
    if errors:
        ep=out.with_suffix(out.suffix+'.errors.json')
        ep.write_text(json.dumps(errors,ensure_ascii=False,indent=2),encoding='utf-8')
        raise SystemExit(f'{len(errors)} unique trace(s) failed')

    records=[]
    for trace in traces: records.extend(expand_trace(trace,conditions))
    records.sort(key=lambda r:(r['bias'],r['item_id'],r['condition'],r['trial']))
    expected_cells=8*args.repeats*7
    expected_traces=8*args.repeats*3
    if len(records)!=expected_cells:
        raise SystemExit(f'Expected {expected_cells} C/P condition cells, got {len(records)}')
    if len({r['shared_trace_id'] for r in records})!=expected_traces:
        raise SystemExit(f'Expected {expected_traces} unique traces')
    with out.open('w',encoding='utf-8') as f:
        for r in records:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    print(f'Completed {expected_traces} unique C/P API traces -> {expected_cells} condition cells',flush=True)

if __name__=='__main__':main()
