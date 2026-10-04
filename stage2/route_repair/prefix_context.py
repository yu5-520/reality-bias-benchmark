"""Observed MCP prefix without later checkpoints, wire calls or terminal answers.

Only the frozen experiment-owned host/structural-bridge correspondence is used
to bind invocation membership. This is not a universal cross-clock ordering
rule. Ambiguous host envelopes or missing wire evidence fail closed. Missing
historical provider I/O is explicitly retained as a limitation.
"""
import copy
import json
import re
from collections import defaultdict
from types import SimpleNamespace

from stage2.r7_checkpoint_v1.common import digest
from stage2.native_v7.software_host_v1 import TASKS
from stage2.monitor_enhancement.frozen_archive import NativeArchive
from stage2.monitor_enhancement.evidence_graph import EvidenceGraph
from stage2.route_repair.native_continuation import load_host_parent, continuation_blocker
from stage2.route_repair.branch_fields import require, seal

TOOLS = {'ACTION_LIST_FILES': 'list_files', 'ACTION_READ_FILE': 'read_file',
         'ACTION_WRITE_FILE': 'write_file', 'ACTION_RUN_TESTS': 'run_tests'}
WIRE = re.compile(r'capability_observer/(\d+)-(.+)\.(client_to_server|server_to_client|server_stderr)\.bin')


