"""Provider-backed read-only planning; host compilation and identity stay separate."""
import copy
import json
from pathlib import Path
from stage2.r7_checkpoint_v1.common import digest
from stage2.route_repair.branch_fields import require, seal, verify_seal
from stage2.route_repair.planning_actor import ReadOnlyPlanningActorSession, _json
from stage2.route_repair.planning_session import RoutePlanningSession
from stage2.route_repair.proposal_authority import ProposalAuthorityCompiler, freeze_task_envelope
from stage2.route_repair.offline_system import revalidate_bundle
from stage2.route_repair.connected_provider import ConnectedExchangeSource
from stage2.route_repair.branch_fields import BranchConstraintError
from stage2.route_repair.source_navigation import SourceNavigation, classify_query_error

TOOL_CONTRACTS = {
    'catalog': {'purpose': 'Full repeated locator metadata; prefix_index already covers every node and version. Use this only when full locators are needed. No source content is read and no witness is selected.',
        'arguments': {}, 'next_reads': ['node(ref)', 'versions(ref, at)', 'read_version(version_handle)', 'message(field_path)']},
    'node': {'purpose': 'Inspect node metadata, version locators and observation IDs; not source-content evidence.',
        'arguments': {'ref': 'exact catalog node ref'}},
    'versions': {'purpose': 'Resolve only observed file versions; TASK_START never substitutes a later snapshot. Returns handles, not source evidence.',
        'arguments': {'ref': 'exact file node ref', 'at': 'optional ALL, TASK_START or PARENT'}},
    'read_version': {'purpose': 'Read exact bytes using a host-issued version_handle from prefix_index or versions; do not construct hashes or combine paths and checkpoints.',
        'arguments': {'version_handle': 'copy one host-issued version: handle'}},
    'message': {'purpose': 'Read actual pending message content, including fields absent from the catalog file list.',
        'arguments': {'field_path': 'exact pointer listed in task_capabilities.message_fields'}},
    'observation': {'purpose': 'Read actual archived observation bytes/text; ref must belong to that observation.',
        'arguments': {'observation_id': 'ID from node metadata', 'ref': 'one bound node ref'}},
    'witness': {'purpose': 'Select an exact source span after reading it; returns quote, offsets, text_hash and span_hash.',
        'returned_id': 'witness_id has prefix witness:; read_id has prefix read: and is not a citation ID',
        'arguments': {'read_id': 'host-returned read ID', 'start': 'integer inclusive character offset',
                      'end': 'integer exclusive character offset; text_length selects the complete read'}},
    'span': {'purpose': 'Select a unique exact quote from an already read source; host returns witness offsets and span_hash.',
        'returned_id': 'witness_id has prefix witness:; copy this ID into witness_ids, never read_id',
        'arguments': {'read_id': 'host-returned read ID', 'quote': 'exact nonempty source substring; ambiguous quotes fail'}},
}

# The existing tool descriptions also supply dispatch argument names.
CONNECTED_TOOLS = {name: list(contract['arguments']) for name, contract in TOOL_CONTRACTS.items()}

# A single root object, rather than named wrappers around message examples.
# The API still captures json_object bytes unchanged; host validation remains
# exact and does not coerce a model's type/kind spelling or resample a reply.
RESPONSE_CONTRACT = {'type': 'object', 'oneOf': [
    {'type': 'object', 'required': ['kind', 'name', 'arguments'], 'additionalProperties': False,
     'properties': {'kind': {'const': 'TOOL'}, 'name': {'enum': list(CONNECTED_TOOLS)},
                    'arguments': {'type': 'object'}}},
    {'type': 'object', 'required': ['kind', 'decision', 'proposal'], 'additionalProperties': False,
     'properties': {'kind': {'const': 'FINAL'}, 'decision': {'const': 'REPAIR'}, 'proposal': {'type': 'object'}}},
    {'type': 'object', 'required': ['kind', 'decision', 'reason', 'inspected_refs', 'witness_ids', 'unknown_relations'],
     'additionalProperties': False,
     'properties': {'kind': {'const': 'FINAL'}, 'decision': {'enum': ['UNRESOLVED', 'NO_REPAIR_NEEDED']},
        'reason': {'type': 'string'}, **{k: {'type': 'array', 'items': {'type': 'string'}}
            for k in ['inspected_refs', 'unknown_relations']},
        'witness_ids': {'type': 'array', 'items': {'type': 'string', 'pattern': '^witness:[1-9][0-9]*$'}}}}]}

