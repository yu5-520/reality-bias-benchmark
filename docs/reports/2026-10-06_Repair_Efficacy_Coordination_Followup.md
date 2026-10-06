# Stage II coordination-obligation repair follow-up — frozen result

Date: 2026-10-06  
Status: **SEALED**  
Case: **G3-X4-T2, nested history-24 contrast**

## Result in one sentence

Changing the live pending obligations **changed the immediate behavior but did not close the process**: the repaired frontend obligation produced an early “already satisfied, no changes” response, yet the system still consumed all 40 remaining turns and later regenerated the same “add a payment button / clarify UX” obligation through different actors.

The frozen classification is:

**REGENERATION_AFTER_LOCAL_SUPPRESSION**

This is a stronger mechanism result than simple persistence because the four original pending messages were actually replaced. The later obligation is a descendant reconstruction, not literal survival of the original text.

## Frozen comparison

The control is the already-observed suffix of the first enhanced-repair trajectory from history 24 through history 64. It was not rerun.

The C treatment branches from that exact history-24 state. At that point:

- the `run.py` application-route correction is present;
- `web/index.html` already contains `#pay-button`;
- `web/app.js` already POSTs to `/api/checkout`;
- the process remains open;
- four pending messages still ask agents to implement/reshape the button, discover additional UX requirements or widen testing.

C replaces only those four pending message contents with visibly attributed branch repairs. Original senders are retained. Queue, history and application files are unchanged by the intervention.

Workflow `37353325159` is the single provider-bearing C attempt.

## Immediate effect: the intervention worked locally

The direct local response changed.

In the frozen control, the corresponding early frontend continuation still planned to rename the button ID, use a fixed cart and potentially ask for a new `/api/cart` endpoint.

In C, turn 27 instead finalized:

> the existing payment button already satisfies the request; no changes were made.

That is a real intervention effect. The repaired obligation no longer drove the same immediate implementation-expansion decision.

This distinction matters: **the intervention was not ignored.**

## Downstream effect: the system regenerated the obligation

The local change did not shorten the trajectory.

| History 25–64 | Frozen B control | C obligation repair |
| --- | ---: | ---: |
| Continued turns | 40 | 40 |
| Boundary | turn budget | turn budget |
| Final answer | no | no |
| Post-parent writes | 0 | 0 |
| Read-file actions | 94 | 88 |
| List-files actions | 17 | 15 |
| Messages | 10 | **13** |
| Tests | 4 | **6** |
| Finalize actions | 4 | 3 |
| Final queue length | 20 | **23** |

Both suffixes used six roles. C redistributed activity: QA and frontend remained dominant, backend/product/reviewer participation increased relative to the frozen control, and release-lead participation decreased.

Most importantly, by the end of C the same semantic class of work had reappeared. At turn 64, backend again asked frontend for the checkout page/API/styling information needed to **add a payment button**, and separately asked product to confirm placement, label, loading and error behavior.

Those are not the four original repaired message strings. They were newly produced descendants.

## Mechanism interpretation

The nested contrast separates two things that a simple “repair succeeded/failed” metric would collapse.

First, pending-obligation semantics have operational force. Replacing the four messages altered the immediate behavior and removed the early implementation-expansion plan.

Second, that local authority change was not sufficient to change the larger process attractor. Other accumulated state — queue position, task framing, prior inter-agent context and newly generated messages — reconstructed equivalent obligations downstream.

The observed structure is:

`local obligation repair → immediate suppression/redirection → continued collaboration → transformed obligation descendants → regenerated task pressure → turn-budget closure`

This directly supports the paper distinction that **direct target change does not imply subsequent process repair**.

It also gives a concrete process-level R/P mechanism candidate: task/collaboration authority can re-enter through newly generated descendants even after the original pending messages have been source-bound and replaced.

## Why this is not a failed experiment

C did not need to terminate early to be informative.

If the four messages had no causal role, their replacement would not have changed the immediate frontend behavior. It did.

If those four messages were the entire cause of the long loop, their replacement should have materially reduced downstream temporal reach. It did not.

The combination is the useful result: **the selected messages were real carriers, but not the whole inertia structure.**

## Evidence accounting

First enhanced trajectory:
- workflow: `37349337495`
- artifact: `11361543373`
- artifact digest: `sha256:91ebc92f0b58ac3b2bd7090cd356e6a98a974a90fa1e86907e0e41587f9814b5`

Zero-dispatch preparation incident:
- workflow: `37352998816`
- failure: HTML preflight searched for CSS-selector bytes `#pay-button` instead of literal `id="pay-button"`
- provider calls: **0**
- scientific C attempt: **no**

Canonical C treatment:
- workflow: `37353325159`
- artifact: `11363043669`
- artifact digest: `sha256:a987033483ffe71c07bf38483bae354d4e2acce3761b78ab1be537bcbbda6fb4`
- repair-exit hash: `8fb8721894427fa08b1727d67861f57cc1b0da2b4ff4b293cac2488007226977`
- result summary hash: `19d14a5c0ae67ccb89e5fbbda0216816b86b87bc8abf5447bb540aaf4bfa5a2c`
- subject calls: **40**
- treatment retries: **0**
- control reruns: **0**

## Current scientific conclusion

Across the two new repair-effect experiments:

1. **Application-route repair** reduced implementation breadth relative to the historical local repair, but did not reduce temporal reach.
2. **Pending-obligation repair** changed the direct local response, but equivalent obligations regenerated downstream and temporal reach again remained unchanged.

Together these results point away from “repair one bad field/message” and toward the paper's original process claim: the relevant object is the **linked route of authority and inherited state**, not a single corrupted object.

This is enough to stop further infrastructure work. Any later intervention should be justified by a specific missing paper distinction, not by a desire to make the repair platform more complete.
