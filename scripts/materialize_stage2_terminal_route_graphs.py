#!/usr/bin/env python3
"""Rebuild only the two pinned observation graphs, without subject/model calls."""
import argparse,json,gzip,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from stage2.monitor_enhancement.frozen_archive import NativeArchive
from stage2.monitor_enhancement.evidence_graph import EvidenceGraph
from stage2.monitor_enhancement.replay_analysis import select_candidates,add_unknown_edges
from stage2.r7_checkpoint_v1.common import stable_json_bytes

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():p.error('fresh graph output required')
 a.out.mkdir(parents=True)
 cases=json.load(open(ROOT/'configs/stage2_terminal_route_repair_first_round_v1.json'))['cases']
 rules=json.load(open(ROOT/'configs/stage2_p2_evidence_graph_replay_v2.json'))['candidate_rules']
 for c in cases:
  fid=c['full_id'];g,cell=fid.split('-',1)
  archive=a.source_root/(g+'A')/'stage2/replication_v2'/g/'natural_A'/cell/'first_attempt.tar.gz'
  ar=NativeArchive(archive,fid,c['archive_sha256']);observations,coverage,sources=ar.build();ar.verify_observations()
  builder=EvidenceGraph()
  for o in observations:builder.add_observation(o)
  graph=builder.snapshot();selected=select_candidates(graph,**rules);add_unknown_edges(builder,graph,selected);graph=builder.snapshot()
  if graph['graph_hash']!=c['graph_hash']:raise ValueError('frozen graph reproduction mismatch: '+fid)
  (a.out/(fid+'.json.gz')).write_bytes(gzip.compress(stable_json_bytes({'full_id':fid,'graph':graph,'source_index':sources}),mtime=0));ar.tf.close()
  print(fid,'graph hash verified',flush=True)
if __name__=='__main__':main()
