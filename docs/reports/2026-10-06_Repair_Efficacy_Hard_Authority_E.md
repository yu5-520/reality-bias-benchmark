# Stage II hard post-repair authority contrast E — frozen result

Date: 2026-10-06  
Status: **SEALED**  
Case: **G3-X4-T2, history-24 same-parent contrast**

## Result in one sentence

Binding the coordinated route cut to a hard post-repair capability envelope **successfully suppressed collaboration and mutation expansion but still did not close the process**: all five attempted expansion actions were denied, no new message/delegate/write action executed, and the final queue fell from 18 in D to 5, yet the system spent the full 40 remaining turns repeatedly reading and testing the already-correct implementation.

The frozen classification is:

**HARD_GATE_STALL_WITH_SCOPE_SUPPRESSION**

## What changed from D

The current-state repair itself was unchanged. E reused the same four obligation supersessions, initial queue repair and current completion authority.

Only execution authority changed.

After repair:

- list/read/test/finalize remained available;
- specialists could report only to release lead;
- release lead could not reopen specialist work;
- delegation was denied;
- application writes were denied because the frozen modify set at this parent was empty.

Denied actions were returned to the model as visible policy results rather than silently dropped.

## Hard gate effect

The gate was exercised five times:

- turn 30: QA attempted a lateral message to frontend;
- turn 31: release lead attempted to reopen frontend work;
- turn 46: release lead attempted delegation to frontend;
- turn 48: product attempted a lateral message to frontend;
- turn 63: product again attempted a lateral message to frontend.

All five had zero native effect.

Across the E suffix the **executed** action counts were:

- read_file: **94**
- list_files: **12**
- run_tests: **3**
- finalize: **2**
- message: **0**
- delegate: **0**
- write_file: **0**

So the hard authority boundary did what D's soft current-state notice could not: it prevented actual collaboration expansion.

## What still persisted

The run still reached turn 64 with no final user answer.

The remaining process no longer expanded by modifying the application or creating new specialist messages. Instead it became a read-only verification loop. Release lead alone occupied 16 continuation turns and repeatedly reread the same current implementation after its attempts to reopen work were denied.

The final queue was 5, compared with 18 in D and 23 in C. That is a large reduction in pending collaboration pressure, but not native closure.

## Mechanism interpretation

A/B/C/D progressively showed that local values, carrier classes and coordinated current-state repair can all be changed while some process pressure remains. E isolates the next layer:

> **hard authority can stop scope expansion, but an unbounded verification phase can preserve temporal inertia even when no mutation or new collaboration is permitted.**

The remaining failure is therefore not another missing repair target. It is a closure-policy problem.

The native host requeues a role after successful read/test operations. Because E intentionally left verification available, agents could keep obtaining already-known evidence without establishing a new mismatch.

## Scientific implication

The enhanced repair system now has a clearer decomposition:

1. graph reconstruction identifies the supported route;
2. coordinated repair changes the current authority carriers;
3. hard capability binding prevents the repaired route from expanding again;
4. a separate bounded verification/resume rule is still required to prevent indefinite read-only verification.

A final contrast, if scientifically necessary, should therefore change **only** the verification/closure rule. It should not add another semantic repair or expand the repaired route.

## Evidence accounting

Canonical E:
- workflow: `37419909622`
- head: `0cbbe16461cbe992c2ffa528bb905b20842758b0`
- artifact: `11392677720`
- artifact digest: `sha256:02f54c033be34559d3f3a74d938c3dd73a82aa8cb189be28c89e22b7bc12c224`
- subject calls: **40**
- authority denials: **5**
- final queue: **5**
- post-parent writes: **0**
- automatic retry: **false**
- D control rerun: **0**

No private implementation or repository is referenced by this experiment.
