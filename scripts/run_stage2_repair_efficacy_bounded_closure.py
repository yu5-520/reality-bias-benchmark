#!/usr/bin/env python3
"""Run the single bounded post-repair verification/closure contrast F."""
import argparse, asyncio, importlib.util, inspect, json, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))

from stage2.r7_checkpoint_v1.common import digest, file_tree_manifest, stable_json_bytes
from stage2.native_v7.software_host_v1 import ALLOWED, DIRECTORY, ROLES
from stage2.route_repair.branch_fields import require, save, seal
from stage2.route_repair.connected_provider import DeepSeekHTTPTransport

CONFIG='configs/stage2_repair_efficacy_bounded_closure_v1.json'

def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

E=load_module('scripts/run_stage2_repair_efficacy_hard_authority.py','hard_authority_E')
D=E.D

def load_contract():
    c=json.loads((ROOT/CONFIG).read_bytes())
    require(c['schema']=='stage2-repair-efficacy-bounded-closure-v1','F_CONTRACT_SCHEMA_DRIFT')
    require(c['status']=='FROZEN_BEFORE_SINGLE_F_EXECUTION','F_CONTRACT_NOT_FROZEN')
    require(c['control_E']['rerun'] is False and c['arm_F_bounded_closure']['automatic_retry'] is False,'F_NO_RERUN_REQUIRED')
    require(c['arm_F_bounded_closure']['same_coordinated_cut_as_D'] is True,'F_D_CUT_DRIFT')
    require(c['arm_F_bounded_closure']['same_hard_authority_as_E'] is True,'F_E_AUTHORITY_DRIFT')
    return c

async def maybe_hook(hook,**payload):
    if hook is None: return
    value=hook(**payload)
    if inspect.isawaitable(value): await value

def disposition_allowed(role,action):
    kind=action.get('type')
    if role=='release_lead':
        return kind=='finalize'
    return kind=='finalize' or (kind=='message' and action.get('to')=='release_lead')

