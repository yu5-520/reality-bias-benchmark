import json
from datetime import datetime, timezone
from collections import defaultdict
from .core import ArenaState, stable_hash
from .prompts import build_agent_messages
from .loop_budget import (
    RUN_STATUS as LOOP_BUDGET_RUN_STATUS,
    TERMINATION_REASON as LOOP_BUDGET_TERMINATION_REASON,
    evaluate_loop_budget,
    validate_loop_budget_config,
)
from .experimental_control import capture_state, restore_state, verify_branch_manifest

TRACE_SCHEMA_VERSION = 'R2-ARENA-TRACE-v0.2'


def parse_envelope(text):
    if isinstance(text, dict):
        obj = text
    else:
        raw = str(text).strip()
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            if '```' not in raw:
                raise
            obj = None
            for piece in raw.split('```'):
                piece = piece.strip()
                if piece.startswith('json'):
                    piece = piece[4:].strip()
                try:
                    obj = json.loads(piece)
                    break
                except Exception:
                    pass
            if obj is None:
                raise
    if not isinstance(obj, dict):
        raise ValueError('agent response must be JSON object')
    obj.setdefault('decision_summary', '')
    obj.setdefault('actions', [])
    return obj


def _sum_usage(model_calls):
    totals = defaultdict(float)
    for call in model_calls:
        for key, value in (call.get('usage') or {}).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                totals[key] += value
    out = {}
    for key, value in totals.items():
        out[key] = int(value) if float(value).is_integer() else value
    return dict(sorted(out.items()))


def _returned_agents(events):
    contribution_types = {'message', 'write_state', 'revise_final_state', 'finalize'}
    return sorted({
        e.get('actor') for e in events
        if e.get('actor') not in (None, 'ENVIRONMENT')
        and e.get('realized_in_baseline')
        and e.get('action_type') in contribution_types
    })


