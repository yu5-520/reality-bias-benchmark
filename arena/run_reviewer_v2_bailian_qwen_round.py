#!/usr/bin/env python3
"""Independent Reviewer-v2 replication through Alibaba Cloud Bailian/Qwen.

This runner intentionally reuses the frozen Reviewer-v2 prompts, packet schemas,
normalization and deterministic synthesis contract. It changes only provider/model
transport and pricing. It never reruns subject generation.
"""
import argparse
import datetime as dt
import json
import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters.bailian_openai_chat import chat_completion, extract_content
from arena.io_utils import load_json, load_jsonl, sha256_file
from arena.reviewer_v2_contract import normalize, parse_json, build_ref_index, get_expansion_record, stable_hash
from arena.evaluate_reviewer_v2_deepseek import PROMPTS, RECORD_VERSION, target_ref

VERSION = 'R234-REVIEWER-V2-BAILIAN-QWEN-ROUND-v0.1'
LAYERS = ('R2', 'R3', 'R4')

class FatalReviewStop(RuntimeError): pass

def append_jsonl(path, row):
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')

def add_usage(dst, usage):
    for k in ('prompt_tokens','completion_tokens','total_tokens'):
        dst[k] = dst.get(k, 0) + int(usage.get(k) or 0)
    details = usage.get('completion_tokens_details') or {}
    dst['reasoning_tokens'] = dst.get('reasoning_tokens', 0) + int(details.get('reasoning_tokens') or 0)

def cost_cny(usage, cfg):
    p = cfg['pricing_snapshot_cny_per_million_tokens']
    return (usage.get('prompt_tokens',0) * p['input'] + usage.get('completion_tokens',0) * p['output_including_reasoning']) / 1_000_000

def make_record(layer, packet, final, cfg_hash, prompt_hash, response, usage, attempt, failures, expansion_ref, launch):
    row = {
      'review_record_version': RECORD_VERSION[layer], 'review_layer': layer,
      'review_record_id': f'RV2-QWEN-{uuid.uuid4()}', 'evidence_batch_hash': packet['evidence_batch_hash'],
      'packet_id': packet['packet_id'],
      'reviewer': {'id':'qwen38max-independent-reviewer-v2-round001','type':'model','provider':'alibaba_cloud_bailian_business_space','model':response.get('model'),'model_config_hash':cfg_hash,'prompt_hash':prompt_hash,'blind_to_prior_review':True,'blind_to_expected_mapping':True},
      'rationale': final['rationale'], 'confidence': final['confidence'], 'uncertainties': final['uncertainties'],
      'evidence_refs': final['evidence_refs'], 'context_expansion_refs':[expansion_ref] if expansion_ref else [],
      'context_expansion_used': bool(expansion_ref), 'created_at':dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00','Z'),
      'usage':usage, 'review_attempt_count':attempt, 'failed_review_attempts':failures,
      'provider_response_id':response.get('id'), 'adapter_version':VERSION,
      'authorization_ref':launch['authorization_ref'], 'launch_record_hash':stable_hash(launch), 'packet_hash':packet.get('packet_hash')}
    if layer == 'R2':
      row['target_ref']=target_ref(layer,packet); row['target_effect_scope']=(packet.get('target_candidate') or {}).get('effect_scope')
      for k in ('epistemic_transition','goal_relation','goal_focus_transition','local_retrospective_outcome','authorization_judgment'): row[k]=final[k]
    elif layer == 'R3':
      row['target_ref']=target_ref(layer,packet)
      for k in ('semantic_adoption','decision_effect','lineage_outcome','penetration_range_refs'): row[k]=final[k]
    else:
      row['window_ref']=target_ref(layer,packet)
      for k in ('correction','persistence','regeneration','regeneration_mechanisms','amplification','laundering','laundered_mechanisms','normalization','black_hole'): row[k]=final[k]
    row['review_record_hash']=stable_hash(row); return row

