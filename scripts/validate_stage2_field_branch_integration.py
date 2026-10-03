#!/usr/bin/env python3
"""Verify sealed mechanical integration, full graph preservation and raw captures."""
import argparse
import gzip
import json
import sys
import tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from stage2.r7_checkpoint_v1.common import digest
from stage2.monitor_enhancement.snapshot_append import AppendOnlyEvidenceGraph
from stage2.route_repair.branch_fields import verify_seal


def validate(root):
    seal=json.loads((root/'seal.json').read_text())
    verify_seal(seal,'seal_hash')
    for path,expected in seal['artifact_hashes'].items():
        assert digest((root/path).read_bytes())==expected, path
    for path,expected in seal['implementation_hashes'].items():
        assert digest((ROOT/path).read_bytes())==expected, path
    receipt=json.loads((root/'integration_receipt.json').read_text())
    graphs={phase:json.loads(gzip.decompress((root/('full_graph_'+phase+'.json.gz')).read_bytes())) for phase in ['before','after']}
    for graph in graphs.values():
        assert AppendOnlyEvidenceGraph.from_snapshot(graph).snapshot()==graph
    before,after=graphs['before'],graphs['after']
    old_observations={o['observation_id']:o for o in before['observations']}
    new_observations={o['observation_id']:o for o in after['observations']}
    old_edges={o['edge_id']:o for o in before['edges']}
    new_edges={o['edge_id']:o for o in after['edges']}
    assert all(new_observations.get(k)==v for k,v in old_observations.items())
    assert all(new_edges.get(k)==v for k,v in old_edges.items())
    assert {n['ref'] for n in before['nodes']} <= {n['ref'] for n in after['nodes']}
    added=[o for k,o in new_observations.items() if k not in old_observations]
    with tarfile.open(root/'native_capture_bundle.tar.gz','r:gz') as archive:
        for observation in added:
            locator=observation['source_locator']
            raw=archive.extractfile(locator['member']).read()
            assert digest(raw)==locator['member_sha256']
            content=json.loads(raw)['content']
            assert digest(content.encode())==observation['content_hash']
    assert receipt['classification']=='OFFLINE_MECHANICAL_INTEGRATION_NOT_SEMANTIC_REPAIR'
    assert receipt['live_provider_calls']==0 and receipt['native_write_attempts']==2
    assert receipt['semantic_repair_effect']=='NOT_EVALUATED'
    assert not receipt['native_agent_continuation_executed'] and not receipt['branch_promoted']
    assert receipt['unrelated_application_preserved'] and receipt['historical_archive_preserved']
    assert before['graph_hash']==receipt['graph_comparison']['before_graph_hash']
    assert after['graph_hash']==receipt['graph_comparison']['after_graph_hash']
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT/'stage2/replication_v2/field_branch_native_integration_v1')
    parser.add_argument('--reproduced',type=Path)
    args=parser.parse_args()
    receipt=validate(args.root)
    if args.reproduced:
        repeated=json.loads((args.reproduced/'integration_receipt.json').read_text())
        assert repeated==receipt, 'independent integration receipt differs'
        for phase in ['before','after']:
            repeated_graph=json.loads((args.reproduced/('full_graph_'+phase+'.json')).read_text())
            frozen_graph=json.loads(gzip.decompress((args.root/('full_graph_'+phase+'.json.gz')).read_bytes()))
            assert repeated_graph==frozen_graph, 'independent graph differs'
    print(json.dumps({'status':'PASS_SEALED_OFFLINE_NATIVE_INTEGRATION','provider_calls':0,
        'native_fixture_writes':2,'semantic_repair_effect':'NOT_EVALUATED',
        'complete_graphs_and_capture_sources_verified':True,'independent_reproduction':bool(args.reproduced)}))


if __name__=='__main__':
    main()
