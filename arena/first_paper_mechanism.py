"""Forward v0.2 diagnostics; source-only classification and parent-aware estimates."""
from __future__ import annotations

import argparse
import copy
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from .branch_comparison_v4 import verify_branch_comparison_v4
from .core import stable_hash
from .io_utils import load_json, load_jsonl
from .system_behavior import content_hash

CONTRACT = Path(__file__).resolve().parents[1] / 'configs/first_paper_mechanism_contract_v0.2.json'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sealed(row, key):
    row = copy.deepcopy(row)
    row[key] = content_hash(row)
    return row


def verify(row, key):
    require(row.get(key) == content_hash({k: v for k, v in row.items() if k != key}), key + '_mismatch')


def build_source_packet(bundle, baseline):
    """Whitelist only the selected parent's source; never copy continuation outputs."""
    common = bundle['plan']['common_identity']
    require(stable_hash(baseline) == common['source_trace_hash'], 'source_trace_hash_mismatch')
    parent = bundle['parent_snapshot']
    key = common['state_key']
    meta = parent['shared_state_metadata'][key]
    idx = meta.get('event_index')
    calls = [c for c in baseline.get('model_calls', [])
             if type(idx) is int and type(c.get('event_index_start')) is int
             and type(c.get('event_index_end')) is int
             and c['event_index_start'] <= idx < c['event_index_end']]
    cfg = load_json(CONTRACT)
    # A unique recorded producing call is required; never guess a nearby call.
    visible = json.dumps(calls[0].get('messages'), ensure_ascii=False) if len(calls) == 1 else None
    cap = cfg['source_input_character_cap']
    entries = [{'ref': 'parent:selected_state', 'value': parent['shared_state'][key]},
               {'ref': 'parent:selected_metadata', 'value': meta}]
    if visible is not None:
        entries.append({'ref': 'source:producing_call_input', 'value': visible[:cap]})
    return sealed({
        'schema': 'RB-ANCHOR-SOURCE-PACKET-v0.2',
        'parent_state_hash': common['parent_state_hash'],
        'source_trace_hash': common['source_trace_hash'],
        'state_key': key, 'evidence': entries,
        'input_missing': visible is None,
        'input_truncated': visible is not None and len(visible) > cap,
        'branch_outcomes_included': False,
        'classification_used_for_selection': False,
        'contract_hash': content_hash(cfg),
    }, 'packet_hash')


def continuation_observations(trace, adapted, dynamics, anchor_view):
    start = trace['experimental_branch']['branch_start_turn']
    events = [e for e in adapted['behavior_events'] if e['turn'] > start]
    realized = [e for e in events if e['realization_status'] == 'REALIZED']
    all_crossings = {c['crossing_id'] for c in dynamics.get('operational_crossings', [])}
    reachable = set(anchor_view['potential_downstream_operational_crossing_ids'])
    require(reachable <= all_crossings, 'anchor_crossings_outside_continuation')
    key = anchor_view['branch_start_anchor']['state_key']
    rewrites = [e for e in realized if (e.get('structured_diff') or {}).get('action_key') == key
                and (e.get('structured_diff') or {}).get('source_action_type') == 'write_state']
    promotions = [e for e in rewrites if e['structured_diff'].get('action_status') in {'fact', 'confirmed', 'verified', 'executed'}]
    return sealed({
        'schema': 'RB-MECHANISM-OBSERVATION-v0.2',
        'trajectory_id': trace['run_id'], 'trace_hash': content_hash(trace),
        'pair_id': anchor_view['pair_id'], 'condition_id': anchor_view['condition_id'],
        'parent_state_hash': anchor_view['branch_start_anchor']['parent_state_hash'],
        'run_status': trace['run_status'],
        'agent_turn_count': sum(e['boundary_id'] == 'AGENT_TURN' for e in realized),
        'realized_action_count': sum((e.get('structured_diff') or {}).get('source_action_type') is not None for e in realized),
        'behavior_event_count': len(events),
        'total_operational_crossing_count': len(all_crossings),
        'anchor_reachable_crossing_count': len(reachable),
        'not_anchor_reachable_crossing_count': len(all_crossings - reachable),
        'anchor_visible_turn_count': anchor_view['anchor_visible_agent_turn_count'],
        'same_key_rewrite_event_refs': [e['behavior_event_id'] for e in rewrites],
        'high_certainty_rewrite_candidate_refs': [e['behavior_event_id'] for e in promotions],
        'task_completion': 'NOT_ADJUDICATED',
        'semantic_adoption': 'NOT_ADJUDICATED',
        'semantic_recertification': 'NOT_ADJUDICATED',
        'challenge_presence': 'NOT_ADJUDICATED',
        'R_status': 'NOT_ADJUDICATED',
    }, 'observation_hash')


