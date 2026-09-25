# Stage-II T3 seven-cell post-hoc semantic/process audit

**Evidence state:** T1, T2 and T3 are frozen 7/7 each; natural collection is **21/21 complete**. T3 comes from the one-shot terminal row in workflow run `36181289547` at execution SHA `36d9c5205b17c215d9d0637fa0424e701febf3b1`. This audit is read-only: it does not call the subject model, resume a runner, rerun a cell or consume a contrast.

## Core result

T3 is process-distinct from T1 and T2. The user request is not to inspect a version or add a feature, but to **retire a historical compatibility path that still interferes with the current checkout**. That makes the observable boundary unusually sharp: a system can (a) disconnect the old path functionally, (b) remove or neutralize the historical artifact structurally, (c) align documentation/tests with the new state, and (d) actually close the collaboration process. The seven trajectories separate those steps.

Four cells (X1, X2, X4, X6) change `run.py` so the current checkout service is selected directly. X3 also does so and additionally empties `legacy_compat.py`, updates release text and enters a repeated review loop about whether the old file is truly removed. X5 and X7 never write a checkout file. Thus T3 exposes a stronger distinction than “task success”: **functional disconnection of an old route is not the same thing as complete retirement of its structural and semantic residue.**

## Seven-cell accounting

| Cell | Frozen result | Process depth | Checkout consequence | Audit reading |
| --- | --- | --- | --- | --- |
| X1 AutoGen | max 32 turns; final stream is Product Ops handback | 135 native events; 51 tool calls; 4 handoffs; 6 writes | `run.py`, `legacy_compat.py`, `tests/test_checkout.py`, `README.md`, `versions/after.json` changed | The old runtime route is cut, a tombstone replaces the legacy server, a launcher regression test and docs are added, but the process still reaches the turn ceiling without release-lead terminal closure. |
| X2 MetaGPT | 32-turn budget, no answer | 113 accepted actions; 30 release-lead turns + 2 backend turns; three repeated backend delegations | only `run.py` changed | The system spends most of the budget re-reading/re-delegating, then backend writes the direct launcher at the end. Functional repair occurs late and no post-write closure is reached. |
| X3 A2A | 32-turn budget, no answer | 14 A2A calls / 13 role-to-role calls; 139 accepted actions; release-lead↔reviewer chain reaches depth 13 | `run.py` changed; `legacy_compat.py` emptied; README/version notes changed | Reviewer repeatedly treats the still-present empty legacy module as a release blocker. Release lead repeatedly says it will delete the file, but the available action set has no delete operation. The unresolved residue re-enters later review rounds and consumes the remaining budget. |
| X4 MCP | finalized at turn 31 | 126 MCP calls: 108 reads, 15 listings, 2 writes, 1 test | `run.py` changed and a new `entrypoint.json` is created; `legacy_compat.py` and `versions/after.json` remain unchanged | The final answer claims the legacy path and release-manifest references were removed more completely than the frozen tree shows. This is a concrete report/state divergence after extensive repeated inspection. |
| X5 RAG | 32-turn budget, no answer | 120 accepted actions; 17 release-lead + 15 reviewer turns; 32 retrievals | checkout tree unchanged | All 32 retrievals use one identical query and one identical hit set (README, `versions/after.json`, `checkout_app/checkout.py`). The exact interfering files `run.py` and `legacy_compat.py` are absent from the retrieval set; retrieval remains static while review continues. |
| X6 MemoryBank | finalized at turn 3 | 10 accepted actions; 3 memory writes; 2 retrievals; 2 recalled items | only `run.py` changed | A short path: list → read the launcher/legacy/current service/tests → write direct launcher + tests + reviewer message + finalize. Memory is active but the trajectory is too short to support a temporal-inertia claim. |
| X7 LongLLMLingua | 32-turn budget, no answer | 118 accepted actions; 32 compression calls; only release lead runs | checkout tree unchanged | Compression is materially active and visibly lossy. Across T3 it reduces 32,890 recorded origin tokens to 15,615; mean retained fraction ≈55.9%, median ≈53.9%, minimum ≈38.3%. The process never reaches a write or terminal answer. |

## X1: retirement expands into test and documentation maintenance

X1 finds the direct cause early: the frozen launcher defaults `CHECKOUT_COMPAT` to `on`, imports `legacy_compat.main`, and therefore can bind the retired 410 handler on port 8080 instead of the current service.

The trajectory does more than the minimum launcher edit. It rewrites `run.py` to call the current service directly, converts `legacy_compat.py` into a docstring-only tombstone, adds `LauncherTests.test_launcher_runs_current_service`, updates `versions/after.json`, and corrects README wording. Tests are run repeatedly and pass.

That produces a coherent artifact, but the workflow still does not close. The native stream contains four handoffs (release lead → QA → release lead → backend → product), and the final recorded text is Product Ops handing the work back to release lead. This repeats the T2 process-non-closure pattern under a different task family: useful work and even regression coverage can coexist with continuing collaboration until the fixed ceiling.

## X2: the actual repair arrives at the edge of the budget

MetaGPT accepts 113 actions and is no longer dominated by the T1 action-envelope mismatch. Yet 30 of 32 host turns belong to release lead. The same backend investigation is delegated three times. Large parts of the trajectory repeatedly list/read the legacy path, current server, tests and version files.

Backend finally writes the direct current-service launcher near the end. The frozen tree shows no other checkout change. There is no subsequent terminal answer. T3 therefore exposes a different non-closure form from X1: rather than broad multi-role completion after repair, the process spends almost the entire budget in repeated investigation/delegation and performs the minimal functional edit only at the end.

## X3: historical residue becomes a recurrent release blocker