ROOT_MESSAGE_INSTRUCTION = (
    'Return exactly one top-level JSON object. Its discriminator key is "kind" (case sensitive), '
    'with value "TOOL" or "FINAL". A tool response is exactly '
    '{"kind":"TOOL","name":"catalog","arguments":{}} with the chosen tool name and arguments. '
    'A repair response is exactly {"kind":"FINAL","decision":"REPAIR","proposal":{...}}. '
    'A no-action response has kind, decision, reason, inspected_refs, witness_ids, unknown_relations. '
    'Use response_contract for the root object; output_schema contains descriptions of alternatives, '
    'not wrapper keys to return. A top-level "type" field is invalid. ')


def freeze_connected_envelope(context, original_task, **capabilities):
    base = freeze_task_envelope(context, original_task, **capabilities)
    base.pop('envelope_hash'); base.update(schema='stage2-connected-task-envelope-v1', mode='CONNECTED_BRANCH_TRIAL')
    return seal(base, 'envelope_hash')


def prefix_index(context, original_task):
    """Lossless navigation projection: every node and file-version membership.

    Keep each handle and its time in the same record. Source bytes,
    locators and observations stay accessible through the original tools. This
    index cannot count as an actual source read or a selected witness.
    """
    catalog = context.catalog(original_task)
    navigation = SourceNavigation(context)
    checkpoints = {}
    for rows in catalog['all_file_versions'].values():
        for row in rows:
            cp = row['checkpoint_hash']
            meta = {k: copy.deepcopy(row[k]) for k in
                ['checkpoint_hash', 'capture_index', 'native_sequence', 'clock_id', 'boundary']}
            require(cp not in checkpoints or checkpoints[cp] == meta, 'PREFIX_VERSION_METADATA_DRIFT')
            checkpoints[cp] = meta
    ordered = sorted(checkpoints.values(), key=lambda r: (r['capture_index'], r['checkpoint_hash']))
    return {'schema': 'stage2-complete-prefix-navigation-index-v3',
        'full_catalog_hash': catalog['context_hash'], 'all_node_refs': catalog['all_node_refs'],
        'checkpoints': ordered,
        'file_versions': {ref: navigation.versions(ref)['versions']
            for ref in catalog['all_file_versions']},
        'coverage': {k: catalog[k] for k in ['node_count', 'edge_count', 'observation_count', 'visibility_scope']},
        'source_limits': {k: copy.deepcopy(catalog['prefix_receipt'][k]) for k in
            ['future_suffix_visible', 'terminal_answer_visible', 'historical_provider_prompt_response_captured',
             'semantic_lineage_complete', 'missing_evidence']},
        'metadata_is_source_read': False, 'semantic_dependency_inferred': False,
        'navigation': 'Each version record binds version_handle, checkpoint_hash, boundary and is_parent. read_version(version_handle) returns the same record as source_version. versions(ref, at) resolves ALL, TASK_START or PARENT. TASK_START labels the initial snapshot; '
            'a later first write checkpoint is not TASK_START. node(ref) discovers native observation sources. '
            'Current functionality does not itself establish the historical absence of changes.'}


def mechanical_envelope(envelope):
    verify_seal(envelope, 'envelope_hash')
    row = {k: copy.deepcopy(v) for k, v in envelope.items() if k != 'envelope_hash'}
    require(row['schema'] == 'stage2-connected-task-envelope-v1' and row['mode'] == 'CONNECTED_BRANCH_TRIAL',
            'CONNECTED_TASK_ENVELOPE_REQUIRED')
    row.update(schema='stage2-task-capability-envelope-v1', mode='OFFLINE_ONLY')
    return seal(row, 'envelope_hash')


