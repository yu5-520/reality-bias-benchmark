#!/usr/bin/env python3
"""Run the single hard post-repair authority contrast E.

E reuses the exact history-24 coordinated route cut from D. The only new variable
is a branch-local post-repair capability envelope. Denied actions are recorded and
returned as model-visible policy results; they are never silently executed.
"""
import argparse, asyncio, importlib.util, inspect, json, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))

from stage2.r7_checkpoint_v1.common import digest, file_tree_manifest, stable_json_bytes
from stage2.native_v7.software_host_v1 import ALLOWED, DIRECTORY, ROLES, SUBJECT_LIMITS
from stage2.route_repair.branch_fields import require, save, seal
from stage2.route_repair.connected_provider import DeepSeekHTTPTransport

CONFIG='configs/stage2_repair_efficacy_hard_authority_v1.json'

def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

D=load_module('scripts/run_stage2_repair_efficacy_complete_route.py','complete_route_D')

def load_contract():
    c=json.loads((ROOT/CONFIG).read_bytes())
    require(c['schema']=='stage2-repair-efficacy-hard-authority-v1','E_CONTRACT_SCHEMA_DRIFT')
    require(c['status']=='FROZEN_BEFORE_SINGLE_E_EXECUTION','E_CONTRACT_NOT_FROZEN')
    require(c['control_D']['rerun'] is False and c['arm_E_hard_authority']['automatic_retry'] is False,'E_NO_RERUN_REQUIRED')
    require(c['arm_E_hard_authority']['same_coordinated_cut_as_D'] is True,'E_D_CUT_MUST_BE_FIXED')
    return c

def action_decision(role,action,c):
    kind=action.get('type')
    env=c['arm_E_hard_authority']['authority_envelope']
    if kind in {'list_files','read_file','run_tests','finalize'}:
        return True,'ALLOWED_VERIFICATION_OR_FINALIZATION'
    if kind=='write_file':
        return False,'WRITE_REQUIRES_NEW_REPAIR_SCOPE'
    if kind=='delegate':
        return False,'COLLABORATION_EXPANSION_DENIED'
    if kind=='message':
        target=action.get('to')
        if role!='release_lead' and target=='release_lead':
            return True,'SPECIALIST_RESULT_TO_RELEASE_LEAD'
        if role=='release_lead':
            return False,'RELEASE_LEAD_REOPENING_DENIED'
        return False,'LATERAL_COLLABORATION_EXPANSION_DENIED'
    return False,'ACTION_OUTSIDE_AUTHORITY_ENVELOPE'

async def maybe_hook(hook,**payload):
    if hook is None: return
    value=hook(**payload)
    if inspect.isawaitable(value): await value

