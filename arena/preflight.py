#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from arena.engine import run_arena_once
from arena.io_utils import load_json
from arena.providers import ScriptedProvider
from arena.topology import topology_metrics


def main():
    domain=load_json(ROOT/'arena/domains/ecommerce.json')
    cfg=load_json(ROOT/'arena/config/arena_v0.1.json')
    scripted=[
      {'decision_summary':'ask inventory','actions':[{'type':'invoke_agent','agent_id':'inventory','request':'Check stock and replenishment risk.'}]},
      {'decision_summary':'share inventory','actions':[{'type':'write_state','key':'inventory_view','value':'A stock risk elevated','basis':'supplier lead time and stock','status':'recommendation'},{'type':'message','to':'ops_lead','content':'A has the tightest stock coverage.'}]},
      {'decision_summary':'finalize first plan','actions':[{'type':'finalize','answer':'Initial promotion plan.'}]},
      {'decision_summary':'respond to late signal','actions':[{'type':'revise_final_state','patch':{'inventory_view':'A stock risk critical'},'reason':'new preliminary inventory signal'},{'type':'finalize','answer':'Updated promotion plan.'}]}
    ]
    trace=run_arena_once(domain,cfg,ScriptedProvider(scripted),'offline-preflight',1)
    types=[e['action_type'] for e in trace['events']]
    assert 'invoke_agent' in types
    assert 'write_state' in types
    assert 'late_event' in types
    assert 'revise_final_state' in types
    assert trace['termination_reason']=='finalized_after_late_event'
    m=topology_metrics(trace)
    assert m['agent_count']>=2
    print('offline engine preflight PASS')
    print(f"events={len(trace['events'])} agents={trace['activated_agent_count']} turns={trace['turns']}")


if __name__=='__main__': main()
