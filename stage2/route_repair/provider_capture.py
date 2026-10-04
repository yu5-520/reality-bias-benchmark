"""Frozen provider request contract and exact offline transport-byte capture.

No credentials or live transport are accepted. Configured model names are not
proof of backend identity. This adapter never rewrites native model messages.
"""
import copy
import json
from pathlib import Path

from stage2.native_v7.software_host_v1 import TASKS
from stage2.r7_checkpoint_v1.common import digest
from stage2.route_repair.branch_fields import require, seal, verify_seal
from stage2.route_repair.planning_actor import _persist, _json

CONFIG = 'configs/stage2_bound_provider_phase_v1.json'


def freeze_provider_bindings(context, root):
    root = Path(root)
    config = json.loads((root / CONFIG).read_bytes())
    require(config['schema'] == 'stage2-bound-provider-phase-config-v1', 'PROVIDER_CONFIG_SCHEMA_MISMATCH')
    for path, expected in config['source_hashes'].items():
        require(digest((root / path).read_bytes()) == expected, 'PROVIDER_FROZEN_SOURCE_DRIFT:' + path)
    require(config['live_planning_enabled'] is False and config['live_subject_enabled'] is False
            and config['automatic_paid_reviewer'] is False and config['automatic_replay'] is False,
            'PROVIDER_PREFLIGHT_CANNOT_ENABLE_LIVE')
    model = json.loads((root / 'arena/config/model_deepseek_v0.2.json').read_bytes())
    subject = json.loads((root / 'stage2/subject.json').read_bytes())
    require(model['provider'] == subject['provider'] == 'deepseek'
            and model['model_alias'] == subject['model_alias']
            and model['expected_model_version'] == subject['expected_model_version']
            and model['subject'] == subject['subject'], 'SUBJECT_PROVIDER_PROFILE_DRIFT')
    require(context.parent['state']['task_id'] in TASKS, 'BOUND_NATIVE_TASK_REQUIRED')
    used = len(context.parent['state']['history']); ceiling = context.parent['state']['max_turns']
    remaining = context.parent['manifest']['remaining_horizon']
    require(remaining == ceiling - used and remaining > 0 and ceiling <= subject['limits']['max_total_model_invocations'],
            'BOUND_SUBJECT_HORIZON_DRIFT')
    require(context.parent['state']['stop_reason'] is None, 'BOUND_STOPPED_PARENT_CANNOT_REOPEN')
    bindings = {}
    for role in ['planning', 'subject']:
        row = config[role]
        require(row['model_config'] == subject['source_config'] and row['parameter_section'] == 'subject'
                and row['format_retry_enabled'] is False and row['transport_retry_enabled'] is False,
                'BOUND_PROVIDER_ATTEMPT_POLICY_DRIFT')
        maximum = row['max_logical_calls'] if role == 'planning' else remaining
        attempt_max = row['max_transport_attempts'] if role == 'planning' else remaining
        require(type(maximum) is int and 1 <= maximum <= 64 and maximum == attempt_max,
                'BOUND_PROVIDER_CALL_BUDGET_REQUIRED')
        bindings[role] = seal({'schema': 'stage2-bound-provider-profile-v1', 'role': role,
            'source_hashes': config['source_hashes'], 'config_hash': digest((root / CONFIG).read_bytes()),
            'parent_checkpoint_hash': context.parent_checkpoint_hash, 'graph_hash': context.graph['graph_hash'],
            'archive_sha256': context.case['archive_sha256'], 'original_task': TASKS[context.parent['state']['task_id']],
            'actor_id': row.get('actor_id') if role == 'planning' else 'ORIGINAL_NATIVE_ROLE_DIRECTORY',
            'provider': model['provider'], 'base_url': model['base_url'], 'endpoint': model['endpoint'],
            'model_alias': model['model_alias'], 'expected_model_version': model['expected_model_version'],
            'parameters': model['subject'], 'timeout_seconds': subject['limits']['transport_timeout_seconds'],
            'max_logical_calls': maximum, 'max_transport_attempts': attempt_max,
            'transport_attempts_per_call': 1, 'format_attempts_per_call': 1,
            'native_history_length': used, 'native_ceiling': ceiling, 'remaining_horizon': remaining,
            'provider_attempt_counts_before_parent': 'UNKNOWN_HISTORICAL_EXCHANGES_NOT_ARCHIVED',
            'configured_model_version_is_verified_backend': False,
            'live_transport_enabled': False, 'automatic_paid_reviewer': False}, 'profile_hash')
    return seal({'schema': 'stage2-provider-bindings-v1', 'profiles': bindings,
        'provider_calls': 0, 'credentials_read': False, 'source_frameworks_modified': False,
        'remaining_gates': config['remaining_gates'], 'live_trial_ready': False}, 'bindings_hash')