async def resume_bounded(branch,hook,c):
    host=branch.host
    roles=c['arm_F_bounded_closure']['retained_roles']
    rule=c['arm_F_bounded_closure']['verification_rule']
    max_calls=rule['global_provider_call_ceiling']
    phase={role:'EVIDENCE' for role in roles}
    role_calls={role:0 for role in roles}
    evidence_batches={role:0 for role in roles}
    closure_denials=[]
    authority_events=[]
    schedule_retirements=[]
    dispositions=[]
    provider_calls_before=branch.source.provider_calls
    stop_boundary=None

    def active_roles():
        return [r for r in roles if phase[r] != 'CLOSED']

    while host.queue and branch.source.provider_calls-provider_calls_before < max_calls:
        role=host.queue.popleft()
        if role not in phase:
            receipt=seal({'schema':'stage2-verification-schedule-retirement-v1','role':role,
                'reason':'ROLE_OUTSIDE_FROZEN_POST_REPAIR_SET','native_effect':'QUEUE_ENTRY_RETIRED'},'receipt_hash')
            schedule_retirements.append(receipt)
            branch.observer.capture('state:verification_schedule',stable_json_bytes(receipt).decode(),
                'VERIFICATION_STALE_SCHEDULE_RETIRED',receipt=receipt)
            continue
        if phase[role]=='CLOSED':
            receipt=seal({'schema':'stage2-verification-schedule-retirement-v1','role':role,
                'reason':'ROLE_ALREADY_DISPOSED','native_effect':'QUEUE_ENTRY_RETIRED'},'receipt_hash')
            schedule_retirements.append(receipt)
            branch.observer.capture('state:verification_schedule',stable_json_bytes(receipt).decode(),
                'VERIFICATION_STALE_SCHEDULE_RETIRED',receipt=receipt)
            continue

        inbox=host.inbox[role]
        observations=[item for item in inbox if item.get('kind')=='tool_result']
        messages=host._prompt(role,observations)
        host.inbox[role]=[]
        turn=len(host.history)+1
        response=await host._complete(messages,role=role,turn=turn)
        role_calls[role]+=1
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
        current_phase=phase[role]
        needs_return=False
        role_disposed=False

        for action in actions:
            kind=action['type']
            if kind in ('message','delegate'):
                target=action.get('to')
                if target not in DIRECTORY or target==role or not action.get('content'):
                    raise ValueError('invalid specialist routing')

            # Hard authority remains identical to E before closure budgeting.
            allowed,authority_code=E.action_decision(role,action,c)
            if not allowed:
                event=seal({'schema':'stage2-post-repair-authority-event-v1','turn':turn,'role':role,
                    'action_type':kind,'action_hash':digest(action),'target_role':action.get('to'),
                    'target_path':action.get('path'),'decision':'DENIED','reason':authority_code,
                    'native_effect':False},'event_hash')
                authority_events.append(event)
                host.inbox[role].append({'kind':'tool_result','action':kind,
                    'content':f'Post-repair authority denied this action: {authority_code}. Provide a disposition within the bounded verification epoch.'})
                branch.observer.capture('state:post_repair_authority',stable_json_bytes(event).decode(),
                    'POST_REPAIR_AUTHORITY_DENIAL',receipt=event,action_id=event['event_hash'])
                needs_return=True
                if current_phase=='ADAPTATION':
                    stop_boundary='ESCALATION_REQUIRED'; break
                phase[role]='ADAPTATION'
                break

            evidence_action=kind in {'list_files','read_file','run_tests'}
            if evidence_action and current_phase!='EVIDENCE':
                event=seal({'schema':'stage2-verification-closure-event-v1','turn':turn,'role':role,
                    'action_type':kind,'action_hash':digest(action),'decision':'DENIED',
                    'reason':'VERIFICATION_BUDGET_EXHAUSTED','native_effect':False,
                    'prior_evidence_batches':evidence_batches[role]},'event_hash')
                closure_denials.append(event)
                host.inbox[role].append({'kind':'tool_result','action':kind,
                    'content':'Bounded post-repair verification is complete for this role. Do not gather more evidence. Submit a disposition now: report to release lead or finalize; if a new repair is required, this branch will escalate instead of expanding scope.'})
                branch.observer.capture('state:verification_closure',stable_json_bytes(event).decode(),
                    'VERIFICATION_BUDGET_DENIAL',receipt=event,action_id=event['event_hash'])
                needs_return=True
                if current_phase=='ADAPTATION':
                    stop_boundary='ESCALATION_REQUIRED'; break
                phase[role]='ADAPTATION'
                break

            if current_phase in {'DECISION','ADAPTATION'} and not disposition_allowed(role,action):
                event=seal({'schema':'stage2-verification-closure-event-v1','turn':turn,'role':role,
                    'action_type':kind,'action_hash':digest(action),'decision':'DENIED',
                    'reason':'DISPOSITION_REQUIRED','native_effect':False},'event_hash')
                closure_denials.append(event)
                host.inbox[role].append({'kind':'tool_result','action':kind,
                    'content':'A bounded verification disposition is required now. Continued verification or scope expansion is not authorized.'})
                branch.observer.capture('state:verification_closure',stable_json_bytes(event).decode(),
                    'VERIFICATION_DISPOSITION_DENIAL',receipt=event,action_id=event['event_hash'])
                needs_return=True
                if current_phase=='ADAPTATION':
                    stop_boundary='ESCALATION_REQUIRED'; break
                phase[role]='ADAPTATION'
                break

            if kind=='message':
                target=action['to']
                host.inbox[target].append({'from':role,'content':action['content']})
                if phase.get(target)!='CLOSED' and target not in host.queue: host.queue.append(target)
                dispositions.append({'turn':turn,'role':role,'kind':'REPORT_TO_RELEASE_LEAD','target':target})
                phase[role]='CLOSED'; role_disposed=True
                break
            if kind=='finalize':
                dispositions.append({'turn':turn,'role':role,'kind':'FINALIZE','answer_present':bool(action.get('answer'))})
                phase[role]='CLOSED'; role_disposed=True
                if role==ROLES['entry_agent']:
                    host.answer=action.get('answer',''); host.stop_reason='finalized'; stop_boundary='NATIVE_FINALIZED'
                else:
                    host.inbox[ROLES['entry_agent']].append({'from':role,'content':action.get('answer','')})
                    if phase['release_lead']!='CLOSED' and 'release_lead' not in host.queue:
                        host.queue.append('release_lead')
                break

            try:
                if kind=='list_files': result=host.checkout.list_files()
                elif kind=='read_file': result=host.checkout.read_file(action['path'])
                elif kind=='run_tests': result=host.checkout.run_tests()
                else: raise RuntimeError('F_ALLOWED_ACTION_DISPATCH_DRIFT')
                host.inbox[role].append({'kind':'tool_result','action':kind,'content':result})
            except (OSError,ValueError,KeyError,UnicodeError) as exc:
                host.inbox[role].append({'kind':'tool_result','action':kind,'content':f'Error: {exc}'})
            needs_return=True

        if stop_boundary: break
        if not role_disposed and current_phase=='EVIDENCE' and needs_return:
            evidence_batches[role]+=1
            phase[role]='DECISION'
        if not role_disposed and needs_return and role not in host.queue:
            host.queue.append(role)

        await maybe_hook(hook,boundary='AFTER_HOST_TURN_RETURNS',event_ref=f'host:turn:{turn:04d}:post',host=host,turn=turn)
        if host.stop_reason: break

        # Once every specialist has a disposition, only release lead needs a provider call.
        specialists=[r for r in roles if r!='release_lead']
        if all(phase[r]=='CLOSED' for r in specialists) and phase['release_lead']!='CLOSED':
            host.queue.clear()
            host.queue.append('release_lead')

    if not stop_boundary:
        if host.stop_reason=='finalized':
            stop_boundary='NATIVE_FINALIZED'
        elif not active_roles():
            stop_boundary='VERIFICATION_CLOSED_NO_PENDING_ROLE'
        elif branch.source.provider_calls-provider_calls_before >= max_calls:
            stop_boundary='GLOBAL_VERIFICATION_BUDGET_EXHAUSTED'
        elif not host.queue:
            stop_boundary='VERIFICATION_CLOSED_NO_PENDING_ROLE'
        else:
            stop_boundary='ESCALATION_REQUIRED'

    if host.stop_reason is None:
        host.stop_reason=stop_boundary.lower()

    return {
      'answer':host.answer,'stop_reason':host.stop_reason,'closure_boundary':stop_boundary,
      'turns':len(host.history),'pending_roles':list(host.queue),'history':host.history,
      'authority_events':authority_events,'closure_denials':closure_denials,
      'schedule_retirements':schedule_retirements,'dispositions':dispositions,
      'role_calls':role_calls,'evidence_batches':evidence_batches,'role_phases':phase
    }

