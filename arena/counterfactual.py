from .evaluation import validate_evaluation

CONDITIONS = {
    'baseline': set(),
    'i_only': {'I'},
    'v_only': {'V'},
    't_only': {'T'},
    'full': {'I','V','T'},
}


def attach_codes(trace, evaluation):
    validate_evaluation(trace, evaluation)
    by_index = {x['event_index']: x for x in evaluation.get('coded_events', [])}
    out=[]
    for event in trace['events']:
        row=dict(event)
        code=by_index.get(event['event_index'])
        if code:
            row['bias_mechanisms']=code.get('bias_mechanisms') or []
            row['authorized_under_contract']=bool(code.get('authorized_under_contract'))
            row['coding_confidence']=code.get('confidence')
            row['coding_evidence']=code.get('evidence')
        else:
            row['bias_mechanisms']=[]
            row['authorized_under_contract']=True
        out.append(row)
    return out


def replay_immediate_containment(trace, evaluation):
    events=attach_codes(trace,evaluation)
    rows=[]
    for condition,gates in CONDITIONS.items():
        realized=[]; blocked=[]; unrealized=[]
        for e in events:
            if not e.get('realized_in_baseline', False):
                unrealized.append(e['event_index'])
                continue
            auth=e.get('authority_class')
            should_block = (
                auth in gates
                and auth in ('I','V','T')
                and not bool(e.get('authorized_under_contract',True))
            )
            target = blocked if should_block else realized
            target.append(e['event_index'])
        rows.append({
            'run_id':trace['run_id'],
            'domain_id':trace['domain_id'],
            'condition':condition,
            'realized_event_indices':realized,
            'blocked_event_indices':blocked,
            'baseline_unrealized_event_indices':unrealized,
            'note':'Immediate event-level counterfactual only; downstream behavior is not regenerated after a block.'
        })
    return rows

