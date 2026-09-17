# R5-R6 Jump-Specificity Inertia Test Protocol v0.1

Date: 2026-09-17  
Status: FORWARD / OFFLINE-CONTRACT-ONLY / NO REAL PROVIDER RUN AUTHORIZED  
Depends on: `docs/R_Plan_v4.4.md`, `theory/theory_contract_v0.8.md`, `docs/system_behavior_measurement_plan_v4.4.md`, `docs/R6_inertia_transition_protocol_v0.2.md`.

## 1. Purpose

This protocol tests whether the downstream inertia response observed after a one-shot factual-authority withdrawal is specific to the selected natural J0 rather than a generic consequence of making any comparable factual field uncertain.

It does not replace the formal historical R5-MID A/B experiment. It defines a new prospective specificity family.

## 2. Scientific hypothesis family

### H-local

A one-shot factual-status downgrade can cause an immediate/local behavioral response.

### H-inertia

When the downgrade targets J0, the post-consumption downstream inertia profile can differ from natural continuation.

### H-specificity

The J0-targeted post-consumption inertia profile is distinguishable from the profile induced by the same downgrade applied to a preregistered matched non-J0 factual field.

The protocol does not assume that S2 must be larger, more complex or more divergent than S1.

## 3. Namespace

Use only the `S` namespace for this protocol:

- `S0_NATURAL_REFERENCE`
- `S1_MATCHED_FACTUAL_FIELD_DOWNGRADE`
- `S2_J0_TARGETED_AUTHORITY_WITHDRAWAL`

Do not alias these conditions to R7 `C1/C2/C3`.

## 4. Common frozen identity

As far as the runtime permits, each matched specificity set must hold fixed:

- natural source trajectory;
- selected J0 and common reference parent;
- task goal;
- Agent role/responsibility pool;
- provider/model configuration;
- Arena configuration;
- passive observability schema;
- continuation horizon or explicit censoring rule;
- one-shot delivery policy for S1/S2;
- one-shot `to_status` value;
- maximum direct experiment-origin exposure count;
- no-reinjection rule;
- no-persistent-mutation rule;
- structural measurement version.

Provider hidden state is not claimed replayed.

## 5. S0 — Natural Reference

S0 begins from the frozen matched reference state and receives no new experiment-origin status downgrade.

Required evidence:

- `experiment_origin_exposure_count = 0`;
- no specificity intervention envelope;
- parent/start-state identity;
- matched observation horizon/censoring rule;
- complete passive structural evidence.

Scientific role: natural inertia reference.

## 6. S1 — Matched Factual-Field Status Downgrade

S1 applies the same mechanical one-shot downgrade used in S2 to a preregistered matched factual field that is not the selected J0 target.

Required properties:

- target belongs to frozen eligible pool;
- target selected outcome-blind under frozen rule;
- pre-status matches the allowed factual-status class;
- same `to_status` as S2;
- same delivery policy as S2;
- exactly one experiment-origin exposure;
- envelope consumed after delivery;
- zero experiment-origin reinjection;
- no persistent Arena-state mutation;
- no opposite factual claim;
- no replacement answer;
- no target terminal answer;
- free downstream continuation after consumption.

Scientific role: estimate generic epistemic uncertainty response.

## 7. S2 — J0-Targeted Authority Withdrawal

S2 applies the same mechanical one-shot downgrade to the selected natural J0 field.

Required properties are identical to S1 except for the frozen target identity.

Scientific role: estimate the J0-targeted response.

## 8. Treatment equivalence requirement

S1 and S2 must match on intervention mechanics. Their intended experimental difference is target identity, not treatment richness.

Freeze and compare:

- operator schema/version;
- `from_status` class;
- `to_status`;
- delivery policy;
- direct exposure limit;
- temporal scope;
- reinjection policy;
- persistent mutation flag;
- experiment-origin provenance;
- prompt-visible delta form;
- observation horizon.

If a target cannot receive a materially equivalent transform, it is not an eligible S1 match.

