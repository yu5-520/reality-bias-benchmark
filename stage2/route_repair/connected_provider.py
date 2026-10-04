"""One-attempt HTTP exchanges. Provenance comes from the host transport, never JSON.

Captured bodies precede interpretation. This is a new branch provider boundary;
it does not change or reconstruct the historical framework's provider adapter.
"""
import copy
import http.client
import json
import os
import ssl
import time
from pathlib import Path

from stage2.r7_checkpoint_v1.common import digest
from stage2.route_repair.branch_fields import require, seal, verify_seal
from stage2.route_repair.planning_actor import _json, _persist
from stage2.route_repair.provider_capture import freeze_provider_bindings

CONFIG = 'configs/stage2_connected_provider_v1.json'
MECHANISM_CONFIG = 'configs/stage2_connected_mechanism_v1.json'


def connected_config(context, root):
    mechanism = json.loads((Path(root) / MECHANISM_CONFIG).read_bytes())
    if context.parent_checkpoint_hash == mechanism['frozen_parent_checkpoint']:
        require(len(context.parent['state']['history']) == mechanism['parent_native_sequence']
                and context.parent['manifest']['remaining_horizon'] == mechanism['subject_trial_max_calls'],
                'MECHANISM_PARENT_WINDOW_DRIFT')
        return MECHANISM_CONFIG, mechanism
    config = json.loads((Path(root) / CONFIG).read_bytes())
    return CONFIG, config


class DeepSeekHTTPTransport:
    def __init__(self):
        key = os.environ.get('DEEPSEEK_API_KEY', '')
        require(bool(key.strip()) and '\r' not in key and '\n' not in key, 'MODEL_CREDENTIAL_UNAVAILABLE_BEFORE_DISPATCH')
        self.__key = key

    def send(self, raw, out, timeout, maximum):
        connection = http.client.HTTPSConnection('api.deepseek.com', timeout=timeout,
                                                  context=ssl.create_default_context())
        try:
            return _send(connection, '/chat/completions', raw, out, maximum,
                         {'Authorization': 'Bearer ' + self.__key})
        finally:
            connection.close()


class LoopbackHTTPTransport:
    """A real socket fixture, incapable of granting live-model provenance."""
    def __init__(self, port):
        require(type(port) is int and 1024 <= port <= 65535, 'LOOPBACK_TEST_PORT_REQUIRED')
        self.port = port

    def send(self, raw, out, timeout, maximum):
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=timeout)
        try:
            return _send(connection, '/chat/completions', raw, out, maximum, {})
        finally:
            connection.close()


def transport_binding(transport):
    require(type(transport) in {DeepSeekHTTPTransport, LoopbackHTTPTransport}, 'HOST_TRANSPORT_CLASS_REQUIRED')
    live = type(transport) is DeepSeekHTTPTransport
    return {'origin': 'LIVE_PROVIDER_HTTP' if live else 'LOOPBACK_HTTP_FIXTURE',
            'url': 'https://api.deepseek.com/chat/completions' if live else
                   f'http://127.0.0.1:{transport.port}/chat/completions', 'live': live}


def _send(connection, endpoint, raw, out, maximum, private_headers):
    # http.client does not redirect or retry. Exact application body bytes are
    # sent once; credentials remain in memory and are never part of a receipt.
    deadline = time.monotonic() + connection.timeout
    socket_handle = None
    def remaining():
        seconds = deadline - time.monotonic()
        require(seconds > 0, 'PROVIDER_TOTAL_DEADLINE_EXCEEDED')
        target_socket = connection.sock or socket_handle
        if target_socket is not None: target_socket.settimeout(seconds)
    connection.request('POST', endpoint, body=raw, headers={
        'Content-Type': 'application/json', 'Accept': 'application/json', **private_headers})
    socket_handle = connection.sock
    remaining()
    response = connection.getresponse()
    headers = {k.lower(): v for k, v in response.getheaders()
               if k.lower() in {'content-type', 'content-length'}}
    _json(out / 'response_headers.json', {'status': response.status, 'headers': headers})
    total = 0
    with (out / 'response.bin').open('xb') as stream:
        while not response.isclosed():
            remaining()
            chunk = response.read1(min(65536, maximum + 1 - total))
            if not chunk:
                break
            stream.write(chunk); stream.flush(); os.fsync(stream.fileno()); total += len(chunk)
            require(total <= maximum, 'PROVIDER_RESPONSE_BODY_LIMIT')
    if 'content-length' in headers:
        require(total == int(headers['content-length']), 'PROVIDER_TRUNCATED_RESPONSE_BODY')
    return {'status': response.status, 'body': (out / 'response.bin').read_bytes()}