OUTPUT_SCHEMA = {
    'tool': {'kind': 'TOOL', 'name': '|'.join(CONNECTED_TOOLS), 'arguments': 'exact named tool arguments'},
    'no_action': {'kind': 'FINAL', 'decision': 'UNRESOLVED|NO_REPAIR_NEEDED', 'reason': 'scoped explanation',
                  'inspected_refs': [], 'witness_ids': [], 'unknown_relations': ['remaining uncertainty']},
    'repair': {'kind': 'FINAL', 'decision': 'REPAIR', 'proposal': {
        'schema': 'stage2-complete-route-proposal-v1', 'original_task': 'exact original_task object',
        'graph_hash': 'binding.graph_hash', 'archive_sha256': 'task_capabilities.archive_sha256',
        'parent_checkpoint_hash': 'binding.parent_checkpoint_hash',
        'route_refs': [], 'modify_refs': [], 'preserve_refs': [], 'verify_refs': [],
        'diagnoses': [{'claim_id': 'unique id', 'source_ref': 'inspected ref', 'destination_ref': 'inspected ref',
                       'status': 'UNKNOWN|CANDIDATE|SOURCE_BOUND_CLAIM', 'adoption_status': 'UNKNOWN|NOT_ESTABLISHED',
                       'meaning_before': 'source-supported statement', 'meaning_after': 'source-supported statement',
                       'authority_effect': 'claimed effect', 'limitation': 'uncertainty',
                       'witness_ids': ['selected witness:* IDs covering both source_ref and destination_ref']}],
        'unknown_relations': [], 'expected_postconditions': [], 'host_answer': None,
        'host_message': {'action_id': 'unique id or omit host_message for file repair; when present and max_actions=1 this is the sole write action',
            'target_ref': 'state:host_parent', 'kind': 'PENDING_MESSAGE_REPLACE',
            'field_path': 'exact task_capabilities.message_fields pointer',
            'before_value_hash': 'text_hash returned by the current message read; never invent or calculate a hash',
            'start': 'character offset of unsupported clause', 'end': 'exclusive clause offset',
            'before_span_hash': 'span_hash returned by the selected original-clause witness',
            'replacement': 'source-qualified replacement for only the selected original span; omit attribution and full message value',
            'depends_on': [], 'diagnosis_ids': []},
        'application_actions': [{'action_id': 'unique id; use only for task_capabilities.writable_refs; MUST be [] when writable_refs is empty',
            'target_ref': 'writable and inspected application file ref; never state:host_parent',
            'kind': 'TEXT_SPAN_REPLACE|JSON_LEAF_REPLACE', 'start': 'text character offset', 'end': 'exclusive offset',
            'pointer': 'JSON pointer (JSON_LEAF_REPLACE only; omit start/end)',
            'before_value_hash': 'sha256 of exact replaced bytes or canonical JSON leaf', 'value': 'proposed replacement',
            'depends_on': [], 'reason': 'source-bound reason', 'diagnosis_ids': []}],
        'verification_tasks': [{'verification_id': 'copy host capability verification_id',
            'operation': 'copy host capability operation', 'refs': ['copy host capability refs'],
            'postcondition': 'copy host capability postcondition', 'depends_on': ['preceding action_id']}],
        'execution_order': ['action_id in execution order', 'verification_id after actions']}}}


def validate_connected_repair_shape(envelope, proposal):
    """Expose existing connected-branch capability boundaries before compilation."""
    actions = proposal['application_actions']
    message = proposal.get('host_message')
    if not envelope['writable_refs']:
        require(actions == [], 'CONNECTED_APPLICATION_ACTIONS_NOT_AUTHORIZED')
    if message:
        require(message['field_path'] in envelope.get('message_fields', []),
                'CONNECTED_MESSAGE_FIELD_NOT_AUTHORIZED')
        if envelope['max_actions'] == 1:
            require(actions == [], 'CONNECTED_MESSAGE_IS_SOLE_ACTION')
        for task in proposal['verification_tasks']:
            require(message['action_id'] in task.get('depends_on', []),
                    'CONNECTED_MESSAGE_VERIFICATION_DEPENDENCY_REQUIRED')


