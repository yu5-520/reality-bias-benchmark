#!/usr/bin/env python3
"""Run one nested coordination-obligation repair from frozen enhanced-B history 24.

The control suffix is already frozen and is never rerun. The intervention changes
only four pending message contents with visible repair attribution; history,
queue and application state are preserved. The original subject provider then
continues for the remaining native horizon. No automatic retry or paid reviewer.
"""
import argparse
import asyncio
import copy
import json
import os
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from stage2.r7_checkpoint_v1.common import digest, file_tree_manifest, stable_json_bytes
from stage2.r7_checkpoint_v1.host_adapter import SoftwareHostCheckpointAdapter
from stage2.native_v7.software_host_v1 import SoftwareEngineeringHost, TASKS
from stage2.r7_prospective_v1.engineering_b_runner import _resume_host
from stage2.route_repair.branch_fields import require, save, seal, FullGraphBranchObserver
from stage2.monitor_enhancement.snapshot_append import AppendOnlyEvidenceGraph
from stage2.route_repair.connected_provider import DeepSeekHTTPTransport, ConnectedExchangeSource, transport_binding
from stage2.route_repair.connected_mcp import ConnectedMCPCheckout
from stage2.route_repair.mcp_same_parent import verify_mcp_environment
from stage2.route_repair.native_message import ATTRIBUTION

CONFIG='configs/stage2_repair_efficacy_coordination_followup_v1.json'


def load_contract():
    c=json.loads((ROOT/CONFIG).read_bytes())
    require(c['schema']=='stage2-repair-efficacy-coordination-followup-v1','COORD_CONTRACT_SCHEMA_DRIFT')
    require(c['status']=='FROZEN_BEFORE_SINGLE_C_EXECUTION','COORD_CONTRACT_NOT_FROZEN')
    require(c['arm_control']['rerun'] is False and c['arm_C_coordination_repair']['automatic_retry'] is False,
            'COORD_NO_RERUN_CONTRACT_REQUIRED')
    return c


def load_prior_parent(root,c):
    branch=Path(root)/'repair-efficacy-b-first-attempt/native_branch'
    require(branch.is_dir(),'PRIOR_EFFICACY_ARTIFACT_ROOT_REQUIRED')
    capture_dir=branch/'captures'
    rows=[]
    for path in sorted(capture_dir.glob('*.json')):
        row=json.loads(path.read_bytes())
        rows.append((path,row))
    target=None
    for i,(path,row) in enumerate(rows):
        if str(path.relative_to(Path(root)))==c['common_descendant_parent']['state_capture_member']:
            target=(i,path,row); break
    require(target is not None,'FROZEN_DESCENDANT_STATE_CAPTURE_REQUIRED')
    i,path,row=target
    require(row['ref']=='state:host_parent' and row['phase']=='NATIVE_MCP_TURN_RETURN','DESCENDANT_STATE_CAPTURE_BOUNDARY_DRIFT')
    state=json.loads(row['content'])
    require(len(state['history'])==c['common_descendant_parent']['history_length']
            and state['max_turns']==c['common_descendant_parent']['native_ceiling']
            and state['stop_reason'] is None,'DESCENDANT_NATIVE_STATE_DRIFT')
    require(digest(state)==c['common_descendant_parent']['state_sha256'],'DESCENDANT_STATE_HASH_DRIFT')
    files={}
    last_sequence=None
    for path2,row2 in rows[i+1:]:
        if row2['ref']=='state:host_parent': break
        if row2['ref'].startswith('file:'):
            files[row2['ref'][5:]]=row2['content'].encode()
            last_sequence=int(path2.stem)
    manifest={p:digest(raw) for p,raw in files.items()}
    require(last_sequence==c['common_descendant_parent']['final_file_capture_sequence'],'DESCENDANT_FILE_CAPTURE_BOUNDARY_DRIFT')
    require(digest(manifest)==c['common_descendant_parent']['application_manifest_sha256'],'DESCENDANT_APPLICATION_MANIFEST_DRIFT')
    for ref,expected in c['frozen_source_checks'].items():
        require(digest(files[ref[5:]])==expected,'DESCENDANT_SOURCE_FILE_DRIFT:'+ref)

    base=json.loads((branch/'full_graph_before.json').read_bytes())
    final=json.loads((branch/'full_graph_after.json').read_bytes())
    graph=AppendOnlyEvidenceGraph.from_snapshot(base)
    old={o['observation_id'] for o in base['observations']}
    cutoff=c['common_descendant_parent']['final_file_capture_sequence']
    additions=[o for o in final['observations'] if o['observation_id'] not in old and o.get('native_sequence',10**12)<=cutoff]
    for observation in sorted(additions,key=lambda o:(o.get('native_sequence',0),o['observation_id'])):
        graph.add_observation(observation)
    prefix=graph.snapshot()
    return state,files,prefix,branch


