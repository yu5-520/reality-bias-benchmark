#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from arena.core import validate_domain
from arena.io_utils import load_json
from arena.prompts import build_agent_messages


def main():
    config=load_json(ROOT/'arena/config/arena_v0.1.json')
    assert config['design']=='fixed_environment_free_routing'
    for domain_id in config['default_domains']:
        path=ROOT/f'arena/domains/{domain_id}.json'
        domain=load_json(path)
        validate_domain(domain)
        entry=next(a for a in domain['agents'] if a['id']==domain['entry_agent'])
        msgs=build_agent_messages(domain,entry,{
            'shared_state':domain['task']['initial_shared_state'],
            'final_state':None,'inbox':[],'active_agents':[domain['entry_agent']],
            'remaining_turn_budget':config['max_turns']
        })
        text=str(msgs)
        for forbidden in ('Completion Bias','Perfection Bias','Retrospective Bias','Information Authority','Invocation Authority','Temporal Authority'):
            if forbidden in text:
                raise AssertionError(f'{domain_id} agent prompt leaked research label: {forbidden}')
        print(f"OK {domain_id}: agents={len(domain['agents'])}")
    print('environment validation PASS')


if __name__=='__main__': main()
