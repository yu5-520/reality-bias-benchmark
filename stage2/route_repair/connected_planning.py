"""Provider-backed read-only planning; host compilation and identity stay separate."""
import copy
import json
from pathlib import Path
from stage2.r7_checkpoint_v1.common import digest
from stage2.route_repair.branch_fields import require, seal, verify_seal
from stage2.route_repair.planning_actor import ReadOnlyPlanningActorSession, TOOLS, _json
from stage2.route_repair.planning_session import RoutePlanningSession
from stage2.route_repair.proposal_authority import ProposalAuthorityCompiler, freeze_task_envelope
from stage2.route_repair.offline_system import revalidate_bundle
from stage2.route_repair.connected_provider import ConnectedExchangeSource


def freeze_connected_envelope(context, original_task, **capabilities):
    base = freeze_task_envelope(context, original_task, **capabilities)
    base.pop('envelope_hash'); base.update(schema='stage2-connected-task-envelope-v1', mode='CONNECTED_BRANCH_TRIAL')
    return seal(base, 'envelope_hash')


def mechanical_envelope(envelope):
    verify_seal(envelope, 'envelope_hash')
    row = {k: copy.deepcopy(v) for k, v in envelope.items() if k != 'envelope_hash'}
    require(row['schema'] == 'stage2-connected-task-envelope-v1' and row['mode'] == 'CONNECTED_BRANCH_TRIAL',
            'CONNECTED_TASK_ENVELOPE_REQUIRED')
    row.update(schema='stage2-task-capability-envelope-v1', mode='OFFLINE_ONLY')
    return seal(row, 'envelope_hash')


OUTPUT_SCHEMA = {
    'tool': {'kind': 'TOOL', 'name': 'catalog|node|file|observation|witness', 'arguments': 'exact named tool arguments'},
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
                       'authority_effect': 'claimed effect', 'limitation': 'uncertainty', 'witness_ids': []}],
        'unknown_relations': [], 'expected_postconditions': [], 'host_answer': None,
        'application_actions': [{'action_id': 'unique id', 'target_ref': 'writable and inspected file ref',
            'kind': 'TEXT_SPAN_REPLACE|JSON_LEAF_REPLACE', 'start': 'text character offset', 'end': 'exclusive offset',
            'pointer': 'JSON pointer (JSON_LEAF_REPLACE only; omit start/end)',
            'before_value_hash': 'sha256 of exact replaced bytes or canonical JSON leaf', 'value': 'proposed replacement',
            'depends_on': [], 'reason': 'source-bound reason', 'diagnosis_ids': []}],
        'verification_tasks': 'host capability objects plus depends_on action IDs',
        'execution_order': 'all action IDs, then host verification IDs'}}}


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
             'provider_calls_enabled': p['transport_binding']['live'], 'tools': copy.deepcopy(TOOLS),
             'verification_capabilities_hash': digest(verification_capabilities), 'planning_exit_is_repair_exit': False}, 'binding_hash')
        self._envelope = copy.deepcopy(envelope); self._retained_binding = copy.deepcopy(self._binding)
        self._messages = []; self._transcript = []
        self._started = False; self._closed = False; self._authorization = None; self._outcome = None
        self._source._gate = lambda: self._started and not self._closed
        _json(self.out / 'binding.json', self._binding); _json(self.out / 'task_envelope.json', envelope)

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
                    'instructions': 'Inspect the complete available prefix using read-only tools. No future evidence is available. '
                        'Return exactly one TOOL with name and arguments, or FINAL with decision. REPAIR supplies a '
                        'stage2-complete-route-proposal-v1: task/graph/archive/parent bindings, route refs classified as '
                        'modify/preserve/verify, diagnoses with inspected endpoint witnesses and adoption UNKNOWN or NOT_ESTABLISHED, '
                        'unknown_relations, expected_postconditions, application_actions, host_answer null, '
                        'verification_tasks and execution_order. NO_REPAIR_NEEDED or UNRESOLVED supplies reason, inspected_refs, '
                        'witness_ids and unknown_relations. No-action decisions are scoped claims, not semantic certification. '
                        'Task capability membership does not itself justify a repair. No native writes or arbitrary commands are tools.',
                    'output_schema': OUTPUT_SCHEMA, 'verification_capabilities': self._verification_capabilities,
                    'tools': TOOLS, 'messages': copy.deepcopy(self._messages)}
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
                result = self.tool(payload['name'], payload['arguments'])
                self._capture(sequence, 'tool-result', result)
                self._messages.append({'role': 'tool', 'name': payload['name'], 'result': result})
            require(final is not None, 'PLANNING_CALL_BUDGET_EXHAUSTED')
            # Revoke tools before host compilation; a final declaration is not
            # a repair-agent exit and never opens independent review.
            self._closed = True
            _json(self.out / 'decision.json', final)
            if final['decision'] == 'REPAIR':
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
