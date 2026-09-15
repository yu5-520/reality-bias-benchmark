#!/usr/bin/env python3
import argparse, concurrent.futures, json, os, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from adapters.deepseek_chat import chat_completion, extract_content
from arena.evaluation import build_evaluator_messages, validate_evaluation, EVALUATOR_VERSION
from arena.io_utils import load_json, load_jsonl, write_jsonl


def parse_json(text):
    raw=text.strip()
    try: return json.loads(raw)
    except json.JSONDecodeError:
        if '```' in raw:
            for p in raw.split('```'):
                p=p.strip()
                if p.startswith('json'): p=p[4:].strip()
                try: return json.loads(p)
                except Exception: pass
        raise


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--max-workers',type=int,default=4)
    ap.add_argument('--execute-real-api',action='store_true')
    a=ap.parse_args()
    if not a.execute_real_api:
        raise SystemExit('Refusing evaluator API calls. Add --execute-real-api only for the final real-model step.')
    if not os.environ.get('DEEPSEEK_API_KEY'):
        raise SystemExit('DEEPSEEK_API_KEY is not set')
    arena_cfg=load_json(ROOT/'arena/config/arena_v0.1.json')
    model_cfg=load_json(ROOT/'arena/config/model_deepseek_v0.1.json')
    traces=load_jsonl(a.input)

    def one(trace):
        domain=load_json(ROOT/f"arena/domains/{trace['domain_id']}.json")
        msgs=build_evaluator_messages(domain,arena_cfg,trace)
        resp=chat_completion(model_cfg,msgs,evaluator=True,response_format_json=True)
        obj=parse_json(extract_content(resp))
        validate_evaluation(trace,obj)
        return {
            'run_id':trace['run_id'],
            'domain_id':trace['domain_id'],
            'evaluator_version':EVALUATOR_VERSION,
            'provider_model':resp.get('model'),
            'usage':resp.get('usage') or {},
            'evaluation':obj,
        }

    rows=[]; errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.max_workers) as ex:
        futs={ex.submit(one,t):t for t in traces}
        for i,fut in enumerate(concurrent.futures.as_completed(futs),1):
            t=futs[fut]
            try:
                rows.append(fut.result()); print(f"[{i}/{len(traces)}] CODED {t['run_id']}",flush=True)
            except Exception as err:
                errors.append({'run_id':t['run_id'],'error':repr(err)})
                print(f"[{i}/{len(traces)}] ERROR {t['run_id']}: {err}",file=sys.stderr,flush=True)
    write_jsonl(a.out,sorted(rows,key=lambda x:x['run_id']))
    if errors:
        Path(a.out+'.errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),encoding='utf-8')
        raise SystemExit(f'{len(errors)} evaluator runs failed')
    print(f'coded {len(rows)} arena traces -> {a.out}')


if __name__=='__main__': main()