def run_arena_once(
    domain,
    config,
    provider,
    run_id,
    logical_seed=None,
    recorder=None,
    initial_state_snapshot=None,
    branch_manifest=None,
    state_snapshot_callback=None,
):
    """Run one Arena continuation.

    `initial_state_snapshot`, `branch_manifest`, and `state_snapshot_callback` are
    experimental-control hooks. They are optional and therefore do not change the
    historical Free-Agent baseline when omitted.
    """
    loop_settings = validate_loop_budget_config(config)

    if initial_state_snapshot is None:
        if branch_manifest is not None:
            raise ValueError('branch_manifest_requires_initial_state_snapshot')
        state = ArenaState(domain, config, run_id, recorder=recorder)
    else:
        if branch_manifest is not None:
            verify_branch_manifest(branch_manifest, branch_start_snapshot=initial_state_snapshot)
        state = restore_state(domain, config, run_id, initial_state_snapshot, recorder=recorder)
        if state.terminated:
            raise ValueError('initial_state_snapshot_is_terminal')

    loop_runtime = evaluate_loop_budget(run_id, state.events, [], loop_settings)
    loop_runtime['stop_applied'] = False

    amap = {a['id']: a for a in domain['agents']}
    model_calls = []
    branch_parent_state_hash = (
        branch_manifest.get('parent_state_hash') if branch_manifest is not None
        else (initial_state_snapshot.get('state_hash') if initial_state_snapshot else None)
    )
    branch_start_state_hash = initial_state_snapshot.get('state_hash') if initial_state_snapshot else None

    while state.queue and not state.terminated and state.turns < config['max_turns']:
        if state_snapshot_callback is not None:
            anchor = capture_state(
                state,
                anchor_ref=f'before_turn:{state.turns + 1}',
                parent_trace_hash=(branch_manifest or {}).get('parent_trace_hash'),
            )
            state_snapshot_callback(anchor)

        actor = state.queue.popleft()
        state.turns += 1
        view = state.runtime_view(actor)
        messages = build_agent_messages(domain, amap[actor], view)
        call = {
            'started_at': datetime.now(timezone.utc).isoformat(),
            'runtime_snapshot': view,
            'runtime_snapshot_hash': stable_hash(view),
            'agent_id': actor,
            'turn': state.turns,
            'status': 'started',
            'prompt_hash': stable_hash(messages),
            'messages': messages,
            'input_message_ids': list(state.last_read_message_ids),
            'input_invocation_ids': list(state.last_read_invocation_ids),
            'event_index_start': len(state.events),
        }
        if recorder:
            recorder({'record_type': 'call_started', 'record': call})
        try:
            response = provider.complete_agent(messages, metadata={
                'run_id': run_id,
                'domain_id': domain['domain_id'],
                'agent_id': actor,
                'turn': state.turns,
                'logical_seed': logical_seed,
                'branch_id': (branch_manifest or {}).get('branch_id'),
                'replicate_index': (branch_manifest or {}).get('replicate_index'),
            })
            call.update({
                'response_id': response.get('response_id'),
                'provider_response': response.get('provider_response'),
                'finish_reason': response.get('finish_reason'),
                'provider_model': response.get('model'),
                'usage': response.get('usage') or {},
                'transport_latency_ms': response.get('transport_latency_ms'),
                'raw_content': response.get('content'),
            })
            envelope = parse_envelope(response['content'])
            if recorder:
                recorder({'record_type': 'provider_response', 'record': call})
            call['parsed_envelope'] = envelope
            call['decision_summary'] = envelope.get('decision_summary', '')
            call['status'] = 'completed'
            state.apply_actions(actor, envelope)
            state.mark_execution(actor, state.turns, True)
            call['event_index_end'] = len(state.events)
            call['completed_at'] = datetime.now(timezone.utc).isoformat()
            model_calls.append(call)
            if recorder:
                recorder({'record_type': 'turn_completed', 'record': call, 'ledgers': state.evidence_snapshot()})

            if state_snapshot_callback is not None:
                anchor = capture_state(
                    state,
                    anchor_ref=f'after_turn:{state.turns}',
                    parent_trace_hash=(branch_manifest or {}).get('parent_trace_hash'),
                )
                state_snapshot_callback(anchor)

            # K is evaluated only after the completed call and its realized events
            # have been frozen into the in-memory trace. Safety failures/censoring
            # always take precedence over a coincident K boundary.
            loop_runtime = evaluate_loop_budget(run_id, state.events, model_calls, loop_settings)
            loop_runtime['stop_applied'] = False
            if loop_runtime['reached'] and not state.termination_reason:
                state.terminated = True
                state.termination_reason = LOOP_BUDGET_TERMINATION_REASON
                loop_runtime['stop_applied'] = True
                if recorder:
                    recorder({
                        'record_type': 'loop_budget_reached',
                        'record': loop_runtime,
                    })
        except Exception as err:
            if getattr(err, 'provider_responses', None):
                call['failed_provider_responses'] = err.provider_responses
                call['usage'] = err.usage
            call['status'] = 'failed'
            call['error'] = repr(err)
            call['event_index_end'] = len(state.events)
            model_calls.append(call)
            state.mark_execution(actor, state.turns, False, repr(err))
            state.failures.append({
                'turn': state.turns,
                'agent_id': actor,
                'stage': 'provider_or_parse',
                'error': repr(err),
                'input_message_ids': list(state.last_read_message_ids),
            })
            state.termination_reason = 'model_call_failure'
            if recorder:
                recorder({'record_type': 'turn_failed', 'record': call, 'ledgers': state.evidence_snapshot()})
            break

    if state.termination_reason:
        termination_reason = state.termination_reason
    elif state.turns >= config['max_turns'] and state.queue:
        termination_reason = 'turn_budget_exhausted'
    elif not state.queue and state.final_state is not None:
        termination_reason = 'queue_empty_with_final_state'
    else:
        termination_reason = 'queue_empty_without_final_state'

    executed_agents = sorted({x['agent_id'] for x in state.execution_ledger if x['status'] == 'completed'})
    model_response_agents = sorted({x['agent_id'] for x in model_calls if x.get('status') == 'completed'})
    returned_agents = _returned_agents(state.events)
    if state.failures:
        run_status = 'RUN_FAILED'
    elif termination_reason == LOOP_BUDGET_TERMINATION_REASON:
        run_status = LOOP_BUDGET_RUN_STATUS
    elif termination_reason in ('turn_budget_exhausted', 'invocation_budget_exhausted', 'queue_capacity_exhausted'):
        run_status = 'BUDGET_CENSORED'
    elif state.final_state is None:
        run_status = 'RUN_INCOMPLETE'
    else:
        run_status = 'RUN_COMPLETE'

    evidence = state.evidence_snapshot()
    condition_limits = {}
    if loop_runtime.get('enabled'):
        condition_limits['structural_feedback_rounds'] = loop_runtime['limit']
    trace = {
        'trace_schema_version': config.get('trace_schema_version', TRACE_SCHEMA_VERSION),
        'observation_policy': config.get('termination_policy'),
        'experimental_stop_policy': 'structural_feedback_round_limit' if loop_runtime.get('enabled') else None,
        'budget_hits': state.budget_hits,
        'observation_censored': run_status == 'BUDGET_CENSORED',
        'condition_complete': run_status in ('RUN_COMPLETE', LOOP_BUDGET_RUN_STATUS),
        'budget_limits': {k: config[k] for k in ('max_turns', 'max_total_invocations', 'max_pending_messages')},
        'condition_limits': condition_limits,
        'loop_budget': loop_runtime,
        'run_id': run_id,
        'domain_id': domain['domain_id'],
        'domain_label': domain['label'],
        'logical_seed': logical_seed,
        'task_hash': stable_hash(domain['task']),
        'agent_registry_hash': stable_hash(domain['agents']),
        'run_status': run_status,
        'review_status': 'PENDING_REVIEW',
        'turns': state.turns,
        'available_agents': sorted(amap),
        'available_agent_count': len(amap),
        'activated_agents': sorted(state.active_agents),
        'activated_agent_count': len(state.active_agents),
        'executed_agents': executed_agents,
        'executed_agent_count': len(executed_agents),
        'model_response_agents': model_response_agents,
        'model_response_agent_count': len(model_response_agents),
        'returned_agents': returned_agents,
        'returned_agent_count': len(returned_agents),
        'total_invocations': state.total_invocations,
        'late_event_delivered': state.late_event_delivered,
        'late_event_consumed': state.late_event_consumed,
        'termination_reason': termination_reason,
        'final_state': state.final_state,
        'remaining_queue': evidence['remaining_queue'],
        'unread_messages': evidence['unread_messages'],
        'pending_invocations': evidence['pending_invocations'],
        'message_ledger': evidence['message_ledger'],
        'invocation_ledger': evidence['invocation_ledger'],
        'execution_ledger': evidence['execution_ledger'],
        'failures': evidence['failures'],
        'usage_summary': _sum_usage(model_calls),
        'events': state.events,
        'model_calls': model_calls,
    }
    if branch_manifest is not None:
        trace['experimental_branch'] = {
            'schema': branch_manifest.get('schema'),
            'branch_id': branch_manifest['branch_id'],
            'branch_hash': branch_manifest['branch_hash'],
            'parent_trace_hash': branch_manifest['parent_trace_hash'],
            'parent_state_hash': branch_parent_state_hash,
            'branch_start_state_hash': branch_start_state_hash,
            'intervention_hash': branch_manifest['intervention_hash'],
            'intervention_applied_before_continuation': branch_parent_state_hash != branch_start_state_hash,
            'replicate_index': branch_manifest['replicate_index'],
            'provider_internal_state_replayed': False,
        }
    return trace