async def execute(branch,c):
    receipts,exitrow=branch.apply()
    branch.phase='NATIVE_SUBJECT_CONTINUATION'; branch.capture('NATIVE_SUBJECT_CONTINUATION_BEFORE')
    async def boundary(**payload):
        branch.capture('NATIVE_TERMINAL_RETURN' if payload['boundary']=='TERMINAL' else 'NATIVE_TURN_RETURN')
    result=None; error=None
    try:
        result=await resume_bounded(branch,boundary,c)
        branch.observer.capture('native:closure',stable_json_bytes(result).decode(),'BOUNDED_VERIFICATION_CLOSURE')
    except BaseException as exc:
        error={'type':type(exc).__name__,'message':str(exc)}
        branch.observer.capture('native:closure',stable_json_bytes(error).decode(),'NATIVE_FAILURE'); raise
    finally:
        D.H.retain_provider_observations(branch); branch.capture('F_BRANCH_AFTER'); comp=branch.observer.finish()
        after=branch.adapter.save_state(branch.host)
        save(branch.out/'native_state_after.json',after); save(branch.out/'native_result.json',result if result is not None else error)
        save(branch.out/'authority_events.json',[] if result is None else result['authority_events'])
        save(branch.out/'closure_events.json',[] if result is None else result['closure_denials'])
        save(branch.out/'schedule_retirements.json',[] if result is None else result['schedule_retirements'])
        current=file_tree_manifest(branch.root); changed=[p for p in current if current[p]!=branch.manifest[p]]
        summary=seal({'schema':'stage2-bounded-post-repair-closure-result-v1',
          'status':'CAPTURED_PENDING_SOURCE_BOUND_COMPARISON' if error is None else 'FAILED_WITH_PARTIAL_EVIDENCE',
          'source_history_length':c['common_parent']['history_length'],
          'remaining_native_horizon':c['common_parent']['remaining_horizon'],
          'history_length_after':len(after['history']),'continued_turns':len(after['history'])-c['common_parent']['history_length'],
          'stop_reason':after['stop_reason'],'closure_boundary':None if result is None else result['closure_boundary'],
          'answer_present':after['answer'] is not None,'subject_provider_calls':branch.source.provider_calls,
          'post_parent_changed_files':changed,'final_queue_length':len(after['queue']),
          'authority_denial_count':0 if result is None else len(result['authority_events']),
          'verification_denial_count':0 if result is None else len(result['closure_denials']),
          'schedule_retirement_count':0 if result is None else len(result['schedule_retirements']),
          'disposition_count':0 if result is None else len(result['dispositions']),
          'role_calls':None if result is None else result['role_calls'],
          'evidence_batches':None if result is None else result['evidence_batches'],
          'role_phases':None if result is None else result['role_phases'],
          'graph_new_observations':comp['new_observations'],'same_coordinated_cut_as_D':True,
          'same_hard_authority_as_E':True,'automatic_retry':False,'control_E_rerun':False,
          'semantic_effect':'PENDING_SOURCE_BOUND_COMPARISON','repair_exit_hash':exitrow['exit_hash'],'error':error},'summary_hash')
        save(branch.out/'summary.json',summary)
    return summary

