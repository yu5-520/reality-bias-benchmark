"""Bounded, read-only planning protocol. Only fixed offline actors are enabled.

The exact host request and actor response are persisted before interpretation.
Planning completion revokes tools; it is not a post-repair REPAIR_AGENT_EXIT.
No callback, provider, native command or compiler is exposed to the actor.
"""
import copy
import gzip
import json
import os
from pathlib import Path

from stage2.r7_checkpoint_v1.common import digest, stable_json_bytes
from stage2.route_repair.branch_fields import require, seal
from stage2.route_repair.planning_session import RoutePlanningSession
from stage2.route_repair.proposal_authority import ProposalAuthorityCompiler

TOOLS = {
    'catalog': [], 'node': ['ref'], 'file': ['ref', 'checkpoint_hash'],
    'observation': ['observation_id', 'ref'], 'witness': ['read_id', 'start', 'end'],
}


def _persist(path, raw):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def _json(path, value):
    _persist(path, stable_json_bytes(value))


class OfflinePlanningScript:
    """Immutable scripted responses, deliberately not an autonomous actor."""
    def __init__(self, responses):
        require(isinstance(responses, list) and responses
                and all(type(row) is dict and set(row) == {'content'}
                        and isinstance(row['content'], str) for row in responses),
                'FIXED_PLANNING_RESPONSES_REQUIRED')
        self._responses = copy.deepcopy(responses)
        self._position = 0

    async def complete(self, request):
        require(self._position < len(self._responses), 'PLANNING_SCRIPT_EXHAUSTED')
        row = copy.deepcopy(self._responses[self._position]); self._position += 1
        return row


