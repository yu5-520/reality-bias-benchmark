#!/usr/bin/env python3
"""Compile a manual inspected-source proposal; no model or native action runs."""
import argparse
import gzip
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from stage2.native_v7.software_host_v1 import TASKS
from stage2.route_repair.route_context import CompleteRouteContext
from stage2.route_repair.planning_session import RoutePlanningSession
from stage2.route_repair.branch_fields import save,verify_seal
from stage2.r7_checkpoint_v1.common import digest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',required=True,type=Path)
    parser.add_argument('--graph-root',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--compare-frozen',action='store_true')
    args=parser.parse_args()
    if args.out.exists():parser.error('fresh output required')
    case=next(c for c in json.loads((ROOT/'configs/stage2_terminal_route_repair_first_round_v1.json').read_text())['cases'] if c['full_id']=='G3-X4-T2')
    with gzip.open(args.graph_root/'G3-X4-T2.json.gz') as f:graph=json.load(f)['graph']
    archive=args.source_root/'G3A/stage2/replication_v2/G3/natural_A/X4-T2/first_attempt.tar.gz'
    context=CompleteRouteContext(graph,archive,case)
    try:
        session=RoutePlanningSession(context,TASKS['T2'],proposal_origin='OFFLINE_MANUAL')
        catalog=session.catalog()
        first_observation=graph['observations'][0]
        session.observation(first_observation['observation_id'],first_observation['object_refs'][0])
        route=['file:README.md','file:run.py','file:legacy_compat.py','file:checkout_app/server.py',
               'file:web/app.js','file:web/index.html','state:terminal']
        witnesses={}
        for ref in route:
            session.node(ref)
            row=session.current_answer() if ref=='state:terminal' else session.file(ref)
            witnesses[ref]=session.witness(row['read_id'],0,len(row['text']))['witness_id']
        historical=[]
        for cp in ['15059da235ce30077c06569fdc8c3f679fb1414350d205cdccce554e7b4d6f10',
                   '65bbbea4635fab7c2f3da7f3b84c7e5af3a2825086347d1708a1b0a979a4999b']:
            row=session.file('file:web/app.js',cp)
            historical.append(session.witness(row['read_id'],0,len(row['text']))['witness_id'])
        # Reuse only the explicitly manual engineering policies, never audit verdicts.
        prior=ROOT/'stage2/replication_v2/source_based_host_branch_integration_v1'
        app_plan=json.loads((prior/'plan.json').read_text())
        combined=json.loads((prior/'combined_plan.json').read_text())
        app_action={**app_plan['actions'][0],'diagnosis_ids':['conditional-alternate-launch']}
        host_policy=combined['host_answer_policy']
        proposal={'schema':'stage2-complete-route-proposal-v1','original_task':TASKS['T2'],
            'graph_hash':graph['graph_hash'],'archive_sha256':case['archive_sha256'],
            'parent_checkpoint_hash':case['terminal_checkpoint_hash'],'route_refs':route,
            'modify_refs':['file:run.py','state:terminal'],
            'preserve_refs':[r for r in route if r not in {'file:run.py','state:terminal'}], 'verify_refs':[],
            'diagnoses':[
                {'claim_id':'conditional-alternate-launch','source_ref':'file:run.py','destination_ref':'file:legacy_compat.py',
                 'status':'SOURCE_BOUND_CLAIM','adoption_status':'UNKNOWN',
                 'meaning_before':'An unset compatibility variable selects legacy in the alternate launcher.',
                 'meaning_after':'The selected legacy handler rejects POST requests.',
                 'authority_effect':'A conditional launch choice can route checkout requests to the retired handler.',
                 'limitation':'Original historical launcher/environment use is not established; the documented primary route works.',
                 'witness_ids':[witnesses['file:run.py'],witnesses['file:legacy_compat.py']]},
                {'claim_id':'captured-change-vs-current-account','source_ref':'file:web/app.js','destination_ref':'state:terminal',
                 'status':'CANDIDATE','adoption_status':'NOT_ESTABLISHED',
                 'meaning_before':'Captured frontend versions show a payment form request added.',
                 'meaning_after':'The current terminal answer says no code changes were required.',
                 'authority_effect':'The completion account could affect later acceptance; adoption is not demonstrated.',
                 'limitation':'Exact source spans support a discrepancy; they do not prove causal or semantic adoption.',
                 'witness_ids':[witnesses['state:terminal'],witnesses['file:web/app.js'],*historical]}],
            'unknown_relations':['Original historical alternate-launcher use is unknown.','Downstream account adoption is unknown.'],
            'application_actions':[app_action],
            'verification_tasks':[{'verification_id':'VERIFY_CONTROLLED_ROUTE','operation':'HOST_DEFINED_OFFLINE_CHECK',
                'refs':['file:run.py','file:checkout_app/server.py','file:legacy_compat.py'],
                'depends_on':['alternate_default_route'],'postcondition':combined['expected_postconditions']}],
            'host_answer':{'field_path':'/answer','value':host_policy['value'],
                'depends_on':host_policy['depends_on'],'diagnosis_ids':['captured-change-vs-current-account']},
            'execution_order':combined['execution_order'],'expected_postconditions':combined['expected_postconditions']}
        bundle=session.compile(proposal,trusted_application_policy=app_plan['policy'],trusted_host_policy=host_policy)
        args.out.mkdir(parents=True)
        save(args.out/'planning_bundle.json',bundle)
        (args.out/'complete_catalog.json.gz').write_bytes(gzip.compress(json.dumps(catalog,sort_keys=True,indent=2).encode(),mtime=0))
        receipt={'schema':'stage2-route-planning-session-check-v1','classification':'OFFLINE_MANUAL_PROPOSAL_COMPILATION_NOT_AGENT_EVALUATION',
            'full_id':case['full_id'],'all_graph_nodes_available':len(graph['nodes']),'selected_route_nodes':len(route),
            'inspected_queries':len(session.query_log),'exact_source_witnesses':len(session.witnesses),
            'compiled_application_actions':len(bundle['application_plan']['actions']),
            'compiled_host_answer_fields':['/answer'],'bundle_hash':bundle['bundle_hash'],
            'native_actions_executed':0,'live_provider_calls':0,'semantic_diagnosis_adjudicated':False,
            'repair_agent_generated':False,'verification_tasks_executed':False,'live_execution_ready':False}
        save(args.out/'planning_receipt.json',receipt)
        if args.compare_frozen:
            frozen=ROOT/'stage2/replication_v2/route_planning_session_integration_v1'
            sealed=json.loads((frozen/'seal.json').read_text());verify_seal(sealed,'seal_hash')
            for path,expected in sealed['implementation_hashes'].items():assert digest((ROOT/path).read_bytes())==expected,path
            for path,expected in sealed['input_hashes'].items():assert digest((ROOT/path).read_bytes())==expected,path
            for path,expected in sealed['artifact_hashes'].items():
                assert digest((frozen/path).read_bytes())==expected,path
                assert (args.out/path).read_bytes()==(frozen/path).read_bytes(),path
        print(json.dumps({**receipt,'sealed_reproduction':args.compare_frozen}))
    finally:context.close()


if __name__=='__main__':main()
