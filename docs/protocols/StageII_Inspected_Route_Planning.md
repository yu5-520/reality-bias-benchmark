# Inspected-source route proposal compilation

The read-only `RoutePlanningSession` supplies a complete observed-node catalog, node context, current/historical files, exact native observation sources and the current host answer. It has no provider, shell, native write or automatic repair invocation. The catalog retains all available nodes and the original task; selecting a route does not truncate the accessible graph. Frozen semantic-audit verdicts are not supplied. The current interface accepts offline manual/scripted proposals; live origin is blocked.

Each successful source read receives a host-retained ID and exact source locator/hash. A witness selects a nonempty character span in the returned text and retains the exact quote. For observation sources the span is over the source text produced by the native locator extraction, including its line/JSON pointer, rather than an arbitrary whole-archive quote. Failed reads are not successful-source entries; this interface does not implement a frozen query budget. Witness IDs and internal ledgers are owned by the host API, not accepted from an agent-provided replacement ledger.

`compile()` consumes a `stage2-complete-route-proposal-v1` object and separately retained host policies. Required fields are:

| Part | Fields / mechanical checks |
| --- | --- |
| Source binding | Original task, graph/archive hashes, exact terminal parent |
| Selected route | Inspected node refs, disjoint modify/preserve/verify sets covering the selected route |
| Diagnosis | Claim ID, source/destination refs, before/after meaning, claimed authority effect, limitation, exact inspected witness IDs for both endpoints |
| Uncertainty | Unknown relations retained; adoption marked unknown/not established |
| Native actions | Action IDs, target fields/ranges, values, dependencies, diagnosis IDs; existing field compiler checks separately retained application policy |
| Verification | Proposed host-defined offline checks, refs, dependencies and postconditions; no shell operation or completion receipt accepted |
| Current host answer | Only `state:terminal /answer`, exact separately retained value/dependencies; policy regenerated against frozen source before accepting |
| Coordination | Application actions → proposed checks → current-answer action; unique step IDs and explicit order |

Descriptions remain claims. Source quotes establish literal source identity, not correctness of semantic interpretation, causal dependence or authority adoption. The compiler refuses a proposal's self-declared verified semantics/adoption and prevents an `UNKNOWN` claim from justifying a mutation. `CANDIDATE` and `SOURCE_BOUND_CLAIM` still require separately retained field policies; these status strings do not establish semantic correctness or grant authority. A proposal cannot widen policy by editing/resealing it. Policy hashes provide integrity, not cryptographic signatures.

The output seals the proposal, inspected witnesses, successful query log, compiled application plan and current-answer policy. It explicitly records zero executed native actions, unexecuted verification tasks, unadjudicated diagnosis, no agent-generated repair and no live readiness. The compiler does not return a false completion receipt or automatically hand a proposal to the old revision harness.

Current limitations: coordination accepts application actions followed by host-defined verification and an optional current-answer supersession. It does not support arbitrary action interleaving, private-state/message mutation, live model planning, native continuation, historical pressure-point resumption or concurrent isolation. Planned verification descriptions are not executable checks; the trusted native coordinator must implement and execute them separately. Preservation of unrelated semantic progression is not inferred from retained file/host fields.

## Offline evidence

`scripts/check_stage2_route_planning_session.py` constructs an explicitly manual proposal from the already sealed source-based engineering branch. It uses no audit verdict or model, and performs no native action. All 1,194 frozen graph nodes remain available; the selected route has seven nodes, nine exact source witnesses and 27 successful API queries. The output compiles one application action and current `/answer` policy without executing either. These numbers describe an interface check, not autonomous diagnosis or repair quality.

Dataset: `stage2/replication_v2/route_planning_session_integration_v1/`. The sealed bundle/catalog/receipt, implementation hashes and referenced manual policy inputs are compared exactly by independent fresh reproduction. Eleven tests cover unread/fabricated witnesses, missing endpoint evidence, verified-claim rejection, unknown-claim action rejection, task/parent drift, route-role conflicts, field overreach, verification ordering/operation boundaries and native observation-object binding. Total route tests: 67.

This closes the mechanical proposal-interface gap. Agent-generated plans, independent semantic evaluation, monitored native continuation and a fair frozen comparison remain required before a live experiment.
