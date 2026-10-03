#!/usr/bin/env python3
"""Replay retained first-attempt queries and verify decisions; no model calls."""
import argparse,gzip,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from stage2.route_repair.terminal import FrozenGraphAccess,validate_terminal_decision

def read(p):return json.loads(Path(p).read_text())

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--graph-root',type=Path,required=True)
    parser.add_argument('--result-root',type=Path,default=ROOT/'stage2/replication_v2/terminal_route_repair_first_attempt_v1')
    args=parser.parse_args();r=args.result_root
    seal=read(r/'seal.json')
    for name,sha in seal['files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha, name
    config=read(r/'frozen_case_config.json');summary=read(r/'summary.json')
    assert config==read(ROOT/'configs/stage2_terminal_route_repair_first_round_v1.json')
    for name,sha in read(r/'run_binding.json')['implementation_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha, name
    with gzip.open(r/'full_model_query_trace.json.gz') as f:traces=json.load(f)['files']
    assert summary['mode']=='ACTIVE' and len(summary['arms'])==4
    calls=0;queries=0;bindings=[]
    for row in summary['arms']:
        case=next(x for x in config['cases'] if x['full_id']==row['full_id'])
        name=row['full_id']+'-'+row['arm'];folder=r/name
        parent=read(folder/'parent_binding.json')
        assert parent['parent_checkpoint_hash']==case['terminal_checkpoint_hash']
        assert parent['archive_sha256']==case['archive_sha256'] and parent['graph_hash']==case['graph_hash']
        g,cell=row['full_id'].split('-',1)
        archive=args.source_root/(g+'A')/'stage2/replication_v2'/g/'natural_A'/cell/'first_attempt.tar.gz'
        with gzip.open(args.graph_root/(row['full_id']+'.json.gz')) as f:graph=json.load(f)['graph']
        assert graph['graph_hash']==case['graph_hash']
        access=FrozenGraphAccess(graph,archive,arm=row['arm'],expected_archive_hash=case['archive_sha256'],
            max_queries=config['limits']['max_queries'],response_chars=config['limits']['max_response_chars'],
            total_chars=config['limits']['max_total_evidence_chars'])
        try:
            for recorded in traces[name+'/evidence_query_log.json']:
                try:response=access.query(recorded['request'])
                except Exception as exc:
                    assert recorded.get('error_type')==type(exc).__name__ and recorded.get('error')==str(exc)
                else:assert response==recorded['response']
                queries+=1
            responses=sorted(k for k in traces if k.startswith(name+'/diagnosis_') and k.endswith('_response.json'))
            requests=sorted(k for k in traces if k.startswith(name+'/diagnosis_') and k.endswith('_request.json'))
            assert len(responses)==len(requests)==row['provider_calls']<=config['limits']['max_agent_calls']
            assert all(traces[k]['model']==read(folder/'provider_binding.json')['model_alias'] for k in responses)
            calls+=len(requests);bindings.append(read(folder/'provider_binding.json'))
            if (folder/'agent_decision_raw.json').exists():
                raw=read(folder/'agent_decision_raw.json');assert raw==json.loads(traces[responses[-1]]['content'])
                gate_parent={'checkpoint_hash':parent['parent_checkpoint_hash'],'restore_capability':'FULL_NATIVE',
                    'native_state_sha256':parent['native_state_sha256']}
                decision=validate_terminal_decision(raw,access=access,parent=gate_parent,current_files=parent['application_files'],
                    authorized_files=[x[5:] for x in case['authorized_file_refs']],preserve_files=[x[5:] for x in case['preserve_file_refs']],
                    max_actions=config['limits']['max_actions'])
                assert decision==read(folder/'validated_decision.json')
                assert decision['actions']==[]
            else:assert row['error']=='NO_DECISION_WITHIN_CALL_BUDGET' and len(requests)==6
            check=read(folder/'downloaded_application_verification.json')
            assert check['application_preserved'] and check['files']==parent['application_files']
        finally:access.close()
    assert all(b==bindings[0] for b in bindings)
    assert calls==summary['provider_calls']==21 and summary['subject_reruns']==0
    assert not any('/continuation_' in name for name in traces)
    print(json.dumps({'status':'PASS','retained_calls':calls,'queries_reproduced':queries,
        'live_provider_calls_in_validation':0,'native_actions_in_trial':0,'semantic_efficacy_validated':False}))

if __name__=='__main__':main()
