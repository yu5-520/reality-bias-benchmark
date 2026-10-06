import os
import json,re,hashlib
from pathlib import Path
from collections import Counter,defaultdict

ROOT=Path(os.environ['MONITOR_COMPARISON_REPO'])
AUD=ROOT/'stage2/replication_v2/gpt56sol_full_context_semantic_audit_v1'
POS={'SUPPORTED','SUPPORTED_CANDIDATE'}
D=json.load(open('joined_inputs.json'))
B=[json.loads(l) for l in open('sources/layer_b_reference_records.jsonl')]
F=json.load(open(ROOT/'configs/stage2_monitor_source_bound_matching_rule_v1.json'))['monitor_rule_to_compatible_structure_families']
def tokens(obj,mode='legacy'):
 s=obj.split(':',1)[-1].strip().lower();base=s.rsplit('/',1)[-1]
 vals={s,base,base.rsplit('.',1)[0]} if mode=='legacy' else {s}
 return sorted(t for t in vals if len(t)>=4)
def overlap(obj,txt,mode):
 for t in tokens(obj,mode):
  if (t in txt if mode=='legacy' else re.search(r'(?<![\w./-])'+re.escape(t)+r'(?![\w./-])',txt)):
   return t
 return None
def btext(r):
 return ' '.join(str(r.get(k)) for k in ['semantic_before','semantic_after','semantic_delta','source_ref','carrier_ref','consequence_ref','decision_or_action_ref'] if r.get(k) is not None).lower()
def temporal(c,r):
 a=c.get('prefix_sequence');b=r.get('first_consequence_sequence')
 return a is None or b is None or int(a)<=int(b)
def score(c,r):
 if r['structure_family'] not in F.get(c['rule_id'],[]) or not temporal(c,r):return -1
 return 2 if overlap(c['object_ref'],btext(r),'legacy') else 1
baseline={};warnings={}
for fid,d in D.items():
 refs=[r for r in B if r['group_id']+'-'+r['cell_id']==fid]
 positives=[r for r in refs if r['claim_status'] in POS and not r['negative_case']]
 negatives=[r for r in refs if r['negative_case'] or r['claim_status']=='NEGATIVE_BOUNDARY']
 matched=set()
 for r in positives:
  opts=sorted([(score(c,r),c) for c in d['old']],key=lambda z:(z[0],-(z[1].get('prefix_sequence') or 0)),reverse=True)
  sc,c=opts[0] if opts else (-1,None)
  cl={2:'SUPPORTED_MATCH',1:'PARTIAL_LOCALIZATION'}.get(sc,'MISS' if r.get('evidence_surface_available',True) else 'UNOBSERVABLE_REFERENCE')
  wid=c['candidate_hash'] if sc>0 else None
  baseline[r['reference_id']]={'match_class':cl,'warning_id':wid}
  if wid:matched.add(wid);warnings[wid]='SUPPORTED'
 for c in d['old']:
  wid=c['candidate_hash']
  if wid in matched:continue
  reject=any(r['structure_family'] in F.get(c['rule_id'],[]) and temporal(c,r) and overlap(c['object_ref'],btext(r),'legacy') for r in negatives)
  if warnings.get(wid)!='SUPPORTED':warnings[wid]='REJECTED' if reject else 'UNSUPPORTED'
frozen=[json.loads(l) for l in open(ROOT/'stage2/replication_v2/primary_monitor_benchmark_84_v1/evaluation_records.jsonl')]
diff=[]
for r in frozen:
 if r.get('reference_id'):
  got=baseline[r['reference_id']]
  if any(got[k]!=r[k] for k in got):diff.append([r['reference_id'],got,{k:r[k] for k in got}])
