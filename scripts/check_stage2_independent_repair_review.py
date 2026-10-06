#!/usr/bin/env python3
"""Prepare read-only post-repair review evidence; no evaluator or native action."""
import argparse
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from stage2.r7_checkpoint_v1.common import digest
from stage2.route_repair.branch_fields import require, save, verify_seal
from stage2.route_repair.route_context import CompleteRouteContext
from stage2.route_repair.system_contract import read_capture_member
from stage2.route_repair.independent_review import RepairReviewContext


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--compare-frozen', action='store_true')
    args = parser.parse_args()
    if args.out.exists(): parser.error('fresh output required')
    dataset = ROOT / 'stage2/replication_v2/monitor_repair_system_integration_v1'
    system_seal = json.loads((dataset / 'seal.json').read_text()); verify_seal(system_seal, 'seal_hash')
    for path, expected in system_seal['artifact_hashes'].items():
        require(digest((dataset / path).read_bytes()) == expected, 'SYSTEM_INPUT_ARTIFACT_DRIFT:' + path)
    for path, expected in {**system_seal['implementation_hashes'], **system_seal['input_hashes']}.items():
        require(digest((ROOT / path).read_bytes()) == expected, 'SYSTEM_INPUT_DEPENDENCY_DRIFT:' + path)
    with gzip.open(dataset / 'full_graph_before.json.gz') as stream: before = json.load(stream)
    with gzip.open(dataset / 'full_graph_after.json.gz') as stream: after = json.load(stream)
    contract = json.loads((dataset / 'system_contract.json').read_text())
    assessment = json.loads((dataset / 'continuation_assessment.json').read_text())
    rules = json.loads((ROOT / 'configs/r8_dynamic_semantic_audit_contract_v0.4.json').read_text())
    lineage = json.loads((ROOT / 'configs/stage2_r6_grade_semantic_audit_rules_v1.json').read_text())
    case = next(c for c in json.loads((ROOT / 'configs/stage2_terminal_route_repair_first_round_v1.json').read_text())['cases']
                if c['full_id'] == 'G3-X4-T2')
    archive = args.source_root / 'G3A/stage2/replication_v2/G3/natural_A/X4-T2/first_attempt.tar.gz'
    native = CompleteRouteContext(before, archive, case)
    try:
        context = RepairReviewContext(native, contract, before, after, assessment,
            branch_source_reader=lambda row: read_capture_member(dataset, row), semantic_rules=rules,
            lineage_rules=lineage, repair_actor_id='OFFLINE_MANUAL_PLAN_COORDINATOR')
        catalog = context.catalog()
        witnesses, reads = [], []
        old_ids = {r['observation_id'] for r in before['observations']}
        selections = {}
        for ref in ['file:run.py', 'file:web/app.js', 'state:terminal']:
            node = context.node(ref)
            old = sorted(r['observation_id'] for r in node['native_observations'] if r['observation_id'] in old_ids)
            new = sorted(r['observation_id'] for r in node['native_observations'] if r['observation_id'] not in old_ids)
            require(old and new, 'REVIEW_MECHANICAL_BEFORE_AFTER_SOURCES_MISSING')
            # Select deterministic examples only. ID order is not temporal order;
            # the full catalog and all native records remain queryable.
            selections[ref] = {'historical_example': old[0], 'new_branch_example': new[0], 'temporal_order_inferred': False}
            for identity in [old[0], new[0]]:
                read = context.read(identity); reads.append(read)
                witnesses.append(context.witness(read['read_id'], 0, len(read['text'])))
        pending = context.pending_receipt()
        require(pending['status'] == 'PENDING_NATIVE_CONTINUATION' and not pending['reviewer_invoked'], 'REVIEW_FALSE_READINESS')
        args.out.mkdir(parents=True)
        save(args.out / 'review_catalog.json', catalog)
        save(args.out / 'source_reads.json', reads)
        save(args.out / 'source_witnesses.json', witnesses)
        save(args.out / 'example_selection.json', selections)
        save(args.out / 'pending_review_receipt.json', pending)
        if args.compare_frozen:
            frozen = ROOT / 'stage2/replication_v2/independent_repair_review_preparation_v1'
            sealed = json.loads((frozen / 'seal.json').read_text()); verify_seal(sealed, 'seal_hash')
            for path, expected in {**sealed['implementation_hashes'], **sealed['input_hashes']}.items():
                require(digest((ROOT / path).read_bytes()) == expected, 'REVIEW_DEPENDENCY_DRIFT:' + path)
            for path, expected in sealed['artifact_hashes'].items():
                require(digest((frozen / path).read_bytes()) == expected, 'REVIEW_FROZEN_HASH_DRIFT:' + path)
                require((args.out / path).read_bytes() == (frozen / path).read_bytes(), 'REVIEW_REPRODUCTION_DRIFT:' + path)
        print(json.dumps({'status': pending['status'], 'observations_available': len(catalog['all_observation_ids']),
                          'reads': len(reads), 'witnesses': len(witnesses), 'reviewer_invoked': False,
                          'new_model_calls': 0, 'native_actions': 0, 'sealed_reproduction': args.compare_frozen}))
    finally: native.close()


if __name__ == '__main__': main()
