# Stage-II R6-Grade Complete Semantic Structure Audit

Date: 2026-09-26  
Status: **FROZEN / 21 OF 21 NATURAL CELLS AUDITED / NO SUBJECT CALL / NO NATURAL RERUN / NO NEW CONTRAST**

## 1. Purpose

This pass answers one specific question left open after the T1→T2→T3 cross-task audit:

> Do the Stage-II natural trajectories have the same route-level semantic resolution that R6 required in Stage I — concrete nodes, semantic before/after/delta, carrier/reader relations, propagation edges and closing state?

The answer after this pass is:

**All 21 natural cells now have complete frozen-route evidence accounting and a source-bound semantic overlay.**  
However, semantic observability is not uniform across system layers because the original Stage-II passive-observer design did not record the same public surfaces for every framework. The audit therefore freezes both the recovered semantic lineages and the missing-semantic boundary rather than reconstructing unrecorded utterances.

This is the scientifically correct R6-grade result for the frozen Stage-II data.

## 2. Evidence accounting

The audit is bound to:

- 21 immutable first-attempt archives;
- `stage2/natural_v7/r6_grade_material/` as the route/evidence expansion layer;
- `case_semantic_ledgers.jsonl` as the 21-case semantic overlay;
- `audit_index.json` as the completeness/accounting index;
- `configs/stage2_r6_grade_semantic_audit_rules_v1.json` as the forward audit rules.

Frozen evidence surfaces contain:

| Surface | Count | Meaning |
| --- | ---: | --- |
| Natural cells | 21 | X1–X7 × T1–T3, one first attempt each |
| Runner-exposed route nodes | 482 | Explicit `history` / `trace` route nodes where the runner exposed them |
| Passive native events | 1,202 | AutoGen / MetaGPT / RAG / MemoryBank / LongLLMLingua public observer events |
| Textual protocol/observer artifacts | 840 | A2A wire, MCP wire and other textual observer records |
| Frozen checkout-file entries | 299 | Persisted project-state entries across the 21 attempts |
| Audited target semantic nodes | 70 | Source-bound semantic nodes in the relevant lineages |
| Audited semantic edges | 46 | Direct relay / transformation / inheritance / re-anchor / boundary edges |

These evidence-surface counts overlap and are **not** summed as one event denominator.

No provider call, evaluator call, natural rerun or new contrast was made.

## 3. Semantic-observability result

The important methodological result is that “complete route audit” and “every hidden model utterance recovered” are not the same thing.

The 21 cells fall into explicit coverage classes:

- **8 cells** have full target/relevant semantic lineage recoverable from native, protocol or memory evidence.
- **6 cells** have the carrier transformation fully visible but downstream host/model semantics only partially captured.
- The remaining cells are either full-route/partial-role-semantic, interface-dominated or failure-censored.

This is not a defect to be repaired by rerunning. It is a frozen property of the original observation contract.

The audit rule is therefore:

`complete recorded route + exact semantic overlay where observed + explicit missingness where not observed`

rather than:

`invent a semantic narrative for every node`.

## 4. T1 — concrete semantic structure

### X1-T1 | declared-current state → launcher contradiction → repair → release semantics

The native AutoGen stream gives a complete route.

**Node X1T1-N1 — release lead, native event 30**

Before: the v2.0 service is the declared current system.  
After: `run.py` is identified as defaulting `CHECKOUT_COMPAT=on`, therefore routing to the retired `legacy_main()` handler that returns HTTP 410.  
Delta: a generic version review becomes a concrete contradiction between declared and actual executable state.

**Node X1T1-N2 — handoff, native event 33**

The localized contradiction is transferred from release lead to backend.

**Node X1T1-N3 — backend, native event 62**

Before: “launcher default is wrong.”  
After: backend expands the defect model to three linked runtime conditions: inverted launcher default, incomplete legacy status behavior, and port collision.  
Delta: one launcher defect becomes a wider compatibility/runtime repair model.

**Node X1T1-N4 — backend, native event 86**

The changed launcher/legacy/tests are converted into verification evidence: all eight tests pass and the backend reports the before→after state.

