#!/usr/bin/env python3
"""Run one coordinated complete-route repair from frozen G3-X4-T2 history 24.

The carrier-class C control is already frozen and is not rerun. D applies one
atomic host-state repair covering stale obligation supersession, duplicate queue
retirement, and current completion authority. History, task, model profile,
application files and native ceiling are unchanged. No automatic retry.
"""
import argparse, asyncio, copy, importlib.util, json, os, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from stage2.r7_checkpoint_v1.common import digest, file_tree_manifest, stable_json_bytes
from stage2.r7_checkpoint_v1.host_adapter import SoftwareHostCheckpointAdapter
from stage2.native_v7.software_host_v1 import SoftwareEngineeringHost, TASKS
from stage2.r7_prospective_v1.engineering_b_runner import _resume_host
from stage2.route_repair.branch_fields import require, save, seal, FullGraphBranchObserver
from stage2.route_repair.connected_provider import DeepSeekHTTPTransport, ConnectedExchangeSource, transport_binding
from stage2.route_repair.connected_mcp import ConnectedMCPCheckout
from stage2.route_repair.mcp_same_parent import verify_mcp_environment
from stage2.route_repair.native_message import ATTRIBUTION

CONFIG='configs/stage2_repair_efficacy_complete_route_v1.json'

def load_helper():
    p=ROOT/'scripts/run_stage2_repair_efficacy_coordination_followup.py'
    spec=importlib.util.spec_from_file_location('coord_helper',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
H=load_helper()

def load_contract():
    c=json.loads((ROOT/CONFIG).read_bytes())
    require(c['status']=='FROZEN_BEFORE_SINGLE_D_EXECUTION','D_CONTRACT_NOT_FROZEN')
    require(c['arm_C_control']['rerun'] is False and c['arm_D_complete_route_repair']['automatic_retry'] is False,'D_NO_RERUN_REQUIRED')
    return c

def profile(c,prefix,transport):
    model=json.loads((ROOT/'arena/config/model_deepseek_v0.2.json').read_bytes())
    subject=json.loads((ROOT/'stage2/subject.json').read_bytes())
    remaining=c['common_parent']['remaining_horizon']
    row={'schema':'stage2-connected-provider-profile-v1','role':'subject','source_hashes':{},
      'config_hash':digest((ROOT/CONFIG).read_bytes()),'parent_checkpoint_hash':'derived:'+c['common_parent']['state_sha256'],
      'graph_hash':prefix['graph_hash'],'archive_sha256':c['source_treatment_B']['artifact_sha256'],
      'original_task':TASKS['T2'],'actor_id':'ORIGINAL_NATIVE_ROLE_DIRECTORY','provider':model['provider'],
      'base_url':model['base_url'],'endpoint':model['endpoint'],'model_alias':model['model_alias'],
      'expected_model_version':model['expected_model_version'],'parameters':model['subject'],
      'timeout_seconds':subject['limits']['transport_timeout_seconds'],'max_logical_calls':remaining,
      'max_transport_attempts':remaining,'transport_attempts_per_call':1,'format_attempts_per_call':1,
      'native_history_length':c['common_parent']['history_length'],'native_ceiling':c['common_parent']['native_ceiling'],
      'remaining_horizon':remaining,'provider_attempt_counts_before_parent':'FROZEN_PRIOR_ARTIFACT_NOT_REPLAYED',
      'configured_model_version_is_verified_backend':False,'live_transport_enabled':True,
      'transport_binding':transport_binding(transport),'automatic_paid_reviewer':False,
      'max_request_bytes':8000000,'max_response_bytes':8000000,'horizon_is_trial_censor_not_native_ceiling':False}
    return seal(row,'profile_hash')

def field(path):
    m=re.fullmatch(r'/inbox/([a-z_]+)/([0-9]+)/content',path); require(m is not None,'D_MESSAGE_FIELD_INVALID'); return m.group(1),int(m.group(2))

class Branch:
    def __init__(self,c,state,files,prefix,out,transport,sdk,protocol):
        self.c=c; self.out=Path(out); require(not self.out.exists(),'FRESH_D_BRANCH_REQUIRED'); self.out.mkdir(parents=True)
        self.root=self.out/'application'; self.root.mkdir()
        for p,raw in files.items():
            t=self.root/p; t.parent.mkdir(parents=True,exist_ok=True); t.write_bytes(raw)
        self.manifest=file_tree_manifest(self.root); require(digest(self.manifest)==c['common_parent']['application_manifest_sha256'],'D_APPLICATION_PARENT_DRIFT')
        verify_mcp_environment(sdk,protocol)
        self.observer=FullGraphBranchObserver(prefix,self.out,'G3-X4-T2-complete-route-D')
        self.phase='RESTORED_AWAITING_COORDINATED_REPAIR'; self.adapter=SoftwareHostCheckpointAdapter()
        prof=profile(c,prefix,transport); self.source=ConnectedExchangeSource(prof,transport,self.out/'provider_exchanges',gate=lambda:self.phase=='NATIVE_SUBJECT_CONTINUATION')
        self.host=SoftwareEngineeringHost(task_id=state['task_id'],checkout=self.root,provider=self.source,max_turns=1,max_actions=state['max_actions']); self.host.max_turns=state['max_turns']
        self.adapter.load_state(self.host,state); require(self.adapter.save_state(self.host)==state,'D_NATIVE_RESTORE_DRIFT')
        self.host.checkout=ConnectedMCPCheckout(self.root,self); save(self.out/'source_parent_state.json',state); save(self.out/'subject_profile.json',prof); self.capture('D_PARENT_RESTORED')

    def capture(self,phase):
        s=self.adapter.save_state(self.host); self.observer.capture('state:host_parent',stable_json_bytes(s).decode(),phase)
        for p in file_tree_manifest(self.root): self.observer.capture('file:'+p,(self.root/p).read_bytes().decode(),phase)

    def apply(self):
        c=self.c; before=self.adapter.save_state(self.host); require(digest(before)==c['common_parent']['state_sha256'],'D_PARENT_STATE_DRIFT')
        require(before['queue']==['qa','qa','frontend','frontend','backend','frontend','frontend','qa','frontend','qa','product'],'D_QUEUE_PARENT_DRIFT')
        after=copy.deepcopy(before); receipts=[]

        replacements=[["/inbox/frontend/4/content","qa","7284cd562304c0a6112ba9419cc6fdbd58d97176acf8f6163257d643d34b39bf","Current source-bound state already contains #pay-button and a /api/checkout client using the existing cart payload. Re-check those exact files against the original request before any write. If the existing button works with the existing checkout flow, report that and make no unrelated identifier, endpoint, UX or payload changes; only act on a concrete mismatch."],["/inbox/frontend/5/content","reviewer","f23ce5279ecaa34f51cc55bf72c71c4961b111a5efe99253766d8708dfcfaa26","Current source-bound state already contains a payment button wired to /api/checkout. Review the implementation against the original request. Do not open a new cart endpoint, rename the button, or expand UX/error scope unless a concrete mismatch prevents the requested existing-flow behavior; report no change if it already satisfies the request."],["/inbox/product/0/content","reviewer","722775b2814f1b13059b773f1d1d31502414b5250a5fe79c3d7f359ec94eaae1","The current source-bound implementation already contains the requested payment button and checkout wiring. No additional UX requirement discovery is current work unless a concrete mismatch with the original request is identified; report only such a mismatch or no additional requirement."],["/inbox/qa/1/content","reviewer","0aa0bbbf841362e4d8710b69bd956a79158f830c6c9088e4daa41062dde1a5ae","Verify only whether the existing payment button works with the existing checkout flow and whether current tests expose a concrete mismatch with the original request. Do not expand into unrelated edge-case or new test scope unless such a mismatch requires it; report no change if the requested behavior is already supported."]]
        for pth,sender,bhash,repl in replacements:
            role,idx=field(pth); msg=after['inbox'][role][idx]
            require(msg.get('from')==sender and digest(msg['content'].encode())==bhash,'D_STALE_MESSAGE_VERSION_DRIFT:'+pth)
            old=msg['content']; msg['content']=ATTRIBUTION+repl
            receipts.append({'kind':'MESSAGE_SUPERSESSION','field_path':pth,'before_hash':digest(old.encode()),'after_hash':digest(msg['content'].encode())})

        before_queue=list(after['queue']); after['queue']=list(c['arm_D_complete_route_repair']['normalized_queue'])
        receipts.append({'kind':'QUEUE_SUPERSESSION','before_queue':before_queue,'after_queue':list(after['queue']),
                         'retired_duplicate_entries':len(before_queue)-len(set(before_queue)),'reason':'one current delivery per retained role plus release-lead closure gate'})

        common=("Current source-bound state already contains the requested #pay-button, web/app.js posts to /api/checkout, "
                "the corrected current launcher route is present, and the recorded backend tests passed. Prior requests to add, rename, "
                "or broaden the payment-button work are superseded for this branch. Continue only for a concrete mismatch with the original "
                "user request that you can identify in current source or tests; otherwise report the task satisfied. Do not create new UX, API, "
                "identifier, payload, or test scope merely because the original task wording is still visible.")
        directives={
          'qa':common,'frontend':common,'backend':common,'product':common,
          'release_lead':common+" Integrate the retained specialist checks and finalize when no concrete mismatch remains; do not reopen the task from superseded obligations alone."
        }
        for role in c['arm_D_complete_route_repair']['normalized_queue']:
            text=ATTRIBUTION+'[CURRENT COMPLETION AUTHORITY]\n'+directives[role]
            after['inbox'][role].append({'from':'REPAIR_CONTROL','content':text})
            receipts.append({'kind':'CURRENT_COMPLETION_AUTHORITY','role':role,'content_hash':digest(text.encode())})

        for k in c['arm_D_complete_route_repair']['preserved_fields']: require(after[k]==before[k],'D_PRESERVE_FIELD_DRIFT:'+k)
        require(file_tree_manifest(self.root)==self.manifest,'D_APPLICATION_MUTATED_BEFORE_DISPATCH')
        require(len([r for r in receipts if r['kind']=='MESSAGE_SUPERSESSION'])==4,'D_REQUIRED_MESSAGE_ACTIONS_MISSING')
        require(len([r for r in receipts if r['kind']=='CURRENT_COMPLETION_AUTHORITY'])==5,'D_REQUIRED_AUTHORITY_ACTIONS_MISSING')
        self.observer.capture('state:host_parent',stable_json_bytes(before).decode(),'D_COORDINATED_REPAIR_BEFORE')
        self.adapter.load_state(self.host,after); actual=self.adapter.save_state(self.host); require(actual==after,'D_ATOMIC_STATE_READBACK_FAILED')
        require(file_tree_manifest(self.root)==self.manifest,'D_APPLICATION_MUTATED_BY_INTERVENTION')
        save(self.out/'coordinated_repair_receipts.json',receipts)
        exitrow=seal({'schema':'stage2-complete-route-repair-exit-v1','required_actions_complete':True,
          'message_supersessions':4,'queue_before':before_queue,'queue_after':list(after['queue']),
          'completion_authority_roles':sorted(directives),'history_unchanged':True,'task_unchanged':True,'application_unchanged':True,
          'semantic_effect_certified':False,'classification':'COORDINATED_SUPPORTED_ROUTE_CUT'},'exit_hash')
        save(self.out/'repair_executor_exit.json',exitrow)
        self.observer.capture('state:host_parent',stable_json_bytes(actual).decode(),'D_COORDINATED_REPAIR_AFTER',receipt=exitrow,written=True)
        return receipts,exitrow

async def execute(branch):
    receipts,exitrow=branch.apply(); branch.phase='NATIVE_SUBJECT_CONTINUATION'; branch.capture('NATIVE_SUBJECT_CONTINUATION_BEFORE')
    async def boundary(**payload): branch.capture('NATIVE_TERMINAL_RETURN' if payload['boundary']=='TERMINAL' else 'NATIVE_TURN_RETURN')
    result=None; error=None
    try:
        result=await _resume_host(branch.host,boundary)
        branch.observer.capture('native:closure',stable_json_bytes(result).decode(),'NATIVE_CLOSURE' if branch.host.stop_reason in {'finalized','queue_exhausted'} else 'NATIVE_CENSOR')
    except BaseException as exc:
        error={'type':type(exc).__name__,'message':str(exc)}; branch.observer.capture('native:closure',stable_json_bytes(error).decode(),'NATIVE_FAILURE'); raise
    finally:
        H.retain_provider_observations(branch); branch.capture('D_BRANCH_AFTER'); comp=branch.observer.finish(); after=branch.adapter.save_state(branch.host)
        save(branch.out/'native_state_after.json',after); save(branch.out/'native_result.json',result if result is not None else error)
        current=file_tree_manifest(branch.root); changed=[p for p in current if current[p]!=branch.manifest[p]]
        summary=seal({'schema':'stage2-complete-route-repair-result-v1','status':'CAPTURED_PENDING_SOURCE_BOUND_COMPARISON' if error is None else 'FAILED_WITH_PARTIAL_EVIDENCE',
          'source_history_length':branch.c['common_parent']['history_length'],'remaining_before':branch.c['common_parent']['remaining_horizon'],
          'history_length_after':len(after['history']),'continued_turns':len(after['history'])-branch.c['common_parent']['history_length'],
          'remaining_after':after['max_turns']-len(after['history']),'stop_reason':after['stop_reason'],'answer_present':after['answer'] is not None,
          'subject_provider_calls':branch.source.provider_calls,'post_parent_changed_files':changed,'final_queue_length':len(after['queue']),
          'graph_new_observations':comp['new_observations'],'required_repair_actions_complete':True,'automatic_retry':False,'control_rerun':False,
          'repair_success':False,'semantic_effect':'PENDING_SOURCE_BOUND_COMPARISON','repair_exit_hash':exitrow['exit_hash'],'error':error},'summary_hash')
        save(branch.out/'summary.json',summary)
    return summary

def preflight(c,state,files,prefix,out):
    out.mkdir(parents=True); require(state['queue']==['qa','qa','frontend','frontend','backend','frontend','frontend','qa','frontend','qa','product'],'D_PREFLIGHT_QUEUE_DRIFT')
    require(b'id="pay-button"' in files['web/index.html'] and b'/api/checkout' in files['web/app.js'],'D_FEATURE_NOT_PRESENT')
    row=seal({'schema':'stage2-complete-route-repair-preflight-v1','history_length':len(state['history']),
      'remaining_horizon':c['common_parent']['remaining_horizon'],'queue_before':state['queue'],'queue_after':c['arm_D_complete_route_repair']['normalized_queue'],
      'required_actions':c['arm_D_complete_route_repair']['required_actions'],'prefix_observations':len(prefix['observations']),
      'planning_provider_calls':0,'subject_provider_calls':0,'automatic_retry':False,'execution_armed':False},'preflight_hash')
    save(out/'preflight.json',row); return row

def main():
    p=argparse.ArgumentParser(); p.add_argument('--prior-artifact-root',required=True,type=Path); p.add_argument('--sdk-root',required=True,type=Path)
    p.add_argument('--protocol-root',required=True,type=Path); p.add_argument('--out',required=True,type=Path); p.add_argument('--execute',action='store_true'); args=p.parse_args()
    require(not args.out.exists(),'FRESH_D_OUTPUT_REQUIRED'); c=load_contract()
    # helper expects these keys and reconstructs the exact frozen history-24 parent.
    helper_c={'source_treatment_B':c['source_treatment_B'],'common_descendant_parent':c['common_parent'],'frozen_source_checks':c['frozen_source_checks']}
    state,files,prefix,_=H.load_prior_parent(args.prior_artifact_root,helper_c); row=preflight(c,state,files,prefix,args.out)
    if not args.execute: print(json.dumps(row)); return
    transport=DeepSeekHTTPTransport(); os.environ.pop('DEEPSEEK_API_KEY',None); os.environ['PYTHONDONTWRITEBYTECODE']='1'
    branch=Branch(c,state,files,prefix,args.out/'treatment_D',transport,args.sdk_root,args.protocol_root)
    summary=asyncio.run(execute(branch)); print(json.dumps(summary))
if __name__=='__main__': main()
