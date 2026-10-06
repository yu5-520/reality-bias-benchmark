import os
import sys,json,tarfile,gzip,hashlib
from pathlib import Path
from collections import defaultdict,Counter
sys.path.insert(0,str(Path('sources').resolve()))
import build_stage2_full_context_semantic_packets as C
import build_stage2_84a_monitor_blind_audit_packets as B
REPO=Path(os.environ['MONITOR_COMPARISON_REPO']);SOURCE=Path(os.environ['MONITOR_COMPARISON_SOURCES']);AUD=REPO/'stage2/replication_v2/gpt56sol_full_context_semantic_audit_v1'
new=defaultdict(list)
for l in (Path(os.environ['MONITOR_COMPARISON_REPLAY'])/'candidate_objects.jsonl').read_text().splitlines():
 r=json.loads(l);new[r['full_id']].append(r)
result={};checks=Counter()
for b in json.load(open(Path(os.environ['MONITOR_COMPARISON_REPLAY'])/'cell_summary.json')):
 fid=b['full_id'];g,cell=b['group_id'],b['cell_id'];d=SOURCE/(g+'A')/'stage2/replication_v2'/g/'natural_A'/cell
 with tarfile.open(d/'first_attempt.tar.gz') as ar:
  m={m.name.removeprefix('./'):m for m in ar if m.isfile()}
  old=json.load(ar.extractfile(m['monitor_candidates.json'])) if 'monitor_candidates.json' in m else []
 bp=B.build_packet(g,cell,d)
 row={'old':old,'new':new[fid],'b_packet':bp}
 cp=AUD/'formal_review'/f'{fid}.json'
 if cp.exists():
  c=json.load(open(cp));packet=C.build_packet(g,cell,d)
  assert packet['packet_sha256']==c['input_packet_sha256'],(fid,packet['packet_sha256'],c['input_packet_sha256'])
  bc=json.load(open(AUD/'layer_b_c_comparison/cells'/f'{fid}.json'))
  assert bp['packet_sha256']==bc['layer_b']['packet_sha256'],fid
  checks.update(c_hash_verified=1,b_hash_verified=1)
  row.update(c_audit=c,c_packet=packet)
 result[fid]=row
 print(fid,flush=True)
Path('joined_inputs.json').write_text(json.dumps(result,ensure_ascii=False))
Path('preparation_checks.json').write_text(json.dumps(dict(checks),indent=2))
print(dict(checks))
