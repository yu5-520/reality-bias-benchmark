# R5-R6 Jump-Specificity Inertia Test Protocol v0.2

Status: **FORWARD EXACT-SOURCE PROTOCOL / NO SUBJECT RUN AUTHORIZATION**  
Predecessor: `R5-R6 Jump-Specificity Inertia Test Protocol v0.1`

## 1. Scientific purpose

The falsification question is not whether changing one information status can alter immediate Agent behavior. Any newly uncertain item may induce additional checking, messaging, writing or rerouting.

The discriminating question is:

> **After the direct one-shot uncertainty annotation has been consumed, is the downstream system-inertia response to the J0-derived escape information structurally distinguishable from the response to the same annotation applied to an ordinary factual information item?**

The primary object is therefore the **R6 post-consumption inertia profile**, not first-turn activity volume.

## 2. Candidate null interpretations

### H0-local

J0 is only a local information event. Its acquired factual authority is not structurally embedded in downstream process generation.

### H0-generic-uncertainty

Any comparable one-shot factual-status downgrade produces the same downstream inertia response, so an observed J0 intervention effect need not be specific to the suspected escape-derived information.

The specificity design targets the second alternative after R5/R6 have already made the first alternative empirically questionable.

## 3. Exact-source discovery

The frozen R5-MID parent at `after_turn:8` contains only one non-initial top-level `shared_state_metadata` entry with status `fact`:

`inventory_stockout_assessment_v1`

Therefore v0.1 cannot honestly construct S1 by selecting a second top-level non-J0 fact-status state key from that exact parent.

The protocol must not solve this by:

- relabeling a `recommendation` or `provisional` container as a fact;
- selecting a field because it is expected to have little effect;
- changing S1 after seeing S-arm outcomes;
- silently changing historical R5-MID evidence.

v0.2 moves the prospective specificity unit to an **atomic prompt-visible factual information item**.

## 4. The escape-derived S2 target

The frozen task emits a late inventory event:

`Product A stock = 1,520`

with evidence status:

`preliminary_unreconciled`

At E32 / T8, Inventory writes `inventory_stockout_assessment_v1` with container status:

`fact`

The atomic S2 target is:

`shared_state.inventory_stockout_assessment_v1.A.preliminary_stock = 1520`

The mechanism under study is not that the value `1520` is necessarily false. The observable authority transition is that a signal originating as preliminary/unreconciled later sits inside a state object that has acquired factual authority.

S2 therefore withdraws only the acquired factual authority of this exact signal:

`fact -> unconfirmed`

without replacing the value.

## 5. The ordinary-fact S1 target

The first S1 control uses an outcome-blind deterministic selection from ordinary source-backed scalar facts already visible to the resumed Operations Lead.

Frozen pool rule:

`PUBLIC_CONTEXT_PRODUCT_SCALAR_NON_INVENTORY_FAMILY_v1`

Eligible fields are product:

- price;
- gross margin percentage;
- ad ROAS.

Direct stock/daily-unit fields are excluded from the first pool so that the generic-uncertainty control does not become a second inventory/stockout-family perturbation.

The pool and selector were frozen before scientific S-arm outputs existed.

Selected S1 target:

`public_context.products.C.gross_margin_pct = 35`

A later same-family robustness control may be added append-only. It may not replace this first S1 after observing outcomes.

## 6. Conditions

### S0 — Natural Reference

No experiment-origin epistemic annotation is added.

Purpose: estimate natural continuation/inertia under the same frozen J0-bearing context.

### S1 — Ordinary Atomic Fact Downgrade

Apply the common one-shot annotation to:

`public_context.products.C.gross_margin_pct`

The numerical value remains `35`.

### S2 — J0 Escape-Derived Atomic Fact Downgrade

Apply the same one-shot annotation to:

`shared_state.inventory_stockout_assessment_v1.A.preliminary_stock`

The numerical value remains `1520`.

## 7. Common intervention primitive

S1 and S2 use the same prospective mechanical primitive:

`ONE_SHOT_TARGET_SCOPED_EPISTEMIC_STATUS_ANNOTATION`

The only prompt-visible addition is a minimal annotation:

```json
{
  "target_locator": "<frozen target locator>",
  "epistemic_status": "unconfirmed"
}
```

