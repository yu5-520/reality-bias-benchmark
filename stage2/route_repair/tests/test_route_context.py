import hashlib,io,json,subprocess,sys,tarfile,tempfile,unittest
from pathlib import Path
from stage2.r7_checkpoint_v1.common import digest
from stage2.route_repair.route_context import CompleteRouteContext
from stage2.route_repair.terminal_runner import build_provider

class RouteContextTests(unittest.TestCase):
    def make_context(self,root,*,drift=False,alias=False):
        raw={'checkpoint_ledger.json':{'checkpoints':[
            {'boundary':'TASK_START','checkpoint_hash':'c0','event_ref':'start','model_decision_sequence':0},
            {'boundary':'TERMINAL','checkpoint_hash':'c1','event_ref':'end','model_decision_sequence':2}]}}
        if alias:raw['checkpoint_ledger.json']['checkpoints'].insert(1,{'boundary':'FIRST_MONITOR_REPAIR_ELIGIBLE_POINT',
            'checkpoint_hash':'c0','event_ref':'structural-annotation','model_decision_sequence':0})
        for cp,event,content in [('c0','start',b'x=1\n'),('c1','end',b'x=2\n')]:
            raw['checkpoints/'+cp+'/application/a.py']=content
            raw['checkpoints/'+cp+'/manifest.json']={'checkpoint_hash':cp,'event_ref':event,
                'application_file_hashes':{'a.py':'drift' if drift else hashlib.sha256(content).hexdigest()}}
        path=root/'archive.tar.gz'
        with tarfile.open(path,'w:gz') as tf:
            for name,value in raw.items():
                data=value if isinstance(value,bytes) else json.dumps(value).encode()
                m=tarfile.TarInfo(name);m.size=len(data);tf.addfile(m,io.BytesIO(data))
        graph={'nodes':[{'ref':'file:a.py','node_type':'OBSERVED_OBJECT'},
            {'ref':'state:terminal','node_type':'OBSERVED_OBJECT'}],'edges':[],'observations':[]}
        graph['graph_hash']=digest(graph)
        case={'full_id':'fixture','graph_hash':graph['graph_hash'],'archive_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'terminal_checkpoint_hash':'c1'}
        return CompleteRouteContext(graph,path,case)
    def test_current_and_historical_file_sources_are_unambiguous(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.make_context(Path(t))
            try:
                self.assertEqual(c.read_file('file:a.py')['content'],'x=2\n')
                self.assertEqual(c.read_file('file:a.py','c0')['content'],'x=1\n')
                self.assertEqual(c.read_file('file:a.py')['source_locator']['member'],'checkpoints/c1/application/a.py')
            finally:c.close()
    def test_complete_context_preserves_all_nodes_without_write_authority(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.make_context(Path(t))
            try:
                catalog=c.catalog({'user_request':'original broad task'})
                self.assertEqual(len(catalog['all_node_refs']),2)
                self.assertFalse(catalog['live_execution_enabled'])
                self.assertFalse(c.node_context('file:a.py')['write_authority_granted'])
                self.assertEqual(len(catalog['all_file_versions']['file:a.py']),2)
            finally:c.close()
    def test_source_alias_is_not_invented(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.make_context(Path(t))
            try:
                with self.assertRaisesRegex(ValueError,'exact version'):c.read_file('file:other/a.py')
            finally:c.close()
    def test_structural_annotation_is_not_a_new_native_capture(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.make_context(Path(t),alias=True)
            try:
                self.assertEqual(len(c.file_versions['file:a.py']),2)
                self.assertEqual(c.ledger_annotations[0]['native_event_ref'],'start')
            finally:c.close()
    def test_checksum_drift_blocks_context(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(ValueError,'checksum mismatch'):self.make_context(Path(t),drift=True)

class PrematureExecutionGateTests(unittest.TestCase):
    def test_historical_provider_builder_cannot_start_a_live_call(self):
        with self.assertRaisesRegex(RuntimeError,'LIVE_EXECUTION_DISABLED'):build_provider()
    def test_cli_blocks_execute_before_archive_or_output_access(self):
        root=Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'must-not-exist'
            r=subprocess.run([sys.executable,str(root/'scripts/run_stage2_terminal_route_repair.py'),
                '--source-root','missing','--graph-root','missing','--out',str(out),'--execute'],capture_output=True,text=True)
            self.assertEqual(r.returncode,2);self.assertIn('INCOMPLETE_NODE_ROUTE_REPAIR_DESIGN',r.stdout)
            self.assertFalse(out.exists())

if __name__=='__main__':unittest.main()
