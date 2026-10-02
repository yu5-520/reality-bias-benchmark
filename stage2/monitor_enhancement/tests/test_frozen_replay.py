import copy
import gzip
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from stage2.r7_checkpoint_v1.common import digest
from stage2.monitor_enhancement.frozen_archive import NativeArchive, ArchiveError
from stage2.monitor_enhancement.evidence_graph import EvidenceGraph, EvidenceGraphError
from stage2.monitor_enhancement.observation_adapter import adapt_relation_evidence
from stage2.monitor_enhancement.replay_analysis import select_candidates, exact_file_mentions
from stage2.monitor_enhancement.route_export import export_observation_map


class NativeReplayTest(unittest.TestCase):
    def archive(self, files, full_id='G2-X1-T1'):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        buf=io.BytesIO()
        with tarfile.open(fileobj=buf,mode='w') as tf:
            for name,value in files.items():
                raw=value if isinstance(value,bytes) else json.dumps(value).encode()
                info=tarfile.TarInfo('./'+name);info.size=len(raw);tf.addfile(info,io.BytesIO(raw))
        raw=gzip.compress(buf.getvalue());p=Path(tmp.name)/'first_attempt.tar.gz';p.write_bytes(raw)
        return NativeArchive(p,full_id,digest(raw))

    def rows(self):
        a=self.archive({'value.json':{'content':'use web/app.js'}})
        for sequence in [2,10]:
            a.payload('value.json',a.json('value.json'),sequence=sequence,clock='capture',kind='MESSAGE',ref='message:same')
        return a

    def test_equal_payload_distinct_occurrences_and_field_binding(self):
        a=self.rows();self.assertEqual(a.verify_observations(),4)
        g=EvidenceGraph()
        for r in a.observations:g.add_observation(r)
        snap=g.snapshot();self.assertEqual(len([n for n in snap['nodes'] if n['node_type']=='EVENT']),2)
        self.assertEqual(next(n for n in snap['nodes'] if n['ref']=='file:web/app.js')['sequences'],[2,10])
        a.observations[1]['field_value_hash']='invalid'
        with self.assertRaises(ArchiveError):a.verify_observations()

    def test_observation_identity_cannot_be_rebound(self):
        a=self.rows();g=EvidenceGraph();g.add_observation(a.observations[0])
        other=copy.deepcopy(a.observations[0]);other['version']='changed'
        with self.assertRaises(EvidenceGraphError):g.add_observation(other)

    def test_missing_stream_and_corrupt_archive_fail(self):
        a=self.archive({'unrelated.json':{}})
        with self.assertRaises(ArchiveError):a.observer_stream('autogen_observer')
        with self.assertRaises(ArchiveError):NativeArchive(a.path,a.full_id,'0'*64)

    def test_snapshot_and_cross_clock_do_not_inflate_native_span(self):
        a=self.rows();rows=a.observations[::2]
        rows[0]['clock_id']='clock1';rows[1]['clock_id']='clock2'
        graph={'observations':rows}
        self.assertEqual(select_candidates(graph),[])
        rows.extend([{**rows[0],'event_ref':'snapshot'+str(i),'source_kind':'CHECKPOINT_SNAPSHOT'} for i in range(5)])
        self.assertEqual(select_candidates(graph),[])

    def test_exact_file_proxy_rejects_generic_and_wrong_directory(self):
        refs=['file:web/app.js','file:other/app.js']
        self.assertEqual(exact_file_mentions(refs,'file app.js'),[])
        self.assertEqual(exact_file_mentions(refs,'use web/app.js.'),[])
        self.assertEqual(exact_file_mentions(refs,'use `web/app.js`'),['file:web/app.js'])

    def test_zero_mcp_requires_complete_invalid_history(self):
        valid={'turns':2,'history':[{'valid':False},{'valid':False,'actions':[]}]}
        a=self.archive({'natural_A_result.json':valid},'G5-X4-T1');a.mcp()
        self.assertEqual(a.coverage['explicit_zero_native_call_history'],1)
        for invalid in [{'turns':3,'history':valid['history']},{'turns':1,'history':[{'valid':True}]}]:
            a=self.archive({'natural_A_result.json':invalid},'G5-X4-T1')
            with self.assertRaises(ArchiveError):a.mcp()

    def test_missing_relation_evidence_level_is_unknown(self):
        row=adapt_relation_evidence({'relation_id':'r','source_ref':'a','destination_ref':'b','relation_type':'reuse','evidence_refs':['e']})
        self.assertEqual(row['status'],'UNKNOWN')

    def test_complete_observation_map_grants_no_authority(self):
        a=self.rows();g=EvidenceGraph()
        for r in a.observations:g.add_observation(r)
        snap=g.snapshot();route=export_observation_map(snap)
        self.assertEqual(route['observations'],snap['observations'])
        self.assertFalse(route['eligible_as_repair_input']);self.assertEqual(route['authorized_write_refs'],[])

if __name__=='__main__':unittest.main()
