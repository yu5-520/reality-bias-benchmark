#!/usr/bin/env python3
"""Zero-call native host bridge probe; never a semantic repair evaluation."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from stage2.route_repair.terminal_runner import prepare_terminal,execute_mcp_revision,save
from stage2.route_repair.terminal import validate_terminal_decision
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source-root',type=Path,required=True)
p.add_argument('--graph-root',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
args=p.parse_args()
c=json.load(open(ROOT/'configs/stage2_terminal_route_repair_first_round_v1.json'))
case=c['cases'][0];dest=args.out.resolve()
archive=args.source_root.resolve()/'G3A/stage2/replication_v2/G3/natural_A/X4-T2/first_attempt.tar.gz'
gp=args.graph_root.resolve()/'G3-X4-T2.json.gz'
a,p,state,files=prepare_terminal(case,archive,gp,dest,'GRAPH',c['limits'])
raw=a.query({'op':'read_member','member':'natural_A_result.json'});e=[{'member':raw['member'],'sha256':raw['member_sha256']}]
d=validate_terminal_decision({'decision':'REPAIR','reason':'Synthetic bridge probe only','parent_checkpoint_hash':p['checkpoint_hash'],'evidence':e,'actions':[{'kind':'process_revision','target_ref':'state:terminal','before_hash':p['native_state_sha256'],'instruction':'Preflight only: finalize with the explicit statement SCRIPTED_BRIDGE_PROBE. Preserve every application file.','reason':'Synthetic preflight','evidence':e}]},access=a,parent=p,current_files=files,authorized_files=[],preserve_files=set(files))
class ScriptedProvider:
 def complete_agent(self,messages,metadata=None):
  return {'content':json.dumps({'actions':[{'type':'finalize','answer':'SCRIPTED_BRIDGE_PROBE'}]}),'model':'SCRIPTED_PREFLIGHT_ONLY','usage':{}}
result=execute_mcp_revision(d,p,state,dest/'checkout',dest,ScriptedProvider(),c['limits'],files)
assert result['error'] is None,result
assert result['final_answer']=='SCRIPTED_BRIDGE_PROBE',result
save(dest/'smoke_receipt.json',{'scope':'SCRIPTED_NATIVE_HOST_BRIDGE_ONLY','live_provider_calls':0,'mcp_tool_calls':0,'native_host_state_roundtrip_verified':True,'native_revision_and_watch_exercised':True,'application_preserved':True,'semantic_effect_tested':False,'result':result})
a.close();print(result)
