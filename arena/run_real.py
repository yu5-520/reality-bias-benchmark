#!/usr/bin/env python3
import argparse, concurrent.futures, json, os, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from arena.engine import run_arena_once
from arena.io_utils import load_json, load_jsonl, write_jsonl
from arena.providers import DeepSeekArenaProvider


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--manifest',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--max-workers',type=int,default=4)
    ap.add_argument('--execute-real-api',action='store_true')
    a=ap.parse_args()
    if not a.execute_real_api:
        raise SystemExit('Refusing to call provider. Add --execute-real-api only for the final real-model step.')
    if not os.environ.get('DEEPSEEK_API_KEY'):
        raise SystemExit('DEEPSEEK_API_KEY is not set')
    arena_cfg=load_json(ROOT/'arena/config/arena_v0.1.json')
    model_cfg=load_json(ROOT/'arena/config/model_deepseek_v0.1.json')
    manifest=load_jsonl(a.manifest)
    provider=DeepSeekArenaProvider(model_cfg)

    def one(entry):
        domain=load_json(ROOT/f"arena/domains/{entry['domain_id']}.json")
        trace=run_arena_once(domain,arena_cfg,provider,entry['run_id'],entry.get('logical_seed'))
        trace['trial']=entry['trial']
        trace['domain_hash']=entry['domain_hash']
        trace['arena_config_hash']=entry['arena_config_hash']
        trace['model_config_hash']=entry['model_config_hash']
        return trace

    rows=[]; errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.max_workers) as ex:
        futs={ex.submit(one,e):e for e in manifest}
        for i,fut in enumerate(concurrent.futures.as_completed(futs),1):
            entry=futs[fut]
            try:
                row=fut.result(); rows.append(row)
                print(f"[{i}/{len(manifest)}] OK {entry['run_id']} agents={row['activated_agent_count']} turns={row['turns']}",flush=True)
            except Exception as err:
                errors.append({'entry':entry,'error':repr(err)})
                print(f"[{i}/{len(manifest)}] ERROR {entry['run_id']}: {err}",file=sys.stderr,flush=True)
    write_jsonl(a.out,sorted(rows,key=lambda x:x['run_id']))
    if errors:
        Path(a.out+'.errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),encoding='utf-8')
        raise SystemExit(f'{len(errors)} arena runs failed')
    print(f'completed {len(rows)} real arena runs -> {a.out}')


if __name__=='__main__': main()
