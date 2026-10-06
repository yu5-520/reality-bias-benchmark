"""Read-only complete-context planning and inspected-source proposal compilation.

No provider, native write, semantic adjudication or live readiness is supplied.
The caller retains host policies separately; source support is never permission.
"""
import copy
import json

from stage2.r7_checkpoint_v1.common import digest
from stage2.native_v7.software_host_v1 import TASKS
from stage2.route_repair.branch_fields import require, seal, verify_seal, compile_branch_plan
from stage2.route_repair.native_host_branch import host_source, build_host_answer_policy
from stage2.route_repair.native_message import message_source, build_message_policy


class RoutePlanningSession:
    def __init__(self, context, original_task, *, proposal_origin='OFFLINE_SCRIPTED'):
        require(original_task == TASKS.get(original_task.get('id')), 'ORIGINAL_TASK_BINDING_MISMATCH')
        require(proposal_origin in {'OFFLINE_SCRIPTED','OFFLINE_MANUAL'}, 'LIVE_PLANNING_NOT_READY')
        self.context=context
        self.task=copy.deepcopy(original_task)
        self.origin=proposal_origin
        self.reads={}
        self.witnesses={}
        self.inspected_nodes=set()
        self.query_log=[]

    def _record(self, operation, request, response):
        self.query_log.append({'sequence':len(self.query_log)+1,'operation':operation,
            'request':copy.deepcopy(request),'response_hash':digest(response)})
        return copy.deepcopy(response)

    def catalog(self):
        return self._record('complete_catalog',{},self.context.catalog(self.task))

    def node(self, ref):
        result=self.context.node_context(ref)
        self.inspected_nodes.add(ref)
        return self._record('node_context',{'ref':ref},result)

    def _read(self, operation, request, ref, text, locator):
        row={'read_id':'read:'+str(len(self.reads)+1),'ref':ref,'text':text,
             'source_locator':copy.deepcopy(locator),'text_hash':digest(text.encode()),
             'text_length':len(text)}
        self.reads[row['read_id']]=copy.deepcopy(row)
        self.inspected_nodes.add(ref)
        return self._record(operation,request,row)

    def file(self, ref, checkpoint_hash=None):
        row=self.context.read_file(ref,checkpoint_hash)
        return self._read('read_file',{'ref':ref,'checkpoint_hash':row['checkpoint_hash']},
            ref,row['content'],row['source_locator'])

    def current_answer(self):
        state,_,locator=host_source(self.context)
        require(isinstance(state['answer'],str),'CURRENT_ANSWER_TEXT_REQUIRED')
        return self._read('current_host_answer',{},'state:terminal',state['answer'],
            {**locator,'json_pointer':'/answer'})

    def message(self, field_path):
        state, role, index, locator = message_source(self.context, field_path)
        return self._read('current_pending_message', {'field_path': field_path},
            'state:host_parent', state['inbox'][role][index]['content'], locator)

    def observation(self, observation_id, ref):
        row=self.context.observation_source(observation_id)
        observation=row['observation']
        require(ref in observation['object_refs'],'OBSERVATION_REF_NOT_BOUND')
        return self._read('observation_source',{'observation_id':observation_id,'ref':ref},
            ref,row['source_text'],observation['source_locator'])

    def witness(self, read_id, start, end):
        require(read_id in self.reads,'WITNESS_SOURCE_NOT_INSPECTED')
        row=self.reads[read_id];text=row['text']
        require(type(start) is int and type(end) is int and 0<=start<end<=len(text), 'EXACT_WITNESS_SPAN_REQUIRED')
        result={'witness_id':'witness:'+str(len(self.witnesses)+1),'read_id':read_id,'ref':row['ref'],
            'source_locator':copy.deepcopy(row['source_locator']),'text_hash':row['text_hash'],
            'start':start,'end':end,'quote':text[start:end],
            'span_hash':digest(text[start:end].encode()),
            'scope':'EXACT_READ_SOURCE_SPAN_NOT_SEMANTIC_VERDICT'}
        self.witnesses[result['witness_id']]=copy.deepcopy(result)
        return self._record('select_source_witness',{'read_id':read_id,'start':start,'end':end},result)

    def span(self, read_id, quote):
        """Select an exact, unique quote from an already read source.

        The host derives offsets and a version hash, not a diagnosis or a
        replacement. Replay still uses the ordinary source-witness operation.
        """
        require(read_id in self.reads, 'WITNESS_SOURCE_NOT_INSPECTED')
        require(isinstance(quote, str) and quote, 'EXACT_SOURCE_QUOTE_REQUIRED')
        text = self.reads[read_id]['text']; start = text.find(quote)
        require(start >= 0, 'SOURCE_QUOTE_NOT_PRESENT')
        require(text.find(quote, start + 1) < 0, 'SOURCE_QUOTE_AMBIGUOUS_USE_OFFSETS')
        return self.witness(read_id, start, start + len(quote))

    def compile(self, proposal, *, trusted_application_policy=None, trusted_host_policy=None):
        require(proposal.get('schema')=='stage2-complete-route-proposal-v1','PROPOSAL_SCHEMA_MISMATCH')
        require(proposal['original_task']==self.task,'PROPOSAL_TASK_DRIFT')
        for key,value in [('graph_hash',self.context.graph['graph_hash']),
                          ('archive_sha256',self.context.case['archive_sha256']),
                          ('parent_checkpoint_hash',self.context.case['terminal_checkpoint_hash'])]:
            require(proposal[key]==value,'PROPOSAL_PARENT_DRIFT:'+key)
        route=set(proposal['route_refs'])
        require(route and route<=set(self.context.access.nodes),'ROUTE_OUTSIDE_COMPLETE_GRAPH')
        require(route<=self.inspected_nodes,'ROUTE_NODE_NOT_INSPECTED')
        groups=[set(proposal[k]) for k in ['modify_refs','preserve_refs','verify_refs']]
        require(all(g<=route for g in groups),'ROLE_OUTSIDE_SELECTED_ROUTE')
        require(not any(groups[i]&groups[j] for i in range(3) for j in range(i+1,3)), 'ROUTE_ROLE_CONFLICT')
        require(set.union(*groups)==route,'UNCLASSIFIED_ROUTE_NODE')
        claims=proposal['diagnoses']
        require(claims,'SOURCE_DIAGNOSIS_REQUIRED')
        seen=set()
        for claim in claims:
            require(claim['claim_id'] not in seen,'DUPLICATE_DIAGNOSIS_ID');seen.add(claim['claim_id'])
            require(claim['source_ref'] in route and claim['destination_ref'] in route,'DIAGNOSIS_OUTSIDE_ROUTE')
            require(claim['status'] in {'UNKNOWN','CANDIDATE','SOURCE_BOUND_CLAIM'},'SEMANTIC_VERDICT_CANNOT_BE_ASSUMED')
            require(claim['adoption_status'] in {'UNKNOWN','NOT_ESTABLISHED'},'SEMANTIC_ADOPTION_NOT_ADJUDICATED')
            require(all(isinstance(claim[k],str) and claim[k].strip() for k in
                ['meaning_before','meaning_after','authority_effect','limitation']), 'DIAGNOSIS_DESCRIPTION_REQUIRED')
            ids=claim['witness_ids']
            require(ids and set(ids)<=set(self.witnesses),'DIAGNOSIS_WITNESS_NOT_INSPECTED')
            refs={self.witnesses[x]['ref'] for x in ids}
            require({claim['source_ref'],claim['destination_ref']}<=refs,'DIAGNOSIS_ENDPOINT_WITNESS_REQUIRED')
        require(proposal['unknown_relations'] and proposal['expected_postconditions'], 'UNCERTAINTY_AND_POSTCONDITIONS_REQUIRED')
        app_actions=proposal['application_actions'];host_action=proposal.get('host_answer')
        message=proposal.get('host_message')
        require(not (host_action and message), 'INCOMPATIBLE_TERMINAL_AND_PENDING_MESSAGE')
        by_claim={c['claim_id']:c for c in claims}
        for action in [*app_actions,*([host_action] if host_action else []),*([message] if message else [])]:
            ids=action['diagnosis_ids']
            require(ids and set(ids)<=seen,'ACTION_DIAGNOSIS_NOT_BOUND')
            require(all(by_claim[x]['status']!='UNKNOWN' for x in ids),'UNKNOWN_CLAIM_CANNOT_JUSTIFY_ACTION')
            target=action.get('target_ref','state:terminal')
            require(any(target in {by_claim[x]['source_ref'],by_claim[x]['destination_ref']} for x in ids),
                    'ACTION_OUTSIDE_DIAGNOSED_ENDPOINTS')
        targets={a['target_ref'] for a in app_actions}
        if host_action:targets.add('state:terminal')
        if message:targets.add('state:host_parent')
        require(targets==groups[0],'MODIFY_ACTION_COVERAGE_MISMATCH')
        action_ids=[a['action_id'] for a in app_actions]
        if message:
            require(set(message['depends_on']) <= set(action_ids), 'MESSAGE_DEPENDENCY_NOT_ORDERED')
            action_ids.append(message['action_id'])
        verification_ids=[v['verification_id'] for v in proposal['verification_tasks']]
        all_ids=action_ids+verification_ids+(['host_answer'] if host_action else [])
        require(len(all_ids)==len(set(all_ids)),'DUPLICATE_COORDINATED_STEP_ID')
        require(proposal['execution_order']==all_ids,'UNSUPPORTED_COORDINATED_ORDER')
        completed=set(action_ids)
        for task in proposal['verification_tasks']:
            require(task['refs'] and set(task['refs'])<=route,'VERIFY_TASK_OUTSIDE_ROUTE')
            require(set(task['depends_on'])<=completed,'VERIFICATION_DEPENDENCY_NOT_ORDERED')
            require(task['operation']=='HOST_DEFINED_OFFLINE_CHECK','UNSUPPORTED_VERIFICATION_OPERATION')
            # These are proposed checks, not completion receipts or shell commands.
            require(task['postcondition'],'VERIFICATION_POSTCONDITION_REQUIRED')
            completed.add(task['verification_id'])
        app_plan=None
        if app_actions:
            require(trusted_application_policy is not None,'SEPARATE_HOST_APPLICATION_POLICY_REQUIRED')
            require(trusted_application_policy['original_task']==self.task,'HOST_APPLICATION_TASK_DRIFT')
            require(targets-{'state:terminal','state:host_parent'}<=set(trusted_application_policy['route_refs']), 'APPLICATION_OUTSIDE_HOST_ROUTE')
            app_plan=compile_branch_plan(self.context,trusted_application_policy,app_actions,
                preserve_refs=groups[1],verify_refs=groups[2])
        if host_action:
            require(trusted_host_policy is not None,'SEPARATE_HOST_ANSWER_POLICY_REQUIRED')
            verify_seal(trusted_host_policy,'policy_hash')
            require(host_action.get('target_ref','state:terminal')=='state:terminal','UNSUPPORTED_HOST_TARGET')
            require(host_action['field_path']=='/answer' and host_action['value']==trusted_host_policy['value'], 'HOST_ANSWER_OUTSIDE_POLICY')
            require(set(host_action['depends_on'])<=completed and host_action['depends_on']==trusted_host_policy['depends_on'], 'HOST_ANSWER_DEPENDENCY_DRIFT')
            canonical=build_host_answer_policy(self.context,original_task=self.task,answer=host_action['value'],
                evidence=trusted_host_policy['source_witnesses'],depends_on=host_action['depends_on'])
            require(canonical==trusted_host_policy,'HOST_ANSWER_SOURCE_REVALIDATION_FAILED')
        if message:
            require(trusted_host_policy is not None, 'SEPARATE_HOST_MESSAGE_POLICY_REQUIRED')
            require(trusted_host_policy == build_message_policy(self.context, original_task=self.task,
                action=message, evidence=trusted_host_policy['source_witnesses']), 'HOST_MESSAGE_SOURCE_REVALIDATION_FAILED')
        row = {'schema':'stage2-inspected-route-plan-bundle-v1','origin':self.origin,
            'proposal':copy.deepcopy(proposal),'application_plan':app_plan,
            'host_answer_policy':copy.deepcopy(trusted_host_policy) if host_action else None,
            'inspected_source_witnesses':copy.deepcopy(self.witnesses),'query_log':copy.deepcopy(self.query_log),
            'source_graph_hash':self.context.graph['graph_hash'],
            'all_observed_nodes_available':len(self.context.graph['nodes']),
            'source_citations_checked':True,'semantic_diagnosis_adjudicated':False,
            'verification_tasks_executed':False,'native_actions_executed':0,
            'repair_agent_generated':False,'live_provider_calls':0,'live_execution_ready':False}
        if message: row['host_message_policy'] = copy.deepcopy(trusted_host_policy)
        return seal(row,'bundle_hash')