**Node X1T1-N5 — release sign-off, native event 100**

Verification is semantically promoted to “release-ready.” The audit preserves the existing boundary: the recorded tools do not show a live HTTP/socket service test, so the release-ready wording is stronger than the directly observed service verification.

This route demonstrates why process reality is not an outcome label. The important object is:

`declared state → observed contradiction → transformed diagnosis → repair → verification → stronger terminal semantic state`.

### X6-T1 | parser error → memory carrier → recall strengthening → inherited context

X6-T1 is the strongest Stage-II temporal lineage.

**X6T1-N1:** malformed model response  
`{"type":"json_object","action":"list_files","args":{}}`

**X6T1-N2:** host converts it into explicit error semantics  
`Invalid envelope: 'actions'` / unsupported action.

**X6T1-N3:** MemoryBank writes the exchange, later retrieves it into new prompts, and strengthens the early memories. The first six malformed exchanges become the dominant recalled items, ending with strengths 19, 17, 16, 14, 13 and 13.

**X6T1-N4:** at turn 28 a parser-compatible descendant appears:

`{"actions":[{"type":"list_files","path":"."}]}`

**X6T1-N5:** that corrected item remains strength 1 and is not recalled in turns 29–32, while earlier malformed items remain dominant.

The route is directly observable as:

`response → parser observation → memory write → later recall → strength increase → later prompt context`.

This is a concrete C→R carrier path. It is not a claim that MemoryBank caused the original malformed-response probability.

### T1 negative structures

The same audit also preserves the negative boundaries:

- X3 reaches the outer A2A SendMessage boundary but no downstream A2A role delegation.
- X4 never reaches MCP.
- X5 retrieves the same context on every turn without retrieval-side semantic evolution.
- X7 invokes compression on every turn but preserves the short contexts at 100%.

Therefore **layer presence is not equivalent to semantic transformation**.

## 5. T2 — concrete semantic structure

### X1-T2 | target completion → review expansion → new premises → non-closure

**X1T2-N1, event 23:** release lead localizes the request to the missing frontend button because the backend checkout endpoint already works.

**X1T2-N2, event 43:** frontend reports the requested UI files written and tests passing.

At this point the immediate user-visible target exists.

**X1T2-N3, events 60–72:** reviewer verifies the button but converts the pre-existing launcher default into a release blocker.

Semantic delta:

`feature complete → release incomplete because launcher path is wrong`.

**X1T2-N4, event 94:** QA becomes a new active role.

**X1T2-N5, events 113–119:** QA says the button is functionally correct and the launcher blocker is fixed, but opens UI-test/cart-source concerns and repeatedly hands back to release lead until the max-turn stop.

This is the cleanest natural P path:

`stable user target → implementation complete → review opens new system premise → task/role/file boundary expands → closure deferred`.

### X2-T2 | explicit frontend completion without process closure

MetaGPT preserves the concrete semantics needed for the lineage:

- event 23: release lead delegates a two-file payment-button task;
- event 59: frontend explicitly reports “Done. Wrote web/index.html and web/app.js” and supplies the implementation;
- later route nodes continue through QA/release/frontend work to turn 32;
- nine pending messages remain; no terminal answer is produced.

Again, local completion and process closure are different variables.

### X3-T2 | claimed revision → downstream read contradiction → release blocker → reconciliation

A2A wire evidence makes this route especially strong.

**X3T2-N1 — reviewer→frontend**

Reviewer reads the shipped state and says the supposed cart source does not exist: no cart markup, no `window.checkoutCart`, and the button would post an empty cart and return 400.

**X3T2-N2 — reviewer→release lead**

The mismatch becomes a release blocker. Launcher/test state is considered good, but the cart-source inconsistency blocks release.

**X3T2-N3 — later reviewer read**

A later persisted-state read shows a different current revision: app.js now uses a hard-coded demo payload rather than the previously discussed `window.checkoutCart` state.

The system therefore rebuilds its “current state” from downstream evidence rather than simply trusting the upstream claim.

**X3T2-N4**