class OfflineWireResponses:
    def __init__(self, rows):
        require(type(rows) is list and rows and all(type(row) is dict
            and set(row) == {'status', 'body'} and type(row['status']) is int
            and isinstance(row['body'], bytes) for row in rows), 'FIXED_OFFLINE_WIRE_RESPONSES_REQUIRED')
        self._rows = copy.deepcopy(rows); self._position = 0

    def send(self, request):
        require(self._position < len(self._rows), 'OFFLINE_WIRE_SCRIPT_EXHAUSTED')
        row = copy.deepcopy(self._rows[self._position]); self._position += 1
        return row


class BoundExchangeSource:
    """Prepared provider interface tested with exact offline HTTP-shaped bytes.

    Attempt IDs are assigned and recorded before dispatch. An uncertain failure
    closes the source; no fallback, JSON resampling or budget refund is supplied.
    Returned content is exactly the model message, without JSON repair.
    """
    def __init__(self, profile, wire, out, *, gate):
        verify_seal(profile, 'profile_hash')
        require(profile['schema'] == 'stage2-bound-provider-profile-v1' and profile['live_transport_enabled'] is False,
                'OFFLINE_PROVIDER_PROFILE_REQUIRED')
        require(type(wire) is OfflineWireResponses and wire._position == 0, 'LIVE_PROVIDER_TRANSPORT_NOT_BOUND')
        require(callable(gate), 'HOST_PROVIDER_PHASE_GATE_REQUIRED')
        self._profile = copy.deepcopy(profile); self._wire = wire; self._gate = gate
        self.out = Path(out); require(not self.out.exists(), 'FRESH_PROVIDER_EXCHANGES_REQUIRED')
        self.out.mkdir(parents=True)
        self.calls = 0; self.failed = False
        _json(self.out / 'profile.json', self._profile)
        _json(self.out / 'offline_wire_script.json', [{'status': r['status'], 'body_hex': r['body'].hex()} for r in wire._rows])

    def complete_agent(self, messages, metadata=None):
        # Gate rejection creates no request and spends no call. The host can
        # retry only this pre-dispatch phase check, never an attempted exchange.
        require(not self.failed, 'PROVIDER_FIRST_ATTEMPT_FAILED_NO_REPLAY')
        require(self._gate() is True, 'SUBJECT_PROVIDER_BEFORE_HOST_RELEASE')
        p = self._profile
        require(metadata is None or (type(metadata) is dict and set(metadata) <= {'role', 'turn', 'parent_checkpoint_hash'}),
                'BOUND_PROVIDER_METADATA_KEYS_REQUIRED')
        if metadata and 'turn' in metadata:
            require(type(metadata['turn']) is int and metadata['turn'] == p['native_history_length'] + self.calls + 1,
                    'BOUND_PROVIDER_NATIVE_TURN_DRIFT')
        require(self.calls < min(p['max_logical_calls'], p['max_transport_attempts']), 'BOUND_PROVIDER_BUDGET_EXHAUSTED')
        require(type(messages) is list and all(type(m) is dict and isinstance(m.get('role'), str)
            and isinstance(m.get('content'), str) for m in messages), 'EXACT_NATIVE_MESSAGES_REQUIRED')
        payload = {'model': p['model_alias'], 'messages': copy.deepcopy(messages),
            'max_tokens': p['parameters']['max_tokens'], 'temperature': p['parameters']['temperature'],
            'thinking': {'type': p['parameters']['thinking']}, 'response_format': {'type': 'json_object'}}
        # Same JSON encoding as the repository DeepSeek adapter, captured before
        # dispatch instead of reconstructed after a normalized response.
        raw_request = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.calls += 1; attempt = self.calls
        directory = self.out / f'{attempt:04d}'
        response = None; failure = None
        try:
            _persist(directory / 'request.bin', raw_request)
            _json(directory / 'request.json', {'attempt': attempt, 'profile_hash': p['profile_hash'],
                'url': p['base_url'].rstrip('/') + p['endpoint'], 'method': 'POST',
                'headers': {'Content-Type': 'application/json', 'Accept': 'application/json'},
                'body_hash': digest(raw_request), 'metadata': copy.deepcopy(metadata or {}),
                'origin': 'OFFLINE_WIRE_FIXTURE', 'provider_call': False, 'timeout_seconds': p['timeout_seconds']})
            response = self._wire.send(copy.deepcopy(payload))
            _persist(directory / 'response.bin', response['body'])
            _json(directory / 'response.json', {'status': response['status'], 'body_hash': digest(response['body']),
                'origin': 'OFFLINE_WIRE_FIXTURE', 'provider_call': False})
            require(200 <= response['status'] < 300, 'BOUND_PROVIDER_HTTP_FAILURE')
            def unique(pairs):
                result = {}
                for key, value in pairs:
                    require(key not in result, 'DUPLICATE_PROVIDER_RESPONSE_FIELD'); result[key] = value
                return result
            obj = json.loads(response['body'], object_pairs_hook=unique,
                             parse_constant=lambda _: require(False, 'NONFINITE_PROVIDER_RESPONSE'))
            require(type(obj) is dict and 'error' not in obj, 'BOUND_PROVIDER_APPLICATION_FAILURE')
            require(obj.get('model') in {p['model_alias'], p['expected_model_version']}, 'BOUND_PROVIDER_REPORTED_MODEL_DRIFT')
            require(isinstance(obj.get('id'), str) and obj['id'], 'BOUND_PROVIDER_RESPONSE_ID_REQUIRED')
            choices = obj.get('choices')
            require(type(choices) is list and len(choices) == 1 and type(choices[0]) is dict,
                    'EXACT_PROVIDER_CHOICE_REQUIRED')
            content = choices[0]['message']['content']
            require(isinstance(content, str), 'PROVIDER_CONTENT_TEXT_REQUIRED')
            require(choices[0].get('finish_reason') == 'stop', 'BOUND_PROVIDER_INCOMPLETE_RESPONSE')
            # The native host/parser decides what the content means. There is no
            # attempt to repair or resample malformed content here.
            return {'content': content, 'response_id': obj['id'], 'model': obj['model'],
                'usage': copy.deepcopy(obj.get('usage') or {}), 'provider_response': obj,
                'finish_reason': choices[0]['finish_reason']}
        except BaseException as exc:
            self.failed = True; failure = {'type': type(exc).__name__, 'message': str(exc)}
            raise
        finally:
            _json(directory / 'receipt.json', seal({'schema': 'stage2-bound-provider-exchange-v1',
                'attempt': attempt, 'profile_hash': p['profile_hash'], 'request_hash': digest(raw_request),
                'response_hash': digest(response['body']) if response else None, 'failure': failure,
                'logical_calls': self.calls, 'transport_attempts': self.calls, 'provider_calls': 0,
                'origin': 'OFFLINE_WIRE_FIXTURE', 'backend_identity_verified': False,
                'credentials_saved': False, 'automatic_retry': False}, 'exchange_hash'))


