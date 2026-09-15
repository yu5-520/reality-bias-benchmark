#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl, sha256_file
from .topology import topology_metrics, participation_metrics

EVIDENCE_BATCH_VERSION = 'R2-EVIDENCE-BATCH-v0.2'
REVIEW_PACKET_VERSION = 'R2-REVIEW-PACKET-v0.1'


def _call_for_event(trace, event_index):
    for i, call in enumerate(trace.get('model_calls', [])):
        start = call.get('event_index_start')
        end = call.get('event_index_end')
        if isinstance(start, int) and isinstance(end, int) and start <= event_index < end:
            return i, call
    return None, None


def _objective_row(trace):
    topo = topology_metrics(trace)
    part = participation_metrics(trace)
    return {
        'run_id': trace['run_id'],
        'domain_id': trace['domain_id'],
        'run_status': trace.get('run_status', 'LEGACY_STATUS_UNKNOWN'),
        'review_status': trace.get('review_status', 'PENDING_REVIEW'),
        'termination_reason': trace.get('termination_reason'),
        'turns': trace.get('turns'),
        'usage_summary': trace.get('usage_summary', 'NOT_RECORDED_IN_SOURCE_VERSION'),
        'participation': part,
        'activation_topology': {
            'edge_count': topo['edge_count'],
            'message_count': topo['message_count'],
            'has_cycle': topo['has_cycle'],
            'max_out_degree': topo['max_out_degree'],
            'max_in_degree': topo['max_in_degree'],
        },
        'execution_topology': {
            'edge_count': topo['execution_edge_count'],
            'has_cycle': topo['execution_has_cycle'],
            'data_status': topo['execution_edge_data_status'],
        },
        'state_write_count': topo['state_write_count'],
        'revision_count': topo['revision_count'],
        'pending_invocation_count': len(trace.get('pending_invocations', [])) if isinstance(trace.get('pending_invocations'), list) else None,
        'failure_count': len(trace.get('failures', [])) if isinstance(trace.get('failures'), list) else None,
        'semantic_review': 'NOT_ADJUDICATED',
    }


def _review_material(trace, batch_hash):
    index_records = []
    packets = []
    run_id = trace['run_id']
    for i, call in enumerate(trace.get('model_calls', [])):
        ref = f"{run_id}:CALL:{i:04d}"
        index_records.append({
            'evidence_ref': ref,
            'record_type': 'model_call',
            'run_id': run_id,
            'record': call,
        })
    for event in trace.get('events', []):
        event_ref = f"{run_id}:EVENT:{event['event_index']:04d}"
        index_records.append({
            'evidence_ref': event_ref,
            'record_type': 'event',
            'run_id': run_id,
            'record': event,
        })
        if event.get('authority_class') not in ('I', 'V', 'T'):
            continue
        call_idx, call = _call_for_event(trace, event['event_index'])
        refs = [event_ref]
        if call_idx is not None:
            refs.append(f"{run_id}:CALL:{call_idx:04d}")
        packet_id = f"{run_id}:AE:{event['event_index']:04d}"
        packet = {
            'review_packet_version': REVIEW_PACKET_VERSION,
            'evidence_batch_hash': batch_hash,
            'packet_id': packet_id,
            'event_id': f"{run_id}:E{event['event_index']:04d}",
            'run_id': run_id,
            'domain_id': trace['domain_id'],
            'actor': event.get('actor'),
            'turn': event.get('turn'),
            'structural_facts': {
                'action_type': event.get('action_type'),
                'authority_class': event.get('authority_class'),
                'realized_in_baseline': event.get('realized_in_baseline'),
                'note': event.get('note'),
                'action': event.get('action'),
                'final_state_before': event.get('final_state_before', 'NOT_RECORDED_IN_SOURCE_VERSION'),
                'final_state_after': event.get('final_state_after'),
                'shared_state_metadata_before': event.get('shared_state_metadata_before', 'NOT_RECORDED_IN_SOURCE_VERSION'),
                'shared_state_metadata_after': event.get('shared_state_metadata_after'),
            },
            'actor_input_message_ids': call.get('input_message_ids', 'NOT_RECORDED_IN_SOURCE_VERSION') if call else 'NO_MATCHING_MODEL_CALL',
            'evidence_refs': refs,
            'semantic_fields': {
                'C_P_R': 'NOT_ADJUDICATED',
                'invocation_necessity': 'NOT_ADJUDICATED',
                'revision_basis_sufficiency': 'NOT_ADJUDICATED',
                'authorization_judgment': 'NOT_ADJUDICATED',
                'decision_impact': 'NOT_ADJUDICATED',
            },
        }
        packets.append(packet)
    return index_records, packets


