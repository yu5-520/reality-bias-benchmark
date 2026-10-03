"""Read-only complete graph context for route planning, without a repair executor."""
from __future__ import annotations
import copy,hashlib,json
from collections import defaultdict
from stage2.r7_checkpoint_v1.common import digest
from stage2.route_repair.terminal import FrozenGraphAccess


class CompleteRouteContext:
    def __init__(self,graph,archive,case):
        if graph['graph_hash']!=case['graph_hash']:raise ValueError('pinned graph mismatch')
        self.access=FrozenGraphAccess(graph,archive,arm='GRAPH',expected_archive_hash=case['archive_sha256'])
        self.graph=graph;self.case=copy.deepcopy(case);self.cache={};self.files_by_checkpoint={}
        self.ledger=json.loads(self.raw('checkpoint_ledger.json'))
        terminals=[x for x in self.ledger['checkpoints'] if x['boundary']=='TERMINAL']
        if len(terminals)!=1 or terminals[0]['checkpoint_hash']!=case['terminal_checkpoint_hash']:
            raise ValueError('terminal checkpoint mismatch')
        self.file_versions=defaultdict(list);self.ledger_annotations=[]
        for capture_index,row in enumerate(self.ledger['checkpoints']):
            cp=row['checkpoint_hash'];member='checkpoints/'+cp+'/manifest.json'
            manifest=json.loads(self.raw(member))
            if manifest['checkpoint_hash']!=cp:
                raise ValueError('ledger manifest binding mismatch')
            if manifest['event_ref']!=row['event_ref']:
                backed=any(x['checkpoint_hash']==cp and x['event_ref']==manifest['event_ref']
                    and x['model_decision_sequence']==row['model_decision_sequence'] for x in self.ledger['checkpoints'])
                if row['boundary']!='FIRST_MONITOR_REPAIR_ELIGIBLE_POINT' or not backed:
                    raise ValueError('ledger manifest event binding mismatch')
                self.ledger_annotations.append({'ledger_row':copy.deepcopy(row),'native_event_ref':manifest['event_ref'],
                    'scope':'HISTORICAL_MONITOR_ANNOTATION_NOT_A_NEW_NATIVE_CAPTURE'})
                continue
            self.files_by_checkpoint[cp]=manifest['application_file_hashes']
            for path,sha in manifest['application_file_hashes'].items():
                content_member='checkpoints/'+cp+'/application/'+path
                locator=self.locator(content_member)
                if locator['member_sha256']!=sha:raise ValueError('file version checksum mismatch')
                self.file_versions['file:'+path].append({
                    'checkpoint_hash':cp,'capture_index':capture_index,
                    'clock_id':'checkpoint_ledger:model_decision_sequence',
                    'native_sequence':row['model_decision_sequence'],'boundary':row['boundary'],
                    'event_ref':row['event_ref'],'content_sha256':sha,
                    'manifest_source':self.locator(member),'content_source':locator})

    def close(self):self.access.close()

    def raw(self,name):
        if name not in self.cache:self.cache[name]=self.access.member(name)
        return self.cache[name]

    def locator(self,name):
        return {'archive_sha256':self.case['archive_sha256'],'member':name,
            'member_sha256':hashlib.sha256(self.raw(name)).hexdigest(),'json_pointer':'','line':None}

    def read_file(self,ref,checkpoint_hash=None):
        cp=checkpoint_hash or self.case['terminal_checkpoint_hash']
        if not ref.startswith('file:') or ref[5:] not in self.files_by_checkpoint.get(cp,{}):
            raise ValueError('file has no exact version in requested checkpoint')
        member='checkpoints/'+cp+'/application/'+ref[5:]
        return {'ref':ref,'checkpoint_hash':cp,'source_locator':self.locator(member),
            'content':self.raw(member).decode('utf-8')}

    def observation_source(self,observation_id):
        observation=self.access.observations[observation_id]
        return {'observation':copy.deepcopy(observation),'source_text':self.access._source(observation['source_locator'])}

    def node_context(self,ref):
        if ref not in self.access.nodes:raise ValueError('node absent from full graph')
        grouped=defaultdict(list)
        for o in self.access.by_object[ref]:grouped[o['clock_id']].append({
            'observation_id':o['observation_id'],'native_sequence':o['native_sequence'],
            'within_capture_sequence':o.get('within_capture_sequence'),
            'event_ref':o['event_ref'],'source_locator':copy.deepcopy(o['source_locator'])})
        for rows in grouped.values():rows.sort(key=lambda x:(x['native_sequence'],x.get('within_capture_sequence') or 0,x['observation_id']))
        versions=copy.deepcopy(self.file_versions.get(ref,[]))
        current=[x for x in versions if x['checkpoint_hash']==self.case['terminal_checkpoint_hash']]
        return {'ref':ref,'node_type':self.access.nodes[ref]['node_type'],
            'current_file_source':current[-1]['content_source'] if current else None,
            'file_versions':versions,'observations_by_clock':dict(grouped),
            'graph_edges':copy.deepcopy(self.access.by_node_edges[ref]),
            'cross_clock_order_inferred':False,'semantic_dependency_inferred':False,
            'write_authority_granted':False}

    def catalog(self,original_task):
        cp=self.case['terminal_checkpoint_hash']
        current={ref:self.read_file(ref,cp)['source_locator'] for ref in self.file_versions if ref[5:] in self.files_by_checkpoint[cp]}
        payload={'schema':'stage2-complete-node-route-context-v1','full_id':self.case['full_id'],
            'graph_hash':self.graph['graph_hash'],'archive_sha256':self.case['archive_sha256'],
            'parent_checkpoint_hash':cp,'original_task':copy.deepcopy(original_task),
            'all_node_refs':sorted(self.access.nodes),'node_count':len(self.graph['nodes']),
            'edge_count':len(self.graph['edges']),'observation_count':len(self.graph['observations']),
            'current_file_sources':current,'all_file_versions':dict(self.file_versions),
            'ledger_annotations':copy.deepcopy(self.ledger_annotations),
            'full_graph_artifact':'full_graph.json.gz','source_queries':['read_file(ref, checkpoint_hash)',
                'node_context(ref)','observation_source(observation_id)'],
            'visibility_scope':'COMPLETE_OBSERVED_TRAJECTORY_WITHOUT_DEPTH_CUTOFF',
            'source_access_verified':True,'audit_verdicts_included':False,
            'semantic_dependencies_adjudicated':False,'native_executor_ready':False,
            'enhanced_post_repair_graph_ready':False,'live_execution_enabled':False}
        payload['context_hash']=digest(payload)
        return payload
