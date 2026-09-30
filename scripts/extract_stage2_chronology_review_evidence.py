#!/usr/bin/env python3
"""Extract frozen observations for targeted correction review; assign no labels."""
import argparse,gzip,hashlib,io,json,re,sys,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from arena.checkpoint_chronology import ordered_checkpoints
COR=ROOT/'stage2/replication_v2/chronology_correction_v1'
PATTERN=re.compile(r'no (?:code |frontend )?changes?|no new payment|already (?:includes|contains|has)|launcher|SRE|endpoint|deleted',re.I)
FOCUS={'G2-X2-T2','G3-X4-T2','G4-X3-T2','G2-X3-T2','G2-X5-T2','G3-X1-T3','G3-X5-T2','G3-X7-T2','G4-X4-T2','G4-X6-T2','G5-X2-T2','G5-X5-T2','G5-X6-T3'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def walk(v,path=''):
 if isinstance(v,dict):
  yield path,v
  for k,val in v.items():yield from walk(val,path+'/'+str(k).replace('~','~0').replace('/','~1'))
 elif isinstance(v,list):
  for i,val in enumerate(v):yield from walk(val,path+'/'+str(i))
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--sources-root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
 packets={p['group_id']+'-'+p['cell_id']:p for p in map(json.loads,gzip.decompress((COR/'full_context_corrected_packets.jsonl.gz').read_bytes()).splitlines())}
 deps=json.loads((COR/'semantic_reference_dependencies.json').read_text());ids=sorted({r['full_id'] for r in deps if r['status']=='REASSESS_EVIDENCE'} | {r['full_id'] for r in json.loads((COR/'natural_changes.json').read_text()) if r['kind']=='full_context' and r['repository_diff_changed']})
 for fid in ids:
  packet=packets[fid];g,cell=packet['group_id'],packet['cell_id'];arc=(a.sources_root/(g+'A')/'stage2/replication_v2'/g/'natural_A'/cell/'first_attempt.tar.gz').read_bytes()
  assert sha(arc)==packet['attempt_receipt']['archive_sha256']
  with tarfile.open(fileobj=io.BytesIO(gzip.decompress(arc))) as ar:
   mm={m.name.removeprefix('./'):m for m in ar.getmembers() if m.isfile()}
   allowed={r['path']:r for r in json.load(ar.extractfile(mm['audit_raw_bundle_manifest.json']))['entries']}
   def raw(path):
    assert path in allowed
    b=ar.extractfile(mm[path]).read();assert sha(b)==allowed[path]['sha256'];return b
   cps=ordered_checkpoints(ar,mm,allowed=allowed)
   transitions=[];messages=[];seen=set();old=None;union=set()
   for _,path,m in cps:
    raw(path)
    cur=m['application_file_hashes'];seq=m['_chronology']['sequence']
    delta={} if old is None else {k:{'before':old.get(k),'after':cur.get(k)} for k in sorted(old.keys()|cur.keys()) if old.get(k)!=cur.get(k)}
    union.update(delta)
    if old is None or delta:
     entry={'sequence':seq,'event_ref':m['event_ref'],'manifest':path,'manifest_sha256':allowed[path]['sha256'],'hash_changes':delta,'initial_hashes':cur if old is None else None}
     if fid in FOCUS:
      entry['file_contents']={}
      for rel in (cur if old is None else delta):
       file=path.rsplit('/manifest.json',1)[0]+'/application/'+rel
       if file in allowed:
        b=raw(file);assert sha(b)==cur[rel]
        entry['file_contents'][rel]={'path':file,'sha256':sha(b),'text':b.decode('utf-8',errors='replace')}
     transitions.append(entry)
    old=cur
    npath=path.replace('/manifest.json','/native_state.json')
    if fid in FOCUS and npath in allowed:
     b=raw(npath);obj=json.loads(b)
     for pointer,v in walk(obj):
      text=v.get('content')
      if isinstance(text,str) and text not in seen and PATTERN.search(text) and v.get('kind')!='tool_result' and v.get('action')!='read_file':
       seen.add(text);messages.append({'first_observed_checkpoint_sequence':seq,'member':npath,'member_sha256':sha(b),'json_pointer':pointer+'/content','text':text})
   result={'schema':'chronology-targeted-observations-v1','full_id':fid,'corrected_packet_sha256':packet['packet_sha256'],'archive_sha256':sha(arc),'checkpoint_count':len(cps),'first_manifest':cps[0][1],'last_manifest':cps[-1][1],'terminal_hashes':cps[-1][2]['application_file_hashes'],'files_changed_at_any_observed_checkpoint':sorted(union),'application_state_transitions':transitions,'selected_messages':messages,'message_selection':'FOCUS cells only; declared regex over non-tool-result content fields. First observed checkpoint is not a send/read/adoption timestamp. No-match does not establish absence.','observability_boundary':'Persisted checkpoints only; within-checkpoint transient actions are not excluded.'}
   (a.out/(fid+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
 print(f'PASS: extracted {len(ids)} frozen cell observations; no semantic labels assigned')
if __name__=='__main__':main()
