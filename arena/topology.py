from collections import Counter, defaultdict


def _has_cycle(nodes, edges):
    adj = defaultdict(list)
    for u, v in edges:
        adj[u].append(v)
    visiting = set(); visited = set(); found = False
    def dfs(n):
        nonlocal found
        if n in visiting:
            found = True; return
        if n in visited or found:
            return
        visiting.add(n)
        for x in adj[n]:
            dfs(x)
        visiting.remove(n); visited.add(n)
    for n in list(nodes):
        dfs(n)
    return int(found)


def topology_metrics(trace, cutoff_event_index=None):
    events = trace['events']
    if cutoff_event_index is not None:
        events = [e for e in events if e['event_index'] < cutoff_event_index]
    nodes = set(); edges = []; messages = 0; state_writes = 0; revisions = 0
    for e in events:
        actor = e.get('actor')
        if actor and actor != 'ENVIRONMENT':
            nodes.add(actor)
        a = e.get('action') or {}
        if e.get('action_type') == 'invoke_agent' and e.get('realized_in_baseline'):
            target = a.get('agent_id')
            if target:
                nodes.add(target); edges.append((actor, target))
        elif e.get('action_type') == 'message' and e.get('realized_in_baseline'):
            target = a.get('to')
            if target:
                nodes.add(target); edges.append((actor, target)); messages += 1
        elif e.get('action_type') == 'write_state' and e.get('realized_in_baseline'):
            state_writes += 1
        elif e.get('action_type') == 'revise_final_state' and e.get('realized_in_baseline'):
            revisions += 1
    indeg = Counter(v for _, v in edges); outdeg = Counter(u for u, _ in edges)
    degree = Counter()
    for n in nodes:
        degree[n] = indeg[n] + outdeg[n]
    centralization = max(degree.values(), default=0) / max(1, len(edges))

    model_calls = trace.get('model_calls', [])
    if cutoff_event_index is not None:
        model_calls = [c for c in model_calls if c.get('event_index_start', 10**9) < cutoff_event_index]
    executed_agents = sorted({c['agent_id'] for c in model_calls if c.get('status', 'completed') == 'completed'})
    returned_agents = sorted({
        e.get('actor') for e in events
        if e.get('actor') not in (None, 'ENVIRONMENT') and e.get('realized_in_baseline')
        and e.get('action_type') in ('message', 'write_state', 'revise_final_state', 'finalize')
    })

    invocation_ledger = trace.get('invocation_ledger')
    execution_edges = []
    execution_edge_data_status = 'RECORDED'
    if isinstance(invocation_ledger, list):
        for row in invocation_ledger:
            proposal_idx = row.get('proposal_event_index')
            if cutoff_event_index is not None and isinstance(proposal_idx, int) and proposal_idx >= cutoff_event_index:
                continue
            if row.get('execution_status') == 'completed':
                execution_edges.append((row.get('requester'), row.get('target')))
    else:
        execution_edge_data_status = 'NOT_RECORDED_IN_SOURCE_VERSION'

    available_agents = trace.get('available_agents')
    return {
        # Backward-compatible activation-topology fields.
        'agent_count': len(nodes),
        'edge_count': len(edges),
        'message_count': messages,
        'state_write_count': state_writes,
        'revision_count': revisions,
        'max_out_degree': max(outdeg.values(), default=0),
        'max_in_degree': max(indeg.values(), default=0),
        'centralization_proxy': centralization,
        'has_cycle': _has_cycle(nodes, edges),
        # Evidence-v0.2 participation fields.
        'available_agent_count': len(available_agents) if isinstance(available_agents, list) else None,
        'activated_agent_count': len(trace.get('activated_agents', [])) if cutoff_event_index is None else len(nodes),
        'executed_agent_count': len(executed_agents),
        'returned_agent_count': len(returned_agents),
        'execution_edge_count': len(execution_edges) if execution_edge_data_status == 'RECORDED' else None,
        'execution_has_cycle': _has_cycle(set(executed_agents), execution_edges) if execution_edge_data_status == 'RECORDED' else None,
        'execution_edge_data_status': execution_edge_data_status,
    }


def participation_metrics(trace):
    calls = trace.get('model_calls', [])
    executed = sorted({c['agent_id'] for c in calls if c.get('status', 'completed') == 'completed'})
    returned = sorted({
        e.get('actor') for e in trace.get('events', [])
        if e.get('actor') not in (None, 'ENVIRONMENT') and e.get('realized_in_baseline')
        and e.get('action_type') in ('message', 'write_state', 'revise_final_state', 'finalize')
    })
    ledger = trace.get('message_ledger')
    if isinstance(ledger, list):
        sent = len(ledger)
        delivered = sum(1 for x in ledger if x.get('delivered_turn') is not None)
        read = sum(1 for x in ledger if x.get('read_turn') is not None)
        unread = sum(1 for x in ledger if x.get('read_turn') is None)
        message_status = 'RECORDED'
    else:
        sent = delivered = read = unread = None
        message_status = 'NOT_RECORDED_IN_SOURCE_VERSION'
    inv = trace.get('invocation_ledger')
    if isinstance(inv, list):
        unexecuted_invocations = sum(1 for x in inv if x.get('queued') and x.get('execution_turn') is None)
        invocation_status = 'RECORDED'
    else:
        unexecuted_invocations = None
        invocation_status = 'NOT_RECORDED_IN_SOURCE_VERSION'
    return {
        'available_agents': trace.get('available_agents'),
        'available_agent_count': trace.get('available_agent_count'),
        'activated_agents': trace.get('activated_agents', []),
        'activated_agent_count': len(trace.get('activated_agents', [])),
        'executed_agents': executed,
        'executed_agent_count': len(executed),
        'returned_agents': returned,
        'returned_agent_count': len(returned),
        'messages_sent': sent,
        'messages_delivered': delivered,
        'messages_read_into_model_input': read,
        'unread_messages': unread,
        'message_lifecycle_status': message_status,
        'unexecuted_invocations': unexecuted_invocations,
        'invocation_execution_status': invocation_status,
        'remaining_queue': trace.get('remaining_queue', 'NOT_RECORDED_IN_SOURCE_VERSION'),
        'decision_impact_status': 'NOT_ADJUDICATED',
    }