def subject_profile(c,prefix,transport):
    model=json.loads((ROOT/'arena/config/model_deepseek_v0.2.json').read_bytes())
    subject=json.loads((ROOT/'stage2/subject.json').read_bytes())
    require(model['provider']==subject['provider']=='deepseek'
            and model['model_alias']==subject['model_alias']
            and model['expected_model_version']==subject['expected_model_version']
            and model['subject']==subject['subject'],'COORD_SUBJECT_PROFILE_DRIFT')
    remaining=c['common_descendant_parent']['remaining_horizon']
    row={
      'schema':'stage2-connected-provider-profile-v1','role':'subject',
      'source_hashes':{},'config_hash':digest((ROOT/CONFIG).read_bytes()),
      'parent_checkpoint_hash':'derived:'+c['common_descendant_parent']['state_sha256'],
      'graph_hash':prefix['graph_hash'],'archive_sha256':c['source_treatment_B']['artifact_sha256'],
      'original_task':TASKS['T2'],'actor_id':'ORIGINAL_NATIVE_ROLE_DIRECTORY',
      'provider':model['provider'],'base_url':model['base_url'],'endpoint':model['endpoint'],
      'model_alias':model['model_alias'],'expected_model_version':model['expected_model_version'],
      'parameters':model['subject'],'timeout_seconds':subject['limits']['transport_timeout_seconds'],
      'max_logical_calls':remaining,'max_transport_attempts':remaining,
      'transport_attempts_per_call':1,'format_attempts_per_call':1,
      'native_history_length':c['common_descendant_parent']['history_length'],
      'native_ceiling':c['common_descendant_parent']['native_ceiling'],
      'remaining_horizon':remaining,'provider_attempt_counts_before_parent':'FROZEN_PRIOR_ARTIFACT_NOT_REPLAYED',
      'configured_model_version_is_verified_backend':False,'live_transport_enabled':True,
      'transport_binding':transport_binding(transport),'automatic_paid_reviewer':False,
      'max_request_bytes':8000000,'max_response_bytes':8000000,
      'horizon_is_trial_censor_not_native_ceiling':False
    }
    return seal(row,'profile_hash')


def parse_field(path):
    m=re.fullmatch(r'/inbox/([a-z_]+)/([0-9]+)/content',path)
    require(m is not None,'COORD_PENDING_MESSAGE_FIELD_REQUIRED')
    return m.group(1),int(m.group(2))