def preflight(c,state,files,prefix,out):
    out.mkdir(parents=True)
    require(digest(state)==c['common_parent']['state_sha256'],'F_PARENT_STATE_DRIFT')
    require(b'id="pay-button"' in files['web/index.html'] and b'/api/checkout' in files['web/app.js'],'F_FEATURE_NOT_PRESENT')
    rule=c['arm_F_bounded_closure']['verification_rule']
    require(rule['max_evidence_batches_per_role']==1 and rule['global_provider_call_ceiling']==15,'F_VERIFICATION_RULE_DRIFT')
    row=seal({'schema':'stage2-bounded-post-repair-closure-preflight-v1',
      'history_length':len(state['history']),'remaining_native_horizon':c['common_parent']['remaining_horizon'],
      'same_coordinated_cut_as_D':True,'same_hard_authority_as_E':True,
      'retained_roles':c['arm_F_bounded_closure']['retained_roles'],
      'max_evidence_batches_per_role':1,'global_provider_call_ceiling':15,
      'planning_provider_calls':0,'subject_provider_calls':0,'automatic_retry':False,'execution_armed':False},'preflight_hash')
    save(out/'preflight.json',row); return row

def main():
    p=argparse.ArgumentParser(); p.add_argument('--prior-artifact-root',required=True,type=Path)
    p.add_argument('--sdk-root',required=True,type=Path); p.add_argument('--protocol-root',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path); p.add_argument('--execute',action='store_true'); args=p.parse_args()
    require(not args.out.exists(),'FRESH_F_OUTPUT_REQUIRED'); c=load_contract()
    helper_c={'source_treatment_B':c['source_treatment_B'],'common_descendant_parent':c['common_parent'],'frozen_source_checks':c['frozen_source_checks']}
    state,files,prefix,_=D.H.load_prior_parent(args.prior_artifact_root,helper_c); row=preflight(c,state,files,prefix,args.out)
    if not args.execute: print(json.dumps(row)); return
    transport=DeepSeekHTTPTransport(); os.environ.pop('DEEPSEEK_API_KEY',None); os.environ['PYTHONDONTWRITEBYTECODE']='1'
    branch=D.Branch(c,state,files,prefix,args.out/'treatment_F',transport,args.sdk_root,args.protocol_root)
    summary=asyncio.run(execute(branch,c)); print(json.dumps(summary))
if __name__=='__main__': main()
