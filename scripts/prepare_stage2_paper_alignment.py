#!/usr/bin/env python3
"""Build corrected review packets and X4 prefix readiness with zero model calls."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from stage2.r7_checkpoint_v1.common import digest
from stage2.route_repair.branch_fields import save, seal, require
from stage2.route_repair.paper_alignment import build_review_material, load_contract, assess_mechanism_entry
from stage2.route_repair.prefix_context import PrefixMCPContext
from stage2.monitor_enhancement.frozen_archive import NativeArchive


def build(source_root):
    material = build_review_material(ROOT)
    contract = load_contract(ROOT)
    native = json.loads((ROOT / 'configs/stage2_same_parent_native_mcp_v1.json').read_bytes())
    fid = native['full_id']
    case = next(c for c in json.loads((ROOT / 'configs/stage2_terminal_route_repair_first_round_v1.json').read_bytes())['cases']
                if c['full_id'] == fid)
    archive = source_root / 'G3A/stage2/replication_v2/G3/natural_A/X4-T2/first_attempt.tar.gz'
    ar = NativeArchive(archive, fid, case['archive_sha256'])
    try:
        # Whole ledger is available only to retrospective readiness preparation.
        # Every assessment is reconstructed using its own prefix-only context.
        ledger = ar.json('checkpoint_ledger.json')['checkpoints']
        parents = {}
        for sequence in contract['retrospective_prefix_checks']:
            rows = [r for r in ledger if r['model_decision_sequence'] == sequence
                    and r['boundary'] != 'FIRST_MONITOR_REPAIR_ELIGIBLE_POINT']
            require(len(rows) == 1, 'PAPER_NATIVE_PARENT_AMBIGUOUS')
            parents[sequence] = rows[0]['checkpoint_hash']
        assessments = []
        for sequence, checkpoint in parents.items():
            try:
                context = PrefixMCPContext(archive, full_id=fid, archive_sha256=case['archive_sha256'],
                                           parent_checkpoint_hash=checkpoint, retain_failed_reads=True)
                try:
                    row = assess_mechanism_entry(context, contract)
                    assessments.append(row)
                finally:
                    context.close()
            except ValueError as error:
                assessments.append({'parent_native_sequence': sequence, 'parent_checkpoint_hash': checkpoint,
                    'repair_entry_ready': False, 'prefix_restore_status': 'BLOCKED', 'reason': str(error),
                    'provider_calls': 0})
        material['entry_readiness.json'] = assessments
        obs = next(r for r in material['case_routes.json'] if r['full_id'] == fid)
        require(obs['archive_sha256'] == ar.archive_sha
                and parents[4] == native['parent_checkpoint_hash'], 'PAPER_NATIVE_CASE_BINDING')
        native_witnesses = []
        for carrier in obs['selected_claim_carriers']:
            raw = ar.read(carrier['member'])
            require(digest(raw) == carrier['member_sha256'], 'PAPER_NATIVE_MESSAGE_MEMBER_DRIFT')
            value = json.loads(raw)
            for part in carrier['json_pointer'].split('/')[1:]:
                key = part.replace('~1', '/').replace('~0', '~')
                value = value[int(key)] if isinstance(value, list) else value[key]
            require(value == carrier['text'], 'PAPER_NATIVE_MESSAGE_VALUE_DRIFT')
            native_witnesses.append({**carrier, 'archive_sha256': ar.archive_sha,
                                     'native_bytes_and_field_verified': True})
        for transition in obs['ordered_file_transitions']:
            for file, value in transition.get('file_contents', {}).items():
                raw = ar.read(value['path'])
                require(digest(raw) == value['sha256'] and raw.decode() == value['text'],
                        'PAPER_NATIVE_FILE_VALUE_DRIFT')
                native_witnesses.append({'file': file, 'sequence': transition['sequence'],
                    'member': value['path'], 'member_sha256': value['sha256'], 'text': value['text'],
                    'archive_sha256': ar.archive_sha, 'native_bytes_and_field_verified': True})
        terminal = ar.json('natural_A_result.json')
        expected_summary = next(e for e in obs['run_summary_previews'] if e['path'] == 'natural_A_result.json')
        require(digest(ar.read('natural_A_result.json')) == expected_summary['sha256'], 'PAPER_NATIVE_TERMINAL_BINDING')
        native_witnesses.append({'member': 'natural_A_result.json', 'member_sha256': digest(ar.read('natural_A_result.json')),
            'archive_sha256': ar.archive_sha, 'native_bytes_and_field_verified': True, 'value': terminal})
        material['G3-X4-T2_native_witnesses.json'] = native_witnesses
        material['summary.json']['x4_verified_native_witnesses'] = len(native_witnesses)
        material['summary.json']['mechanism_entry_ready'] = any(r['repair_entry_ready'] for r in assessments)
    finally:
        ar.tf.close()
    return material


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--compare-frozen', action='store_true')
    args = parser.parse_args()
    require(not args.out.exists(), 'PAPER_FRESH_OUTPUT_REQUIRED')
    material = build(args.source_root)
    for name, value in material.items():
        save(args.out / name, value)
    sources = ['stage2/route_repair/paper_alignment.py', 'scripts/prepare_stage2_paper_alignment.py',
               'stage2/route_repair/prefix_context.py',
               'stage2/route_repair/native_continuation.py', 'stage2/monitor_enhancement/frozen_archive.py',
               'arena/checkpoint_chronology.py',
               'configs/stage2_paper_mechanism_contract_v1.json']
    manifest = seal({'schema': 'stage2-paper-alignment-seal-v1',
        'implementation_hashes': {p: digest((ROOT / p).read_bytes()) for p in sources},
        'frozen_inputs': load_contract(ROOT)['frozen_inputs'],
        'artifacts': {name: digest((args.out / name).read_bytes()) for name in material},
        'provider_calls': 0, 'subject_calls': 0, 'repair_calls': 0, 'natural_reruns': 0}, 'seal_hash')
    save(args.out / 'seal.json', manifest)
    if args.compare_frozen:
        frozen = ROOT / 'stage2/replication_v2/paper_mechanism_alignment_v1'
        require(manifest == json.loads((frozen / 'seal.json').read_bytes()), 'PAPER_SEAL_DRIFT')
        for name in material:
            require((args.out / name).read_bytes() == (frozen / name).read_bytes(), 'PAPER_ARTIFACT_DRIFT:' + name)
    print(json.dumps(material['summary.json'], ensure_ascii=False))


if __name__ == '__main__':
    main()
