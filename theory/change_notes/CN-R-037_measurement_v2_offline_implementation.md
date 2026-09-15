# CN-R-037 — Measurement v2 Offline Implementation

Date: 2026-09-15  
Status: IMPLEMENTED / OFFLINE VALIDATION

## Decision

Implement the first executable Measurement v2 layer over frozen Formal Batch001 evidence without changing the subject Arena and without calling any paid model.

The implementation adds:

- deterministic R2 structural candidate indexing;
- R3 lineage-window construction from recorded structural relations;
- R4 dynamics windows mapped from the semantic-blind feedback counter;
- target-local Reviewer v2 packet generation;
- unit tests and a repository offline validation workflow.

## Machine/reviewer boundary refinement

The implementation is intentionally more conservative than a literal reading of the first v2 planning draft.

A deterministic machine may identify:

- high-certainty state writes;
- explicit same-key status transitions;
- post-settlement state writes and certainty promotions;
- invocation expansion, repeat invocation and pending-duplicate structure;
- final revision/reopen structure;
- recorded goal/priority changes only when those fields explicitly exist;
- message/state/final-version lineage;
- neutral structural feedback intervals and resource proxies.

The deterministic layer does **not** identify retrospective legitimation itself. In particular, it does not emit a machine `LEGITIMACY_REWRITE_CANDIDATE`; laundering and normalization require semantic inspection of Agent input/output language.

This preserves the rule:

> machine finds structure; reviewer decides whether the structure actually implements C/P/R.

## Formal Batch001 replay

Source evidence batch:

`94c6e884fc3b0122e67d613f9bf956a5fab2ad52a6c49b7ada8dfc5dde9c4ed9`

Deterministic output hash:

`9a2b966849f8b18fa553b2b425ff9723fe0d66c2b58e88260e29ad43e6f767f6`

Observed offline output:

- R2 candidate records: 70
- realized structural effects: 68
- non-realized Authority attempts: 2
- R3 lineage windows: 70
- R4 neutral dynamics windows: 4
- Reviewer v2 target-local packets: 70
- paid API calls: 0

These are structural counts and must not be reported as C/P/R event counts.

## Review-packet rule

Reviewer v2 packets exclude `same_response_actions` and use a single target. They do not contain Reviewer A/B outputs, expected C/P/R→Authority mappings, prior agreement statistics, disagreement-selection status or paper claims.

The semantic review stage asks neutral boundary questions about epistemic status, goal relation/focus and retrospective outcome. C/P/R mechanism synthesis occurs only after those fields are frozen.

## Historical preservation

- Reviewer A/B v1 remain unchanged.
- Formal Batch001 subject traces remain unchanged.
- Existing structural feedback counter remains semantic-blind.
- No subject rerun is authorized by this Change Note.
- No paid Reviewer v2 call is authorized by this Change Note.

## Next gate

Repository CI must reproduce the frozen Batch001 output hash, pass unit tests, pass target-local packet checks, and pass prior-review/expected-mapping leakage checks before a new independent semantic review can be considered.