## 9. Matched-field selection contract

S1 target selection must be completed before the S-arm outcomes exist.

The selection record must contain:

- source trace hash;
- parent state hash;
- J0 event/candidate refs;
- eligible-pool schema/version;
- pool hash;
- each candidate field's evidence refs;
- each candidate field's status, visibility, timing, state/interface family and actor accessibility;
- matching feature vector;
- deterministic/randomized selection rule;
- selected field;
- selected-field hash;
- exclusions and reasons;
- explicit statement that downstream S outcomes were unavailable at selection time.

## 10. Primary contrasts

### Generic uncertainty response

`S1 - S0`

Question: what structural response is induced by the same one-shot downgrade on a matched non-J0 factual field?

### Total J0-targeted response

`S2 - S0`

Question: what structural response follows one-shot factual-authority withdrawal at J0?

### Target-specificity contrast

`S2 - S1`

Primary question:

> Is the post-consumption inertia response to J0 distinguishable from the response to a matched factual-field downgrade under the same intervention mechanics?

## 11. Primary readout level

The primary specificity endpoint is R6 **post-consumption inertia**, not immediate local activity.

Report separately:

1. local perturbation response;
2. post-consumption inertia profile;
3. target-specificity contrast.

## 12. R6 dimensions reused

Use the same structural dimensions in all S arms:

- descendant Jump structure and distance;
- family continuation/transformation;
- direct/indirect inheritance;
- field/actor transfer;
- root reach/depth;
- branch/merge/re-entry;
- cross-Agent spread;
- path-family structure;
- state-lineage destination;
- delayed re-emergence;
- retrospective return/rebound;
- post-return inheritance;
- reconstruction/replacement;
- reconvergence;
- censoring.

No new single-number `inertia score` is required.

## 13. Interpretation matrix

Possible observations must be reported without forcing a monotonic direction:

- S1 and S2 both reorganize similarly: generic uncertainty explanation remains viable.
- S2 reorganizes while S1 is locally responsive but inertia-similar to S0: supports target specificity under the matched design.
- S1 reorganizes more than S2: weakens a simple J0-specificity interpretation and requires structural explanation.
- S1/S2 reorganize in different non-monotonic directions: may still support target specificity if the inertia profiles are structurally distinguishable under frozen comparison rules.
- neither differs from S0 beyond matched natural variability: weakens the perturbation/inertia hypothesis for that design.
- censoring prevents comparison: result is unresolved, not negative.

## 14. Claim boundaries

A positive specificity result may support:

> under the frozen matched intervention, the selected J0's acquired factual authority is implicated in downstream process inertia in a way distinguishable from the generic response to a matched factual-status downgrade.

It does not by itself establish:

- universal causality;
- semantic CPR truth;
- stable directional treatment effect;
- cross-model/domain generality;
- provider hidden-state replay;
- permanent downstream elimination or recovery.

## 15. Freeze-before-run requirement

A future real specificity run requires a new immutable execution freeze binding:

- exact source evidence and parent/J0;
- S0/S1/S2 definitions;
- S1 eligible pool and selection record;
- operator version/hash;
- target hashes;
- model/provider and Arena config hashes;
- observation horizon/censoring;
- structural measurement contract;
- replicate count/order policy;
- spending ceiling;
- explicit paid authorization.

No old R5 or R7 authorization may be reused.

## 16. Evidence-first order

```text
prepare/freeze protocol
  -> run subjects if explicitly authorized
  -> freeze raw evidence
  -> integrity validation
  -> derive local response
  -> derive R6 inertia profiles
  -> derive S contrasts
  -> only later perform R8 semantic review
```

Evaluation failure must never cause automatic subject rerun.

## 17. Historical boundary

Formal R5-MID A1/B1/A2/B2 remain historical A/B identities and are not retroactively converted into S0/S2.

Existing R7 C conditions remain unchanged.

## 18. Authorization

This protocol authorizes no provider or evaluator call.