class ReadOnlyPlanningActorSession:
    def __init__(self, context, envelope, actor, out, *, actor_id, max_calls=32,
                 max_response_bytes=1_000_000):
        # Live providers require a separate, frozen provider/actor binding. An
        # actor payload cannot certify its origin or enable that capability.
        require(type(actor) is OfflinePlanningScript, 'LIVE_PLANNING_ACTOR_DISABLED')
        require(actor._position == 0, 'FRESH_PLANNING_ACTOR_REQUIRED')
        require(isinstance(actor_id, str) and actor_id.strip(), 'HOST_ACTOR_ID_REQUIRED')
        require(type(max_calls) is int and 1 <= max_calls <= 128, 'PLANNING_CALL_BOUND_REQUIRED')
        require(type(max_response_bytes) is int and 1 <= max_response_bytes <= 1_000_000,
                'PLANNING_RESPONSE_BOUND_REQUIRED')
        self._compiler = ProposalAuthorityCompiler(context, envelope)
        require(envelope['parent_checkpoint_hash'] == context.parent_checkpoint_hash,
                'PLANNING_PREFIX_PARENT_MISMATCH')
        require(not envelope['host_answer_allowed'], 'NONTERMINAL_HOST_ANSWER_DISABLED')
        self._session = RoutePlanningSession(context, envelope['original_task'])
        self._actor = actor; self.out = Path(out)
        require(not self.out.exists(), 'FRESH_PLANNING_SESSION_REQUIRED')
        self.out.mkdir(parents=True)
        self._binding = seal({'schema': 'stage2-read-only-planning-binding-v1',
            'actor_id': actor_id, 'actor_origin': 'OFFLINE_SCRIPTED',
            'parent_checkpoint_hash': context.parent_checkpoint_hash,
            'graph_hash': context.graph['graph_hash'], 'envelope_hash': envelope['envelope_hash'],
            'max_calls': max_calls, 'max_response_bytes': max_response_bytes,
            'provider_calls_enabled': False, 'tools': copy.deepcopy(TOOLS),
            'planning_exit_is_repair_exit': False}, 'binding_hash')
        self._envelope = copy.deepcopy(envelope)
        self._messages = []
        self._transcript = []; self._started = False; self._closed = False
        self._authorization = None; self._outcome = None
        _json(self.out / 'binding.json', self._binding)
        _json(self.out / 'task_envelope.json', envelope)
        _json(self.out / 'script.json', actor._responses)

    def _capture(self, sequence, kind, value):
        raw = stable_json_bytes(value)
        member = f'exchanges/{sequence:04d}-{kind}.json.gz'
        compressed = gzip.compress(raw, mtime=0)
        _persist(self.out / member, compressed)
        self._transcript.append({'sequence': sequence, 'kind': kind, 'member': member,
            'content_hash': digest(raw), 'member_hash': digest(compressed)})
        # Durable ledger follows each captured artifact, including failures.
        _json(self.out / f'ledger/{len(self._transcript):04d}.json', self._transcript[-1])

    def tool(self, name, arguments):
        require(not self._closed and self._started, 'PLANNING_TOOLS_REVOKED')
        require(name in TOOLS and type(arguments) is dict, 'READ_ONLY_PLANNING_TOOL_REQUIRED')
        required = set(TOOLS[name]) - ({'checkpoint_hash'} if name == 'file' else set())
        require(required <= set(arguments) <= set(TOOLS[name]), 'EXACT_PLANNING_TOOL_ARGUMENTS_REQUIRED')
        return getattr(self._session, name)(**arguments)

    def _final(self, payload):
        decision = payload.get('decision')
        require(decision in {'REPAIR', 'NO_REPAIR_NEEDED', 'UNRESOLVED'}, 'PLANNING_DECISION_REQUIRED')
        if decision == 'REPAIR':
            require(set(payload) == {'kind', 'decision', 'proposal'} and type(payload['proposal']) is dict,
                    'EXACT_REPAIR_DECISION_REQUIRED')
        else:
            require(set(payload) == {'kind', 'decision', 'reason', 'inspected_refs', 'witness_ids',
                                     'unknown_relations'}, 'EXACT_NO_ACTION_DECISION_REQUIRED')
            require(isinstance(payload['reason'], str) and payload['reason'].strip(), 'DECISION_REASON_REQUIRED')
            for key in ['inspected_refs', 'witness_ids', 'unknown_relations']:
                require(type(payload[key]) is list and all(isinstance(x, str) and x for x in payload[key]),
                        'DECISION_EVIDENCE_LIST_REQUIRED')
            refs = set(payload['inspected_refs']); ids = set(payload['witness_ids'])
            require(refs <= self._session.inspected_nodes and ids <= set(self._session.witnesses),
                    'NO_ACTION_SOURCE_NOT_INSPECTED')
            require(payload['unknown_relations'], 'NO_ACTION_UNCERTAINTY_REQUIRED')
            witness_refs = {self._session.witnesses[x]['ref'] for x in ids}
            require(witness_refs <= refs, 'NO_ACTION_WITNESS_OUTSIDE_SCOPE')
            if decision == 'NO_REPAIR_NEEDED':
                require(refs and refs <= witness_refs, 'NO_REPAIR_INSPECTED_SCOPE_REQUIRED')
        return copy.deepcopy(payload)

    async def run(self):
        require(not self._started, 'PLANNING_FIRST_ATTEMPT_ALREADY_STARTED')
        self._started = True; final = None; failure = None; calls = 0
        try:
            for sequence in range(1, self._binding['max_calls'] + 1):
                request = {'schema': 'stage2-read-only-planning-request-v1',
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
                self._authorization = self._compiler.compile(self._session, final['proposal'])
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
            self._outcome = seal({'schema': 'stage2-planning-session-outcome-v1',
                'binding_hash': self._binding['binding_hash'], 'transcript_hash': digest(self._transcript),
                'state': 'FAILED' if failure else 'COMPLETED', 'failure': failure,
                'decision': (final or {}).get('decision'), 'actor_calls': calls, 'provider_calls': 0,
                'tool_queries': len(self._session.query_log), 'tools_revoked': True,
                'exit_kind': 'OFFLINE_PLANNING_SESSION_EXIT', 'actual_repair_agent_exit': False,
                'authorization_hash': self._authorization.receipt['authorization_hash'] if self._authorization else None,
                'agent_generated_proposal': False, 'native_actions_executed': 0,
                'semantic_truth_certified': False, 'repair_success': False,
                'live_execution_enabled': False}, 'outcome_hash')
            _json(self.out / 'outcome.json', self._outcome)
        return copy.deepcopy(self._outcome)

    @property
    def authorization(self):
        require(self._closed and self._outcome and self._outcome['state'] == 'COMPLETED',
                'COMPLETED_PLANNING_SESSION_REQUIRED')
        return self._authorization

    @property
    def outcome(self):
        require(self._closed and self._outcome is not None, 'CLOSED_PLANNING_OUTCOME_REQUIRED')
        return copy.deepcopy(self._outcome)
