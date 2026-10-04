#!/usr/bin/env python3
"""Freeze provider profiles and reproduce explicit MCP phases without a model."""
import argparse
import asyncio
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from stage2.r7_checkpoint_v1.common import digest
from stage2.native_v7.software_host_v1 import TASKS
from stage2.route_repair.branch_fields import require, save, seal, BranchConstraintError
from stage2.route_repair.prefix_context import PrefixMCPContext
from stage2.route_repair.proposal_authority import freeze_task_envelope
from stage2.route_repair.planning_actor import ReadOnlyPlanningActorSession, OfflinePlanningScript
from stage2.route_repair.native_continuation import OfflineScript
from stage2.route_repair.provider_capture import (CONFIG, freeze_provider_bindings, BoundExchangeSource,
                                                   OfflineWireResponses, PlanningRequestAdapter)
from stage2.route_repair.phased_mcp import PhasedPlanningRepairEntry
from stage2.route_repair.checkout_route_probe import probe
from scripts.check_stage2_same_parent_native_mcp import scripted_proposal

FROZEN = ROOT / 'stage2/replication_v2/bound_provider_phase_preflight_v1'


def reply(content): return {'content': json.dumps(content, ensure_ascii=False, sort_keys=True)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['source-root', 'sdk-root', 'protocol-root', 'out']:
        p.add_argument('--'+name, required=True, type=Path)
    p.add_argument('--compare-frozen', action='store_true'); args = p.parse_args()
    require(not args.out.exists(), 'FRESH_BOUND_PROVIDER_PHASE_OUTPUT_REQUIRED')
    active = json.loads((ROOT/'configs/stage2_monitor_repair_active.json').read_bytes())
    require(active['implementation'] == PhasedPlanningRepairEntry.__module__ + '.' + PhasedPlanningRepairEntry.__name__
        and active['provider_config'] == CONFIG and active['phases'] == ['plan_and_repair','release','continue_native']
        and active['legacy_fallback_enabled'] is False and active['live_execution_enabled'] is False,
        'ACTIVE_PHASED_ENTRY_REGISTRY_DRIFT')
    native = json.loads((ROOT / 'configs/stage2_same_parent_native_mcp_v1.json').read_text())
    case = next(c for c in json.loads((ROOT / 'configs/stage2_terminal_route_repair_first_round_v1.json').read_text())['cases']
                if c['full_id'] == native['full_id'])
    context = PrefixMCPContext(args.source_root / 'G3A/stage2/replication_v2/G3/natural_A/X4-T2/first_attempt.tar.gz',
        full_id=case['full_id'], archive_sha256=case['archive_sha256'], parent_checkpoint_hash=native['parent_checkpoint_hash'])
    try:
        bindings = freeze_provider_bindings(context, ROOT)
        save(args.out / 'provider_bindings.json', bindings)
        envelope = freeze_task_envelope(context, TASKS['T2'], writable_refs=['file:' + p for p in context.parent['files']],
            branch_id='bound-provider-phase-engineering', max_actions=native['max_actions'], max_value_bytes=native['max_value_bytes'])
        fixture, proposal, _ = scripted_proposal(context)
        names = {'complete_catalog':'catalog', 'node_context':'node', 'read_file':'file',
                 'observation_source':'observation', 'select_source_witness':'witness'}
        rows = [reply({'kind':'TOOL','name':names[q['operation']], 'arguments':q['request']}) for q in fixture.query_log]
        rows += [reply({'kind':'FINAL','decision':'REPAIR','proposal':proposal})]
        planning = ReadOnlyPlanningActorSession(context, envelope, OfflinePlanningScript(rows), args.out / 'planning',
            actor_id=bindings['profiles']['planning']['actor_id'], max_calls=bindings['profiles']['planning']['max_logical_calls'])
        asyncio.run(planning.run())
        # Check prepared planning encoding against an actual recorded host request.
        # This additional offline exchange did NOT generate the scripted proposal.
        request = json.loads(gzip.decompress((planning.out / 'exchanges/0001-request.json.gz').read_bytes()))
        content = reply({'kind':'FINAL','decision':'UNRESOLVED','reason':'Offline encoding fixture.',
            'inspected_refs':[], 'witness_ids':[], 'unknown_relations':['No actual model diagnosis.']})['content']
        response = json.dumps({'id':'offline-planning-encoding','model':bindings['profiles']['planning']['model_alias'],
            'choices':[{'message':{'role':'assistant','content':content},'finish_reason':'stop'}], 'usage':{}}).encode()
        source = BoundExchangeSource(bindings['profiles']['planning'], OfflineWireResponses([{'status':200,'body':response}]),
            args.out / 'planning_encoding', gate=lambda: True)
        encoded = asyncio.run(PlanningRequestAdapter(source).complete(request))
        require(encoded['content'] == content, 'PLANNING_ENCODING_CHANGED_RESPONSE')
        task = proposal['verification_tasks'][0]
        def verify(root):
            value = probe(root)
            passed = (value['controlled_launcher_selection'] == {'UNSET':['current'],'on':['legacy'],'off':['current']}
                and all(r['status'] == 200 and r['body'] == {'status':'pending_payment','amount_cents':2500,'method':r['method']}
                        for r in value['http_handler_contracts']['current'])
                and all(r['status'] == 410 for r in value['http_handler_contracts']['legacy']))
            return {'passed':passed, 'controlled_probe':value,'scope':'TWO_METHODS_ONE_CART_NOT_BROWSER_OR_REAL_PAYMENT'}
        scripts = [{'content':json.dumps({'actions':[{'type':'read_file','path':'run.py'},
            {'type':'finalize','answer':'Offline phased continuation; no semantic verdict.'}]})}]
        scripts += [{'content':json.dumps({'actions':[{'type':'finalize',
            'answer':'Offline phased continuation; no semantic verdict.'}]})} for _ in range(3)]
        entry = PhasedPlanningRepairEntry(context, planning, bindings, args.out / 'host', repo_root=ROOT)
        asyncio.run(entry.plan_and_repair(script=OfflineScript(scripts),sdk_root=args.sdk_root,protocol_root=args.protocol_root,
            verifiers={task['verification_id']:{**task,'run':verify}}))
        branch = entry._branch
        paused = json.loads((branch.out/'phase_receipt.json').read_text()); save(args.out / 'paused_receipt.json', paused)
        require(paused['scripted_subject_calls'] == 0 and paused['remaining_after'] == 60
            and branch.adapter.save_state(branch.host) == context.parent['state'], 'PAUSED_REPAIR_SPENT_SUBJECT_BUDGET')
        raw = (branch.out / 'full_graph_after.json').read_bytes()
        (args.out / 'paused_graph.json.gz').write_bytes(gzip.compress(raw, mtime=0))
        for operation in ['direct_provider', 'continuation']:
            try:
                if operation == 'direct_provider': branch.source.complete_agent([], {'turn':5})
                else: asyncio.run(branch.continue_native())
            except BranchConstraintError as exc:
                save(args.out / ('blocked_' + operation + '.json'), {'operation':operation,'error':str(exc),
                    'scripted_subject_calls':branch.source.calls,'provider_calls':0,'native_state_unchanged':
                    branch.adapter.save_state(branch.host) == context.parent['state']})
            else: require(False, 'SUBJECT_CALL_BEFORE_HOST_RELEASE')
        require(branch.source.calls == 0, 'BLOCKED_CALL_CONSUMED_SUBJECT_BUDGET')
        release = entry.release(); save(args.out / 'host_release.json', release)
        receipt = asyncio.run(entry.continue_native())
        require(receipt['scripted_subject_calls'] == 4 and receipt['remaining_after'] == 56
            and receipt['native_mcp_invocations'] == 4 and receipt['native_repair_actions'] == 1,
            'PHASED_NATIVE_CONTINUATION_DRIFT')
        after = branch.observer.graph.snapshot()
        require(not any(o['event_kind'] == 'REPAIR_AGENT_EXIT' for o in after['observations']), 'OFFLINE_RELEASE_IS_NOT_REAL_EXIT')
        failures = {}
        for label, status, body in [('http_failure',503,b'{"error":"offline unavailable"}'),
                                  ('malformed_response',200,b'not JSON')]:
            failed = BoundExchangeSource(bindings['profiles']['subject'], OfflineWireResponses([{'status':status,'body':body}]),
                args.out / label, gate=lambda:True)
            try: failed.complete_agent([{'role':'user','content':'Offline failure fixture.'}])
            except Exception as exc:
                require(failed.failed and failed.calls == 1, 'FAILED_EXCHANGE_NOT_RETAINED')
                failures[label] = {'type':type(exc).__name__, 'message':str(exc), 'attempts':failed.calls, 'provider_calls':0}
            else: require(False,'EXPECTED_PROVIDER_FAILURE_NOT_OBSERVED')
        for name in ['full_graph_before.json','full_graph_after.json']:
            path=branch.out/name; (branch.out/(name+'.gz')).write_bytes(gzip.compress(path.read_bytes(),mtime=0))
        summary = seal({'schema':'stage2-bound-provider-phase-preflight-v1', 'provider_calls':0,
            'source_bindings_hash':bindings['bindings_hash'], 'parent_checkpoint_hash':context.parent_checkpoint_hash,
            'planning_profile_calls':16,'subject_profile_calls':60,'planning_encoding_exchange_origin':'OFFLINE_FIXTURE_NOT_DIAGNOSIS',
            'repair_before_release_subject_calls':0, 'after_release_scripted_subject_calls':4,
            'native_mcp_invocations':4,'native_repair_actions':1, 'remaining_before':60,'remaining_after':56,
            'prefix_observations':len(context.graph['observations']),'new_observations':len(after['observations'])-len(context.graph['observations']),
            'negative_provider_cases':failures, 'actual_repair_agent_exit':False,'agent_generated_proposal':False,
            'repair_success':False,'independent_review_invoked':False,'live_trial_ready':False,
            'configured_model_version_is_verified_backend':False,'frozen_natural_experiments_rerun':False,
            'remaining_gates':bindings['remaining_gates']},'summary_hash')
        save(args.out/'summary.json',summary)
        deps=json.loads((ROOT/'stage2/replication_v2/read_only_planning_entry_integration_v1/seal.json').read_text())['implementation_hashes']
        for name in ['stage2/route_repair/provider_capture.py','stage2/route_repair/phased_mcp.py','scripts/check_stage2_provider_phase.py']:
            deps[name]=digest((ROOT/name).read_bytes())
        artifacts={str(p.relative_to(args.out)):digest(p.read_bytes()) for p in sorted(args.out.rglob('*'))
            if p.is_file() and '/native_branch/application/' not in '/'+str(p.relative_to(args.out))
            and '__pycache__' not in p.parts and not p.name.endswith('.pyc')
            and p.name not in {'full_graph_before.json','full_graph_after.json'}}
        sealed=seal({'schema':'stage2-bound-provider-phase-seal-v1','artifact_hashes':artifacts,
            'implementation_hashes':deps,'input_hashes':{name:digest((ROOT/name).read_bytes()) for name in [CONFIG,'configs/stage2_monitor_repair_active.json']},
            'archive_sha256':case['archive_sha256'],'summary_hash':summary['summary_hash']},'seal_hash')
        save(args.out/'seal.json',sealed)
        if args.compare_frozen:
            require(sealed == json.loads((FROZEN/'seal.json').read_text()),'BOUND_PROVIDER_PHASE_SEAL_DRIFT')
            for name,h in artifacts.items():
                require(digest((FROZEN/name).read_bytes())==h and (FROZEN/name).read_bytes()==(args.out/name).read_bytes(),
                    'BOUND_PROVIDER_PHASE_ARTIFACT_DRIFT:'+name)
        print(json.dumps({'sealed_reproduction':args.compare_frozen,'artifacts':len(artifacts),'provider_calls':0,
            'subject_calls_before_release':0,'scripted_subject_calls_after_release':4,'repair_success':False}))
    finally: context.close()


if __name__=='__main__': main()
