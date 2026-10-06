"""Source-bound current answer supersession on an experiment-owned host branch.

Only the current /answer field is writable. Original history, inboxes, queue,
task, stop state and foreign system state are preserved. The host never calls a
provider here. This is a native adapter binding, not an agent repair efficacy test.
"""
import copy
import json

from stage2.r7_checkpoint_v1.common import digest, stable_json_bytes, file_tree_manifest
from stage2.r7_checkpoint_v1.host_adapter import SoftwareHostCheckpointAdapter, ADAPTER_ID
from stage2.native_v7.software_host_v1 import SoftwareEngineeringHost, TASKS
from stage2.route_repair.branch_fields import require, seal, verify_seal, save


class NoCallProvider:
    def complete_agent(self, *args, **kwargs):
        raise RuntimeError("OFFLINE_NATIVE_BINDING_PROVIDER_CALL_FORBIDDEN")


def host_source(context):
    checkpoint = context.case['terminal_checkpoint_hash']
    prefix = 'checkpoints/' + checkpoint + '/'
    manifest = json.loads(context.raw(prefix + 'manifest.json'))
    require(manifest['adapter_id'] == ADAPTER_ID, 'UNSUPPORTED_HOST_ADAPTER')
    require(manifest['restore_capability'] == 'FULL_NATIVE', 'HOST_NATIVE_PARENT_REQUIRED')
    require(manifest['system_id'] in {'X4_MCP', 'X5_RAG', 'X6_MEMORYBANK', 'X7_LONGLMLINGUA'}, 'FOREIGN_STATE_NOT_WRITABLE')
    state = json.loads(context.raw(prefix + 'native_state.json'))
    require(state['schema'] == 'stage2-r7-software-host-state-v1', 'HOST_STATE_SCHEMA_MISMATCH')
    require(digest(state) == manifest['native_state_sha256'], 'HOST_STATE_VERSION_MISMATCH')
    require(state['answer'] == json.loads(context.raw('natural_A_result.json'))['answer'], 'TERMINAL_ANSWER_SOURCE_MISMATCH')
    return state, manifest, context.locator(prefix + 'native_state.json')


def build_host_answer_policy(context, *, original_task, answer, evidence, depends_on):
    state, manifest, locator = host_source(context)
    require(original_task == TASKS[state['task_id']], 'ORIGINAL_TASK_BINDING_MISMATCH')
    require(isinstance(answer, str) and answer and answer != state['answer'], 'ANSWER_NO_EFFECT')
    require(evidence and depends_on, 'SOURCE_BOUND_COORDINATED_PLAN_REQUIRED')
    refs = []
    for supplied in evidence:
        source = context.locator(supplied['member'])
        require(source['member_sha256'] == supplied['member_sha256'], 'ANSWER_WITNESS_DRIFT')
        refs.append(source)
    next_state = copy.deepcopy(state)
    next_state['answer'] = answer
    return seal({'schema':'stage2-native-host-answer-policy-v1',
        'mode':'OFFLINE_SOURCE_BASED_ENGINEERING_BRANCH', 'graph_hash':context.graph['graph_hash'],
        'archive_sha256':context.case['archive_sha256'], 'parent_checkpoint_hash':manifest['checkpoint_hash'],
        'original_task':copy.deepcopy(original_task), 'target_ref':'state:terminal', 'field_path':'/answer',
        'source_locator':locator, 'before_state_hash':digest(state), 'before_answer_hash':digest(state['answer']),
        'after_state_hash':digest(next_state), 'after_answer_hash':digest(answer), 'value':answer,
        'depends_on':list(depends_on), 'source_witnesses':refs,
        'historical_records_rewritten':False, 'model_generated':False,
        'semantic_adoption_verified':False, 'native_agent_continuation_executed':False}, 'policy_hash')