class ConnectedAuthorization:
    def __init__(self, base, binding, source, transcript):
        self.context = base.context
        self._mechanical = base
        self._dispatched = False
        self._application_policy = copy.deepcopy(base._application_policy)
        self._host_policy = copy.deepcopy(base._host_policy)
        self._provenance = {'binding_hash': binding['binding_hash'], 'profile_hash': source._profile['profile_hash'],
                            'transcript_hash': digest(transcript), 'provider_calls': source.provider_calls,
                            'transport_attempts': source.transport_attempts, 'origin': source._profile['transport_binding']['origin']}
        self._bundle = self._derive()
        row = {k: copy.deepcopy(v) for k, v in base.receipt.items() if k != 'authorization_hash'}
        row.update(schema='stage2-connected-authorization-v1', bundle_hash=self._bundle['bundle_hash'],
                   provenance=self._provenance, live_execution_enabled=source._profile['transport_binding']['live'])
        self._receipt = seal(row, 'authorization_hash')

    def _derive(self):
        row = self._mechanical.bundle; row.pop('bundle_hash')
        row.update(schema='stage2-connected-route-plan-bundle-v1', origin=self._provenance['origin'],
                   repair_agent_generated=bool(self._provenance['provider_calls']),
                   live_provider_calls=self._provenance['provider_calls'], live_execution_ready=bool(self._provenance['provider_calls']),
                   host_provenance=copy.deepcopy(self._provenance))
        return seal(row, 'bundle_hash')

    def revalidate(self, supplied):
        revalidate_bundle(self.context, self._mechanical.bundle, self._application_policy, self._host_policy)
        require(supplied == self._bundle == self._derive(), 'CONNECTED_HOST_AUTHORIZATION_DRIFT')

    @property
    def bundle(self): return copy.deepcopy(self._bundle)

    @property
    def receipt(self): return copy.deepcopy(self._receipt)