class PrefixMCPContext:
    def __init__(self, archive, *, full_id, archive_sha256, parent_checkpoint_hash):
        require(full_id.split('-')[1] == 'X4', 'PREFIX_BINDING_ONLY_SUPPORTS_NATIVE_MCP_HOST')
        self._archive = NativeArchive(archive, full_id, archive_sha256)
        ar = self._archive
        try:
            whole_ledger = ar.json('checkpoint_ledger.json')
            host_context = SimpleNamespace(raw=ar.read, ledger=whole_ledger)
            parent = load_host_parent(host_context, parent_checkpoint_hash)
            require(continuation_blocker(parent) is None, 'PREFIX_PARENT_NOT_CONTINUABLE')
            state = parent['state']
            cutoff = len(state['history'])
            # Each valid envelope's action count is recorded by the frozen host.
            # Reject invalid/partial envelopes: the bridge could have recorded
            # rejected actions whose native execution cannot be inferred.
            require(all(h['valid'] is True and type(h['actions']) is int and h['actions'] >= 0
                        for h in state['history']), 'AMBIGUOUS_PREFIX_ENVELOPE_MEMBERSHIP')
            native_rows, annotations, allowed_cp = [], [], set()
            previous = -1
            for row in whole_ledger['checkpoints']:
                seq = row['model_decision_sequence']
                require(type(seq) is int and seq >= previous, 'PREFIX_LEDGER_CLOCK_INVALID')
                previous = seq
                if seq > cutoff: continue
                cp = row['checkpoint_hash']
                p = load_host_parent(host_context, cp)
                require(p['state']['history'] == state['history'][:seq], 'PREFIX_HISTORY_BINDING_MISMATCH')
                if row['event_ref'] == p['manifest']['event_ref']:
                    require(row['boundary'] != 'TERMINAL' and p['state']['stop_reason'] is None,
                            'EARLY_PREFIX_CONTAINS_TERMINAL_OR_STOPPED_STATE')
                    native_rows.append(copy.deepcopy(row)); allowed_cp.add(cp)
                else:
                    require(row['boundary'] == 'FIRST_MONITOR_REPAIR_ELIGIBLE_POINT',
                            'PREFIX_UNSUPPORTED_LEDGER_ANNOTATION')
                    annotations.append(copy.deepcopy(row))
            require({r['model_decision_sequence'] for r in native_rows} == set(range(cutoff + 1)),
                    'PREFIX_NATIVE_CAPTURE_GAP')
            events = ar.json('monitor_evidence.json')
            prefix_count = sum(h['actions'] for h in state['history'])
            selected_events = events[:prefix_count]
            require(len(selected_events) == prefix_count, 'PREFIX_STRUCTURAL_ACTION_GAP')
            cursor, tool_rows = 0, []
            action_bindings = []
            for turn in state['history']:
                rows = selected_events[cursor:cursor + turn['actions']]
                for index, row in enumerate(rows, cursor):
                    require(row['sequence'] == index + 1 and row['actor'] == turn['role']
                            and row['kind'].startswith('ACTION_'), 'PREFIX_HOST_BRIDGE_CORRESPONDENCE_MISMATCH')
                    # A finalize may stop before remaining actions run. A prefix
                    # with such an envelope is not supported by this binding.
                    require(row['kind'] != 'ACTION_FINALIZE', 'PREFIX_FINALIZE_ACTION_AMBIGUITY')
                    binding = {'structural_sequence': index + 1, 'host_turn': turn['turn'],
                               'actor': turn['role'], 'kind': row['kind']}
                    if row['kind'] in TOOLS:
                        tool_rows.append((row, binding))
                    action_bindings.append(binding)
                cursor += turn['actions']
            wire_files = defaultdict(dict)
            for name in ar.members:
                match = WIRE.fullmatch(name)
                if match:
                    seq, tool, direction = match.groups()
                    wire_files[int(seq)][direction] = (name, tool)
            invocations = []
            for i, (row, binding) in enumerate(tool_rows, 1):
                require(i in wire_files and {'client_to_server', 'server_to_client'} <= set(wire_files[i]),
                        'PREFIX_NATIVE_MCP_WIRE_GAP')
                pair = wire_files[i]
                tool = TOOLS[row['kind']]
                require(all(t == tool for _, t in pair.values()), 'PREFIX_MCP_TOOL_ORDER_MISMATCH')
                outgoing = [json.loads(line) for line in ar.read(pair['client_to_server'][0]).splitlines() if line.strip()]
                incoming = [json.loads(line) for line in ar.read(pair['server_to_client'][0]).splitlines() if line.strip()]
                calls = [r for r in outgoing if r.get('method') == 'tools/call']
                require(len(calls) == 1 and calls[0]['params']['name'] == tool,
                        'PREFIX_MCP_INVOCATION_AMBIGUITY')
                call = calls[0]
                replies = [r for r in incoming if r.get('id') == call['id']]
                require(len(replies) == 1 and 'result' in replies[0] and 'error' not in replies[0]
                        and not replies[0]['result'].get('isError', False), 'PREFIX_MCP_TOOL_RESULT_NOT_ESTABLISHED')
                if tool in {'read_file', 'write_file'}:
                    require(row['object_refs'] == ['file:' + call['params']['arguments']['path']],
                            'PREFIX_MCP_PATH_BINDING_MISMATCH')
                binding['mcp_invocation'] = i
                invocations.append({**copy.deepcopy(binding),
                    'client_source': ar.source(pair['client_to_server'][0]),
                    'server_source': ar.source(pair['server_to_client'][0]),
                    'basis': 'FROZEN_HOST_HISTORY_AND_PASSIVE_BRIDGE_PLUS_NATIVE_TOOL_REQUEST',
                    'semantic_dependency_established': False})

            allowed = {'checkpoint_ledger.json', 'monitor_evidence.json'}
            for name in ar.members:
                if any(name.startswith('checkpoints/' + cp + '/') for cp in allowed_cp): allowed.add(name)
                match = WIRE.fullmatch(name)
                if match and 1 <= int(match.group(1)) <= len(tool_rows): allowed.add(name)
            # The archive remains immutable. Only the host-side derivation sees
            # whole ledger/event members; planner tools never return them whole.
            self._allowed_members = allowed - {'checkpoint_ledger.json', 'monitor_evidence.json'}
            ar.members = {n: m for n, m in ar.members.items() if n in allowed}
            ar.mcp()
            ar.checkpoints()
            for row in native_rows:
                cp = row['checkpoint_hash']; seq = row['model_decision_sequence']
                for member, kind, ref in [('native_state.json', 'CHECKPOINT_HOST_STATE', 'state:host_parent'),
                                          ('model_context.json', 'CHECKPOINT_MODEL_CONTEXT', 'state:model_context')]:
                    name = 'checkpoints/' + cp + '/' + member
                    ar.payload(name, ar.json(name), sequence=seq, clock='model_decision_sequence', kind=kind,
                               ref=ref, source_kind='CHECKPOINT_SNAPSHOT', version=cp, actor='SYSTEM')
            for index, row in enumerate(selected_events):
                binding = action_bindings[index]
                ar.payload('monitor_evidence.json', row, pointer='/' + str(index),
                    sequence=row['sequence'], clock='structural_bridge', kind='PREFIX_STRUCTURAL_RECORD',
                    ref=row['object_refs'][0], actor=row['actor'], source_kind='PASSIVE_STRUCTURAL_COPY',
                    prefix_membership_binding=copy.deepcopy(binding))
            ar.verify_observations()
            builder = EvidenceGraph()
            for o in ar.observations: builder.add_observation(o)
            self.graph = builder.snapshot()
            self.parent = parent
            self.parent_checkpoint_hash = parent_checkpoint_hash
            self.ledger = {'checkpoints': [*native_rows, *annotations]}
            self.files_by_checkpoint = {}
            self.file_versions = defaultdict(list)
            for rank, row in enumerate(native_rows):
                cp = row['checkpoint_hash']
                manifest = ar.json('checkpoints/' + cp + '/manifest.json')
                self.files_by_checkpoint[cp] = copy.deepcopy(manifest['application_file_hashes'])
                for path, sha in manifest['application_file_hashes'].items():
                    self.file_versions['file:' + path].append({'checkpoint_hash': cp, 'capture_index': rank,
                        'native_sequence': row['model_decision_sequence'], 'boundary': row['boundary'],
                        'clock_id': 'model_decision_sequence', 'content_sha256': sha,
                        'content_source': ar.source('checkpoints/' + cp + '/application/' + path)})
            self._observations = {o['observation_id']: o for o in self.graph['observations']}
            self._nodes = {n['ref']: n for n in self.graph['nodes']}
            self.access = SimpleNamespace(nodes=self._nodes, archive=SimpleNamespace(name=str(archive)))
            # Compatibility mapping for sealed offline field/planning primitives.
            # This internal key selects the current parent and is never described
            # as a terminal checkpoint in the prefix catalog or evidence.
            self.case = {'full_id': full_id, 'archive_sha256': archive_sha256,
                         'graph_hash': self.graph['graph_hash'], 'terminal_checkpoint_hash': parent_checkpoint_hash}
            self.prefix_receipt = seal({'schema': 'stage2-observed-native-mcp-prefix-v1',
                'full_id': full_id, 'archive_sha256': archive_sha256, 'parent_checkpoint_hash': parent_checkpoint_hash,
                'parent_native_sequence': cutoff, 'native_checkpoint_count': len(native_rows),
                'structural_record_count': prefix_count, 'mcp_invocation_count': len(tool_rows),
                'invocation_membership_bindings': invocations, 'monitor_annotations': annotations,
                'graph_hash': self.graph['graph_hash'], 'observations': len(self.graph['observations']),
                'all_observed_prefix_nodes_available': len(self.graph['nodes']),
                'future_suffix_visible': False, 'terminal_answer_visible': False,
                'coverage': 'ALL_AVAILABLE_MEMBERS_WITH_VERIFIED_PREFIX_MEMBERSHIP',
                'cross_clock_semantic_order_inferred': False,
                'historical_provider_prompt_response_captured': False,
                'missing_evidence': ['EXACT_HISTORICAL_PROVIDER_PROMPT_AND_RESPONSE_BYTES_NOT_IN_ARCHIVE'],
                'semantic_lineage_complete': False, 'live_execution_ready': False}, 'prefix_hash')
        except BaseException:
            ar.tf.close()
            raise

    def close(self): self._archive.tf.close()

    def raw(self, name):
        require(name in self._allowed_members, 'MEMBER_OUTSIDE_VERIFIED_PREFIX')
        return self._archive.read(name)

    def locator(self, name):
        require(name in self._allowed_members, 'LOCATOR_OUTSIDE_VERIFIED_PREFIX')
        return self._archive.source(name)

    def read_file(self, ref, checkpoint_hash=None):
        cp = checkpoint_hash or self.parent_checkpoint_hash
        require(ref.startswith('file:') and ref[5:] in self.files_by_checkpoint.get(cp, {}),
                'FILE_VERSION_OUTSIDE_VERIFIED_PREFIX')
        name = 'checkpoints/' + cp + '/application/' + ref[5:]
        return {'ref': ref, 'checkpoint_hash': cp, 'content': self.raw(name).decode(), 'source_locator': self.locator(name)}

    def observation_source(self, observation_id):
        require(observation_id in self._observations, 'OBSERVATION_OUTSIDE_VERIFIED_PREFIX')
        o = self._observations[observation_id]
        value = self._archive.resolve(o['source_locator'])
        return {'observation': copy.deepcopy(o),
                'source_text': value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)}

    def node_context(self, ref):
        require(ref in self._nodes, 'NODE_OUTSIDE_VERIFIED_PREFIX')
        grouped = defaultdict(list)
        for o in self.graph['observations']:
            if ref in o['object_refs']: grouped[o['clock_id']].append(copy.deepcopy(o))
        return {'ref': ref, 'node_type': self._nodes[ref]['node_type'],
                'file_versions': copy.deepcopy(self.file_versions.get(ref, [])),
                'observations_by_clock': dict(grouped),
                'graph_edges': [copy.deepcopy(e) for e in self.graph['edges']
                                if ref in {e['source_ref'], e['destination_ref']}],
                'write_authority_granted': False, 'cross_clock_order_inferred': False,
                'semantic_dependency_inferred': False}

    def catalog(self, original_task):
        require(original_task == TASKS[self.parent['state']['task_id']], 'PREFIX_TASK_BINDING_MISMATCH')
        return seal({'schema': 'stage2-observed-prefix-route-context-v1',
            'original_task': copy.deepcopy(original_task), 'parent_checkpoint_hash': self.parent_checkpoint_hash,
            'parent_is_terminal': False, 'graph_hash': self.graph['graph_hash'],
            'archive_sha256': self.case['archive_sha256'], 'all_node_refs': sorted(self._nodes),
            'node_count': len(self._nodes), 'edge_count': len(self.graph['edges']),
            'observation_count': len(self.graph['observations']),
            'all_file_versions': copy.deepcopy(dict(self.file_versions)),
            'current_file_sources': {ref: self.read_file(ref)['source_locator'] for ref in self.file_versions},
            'source_queries': ['node_context(ref)', 'read_file(ref, prefix_checkpoint_hash)',
                               'observation_source(prefix_observation_id)'],
            'prefix_receipt': copy.deepcopy(self.prefix_receipt),
            'visibility_scope': 'COMPLETE_OBSERVED_PREFIX_WITHOUT_DEPTH_CUTOFF',
            'audit_verdicts_included': False, 'live_execution_enabled': False}, 'context_hash')
