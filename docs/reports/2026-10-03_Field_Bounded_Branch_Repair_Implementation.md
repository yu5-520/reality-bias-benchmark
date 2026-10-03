# Field-bounded branch repair implementation

The application repair path now uses a separately held field policy, coordinated operation plan and native application branch executor. A complete enhanced graph remains available. This replaces the old local revision strategy for the new offline integration path; the historical harness stays disabled and its 21 calls remain immutable diagnostic records.

## Implemented and checked

- Exact source/archive/checkpoint/task bindings and separate branch identity.
- JSON scalar leaf and exact text span operations; multiple ordered fields in one object and multiple objects in one plan.
- Before-version and expected-output checks, explicit dependencies and preservation of nonselected application objects.
- Rejection of policy widening, out-of-scope fields, unsupported/private native surfaces, stale data, unknown mutation refs and bypass-style whole-file actions.
- Native `HostCheckout.write_file` execution in a new branch, recorded intents/receipts and partial-failure retention.
- Read-only enhanced observation before/during/after application actions and complete before/after graph artifacts; original node identities, observations, relations and archives remain intact.

No private product code was added. No original framework was modified. The source implementation used for the frozen P2 replay remains byte-identical; graph append support is an independently added extension.

## Frozen MCP mechanical integration

| Measure | Result |
| --- | --- |
| Original observed graph nodes | 1,194 |
| Post-integration graph nodes | 1,222 |
| Original observations preserved exactly | 3,343 |
| Original edges preserved exactly | 6,514 |
| New before/during/after application observations | 28 |
| Native fixture write operations | 2 |
| Unrelated application files and source archive | Preserved |
| New model/provider calls | 0 |
| Native agent continuation | Not executed |
| Semantic repair effect | Not evaluated |

The two deliberately marked changes test JSON leaf and text-span execution on captured application content. They are not a diagnosis, CPR intervention result or evidence that actual process semantics were repaired. The operation order is an executor dependency, not an inferred semantic relationship.

45 route-repair tests and 12 enhanced-monitor tests passed locally. They cover successful coordinated actions, multi-field version ordering, out-of-policy rejection, whole-object rejection, policy tampering, duplicate JSON ambiguity, exact span preservation, source drift, version/preserve conflicts and retention of a failed native output. Sealed graphs and all 28 source captures verify; the independent workflow reproduces the integration receipt and graph contents.

## Remaining scientific and engineering scope

The available hard constraint covers experiment-owned application state. It does not guarantee a model's reasoning, enforce arbitrary semantic authority inside a foreign store, acquire concurrent locks or repair a native message/plan surface that has no verified forward-write operation. A repaired field can affect other semantic routes through legitimate shared dependencies; mechanical preservation is not a proof of semantic noninterference.

Evidence-grounded branch diagnosis, operational authority assessment, native process-state/message bindings, continued agent monitoring, branch promotion and fair live evaluation remain pending. Readiness is reported per capability in `configs/stage2_node_route_repair_design_v1.json`; live execution remains disabled.

Protocol: `docs/protocols/StageII_Field_Bounded_Branch_Repair.md`.

Evidence: `stage2/replication_v2/field_branch_native_integration_v1/`.