class Branch:
    def __init__(self,c,state,files,prefix,out,transport,sdk_root,protocol_root):
        self.c=c; self.out=Path(out); require(not self.out.exists(),'FRESH_COORD_BRANCH_REQUIRED_NO_REPLAY')
        self.out.mkdir(parents=True); self.root=self.out/'application'; self.root.mkdir()
        for path,raw in files.items():
            target=self.root/path; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(raw)
        self.original_manifest=file_tree_manifest(self.root)
        require(digest(self.original_manifest)==c['common_descendant_parent']['application_manifest_sha256'],
                'COORD_BRANCH_APPLICATION_COPY_DRIFT')
        verify_mcp_environment(sdk_root,protocol_root)
        self.observer=FullGraphBranchObserver(prefix,self.out,'G3-X4-T2-coordination-obligation-followup')
        self.phase='RESTORED_AWAITING_COORDINATION_REPAIR'
        profile=subject_profile(c,prefix,transport)
        self.source=ConnectedExchangeSource(profile,transport,self.out/'provider_exchanges',
            gate=lambda:self.phase=='NATIVE_SUBJECT_CONTINUATION')
        self.host=SoftwareEngineeringHost(task_id=state['task_id'],checkout=self.root,provider=self.source,max_turns=1,
                                          max_actions=state['max_actions'])
        self.host.max_turns=state['max_turns']; self.adapter=SoftwareHostCheckpointAdapter(); self.adapter.load_state(self.host,state)
        require(self.adapter.save_state(self.host)==state,'COORD_NATIVE_RESTORE_DRIFT')
        self.host.checkout=ConnectedMCPCheckout(self.root,self)
        save(self.out/'source_parent_state.json',state); save(self.out/'subject_profile.json',profile)
        self.capture('COORD_PARENT_RESTORED')

    def capture(self,phase):
        state=self.adapter.save_state(self.host)
        self.observer.capture('state:host_parent',stable_json_bytes(state).decode(),phase)
        for path in file_tree_manifest(self.root):
            self.observer.capture('file:'+path,(self.root/path).read_bytes().decode(),phase)

    def apply_messages(self):
        before=self.adapter.save_state(self.host)
        require(digest(before)==self.c['common_descendant_parent']['state_sha256'],'COORD_PRE_REPAIR_STATE_DRIFT')
        after=copy.deepcopy(before); receipts=[]
        for action in self.c['arm_C_coordination_repair']['message_replacements']:
            role,index=parse_field(action['field_path'])
            require(index<len(after['inbox'][role]),'COORD_PENDING_MESSAGE_MISSING')
            msg=after['inbox'][role][index]
            require(set(msg)=={'from','content'} and msg['from']==action['original_sender'],'COORD_MESSAGE_SENDER_DRIFT')
            require(digest(msg['content'].encode())==action['before_sha256'],'COORD_MESSAGE_VERSION_DRIFT')
            old=msg['content']; new=ATTRIBUTION+action['replacement']
            self.observer.capture('state:host_parent',stable_json_bytes(after).decode(),
                'HOST_MESSAGE_BEFORE',action_id=action['field_path'])
            msg['content']=new
            receipt={'field_path':action['field_path'],'original_sender':action['original_sender'],
                     'before_hash':digest(old.encode()),'after_hash':digest(new.encode()),
                     'native_interface':'native:SoftwareHostCheckpointAdapter.load_state',
                     'attribution_visible_to_subject':True}
            receipts.append(receipt)
        self.adapter.load_state(self.host,after)
        actual=self.adapter.save_state(self.host)
        require(actual==after,'COORD_MESSAGE_READBACK_FAILED')
        require(actual['history']==before['history'] and actual['queue']==before['queue']
                and actual['max_turns']==before['max_turns'] and actual['max_actions']==before['max_actions'],
                'COORD_UNRELATED_HOST_STATE_DRIFT')
        require(file_tree_manifest(self.root)==self.original_manifest,'COORD_APPLICATION_MUTATED_BY_MESSAGE_REPAIR')
        self.observer.capture('state:host_parent',stable_json_bytes(actual).decode(),
            'HOST_COORDINATION_REPAIR_AFTER',receipt={'message_replacements':len(receipts)},written=True)
        save(self.out/'coordination_repair_receipts.json',receipts)
        exitrow=seal({'schema':'stage2-coordination-obligation-repair-exit-v1',
            'message_replacements':len(receipts),'queue_unchanged':True,'history_unchanged':True,
            'application_unchanged':True,'semantic_effect_certified':False,
            'classification':'SOURCE_BOUND_PENDING_OBLIGATION_SUPERSESSION'},'exit_hash')
        save(self.out/'repair_executor_exit.json',exitrow)
        self.observer.capture('native:coordination_repair_executor',stable_json_bytes(exitrow).decode(),
            'COORDINATION_REPAIR_EXECUTOR_EXIT')
        return receipts,exitrow


def retain_provider_observations(branch):
    source=branch.source
    for directory in sorted(source.out.glob('[0-9][0-9][0-9][0-9]')):
        for name in ['request.bin','response_headers.json','response.bin','receipt.json']:
            path=directory/name
            if not path.exists(): continue
            raw=path.read_bytes()
            content=stable_json_bytes({'bytes_hex':raw.hex()}).decode() if name.endswith('.bin') else raw.decode()
            branch.observer.capture('native:subject_provider_exchange',content,
                'CONNECTED_SUBJECT_'+name.split('.')[0].upper(),
                receipt={'exchange_member':str(path.relative_to(branch.out)),'exchange_hash':digest(raw),
                         'provider_calls':source.provider_calls,'origin':'LIVE_PROVIDER_HTTP'})


