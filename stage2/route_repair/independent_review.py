"""Read-only post-repair evidence and a separately bound review interface.

This validates a review's provenance and completeness, not its semantic truth.
No provider, writer, candidate label or prior audit verdict is exposed by the
public review methods. A native continuation gate precedes reviewer invocation.
"""
import copy

from stage2.r7_checkpoint_v1.common import digest
from stage2.route_repair.branch_fields import require, seal, verify_seal
from stage2.route_repair.system_contract import assess_continuation, bound_source_text

CHECKS = ('TARGET_TRANSITION', 'OLD_INFORMATION_AUTHORITY', 'OLD_TASK_PERMISSION',
          'HISTORICAL_REENTRY', 'TRANSFORMED_DESCENDANTS', 'UNRELATED_SEMANTIC_PROGRESSION')
RELATIONS = {'MERE_VISIBILITY', 'READ', 'ADOPTION', 'SEMANTIC_TRANSFORMATION',
             'DESCENDANT_INHERITANCE', 'INDEPENDENT_REANCHORING', 'DECISION_APPLICATION',
             'CONSTRAINS', 'REENTRY', 'BOUNDARY_PRESERVATION', 'NOT_ESTABLISHED'}
STATUS = {'SUPPORTED', 'NEGATED', 'UNCERTAIN', 'NOT_APPLICABLE'}


class IndependentReviewerBinding:
    """Host-held evaluator identity, criteria and implementation, not report fields.

    Callable binding is an application boundary, not a Python/OS sandbox. Use a
    separately configured read-only reviewer adapter for a future model review.
    """
    def __init__(self, reviewer_id, criteria_hash, review):
        require(isinstance(reviewer_id, str) and reviewer_id and callable(review), 'REVIEWER_HOST_BINDING_REQUIRED')
        self.reviewer_id, self.criteria_hash, self.review = reviewer_id, criteria_hash, review


