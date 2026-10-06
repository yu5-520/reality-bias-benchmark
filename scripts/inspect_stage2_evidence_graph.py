#!/usr/bin/env python3
"""Trace one observed object back to exact archived fields, by independent clock."""
import argparse
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stage2.r7_checkpoint_v1.common import digest
from stage2.monitor_enhancement.frozen_archive import NativeArchive


def inspect(graph_file, object_ref, archive=None):
    bundle=json.loads(gzip.decompress(Path(graph_file).read_bytes()));g=bundle['graph']
    if digest({k:v for k,v in g.items() if k!='graph_hash'})!=g['graph_hash']: raise ValueError('graph hash mismatch')
    rows=[r for r in g['observations'] if object_ref in r['object_refs']]
    if not rows: raise ValueError('object absent')
    ar=NativeArchive(archive,bundle['full_id'],rows[0]['source_locator']['archive_sha256']) if archive else None
    clocks=defaultdict(list)
    for r in rows:
        if ar:
            value=ar.resolve(r['source_locator'])
            if digest(value)!=r['field_value_hash']: raise ValueError('field hash mismatch')
            r={**r,'resolved_value':value}
        clocks[r['clock_id']].append(r)
    for clock in clocks: clocks[clock].sort(key=lambda r:r['native_sequence'])
    return {'full_id':bundle['full_id'],'object_ref':object_ref,'observation_count':len(rows),
            'cross_clock_order':'UNRESOLVED','ties':'UNORDERED','semantic_adoption':'NOT_INFERRED',
            'source_fields_verified':bool(ar),'independent_clocks':dict(clocks)}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--graphs',type=Path,required=True);p.add_argument('--cell',required=True)
    p.add_argument('--object',required=True);p.add_argument('--archive',type=Path);a=p.parse_args()
    print(json.dumps(inspect(a.graphs/(a.cell+'.json.gz'),a.object,a.archive),ensure_ascii=False,indent=2))
