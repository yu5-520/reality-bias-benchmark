#!/usr/bin/env python3
"""Small-scale Qwen Reviewer-v2 runtime preflight; never a formal result."""
import argparse,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from adapters.bailian_openai_chat import chat_completion,extract_content,explicit_cache_text
from arena.io_utils import load_jsonl,sha256_file
from arena.reviewer_v2_contract import normalize,parse_json,stable_hash
from arena.evaluate_reviewer_v2_deepseek import PROMPTS
VERSION='R234-QWEN-REVIEWER-V2-PREFLIGHT-v0.2'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--r2',required=True);ap.add_argument('--outdir',required=True);ap.add_argument('--count',type=int,default=5);ap.add_argument('--explicit-cache',action='store_true');a=ap.parse_args()
 if not 1<=a.count<=10:raise SystemExit('preflight count must be 1..10')
 if not all(os.environ.get(x) for x in ('BAI','BAILIAN_BASE_URL','BAILIAN_MODEL')):raise SystemExit('Bailian binding missing')
 packets=load_jsonl(a.r2)[:a.count];prompt_path=ROOT/PROMPTS['R2'];prompt=prompt_path.read_text(encoding='utf-8');out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True);rows=[]
 for i,p in enumerate(packets,1):
  system_content=explicit_cache_text(prompt) if a.explicit_cache else prompt
  messages=[{'role':'system','content':system_content},{'role':'user','content':json.dumps(p,ensure_ascii=False)}];failures=[];final=None
  for attempt in range(1,4):
   started=time.time()
   try:
    r=chat_completion(messages,response_format_json=True,max_tokens=4000,temperature=0);lat=round((time.time()-started)*1000,2);raw=extract_content(r);final=normalize('R2',parse_json(raw));u=r.get('usage') or {};pd=u.get('prompt_tokens_details') or {};cd=u.get('completion_tokens_details') or {};pt=u.get('prompt_tokens');cached=pd.get('cached_tokens');created=pd.get('cache_creation_input_tokens')
    rows.append({'index':i,'packet_id':p['packet_id'],'packet_hash':p.get('packet_hash'),'attempt':attempt,'returned_model':r.get('model'),'latency_ms':lat,'transport_latency_ms':r.get('_transport_latency_ms'),'prompt_tokens':pt,'cache_creation_input_tokens':created,'cached_prompt_tokens':cached,'completion_tokens':u.get('completion_tokens'),'reasoning_tokens':cd.get('reasoning_tokens'),'total_tokens':u.get('total_tokens'),'review_status':final.get('review_status'),'failures_before_success':failures});break
   except Exception as e:failures.append({'attempt':attempt,'error':repr(e),'latency_ms':round((time.time()-started)*1000,2)})
  if final is None:rows.append({'index':i,'packet_id':p['packet_id'],'status':'FAILED','failures':failures});break
 (out/'preflight_records.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');successes=[x for x in rows if x.get('review_status')];later=successes[1:]
 summary={'version':VERSION,'status':'PASS' if len(successes)==a.count else 'FAIL','requested':a.count,'completed':len(successes),'model':os.environ['BAILIAN_MODEL'],'prompt_sha256':sha256_file(prompt_path),'cache_mode':'explicit_ephemeral_system_prefix' if a.explicit_cache else 'implicit','mean_latency_ms':sum(x['latency_ms'] for x in successes)/len(successes) if successes else None,'mean_reasoning_tokens':sum((x.get('reasoning_tokens') or 0) for x in successes)/len(successes) if successes else None,'cache_creation_input_tokens':[x.get('cache_creation_input_tokens') for x in successes],'cached_prompt_tokens':[x.get('cached_prompt_tokens') for x in successes],'later_packets_all_cache_hit':bool(later) and all((x.get('cached_prompt_tokens') or 0)>0 for x in later),'formal_replication_result':False,'subject_reruns_triggered':0}
 summary['summary_hash']=stable_hash(summary);(out/'preflight_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True),encoding='utf-8');print(json.dumps(summary,ensure_ascii=False,indent=2))
 if summary['status']!='PASS':raise SystemExit('Qwen Reviewer-v2 preflight failed')
if __name__=='__main__':main()