async def execute(branch):
    receipts,exitrow=branch.apply_messages()
    branch.phase='NATIVE_SUBJECT_CONTINUATION'; branch.capture('NATIVE_SUBJECT_CONTINUATION_BEFORE')
    async def boundary(**payload):
        branch.capture('NATIVE_TERMINAL_RETURN' if payload['boundary']=='TERMINAL' else 'NATIVE_TURN_RETURN')
    error=None; result=None
    try:
        result=await _resume_host(branch.host,boundary)
        branch.observer.capture('native:closure',stable_json_bytes(result).decode(),
            'NATIVE_CLOSURE' if branch.host.stop_reason in {'finalized','queue_exhausted'} else 'NATIVE_CENSOR')
    except BaseException as exc:
        error={'type':type(exc).__name__,'message':str(exc)}
        branch.observer.capture('native:closure',stable_json_bytes(error).decode(),'NATIVE_FAILURE')
        raise
    finally:
        retain_provider_observations(branch); branch.capture('COORD_BRANCH_AFTER')
        comparison=branch.observer.finish(); after=branch.adapter.save_state(branch.host)
        save(branch.out/'native_state_after.json',after); save(branch.out/'native_result.json',result if result is not None else error)
        require(after['history'][:branch.c['common_descendant_parent']['history_length']]
                ==json.loads((branch.out/'source_parent_state.json').read_bytes())['history'],'COORD_HISTORY_PREFIX_DRIFT')
        current=file_tree_manifest(branch.root)
        changed=[p for p in current if current[p]!=branch.original_manifest[p]]
        summary=seal({'schema':'stage2-coordination-obligation-followup-result-v1',
          'status':'CAPTURED_PENDING_SOURCE_BOUND_COMPARISON' if error is None else 'FAILED_WITH_PARTIAL_EVIDENCE',
          'source_history_length':branch.c['common_descendant_parent']['history_length'],
          'remaining_before':branch.c['common_descendant_parent']['remaining_horizon'],
          'history_length_after':len(after['history']),'remaining_after':after['max_turns']-len(after['history']),
          'continued_turns':len(after['history'])-branch.c['common_descendant_parent']['history_length'],
          'stop_reason':after['stop_reason'],'answer_present':after['answer'] is not None,
          'message_replacements':len(receipts),'subject_provider_calls':branch.source.provider_calls,
          'subject_logical_calls':branch.source.calls,'post_parent_changed_files':changed,
          'graph_new_observations':comparison['new_observations'],'queue_mutated_by_intervention':False,
          'history_mutated_by_intervention':False,'application_mutated_by_intervention':False,
          'automatic_retry':False,'control_rerun':False,'repair_success':False,
          'semantic_effect':'PENDING_SOURCE_BOUND_COMPARISON','repair_exit_hash':exitrow['exit_hash'],
          'error':error},'summary_hash')
        save(branch.out/'summary.json',summary)
    return summary


def preflight(c,state,files,prefix,out):
    out.mkdir(parents=True)
    for a in c['arm_C_coordination_repair']['message_replacements']:
        role,index=parse_field(a['field_path']); msg=state['inbox'][role][index]
        require(msg['from']==a['original_sender'] and digest(msg['content'].encode())==a['before_sha256'],
                'COORD_PREFLIGHT_MESSAGE_DRIFT')
    require(b'#pay-button' in files['web/index.html'] and b'/api/checkout' in files['web/app.js'],
            'COORD_PARENT_FEATURE_NOT_PRESENT')
    row=seal({'schema':'stage2-coordination-followup-preflight-v1','history_length':len(state['history']),
      'remaining_horizon':c['common_descendant_parent']['remaining_horizon'],
      'message_replacements':len(c['arm_C_coordination_repair']['message_replacements']),
      'queue_length':len(state['queue']),'prefix_observations':len(prefix['observations']),
      'planning_provider_calls':0,'subject_provider_calls':0,'automatic_retry':False,'execution_armed':False},
      'preflight_hash')
    save(out/'preflight.json',row); return row


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prior-artifact-root',required=True,type=Path)
    p.add_argument('--sdk-root',required=True,type=Path); p.add_argument('--protocol-root',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path); p.add_argument('--execute',action='store_true')
    args=p.parse_args(); require(not args.out.exists(),'FRESH_COORD_OUTPUT_REQUIRED_NO_REPLAY')
    c=load_contract(); state,files,prefix,_=load_prior_parent(args.prior_artifact_root,c)
    row=preflight(c,state,files,prefix,args.out)
    if not args.execute:
        print(json.dumps(row)); return
    transport=DeepSeekHTTPTransport(); os.environ.pop('DEEPSEEK_API_KEY',None); os.environ['PYTHONDONTWRITEBYTECODE']='1'
    branch=Branch(c,state,files,prefix,args.out/'treatment_C',transport,args.sdk_root,args.protocol_root)
    summary=asyncio.run(execute(branch)); print(json.dumps(summary))


if __name__=='__main__':
    main()