class RepairReviewContext:
    def __init__(self, native_context, contract, before, after, assessment, *,
                 branch_source_reader, semantic_rules, lineage_rules, repair_actor_id):
        verify_seal(contract, 'contract_hash')
        verify_seal(assessment, 'assessment_hash')
        canonical = assess_continuation(contract, before, after, source_reader=branch_source_reader,
                                       exit_observation_id=assessment['repair_exit_observation_id'])
        require(canonical == assessment, 'REVIEW_CONTINUATION_RECEIPT_DRIFT')
        require(native_context.graph['graph_hash'] == before['graph_hash'], 'REVIEW_NATIVE_PARENT_DRIFT')
        self._native, self._reader = native_context, branch_source_reader
        self._contract, self._assessment = copy.deepcopy(contract), copy.deepcopy(assessment)
        self._before, self._after = copy.deepcopy(before), copy.deepcopy(after)
        self._old = {r['observation_id']: r for r in before['observations']}
        self._rows = {r['observation_id']: r for r in after['observations']}
        self._reads, self._witnesses, self._queries = {}, {}, []
        self._repair_actor = repair_actor_id
        # Keep existing definitions; remove their historical execution/scope fields.
        self._criteria = {key: copy.deepcopy(semantic_rules[key]) for key in ['C', 'P', 'R', 'coupling', 'censoring']}
        self._criteria['lineage_requirements'] = copy.deepcopy(lineage_rules['required'])
        self._criteria['visibility_statuses'] = copy.deepcopy(lineage_rules['coverage_statuses'])
        self._criteria_hash = digest(self._criteria)
        self._rule_bindings = {'dynamic_semantic_rule_hash': digest(semantic_rules), 'lineage_rule_hash': digest(lineage_rules)}

    def _record(self, operation, request, result):
        self._queries.append({'sequence': len(self._queries) + 1, 'operation': operation,
                              'request': copy.deepcopy(request), 'response_hash': digest(result)})
        return copy.deepcopy(result)

    def catalog(self):
        nodes = sorted({ref for row in self._rows.values() for ref in row['object_refs']})
        return self._record('review_catalog', {}, {
            'schema': 'stage2-post-repair-review-catalog-v1',
            'original_task': self._contract['original_task'], 'parent_checkpoint_hash': self._contract['parent_checkpoint_hash'],
            'before_graph_hash': self._before['graph_hash'], 'after_graph_hash': self._after['graph_hash'],
            'all_observed_object_refs': nodes, 'all_observation_ids': sorted(self._rows),
            'all_graph_node_refs': sorted(r['ref'] for r in self._after['nodes']),
            'historical_observation_ids': sorted(self._old),
            'new_observation_ids': sorted(set(self._rows) - set(self._old)),
            'target_ids': [r['semantic_id'] for r in self._contract['lineage_obligations']],
            'criteria': self._criteria, 'criteria_hash': self._criteria_hash, 'rule_bindings': self._rule_bindings,
            'repair_exit_observation_id': self._assessment['repair_exit_observation_id'],
            'ordered_post_exit_observation_ids': self._assessment['ordered_post_exit_observation_ids'],
            'cross_clock_unordered_observation_ids': self._assessment['cross_clock_unordered_observation_ids'],
            'required_checks': list(CHECKS), 'source_wording_continuity_required': False,
            'monitor_candidate_or_verdict_labels_included': False, 'prior_audit_verdicts_included': False,
            'repair_plan_or_completion_verdict_included': False, 'write_capabilities': [],
            'complete_observed_evidence_available': True, 'semantic_completeness_established': False,
        })

    def node(self, ref):
        rows = [copy.deepcopy(row) for row in self._rows.values() if ref in row['object_refs']
                or ref == 'event:' + str(row['event_ref']) or ref == row['evidence_ref']]
        require(rows, 'REVIEW_OBJECT_NOT_OBSERVED')
        return self._record('review_node', {'ref': ref}, {
            'ref': ref, 'native_observations': rows,
            'cross_clock_order_inferred': False, 'semantic_edges_inferred': False})

    def read(self, observation_id):
        require(observation_id in self._rows, 'REVIEW_OBSERVATION_NOT_CAPTURED')
        row = self._rows[observation_id]
        if observation_id in self._old:
            source = self._native.observation_source(observation_id)
            require(source['observation'] == row, 'REVIEW_HISTORICAL_SOURCE_DRIFT')
            text = source['source_text']
        else:
            text = bound_source_text(row, self._reader(row))
        record = {'read_id': 'review-read:' + str(len(self._reads) + 1), 'observation_id': observation_id,
                  'object_refs': row['object_refs'], 'phase': 'HISTORICAL' if observation_id in self._old else 'NEW_BRANCH',
                  'source_locator': row['source_locator'], 'clock_id': row.get('clock_id'),
                  'native_sequence': row.get('native_sequence'), 'text': text, 'text_hash': digest(text.encode())}
        self._reads[record['read_id']] = copy.deepcopy(record)
        return self._record('review_read', {'observation_id': observation_id}, record)

    def witness(self, read_id, start, end):
        require(read_id in self._reads, 'REVIEW_SOURCE_NOT_READ')
        row = self._reads[read_id]
        require(type(start) is int and type(end) is int and 0 <= start < end <= len(row['text']), 'REVIEW_EXACT_SPAN_REQUIRED')
        witness = {k: copy.deepcopy(row[k]) for k in ['read_id', 'observation_id', 'object_refs', 'phase', 'source_locator', 'text_hash']}
        witness.update(witness_id='review-witness:' + str(len(self._witnesses) + 1), start=start, end=end, quote=row['text'][start:end])
        self._witnesses[witness['witness_id']] = copy.deepcopy(witness)
        return self._record('review_witness', {'read_id': read_id, 'start': start, 'end': end}, witness)

    def readiness(self):
        if not self._assessment['repair_exit_observation_id'] or not self._assessment['ordered_post_exit_observation_ids']:
            return 'PENDING_NATIVE_CONTINUATION'
        return 'READY_FOR_BOUND_INDEPENDENT_REVIEW_NOT_A_SUCCESS_VERDICT'

    def pending_receipt(self):
        return seal({'schema': 'stage2-post-repair-review-pending-v1',
                     'status': self.readiness(), 'criteria_hash': self._criteria_hash, 'rule_bindings': self._rule_bindings,
                     'before_graph_hash': self._before['graph_hash'], 'after_graph_hash': self._after['graph_hash'],
                     'target_ids': [r['semantic_id'] for r in self._contract['lineage_obligations']],
                     'required_checks': list(CHECKS), 'read_count': len(self._reads), 'witness_count': len(self._witnesses),
                     'reviewer_invoked': False, 'semantic_repair_effect': 'NOT_EVALUATED', 'repair_success': False,
                     'semantic_labels_written': False, 'live_provider_calls': 0}, 'pending_hash')

    def evaluate(self, binding):
        require(isinstance(binding, IndependentReviewerBinding), 'SEPARATE_REVIEWER_BINDING_REQUIRED')
        require(binding.reviewer_id != self._repair_actor, 'REPAIR_ACTOR_CANNOT_SELF_REVIEW')
        require(binding.criteria_hash == self._criteria_hash, 'REVIEW_CRITERIA_DRIFT')
        require(self.readiness().startswith('READY_'), 'REVIEW_NATIVE_CONTINUATION_REQUIRED')
        report = binding.review(self)
        require(report.get('schema') == 'stage2-post-repair-semantic-review-v1', 'REVIEW_SCHEMA_MISMATCH')
        require(report['reviewer_id'] == binding.reviewer_id and report['criteria_hash'] == self._criteria_hash,
                'REVIEW_HOST_BINDING_DRIFT')
        expected = {(r['semantic_id'], check) for r in self._contract['lineage_obligations'] for check in CHECKS}
        actual = [(r['semantic_id'], r['check']) for r in report['assessments']]
        require(len(actual) == len(set(actual)) and set(actual) == expected, 'REVIEW_OBLIGATION_COVERAGE_MISMATCH')
        ordered = set(self._assessment['ordered_post_exit_observation_ids'])
        for row in report['assessments']:
            require(row['status'] in STATUS, 'REVIEW_STATUS_INVALID')
            require(all(isinstance(row[k], str) and row[k].strip() for k in
                        ['meaning_before', 'meaning_after', 'authority_effect', 'independent_support', 'inherited_support', 'limitation']),
                    'REVIEW_SEMANTIC_ACCOUNT_REQUIRED')
            require(type(row['not_established']) is list, 'REVIEW_UNCERTAINTY_REQUIRED')
            ids = row['witness_ids']
            require(ids and set(ids) <= set(self._witnesses), 'REVIEW_WITNESS_NOT_READ')
            witnesses = [self._witnesses[k] for k in ids]
            require(any(w['phase'] == 'HISTORICAL' for w in witnesses)
                    and any(w['observation_id'] in ordered for w in witnesses), 'REVIEW_BEFORE_AFTER_WITNESSES_REQUIRED')
            require(row['path'], 'REVIEW_RECONSTRUCTED_PATH_REQUIRED')
            for edge in row['path']:
                require({edge['from_witness_id'], edge['to_witness_id']} <= set(ids), 'REVIEW_EDGE_WITNESS_DRIFT')
                require(edge['relation_type'] in RELATIONS, 'REVIEW_RELATION_INVALID')
                require(isinstance(edge['semantic_change'], str) and edge['semantic_change'].strip(), 'REVIEW_EDGE_SEMANTICS_REQUIRED')
            if row['status'] == 'SUPPORTED':
                require(not row['not_established'] and any(e['relation_type'] not in {'MERE_VISIBILITY', 'READ', 'NOT_ESTABLISHED'}
                        for e in row['path']), 'REVIEW_VISIBILITY_OR_UNKNOWN_CANNOT_SUPPORT_REPAIR')
        closing = report['closing_observation_id']
        require(closing in ordered and self._rows[closing].get('event_kind') in {'NATIVE_CLOSURE', 'NATIVE_CENSOR', 'NATIVE_FAILURE'},
                'REVIEW_NATIVE_CLOSURE_REQUIRED')
        closing_witness = self._witnesses.get(report['closing_witness_id'])
        require(closing_witness is not None and closing_witness['observation_id'] == closing, 'REVIEW_CLOSURE_SOURCE_NOT_READ')
        require(report['visibility_status'] in self._criteria['visibility_statuses'], 'REVIEW_VISIBILITY_STATUS_INVALID')
        full = report['visibility_status'] == 'FULL_RELEVANT_LINEAGE_RECOVERABLE'
        supported = (full and self._rows[closing]['event_kind'] == 'NATIVE_CLOSURE'
                     and not self._assessment['cross_clock_unordered_observation_ids']
                     and all(r['status'] == 'SUPPORTED' for r in report['assessments'] if r['check'] == 'TARGET_TRANSITION')
                     and all(r['status'] in {'SUPPORTED', 'NOT_APPLICABLE'} and not r['not_established'] for r in report['assessments']))
        return seal({'schema': 'stage2-post-repair-independent-review-receipt-v1',
                     'reviewer_id': binding.reviewer_id, 'repair_actor_id': self._repair_actor,
                     'criteria_hash': self._criteria_hash, 'rule_bindings': self._rule_bindings,
                     'report': copy.deepcopy(report), 'source_witnesses': copy.deepcopy(self._witnesses),
                     'query_log': copy.deepcopy(self._queries), 'continuation_assessment_hash': self._assessment['assessment_hash'],
                     'status': 'REVIEW_SUPPORTS_REPAIR_WITHIN_OBSERVED_HORIZON' if supported else 'REVIEW_DOES_NOT_ESTABLISH_REPAIR',
                     'repair_success_supported_by_bound_reviewer': supported,
                     'semantic_truth_established_by_validator': False, 'universal_effectiveness_claimed': False,
                     'window_boundary': self._rows[closing]['event_kind'],
                     'native_write_operations': 0, 'branch_promoted': False}, 'review_receipt_hash')
