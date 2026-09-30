#!/usr/bin/env python3
"""Validate corrected bundles offline without invoking an evaluator."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'stage2/replication_v2/chronology_correction_v1'


def read(name):
    return json.loads((OUT / name).read_text())


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    summary = read('summary.json')
    count = 0
    for item in summary['corrected_packet_archives']:
        compressed = (OUT / item['path']).read_bytes()
        assert digest(compressed) == item['sha256']
        raw = gzip.decompress(compressed)
        assert digest(raw) == item['uncompressed_sha256']
        packets = [json.loads(line) for line in raw.splitlines()]
        assert len(packets) == item['packet_count']
        count += len(packets)
        for packet in packets:
            expected = packet['packet_sha256']
            packet['packet_sha256'] = ''
            encoded = json.dumps(packet, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
            assert digest(encoded) == expected
            state = packet.get('repository_state')
            if state and 'changed_file_snapshots' in state:
                evidence = {e['ref']: e for e in packet['evidence']}
                for snapshot in state['changed_file_snapshots']:
                    # Shape is defined by the full-context builder, not old file sorting.
                    endpoint = state['first_manifest'] if snapshot['position'] == 'earliest' else state['last_manifest']
                    assert evidence[snapshot['evidence_ref']]['path'].startswith(endpoint.rsplit('/manifest.json', 1)[0] + '/application/')
    assert count == 209
    pairs = read('paired_changes.json')
    natural = read('natural_changes.json')
    deps = read('semantic_reference_dependencies.json')
    assert len(pairs) == summary['paired']['arms'] == 90
    assert len({(r['group_id'], r['cell_id']) for r in pairs}) == summary['paired']['pairs'] == 45
    for field in ('endpoint_changed', 'repository_diff_changed'):
        assert sum(r[field] for r in pairs) == summary['paired'][field]
    assert sorted({r['group_id'] + '-' + r['cell_id'] for r in pairs if r['repository_diff_changed']}) == summary['paired']['affected_pairs']
    for kind, expected in summary['natural'].items():
        rows = [r for r in natural if r['kind'] == kind]
        assert len(rows) == expected['packets']
        for field in ('repository_diff_changed', 'frozen_baseline_binding_verified'):
            assert sum(r[field] for r in rows) == expected[field]
    assert len(deps) == 240
    assert dict(Counter(r['status'] for r in deps)) == summary['semantic_dependencies']
    for key in ('replacement_semantic_counts', 'replacement_engineering_effect_counts', 'replacement_monitor_performance'):
        assert summary[key] is None
    for key in ('subject_calls', 'provider_calls', 'repair_calls'):
        assert summary[key] == 0
    assert summary['raw_evidence_modified'] is False
    for row in read('source_commits.json'):
        cfg = json.loads((ROOT / f"configs/stage2_{row['group_id'].lower()}_ab_paired_semantic_audit_v1.json").read_text())
        for key in ('natural_A_evidence_commit', 'repair_B_evidence_commit'):
            assert row[key] == cfg['source'][key]
    a2a = read('a2a_g1_x3_t3_request_order.json')
    source = ROOT / 'stage2/natural_v7/X3-T3/first_attempt.tar.gz'
    assert digest(source.read_bytes()) == a2a['archive_sha256']
    assert len(a2a['rows']) == a2a['request_count'] == 14
    assert [r['depth'] for r in a2a['rows']] == list(range(14))
    with tarfile.open(source) as archive:
        members = {m.name.removeprefix('./'): m for m in archive.getmembers()}
        for row in a2a['rows']:
            raw = archive.extractfile(members[row['member']]).read()
            assert digest(raw) == row['sha256']
            obj = json.loads(raw)
            payload = json.loads(obj['params']['message']['parts'][0]['text'])
            for key in ('content', 'depth', 'remaining_turns', 'sender', 'target'):
                assert row[key] == payload[key]
    print('PASS: 209 packets, digests, endpoint excerpts, impact accounting and frozen provenance')


if __name__ == '__main__':
    main()
