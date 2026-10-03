"""Two-arm terminal repair runner; preserves every first attempt and query trace."""
from __future__ import annotations
import asyncio
import copy
import gzip
import json
import os
import tarfile
from pathlib import Path
from stage2.r7_checkpoint_v1.common import CheckpointRegistry, digest, file_tree_manifest
from stage2.route_repair.terminal import FrozenGraphAccess, exact_hash, validate_terminal_decision

ROOT=Path(__file__).resolve().parents[2]


def save(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n')


def prepare_terminal(case, archive, graph_path, destination, arm, limits):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    with gzip.open(graph_path) as f:bundle=json.load(f)
    graph=bundle['graph']
    if bundle['full_id']!=case['full_id'] or graph['graph_hash']!=case['graph_hash']:
        raise ValueError('frozen graph identity mismatch')
    access=FrozenGraphAccess(graph,archive,arm=arm,expected_archive_hash=case['archive_sha256'],
        max_queries=limits['max_queries'],response_chars=limits['max_response_chars'],
        total_chars=limits['max_total_evidence_chars'])
    prefix='checkpoints/'+case['terminal_checkpoint_hash']+'/'
    checkpoint_root=destination/'checkpoints'
    for name,m in access.members.items():
        if not name.startswith(prefix):continue
        rel=Path(name)
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('unsafe checkpoint member')
        target=destination/rel;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(access.archive.extractfile(m).read())
    registry=CheckpointRegistry(checkpoint_root)
    parent=registry.load_manifest(case['terminal_checkpoint_hash'])
    if parent['restore_capability']!='FULL_NATIVE':raise ValueError('parent is not full native')
    ledger=json.loads(access.member('checkpoint_ledger.json'))
    terminals=[r for r in ledger['checkpoints'] if r['boundary']=='TERMINAL']
    if len(terminals)!=1 or terminals[0]['checkpoint_hash']!=parent['checkpoint_hash']:
        raise ValueError('parent not the frozen terminal checkpoint')
    if parent['remaining_horizon']!=case['remaining_horizon']:raise ValueError('remaining horizon mismatch')
    files=registry.restore_application(parent['checkpoint_hash'],destination/'checkout')
    state=registry.load_native_state(parent['checkpoint_hash'])
    context=registry.load_model_context(parent['checkpoint_hash'])
    save(destination/'parent_binding.json',{'full_id':case['full_id'],'arm':arm,
        'archive_sha256':case['archive_sha256'],'graph_hash':case['graph_hash'],
        'parent_checkpoint_hash':parent['checkpoint_hash'],'native_state_sha256':digest(state),
        'application_files':files,'context_sha256':digest(context),'terminal_event_ref':parent['event_ref'],
        'restore_verification':'REGISTRY_CONTENT_AND_APPLICATION','native_forward_execution_tested':False})
    return access,parent,state,files


class BudgetedProvider:
    def __init__(self, base, maximum, destination, phase):
        self.base=base;self.maximum=maximum;self.destination=Path(destination)
        self.phase=phase;self.calls=0
    def complete_agent(self,messages,metadata=None):
        if self.calls>=self.maximum:raise RuntimeError('PROVIDER_CALL_BUDGET_EXHAUSTED')
        self.calls+=1
        path=self.destination/f'{self.phase}_{self.calls:02d}'
        save(str(path)+'_request.json',{'messages':messages,'metadata':metadata})
        response=self.base.complete_agent(messages,metadata=metadata)
        save(str(path)+'_response.json',response)
        return response


def build_provider():
    if not os.environ.get('DEEPSEEK_API_KEY'):raise RuntimeError('DEEPSEEK_API_KEY_UNAVAILABLE')
    from arena.providers import DeepSeekArenaProvider
    subject=json.loads((ROOT/'stage2/subject.json').read_text())
    config=json.loads((ROOT/subject['source_config']).read_text())
    for key in ['provider','model_alias','expected_model_version','subject']:
        if config[key]!=subject[key]:raise ValueError('subject binding drift')
    config=copy.deepcopy(config)
    # The adapter counts attempts, rather than additional retries.
    config['transport']['max_retries']=1;config['json_format_retries']=1
    return DeepSeekArenaProvider(config),config


def agent_diagnosis(provider, access, parent, case, files, terminal_record):
    task=next(t for t in json.loads((ROOT/'stage2/tasks.json').read_text())['tasks'] if t['id']==case['full_id'].rsplit('-',1)[-1])
    initial={'user_request':task['user_request'],'arm':access.arm,
        'parent_checkpoint_hash':parent['checkpoint_hash'],'native_state_sha256':parent['native_state_sha256'],
        'application_file_hashes':files,'seed_refs':['state:terminal'],
        'terminal_member':'natural_A_result.json','checkpoint_ledger_member':'checkpoint_ledger.json',
        'shared_initial_evidence':terminal_record,
        'scope':'New terminal repair phase; original evidence remains immutable.',
        'preserve_file_refs':case['preserve_file_refs'],'authorized_file_refs':case['authorized_file_refs'],
        'process_revision_allowed':case['process_revision_allowed'],
        'available_queries':['list_members','read_member']+(['list_nodes','node','object_history','observation'] if access.arm=='GRAPH' else []),
        'query_parameters':{'node':'ref, offset, limit','object_history':'ref, offset, limit','observation':'observation_id, start',
                            'read_member':'member, start, length','list_nodes':'prefix, offset, limit'},
        'output_examples':[{'queries':[{'op':'read_member','member':'natural_A_result.json'}]},
                  {'decision':'REPAIR|NO_REPAIR_NEEDED|UNRESOLVED','parent_checkpoint_hash':parent['checkpoint_hash'],
                    'reason':'Evidence-supported diagnosis, including whether historical issues are already resolved.',
                    'evidence':[{'member':'read member name','sha256':'returned checksum'}],
                    'actions':[{'kind':'process_revision','target_ref':'state:terminal','before_hash':parent['native_state_sha256'],
                       'instruction':'A bounded verification/revision request to the original native host, without altering old messages.',
                       'reason':'Why this revision is needed','evidence':[{'member':'read member name','sha256':'returned checksum'}]}]}]}
    messages=[{'role':'system','content':
       'Review this completed software-engineering process using captured evidence. Do not assume a defect. '
       'Return JSON with either queries (at most three per response) or decision, reason, evidence, actions and parent_checkpoint_hash. '
       'Cite only evidence you have read. NO_REPAIR_NEEDED and UNRESOLVED have empty actions. '
       'An observation or unknown edge is not a causal dependency or write permission. '
       'Preserve implemented functionality. Do not use audit verdicts, CPR labels, or private chain of thought. '
       'The graph is a complete queryable index; pagination never removes other nodes.'},
       {'role':'user','content':json.dumps(initial,ensure_ascii=False)}]
    for _ in range(provider.maximum):
        response=provider.complete_agent(messages,metadata={'role':'terminal_route_repair','arm':access.arm})
        text=response['content'];messages.append({'role':'assistant','content':text});obj=json.loads(text)
        if 'queries' not in obj:return obj
        if 'decision' in obj or not isinstance(obj['queries'],list) or not 1<=len(obj['queries'])<=3:
            raise ValueError('invalid query envelope')
        answers=[]
        for q in obj['queries']:
            try:answers.append({'request':q,'result':access.query(q)})
            except (ValueError,KeyError,IndexError,UnicodeError) as e:
                answers.append({'request':q,'error':str(e)})
        messages.append({'role':'user','content':json.dumps({'query_results':answers},ensure_ascii=False)})
    raise RuntimeError('NO_DECISION_WITHIN_CALL_BUDGET')


def execute_mcp_revision(decision, parent, state, checkout, destination, base_provider, limits, preserve):
    from stage2.r7_checkpoint_v1.host_adapter import SoftwareHostCheckpointAdapter
    from stage2.r7_prospective_v1.engineering_b_runner import _build_host,_inject_host_process_revision,_resume_host
    from stage2.native_v7.software_host_v1 import ROLES
    from stage2.r7_prospective_v1.runtime_event_adapter import PassiveActionTapProvider,RuntimeStructuralBridge
    from stage2.r7_prospective_v1.online_monitor import OnlineStructuralMonitor
    from stage2.r7_checkpoint_v1.controller import ProspectiveCheckpointController
    from stage2.r7_prospective_v1.recorders import HostBoundaryCheckpointRecorder
    from stage2.r7_prospective_v1.integration import HostIntegratedCheckpointMonitorHook
    provider=BudgetedProvider(base_provider,min(limits['max_post_repair_calls'],int(parent['remaining_horizon'])),destination,'continuation')
    tap=PassiveActionTapProvider(provider)
    task=next(t for t in json.loads((ROOT/'stage2/tasks.json').read_text())['tasks'] if t['id']==parent['task_id'])
    host,_=_build_host(system='X4',task=task,checkout=checkout,provider=tap,out=destination)
    adapter=SoftwareHostCheckpointAdapter();adapter.load_state(host,state)
    if digest(adapter.save_state(host))!=parent['native_state_sha256']:raise ValueError('native parent roundtrip failed')
    receipts=[]
    for action in decision['actions']:
        if action['kind']!='process_revision':raise ValueError('first round supports process revision only')
        if file_tree_manifest(checkout)!=preserve:raise ValueError('preserve drift before native action')
        before=digest(adapter.save_state(host))
        # Explicit new repair-phase reopening of experiment-owned host state.
        # The frozen parent, historical answer, messages and files are never rewritten.
        _inject_host_process_revision(host,ROLES['entry_agent'],action['instruction'])
        # The new terminal repair request enters through the native entry role.
        # Keep other queued work/inbox records, but service this new request first.
        host.queue.remove(ROLES['entry_agent'])
        host.queue.appendleft(ROLES['entry_agent'])
        host.stop_reason=None
        host.answer=None
        receipts.append({'native_interface':'native:SoftwareEngineeringHost.inbox_queue_revision',
            'target_ref':action['target_ref'],'before_hash':before,'after_hash':digest(adapter.save_state(host)),
            'instruction':action['instruction'],'decision_hash':decision['decision_hash']})
    save(destination/'native_action_receipts.json',receipts)
    save(destination/'post_revision_native_state.json',adapter.save_state(host))
    controller=ProspectiveCheckpointController();controller.model_decision_sequence=len(host.history)
    monitor=OnlineStructuralMonitor(mode='WATCH_ONLY')
    recorder=HostBoundaryCheckpointRecorder(registry=CheckpointRegistry(destination/'post_repair_checkpoints'),
        controller=controller,system_id='X4_MCP',group_id='TERMINAL_ROUTE_REPAIR',
        run_id=destination.name,task_id=parent['task_id'])
    bridge=RuntimeStructuralBridge(tap=tap,monitor=monitor,controller=controller,cell_id=destination.name)
    hook=HostIntegratedCheckpointMonitorHook(recorder=recorder,bridge=bridge)
    # Native continuation may inspect/read/test/finalize. Application mutations
    # are intercepted before the MCP request in this account-only first round.
    original_checkout=host.checkout
    class PreserveCheckout:
        root=Path(checkout)
        def list_files(self):return original_checkout.list_files()
        def read_file(self,path):return original_checkout.read_file(path)
        def run_tests(self):return original_checkout.run_tests()
        def write_file(self,path,content):raise ValueError('APPLICATION_PRESERVE_SCOPE_WRITE_BLOCKED')
    host.checkout=PreserveCheckout()
    error=None
    try:result=asyncio.run(_resume_host(host,hook))
    except Exception as e:
        error={'type':type(e).__name__,'message':str(e)}
        result={'status':'CONTINUATION_BOUNDARY','answer':host.answer,'stop_reason':host.stop_reason,'history':host.history}
    save(destination/'post_repair_native_state.json',adapter.save_state(host))
    save(destination/'post_repair_result.json',result)
    save(destination/'post_repair_checkpoint_ledger.json',controller.ledger())
    save(destination/'post_repair_monitor.json',{'mode':'WATCH_ONLY','evidence':monitor.evidence(),'candidates':monitor.candidates(),'packages':monitor.packages()})
    if file_tree_manifest(checkout)!=preserve:raise ValueError('preserve drift after continuation')
    return {'native_action_count':len(receipts),'continuation_provider_calls':provider.calls,
            'repair_executor_exited_before_watch':True,'error':error,'final_answer':result.get('answer'),
            'semantic_repair_effect':'AWAITING_SEPARATE_AUDIT'}


def run_arm(case,archive,graph_path,destination,arm,limits,*,execute=False):
    access=None;status={'full_id':case['full_id'],'arm':arm,'provider_calls':0,'native_action_count':0,
        'mode':'ACTIVE' if execute else 'ZERO_CALL_PREFLIGHT','semantic_effect_tested':False}
    try:
        access,parent,state,files=prepare_terminal(case,archive,graph_path,destination,arm,limits)
        # Both arms read the same terminal record; graph navigation is the treatment.
        terminal=access.query({'op':'read_member','member':'natural_A_result.json','length':8000})
        citation={'member':'natural_A_result.json','sha256':terminal['member_sha256']}
        if execute:
            base,provider_config=build_provider();save(Path(destination)/'provider_binding.json',provider_config)
            budget=BudgetedProvider(base,limits['max_agent_calls'],destination,'diagnosis')
            choice=agent_diagnosis(budget,access,parent,case,files,terminal)
            status['provider_calls']=budget.calls
        else:
            if arm=='GRAPH':
                access.query({'op':'list_nodes','prefix':'file:','limit':10})
                ref='file:run.py'
                history=access.query({'op':'object_history','ref':ref,'limit':1})
                if history['items']:
                    access.query({'op':'observation','observation_id':history['items'][0]['observation_id']})
            choice={'decision':'NO_REPAIR_NEEDED','parent_checkpoint_hash':parent['checkpoint_hash'],
                'reason':'Scripted preflight validates a no-action branch only; it is not a semantic judgment.',
                'evidence':[citation],'actions':[]}
            base=None
        save(Path(destination)/'agent_decision_raw.json',choice)
        decision=validate_terminal_decision(choice,access=access,parent=parent,current_files=files,
            authorized_files=[r[5:] for r in case['authorized_file_refs']],
            preserve_files=[r[5:] for r in case['preserve_file_refs']],max_actions=limits['max_actions'])
        if not case['process_revision_allowed'] and decision['actions']:
            raise ValueError('NATIVE_MUTATION_CAPABILITY_NOT_AUTHORIZED_FOR_THIS_CASE')
        save(Path(destination)/'validated_decision.json',decision)
        status['decision']=decision['decision'];status['decision_hash']=decision['decision_hash']
        if execute and decision['decision']=='REPAIR':
            if '-X4-' not in case['full_id']:raise ValueError('native executor unavailable')
            result=execute_mcp_revision(decision,parent,state,Path(destination)/'checkout',Path(destination),base,limits,files)
            status.update(result);status['provider_calls']+=result['continuation_provider_calls']
        final_files=file_tree_manifest(Path(destination)/'checkout')
        save(Path(destination)/'post_repair_file_manifest.json',final_files)
        save(Path(destination)/'post_repair_observation_delta.json',{
            'schema':'stage2-terminal-repair-observation-delta-v1','parent_graph_hash':case['graph_hash'],
            'parent_checkpoint_hash':parent['checkpoint_hash'],'decision_hash':decision['decision_hash'],
            'application_changes':{p:[files.get(p),final_files.get(p)] for p in set(files)|set(final_files) if files.get(p)!=final_files.get(p)},
            'native_receipts_path':'native_action_receipts.json' if status['native_action_count'] else None,
            'scope':'FILE_STATE_AND_NATIVE_ACTION_DELTA; not a complete semantic graph',
            'new_semantic_edges_inferred':False})
        status.update(status='CONTINUATION_BOUNDARY' if status.get('error') else 'PASS',application_preserved=files==final_files,
            native_forward_execution_tested=bool(execute and decision['decision']=='REPAIR'),
            graph_query_count=len(access.log))
    except Exception as e:
        status.update(status='BOUNDARY',error_type=type(e).__name__,error=str(e))
        # Actual calls, including failed calls, are read from preserved request files.
        if Path(destination).exists():
            status['provider_calls']=len(list(Path(destination).glob('*_request.json')))
    finally:
        if access:
            save(Path(destination)/'evidence_query_log.json',access.log);access.close()
        save(Path(destination)/'attempt_receipt.json',status)
    return status