def grouped_analysis(comparisons, summary, observations):
    require(summary.get('planned_pair_count') == len(summary['pair_index']), 'planned_pair_index_incomplete')
    index = {r['pair_id']: r for r in summary['pair_index']}
    require(len(index) == len(summary['pair_index']), 'duplicate_pair_index')
    by_run = {}
    for obs in observations:
        verify(obs, 'observation_hash')
        require(obs['trajectory_id'] not in by_run, 'duplicate_observation')
        by_run[obs['trajectory_id']] = obs
    groups = defaultdict(list)
    pairs = []
    for row in comparisons:
        verify_branch_comparison_v4(row)
        require(index.get(row['pair_id'], {}).get('pair_status') == 'PAIR_COMPARED_STRUCTURALLY_V4', 'ineligible_pair')
        require(row['pair_id'] not in {p['pair_id'] for p in pairs}, 'duplicate_pair')
        delta = row['structural_deltas']['r5_mid_branch_anchor']['potential_downstream_operational_crossing_count']['delta_intervention_minus_control']
        require(type(delta) in (int, float) and math.isfinite(delta), 'nonfinite_or_missing_delta')
        pair = {'pair_id': row['pair_id'], 'parent_state_hash': row['common_parent_state_hash'], 'delta': delta, 'auxiliary': {}}
        c, i = by_run.get(row['control_run_id']), by_run.get(row['intervention_run_id'])
        if c is not None and i is not None:
            for obs, condition in ((c, 'CONTROL_CONTINUATION'), (i, 'STATUS_DOWNGRADE_INTERVENTION')):
                require(obs['pair_id'] == row['pair_id'] and obs['parent_state_hash'] == row['common_parent_state_hash'], 'observation_pair_identity_mismatch')
                require(obs['condition_id'] == condition and obs['run_status'] == 'RUN_COMPLETE', 'observation_condition_or_status_mismatch')
            for metric in ('agent_turn_count', 'realized_action_count', 'total_operational_crossing_count', 'not_anchor_reachable_crossing_count', 'anchor_visible_turn_count'):
                pair['auxiliary'][metric] = {'control': c[metric], 'intervention': i[metric], 'delta': i[metric] - c[metric]}
        pair['auxiliary_status'] = 'OBSERVED' if pair['auxiliary'] else 'MISSING_NOT_ZERO'
        groups[row['common_parent_state_hash']].append(delta)
        pairs.append(pair)
    require({p['pair_id'] for p in pairs} == {k for k, v in index.items() if v['pair_status'] == 'PAIR_COMPARED_STRUCTURALLY_V4'}, 'comparison_set_mismatch')
    parent_rows = [{'parent_state_hash': k, 'complete_pair_count': len(v), 'mean_pair_delta': statistics.fmean(v), 'pair_deltas': v} for k, v in sorted(groups.items())]
    return sealed({
        'schema': 'RB-FIRST-PAPER-MECHANISM-ANALYSIS-v0.2',
        'contract_hash': content_hash(load_json(CONTRACT)),
        'planned_pair_count': summary['planned_pair_count'],
        'complete_pair_count': len(pairs), 'parent_count': len(parent_rows),
        'parent_groups': parent_rows, 'pairs': pairs, 'planned_pair_index': summary['pair_index'],
        'parent_balanced_mean_delta': statistics.fmean(p['mean_pair_delta'] for p in parent_rows) if parent_rows else None,
        'primary_interval': None,
        'interval_status': 'NOT_ESTIMATED_INDEPENDENT_PARENT_SAMPLING_NOT_ESTABLISHED',
        'semantic_status': 'NOT_ADJUDICATED',
        'automatic_paid_evaluator_called': False,
    }, 'analysis_hash')


def append_reviews(packets, incoming, ledger_path):
    """Append frozen source classifications or bounded downstream diagnostics."""
    cfg = load_json(CONTRACT)
    lookup = {}
    for p in packets:
        verify(p, 'packet_hash')
        require(p['packet_hash'] not in lookup, 'duplicate_packet')
        lookup[p['packet_hash']] = p
    ledger = Path(ledger_path)
    existing = load_jsonl(ledger) if ledger.exists() else []
    seen = set()
    for record in existing + incoming:
        verify(record, 'review_hash')
        p = lookup.get(record.get('packet_hash'))
        require(p is not None, 'unknown_packet')
        reviewer = record.get('reviewer_id')
        require(isinstance(reviewer, str) and reviewer, 'reviewer_required')
        key = (record['packet_hash'], reviewer)
        require(key not in seen, 'duplicate_independent_reviewer')
        seen.add(key)
        refs = {e['ref'] for e in p['evidence']}
        require(set(record.get('evidence_refs', [])) <= refs, 'unknown_evidence_ref')
        require(record.get('independent') is True, 'independent_review_required')
        require(record.get('evidence_sufficiency') in {'SUFFICIENT', 'INSUFFICIENT'}, 'evidence_sufficiency_required')
        if p['schema'] == 'RB-ANCHOR-SOURCE-PACKET-v0.2':
            require(record.get('outcome_blind') is True, 'outcome_blind_classification_required')
            require(record.get('anchor_class') in cfg['anchor_classes'], 'anchor_class_invalid')
            determinate = record['anchor_class'] != 'INSUFFICIENT_EVIDENCE'
            require(not determinate or (record['evidence_sufficiency'] == 'SUFFICIENT' and record.get('evidence_refs') and not p['input_missing'] and not p['input_truncated']), 'insufficient_source_cannot_resolve')
        else:
            require(p['schema'] == 'RB-MECHANISM-REVIEW-PACKET-v0.2', 'packet_schema_invalid')
            require(set(record.get('judgments', {})) == set(cfg['semantic_fields']), 'semantic_fields_invalid')
            for value in record['judgments'].values():
                require(value in cfg['semantic_values'], 'semantic_value_invalid')
                require(value not in {'YES', 'NO'} or (record['evidence_sufficiency'] == 'SUFFICIENT' and record.get('evidence_refs')), 'insufficient_review_cannot_resolve')
    require(incoming, 'empty_review_import')
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open('a', encoding='utf-8') as f:
        for r in incoming:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n')
    return existing + incoming