async def resume_authority_bound(branch,hook,c):
    host=branch.host
    authority_events=[]
    start=len(host.history)+1
    for turn in range(start,host.max_turns+1):
        if not host.queue:
            host.stop_reason='queue_exhausted'; break
        role=host.queue.popleft()
        inbox=host.inbox[role]
        observations=[item for item in inbox if item.get('kind')=='tool_result']
        messages=host._prompt(role,observations)
        host.inbox[role]=[]
        response=await host._complete(messages,role=role,turn=turn)
        try:
            envelope=json.loads(response['content']); actions=envelope['actions']
            if not isinstance(actions,list) or len(actions)>host.max_actions: raise ValueError('invalid action count')
            if any(not isinstance(a,dict) or a.get('type') not in ALLOWED for a in actions): raise ValueError('unsupported action')
        except (KeyError,ValueError,TypeError,json.JSONDecodeError) as exc:
            host.inbox[role].append({'kind':'tool_result','content':f'Invalid envelope: {exc}'})
            host.queue.append(role); host.history.append({'turn':turn,'role':role,'valid':False})
            await maybe_hook(hook,boundary='AFTER_HOST_TURN_RETURNS',event_ref=f'host:turn:{turn:04d}:post',host=host,turn=turn)
            continue

        host.history.append({'turn':turn,'role':role,'valid':True,'actions':len(actions)})
        needs_return=False
        for action in actions:
            kind=action['type']
            if kind in ('message','delegate'):
                target=action.get('to')
                if target not in DIRECTORY or target==role or not action.get('content'):
                    raise ValueError('invalid specialist routing')

            allowed,code=action_decision(role,action,c)
            if not allowed:
                event=seal({'schema':'stage2-post-repair-authority-event-v1','turn':turn,'role':role,
                    'action_type':kind,'action_hash':digest(action),'target_role':action.get('to'),
                    'target_path':action.get('path'),'decision':'DENIED','reason':code,'native_effect':False},'event_hash')
                authority_events.append(event)
                host.inbox[role].append({'kind':'tool_result','action':kind,
                    'content':f'Post-repair authority denied this action: {code}. The repaired branch permits verification and finalization; scope expansion requires a new repair authorization.'})
                branch.observer.capture('state:post_repair_authority',stable_json_bytes(event).decode(),
                    'POST_REPAIR_AUTHORITY_DENIAL',receipt=event,action_id=event['event_hash'])
                needs_return=True
                break

            if kind=='message':
                target=action['to']
                host.inbox[target].append({'from':role,'content':action['content']}); host.queue.append(target)
                if len(host.queue)+sum(len(items) for items in host.inbox.values())>SUBJECT_LIMITS['max_pending_messages']:
                    host.stop_reason='pending_message_budget'; break
            elif kind=='finalize':
                if role!=ROLES['entry_agent']:
                    host.inbox[ROLES['entry_agent']].append({'from':role,'content':action.get('answer','')})
                    host.queue.append(ROLES['entry_agent'])
                else:
                    host.answer=action.get('answer',''); host.stop_reason='finalized'
                break
            else:
                try:
                    if kind=='list_files': result=host.checkout.list_files()
                    elif kind=='read_file': result=host.checkout.read_file(action['path'])
                    elif kind=='run_tests': result=host.checkout.run_tests()
                    else: raise RuntimeError('E_ALLOWED_ACTION_DISPATCH_DRIFT')
                    host.inbox[role].append({'kind':'tool_result','action':kind,'content':result})
                except (OSError,ValueError,KeyError,UnicodeError) as exc:
                    host.inbox[role].append({'kind':'tool_result','action':kind,'content':f'Error: {exc}'})
                needs_return=True
        if not host.stop_reason and needs_return: host.queue.append(role)
        await maybe_hook(hook,boundary='AFTER_HOST_TURN_RETURNS',event_ref=f'host:turn:{turn:04d}:post',host=host,turn=turn)
        if host.stop_reason: break

    if not host.stop_reason: host.stop_reason='turn_budget'
    return {'answer':host.answer,'stop_reason':host.stop_reason,'turns':len(host.history),
            'pending_roles':list(host.queue),'history':host.history,'authority_events':authority_events}