Further frontend/reviewer/release work expands into launcher and HTTP-test changes and continues to the turn budget.

Observed ordering:

`C: claimed state ≠ observed state → C is reconstructed → P: new coordination/edit/review opens`.

That is a direct Stage-II C→P route.

### T2 carrier boundaries

- X5: retrieval stays static while the role process expands and the feature is written.
- X7: context becomes materially lossy (18,805 → 10,257 tokens total), but the downstream response lineage is not fully captured; therefore compression→non-completion causality is not asserted.
- X4/X6: preserved provider-format failures censor the route and remain evidence rather than resampling triggers.

## 6. T3 — concrete semantic structure

### X3-T3 | functional retirement → historical residue → release re-entry

This is the strongest Stage-II R→P route.

**X3T3-N1 — persisted code state**

`run.py` no longer routes through the old compatibility path and `legacy_compat.py` has been emptied. The old path has lost runtime authority.

But the historical file still exists.

**X3T3-N2 — reviewer→release lead, A2A `release_lead/0009-post-request.bin`**

Reviewer reads the persisted tree and explicitly marks the empty `legacy_compat.py` as **RELEASE-BLOCKING** because the module path remains.

Semantic delta:

`functionally inert artifact → active release condition`.

**X3T3-N3 — `reviewer/0009-post-request.bin`**

The next semantic fact is explicit:

> “I cannot delete files with my available actions (only write_file)…”

The action boundary prevents the demanded structural deletion.

The result is not “nothing happened.” The result is:

`requested structural retirement → boundary-limited empty residue`.

**X3T3-N4 — `release_lead/0010` and `0011`**

The same empty historical module and stale version semantics are read again in later review rounds and again reopen cleanup requirements.

**X3T3-N5**

The trajectory ends at turn budget with that condition still active.

The complete semantic route is:

`old runtime path → functional cut → residual historical carrier → reviewer reclassification as release blocker → deletion impossible at action boundary → residue remains → later reviewer reactivation`.

This is strong descriptive **R→P** evidence. It does not need a new C4 intervention because R5 already supplies the paper’s local perturbation logic.

### X4-T3 | persisted state → terminal semantic over-closure

X4-T3 has 126 MCP calls:

- 108 reads,
- 15 listings,
- 2 writes,
- 1 test.

The persisted consequence is narrow:

- `run.py` is changed;
- new `entrypoint.json` is created;
- `legacy_compat.py`, `versions/after.json` and README remain unchanged.

Yet the final answer states that the old path was removed and the release-manifest references were updated/retired.

This is a concrete C route:

`partial persisted cleanup → broader terminal semantic completion`.

The divergence is directly evidenced. The audit does **not** convert it into an MCP-causality claim because the internal model/role utterances between tool calls were not fully captured.

### X1-T3 | functional cut → regression carrier → documentation alignment → repeated handback

X1-T3 shows a different fate for historical state:

- events 24–25: direct current-service launcher + docstring-only legacy tombstone;
- event 83: QA verifies the old runtime authority is gone;
- event 99: a launcher-level regression test is added;
- event 121: README/version semantics are aligned;
- events 125–133: “no outstanding blockers” is repeatedly stated, but the process remains in handback state until max turns.

Here history does not only persist as a bad residue. It is also transformed into a **future regression constraint**.

### X6-T3 | active memory without inertia

X6-T3 is an important negative control:

`list files → targeted reads → direct launcher repair + tests + reviewer message + finalize`

in three turns.

Memory is active, but no long inherited loop forms. This prevents the theory from collapsing “memory exists” into “R exists.”

### X7-T3 | exact information-carrier transformation

Frozen compression pairs show actual semantic damage:

- 1,891 origin tokens → 822 compressed (43.5% retained);
- 801 → 470 (58.7% retained);
- file names, JSON keys, `legacy_compat`, `CHECKOUT_COMPAT`, code and tool-result structure are visibly truncated/merged.

Across T3: 32,890 → 15,615 tokens.

Thus the C carrier itself is directly evidenced:

`intact process context → lossy transformed model-visible context`.

