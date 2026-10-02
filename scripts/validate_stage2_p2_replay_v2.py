#!/usr/bin/env python3
"""Validate persisted replay bytes, graph bindings, coverage and observation maps."""
import argparse
import gzip
import json
import sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from stage2.r7_checkpoint_v1.common import digest


def require(condition, message):
    if not condition: raise ValueError(message)


def validate(root):
    manifest=json.loads((root/'manifest.json').read_bytes())
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}-{'manifest.json'}
    require(actual==set(manifest['files']),'file inventory mismatch')
    for name,b in manifest['files'].items():
        data=(root/name).read_bytes()
        require(len(data)>0 and len(data)==b['bytes'] and digest(data)==b['sha256'],'file binding: '+name)
    binding=json.loads((root/'run_binding.json').read_bytes())
    for name,h in binding['implementation_sha256'].items(): require(digest((ROOT/name).read_bytes())==h,'implementation drift: '+name)
    cells=json.loads((root/'cell_summary.json').read_bytes());summary=json.loads((root/'summary.json').read_bytes())
    expected={f'G{g}-X{x}-T{t}' for g in range(2,6) for x in range(1,8) for t in range(1,4)}
    require(len(cells)==84 and {r['full_id'] for r in cells}==expected,'population mismatch')
    config=json.loads((ROOT/'configs/stage2_p2_evidence_graph_replay_v2.json').read_bytes())
    require({p.stem.removesuffix('.json') for p in (root/'graphs').glob('*.gz')}==expected,'graph population')
    require({p.stem.removesuffix('.json') for p in (root/'route_maps').glob('*.gz')}==set(config['priority_route_maps']),'route population')
    total=Counter()
    for c in cells:
        fid=c['full_id'];cover=c['coverage']
        require(cover['native_records']>0 or cover.get('explicit_zero_native_call_history')==1,'unexplained empty stream')
        require(cover['last_observed_file_count']>0,'empty final observed state')
        bundle=json.loads(gzip.decompress((root/'graphs'/f'{fid}.json.gz').read_bytes()));g=bundle['graph'];sources=bundle['source_index']
        require(bundle['full_id']==fid,'bundle identity')
        require(digest({k:v for k,v in g.items() if k!='graph_hash'})==g['graph_hash']==c['graph_hash'],'graph hash')
        obs={r['observation_id']:r for r in g['observations']}
        require(len(obs)==len(g['observations'])==c['observation_count']==c['resolved_observation_count'],'observation count')
        nodes={r['ref']:r for r in g['nodes']};obs_ids=set(obs);node_refs=set(nodes);source_refs=set(sources)
        node_obs={ref:set(n['observation_ids']) for ref,n in nodes.items()}
        require(len(nodes)==c['graph_node_count'] and len(g['edges'])==c['graph_edge_count'],'graph counts')
        for n in nodes.values(): require(set(n['observation_ids'])<=obs_ids,'node observation refs')
        for oid,r in obs.items():
            require(r['trajectory_id']==fid and type(r['native_sequence']) is int and bool(r['clock_id']),'observation clock/identity')
            loc=r['source_locator'];require(loc['archive_sha256']==c['archive_sha256'],'source archive binding')
            require(sources[r['evidence_ref']]==loc and r['evidence_ref']=='evidence:'+digest(loc),'source index binding')
            require('event:'+r['event_ref'] in nodes and set(r['object_refs'])<=node_refs,'observation endpoint')
            require(oid in node_obs['event:'+r['event_ref']],'event observation binding')
            for ref in r['object_refs']: require(oid in node_obs[ref],'object observation binding')
        for e in g['edges']:
            require(e['source_ref'] in nodes and e['destination_ref'] in nodes,'edge endpoint')
            require(set(e['evidence_refs'])<=source_refs,'edge evidence ref')
        if fid in config['priority_route_maps']:
            route=json.loads(gzip.decompress((root/'route_maps'/f'{fid}.json.gz').read_bytes()))
            require(digest({k:v for k,v in route.items() if k!='route_map_hash'})==route['route_map_hash'],'route hash')
            require(route['graph_hash']==g['graph_hash'] and route['edges']==g['edges'] and route['observations']==g['observations'],'complete route')
            require([{k:v for k,v in n.items() if k!='route_capability'} for n in route['nodes']]==g['nodes'],'route nodes')
            require(not route['authorized_write_refs'] and route['eligible_as_repair_input'] is False,'route authority')
        total.update(cover);total.update(observations=len(obs),resolved_observations=len(obs),nodes=len(nodes),edges=len(g['edges']),candidates=c['candidate_count'],old_candidate_records=c['old_candidate_count'])
    require(dict(total)==summary['totals'],'summary totals')
    require(all(v==0 for v in summary['execution'].values()),'unexpected model execution')
    require(len(json.loads((root/'old_candidate_hashes.json').read_bytes()))==summary['old_unique_candidate_hashes']==955,'legacy identities')
    comparison=[json.loads(l) for l in (root/'reference_comparison.jsonl').read_text().splitlines()]
    require(len(comparison)==summary['reference_records']==65,'reference count')
    require(all(r['event_detection_truth_available'] is False for r in comparison),'proxy relabelled as truth')
    return {'status':'PASS','trajectories':84,'totals':dict(total),'manifest_sha256':digest((root/'manifest.json').read_bytes()),
            'validator_sha256':digest(Path(__file__).read_bytes()),'scope':'PERSISTED_GRAPH_INTEGRITY_SOURCE_FIELDS_VERIFIED_DURING_BUILD'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--receipt',type=Path);a=p.parse_args()
    result=validate(a.root)
    if a.receipt:
        if a.receipt.resolve().is_relative_to(a.root.resolve()): raise ValueError('receipt must be outside manifested output')
        a.receipt.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