def main():
    ap=argparse.ArgumentParser()
    for x in ('launch-record','r2','r3','r4','traces','outdir'): ap.add_argument('--'+x, required=True)
    ap.add_argument('--model-config',default='arena/config/model_bailian_qwen38max_v0.1.json'); ap.add_argument('--execute-real-api',action='store_true'); args=ap.parse_args()
    if not args.execute_real_api: raise SystemExit('real independent replication locked')
    launch=load_json(args.launch_record); cfg_path=ROOT/args.model_config; cfg=load_json(cfg_path)
    if launch.get('status')!='AUTHORIZED' or launch.get('execute_real_api') is not True or not launch.get('authorization_ref'): raise SystemExit('immutable authorized launch record required')
    if launch.get('scientific_role')!='INDEPENDENT_REVIEWER_V2_REPLICATION': raise SystemExit('wrong scientific role')
    if launch.get('provider',{}).get('model_family')!='Qwen': raise SystemExit('wrong model family binding')
    if launch.get('blind_bundle_binding',{}).get('bundle_hash')!='fc46e673c0d21bff9e30ca97a197c3b9dd04c27bf69ba0f3e07849ee6d00638e': raise SystemExit('blind bundle hash mismatch')
    max_spend=launch.get('spend_policy',{}).get('launch_max_spend_cny'); ceiling=launch.get('spend_policy',{}).get('repository_level_absolute_ceiling_cny')
    if type(max_spend) not in (int,float) or not (0 < max_spend <= ceiling): raise SystemExit('valid CNY spend ceiling required')
    if sha256_file(cfg_path)!=launch.get('model_config_sha256'): raise SystemExit('model config hash mismatch')
    if not os.environ.get('BAI') or not os.environ.get('BAILIAN_BASE_URL') or not os.environ.get('BAILIAN_MODEL'): raise SystemExit('Bailian runtime binding missing')
    if os.environ['BAILIAN_MODEL']!='qwen3.8-max-0902': raise SystemExit('runtime model differs from frozen model')
    paths={'R2':Path(args.r2),'R3':Path(args.r3),'R4':Path(args.r4)}
    for layer in LAYERS:
      if sha256_file(paths[layer]) != launch['packet_hashes'][layer]: raise SystemExit(f'{layer} packet hash mismatch')
      if sha256_file(ROOT/PROMPTS[layer]) != launch['prompt_hashes'][layer]: raise SystemExit(f'{layer} prompt hash mismatch')
    packets={x:load_jsonl(paths[x]) for x in LAYERS}; requested=sum(map(len,packets.values()))
    if requested!=144: raise SystemExit(f'population must be 144, got {requested}')
    ref_index=build_ref_index(load_jsonl(args.traces)); prompts={x:(ROOT/PROMPTS[x]).read_text(encoding='utf-8') for x in LAYERS}
    out=Path(args.outdir); out.mkdir(parents=True,exist_ok=True); budget={'usage':{},'cost_cny':0.0,'provider_calls':0}; completed=0; errors=[]; counts={x:0 for x in LAYERS}
    try:
      for layer in LAYERS:
       for packet in packets[layer]:
        failures=[]; expansion_ref=None; total_usage={}; messages=[{'role':'system','content':prompts[layer]},{'role':'user','content':json.dumps(packet,ensure_ascii=False)}]
        final_response=None; final=None; final_attempt=0
        for attempt in range(1,4):
         try:
          while True:
           if budget['cost_cny']>=max_spend: raise FatalReviewStop('hard spend ceiling reached')
           response=chat_completion(messages,response_format_json=True,max_tokens=cfg['evaluator']['max_tokens'],temperature=cfg['evaluator']['temperature'])
           budget['provider_calls']+=1; usage=response.get('usage') or {}; add_usage(total_usage,usage); add_usage(budget['usage'],usage); budget['cost_cny']=cost_cny(budget['usage'],cfg)
           if budget['cost_cny']>max_spend: raise FatalReviewStop('hard spend ceiling exceeded')
           if response.get('model') not in cfg['expected_returned_models']: raise FatalReviewStop('unexpected returned model')
           raw=extract_content(response); parsed=normalize(layer,parse_json(raw))
           if parsed['review_status']=='REQUEST_EXPANSION':
            if expansion_ref is not None: raise FatalReviewStop('second expansion requested')
            expansion_ref=parsed['context_expansion_ref']; expansion=get_expansion_record(packet,ref_index,expansion_ref); messages += [{'role':'assistant','content':raw},{'role':'user','content':json.dumps({'bounded_frozen_expansion':expansion},ensure_ascii=False)}]; continue
           final_response=response; final=parsed; final_attempt=attempt; break
          if final is not None: break
         except FatalReviewStop: raise
         except Exception as e: failures.append({'attempt':attempt,'error':repr(e)})
        if final is None: raise RuntimeError(f'{layer} review failed after retries')
        row=make_record(layer,packet,final,sha256_file(cfg_path),sha256_file(ROOT/PROMPTS[layer]),final_response,total_usage,final_attempt,failures,expansion_ref,launch)
        append_jsonl(out/f'{layer.lower()}_review_records.jsonl',row); completed+=1; counts[layer]+=1
    except Exception as e:
      errors.append(repr(e)); status='STOPPED'
    else: status='COMPLETED'
    summary={'round_version':VERSION,'status':status,'scientific_role':launch['scientific_role'],'requested_unit_count':requested,'completed_unit_count':completed,'per_layer_completed':counts,'error_count':len(errors),'errors':errors,'aggregate_usage':budget['usage'],'estimated_cost_cny':budget['cost_cny'],'max_spend_cny':max_spend,'provider_calls':budget['provider_calls'],'subject_reruns_triggered':0}
    summary['output_hash']=stable_hash(summary); (out/'review_round_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True),encoding='utf-8')
    if status!='COMPLETED': raise SystemExit('independent Reviewer-v2 round stopped; partial evidence preserved')

if __name__=='__main__': main()