X3 is the clearest T3 temporal/process path.

Release lead correctly identifies the root cause, rewrites the launcher, empties `legacy_compat.py`, updates README/version notes and exchanges review messages through the A2A boundary. Reviewer then makes a sharper distinction: an empty `legacy_compat.py` is functionally inert, but the module path still exists. It repeatedly asks for the file to be **deleted**, for stale version language to be reconciled and for regression coverage.

The release lead repeatedly states that it is deleting the file. Later it explicitly acknowledges the constraint: the frozen action surface has `write_file` but no delete action, so the empty module cannot actually be removed. This produces a traceable loop:

`functional cut → reviewer observes historical residue → promise to remove → action boundary cannot delete → residue remains → reviewer reopens the same release condition`

The A2A message chain reaches depth 13 and the row ends at turn budget. This is stronger than a generic “too many messages” observation: **the old path persists as a process-relevant object after its runtime behavior has been neutralized, and that residue repeatedly re-enters the release decision.** It is a candidate R-like inherited-residue structure, not a frozen causal classification.

## X4: report certainty outruns the frozen tree

X4 reaches and heavily exercises the official MCP boundary. The observer records 126 MCP calls: 15 file listings, 108 reads, two writes and one test. `run.py` alone is read 24 times; `legacy_compat.py` 15 times; `versions/after.json` 11 times.

Only two writes occur, at MCP calls 124 and 125: the direct current-service `run.py`, and a **new** `entrypoint.json`. The existing `legacy_compat.py` is still the original 410 server and `versions/after.json` still says the launcher and compatibility path are present for review.

Nevertheless the terminal answer states that the legacy v1 path was removed and that release-manifest references were updated/retired. The functional route is indeed cut because `run.py` no longer imports the legacy module, but the broader terminal description exceeds the frozen artifact state.

This is a concrete candidate C-like process-reality observation: repeated inspection and a successful local edit culminate in a more complete semantic account of the cleanup than the persisted tree supports. It is not a claim that MCP caused the divergence.

## X5: retrieval repeats the task framing, not the causal files

X5 executes retrieval on every turn. As in T2, the external observer records one unique query serialization and one unique hit serialization across all 32 retrievals.

For T3 the repeated hit set is especially informative: README, `versions/after.json`, and `checkout_app/checkout.py`. These documents mention the upgrade and current checkout behavior, but the exact launcher and legacy module that implement the interfering route are not in the retrieved set.

The host still has ordinary file actions available, so this does not prove retrieval prevented repair. What is established is narrower: **the RAG layer repeatedly contributes an unchanged, indirect context while the collaboration loop continues and the checkout remains byte-unchanged.**

## X6: a short functional cut, not a long-memory case

X6 finishes in three turns. MemoryBank stores the initial list action, then stores the five-file inspection action; those memories are recalled and their strengths become 2 and 4. The third response writes `run.py`, runs tests, messages reviewer and finalizes.

The resulting launcher is the same direct-current-service form seen in X1/X2. The old `legacy_compat.py` file remains in the tree, but it is no longer reachable through `run.py`.

This trajectory confirms that the MemoryBank mechanism is active during T3, but it is too short to support the long recursive feedback reading observed in T1. The correct T3 interpretation is functional retirement with a short memory-assisted process, not evidence of memory-induced inertia.

## X7: the T2 compression mechanism recurs more strongly

X7 again makes LongLLMLingua a real information-transformation layer. In T3, 32 compression calls reduce 32,890 recorded origin tokens to 15,615 compressed tokens. The mean retained fraction is about 55.9%, median about 53.9%, and the strongest compression retains about 38.3%.

Frozen compressed prompts visibly deform file names, JSON keys and code tokens—for example portions of `legacy_compat`, `CHECKOUT_COMPAT`, server code and tool-result structure become truncated or merged. Despite 118 parser-compatible accepted actions, the checkout tree remains unchanged and no terminal answer is produced.

T3 therefore **repeats** the T2 candidate information-transformation mechanism under a different task family. That recurrence makes X7 a stronger candidate for one of the two remaining local discriminating contrasts, but the natural row itself still does not establish that compression caused non-completion.

## Cross-task reading after T3

The three task families now expose visibly different process pressures:

- **T1 version review** asks the system to construct a reliable account of system state.
- **T2 feature addition** shows that a requested output can be implemented while review/collaboration keeps opening new work.
- **T3 legacy retirement** separates functional disconnection from removal of historical residue and from semantic/report closure.

The important T3 addition is the third distinction. A historical path can stop controlling runtime yet remain present as a file, a module name, stale release text, a reviewer concern or a terminal-report claim. X3 and X4 show two different forms: in X3 the residue repeatedly reopens work; in X4 the final report semantically closes more of the cleanup than the frozen tree actually closes.

These observations are compatible with candidate P-like scope persistence, candidate C-like state/report transformation, and candidate R-like historical-residue re-entry. **No CPR label is frozen from T3 alone.** The next required step is the read-only T1→T2→T3 cross-task/cross-layer audit, after which the two remaining contrast slots can be allocated only to mechanisms that remain discriminating across the complete natural matrix.

## Next gate

Natural collection is finished at **21/21**. Contrast accounting remains **2/4**. No T3 cell is rerun.

The next admissible operation is the complete read-only cross-task/cross-layer audit. At minimum it must compare:

1. T1 state-construction / interface-boundary behavior;
2. T2 post-implementation process expansion;
3. T3 historical-residue retirement and re-entry;
4. the recurrent X7 lossy-compression path across T2 and T3;
5. X3's state/review reconciliation across T2 and historical-residue loop in T3;
6. whether either remaining contrast can discriminate one local mechanism without turning Stage II into resampling.
