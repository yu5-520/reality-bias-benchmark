#!/usr/bin/env python3
"""Independent Reviewer-v2 replication through Alibaba Cloud Bailian/Qwen.

Supports immutable packet-level continuation after a stopped run. Completed packet
records are reused byte-for-byte; subject generation is never rerun. Failed provider
attempts are now frozen with raw response/error evidence for diagnosis.
"""
import argparse, datetime as dt, json, os, shutil, sys, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from adapters.bailian_openai_chat import chat_completion, extract_content
from arena.io_utils import load_json, load_jsonl, sha256_file
from arena.reviewer_v2_contract import normalize, parse_json, build_ref_index, get_expansion_record, stable_hash
from arena.evaluate_reviewer_v2_deepseek import PROMPTS, RECORD_VERSION, target_ref
VERSION='R234-REVIEWER-V2-BAILIAN-QWEN-ROUND-v0.2'; LAYERS=('R2','R3','R4')
class FatalReviewStop(RuntimeError): pass

def append_jsonl(path,row):
 with path.open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+'\n')
def add_usage(dst,u):
 for k in ('prompt_tokens','completion_tokens','total_tokens'):dst[k]=dst.get(k,0)+int(u.get(k) or 0)
 dst['reasoning_tokens']=dst.get('reasoning_tokens',0)+int((u.get('completion_tokens_details') or {}).get('reasoning_tokens') or 0)
def cost_cny(u,cfg):
 p=cfg['pricing_snapshot_cny_per_million_tokens'];return (u.get('prompt_tokens',0)*p['input']+u.get('completion_tokens',0)*p['output_including_reasoning'])/1_000_000
