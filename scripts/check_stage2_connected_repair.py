#!/usr/bin/env python3
"""Reproduce real loopback HTTP plus unchanged native MCP; zero model calls."""
import argparse
import asyncio
import gzip
import json
import os
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from stage2.r7_checkpoint_v1.common import digest, stable_json_bytes
from stage2.route_repair.branch_fields import require, save, seal, BranchConstraintError
from stage2.route_repair.connected_provider import CONFIG, LoopbackHTTPTransport, ConnectedExchangeSource, freeze_connected_bindings
from stage2.route_repair.connected_planning import ConnectedPlanningSession, freeze_connected_envelope
from stage2.route_repair.connected_mcp import ConnectedPlanningRepairEntry
from stage2.route_repair.http_fixture import FixtureHTTPServer, fixture_reply
from stage2.route_repair.checkout_route_probe import probe
from scripts.check_stage2_same_parent_native_mcp import scripted_proposal
from scripts.run_stage2_connected_repair import load_context, prepare_review

FROZEN = ROOT / 'stage2/replication_v2/connected_http_mcp_preflight_v1'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['source-root','sdk-root','protocol-root','out']: p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--compare-frozen',action='store_true'); args=p.parse_args()
    require(not args.out.exists(),'FRESH_CONNECTED_INTEGRATION_OUTPUT_REQUIRED')
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    active=json.loads((ROOT/'configs/stage2_monitor_repair_active.json').read_bytes())
    require(active['implementation']=='stage2.route_repair.connected_mcp.ConnectedPlanningRepairEntry'
        and active['legacy_fallback_enabled'] is False and active['provider_config']==CONFIG,'CONNECTED_ACTIVE_ENTRY_DRIFT')
    context=load_context(args.source_root)
    try:
        scripted, proposal, _=scripted_proposal(context)
        names={'complete_catalog':'catalog','node_context':'node','read_file':'file','observation_source':'observation','select_source_witness':'witness'}
        contents=[json.dumps({'kind':'TOOL','name':names[q['operation']],'arguments':q['request']},ensure_ascii=False,sort_keys=True)
                  for q in scripted.query_log]
        contents += [json.dumps({'kind':'FINAL','decision':'REPAIR','proposal':proposal},ensure_ascii=False,sort_keys=True)]
        # Four native read turns deliberately keep the queue open. Horizon censor
        # occurs at the fourth returned turn; the fifth role is never popped.
        subject=json.dumps({'actions':[{'type':'read_file','path':'run.py'}]},ensure_ascii=False,sort_keys=True)
        rows=[fixture_reply(c) for c in contents]+[fixture_reply(subject)]*4
        port=json.loads((ROOT/CONFIG).read_bytes())['loopback_fixture_port']
        with FixtureHTTPServer(rows,port=port) as server:
            transport=LoopbackHTTPTransport(server.port); bindings=freeze_connected_bindings(context,ROOT,transport)
            save(args.out/'provider_bindings.json',bindings); save(args.out/'prefix_receipt.json',context.prefix_receipt)
            envelope=freeze_connected_envelope(context,bindings['profiles']['planning']['original_task'],
                writable_refs=['file:'+p for p in context.parent['files']],branch_id='connected-http-native-fixture',max_actions=8,max_value_bytes=65536)
            task=proposal['verification_tasks'][0]; cap={k:v for k,v in task.items() if k!='depends_on'}
            source=ConnectedExchangeSource(bindings['profiles']['planning'],transport,args.out/'planning_http',gate=lambda:True)
            planning=ConnectedPlanningSession(context,envelope,source,args.out/'planning',verification_capabilities=[cap])
            entry=ConnectedPlanningRepairEntry(context,planning,bindings,args.out/'host',repo_root=ROOT,transport=transport)
            def check(root):
                value=probe(root)
                passed=(value['controlled_launcher_selection']=={'UNSET':['current'],'on':['legacy'],'off':['current']}
                    and all(r['status']==200 and r['body']=={'status':'pending_payment','amount_cents':2500,'method':r['method']}
                            for r in value['http_handler_contracts']['current'])
                    and all(r['status']==410 for r in value['http_handler_contracts']['legacy']))
                return {'passed':passed,'controlled_probe':value,'scope':'ENGINEERING_FIXTURE_NOT_SEMANTIC_FINDING'}
            paused=asyncio.run(entry.plan_and_repair(sdk_root=args.sdk_root,protocol_root=args.protocol_root,
                         verifiers={cap['verification_id']:{**cap,'run':check}}))
            branch=entry._branch
            require(branch.source.calls==0 and branch.adapter.save_state(branch.host)==context.parent['state'], 'CONNECTED_PAUSE_SPENT_NATIVE_BUDGET')
            save(args.out/'paused_receipt.json',paused)
            for label,call in [('provider',lambda:branch.source.complete_agent([],{'turn':5})),
                               ('continuation',lambda:asyncio.run(branch.continue_native()))]:
                try: call()
                except BranchConstraintError as exc: save(args.out/('blocked_'+label+'.json'),{'error':str(exc),'subject_calls':branch.source.calls})
                else: require(False,'CONNECTED_PRE_RELEASE_DISPATCH')
            release=entry.release(); save(args.out/'release.json',release)
            result=asyncio.run(entry.continue_native()); save(args.out/'result.json',result)
            require(result['subject_calls']==4 and result['remaining_after']==56 and result['native_ceiling_preserved']
                    and result['native_mcp_invocations']==7 and result['native_repair_actions']==1,'CONNECTED_RETURNED_HORIZON_DRIFT')
            state=branch.adapter.save_state(branch.host)
            require(len(state['history'])==8 and state['max_turns']==64 and state['stop_reason'] is None
                    and list(branch.host.queue) and result['failure'] is None,'CONNECTED_CENSOR_RESET_OR_CONSUMED_NATIVE_STATE')
            require(not any(o['event_kind']=='REPAIR_AGENT_EXIT' for o in branch.observer.graph.snapshot()['observations']), 'LOOPBACK_CANNOT_CERTIFY_ACTUAL_EXIT')
            prepare_review(context,branch)
            expected_requests=[(source.out/f'{i+1:04d}/request.bin').read_bytes() for i in range(len(contents))]
            expected_requests += [(branch.source.source.out/f'{i+1:04d}/request.bin').read_bytes() for i in range(4)]
            require(server.requests==expected_requests and server.position==len(rows),'LOOPBACK_EXACT_REQUEST_MISMATCH')
            save(args.out/'http_socket_receipt.json',{'loopback_exchanges':len(server.requests),'request_hashes':[digest(r) for r in server.requests],
                    'provider_calls':0,'origin':'LOOPBACK_HTTP_FIXTURE','autonomous_semantic_diagnosis':False,'native_wire_storage':'RETAINED_BYTE_SNAPSHOTS_TRANSIENT_PROCESS_LOGS_EXCLUDED'})
        after=branch.observer.graph.snapshot()
        retained_count=0
        for path in (branch.out/'captures').glob('*.json'):
            capture=json.loads(path.read_bytes()); receipt=capture.get('native_receipt') or {}
            if 'wire_member' in receipt:
                require(receipt['wire_member'].startswith('retained_wire/')
                    and digest((branch.out/receipt['wire_member']).read_bytes())==receipt['wire_sha256'], 'RETAINED_NATIVE_WIRE_HASH_DRIFT')
                retained_count+=1
        require(retained_count==21, 'RETAINED_NATIVE_WIRE_STREAM_COUNT_DRIFT')
        for name in ['full_graph_before.json','full_graph_after.json']:
            path=branch.out/name; (branch.out/(name+'.gz')).write_bytes(gzip.compress(path.read_bytes(),mtime=0))
        summary=seal({'schema':'stage2-connected-http-native-preflight-v1','provider_calls':0,
            'origin':'LOOPBACK_HTTP_FIXTURE','planning_http_exchanges':len(contents),'subject_http_exchanges':4,
            'native_mcp_invocations':7,'native_repair_actions':1,'old_observations':len(context.graph['observations']),
            'old_edges':len(context.graph['edges']),'new_observations':len(after['observations'])-len(context.graph['observations']),
            'native_history_before':4,'native_history_after':8,'native_ceiling':64,'remaining_before':60,'remaining_after':56,
            'native_stop_reason':None,'trial_censored':True,'fifth_role_popped':False,
            'actual_repair_agent_exit':False,'agent_generated_proposal':False,'repair_success':False,
            'independent_review_invoked':False,'frozen_natural_experiments_rerun':False},'summary_hash')
        save(args.out/'summary.json',summary)
        deps=json.loads((ROOT/'stage2/replication_v2/bound_provider_phase_preflight_v1/seal.json').read_bytes())['implementation_hashes']
        for name in ['stage2/route_repair/connected_provider.py','stage2/route_repair/connected_planning.py',
            'stage2/route_repair/connected_mcp.py','stage2/route_repair/http_fixture.py',
            'scripts/run_stage2_connected_repair.py','scripts/check_stage2_connected_repair.py']:
            deps[name]=digest((ROOT/name).read_bytes())
        artifacts={str(p.relative_to(args.out)):digest(p.read_bytes()) for p in sorted(args.out.rglob('*'))
            if p.is_file() and '/native_branch/application/' not in '/'+str(p.relative_to(args.out))
            and '/native_branch/native_wire/' not in '/'+str(p.relative_to(args.out))
            and '__pycache__' not in p.parts and not p.name.endswith('.pyc')
            and p.name not in {'full_graph_before.json','full_graph_after.json'}}
        sealed=seal({'schema':'stage2-connected-http-native-seal-v1','artifact_hashes':artifacts,'implementation_hashes':deps,
            'input_hashes':{name:digest((ROOT/name).read_bytes()) for name in [CONFIG,'configs/stage2_monitor_repair_active.json']},
            'archive_sha256':context.case['archive_sha256'],'summary_hash':summary['summary_hash']},'seal_hash')
        save(args.out/'seal.json',sealed)
        if args.compare_frozen:
            require(sealed==json.loads((FROZEN/'seal.json').read_bytes()),'CONNECTED_HTTP_NATIVE_SEAL_DRIFT')
            for name,h in artifacts.items(): require((FROZEN/name).read_bytes()==(args.out/name).read_bytes(),'CONNECTED_ARTIFACT_DRIFT:'+name)
        print(json.dumps({'artifacts':len(artifacts),'sealed_reproduction':args.compare_frozen,**summary}))
    finally: context.close()


if __name__=='__main__': main()