The original information remains in its original location and retains its original value/content.

Required invariants:

- `from_status = fact`;
- `to_status = unconfirmed`;
- one direct experiment-origin exposure;
- no persistent Arena-state mutation;
- zero experiment-origin reinjection after consumption;
- no opposite factual claim;
- no replacement factual value;
- no replacement conclusion;
- no desired terminal answer;
- no Agent identity/prompt-role modification;
- no topology/path instruction;
- free downstream continuation after consumption.

The prompt-visible annotation schema is identical across S1/S2 except for the target locator.

## 8. Historical R5 boundary

The original formal R5-MID intervention changed:

`shared_state_metadata.inventory_stockout_assessment_v1.status: fact -> unconfirmed`

v0.2 does **not** claim to replay that exact historical operator.

Instead, v0.2 is a prospective **atomic target-specificity follow-up** designed after exact-source audit showed that the original top-level-state-key control interface had no honest second factual target.

Historical R5-MID A/B evidence remains immutable and retains its original labels.

## 9. Observation hierarchy

The analysis must preserve three distinct layers:

1. **Local perturbation response** — immediate extra checking, writing, messaging or rerouting;
2. **Post-consumption R6 inertia** — downstream continuation, extinction, transfer, transformation, re-entry, branch/merge structure, cross-Agent spread, path-family structure, delayed return/reconstruction and reconvergence after the direct annotation is gone;
3. **Terminal outcome** — reported separately and never used to define process reality.

A local response is not sufficient evidence of target specificity.

## 10. Contrasts

### Generic uncertainty

`S1 - S0`

Estimates the structural response to making one ordinary fact uncertain once.

### Total J0-targeted response

`S2 - S0`

Estimates the total response associated with withdrawing factual authority from the J0-derived atomic information.

### Primary target-specificity contrast

`S2 - S1`

Asks whether the J0-derived target produces a post-consumption inertia profile structurally distinguishable from generic one-shot factual uncertainty under matched mechanics.

## 11. R6 measurement object

No single unvalidated scalar is required.

The preregistered profile may include:

- descendant Jump continuation/count/distance;
- direct or indirect inheritance;
- target/field/actor transfer;
- root reach and depth;
- affected-Agent structure;
- branch / merge / re-entry;
- cross-Agent relations;
- path-family structure;
- state-lineage destination;
- delayed re-emergence;
- retrospective return/rebound where source-backed;
- replacement/reconstruction/hybridization;
- reconvergence;
- censoring/natural termination.

## 12. Interpretation matrix

### S1 and S2 inertia profiles are similar

The generic-uncertainty explanation remains viable for this design.

### S2 is structurally distinguishable from S1

Supports target-specificity under the frozen atomic intervention and selection rules.

This does not by itself semantically adjudicate CPR or establish a universal causal law.

### S1 is stronger than S2

Weakens a simple J0-specificity interpretation and must be retained as a real result.

### S1/S2 differ in non-monotonic directions

Target specificity may still be supported if the preregistered multidimensional inertia profiles are structurally distinguishable. No monotonic complexity direction is required.

### Natural termination prevents sufficient downstream observation

Classify as censored/unresolved, not as zero inertia.

## 13. Independence and replication boundary

Repeated continuations from the same frozen parent are matched repeated realizations, not independent population samples.

Provider hidden state is not replayed.

Future replication across independent parents, models and domains belongs to later robustness layers/R9.

## 14. Evidence binding

Forward exact-source artifacts:

- `docs/R5_R6_specificity_source_audit_2026-09-17.md`
- `configs/r5r6_specificity_field_selection_contract_v0.2.json`
- `configs/r5r6_specificity_exact_source_binding_v0.2.json`
- `manifests/r5r6_specificity_source_slice_2026-09-17_v0_2.json`
- `manifests/r5r6_specificity_s1_selection_2026-09-17_v0_2.json`
- `arena/r5r6_specificity_atomic_v0_2.py`
- `arena/r5r6_specificity_atomic_preflight_v0_2.py`

## 15. Authorization boundary

This protocol authorizes only offline implementation, target-binding validation, deterministic preflight, testing and readiness audit.

It does not authorize:

- scientific S0/S1/S2 provider calls;
- paid evaluator calls;
- semantic CPR adjudication;
- mutation of historical frozen evidence.