class PlanningRequestAdapter:
    """Encode the existing host planning request without narrowing its task.

    Prepared adapter only: the sealed scripted planning loop cannot instantiate
    this class as a live actor. No source query or write is performed here.
    """
    def __init__(self, source):
        require(type(source) is BoundExchangeSource and source._profile['role'] == 'planning',
                'BOUND_PLANNING_PROVIDER_REQUIRED')
        self._source = source

    async def complete(self, request):
        p = self._source._profile
        require(request.get('schema') == 'stage2-read-only-planning-request-v1', 'BOUND_PLANNING_REQUEST_SCHEMA')
        require(request['binding']['parent_checkpoint_hash'] == p['parent_checkpoint_hash']
                and request['binding']['graph_hash'] == p['graph_hash']
                and request['original_task'] == p['original_task'], 'BOUND_PLANNING_REQUEST_DRIFT')
        require(request['binding']['max_calls'] <= p['max_logical_calls'], 'BOUND_PLANNING_REQUEST_BUDGET_DRIFT')
        messages = [{'role': 'system', 'content': request['instructions']},
                    {'role': 'user', 'content': json.dumps(request, ensure_ascii=False, sort_keys=True)}]
        return self._source.complete_agent(messages, {'role': 'read_only_planning',
            'parent_checkpoint_hash': p['parent_checkpoint_hash']})
