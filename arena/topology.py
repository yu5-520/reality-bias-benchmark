from collections import Counter, defaultdict


def topology_metrics(trace, cutoff_event_index=None):
    events = trace['events']
    if cutoff_event_index is not None:
        events = [e for e in events if e['event_index'] < cutoff_event_index]
    nodes=set()
    edges=[]
    messages=0
    state_writes=0
    revisions=0
    for e in events:
        actor=e.get('actor')
        if actor and actor!='ENVIRONMENT':
            nodes.add(actor)
        a=e.get('action') or {}
        if e.get('action_type')=='invoke_agent' and e.get('realized_in_baseline'):
            target=a.get('agent_id')
            if target:
                nodes.add(target); edges.append((actor,target))
        elif e.get('action_type')=='message' and e.get('realized_in_baseline'):
            target=a.get('to')
            if target:
                nodes.add(target); edges.append((actor,target)); messages += 1
        elif e.get('action_type')=='write_state' and e.get('realized_in_baseline'):
            state_writes += 1
        elif e.get('action_type')=='revise_final_state' and e.get('realized_in_baseline'):
            revisions += 1
    indeg=Counter(v for _,v in edges); outdeg=Counter(u for u,_ in edges)
    degree=Counter()
    for n in nodes:
        degree[n]=indeg[n]+outdeg[n]
    centralization=max(degree.values(),default=0)/max(1,len(edges))
    adj=defaultdict(list)
    for u,v in edges: adj[u].append(v)
    has_cycle=False
    visiting=set(); visited=set()
    def dfs(n):
        nonlocal has_cycle
        if n in visiting: has_cycle=True; return
        if n in visited or has_cycle: return
        visiting.add(n)
        for x in adj[n]: dfs(x)
        visiting.remove(n); visited.add(n)
    for n in list(nodes): dfs(n)
    return {
        'agent_count':len(nodes),
        'edge_count':len(edges),
        'message_count':messages,
        'state_write_count':state_writes,
        'revision_count':revisions,
        'max_out_degree':max(outdeg.values(),default=0),
        'max_in_degree':max(indeg.values(),default=0),
        'centralization_proxy':centralization,
        'has_cycle':int(has_cycle),
    }
