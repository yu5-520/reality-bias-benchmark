import os
import json,gzip,hashlib,re
from pathlib import Path
from collections import Counter
ROOT=Path(os.environ['MONITOR_COMPARISON_REPO'])/'stage2/replication_v2'
D=json.load(open('joined_inputs.json'));R=json.load(open('localization_records.json'))
P={}
for line in gzip.open(ROOT/'chronology_correction_v1/full_context_corrected_packets.jsonl.gz','rt'):
 p=json.loads(line);expected=p['packet_sha256'];p['packet_sha256']=''
 assert hashlib.sha256(json.dumps(p,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()==expected
 p['packet_sha256']=expected;P[p['group_id']+'-'+p['cell_id']]=p
reviews={(r['full_id'],r['event_id']):r for r in json.load(open(ROOT/'chronology_semantic_review_v1/semantic_reviews.json'))}
out=[]
for row in R:
 if row['layer']!='C' or row['corrected_status'] not in {'SUPPORTED','SUPPORTED_CANDIDATE'}:continue
 r=dict(row);key=(r['full_id'],r['reference_id']);rev=reviews.get(key)
 r['input_basis']='ORIGINAL_FROZEN_AUDIT_UNTARGETED'
 if rev:
  p=P[r['full_id']];assert p['packet_sha256']==rev['corrected_packet_sha256']
  em={e['ref']:e for e in p['evidence']}
  core=rev['reviewed_rationale'].lower()
  evidence=' '.join(str(em[e]['preview'])+' '+em[e]['path'] for e in rev['corrected_evidence_refs']).lower()
  r['core']=core;r['input_basis']='CORRECTED_TARGETED_RATIONALE_AND_EVIDENCE'
  r['evidence_refs']=rev['corrected_evidence_refs']
  for ver in ['old','new']:
   hits=[]
   for obj in sorted({c['object_ref'] for c in D[r['full_id']][ver]}):
    tok=obj.split(':',1)[-1].lower()
    if len(tok)<4:continue
    pat=r'(?<![\w./-])'+re.escape(tok)+r'(?![\w./-])'
    ct=re.search(pat,core);et=re.search(pat,evidence)
    if ct or et:hits.append({'object':obj,'tier':'core' if ct else 'evidence','token':tok})
   r[ver+'_literal']={'tier':'core' if any(h['tier']=='core' for h in hits) else 'evidence' if hits else 'none','objects':hits}
 out.append(r)
summary={'n':len(out),'basis':dict(Counter(r['input_basis'] for r in out))}
for ver in ['old','new']:summary[ver]=dict(Counter(r[ver+'_literal']['tier'] for r in out))
summary['gained']=[r['full_id']+':'+r['reference_id'] for r in out if r['old_literal']['tier']=='none' and r['new_literal']['tier']!='none']
summary['lost']=[r['full_id']+':'+r['reference_id'] for r in out if r['old_literal']['tier']!='none' and r['new_literal']['tier']=='none']
summary['new_unmatched']=[r['full_id']+':'+r['reference_id'] for r in out if r['new_literal']['tier']=='none']
json.dump({'summary':summary,'records':out},open('corrected_comparison.json','w'),ensure_ascii=False,indent=2)
print(json.dumps(summary,ensure_ascii=False,indent=2))