async def execute(branch,c):
    receipts,exitrow=branch.apply()
    branch.phase='NATIVE_SUBJECT_CONTINUATION'; branch.capture('NATIVE_SUBJECT_CONTINUATION_BEFORE')
    async def boundary(**payload):
        branch.capture('NATIVE_TERMINAL_RETURN' if payload['boundary']=='TERMINAL' else 'NATIVE_TURN_RETURN')
    result=None; error=None
    try:
        result=await resume_authority_bound(branch,boundary,c)
        branch.observer.capture('native:closure',stable_json_bytes(result).decode(),
            'NATIVE_CLOSURE' if branch.host.stop_reason in {'finalized','queue_exhausted'} else 'NATIVE_CENSOR')
    except BaseException as exc:
        error={'type':type(exc).__name__,'message':str(exc)}
        branch.observer.capture('native:closure',stable_json_bytes(error).decode(),'NATIVE_FAILURE')
        raise
    finally:
        D.H.retain_provider_observations(branch); branch.capture('E_BRANCH_AFTER'); comp=branch.observer.finish()
        after=branch.adapter.save_state(branch.host)
        save(branch.out/'native_state_after.json',after); save(branch.out/'native_result.json',result if result is not None else error)
        events=[] if result is None else list(result.get('authority_events') or [])
        save(branch.out/'authority_events.json',events)
        current=file_tree_manifest(branch.root); changed=[p for p in current if current[p]!=branch.manifest[p]]
        summary=seal({'schema':'stage2-hard-post-repair-authority-result-v1',
          'status':'CAPTURED_PENDING_SOURCE_BOUND_COMPARISON' if error is None else 'FAILED_WITH_PARTIAL_EVIDENCE',
          'source_history_length':c['common_parent']['history_length'],'remaining_before':c['common_parent']['remaining_horizon'],
          'history_length_after':len(after['history']),'continued_turns':len(after['history'])-c['common_parent']['history_length'],
          'remaining_after':after['max_turns']-len(after['history']),'stop_reason':after['stop_reason'],
          'answer_present':after['answer'] is not None,'subject_provider_calls':branch.source.provider_calls,
          'post_parent_changed_files':changed,'final_queue_length':len(after['queue']),
          'authority_denial_count':len(events),'authority_denial_reasons':sorted({e['reason'] for e in events}),
          'graph_new_observations':comp['new_observations'],'coordinated_cut_same_as_D':True,
          'automatic_retry':False,'control_D_rerun':False,'repair_success':False,
          'semantic_effect':'PENDING_SOURCE_BOUND_COMPARISON','repair_exit_hash':exitrow['exit_hash'],'error':error},'summary_hash')
        save(branch.out/'summary.json',summary)
    return summary

def preflight(c,state,files,prefix,out):
    out.mkdir(parents=True)
    require(digest(state)==c['common_parent']['state_sha256'],'E_PARENT_STATE_DRIFT')
    require(b'id="pay-button"' in files['web/index.html'] and b'/api/checkout' in files['web/app.js'],'E_FEATURE_NOT_PRESENT')
    env=c['arm_E_hard_authority']['authority_envelope']
    require(env['frozen_modify_refs']==[] and env['write_file_policy']=='DENY_AND_REQUIRE_NEW_REPAIR_SCOPE','E_WRITE_GATE_DRIFT')
    row=seal({'schema':'stage2-hard-post-repair-authority-preflight-v1','history_length':len(state['history']),
      'remaining_horizon':c['common_parent']['remaining_horizon'],'same_coordinated_cut_as_D':True,
      'allowed_actions':env['allowed_actions'],'frozen_modify_refs':env['frozen_modify_refs'],
      'planning_provider_calls':0,'subject_provider_calls':0,'automatic_retry':False,'execution_armed':False},'preflight_hash')
    save(out/'preflight.json',row); return row

def main():
    p=argparse.ArgumentParser(); p.add_argument('--prior-artifact-root',required=True,type=Path)
    p.add_argument('--sdk-root',required=True,type=Path); p.add_argument('--protocol-root',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path); p.add_argument('--execute',action='store_true'); args=p.parse_args()
    require(not args.out.exists(),'FRESH_E_OUTPUT_REQUIRED'); c=load_contract()
    helper_c={'source_treatment_B':c['source_treatment_B'],'common_descendant_parent':c['common_parent'],'frozen_source_checks':c['frozen_source_checks']}
    state,files,prefix,_=D.H.load_prior_parent(args.prior_artifact_root,helper_c); row=preflight(c,state,files,prefix,args.out)
    if not args.execute: print(json.dumps(row)); return
    transport=DeepSeekHTTPTransport(); os.environ.pop('DEEPSEEK_API_KEY',None); os.environ['PYTHONDONTWRITEBYTECODE']='1'
    branch=D.Branch(c,state,files,prefix,args.out/'treatment_E',transport,args.sdk_root,args.protocol_root)
    summary=asyncio.run(execute(branch,c)); print(json.dumps(summary))
if __name__=='__main__': main()
