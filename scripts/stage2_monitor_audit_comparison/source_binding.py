import os
import json,gzip,re
from pathlib import Path
from collections import defaultdict,Counter
ROOT=Path(os.environ['MONITOR_COMPARISON_REPLAY'])/'graphs'
D=json.load(open('joined_inputs.json'))
records=json.load(open('localization_records.json'))
out=[]
for fid,d in D.items():
 graph=json.load(gzip.open(ROOT/(fid+'.json.gz')))['graph']
 candidates={c['object_ref'] for c in d['new']}
 locs=defaultdict(set)
 for o in graph['observations']:
  objs=set(o['object_refs'])&candidates
  if not objs:continue
  for key in ['source_locator','occurrence_locator']:
   loc=o.get(key)
   if loc:
    locs[(loc['member'],loc['member_sha256'],loc.get('line'))].update(objs)
 for r in records:
  if r['full_id']!=fid:continue
  em={e['ref']:e for e in d[r['layer'].lower()+'_packet']['evidence']}
  hits=[]
  for ref in r['evidence_refs']:
   e=em[ref];path=e['path'];member=path.split('#',1)[0]
   # A route item cannot be matched by the checksum of its containing terminal file.
   if '#route[' in path:continue
   # Derived diff summaries have a manifest checksum but are not that raw manifest.
   if 'derived_from' in str(e.get('preview','')):continue
   line=int(path.rsplit('#L',1)[1]) if '#L' in path else None
   objs=locs.get((member,e['sha256'],line),set())
   if objs:hits.append({'evidence_ref':ref,'path':path,'objects':sorted(objs),'level':'exact_record' if line else 'exact_member'})
  out.append({'full_id':fid,'layer':r['layer'],'reference_id':r['reference_id'],'positive':r['positive'],'status':r['status'],'corrected_status':r['corrected_status'],'hits':hits})
Path('source_binding_records.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
summary={}
for layer in ['B','C']:
 rr=[r for r in out if r['layer']==layer and r['positive']]
 lookup={(r['full_id'],r['reference_id']):r for r in records if r['layer']==layer}
 summary[layer]={'positive_events':len(rr),'candidate_source_bound_events':sum(bool(r['hits']) for r in rr),'extra_beyond_literal':sum(bool(r['hits']) and lookup[(r['full_id'],r['reference_id'])]['new_literal']['tier']=='none' for r in rr)}
Path('source_binding_summary.json').write_text(json.dumps(summary,indent=2))
print(summary)