class NativeHostAnswerBinding:
    def __init__(self, context, checkout, policy, *, trusted_policy):
        verify_seal(policy, 'policy_hash')
        require(policy == trusted_policy, 'HOST_TRUSTED_POLICY_MISMATCH')
        require(policy['mode'] == 'OFFLINE_SOURCE_BASED_ENGINEERING_BRANCH'
                and policy['target_ref'] == 'state:terminal' and policy['field_path'] == '/answer', 'HOST_FIELD_NOT_AUTHORIZED')
        canonical = build_host_answer_policy(context, original_task=policy['original_task'],
            answer=policy['value'], evidence=policy['source_witnesses'], depends_on=policy['depends_on'])
        require(policy == canonical, 'HOST_POLICY_SOURCE_REVALIDATION_FAILED')
        self.context, self.policy, self.checkout = context, copy.deepcopy(policy), checkout
        self.before, manifest, _ = host_source(context)
        require(policy['archive_sha256'] == context.case['archive_sha256']
                and policy['parent_checkpoint_hash'] == manifest['checkpoint_hash']
                and policy['graph_hash'] == context.graph['graph_hash'], 'HOST_PARENT_BINDING_MISMATCH')
        require(digest(self.before) == policy['before_state_hash'], 'STALE_HOST_STATE')
        self.host = SoftwareEngineeringHost(task_id=self.before['task_id'], checkout=checkout,
            provider=NoCallProvider(), max_turns=1, max_actions=self.before['max_actions'])
        # Restore the exact captured per-run budget on this branch instance. A
        # replication checkpoint may exceed today's constructor default ceiling.
        # Do not mutate module limits or increase the saved continuation budget.
        self.host.max_turns = self.before['max_turns']
        self.adapter = SoftwareHostCheckpointAdapter()
        self.adapter.load_state(self.host, self.before)
        self.executed = False

    def current(self):
        return self.adapter.save_state(self.host)

    def apply(self, *, completed_actions, observer):
        require(not self.executed, 'HOST_SUPERSESSION_ALREADY_APPLIED')
        require(set(self.policy['depends_on']) <= set(completed_actions), 'HOST_UPSTREAM_DEPENDENCY_NOT_COMPLETE')
        before = self.current()
        require(digest(before) == self.policy['before_state_hash'], 'STALE_HOST_STATE')
        require(digest(before['answer']) == self.policy['before_answer_hash'], 'STALE_HOST_ANSWER')
        files_before = file_tree_manifest(self.checkout)
        after = copy.deepcopy(before)
        after['answer'] = self.policy['value']
        require(digest(after) == self.policy['after_state_hash'], 'HOST_EXPECTED_OUTPUT_MISMATCH')
        preserved_before = {k:v for k,v in before.items() if k != 'answer'}
        preserved_after = {k:v for k,v in after.items() if k != 'answer'}
        require(preserved_before == preserved_after, 'UNRELATED_HOST_STATE_DRIFT')
        self.executed = True
        observer.capture('state:terminal', stable_json_bytes(before).decode(), 'HOST_FIELD_BEFORE', action_id='host_answer')
        save(observer.out/'intents/host_answer.json', {'policy_hash':self.policy['policy_hash'],
            'target_ref':'state:terminal', 'field_path':'/answer', 'before_hash':digest(before), 'after_hash':digest(after)})
        error = None
        try:
            # Native restore API operates on the new experiment-owned host only.
            self.adapter.load_state(self.host, after)
            actual = self.current()
            require(actual == after, 'HOST_NATIVE_POSTCONDITION_FAILED')
            require(file_tree_manifest(self.checkout) == files_before, 'HOST_OPERATION_CHANGED_APPLICATION')
        except Exception as exc:
            error = {'type':type(exc).__name__, 'message':str(exc)}
        actual = self.current()
        receipt = {'schema':'stage2-native-host-answer-supersession-v1',
            'native_interface':'native:SoftwareHostCheckpointAdapter.load_state',
            'mutation_class':'EXPERIMENT_OWNED_CURRENT_HOST_ANSWER_SUPERSESSION',
            'target_ref':'state:terminal', 'field_path':'/answer',
            'before_hash':digest(before), 'after_hash':digest(actual),
            'expected_output_hash':self.policy['after_state_hash'], 'error':error,
            'unrelated_host_fields_preserved':{k:v for k,v in actual.items() if k!='answer'} == preserved_before,
            'application_files_preserved':file_tree_manifest(self.checkout) == files_before,
            'source_checkpoint_retained':self.policy['parent_checkpoint_hash'],
            'new_provider_calls':0, 'native_agent_continuation_executed':False}
        save(observer.out/'native_host_action_receipt.json', receipt)
        observer.capture('state:terminal', stable_json_bytes(actual).decode(), 'HOST_FIELD_AFTER',
            receipt=receipt, action_id='host_answer', written=True)
        save(observer.out/'native_host_state_after.json', actual)
        return receipt
