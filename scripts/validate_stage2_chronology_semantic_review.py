#!/usr/bin/env python3
"""Validate targeted review accounting and immutable evidence bindings offline."""
from collections import Counter
import gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'stage2/replication_v2';COR=BASE/'chronology_correction_v1';OUT=BASE/'chronology_semantic_review_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def main():
 s=read(OUT/'summary.json');rows=read(OUT/'semantic_reviews.json');pairs=read(OUT/'paired_reviews.json')
 z=(OUT/s['observations']['path']).read_bytes();assert sha(z)==s['observations']['sha256'];raw=gzip.decompress(z);assert sha(raw)==s['observations']['uncompressed_sha256']
 obs={o['full_id']:o for o in map(json.loads,raw.splitlines())};assert len(obs)==s['observations']['cells']==58
 ps={p['group_id']+'-'+p['cell_id']:p for p in map(json.loads,gzip.decompress((COR/'full_context_corrected_packets.jsonl.gz').read_bytes()).splitlines())}
 deps=read(COR/'semantic_reference_dependencies.json');expected={(r['full_id'],r['event_id']) for r in deps if r['status']=='REASSESS_EVIDENCE'}
 keys={(r['full_id'],r['event_id']) for r in rows};assert len(keys)==len(rows)==65;assert expected<=keys
 assert sum(r['selection']=='DEPENDENCY_FLAG' for r in rows)==61
 for r in rows:
  p=ps[r['full_id']];oldpath=ROOT/r['legacy_audit_path'];a=read(oldpath);e=next(e for e in a['cpr_events'] if e['event_id']==r['event_id'])
  assert sha(oldpath.read_bytes())==r['legacy_audit_sha256'];assert e['status']==r['legacy_status'];assert a['input_packet_sha256']==r['legacy_packet_sha256']
  assert r['corrected_packet_sha256']==p['packet_sha256'];refs={e['ref'] for e in p['evidence']};assert r['corrected_evidence_refs'] and set(r['corrected_evidence_refs'])<=refs
  assert r['status_changed']==(r['legacy_status']!=r['reviewed_status'])
  assert r['old_graph_or_transition_labels_rebound'] is False
  assert r['observation_sha256']==sha(enc(obs[r['full_id']]))
  assert obs[r['full_id']]['corrected_packet_sha256']==p['packet_sha256']
  assert r['reviewed_rationale']
 for o in obs.values():
  current=None;union=set()
  for t in o['application_state_transitions']:
   if current is None:current=dict(t['initial_hashes']);continue
   for k,v in t['hash_changes'].items():
    assert current.get(k)==v['before'];union.add(k)
    if v['after'] is None:current.pop(k,None)
    else:current[k]=v['after']
  assert current==o['terminal_hashes'];assert sorted(union)==o['files_changed_at_any_observed_checkpoint']
 assert sum(r['status_changed'] for r in rows)==s['status_changes']==9
 assert dict(Counter(r['reviewed_status'] for r in rows))==s['reviewed_subset_status_counts']
 assert dict(Counter(r['reviewed_status'] for r in rows if r['selection']=='DEPENDENCY_FLAG'))==s['dependency_subset_status_counts']
 assert s['unreviewed_historical_dimension_records']==240-len(rows)==175
 pp={}
 for g in ('G2','G3','G4','G5'):
  for p in map(json.loads,gzip.decompress((COR/(g+'_corrected_packets.jsonl.gz')).read_bytes()).splitlines()):pp[g+'-'+p['cell_id']]=p
 assert len(pairs)==9 and {r['full_id'] for r in pairs}==set(read(COR/'summary.json')['paired']['affected_pairs'])
 for r in pairs:
  p=pp[r['full_id']];assert p['packet_sha256']==r['corrected_packet_sha256'];g,cell=r['full_id'].split('-',1)
  old=BASE/g/'paired_semantic_audit_v1/audits'/(cell+'.json');assert sha(old.read_bytes())==r['legacy_audit_sha256']
  refs={e['ref'] for e in p['evidence']};assert r['intervention_refs'] and set(r['intervention_refs'])<=refs
  for arm,v in r['arms'].items():
   assert v['hash_transitions']==p[arm]['repository_diff']['hash_transitions'];assert v['receipt']==p[arm]['attempt_receipt'];assert set(v['evidence_refs'])<=refs
  assert r['replacement_causal_effect_class'] is None
 invalidations=read(OUT/'graph_invalidations.json')
 expected_graph_cells={r['full_id'] for r in rows if r['legacy_status']=='SUPPORTED' and r['reviewed_status']!='SUPPORTED'}
 assert {r['full_id'] for r in invalidations}==expected_graph_cells
 for r in invalidations:
  old=read(BASE/'gpt56sol_full_context_semantic_audit_v1/formal_review'/(r['full_id']+'.json'))
  assert r['legacy_topology']==old['dynamic_topology']
 assert len(read(OUT/'counterevidence_screen.json'))==18
 for key in ('full_population_replacement_semantic_counts','replacement_engineering_causal_counts','replacement_primary_monitor_metrics'):assert s[key] is None
 for key in ('provider_calls','subject_calls','repair_calls'):assert s[key]==0
 assert s['primary_blind_reference_labels_modified'] is False
 print('PASS: 65 reviewed records, nine contrasts, 58 observation bindings, nine status changes; no mixed reference population')
if __name__=='__main__':main()
