# R6 Structural Support, Trace and Control-Surface Identification Protocol v1.0

Date: 2026-09-18  
Status: FORWARD v5 / CENTRAL IDENTIFICATION LAYER / NO SCIENTIFIC RUN AUTHORIZATION

## 1. Purpose

R6 identifies where persistence is structurally supported and where a system should detect, trace and potentially intervene.

System Inertia remains an important downstream property, but R6 is no longer defined only as an inertia score or target-specific contrast.

## 2. Required map

Where evidence permits, R6 constructs:

\`source -> transformations -> structural support -> stable pool -> exposure -> descendants\`

and records:

- \`detection_surface_ref\`;
- \`trace_root_ref\`;
- \`structural_support_refs\`;
- \`pool_entry_refs\`;
- \`exposure_anchor_refs\`;
- \`evidence_supported_affected_closure\`;
- \`candidate_intervention_surface_refs\`.

## 3. Upstream tracing

Tracing should prefer machine-recorded provenance/lineage before semantic reconstruction.

Semantic audit is applied to the bounded ancestry needed to interpret the trace.

## 4. Downstream tracing

R6 distinguishes:

- potential structural descendants;
- evidence-supported semantic/decision dependence;
- mechanically required replay dependencies.

Reachability alone does not define affectedness.

## 5. Control-surface candidates

Possible intervention surfaces:

- source;
- early transformation;
- Structural Support point;
- Stable Shared Pool entry;
- derived constraint/action;
- bounded repair closure.

No surface is assumed optimal.

## 6. Cost tradeoff

R6 may compare:

- detection cost;
- semantic-audit cost;
- propagation cost;
- repair cost;
- audit/reconstruction risk.

The earliest source is not assumed to be the best detection point.

## 7. Historical modules

The following remain usable as optional modules:

- natural variability baseline;
- carrier/inheritance evidence;
- post-consumption inertia transition;
- target-specific contrasts.

They are not mandatory geometry for every new Whole-Process Run.

## 8. Handoff to R7

R6 should hand R7 an explicit:

- selected intervention surface;
- EvidenceSupportedAffectedClosure;
- RepairClosure candidate;
- preserved structure set;
- authority/provenance condition;
- unresolved semantic risks.

## 9. Authorization

No provider/evaluator/recovery action is authorized.