def build_batch(manifest_path, traces_path, errors_path, outdir, code_sha=None):
    manifest = load_jsonl(manifest_path)
    traces = load_jsonl(traces_path)
    errors = []
    if errors_path and Path(errors_path).exists():
        errors = json.loads(Path(errors_path).read_text(encoding='utf-8'))
    by_run = {x['run_id']: x for x in manifest}
    for trace in traces:
        row = by_run.get(trace['run_id'])
        if row is None:
            raise ValueError(f"trace not present in manifest: {trace['run_id']}")
        for key in ('domain_hash', 'arena_config_hash', 'model_config_hash'):
            if trace.get(key) != row.get(key):
                raise ValueError(f"binding mismatch {trace['run_id']} {key}")
    source = {
        'version': EVIDENCE_BATCH_VERSION,
        'manifest_sha256': sha256_file(manifest_path),
        'traces_sha256': sha256_file(traces_path),
        'errors_sha256': sha256_file(errors_path) if errors_path and Path(errors_path).exists() else None,
        'code_commit_sha': code_sha or os.environ.get('GITHUB_SHA') or 'LOCAL_OR_UNRECORDED',
        'manifest_bindings': [{
            'run_id': x['run_id'],
            'domain_id': x['domain_id'],
            'task_hash': x.get('task_hash'),
            'agent_pool_hash': x.get('agent_pool_hash'),
            'domain_hash': x.get('domain_hash'),
            'arena_config_version': x.get('arena_config_version'),
            'arena_config_hash': x.get('arena_config_hash'),
            'model_config_version': x.get('model_config_version'),
            'model_config_hash': x.get('model_config_hash'),
        } for x in manifest],
    }
    batch_hash = stable_hash(source)
    objective_rows = [_objective_row(x) for x in traces]
    index_records = []; packets = []
    for trace in traces:
        idx, p = _review_material(trace, batch_hash)
        index_records.extend(idx); packets.extend(p)

    completed = sum(1 for x in traces if x.get('run_status') == 'RUN_COMPLETE')
    if len(traces) == len(manifest) and completed == len(traces) and not errors:
        status = 'RUN_COMPLETE_PENDING_REVIEW'
    else:
        status = 'RUN_FINISHED_WITH_INCOMPLETE_EVIDENCE_PENDING_REVIEW'
    missing_legacy = sorted({
        field for trace in traces for field in ('message_ledger', 'invocation_ledger', 'remaining_queue', 'usage_summary')
        if field not in trace
    })
    metadata = {
        **source,
        'evidence_batch_hash': batch_hash,
        'status': status,
        'review_status': 'PENDING_REVIEW',
        'planned_runs': len(manifest),
        'preserved_traces': len(traces),
        'complete_runs': completed,
        'runner_errors': len(errors),
        'review_packet_count': len(packets),
        'legacy_missing_fields': missing_legacy,
        'semantic_warning': 'Objective outputs contain no C/P/R zeros. Until adjudication exists, all semantic labels are NOT_ADJUDICATED.',
    }
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    (out / 'evidence_batch.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    write_jsonl(out / 'objective_stats.jsonl', objective_rows)
    write_jsonl(out / 'review_evidence_index.jsonl', index_records)
    write_jsonl(out / 'review_packets.jsonl', packets)
    report = [
        '# R2 Arena Run Report — Objective Facts Only', '',
        f"Evidence batch: `{batch_hash}`", '',
        f"Status: **{status}**", '',
        f"Planned runs: {len(manifest)}; preserved traces: {len(traces)}; complete runs: {completed}; runner errors: {len(errors)}.", '',
        'C/P/R: **NOT_ADJUDICATED**.', '',
        'Invocation necessity: **NOT_ADJUDICATED**. Revision-basis sufficiency: **NOT_ADJUDICATED**. Decision impact: **NOT_ADJUDICATED**.', '',
        'This report intentionally stops at deterministic execution facts. Review packets are exported separately and can be judged later by humans or independent evaluator agents without rerunning the subject experiment.', '',
        '|Run|Status|Activated|Executed|Returned|Turns|Unread messages|Unexecuted invocations|',
        '|---|---|---:|---:|---:|---:|---:|---:|',
    ]
    for row in objective_rows:
        p = row['participation']
        report.append(
            f"|{row['run_id']}|{row['run_status']}|{p['activated_agent_count']}|{p['executed_agent_count']}|{p['returned_agent_count']}|{row['turns']}|{p['unread_messages'] if p['unread_messages'] is not None else 'N/R'}|{p['unexecuted_invocations'] if p['unexecuted_invocations'] is not None else 'N/R'}|"
        )
    (out / 'RUN_REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    integrity = {
        'evidence_batch_hash': batch_hash,
        'files': {
            'objective_stats.jsonl': sha256_file(out / 'objective_stats.jsonl'),
            'review_evidence_index.jsonl': sha256_file(out / 'review_evidence_index.jsonl'),
            'review_packets.jsonl': sha256_file(out / 'review_packets.jsonl'),
            'RUN_REPORT.md': sha256_file(out / 'RUN_REPORT.md'),
        }
    }
    (out / 'integrity.json').write_text(json.dumps(integrity, indent=2), encoding='utf-8')
    return metadata


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--traces', required=True)
    ap.add_argument('--errors')
    ap.add_argument('--outdir', required=True)
    ap.add_argument('--code-sha')
    a = ap.parse_args()
    meta = build_batch(a.manifest, a.traces, a.errors, a.outdir, a.code_sha)
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
