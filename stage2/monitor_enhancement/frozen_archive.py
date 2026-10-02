"""Read-only native archive adapter. Capture clocks are not global/causal clocks."""
from __future__ import annotations
import gzip
import io
import json
import re
import tarfile
from collections import Counter
from pathlib import Path, PurePosixPath
from arena.checkpoint_chronology import ordered_checkpoints
from stage2.r7_checkpoint_v1.common import digest


class ArchiveError(ValueError):
    pass


FILE_PATTERN = re.compile(r'(?<![\w./-])(?:[\w.-]+/)*[\w.-]+\.(?:py|js|html|json|md|css|ts|tsx|yml|yaml|txt)(?![\w./-])')


def pointer_token(value):
    return str(value).replace('~', '~0').replace('/', '~1')


def strings(value, pointer=''):
    if isinstance(value, str):
        yield pointer, value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from strings(v, pointer + '/' + pointer_token(k))
    elif isinstance(value, list):
        for k, v in enumerate(value):
            yield from strings(v, pointer + '/' + str(k))


class NativeArchive:
    def __init__(self, path, full_id, expected_sha):
        self.path = Path(path)
        raw = self.path.read_bytes()
        self.archive_sha = digest(raw)
        if self.archive_sha != expected_sha:
            raise ArchiveError('archive hash mismatch: ' + full_id)
        self.full_id = full_id
        self.tf = tarfile.open(fileobj=io.BytesIO(gzip.decompress(raw)), mode='r:')
        self.members = {}
        for m in self.tf.getmembers():
            name = m.name[2:] if m.name.startswith('./') else m.name
            if not m.isfile():
                continue
            if name in self.members or name.startswith('/') or '..' in PurePosixPath(name).parts:
                raise ArchiveError('unsafe or duplicate member: ' + name)
            self.members[name] = m
        self.cache, self.parsed, self.sources = {}, {}, {}
        self.observations, self.coverage = [], Counter()
        self.attempt_receipt = None
        receipt = self.path.parent / 'attempt_receipt.json'
        if receipt.exists():
            raw = receipt.read_bytes(); record = json.loads(raw)
            if record['archive_sha256'] != self.archive_sha or record['group_id'] + '-' + record['cell_id'] != full_id:
                raise ArchiveError('attempt receipt binding mismatch')
            self.attempt_receipt = {'sha256': digest(raw), 'record': record}

    def read(self, name):
        if name not in self.members:
            raise ArchiveError('missing native evidence: ' + name)
        if name not in self.cache:
            self.cache[name] = self.tf.extractfile(self.members[name]).read()
        return self.cache[name]

    def json(self, name):
        return json.loads(self.read(name))

    def source(self, name, pointer='', line=None):
        return {'archive_sha256': self.archive_sha, 'member': name,
                'member_sha256': digest(self.read(name)), 'json_pointer': pointer, 'line': line}

    def resolve(self, locator):
        name, line = locator['member'], locator.get('line')
        if locator['archive_sha256'] != self.archive_sha or digest(self.read(name)) != locator['member_sha256']:
            raise ArchiveError('source binding mismatch')
        key = (name, line)
        if key not in self.parsed:
            raw = self.read(name)
            if line is not None:
                if type(line) is not int or line < 1:
                    raise ArchiveError('invalid source line')
                raw = raw.splitlines()[line - 1]
            try:
                value = json.loads(raw)
            except (ValueError, UnicodeDecodeError):
                value = raw.decode('utf-8')
            self.parsed[key] = value
        value = self.parsed[key]
        pointer = locator['json_pointer']
        if pointer and not pointer.startswith('/'):
            raise ArchiveError('invalid JSON pointer')
        for token in pointer.split('/')[1:]:
            token = token.replace('~1', '/').replace('~0', '~')
            value = value[int(token)] if isinstance(value, list) else value[token]
        return value

    def emit(self, name, value, *, sequence, clock, kind, ref, pointer='', line=None,
             actor='UNKNOWN', source_kind='NATIVE_RECORD', version=None, content_hash=None,
             relation='EVENT_OBSERVES_OBJECT', span=None, **extras):
        locator = self.source(name, pointer, line)
        # Occurrence is part of event identity: identical bytes can be observed twice.
        identity = {'member': name, 'line': line, 'clock': clock, 'sequence': sequence}
        evidence = 'evidence:' + digest(locator)
        self.sources[evidence] = locator
        row = {'schema': 'RB-STAGE2-ENHANCED-OBSERVATION-v1',
               'trajectory_id': self.full_id, 'event_ref': self.full_id + ':native:' + digest(identity)[:24],
               'native_sequence': sequence, 'clock_id': clock, 'actor': str(actor or 'UNKNOWN'),
               'event_kind': kind, 'object_refs': [ref], 'written_refs': [],
               'downstream_legal_refs': [], 'preserve_refs': [], 'evidence_ref': evidence,
               'source_kind': source_kind, 'source_locator': locator, 'version': version,
               'content_hash': content_hash, 'field_path': pointer, 'text_span': span,
               'visibility_scope': 'FROZEN_EXTERNAL_EVIDENCE_NOT_WRITE_AUTHORITY',
               'object_relation': relation, 'field_value_hash': digest(value), **extras}
        row['observation_id'] = 'obs:' + digest(row)
        self.observations.append(row)

    def payload(self, name, value, *, sequence, clock, kind, ref=None, pointer='', line=None, **extras):
        args = dict(sequence=sequence, clock=clock, kind=kind, line=line, **extras)
        if ref is None:
            ref = 'record:' + digest({'member': name, 'line': line, 'pointer': pointer})
        self.emit(name, value, pointer=pointer, ref=ref, **args)
        for field, text in strings(value, pointer):
            for match in FILE_PATTERN.finditer(text):
                self.emit(name, text, pointer=field, ref='file:' + match.group(),
                          relation='EVENT_MENTIONS_OBJECT', span=[match.start(), match.end()], **args)

    def observer_stream(self, root):
        index = root + '/events.jsonl'; previous = -1; count = 0
        for line, raw in enumerate(self.read(index).splitlines(), 1):
            if not raw.strip():
                continue
            meta = json.loads(raw); seq = meta['sequence']
            if type(seq) is not int or seq <= previous:
                raise ArchiveError('non-increasing observer clock')
            previous = seq
            name = root + '/' + meta['raw_path']; payload = self.read(name)
            if digest(payload) != meta['sha256'] or len(payload) != meta['bytes']:
                raise ArchiveError('observer payload binding mismatch')
            try: value = json.loads(payload)
            except ValueError: value = payload.decode('utf-8')
            surface = meta['surface']
            actor = (value.get('source') or value.get('sent_from') or value.get('role')) if isinstance(value, dict) else 'UNKNOWN'
            if root in ('autogen_observer', 'metagpt_observer'):
                ref = 'message:' + str(value.get('id') or meta['sha256']) if isinstance(value, dict) else 'message:' + meta['sha256']
            else:
                prefix = 'retrieval-result' if '.hits.' in surface else 'memory-record' if 'memory' in surface else 'compression-record' if 'compress' in surface else 'query'
                ref = prefix + ':' + meta['sha256']
            args = dict(sequence=seq, clock=root, kind='NATIVE_OBSERVER_RECORD', actor=actor,
                        occurrence_locator=self.source(index, line=line), surface=surface)
            self.payload(name, value, ref=ref, **args)
            if '.hits.' in surface and isinstance(value, list):
                for i, hit in enumerate(value):
                    if isinstance(hit, dict) and hit.get('sha256'):
                        self.emit(name, hit, pointer='/' + str(i), ref='rag-hit:' + hit['sha256'], content_hash=hit['sha256'], **args)
            count += 1
        if not count:
            raise ArchiveError('empty observer stream')
        self.coverage.update(native_records=count, observer_records=count)

    def a2a(self):
        names = sorted(n for n in self.members if n.startswith('wire/') and n.endswith('-meta.json'))
        if not names:
            raise ArchiveError('missing A2A wire stream')
        seen = set()
        for name in names:
            meta = self.json(name); key = (meta['role'], meta['sequence'])
            if key in seen or type(key[1]) is not int:
                raise ArchiveError('invalid A2A occurrence')
            seen.add(key)
            for direction in ('request', 'response'):
                member = name[:-len('meta.json')] + direction + '.bin'
                raw = self.read(member)
                if digest(raw) != meta[direction + '_sha256']:
                    raise ArchiveError('A2A wire hash mismatch')
                try: value = json.loads(raw)
                except ValueError: value = raw.decode('utf-8')
                self.payload(member, value, sequence=key[1], clock='a2a:' + key[0], kind='A2A_WIRE_RECORD',
                             actor=key[0], ref='protocol-call:' + key[0] + ':' + str(key[1]),
                             direction=direction, occurrence_locator=self.source(name))
                self.coverage.update(native_records=1, wire_records=1)

    def mcp(self):
        names = sorted(n for n in self.members if re.fullmatch(r'capability_observer/\d+-.+\.(client_to_server|server_to_client)\.bin', n))
        if not names:
            result = self.json('natural_A_result.json'); history = result.get('history', [])
            if not history or result.get('turns') != len(history) or any(r.get('valid') is not False or r.get('actions') for r in history):
                raise ArchiveError('unexplained missing MCP wire evidence')
            self.coverage['explicit_zero_native_call_history'] = 1
            self.coverage['native_records'] = 0
            return
        for name in names:
            seq, tool, direction = re.fullmatch(r'capability_observer/(\d+)-(.+)\.(client_to_server|server_to_client)\.bin', name).groups()
            for line, raw in enumerate(self.read(name).splitlines(), 1):
                if not raw.strip(): continue
                value = json.loads(raw)
                args = dict(sequence=int(seq), clock='mcp_invocation', kind='MCP_WIRE_RECORD', line=line,
                            direction=direction, tool=tool, within_capture_sequence=line)
                self.payload(name, value, ref='protocol-call:mcp:' + seq + ':' + str(value.get('id', 'notification')), **args)
                if direction == 'client_to_server' and value.get('method') == 'tools/call':
                    params = value.get('params', {}); path = params.get('arguments', {}).get('path')
                    if params.get('name') in ('read_file', 'write_file') and isinstance(path, str):
                        self.emit(name, path, pointer='/params/arguments/path', ref='file:' + path,
                                  relation='EVENT_REQUESTS_' + ('READ' if params['name'] == 'read_file' else 'WRITE'), **args)
                self.coverage.update(native_records=1, wire_records=1)

    def checkpoints(self):
        ordered = ordered_checkpoints(self.tf, self.members)
        if not ordered: raise ArchiveError('missing checkpoints')
        previous = {}
        for _, name, obj in ordered:
            chronology = obj['_chronology']; seq = chronology['sequence']; clock = chronology['clock']
            if seq is None:
                clock = 'native_boundary:' + chronology['boundary']; seq = 0
            version = obj['checkpoint_hash']; current = obj['application_file_hashes']
            self.coverage['ledger_bound_checkpoints' if chronology['basis'] == 'FROZEN_CHECKPOINT_LEDGER' else 'native_ref_ordered_checkpoints'] += 1
            for path in sorted(set(current) | set(previous)):
                present = path in current; content = current.get(path)
                if present and digest(self.read(f'checkpoints/{version}/application/{path}')) != content:
                    raise ArchiveError('checkpoint file hash mismatch')
                pointer = '/application_file_hashes/' + pointer_token(path) if present else '/application_file_hashes'
                changed = bool(previous) and previous.get(path) != content
                self.emit(name, content if present else current, sequence=seq, clock=clock, kind='CHECKPOINT_FILE_STATE',
                          ref='file:' + path, pointer=pointer, actor='SYSTEM', source_kind='CHECKPOINT_SNAPSHOT',
                          version=version, content_hash=content, chronology=chronology,
                          state_presence='PRESENT' if present else 'DELETED',
                          changed_since_previous_checkpoint=changed, previous_content_hash=previous.get(path))
                self.coverage['checkpoint_file_changes'] += int(changed)
            for i, ref in enumerate(obj.get('external_carrier_refs', [])):
                self.emit(name, ref, sequence=seq, clock=clock, kind='CHECKPOINT_CARRIER',
                          ref=ref if isinstance(ref, str) else 'carrier:' + digest(ref),
                          pointer='/external_carrier_refs/' + str(i), source_kind='CHECKPOINT_SNAPSHOT',
                          version=version, chronology=chronology, actor='SYSTEM')
            native = f'checkpoints/{version}/native_state.json'
            if native in self.members:
                state = self.json(native)
                if digest(state) != obj['native_state_sha256']:
                    raise ArchiveError('checkpoint native state hash mismatch')
                for holder, messages in state.get('inbox', {}).items():
                    for i, message in enumerate(messages):
                        self.emit(native, message, sequence=seq, clock=clock, kind='CHECKPOINT_INBOX_MESSAGE',
                                  ref='snapshot-message:' + digest(message),
                                  pointer='/inbox/' + pointer_token(holder) + '/' + str(i),
                                  actor=message.get('from', 'UNKNOWN'), source_kind='CHECKPOINT_SNAPSHOT',
                                  version=version, chronology=chronology, observed_holder=holder)
            previous = current
        self.coverage['checkpoints'] = len(ordered)
        self.coverage['last_observed_file_count'] = len(previous)
        self.coverage['terminal_checkpoint_present'] = int(ordered[-1][2]['event_ref'].endswith(':terminal'))

    def build(self):
        system = self.full_id.split('-')[1]
        if system == 'X3': self.a2a()
        elif system == 'X4': self.mcp()
        else: self.observer_stream({'X1': 'autogen_observer', 'X2': 'metagpt_observer'}.get(system, 'capability_observer'))
        self.checkpoints()
        terminal = [n for n in ('natural_A_result.json', 'failure.json') if n in self.members]
        for name in terminal:
            self.emit(name, self.json(name), sequence=0, clock='terminal_record', kind='TERMINAL_RECORD',
                      ref='state:terminal', source_kind='TERMINAL_RECORD')
        if not terminal:
            receipt = (self.attempt_receipt or {}).get('record', {})
            if type(receipt.get('runner_exit_code')) is not int or receipt['runner_exit_code'] == 0:
                raise ArchiveError('missing terminal record without failed attempt receipt')
            self.coverage['failed_attempt_without_terminal_record'] = 1
        return self.observations, dict(self.coverage), self.sources

    def verify_observations(self):
        for row in self.observations:
            value = self.resolve(row['source_locator'])
            if digest(value) != row['field_value_hash']:
                raise ArchiveError('field value binding mismatch')
            if row.get('occurrence_locator'): self.resolve(row['occurrence_locator'])
            span = row.get('text_span')
            if span is not None and 'file:' + value[span[0]:span[1]] != row['object_refs'][0]:
                raise ArchiveError('field span mismatch')
        return len(self.observations)