def resolve_reviews(records):
    grouped = defaultdict(list)
    for r in records:
        grouped[r['packet_hash']].append(r)
    result = []
    for packet, rows in sorted(grouped.items()):
        eligible = [r for r in rows if r['evidence_sufficiency'] == 'SUFFICIENT']
        fields = ['anchor_class'] if 'anchor_class' in rows[0] else load_json(CONTRACT)['semantic_fields']
        values = {}
        for field in fields:
            observed = [r.get(field) if field == 'anchor_class' else r['judgments'][field] for r in eligible]
            determinate = {'SUPPORTED_CALIBRATED', 'UNSUPPORTED_OR_OVERSTATED'} if field == 'anchor_class' else {'YES', 'NO'}
            values[field] = observed[0] if len({r['reviewer_id'] for r in eligible}) >= 2 and len(set(observed)) == 1 and observed[0] in determinate else 'UNRESOLVED'
        result.append({'packet_hash': packet, 'resolutions': values})
    return result


def aggregate_batches(batches):
    """Combine frozen descriptive batches without inventing independent samples."""
    parents = defaultdict(list)
    sources = defaultdict(set)
    seen = set()
    planned = 0
    batch_hashes = []
    for batch in batches:
        verify(batch, 'analysis_hash')
        require(batch.get('schema') == 'RB-FIRST-PAPER-MECHANISM-ANALYSIS-v0.2', 'analysis_schema_mismatch')
        require(batch['contract_hash'] == content_hash(load_json(CONTRACT)), 'contract_mismatch')
        source = batch.get('source_trace_hash')
        require(isinstance(source, str) and source, 'source_cluster_required')
        require(batch['analysis_hash'] not in batch_hashes, 'duplicate_batch')
        batch_hashes.append(batch['analysis_hash'])
        planned += batch['planned_pair_count']
        for pair in batch['pairs']:
            require(pair['pair_id'] not in seen, 'duplicate_pair_across_batches')
            seen.add(pair['pair_id'])
            parents[pair['parent_state_hash']].append(pair['delta'])
            sources[source].add(pair['parent_state_hash'])
    parent_rows = [{'parent_state_hash': key, 'pair_count': len(values), 'mean_pair_delta': statistics.fmean(values)} for key, values in sorted(parents.items())]
    return sealed({'schema': 'RB-MECHANISM-MULTIPARENT-SUMMARY-v0.2',
                   'batch_hashes': batch_hashes, 'planned_pair_count': planned,
                   'complete_pair_count': len(seen), 'parent_count': len(parents),
                   'baseline_source_count': len(sources),
                   'source_clusters': {k: sorted(v) for k, v in sorted(sources.items())},
                   'parent_groups': parent_rows,
                   'parent_balanced_mean_delta': statistics.fmean(p['mean_pair_delta'] for p in parent_rows) if parent_rows else None,
                   'primary_interval': None, 'independence_status': 'NOT_ESTABLISHED_BY_HASH_DISTINCTNESS'}, 'summary_hash')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--packets')
    p.add_argument('--reviews')
    p.add_argument('--ledger')
    p.add_argument('--analyses', nargs='+')
    p.add_argument('--out', required=True)
    a = p.parse_args()
    require(not Path(a.out).exists(), 'refusing_to_overwrite_review_summary')
    if a.analyses:
        require(not any((a.packets, a.reviews, a.ledger)), 'mixed_modes')
        result = aggregate_batches([load_json(path) for path in a.analyses])
        Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        print('Parent-aware summary saved; intervals not estimated; evaluator calls=0')
        return
    require(all((a.packets, a.reviews, a.ledger)), 'review_inputs_required')
    rows = append_reviews(load_jsonl(a.packets), load_jsonl(a.reviews), a.ledger)
    Path(a.out).write_text(json.dumps(resolve_reviews(rows), ensure_ascii=False, indent=2) + '\n')
    print('Mechanism review appended; source unchanged; evaluator calls=0')


if __name__ == '__main__':
    main()
