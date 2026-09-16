# CPR Adjudication Contract v1

Date: 2026-09-17  
Status: FORWARD R8 REVIEW CONTRACT / APPEND-ONLY  
Depends on: `CPR_DEFINITION_CONTRACT_v1.md`, `docs/R8_CPR_semantic_closure_protocol_v0.1.md`.

## 1. Purpose

This contract specifies how frozen structural candidates may be reviewed semantically under CPR without mutating the underlying raw or structural evidence.

It supplements existing independent semantic-review infrastructure. It does not invalidate prior reviewer protocols or prior review records.

## 2. Eligibility

A CPR review packet is eligible only if:

- its raw/source evidence is identified;
- the structural candidate/window is frozen or otherwise version-bound;
- the packet contains the minimum context required by the candidate type;
- no source freeze explicitly forbids later semantic adjudication.

Evidence protected by a `NOT_ADJUDICATED` no-new-review freeze remains ineligible unless a later source contract explicitly permits an append-only derivative review without altering the protected evidence identity.

## 3. Packet construction

A packet should contain the smallest sufficient evidence window, including where relevant:

- candidate event/window identity;
- pre/post state/status;
- source evidence refs;
- task/role/authority context needed to judge support or scope;
- source-backed prior lineage;
- downstream inheritance needed to judge operational significance;
- retrospective/challenge/reopen/correction boundary for R candidates;
- explicit missingness/censoring notes.

Reviewers should not be required to reconstruct the full system graph if the structural layer has already frozen the candidate and its evidence refs.

## 4. Reviewer independence

Each review record must bind:

- reviewer identity/class without exposing unnecessary personal data;
- model/provider/version where a model reviewer is used;
- prompt/instruction version;
- packet hash/identity;
- CPR definition-contract version;
- review timestamp;
- review output and confidence/uncertainty representation.

Later reviewers must not overwrite earlier reviewer outputs.

## 5. Allowed primary outcomes

For a candidate packet, an eligible reviewer may return:

- `C`;
- `P`;
- `R`;
- `MULTI_LABEL` only if the review launch contract explicitly permits it;
- `NON_CPR`;
- `UNRESOLVED`;
- `NOT_APPLICABLE`.

A reviewer must be able to explain which required semantic condition is supported, absent or unresolved using packet evidence refs.

## 6. Structural candidate versus semantic result

The following distinction is mandatory:

- `STRUCTURAL_CANDIDATE_ONLY` means a structural detector/measurement identified a window requiring possible semantic review;
- `ADJUDICATED_*` means a separate semantic review process reached the named result under a frozen adjudication rule.

A candidate that is rejected as CPR remains valid structural evidence.

## 7. Multiple reviewers and disagreement

Multiple reviews are append-only.

Before a confirmatory semantic batch, its launch record must freeze one of the following aggregation modes:

- no aggregate label; report reviewer-level results only;
- exact agreement requirement;
- preregistered majority/consensus rule;
- explicit independent adjudicator over conflicting parent reviews.

No aggregation rule may be invented after seeing the desired semantic outcome.

If the frozen rule cannot resolve disagreement, status remains `REVIEW_DISAGREEMENT`.

## 8. R-specific prerequisite

An R-positive adjudication requires:

- an eligible prior semantic lineage under the review contract;
- a valid retrospective/challenge/reopen/correction boundary;
- source-backed evidence of post-boundary persistence/regeneration/amplification/laundering/normalization.

A later similar Jump alone is insufficient.

## 9. Missingness

- missing evidence != semantic negative;
- censored downstream window != no recurrence;
- absent reviewer != `NON_CPR`;
- `UNRESOLVED` != `NON_CPR`;
- invalid packet != semantic negative.

## 10. Adjudication record

An aggregate/adjudication record, when produced, must reference:

- all parent review record IDs/hashes;
- frozen aggregation/adjudication rule;
- resulting status;
- unresolved disagreements if any;
- CPR definition-contract version;
- packet identity;
- provenance back to structural evidence.

## 11. Append-only rule

New interpretation layers may be added later, including R9 reviewer robustness studies, but they must not mutate:

- raw evidence;
- structural derivation;
- prior packets;
- prior reviewer outputs;
- prior adjudication records.

If a semantic definition changes, create a new versioned contract and new interpretation layer.

## 12. No paid-review authorization

This contract defines review semantics only. It authorizes no paid evaluator or provider call.