class ConnectedPlanningSession(ReadOnlyPlanningActorSession):
    def __init__(self, context, envelope, source, out, *, verification_capabilities):
        require(type(source) is ConnectedExchangeSource and source._profile['role'] == 'planning'
                and source.calls == 0, 'FRESH_CONNECTED_PLANNING_SOURCE_REQUIRED')
        p = source._profile
        require(p['parent_checkpoint_hash'] == context.parent_checkpoint_hash and p['graph_hash'] == context.graph['graph_hash']
                and p['original_task'] == envelope['original_task'], 'CONNECTED_PLANNING_PARENT_DRIFT')
        self._compiler = ProposalAuthorityCompiler(context, mechanical_envelope(envelope))
        require(not envelope['host_answer_allowed'], 'NONTERMINAL_HOST_ANSWER_DISABLED')
        self._session = RoutePlanningSession(context, envelope['original_task'])
        self._source = source; self._actor = _RequestAdapter(source)
        self._verification_capabilities = copy.deepcopy(verification_capabilities)
        require(type(verification_capabilities) is list and verification_capabilities, 'HOST_VERIFICATION_CAPABILITIES_REQUIRED')
        self.out = Path(out); require(not self.out.exists(), 'FRESH_PLANNING_SESSION_REQUIRED'); self.out.mkdir(parents=True)
        self._binding = seal({'schema': 'stage2-connected-planning-binding-v1', 'actor_id': p['actor_id'],
             'actor_origin': p['transport_binding']['origin'], 'parent_checkpoint_hash': context.parent_checkpoint_hash,
             'graph_hash': context.graph['graph_hash'], 'envelope_hash': envelope['envelope_hash'],
             'profile_hash': p['profile_hash'], 'max_calls': p['max_logical_calls'], 'max_response_bytes': 1_000_000,
             'provider_calls_enabled': p['transport_binding']['live'], 'tools': copy.deepcopy(CONNECTED_TOOLS),
             'verification_capabilities_hash': digest(verification_capabilities), 'planning_exit_is_repair_exit': False}, 'binding_hash')
        self._envelope = copy.deepcopy(envelope); self._retained_binding = copy.deepcopy(self._binding)
        self._prefix_index = prefix_index(context, envelope['original_task'])
        self._navigation = SourceNavigation(context)
        self._query_failures = []
        self._messages = []; self._transcript = []
        self._started = False; self._closed = False; self._authorization = None; self._outcome = None
        self._source._gate = lambda: self._started and not self._closed
        _json(self.out / 'binding.json', self._binding); _json(self.out / 'task_envelope.json', envelope)

    def tool(self, name, arguments):
        require(not self._closed and self._started, 'PLANNING_TOOLS_REVOKED')
        require(name in CONNECTED_TOOLS, 'READ_ONLY_PLANNING_TOOL_REQUIRED')
        required = set(CONNECTED_TOOLS[name]) - ({'at'} if name == 'versions' else set())
        require(type(arguments) is dict and required <= set(arguments) <= set(CONNECTED_TOOLS[name]),
                'EXACT_PLANNING_TOOL_ARGUMENTS_REQUIRED')
        if name == 'versions':
            require(all(isinstance(v, str) for v in arguments.values()), 'EXACT_PLANNING_TOOL_ARGUMENTS_REQUIRED')
            return self._navigation.versions(**arguments)
        if name == 'read_version':
            return self._navigation.read(self._session, arguments['version_handle'])
        result = getattr(self._session, name)(**arguments)
        if name in {'span', 'witness'}:
            result['source_version'] = self._navigation.read_version_metadata(
                self._session.reads[result['read_id']])
        return result

    def query(self, name, arguments, sequence):
        try:
            return self.tool(name, arguments)
        except BranchConstraintError as exc:
            category, recoverable = classify_query_error(str(exc))
            receipt = seal({'schema': 'stage2-planning-query-failure-v1',
                'binding_hash': self._binding['binding_hash'], 'sequence': sequence,
                'tool': name, 'arguments_hash': digest(arguments), 'error_code': str(exc),
                'category': category, 'recoverable_in_same_session': recoverable,
                'remaining_responses': self._binding['max_calls'] - sequence,
                'source_content_returned': False, 'authority_expanded': False,
                'next_action': 'CORRECT_QUERY_WITHIN_EXISTING_BUDGET' if recoverable else 'STOP'}, 'receipt_hash')
            self._query_failures.append(receipt)
            self._capture(sequence, 'query-failure', receipt)
            if not recoverable:
                raise
            return {'status': 'QUERY_REJECTED', 'failure_receipt': receipt,
                    'guidance': 'Use exact host-returned handles and read IDs. For quotes use an exact unique substring or witness offsets. No automatic retry or alias conversion occurred.'}

    def source_read_state(self):
        """Host-owned progress; listing a source cannot turn it into a read."""
        return {'metadata_inspected_refs': sorted(self._session.inspected_nodes),
            'actual_source_reads': [{**{k: copy.deepcopy(r[k]) for k in
                ['read_id', 'ref', 'text_hash', 'text_length', 'source_locator']},
                'source_version': self._navigation.read_version_metadata(r)} for r in self._session.reads.values()],
            'selected_witnesses': [{**{k: copy.deepcopy(w[k]) for k in
                ['witness_id', 'read_id', 'ref', 'start', 'end', 'span_hash', 'source_locator']},
                'source_version': self._navigation.read_version_metadata(self._session.reads[w['read_id']])}
                for w in self._session.witnesses.values()],
            'pending_message_sources': [{'field_path': p, 'ref': 'state:host_parent', 'read_tool': 'message',
                'parent_checkpoint_hash': self._binding['parent_checkpoint_hash'],
                'required_witness_scope': 'Complete current message: start=0, end=text_length; also select the replaced clause.'}
                for p in self._envelope.get('message_fields', [])],
            'catalog_is_source_read': False, 'source_evidence_grants_write_permission': False,
            'evidence_flow': ['versions or prefix_index', 'read_version or message or observation', 'span or witness', 'FINAL'],
            'citation_rule': 'Only selected_witnesses.witness_id is a citation. Reads are not citations.'}

    async def run(self):
        require(not self._started, 'PLANNING_FIRST_ATTEMPT_ALREADY_STARTED')
        require(self._binding == self._retained_binding, 'CONNECTED_PLANNING_BINDING_MUTATED')
        self._started = True; final = None; failure = None; calls = 0
        try:
            for sequence in range(1, self._binding['max_calls'] + 1):
                require(self._binding == self._retained_binding, 'CONNECTED_PLANNING_BINDING_MUTATED')
                request = {'schema': 'stage2-connected-planning-request-v1',
                    'binding': self._binding, 'original_task': self._envelope['original_task'],
                    'task_capabilities': self._envelope,
                    'instructions': ROOT_MESSAGE_INSTRUCTION +
                        'Inspect the complete available prefix using read-only tools. No future evidence is available. '
                        'Catalog and node metadata are navigation, not file/message reads or selected witnesses. '
                        'prefix_index already lists every available node, checkpoint and file version without repeated locators; '
                        'use it to navigate directly, and catalog only for full locator metadata. '
                        'Use tool_contracts and the host-owned source_read_state to choose actual reads. '
                        'An available pending message is read with message(field_path), even if it is absent from the file index. '
                        'Assess process-account consistency and authority as well as original task progression: '
                        'functionality or recorded file writes alone cannot certify that a pending process claim needs no repair. '
                        'Do not presume any inconsistency or adoption before reading its sources. '
                        'Use read_version with a host-issued handle; the old file(ref, checkpoint_hash) tool is not available. '
                        'A QUERY_REJECTED result permits a corrected query only within the original remaining budget; '
                        'access-boundary and integrity failures still close the session. '
                        'Copy version hashes and offsets from read/witness results; span selects a unique exact quote. '
                        'read:* IDs identify reads, not witnesses. Before citing a read, call witness or span and copy '
                        'the returned witness_id (witness:*). A FINAL must not put read:* into witness_ids. '
                        'For a temporal process statement, distinguish TASK_START, later writes and current snapshots; '
                        'do not infer "never changed" from a working current snapshot or current absence from TASK_START bytes. '
                        'source_version.is_parent identifies the exact frozen parent, not semantic correctness. '
                        'Declare unread history or unread current sources as uncertainty. '
                        'NO_REPAIR_NEEDED requires actual selected witnesses covering every inspected_ref in its declared scope. '
                        'UNRESOLVED may declare empty inspected_refs/witness_ids when no source was read; do not invent inspection. '
                        'Return exactly one TOOL with name and arguments, or FINAL with decision. REPAIR supplies a '
                        'stage2-complete-route-proposal-v1: task/graph/archive/parent bindings, route refs classified as '
                        'modify/preserve/verify, diagnoses with inspected endpoint witnesses and adoption UNKNOWN or NOT_ESTABLISHED, '
                        'unknown_relations, expected_postconditions, application_actions, host_answer null, optional host_message. '
                        'Every diagnosis must cite selected witness:* IDs covering both source_ref and destination_ref; raw read:* IDs '
                        'or uncited reads are insufficient. If you read an endpoint that will appear in a diagnosis, select its witness '
                        'before FINAL; a read_version result alone is not a citation. application_actions may target only refs listed in '
                        'task_capabilities.writable_refs. When writable_refs is empty, application_actions MUST be []. A pending message '
                        'repair uses host_message as the sole write action when max_actions=1; never duplicate it as an application action. '
                        'Its verification task depends_on host_message.action_id. A message action must replace only a preauthorized pending content field '
                        'and cite the current message plus actual prefix sources. The host prepends the fixed repair attribution; '
                        'do not include that attribution in replacement. Select a witness for the complete current message '
                        '(start=0, end=text_length) and for the replaced clause. Supply exact start/end, before_span_hash and '
                        'replacement only. Do not return a full message value; the host derives value from the frozen current '
                        'message, selected span, replacement and attribution, preserving unrelated message text. '
                        'Keep original task scope; distinguish failed reads, observed writes and unknown adoption. '
                        'verification_tasks and execution_order. NO_REPAIR_NEEDED or UNRESOLVED supplies reason, inspected_refs, '
                        'witness_ids and unknown_relations. No-action decisions are scoped claims, not semantic certification. '
                        'Task capability membership does not itself justify a repair. No native writes or arbitrary commands are tools.',
                    'response_contract': RESPONSE_CONTRACT,
                    'output_schema': OUTPUT_SCHEMA, 'verification_capabilities': self._verification_capabilities,
                    'tools': CONNECTED_TOOLS, 'tool_contracts': TOOL_CONTRACTS,
                    'prefix_index': copy.deepcopy(self._prefix_index),
                    'source_read_state': self.source_read_state(),
                    'remaining_responses_including_this': self._binding['max_calls'] - sequence + 1,
                    'messages': copy.deepcopy(self._messages)}
                self._capture(sequence, 'request', request)
                calls += 1
                response = await self._actor.complete(copy.deepcopy(request))
                self._capture(sequence, 'response', response)
                require(len(response['content'].encode()) <= self._binding['max_response_bytes'],
                        'PLANNING_RESPONSE_BUDGET_EXHAUSTED')
                # Preserve provider content exactly; reject duplicate fields or
                # NaN rather than interpreting an ambiguous proposal.
                def unique(pairs):
                    row = {}
                    for key, value in pairs:
                        require(key not in row, 'DUPLICATE_ACTOR_JSON_FIELD'); row[key] = value
                    return row
                payload = json.loads(response['content'], object_pairs_hook=unique,
                                     parse_constant=lambda _: require(False, 'NONFINITE_ACTOR_JSON'))
                require(type(payload) is dict, 'STRUCTURED_PLANNING_MESSAGE_REQUIRED')
                self._messages.append({'role': 'actor', 'content': response['content']})
                if payload.get('kind') == 'FINAL':
                    final = self._final(payload)
                    break
                require(set(payload) == {'kind', 'name', 'arguments'} and payload['kind'] == 'TOOL',
                        'EXACT_READ_ONLY_TOOL_MESSAGE_REQUIRED')
                result = self.query(payload['name'], payload['arguments'], sequence)
                self._capture(sequence, 'tool-result', result)
                self._messages.append({'role': 'tool', 'name': payload['name'], 'result': result})
            require(final is not None, 'PLANNING_CALL_BUDGET_EXHAUSTED')
            # Revoke tools before host compilation; a final declaration is not
            # a repair-agent exit and never opens independent review.
            self._closed = True
            _json(self.out / 'decision.json', final)
            if final['decision'] == 'REPAIR':
                validate_connected_repair_shape(self._envelope, final['proposal'])
                require(final['proposal']['verification_tasks'], 'CONNECTED_HOST_VERIFICATION_REQUIRED')
                for task in final['proposal']['verification_tasks']:
                    require(any(all(task.get(k) == cap[k] for k in ['verification_id', 'operation', 'refs', 'postcondition'])
                        for cap in self._verification_capabilities), 'CONNECTED_VERIFICATION_NOT_HOST_BOUND')
                base = self._compiler.compile(self._session, final['proposal'])
                self._authorization = ConnectedAuthorization(base, self._binding, self._source, self._transcript)
                _json(self.out / 'authorization.json', self._authorization.receipt)
                _json(self.out / 'bundle.json', self._authorization.bundle)
        except BaseException as exc:
            failure = {'error_type': type(exc).__name__, 'message': str(exc)}
            self._authorization = None
            raise
        finally:
            self._closed = True
            _json(self.out / 'query_failures.json', self._query_failures)
            _json(self.out / 'query_log.json', self._session.query_log)
            _json(self.out / 'witnesses.json', self._session.witnesses)
            _json(self.out / 'transcript.json', self._transcript)
            self._outcome = seal({'schema': 'stage2-connected-planning-outcome-v1',
                'binding_hash': self._binding['binding_hash'], 'transcript_hash': digest(self._transcript),
                'state': 'FAILED' if failure else 'COMPLETED', 'failure': failure,
                'decision': (final or {}).get('decision'), 'actor_calls': calls, 'provider_calls': self._source.provider_calls,
                'transport_attempts': self._source.transport_attempts, 'valid_responses': self._source.valid_responses,
                'actor_origin': self._source._profile['transport_binding']['origin'],
                'tool_queries': len(self._session.query_log), 'tools_revoked': True,
                'exit_kind': 'HOST_CLOSED_PLANNING_SESSION', 'actual_repair_agent_exit': False,
                'authorization_hash': self._authorization.receipt['authorization_hash'] if self._authorization else None,
                'agent_generated_proposal': bool(final and self._authorization and self._source.provider_calls), 'native_actions_executed': 0,
                'semantic_truth_certified': False, 'repair_success': False,
                'live_execution_enabled': self._source._profile['transport_binding']['live']}, 'outcome_hash')
            _json(self.out / 'outcome.json', self._outcome)
        return copy.deepcopy(self._outcome)


class _RequestAdapter:
    def __init__(self, source): self.source = source

    async def complete(self, request):
        p = self.source._profile
        require(request['binding']['profile_hash'] == p['profile_hash'] and request['original_task'] == p['original_task'],
                'CONNECTED_REQUEST_BINDING_DRIFT')
        messages = [{'role': 'system', 'content': request['instructions']},
                    {'role': 'user', 'content': json.dumps(request, ensure_ascii=False, sort_keys=True)}]
        return self.source.complete_agent(messages, {'role': 'read_only_planning', 'parent_checkpoint_hash': p['parent_checkpoint_hash']})
