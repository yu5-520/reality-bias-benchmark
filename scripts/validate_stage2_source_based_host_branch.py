#!/usr/bin/env python3
"""Validate source-based manual branch receipts; never score agent efficacy."""
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


def validate(root, reproduced=None):
    sealed=json.loads((root/'seal.json').read_text())
    verify_seal(sealed,'seal_hash')
    for path,expected in sealed['artifact_hashes'].items():
        assert digest((root/path).read_bytes())==expected,path
    for path,expected in sealed['implementation_hashes'].items():
        assert digest((ROOT/path).read_bytes())==expected,path
    read=lambda name:json.loads((root/name).read_text())
    result=read('source_based_integration_receipt.json')
    assert result['classification']=='SOURCE_BASED_MANUAL_ENGINEERING_BRANCH_NOT_AGENT_REPAIR_EVALUATION'
    assert result['status']=='PASS_OFFLINE_APPLICATION_HOST_BRANCH'
    assert result['native_application_writes']==result['native_host_answer_supersessions']==1
    assert result['live_provider_calls']==0
    for key in ['repair_agent_generated','historical_server_execution_inferred',
                'semantic_descendant_adoption_verified','native_agent_continuation_executed','branch_promoted']:
        assert result[key] is False,key
    for key in ['unrelated_application_files_preserved','unrelated_host_fields_preserved',
                'native_history_preserved','native_queue_and_inboxes_preserved',
                'documented_primary_route_preserved','explicit_legacy_mode_preserved']:
        assert result[key] is True,key
    plan=read('combined_plan.json')
    assert digest(plan)==result['combined_plan_hash']
    assert plan['complete_plan_before_first_write'] is True
    assert plan['execution_order']==['alternate_default_route','VERIFY_CONTROLLED_ROUTE','host_answer']
    phases=[row['phase'] for row in read('coordination_journal.json')]
    assert phases==['COMPLETE_PLAN_AND_BOTH_NATIVE_BINDINGS_VALIDATED_BEFORE_FIRST_WRITE',
        'APPLICATION_ACTION_START','CONTROLLED_ROUTE_POSTCONDITIONS_VERIFIED',
        'CURRENT_HOST_ANSWER_SUPERSESSION_VERIFIED']
    policy=plan['host_answer_policy'];verify_seal(policy,'policy_hash')
    assert policy['field_path']=='/answer' and policy['target_ref']=='state:terminal'
    tasks=json.loads((ROOT/'stage2/tasks.json').read_text())['tasks']
    assert policy['original_task']==next(t for t in tasks if t['id']=='T2')
    diagnosis=read('route_diagnosis.json')
    assert not diagnosis['audit_verdicts_used'] and len(diagnosis['unknown_relations'])==2
    assert [r['status'] for r in diagnosis['routes']]==[
        'PRESERVE_AND_VERIFY','CONDITIONAL_REPAIR_OPTION','SOURCE_SUPPORTED_ACCOUNT_CORRECTION_CANDIDATE']
    before_probe,after_probe=read('route_probe_before.json'),read('route_probe_after.json')
    assert before_probe['controlled_launcher_selection']=={'UNSET':['legacy'],'on':['legacy'],'off':['current']}
    assert after_probe['controlled_launcher_selection']=={'UNSET':['current'],'on':['legacy'],'off':['current']}
    assert before_probe['http_handler_contracts']==after_probe['http_handler_contracts']
    for row in after_probe['http_handler_contracts']['current']:
        assert row['status']==200 and row['body']=={'status':'pending_payment','amount_cents':2500,'method':row['method']}
    assert all(r['status']==410 for r in after_probe['http_handler_contracts']['legacy'])
    graphs={p:json.loads(gzip.decompress((root/('full_graph_'+p+'.json.gz')).read_bytes())) for p in ['before','after']}
    for graph in graphs.values():assert AppendOnlyEvidenceGraph.from_snapshot(graph).snapshot()==graph
    before,after=graphs['before'],graphs['after']
    observations={o['observation_id']:o for o in after['observations']}
    edges={e['edge_id']:e for e in after['edges']}
    assert all(observations.get(o['observation_id'])==o for o in before['observations'])
    assert all(edges.get(e['edge_id'])==e for e in before['edges'])
    assert {n['ref'] for n in before['nodes']} <= {n['ref'] for n in after['nodes']}
    old={o['observation_id'] for o in before['observations']}
    added=[o for o in after['observations'] if o['observation_id'] not in old]
    captured=[]
    with tarfile.open(root/'native_capture_bundle.tar.gz','r:gz') as archive:
        for observation in added:
            locator=observation['source_locator'];raw=archive.extractfile(locator['member']).read()
            assert digest(raw)==locator['member_sha256']
            capture=json.loads(raw);captured.append(capture)
            assert digest(capture['content'].encode())==observation['content_hash']
        assert json.loads(archive.extractfile('intents/host_answer.json').read())['policy_hash']==policy['policy_hash']
    original=json.loads(next(c['content'] for c in captured if c['phase']=='HOST_BRANCH_BEFORE'))
    updated=read('native_host_state_after.json')
    assert {k:v for k,v in original.items() if k!='answer'}=={k:v for k,v in updated.items() if k!='answer'}
    assert updated['answer']==policy['value'] and digest(updated)==policy['after_state_hash']
    assert digest(original)==policy['before_state_hash']
    before_run=next(c['content'] for c in captured if c['ref']=='file:run.py' and c['phase']=='BRANCH_BEFORE')
    after_run=next(c['content'] for c in captured if c['ref']=='file:run.py' and c['phase']=='BRANCH_AFTER')
    assert after_run==before_run.replace('os.getenv("CHECKOUT_COMPAT", "on")','os.getenv("CHECKOUT_COMPAT", "off")',1)
    native=read('native_host_action_receipt.json')
    assert native['error'] is None and native['after_hash']==digest(updated)
    for phase in ['before','after']:
        assert graphs[phase]['graph_hash']==result['graph_comparison'][phase+'_graph_hash']
    assert len(added)==result['graph_comparison']['new_observations']==31
    if reproduced:
        # Compare exact deterministic native receipts, plan, diagnosis and full graphs.
        for path in sealed['artifact_hashes']:
            if path.endswith('.json'):assert json.loads((reproduced/path).read_text())==read(path),path
        for phase in ['before','after']:
            assert json.loads((reproduced/('full_graph_'+phase+'.json')).read_text())==graphs[phase],phase
        with tarfile.open(root/'native_capture_bundle.tar.gz','r:gz') as archive:
            for member in archive.getmembers():
                if member.isfile():assert (reproduced/member.name).read_bytes()==archive.extractfile(member).read(),member.name
    return {'status':'PASS_SEALED_SOURCE_BASED_NATIVE_BRANCH','provider_calls':0,
        'application_writes':1,'current_host_answer_supersessions':1,
        'full_graph_and_raw_capture_sources_verified':True,'independent_reproduction':bool(reproduced),
        'semantic_repair_effect':'NOT_EVALUATED','agent_generated_repair':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT/'stage2/replication_v2/source_based_host_branch_integration_v1')
    parser.add_argument('--reproduced',type=Path)
    args=parser.parse_args()
    print(json.dumps(validate(args.root,args.reproduced)))
