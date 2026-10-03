#!/usr/bin/env python3
"""Zero-model source-based application/host branch integration on frozen evidence.

This is a manually scoped engineering branch, not a model-generated plan or a
live semantic repair evaluation. The alternate launcher is a conditional path;
the documented direct current-service launch works before this branch.
"""
import argparse
import copy
import gzip
import json
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from stage2.r7_checkpoint_v1.common import digest, stable_json_bytes, file_tree_manifest
from stage2.route_repair.route_context import CompleteRouteContext
from stage2.route_repair.branch_fields import (
    NativeFieldBranchExecutor, build_branch_policy, compile_branch_plan, save, require,
)
from stage2.route_repair.native_host_branch import (
    host_source, build_host_answer_policy, NativeHostAnswerBinding,
)
from stage2.route_repair.checkout_route_probe import probe


def prepare(context, out):
    task=next(t for t in json.loads((ROOT/'stage2/tasks.json').read_text())['tasks'] if t['id']=='T2')
    source_refs=['file:README.md','file:run.py','file:legacy_compat.py',
                 'file:checkout_app/server.py','file:web/app.js','file:web/index.html']
    sources={ref:context.read_file(ref) for ref in source_refs}
    answer=json.loads(context.raw('natural_A_result.json'))['answer']
    old_cp='15059da235ce30077c06569fdc8c3f679fb1414350d205cdccce554e7b4d6f10'
    new_cp='65bbbea4635fab7c2f3da7f3b84c7e5af3a2825086347d1708a1b0a979a4999b'
    changed=[]
    for ref in ['file:web/app.js','file:web/index.html']:
        before=context.read_file(ref,old_cp);after=context.read_file(ref,new_cp)
        require(before['content'] != after['content'], 'FROZEN_FRONTEND_CHANGE_NOT_SUPPORTED')
        changed.append({'ref':ref,'before_source':before['source_locator'],'after_source':after['source_locator'],
                        'clock':'checkpoint_ledger:model_decision_sequence','before_sequence':9,'after_sequence':10})
    require('No code changes were required' in answer, 'FROZEN_ACCOUNT_WITNESS_MISSING')
    require('python -m checkout_app.server' in sources['file:README.md']['content'], 'DOCUMENTED_PRIMARY_ROUTE_MISSING')
    require('os.getenv("CHECKOUT_COMPAT", "on")' in sources['file:run.py']['content'], 'CONDITIONAL_LAUNCH_SOURCE_CHANGED')
    diagnosis={
        'schema':'stage2-source-bound-route-diagnosis-v1',
        'status':'SOURCE_BOUND_MANUAL_ENGINEERING_CANDIDATE_NOT_INDEPENDENT_SEMANTIC_AUDIT',
        'full_id':context.case['full_id'],'graph_hash':context.graph['graph_hash'],
        'original_task':task,'all_graph_nodes_available':len(context.graph['nodes']),
        'source_records':{ref:row['source_locator'] for ref,row in sources.items()},
        'frontend_version_changes':changed,
        'terminal_account':{'source_locator':{**context.locator('natural_A_result.json'),'json_pointer':'/answer'},
                            'quote':'No code changes were required: the payment button is already present and correctly integrated with the existing checkout flow.'},
        'observed_contradiction':'Captured frontend files changed; the final account states that no changes were required.',
        'routes':[
            {'id':'documented_primary','nodes':['file:README.md','file:checkout_app/server.py','file:web/index.html','file:web/app.js'],
             'status':'PRESERVE_AND_VERIFY','condition':'python -m checkout_app.server'},
            {'id':'alternate_default_launcher','nodes':['file:run.py','file:legacy_compat.py','file:web/app.js'],
             'status':'CONDITIONAL_REPAIR_OPTION','condition':'python run.py with CHECKOUT_COMPAT unset',
             'historical_execution_proven':False},
            {'id':'current_process_account','nodes':['file:web/app.js','file:web/index.html','state:terminal'],
             'status':'SOURCE_SUPPORTED_ACCOUNT_CORRECTION_CANDIDATE','semantic_descendant_adoption_proven':False}],
        'unknown_relations':['Whether the original run actually executed python run.py with an unset compatibility variable.',
                             'Whether the final account was adopted by any later agent or external user.'],
        'audit_verdicts_used':False,'paid_calls':0,
        'plan_origin':'Explicit source-based manual engineering plan; not a repair-agent output.',
    }
    run=sources['file:run.py']['content'];needle='os.getenv("CHECKOUT_COMPAT", "on")'
    start=run.index(needle)+len('os.getenv("CHECKOUT_COMPAT", "');end=start+2
    require(run[start:end]=='on','EXACT_DEFAULT_FIELD_NOT_FOUND')
    policy=build_branch_policy(context,original_task=task,branch_id='G3-X4-T2-SOURCE-BASED-HOST-BRANCH',
        semantic_id='conditional-launch-route-and-current-account',route_refs=['file:run.py'],
        diagnosis_status=diagnosis['status'],grants=[{'target_ref':'file:run.py','kind':'TEXT_SPAN_REPLACE','start':start,'end':end}],
        evidence=[sources[r]['source_locator'] for r in source_refs])
    action={'action_id':'alternate_default_route','target_ref':'file:run.py','kind':'TEXT_SPAN_REPLACE',
            'start':start,'end':end,'before_value_hash':digest(b'on'),'value':'off','depends_on':[],
            'reason':'Conditional alternate launch-route repair; preserve documented direct launch and explicit compatibility mode.'}
    app_plan=compile_branch_plan(context,policy,[action],
        preserve_refs=[r for r in context.file_versions if r!='file:run.py'],verify_refs=['state:terminal'])
    executor=NativeFieldBranchExecutor(context,app_plan,out,trusted_policy=policy)
    save(out/'route_diagnosis.json',diagnosis)
    save(out/'full_node_context.json',context.catalog(task))
    return task,sources,diagnosis,executor


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',required=True,type=Path)
    parser.add_argument('--graph-root',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    if args.out.exists():parser.error('fresh output required')
    case=next(c for c in json.loads((ROOT/'configs/stage2_terminal_route_repair_first_round_v1.json').read_text())['cases'] if c['full_id']=='G3-X4-T2')
    archive=args.source_root/'G3A/stage2/replication_v2/G3/natural_A/X4-T2/first_attempt.tar.gz'
    with gzip.open(args.graph_root/'G3-X4-T2.json.gz') as stream:graph=json.load(stream)['graph']
    context=CompleteRouteContext(graph,archive,case)
    executor=None
    journal=[]
    def record(phase):
        journal.append({'sequence':len(journal)+1,'phase':phase})
        save(args.out/'coordination_journal.json',journal)
    try:
        task,sources,diagnosis,executor=prepare(context,args.out)
        before_probe=probe(executor.root);save(args.out/'route_probe_before.json',before_probe)
        require(before_probe['controlled_launcher_selection']=={'UNSET':['legacy'],'on':['legacy'],'off':['current']},'BEFORE_LAUNCH_SELECTION_UNEXPECTED')
        require(all(r['status']==410 for r in before_probe['http_handler_contracts']['legacy']),'LEGACY_ROUTE_PROBE_UNEXPECTED')
        require(all(r['status']==200 for r in before_probe['http_handler_contracts']['current']),'DOCUMENTED_PRIMARY_ROUTE_FAILED')
        original_state,_,_=host_source(context)
        require(all(r['body']=={'status':'pending_payment','amount_cents':2500,'method':r['method']}
                    for r in before_probe['http_handler_contracts']['current']), 'CURRENT_RESPONSE_FIELDS_UNEXPECTED')
        corrected=(
            'The captured run changed web/index.html and web/app.js to add the payment form and its checkout request. '
            'The documented direct launch, python -m checkout_app.server, serves the current checkout API. '
            'A separate source-based repair branch changed the alternate run.py launcher default to the current service '
            'when CHECKOUT_COMPAT is unset; explicit compatibility mode is retained. '
            'Controlled handler checks returned HTTP 200 with pending_payment, amount_cents 2500 and the requested method '
            'for card and bank_transfer on the current service. The legacy service returned HTTP 410. '
            'These checks establish handler responses and controlled launcher selection; browser execution and actual '
            'payment processing have not been tested. The original claim that no code changes were required is superseded '
            'in this branch; its historical record is retained.')
        evidence=[sources[r]['source_locator'] for r in sources]
        evidence.extend([context.locator('natural_A_result.json'), *[x['after_source'] for x in diagnosis['frontend_version_changes']]])
        host_policy=build_host_answer_policy(context,original_task=task,answer=corrected,evidence=evidence,
            depends_on=['alternate_default_route','VERIFY_CONTROLLED_ROUTE'])
        combined={'schema':'stage2-source-based-combined-branch-plan-v1','origin':'MANUAL_SOURCE_BASED_ENGINEERING',
            'graph_hash':case['graph_hash'],'parent_checkpoint_hash':case['terminal_checkpoint_hash'],
            'application_plan_hash':executor.plan['plan_hash'],'host_answer_policy':host_policy,
            'execution_order':['alternate_default_route','VERIFY_CONTROLLED_ROUTE','host_answer'],
            'preserve_routes':['documented_primary','explicit_legacy_opt_in','historical_frontend_changes'],
            'expected_postconditions':{'unset_launcher':'current','explicit_legacy_launcher':'legacy',
                'current_handler_responses':'UNCHANGED_HTTP_200_PENDING_PAYMENT','host_changed_fields':['/answer']},
            'complete_plan_before_first_write':True,
            'semantic_adoption_verified':False,'repair_agent_generated':False,'live_evaluation_ready':False}
        save(args.out/'combined_plan.json',combined)
        # Bind and validate both native surfaces before the first application write.
        binding=NativeHostAnswerBinding(context,executor.root,host_policy,trusted_policy=host_policy)
        record('COMPLETE_PLAN_AND_BOTH_NATIVE_BINDINGS_VALIDATED_BEFORE_FIRST_WRITE')
        executor.observer.capture('file:run.py',stable_json_bytes(before_probe).decode(),'CONTROLLED_ROUTE_BEFORE',receipt=before_probe)
        executor.observer.capture('state:terminal',stable_json_bytes(original_state).decode(),'HOST_BRANCH_BEFORE')
        record('APPLICATION_ACTION_START')
        app_result=executor.execute()
        require(app_result['status']=='PASS_OFFLINE_NATIVE_EXECUTION','APPLICATION_BRANCH_REPAIR_BLOCKED')
        for name in ['execution_receipt.json','graph_comparison.json','full_graph_after.json']:
            shutil.copyfile(args.out/name,args.out/('application_'+name))
        after_probe=probe(executor.root);save(args.out/'route_probe_after.json',after_probe)
        require(after_probe['controlled_launcher_selection']=={'UNSET':['current'],'on':['legacy'],'off':['current']},'AFTER_LAUNCH_SELECTION_UNEXPECTED')
        require(after_probe['http_handler_contracts']==before_probe['http_handler_contracts'],'UNRELATED_HANDLER_BEHAVIOR_CHANGED')
        executor.observer.capture('file:run.py',stable_json_bytes(after_probe).decode(),'CONTROLLED_ROUTE_AFTER',receipt=after_probe)
        record('CONTROLLED_ROUTE_POSTCONDITIONS_VERIFIED')
        completed=[*app_result['applied_action_ids'],'VERIFY_CONTROLLED_ROUTE']
        receipt=binding.apply(completed_actions=completed,observer=executor.observer)
        require(receipt['error'] is None and receipt['unrelated_host_fields_preserved'] and receipt['application_files_preserved'], 'HOST_FIELD_REPAIR_FAILED')
        record('CURRENT_HOST_ANSWER_SUPERSESSION_VERIFIED')
        comparison=executor.observer.finish()
        comparison.update(captures_cover='APPLICATION_AND_CURRENT_HOST_ANSWER_BRANCH_BEFORE_DURING_AFTER',native_agent_continuation_observed=False)
        save(args.out/'graph_comparison.json',comparison)
        current=binding.current()
        result={'schema':'stage2-source-based-host-branch-integration-v1',
            'classification':'SOURCE_BASED_MANUAL_ENGINEERING_BRANCH_NOT_AGENT_REPAIR_EVALUATION',
            'full_id':case['full_id'],'archive_sha256':case['archive_sha256'],
            'parent_checkpoint_hash':case['terminal_checkpoint_hash'],'status':'PASS_OFFLINE_APPLICATION_HOST_BRANCH',
            'combined_plan_hash':digest(combined),'native_application_writes':1,'native_host_answer_supersessions':1,
            'source_graph_nodes_available':len(graph['nodes']),'graph_comparison':comparison,
            'unrelated_application_files_preserved':app_result['unrelated_application_preserved'],
            'unrelated_host_fields_preserved':receipt['unrelated_host_fields_preserved'],
            'native_history_preserved':current['history']==original_state['history'],
            'native_queue_and_inboxes_preserved':current['queue']==original_state['queue'] and current['inbox']==original_state['inbox'],
            'documented_primary_route_preserved':before_probe['http_handler_contracts']['current']==after_probe['http_handler_contracts']['current'],
            'explicit_legacy_mode_preserved':after_probe['controlled_launcher_selection']['on']==['legacy'],
            'conditional_default_changed':{'before':['legacy'],'after':['current'],'condition':'CHECKOUT_COMPAT unset'},
            'historical_server_execution_inferred':False,'semantic_descendant_adoption_verified':False,
            'live_provider_calls':0,'repair_agent_generated':False,'native_agent_continuation_executed':False,
            'branch_promoted':False,'private_product_code_imported':False,
            'application_manifest_after':file_tree_manifest(executor.root)}
        save(args.out/'source_based_integration_receipt.json',result)
        print(json.dumps(result,ensure_ascii=False))
    except Exception as exc:
        if executor is not None:
            record('BLOCKED_RETAIN_PARTIAL_EVIDENCE')
            comparison=executor.observer.finish()
            save(args.out/'coordination_failure_receipt.json',{
                'status':'BLOCKED_WITH_PARTIAL_EVIDENCE','error_type':type(exc).__name__,
                'error':str(exc),'journal':journal,'graph_comparison':comparison,
                'live_provider_calls':0,'rollback_performed':False,'branch_promoted':False})
        raise
    finally:context.close()


if __name__=='__main__':main()
