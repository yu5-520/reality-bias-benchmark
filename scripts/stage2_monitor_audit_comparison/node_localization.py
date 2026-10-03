import os
import json,re
from collections import Counter
D=json.load(open('joined_inputs.json'))
POS={'SUPPORTED','SUPPORTED_CANDIDATE'}
def hit(obj,text):
 t=obj.split(':',1)[-1].lower()
 return len(t)>=4 and re.search(r'(?<![\w./-])'+re.escape(t)+r'(?![\w./-])',text.lower()) is not None
out=[];events=[]
for fid,d in D.items():
 if 'c_audit' not in d:continue
 a=d['c_audit'];em={e['ref']:e for e in d['c_packet']['evidence']}
 positives=[e for e in a['cpr_events'] if e['status'] in POS]
 used={n for e in positives for n in e['semantic_node_refs']}
 bynode={}
 for n in a['semantic_nodes']:
  if n['node_id'] not in used:continue
  text=n['semantic_state']+' '+' '.join(str(em[e].get('preview',''))+' '+em[e]['path'] for e in n['evidence_refs'])
  r={'full_id':fid,'node_id':n['node_id'],'role':n['role']}
  for ver in ['old','new']:
   r[ver]=any(hit(c['object_ref'],text) for c in d[ver])
  out.append(r);bynode[n['node_id']]=r
 for e in positives:
  ns=e['semantic_node_refs']
  events.append({'full_id':fid,'event_id':e['event_id'],'n':len(ns),**{v:sum(bynode[n][v] for n in ns) for v in ['old','new']}})
summary={'unique_positive_event_nodes':len(out),'nodes_with_literal_object_evidence':{v:sum(r[v] for r in out) for v in ['old','new']},'events_all_referenced_nodes_with_object_evidence':{v:sum(r[v]==r['n'] for r in events) for v in ['old','new']},'event_count':len(events)}
json.dump({'summary':summary,'nodes':out,'events':events},open('node_localization.json','w'),indent=2)
print(summary)
