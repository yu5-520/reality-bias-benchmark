import json
import tempfile
import unittest
from pathlib import Path

from arena.anchor_selection import select_anchor
from arena.branch_plan import build_branch_plan
from arena.branch_recovery_preflight import StatusResponsiveProvider
from arena.derive_branch_measurements import derive_bundle
from arena.engine import run_arena_once
from arena.io_utils import load_json, sha256_file, write_jsonl
from arena.providers import ScriptedProvider


ROOT = Path(__file__).resolve().parents[2]


class BranchMeasurementDerivationTest(unittest.TestCase):
    def setUp(self):
        self.domain_path = ROOT / 'arena/domains/ecommerce.json'
        self.arena_path = ROOT / 'arena/config/arena_v0.3.json'
        self.model_path = ROOT / 'arena/config/model_deepseek_v0.2.json'
        self.rule_path = ROOT / 'arena/config/r5r6_anchor_rule_v0.1.json'
        self.domain = load_json(self.domain_path)
        self.config = load_json(self.arena_path)
        self.rule = load_json(self.rule_path)

    def _plan_bundle(self):
        anchors = []
        trace = run_arena_once(
            self.domain,
            self.config,
            ScriptedProvider([
                {
                    'decision_summary': 'ask inventory',
                    'actions': [{'type': 'invoke_agent', 'agent_id': 'inventory', 'request': 'Check stock.'}],
                },
                {
                    'decision_summary': 'write candidate',
                    'actions': [{
                        'type': 'write_state',
                        'key': 'inventory_view',
                        'value': 'Stockout certain',
                        'status': 'fact',
                        'basis': 'derivation fixture',
                    }],
                },
                {'decision_summary': 'finish', 'actions': [{'type': 'finalize', 'answer': 'Plan.'}]},
                {'decision_summary': 'finish late', 'actions': [{'type': 'finalize', 'answer': 'Plan late.'}]},
            ]),
            'branch-measurement-phase-a-fixture',
            logical_seed=1,
            state_snapshot_callback=anchors.append,
        )
        trace.update({
            'provider': 'deepseek',
            'domain_hash': sha256_file(self.domain_path),
            'arena_config_path': 'arena/config/arena_v0.3.json',
            'arena_config_version': self.config['version'],
            'arena_config_hash': sha256_file(self.arena_path),
            'model_config_path': 'arena/config/model_deepseek_v0.2.json',
            'model_config_version': load_json(self.model_path).get('config_version'),
            'model_config_hash': sha256_file(self.model_path),
            'anchor_rule_path': 'arena/config/r5r6_anchor_rule_v0.1.json',
            'anchor_rule_hash': sha256_file(self.rule_path),
            'code_commit_sha': 'BASELINE_FIXTURE_SHA',
        })
        selection = select_anchor(
            trace,
            anchors,
            self.rule,
            evidence_hash='phase-a-derivation-evidence',
            selection_id='DERIVATION-FIXTURE-SEL',
        )
        return build_branch_plan(
            selection,
            trace,
            replicates=1,
            branch_code_sha='BRANCH_FIXTURE_SHA',
        )

    def test_complete_pair_derives_measurement_v3_without_semantic_promotion(self):
        bundle = self._plan_bundle()
        manifest_by_hash = {row['branch_hash']: row for row in bundle['branch_manifests']}
        traces = []
        for row in bundle['branch_rows']:
            start = (
                bundle['parent_snapshot']
                if row['condition_id'] == 'CONTROL_CONTINUATION'
                else bundle['intervention_start_snapshot']
            )
            label = 'control' if row['condition_id'] == 'CONTROL_CONTINUATION' else 'intervention'
            trace = run_arena_once(
                self.domain,
                self.config,
                StatusResponsiveProvider(label),
                row['run_id'],
                logical_seed=row['logical_seed'],
                initial_state_snapshot=start,
                branch_manifest=manifest_by_hash[row['branch_hash']],
            )
            trace.update({
                'pair_id': row['pair_id'],
                'replicate_index': row['replicate_index'],
                'condition_id': row['condition_id'],
                'pair_order_pattern': row['pair_order_pattern'],
                'execution_order': row['execution_order'],
                'branch_plan_hash': bundle['plan']['plan_hash'],
            })
            self.assertEqual('RUN_COMPLETE', trace['run_status'])
            traces.append(trace)

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            plan_dir = tmp / 'plan'
            plan_dir.mkdir()
            (plan_dir / 'branch_plan.json').write_text(json.dumps(bundle['plan']), encoding='utf-8')
            (plan_dir / 'parent_snapshot.json').write_text(json.dumps(bundle['parent_snapshot']), encoding='utf-8')
            (plan_dir / 'intervention_start_snapshot.json').write_text(json.dumps(bundle['intervention_start_snapshot']), encoding='utf-8')
            write_jsonl(plan_dir / 'branch_execution_manifest.jsonl', bundle['branch_rows'])
            write_jsonl(plan_dir / 'branch_manifests.jsonl', bundle['branch_manifests'])
            traces_path = tmp / 'traces.jsonl'
            write_jsonl(traces_path, traces)
            evidence_path = tmp / 'evidence_batch.json'
            evidence_path.write_text(json.dumps({'evidence_batch_hash': 'TEST_FROZEN_EVIDENCE_HASH'}), encoding='utf-8')

            measurements, comparisons, summary = derive_bundle(
                plan_dir=plan_dir,
                traces_path=traces_path,
                evidence_batch_path=evidence_path,
            )

        self.assertEqual(2, len(measurements))
        self.assertEqual(1, len(comparisons))
        self.assertEqual(1, summary['structurally_measured_pair_count'])
        self.assertTrue(all(row['evidence_batch_hash'] == 'TEST_FROZEN_EVIDENCE_HASH' for row in measurements))
        self.assertTrue(all(row['semantic_status']['C'] == 'NOT_ADJUDICATED' for row in measurements))
        self.assertEqual('NOT_ADJUDICATED', comparisons[0]['semantic_status']['causal_effect'])
        self.assertEqual('NOT_ADJUDICATED', summary['authority_penetration_status'])
        self.assertEqual('PAIR_MEASURED_STRUCTURALLY', summary['pair_index'][0]['pair_status'])
        self.assertTrue(comparisons[0]['intervention_changed_start_state'])


if __name__ == '__main__':
    unittest.main()