assert not diff,diff
print('BASELINE_B',dict(Counter(r['match_class'] for r in baseline.values())),dict(Counter(warnings.values())))
corrections={(r['full_id'],r['event_id']):r for r in json.load(open(ROOT/'stage2/replication_v2/chronology_semantic_review_v1/semantic_reviews.json'))}
records=[];unresolved=[]
for fid,d in D.items():
 for layer in ['B','C']:
  if layer=='C' and 'c_audit' not in d:continue
  packet=d[layer.lower()+'_packet'];em={e['ref']:e for e in packet['evidence']}
  refs=[r for r in B if r['group_id']+'-'+r['cell_id']==fid] if layer=='B' else d['c_audit']['cpr_events']
  nm={n['node_id']:n for n in d.get('c_audit',{}).get('semantic_nodes',[])}
  for r in refs:
   rid=r['reference_id'] if layer=='B' else r['event_id']
   status=r['claim_status'] if layer=='B' else r['status']
   erefs=set(r.get('evidence_refs',[]))
   if layer=='B':
    core=btext(r)
    for k in ['source_ref','carrier_ref','consequence_ref','decision_or_action_ref']:
     erefs.update(re.findall(r'\bE\d{4}\b',str(r.get(k,''))))
   else:
    nodes=[nm[n] for n in r.get('semantic_node_refs',[]) if n in nm]
    core=' '.join([r.get('summary',''),r.get('counter_explanation','')]+[n['semantic_state'] for n in nodes]).lower()
    for n in nodes:erefs.update(n.get('evidence_refs',[]))
   missing=erefs-set(em)
   if missing:unresolved.append([fid,layer,rid,sorted(missing)])
   evidence=' '.join(str(em[e].get('preview',''))+' '+em[e]['path'] for e in sorted(erefs) if e in em).lower()
   row={'full_id':fid,'layer':layer,'reference_id':rid,'status':status,'positive':status in POS and not r.get('negative_case',False),'family':r.get('structure_family',r.get('dimension')),'core':core,'evidence_refs':sorted(erefs)}
   row['corrected_status']=corrections.get((fid,rid),{}).get('reviewed_status',status) if layer=='C' else status
   for mode in ['legacy','literal']:
    for version in ['old','new']:
     hits=[]
     for obj in sorted(set(c['object_ref'] for c in d[version])):
      ct=overlap(obj,core,mode);et=overlap(obj,evidence,mode)
      if ct or et:hits.append({'object':obj,'tier':'core' if ct else 'evidence','token':ct or et})
     row[version+'_'+mode]={'tier':'core' if any(h['tier']=='core' for h in hits) else 'evidence' if hits else 'none','objects':hits}
   records.append(row)
assert not unresolved,unresolved
Path('localization_records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
summary={'baseline_b':dict(Counter(r['match_class'] for r in baseline.values())),'baseline_b_warnings':dict(Counter(warnings.values())),'unresolved_evidence_refs':unresolved,'populations':{}}
for layer in ['B','C']:
 for status_filter in ['positive','supported_only','corrected_positive']:
  if layer=='B' and status_filter=='corrected_positive':continue
  rr=[r for r in records if r['layer']==layer and (r['positive'] if status_filter=='positive' else r['status']=='SUPPORTED' if status_filter=='supported_only' else r['corrected_status'] in POS)]
  pop={ 'n':len(rr),'trajectories':len(set(r['full_id'] for r in rr)) }
  for mode in ['legacy','literal']:
   ss={}
   for ver in ['old','new']:
    ss[ver]=dict(Counter(r[ver+'_'+mode]['tier'] for r in rr))
    ss[ver]['hit_trajectories']=len(set(r['full_id'] for r in rr if r[ver+'_'+mode]['tier']!='none'))
   ss['paired']=dict(Counter(('both' if r['old_'+mode]['tier']!='none' and r['new_'+mode]['tier']!='none' else 'gained' if r['new_'+mode]['tier']!='none' else 'lost' if r['old_'+mode]['tier']!='none' else 'neither') for r in rr))
   ss['systems']={x:{'n':len([r for r in rr if r['full_id'].split('-')[1]==x]),**{v:sum(r[v+'_'+mode]['tier']!='none' for r in rr if r['full_id'].split('-')[1]==x) for v in ['old','new']}} for x in ['X'+str(i) for i in range(1,8)]}
   pop[mode]=ss
  summary['populations'][layer+'_'+status_filter]=pop
burden={}
for layer in ['B','C']:
 cells=set(r['full_id'] for r in records if r['layer']==layer)
 burden[layer]={}
 for ver in ['old','new']:
  objs={(f,c['object_ref']) for f in cells for c in D[f][ver]}
  positives={(r['full_id'],h['object']) for r in records if r['layer']==layer and r['positive'] for h in r[ver+'_literal']['objects']}
  negatives={(r['full_id'],h['object']) for r in records if r['layer']==layer and r['status']=='NEGATIVE_BOUNDARY' for h in r[ver+'_literal']['objects']}
  unestablished={(r['full_id'],h['object']) for r in records if r['layer']==layer and r['status']=='NOT_ESTABLISHED' for h in r[ver+'_literal']['objects']}
  burden[layer][ver]={'records':sum(len(D[f][ver]) for f in cells),'unique_objects_per_trajectory':len(objs),'positive_linked_objects':len(positives),'positive_and_negative':len(positives&negatives),'negative_only_objects':len(negatives-positives),'not_established_only_objects':len(unestablished-positives-negatives),'no_label_link':len(objs-positives-negatives-unestablished)}
summary['burden']=burden
Path('comparison_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False,indent=2))
