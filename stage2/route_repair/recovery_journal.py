"""Durable host-owned journal and read-only interruption reconciliation.

Single coordinator only. Recovery reports a next decision and never replays a
write, reruns a subject, rolls back, or treats a content hash as authorization.
"""
import copy
import json
import os
from pathlib import Path

from stage2.route_repair.branch_fields import require, seal, verify_seal


class RecoveryJournal:
    def __init__(self, root, binding):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.binding = copy.deepcopy(binding)
        require(set(binding) == {'bundle_hash', 'contract_hash', 'parent_checkpoint_hash'}, 'JOURNAL_BINDING_REQUIRED')
        self.rows = self._load()

    def _load(self):
        rows = []
        previous = None
        for index, path in enumerate(sorted(self.root.glob('*.json')), 1):
            require(path.name == f'{index:06d}.json', 'JOURNAL_SEQUENCE_GAP')
            row = json.loads(path.read_text())
            verify_seal(row, 'entry_hash')
            require(row['sequence'] == index and row['previous_hash'] == previous, 'JOURNAL_CHAIN_DRIFT')
            require(row['binding'] == self.binding, 'JOURNAL_PARENT_DRIFT')
            previous = row['entry_hash']
            rows.append(row)
        return rows

    def append(self, phase, payload):
        require(self._load() == self.rows, 'JOURNAL_STALE_COORDINATOR')
        row = seal({'schema': 'stage2-repair-recovery-entry-v1', 'sequence': len(self.rows) + 1,
                    'previous_hash': self.rows[-1]['entry_hash'] if self.rows else None,
                    'binding': self.binding, 'phase': phase, 'payload': copy.deepcopy(payload)}, 'entry_hash')
        # Exclusive create rejects a second coordinator at the same sequence.
        # A torn write is rejected on recovery rather than silently discarded.
        with (self.root / f'{row["sequence"]:06d}.json').open('x') as stream:
            json.dump(row, stream, sort_keys=True, ensure_ascii=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        fd = os.open(self.root, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        self.rows.append(row)
        return copy.deepcopy(row)

    def intent(self, action_id, target_ref, before_hash, expected_hash):
        require(not any(r['phase'] == 'ACTION_INTENT' and r['payload']['action_id'] == action_id for r in self.rows),
                'JOURNAL_ACTION_ALREADY_ATTEMPTED')
        return self.append('ACTION_INTENT', {'action_id': action_id, 'target_ref': target_ref,
                                            'before_hash': before_hash, 'expected_hash': expected_hash})

    def complete(self, action_id, actual_hash, native_receipt):
        intent = next((r for r in self.rows if r['phase'] == 'ACTION_INTENT' and r['payload']['action_id'] == action_id), None)
        require(intent is not None, 'JOURNAL_ACTION_INTENT_REQUIRED')
        require(not any(r['phase'] == 'ACTION_RESULT' and r['payload']['action_id'] == action_id for r in self.rows),
                'JOURNAL_ACTION_ALREADY_RECORDED')
        status = 'POSTCONDITION_PASSED' if actual_hash == intent['payload']['expected_hash'] else 'POSTCONDITION_FAILED'
        return self.append('ACTION_RESULT', {'action_id': action_id, 'actual_hash': actual_hash,
                                             'status': status, 'native_receipt': copy.deepcopy(native_receipt)})

    def reconcile(self, current_hash_reader):
        require(self._load() == self.rows, 'JOURNAL_STALE_COORDINATOR')
        results = {r['payload']['action_id']: r['payload'] for r in self.rows if r['phase'] == 'ACTION_RESULT'}
        rows = []
        for row in self.rows:
            if row['phase'] != 'ACTION_INTENT':
                continue
            intent = row['payload']
            action_id = intent['action_id']
            actual = current_hash_reader(intent['target_ref'])
            # Later actions may share an object. Inspect the latest intended
            # version and retain earlier results instead of guessing their state.
            later = any(r['phase'] == 'ACTION_INTENT' and r['sequence'] > row['sequence']
                        and r['payload']['target_ref'] == intent['target_ref'] for r in self.rows)
            if later:
                decision = 'INTERMEDIATE_VERSION_REQUIRES_RECEIPT_REVIEW'
            elif actual == intent['expected_hash']:
                decision = 'EXPECTED_STATE_PRESENT_NO_REPLAY'
            elif actual == intent['before_hash'] and action_id not in results:
                decision = 'BEFORE_STATE_PRESENT_REVALIDATE_BEFORE_NEW_PLAN'
            else:
                decision = 'DIVERGED_OR_FAILED_STOP'
            rows.append({'action_id': action_id, 'current_hash': actual, 'decision': decision,
                         'recorded_result': results.get(action_id)})
        return {'binding': self.binding, 'actions': rows, 'automatic_replay_enabled': False,
                'rollback_performed': False, 'native_restore_proven': False}