def freeze_connected_bindings(context, root, transport):
    base = freeze_provider_bindings(context, root)
    config_path, config = connected_config(context, root)
    raw = (Path(root) / config_path).read_bytes()
    require(config['schema'] == 'stage2-connected-provider-config-v1'
            and config['planning_max_calls'] == 16 and (config['subject_trial_max_calls'] == 4
                or (config_path == MECHANISM_CONFIG and config['subject_trial_max_calls'] == 49))
            and config['automatic_paid_reviewer'] is False and config['automatic_replay'] is False,
            'CONNECTED_PROVIDER_CONFIG_DRIFT')
    binding = transport_binding(transport); profiles = {}
    for role, frozen in base['profiles'].items():
        p = {k: copy.deepcopy(v) for k, v in frozen.items() if k != 'profile_hash'}
        require(p['base_url'].rstrip('/') == 'https://api.deepseek.com' and p['endpoint'] == '/chat/completions',
                'CONNECTED_PROVIDER_ENDPOINT_DRIFT')
        maximum = config['planning_max_calls'] if role == 'planning' else min(config['subject_trial_max_calls'], p['remaining_horizon'])
        p.update(schema='stage2-connected-provider-profile-v1', live_transport_enabled=binding['live'],
                 transport_binding=binding, connected_config_hash=digest(raw),
                 max_logical_calls=maximum, max_transport_attempts=maximum,
                 max_request_bytes=8_000_000, max_response_bytes=8_000_000,
                 horizon_is_trial_censor_not_native_ceiling=True)
        profiles[role] = seal(p, 'profile_hash')
    return seal({'schema': 'stage2-connected-provider-bindings-v1', 'profiles': profiles,
                 'transport_binding': binding, 'automatic_paid_reviewer': False,
                 'automatic_replay': False, 'configured_model_version_is_verified_backend': False}, 'bindings_hash')


