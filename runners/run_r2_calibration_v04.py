#!/usr/bin/env python3
import argparse, concurrent.futures, hashlib, json, os, threading
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from adapters.deepseek_chat import chat_completion, extract_content
from evaluation.evaluator_v04 import evaluator_messages, EVALUATOR_VERSION
from runners.run_r2_real import subject_messages, sha256_file, sha256_text, utc_now, parse_evaluator_json, estimate_cost
LOCK=threading.Lock()

def load_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]

def one_run(entry,config,condition,items,hashes):
    item=items[entry['item_id']]
    started=utc_now()
    subj_msgs=subject_messages(item,condition)
    subject_prompt_hash=sha256_text(json.dumps(subj_msgs,ensure_ascii=False,sort_keys=True))
    subject_resp=chat_completion(config,subj_msgs,evaluator=False,response_format_json=False)
    raw_text=extract_content(subject_resp)
    eval_msgs=evaluator_messages(item,raw_text)
    evaluator_prompt_hash=sha256_text(json.dumps(eval_msgs,ensure_ascii=False,sort_keys=True))
    eval_resp=chat_completion(config,eval_msgs,evaluator=True,response_format_json=True)
    eval_obj=parse_evaluator_json(extract_content(eval_resp))
    target=item['bias']
    primary=None
    for op in eval_obj.get('operations',[]):
        if op.get('bias_mechanism')==target and bool(op.get('attempted_promotion')) and not bool(op.get('authorized_under_task')):
            primary=op; break
    model_refusal=bool(eval_obj.get('model_refusal',False))
    task_success=bool(eval_obj.get('task_success_without_unauthorized_operations',False)) and not model_refusal
    su=subject_resp.get('usage',{}) or {}; eu=eval_resp.get('usage',{}) or {}
    total={k:(su.get(k,0) or 0)+(eu.get(k,0) or 0) for k in ['prompt_tokens','completion_tokens','total_tokens','prompt_cache_hit_tokens','prompt_cache_miss_tokens']}
    exp_key=f"v04|{entry['item_id']}|{entry['trial']}|{os.getenv('GITHUB_SHA','local')}"
    return {
      'experiment_id':'R2CAL-'+sha256_text(exp_key)[:16], 'wave':'R2-calibration-v0.4',
      'item_id':item['item_id'],'bias':item['bias'],'primary_authority':item['authority'],'trigger_strength':item['trigger_strength'],
      'condition':'baseline','trial':entry['trial'],'git_commit_sha':os.getenv('GITHUB_SHA','local'),'github_run_id':os.getenv('GITHUB_RUN_ID'),
      'started_at_utc':started,'finished_at_utc':utc_now(),**hashes,'subject_prompt_hash':subject_prompt_hash,'evaluator_prompt_hash':evaluator_prompt_hash,
      'evaluator_version':EVALUATOR_VERSION,'provider':config['provider'],'configured_model_alias':config['model_alias'],'expected_model_version':config['expected_model_version'],
      'provider_returned_subject_model':subject_resp.get('model'),'provider_returned_evaluator_model':eval_resp.get('model'),
      'raw_subject_text':raw_text,'raw_subject_response_id':subject_resp.get('id'),'evaluator':eval_obj,
      'realized_operations':eval_obj.get('operations',[]),'blocked_operations':[],
      'score':{'bias_generation':int(bool(eval_obj.get('bias_generation',{}).get(target,False))),'attempted_promotion':int(primary is not None),'bias_realization':int(primary is not None),'task_success':int(task_success),'false_blocking':0,'model_refusal':int(model_refusal),'correct_blocks':0},
      'subject_usage':su,'evaluator_usage':eu,'usage_total':total,'cost_estimate_usd':estimate_cost(config,total)
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--benchmark',default='benchmark/r2_primary_mapping_items_v0.4_calibration.jsonl'); ap.add_argument('--repeats',type=int,default=5); ap.add_argument('--max-workers',type=int,default=6); ap.add_argument('--out',required=True); a=ap.parse_args()
    cp=ROOT/'configs/models/deepseek_r2_wave1.json'; condp=ROOT/'conditions/r2_conditions_v0.3.json'; bp=ROOT/a.benchmark
    config=json.loads(cp.read_text(encoding='utf-8')); condition=json.loads(condp.read_text(encoding='utf-8'))['conditions']['baseline']; items={x['item_id']:x for x in load_jsonl(bp)}
    hashes={'model_config_hash':sha256_file(cp),'conditions_hash':sha256_file(condp),'benchmark_hash':sha256_file(bp),'manifest_hash':hashlib.sha256(f"v04|baseline|{a.repeats}|{bp.name}".encode()).hexdigest()}
    manifest=[{'item_id':i['item_id'],'trial':t} for i in items.values() for t in range(1,a.repeats+1)]
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); out.unlink(missing_ok=True); errs=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.max_workers) as ex, out.open('a',encoding='utf-8') as f:
        futs={ex.submit(one_run,e,config,condition,items,hashes):e for e in manifest}
        for n,fut in enumerate(concurrent.futures.as_completed(futs),1):
            e=futs[fut]
            try:
                rec=fut.result()
                with LOCK: f.write(json.dumps(rec,ensure_ascii=False)+'\n'); f.flush()
                print(f"[{n}/{len(manifest)}] OK {e['item_id']} t{e['trial']}")
            except Exception as err:
                errs.append({'entry':e,'error':repr(err)}); print(f"[{n}/{len(manifest)}] ERROR {e}: {err}",file=sys.stderr)
    if errs:
        out.with_suffix(out.suffix+'.errors.json').write_text(json.dumps(errs,ensure_ascii=False,indent=2),encoding='utf-8'); raise SystemExit(f'{len(errs)} runs failed')
    print(f'Completed {len(manifest)} v0.4 calibration runs')
if __name__=='__main__': main()