def make_record(layer,packet,final,cfg_hash,prompt_hash,response,usage,attempt,failures,expansion_ref,launch):
 row={'review_record_version':RECORD_VERSION[layer],'review_layer':layer,'review_record_id':f'RV2-QWEN-{uuid.uuid4()}','evidence_batch_hash':packet['evidence_batch_hash'],'packet_id':packet['packet_id'],'reviewer':{'id':'qwen38max-independent-reviewer-v2-round001','type':'model','provider':'alibaba_cloud_bailian_business_space','model':response.get('model'),'model_config_hash':cfg_hash,'prompt_hash':prompt_hash,'blind_to_prior_review':True,'blind_to_expected_mapping':True},'rationale':final['rationale'],'confidence':final['confidence'],'uncertainties':final['uncertainties'],'evidence_refs':final['evidence_refs'],'context_expansion_refs':[expansion_ref] if expansion_ref else [],'context_expansion_used':bool(expansion_ref),'created_at':dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00','Z'),'usage':usage,'review_attempt_count':attempt,'failed_review_attempts':failures,'provider_response_id':response.get('id'),'adapter_version':VERSION,'authorization_ref':launch['authorization_ref'],'launch_record_hash':stable_hash(launch),'packet_hash':packet.get('packet_hash')}
 if layer=='R2':
  row['target_ref']=target_ref(layer,packet);row['target_effect_scope']=(packet.get('target_candidate') or {}).get('effect_scope')
  for k in ('epistemic_transition','goal_relation','goal_focus_transition','local_retrospective_outcome','authorization_judgment'):row[k]=final[k]
 elif layer=='R3':
  row['target_ref']=target_ref(layer,packet)
  for k in ('semantic_adoption','decision_effect','lineage_outcome','penetration_range_refs'):row[k]=final[k]
 else:
  row['window_ref']=target_ref(layer,packet)
  for k in ('correction','persistence','regeneration','regeneration_mechanisms','amplification','laundering','laundered_mechanisms','normalization','black_hole'):row[k]=final[k]
 row['review_record_hash']=stable_hash(row);return row

def main():
 ap=argparse.ArgumentParser()
 for x in ('launch-record','r2','r3','r4','traces','outdir'):ap.add_argument('--'+x,required=True)
 ap.add_argument('--model-config',default='arena/config/model_bailian_qwen38max_v0.1.json');ap.add_argument('--resume-from');ap.add_argument('--execute-real-api',action='store_true');a=ap.parse_args()
 if not a.execute_real_api:raise SystemExit('real independent replication locked')
 launch=load_json(a.launch_record);cfgp=ROOT/a.model_config;cfg=load_json(cfgp)
 if launch.get('status')!='AUTHORIZED' or launch.get('execute_real_api') is not True or not launch.get('authorization_ref'):raise SystemExit('immutable authorized launch record required')
 if launch.get('scientific_role')!='INDEPENDENT_REVIEWER_V2_REPLICATION' or launch.get('provider',{}).get('model_family')!='Qwen':raise SystemExit('wrong scientific binding')
 if launch.get('blind_bundle_binding',{}).get('bundle_hash')!='fc46e673c0d21bff9e30ca97a197c3b9dd04c27bf69ba0f3e07849ee6d00638e':raise SystemExit('blind bundle hash mismatch')
 maxsp=launch['spend_policy']['launch_max_spend_cny'];ceiling=launch['spend_policy']['repository_level_absolute_ceiling_cny']
 if not (0<maxsp<=ceiling):raise SystemExit('valid CNY spend ceiling required')
 if sha256_file(cfgp)!=launch['model_config_sha256']:raise SystemExit('model config hash mismatch')
 if not all(os.environ.get(x) for x in ('BAI','BAILIAN_BASE_URL','BAILIAN_MODEL')) or os.environ['BAILIAN_MODEL']!='qwen3.8-max-0902':raise SystemExit('Bailian runtime binding mismatch')
 paths={'R2':Path(a.r2),'R3':Path(a.r3),'R4':Path(a.r4)}
 for l in LAYERS:
  if sha256_file(paths[l])!=launch['packet_hashes'][l] or sha256_file(ROOT/PROMPTS[l])!=launch['prompt_hashes'][l]:raise SystemExit(f'{l} frozen binding mismatch')
 packets={x:load_jsonl(paths[x]) for x in LAYERS};requested=sum(map(len,packets.values()))
 if requested!=144:raise SystemExit(f'population must be 144, got {requested}')
 refidx=build_ref_index(load_jsonl(a.traces));prompts={x:(ROOT/PROMPTS[x]).read_text(encoding='utf-8') for x in LAYERS};out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
 budget={'usage':{},'cost_cny':0.0,'provider_calls':0};done=set();counts={x:0 for x in LAYERS};resumed=0
 if a.resume_from:
  src=Path(a.resume_from);s=load_json(src/'review_round_summary.json')
  if s.get('status')!='STOPPED':raise SystemExit('resume source must be frozen STOPPED run')
  if launch.get('continuation_of',{}).get('artifact_digest')!=launch.get('continuation_of',{}).get('expected_artifact_digest'):raise SystemExit('continuation artifact binding mismatch')
  budget={'usage':dict(s.get('aggregate_usage') or {}),'cost_cny':float(s.get('estimated_cost_cny') or 0),'provider_calls':int(s.get('provider_calls') or 0)}
  for l in LAYERS:
   sp=src/f'{l.lower()}_review_records.jsonl'
   if sp.exists():
    rows=load_jsonl(sp);counts[l]=len(rows);resumed+=len(rows);done.update(r['packet_id'] for r in rows);shutil.copyfile(sp,out/sp.name)
 errors=[];failedlog=out/'failed_attempts.jsonl'
 try:
  for l in LAYERS:
   for packet in packets[l]:
    if packet['packet_id'] in done:continue
    failures=[];exp=None;tu={};msgs=[{'role':'system','content':prompts[l]},{'role':'user','content':json.dumps(packet,ensure_ascii=False)}];finalr=final=None;fa=0
    for attempt in range(1,4):
     try:
      while True:
       if budget['cost_cny']>=maxsp:raise FatalReviewStop('hard spend ceiling reached')
       resp=chat_completion(msgs,response_format_json=True,max_tokens=cfg['evaluator']['max_tokens'],temperature=cfg['evaluator']['temperature']);budget['provider_calls']+=1;u=resp.get('usage') or {};add_usage(tu,u);add_usage(budget['usage'],u);budget['cost_cny']=cost_cny(budget['usage'],cfg)
       raw=extract_content(resp)
       if budget['cost_cny']>maxsp:raise FatalReviewStop('hard spend ceiling exceeded')
       if resp.get('model') not in cfg['expected_returned_models']:raise FatalReviewStop('unexpected returned model')
       parsed=normalize(l,parse_json(raw))
       if parsed['review_status']=='REQUEST_EXPANSION':
        if exp is not None:raise FatalReviewStop('second expansion requested')
        exp=parsed['context_expansion_ref'];e=get_expansion_record(packet,refidx,exp);msgs += [{'role':'assistant','content':raw},{'role':'user','content':json.dumps({'bounded_frozen_expansion':e},ensure_ascii=False)}];continue
       finalr=resp;final=parsed;fa=attempt;break
      if final is not None:break
     except FatalReviewStop:raise
     except Exception as e:
      f={'layer':l,'packet_id':packet['packet_id'],'attempt':attempt,'error':repr(e),'provider_response_id':locals().get('resp',{}).get('id') if isinstance(locals().get('resp'),dict) else None,'returned_model':locals().get('resp',{}).get('model') if isinstance(locals().get('resp'),dict) else None,'usage':locals().get('u',{}),'raw_response':locals().get('raw')};failures.append(f);append_jsonl(failedlog,f)
    if final is None:raise RuntimeError(f'{l} review failed after retries at packet {packet["packet_id"]}')
    append_jsonl(out/f'{l.lower()}_review_records.jsonl',make_record(l,packet,final,sha256_file(cfgp),sha256_file(ROOT/PROMPTS[l]),finalr,tu,fa,failures,exp,launch));done.add(packet['packet_id']);counts[l]+=1
 except Exception as e:errors.append(repr(e));status='STOPPED'
 else:status='COMPLETED'
 summary={'round_version':VERSION,'status':status,'scientific_role':launch['scientific_role'],'requested_unit_count':requested,'resumed_completed_unit_count':resumed,'completed_unit_count':sum(counts.values()),'per_layer_completed':counts,'error_count':len(errors),'errors':errors,'aggregate_usage':budget['usage'],'estimated_cost_cny':budget['cost_cny'],'max_spend_cny':maxsp,'provider_calls':budget['provider_calls'],'subject_reruns_triggered':0}
 summary['output_hash']=stable_hash(summary);(out/'review_round_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True),encoding='utf-8')
 if status!='COMPLETED':raise SystemExit('independent Reviewer-v2 round stopped; partial evidence preserved')
if __name__=='__main__':main()