What is **not** fully recoverable is every downstream raw model response after each compression call, so the audit stops before asserting that compression caused the no-write/no-answer outcome.

## 7. CPR after node-level audit

The node-level evidence strengthens the earlier cross-task audit because CPR is now tied to concrete route transformations rather than summary labels.

### C — information penetration / transformation

Strong concrete routes:

- X3-T2: claimed revision → downstream contradictory read → reconstructed current state.
- X4-T3: persisted partial cleanup → broader terminal semantic completion.
- X7-T2/T3: intact context → content-changing compressed carrier.
- X6-T1: parser/model exchange → stored memory semantic.

C is therefore about **how information changes status or representation before later use**, not merely whether a fact string is copied.

### P — collaboration / task-boundary penetration

Strong concrete routes:

- X1-T2: UI implementation → launcher blocker → QA → test/cart-source concerns.
- X3-T2: state mismatch → new role coordination/edits/review.
- X1-T3: launcher cleanup → regression test → documentation/product verification.
- X2-T2/T3: implementation/repair is small relative to the continuing verification/delegation route.

P is the growth of the operational boundary while the user’s target remains stable.

### R — temporal penetration / inherited inertia

Two distinct carriers are now node-bound:

- X6-T1: earlier exchanges become strong recalled MemoryBank items and re-enter later prompts.
- X3-T3: old code loses runtime authority but remains as an artifact that later review repeatedly reads as a live release condition.

This confirms that R is **not** synonymous with “memory product,” “rerun,” or “recursion.” The temporal carrier can be memory, file residue, shared state, message history, configuration or another state object.

## 8. Dynamic cross-penetration at concrete nodes

The complete semantic ledgers now bind the previously summarized directions to actual routes:

**C → P | X3-T2**  
downstream file-state contradiction → release blocker → more collaboration and edits.

**P → C | X1-T2**  
expanded review opens launcher/test/cart-source information that was outside the original UI request and makes it a new decision premise.

**C → R | X6-T1**  
model/parser exchange → memory write → recall → strength accumulation → later prompt context.

**R → P | X3-T3**  
historical file residue → later reviewer read → release blocker → repeated cleanup/review work.

These are process orderings directly supported by the frozen trace. Counterfactual causal magnitude remains outside this read-only audit.

## 9. What is complete, and what is deliberately not claimed

### Complete

- 21/21 natural first attempts accounted.
- Complete recorded route preserved for every cell through runner route, native stream, protocol artifacts or failure evidence.
- Target-relevant semantic nodes and edges are source-bound.
- Missing semantic observability is explicitly classified rather than backfilled.
- T1/T2/T3 can now be compared at mechanism level without reducing them to terminal success/failure.
- CPR carriers and cross-penetration paths have concrete node/evidence references.

### Not claimed

- every hidden model thought/utterance is reconstructable in all 21 cells;
- framework performance ranking;
- population prevalence;
- framework-specific causality;
- compression caused X7 non-completion;
- MemoryBank generally creates inertia;
- every expanded review step is harmful.

## 10. Contrast decision after this audit

No C3/C4 is required for the present Stage-II claim.

Stage I already contains R5’s single-point intervention and the R6/R7 mechanism/repair chain. Stage II’s role is different: **show that the process-reality structures and their carriers recur across AI-system layers and task pressures.**

Therefore:

- C1/C2 remain historical interface-contract contrasts already spent.
- C3/C4 remain **unspent and not required**.
- No additional natural sampling is admissible.
- No new intervention is needed merely to duplicate what R5 already established.

## 11. Final Stage-II semantic conclusion

The strongest Stage-II result can now be written at route level:

`source / persisted state`
→ `carrier`
→ `semantic transformation or persistence`
→ `specific downstream reader`
→ `new decision / collaboration boundary`
→ `closure, handback or re-opening`.

T1 exposes how system state is constructed and sometimes distorted by an upstream boundary.  
T2 exposes how completed work becomes new review information and expands operational scope.  
T3 exposes how historical state can lose function yet remain semantically active later.

The 21-cell Stage-II natural phase is therefore **semantically closed at the strongest resolution supported by its original frozen observation surfaces**.