class ConnectedExchangeSource:
    def __init__(self, profile, transport, out, *, gate):
        verify_seal(profile, 'profile_hash')
        require(profile['schema'] == 'stage2-connected-provider-profile-v1'
                and profile['transport_binding'] == transport_binding(transport), 'CONNECTED_TRANSPORT_PROFILE_DRIFT')
        require(callable(gate), 'HOST_PROVIDER_PHASE_GATE_REQUIRED')
        self._profile = copy.deepcopy(profile); self._transport = transport; self._gate = gate
        self._retained_profile_hash = digest(profile)
        self.out = Path(out); require(not self.out.exists(), 'FRESH_PROVIDER_EXCHANGES_REQUIRED')
        self.out.mkdir(parents=True); _json(self.out / 'profile.json', profile)
        self.calls = 0; self.transport_attempts = 0; self.valid_responses = 0
        self.failed = False; self.in_flight = False

    @property
    def provider_calls(self):
        # Counts dispatch attempts, not successful inference. Historical counts
        # before the parent remain unknown. A timeout never refunds an attempt.
        return self.transport_attempts if self._profile['transport_binding']['live'] else 0

    def complete_agent(self, messages, metadata=None):
        require(not self.failed and not self.in_flight, 'PROVIDER_FIRST_ATTEMPT_FAILED_OR_IN_FLIGHT_NO_REPLAY')
        require(digest(self._profile) == self._retained_profile_hash, 'CONNECTED_PROFILE_MUTATED')
        require(self._profile['transport_binding'] == transport_binding(self._transport), 'CONNECTED_TRANSPORT_MUTATED')
        require(self._gate() is True, 'SUBJECT_PROVIDER_BEFORE_HOST_RELEASE')
        p = self._profile
        require(metadata is None or (type(metadata) is dict and set(metadata) <= {'role', 'turn', 'parent_checkpoint_hash'}),
                'BOUND_PROVIDER_METADATA_KEYS_REQUIRED')
        if metadata and 'turn' in metadata:
            require(type(metadata['turn']) is int and metadata['turn'] == p['native_history_length'] + self.calls + 1,
                    'BOUND_PROVIDER_NATIVE_TURN_DRIFT')
        require(self.calls < p['max_logical_calls'], 'BOUND_PROVIDER_BUDGET_EXHAUSTED')
        require(type(messages) is list and all(type(m) is dict and set(m) == {'role', 'content'}
                and isinstance(m['role'], str) and isinstance(m['content'], str) for m in messages),
                'EXACT_NATIVE_MESSAGES_REQUIRED')
        payload = {'model': p['model_alias'], 'messages': copy.deepcopy(messages),
                   'max_tokens': p['parameters']['max_tokens'], 'temperature': p['parameters']['temperature'],
                   'thinking': {'type': p['parameters']['thinking']}, 'response_format': {'type': 'json_object'}}
        raw = json.dumps(payload, ensure_ascii=False).encode()
        require(len(raw) <= p['max_request_bytes'], 'PROVIDER_REQUEST_BODY_LIMIT')
        self.calls += 1; directory = self.out / f'{self.calls:04d}'; directory.mkdir()
        failure = None; complete_body = False; self.in_flight = True
        try:
            _persist(directory / 'request.bin', raw)
            _json(directory / 'request.json', {'attempt': self.calls, 'profile_hash': p['profile_hash'],
                  'url': p['transport_binding']['url'], 'method': 'POST', 'body_hash': digest(raw),
                  'headers': {'Content-Type': 'application/json', 'Accept': 'application/json'},
                  'metadata': copy.deepcopy(metadata or {}), 'origin': p['transport_binding']['origin'],
                  'transport_attempt_intent': True, 'automatic_retry': False})
            self.transport_attempts += 1
            response = self._transport.send(raw, directory, p['timeout_seconds'], p['max_response_bytes'])
            complete_body = True
            require(200 <= response['status'] < 300, 'BOUND_PROVIDER_HTTP_FAILURE')
            def unique(pairs):
                row = {}
                for key, value in pairs:
                    require(key not in row, 'DUPLICATE_PROVIDER_RESPONSE_FIELD'); row[key] = value
                return row
            obj = json.loads(response['body'], object_pairs_hook=unique,
                             parse_constant=lambda _: require(False, 'NONFINITE_PROVIDER_RESPONSE'))
            require(type(obj) is dict and 'error' not in obj, 'BOUND_PROVIDER_APPLICATION_FAILURE')
            require(obj.get('model') in {p['model_alias'], p['expected_model_version']}, 'BOUND_PROVIDER_REPORTED_MODEL_DRIFT')
            require(isinstance(obj.get('id'), str) and obj['id'], 'BOUND_PROVIDER_RESPONSE_ID_REQUIRED')
            choices = obj.get('choices')
            require(type(choices) is list and len(choices) == 1 and type(choices[0]) is dict, 'EXACT_PROVIDER_CHOICE_REQUIRED')
            content = choices[0]['message']['content']
            require(isinstance(content, str), 'PROVIDER_CONTENT_TEXT_REQUIRED')
            require(choices[0].get('finish_reason') == 'stop', 'BOUND_PROVIDER_INCOMPLETE_RESPONSE')
            self.valid_responses += 1
            return {'content': content, 'response_id': obj['id'], 'model': obj['model'],
                    'usage': copy.deepcopy(obj.get('usage') or {}), 'provider_response': obj,
                    'finish_reason': 'stop'}
        except BaseException as exc:
            self.failed = True
            # Exceptions from HTTP or injected endpoints must not echo headers.
            failure = {'type': type(exc).__name__, 'message': 'CAPTURED_EXCHANGE_FAILED_NO_RETRY'}
            raise
        finally:
            self.in_flight = False
            body = directory / 'response.bin'
            _json(directory / 'receipt.json', seal({'schema': 'stage2-connected-exchange-v1',
                  'attempt': self.calls, 'profile_hash': p['profile_hash'], 'request_hash': digest(raw),
                  'response_hash': digest(body.read_bytes()) if body.exists() else None,
                  'response_body_complete': complete_body, 'failure': failure,
                  'logical_calls': self.calls, 'transport_attempts': self.transport_attempts,
                  'provider_calls': self.provider_calls, 'origin': p['transport_binding']['origin'],
                  'backend_identity_verified': False, 'credentials_saved': False, 'automatic_retry': False}, 'exchange_hash'))
