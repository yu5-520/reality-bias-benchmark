# CN-R-058 — Formal Prospective One-Shot Execution Binding

Date: 2026-09-17

## Decision

The formal prospective one-shot path must bind experimental condition **before the first provider call** and must not infer execution identity only after the trajectory finishes.

The forward runner therefore verifies the prepared plan, exact execution code SHA, model/arena/domain hashes, same frozen parent, branch manifest and envelope before provider access. Each branch journal receives a pre-provider execution-binding record.

## Direct-exposure invariant

- control: 0 experiment-origin runtime overlays;
- intervention: exactly 1 overlay;
- intervention overlay occurs on `parent_turn + 1` and the first queued resumed actor;
- overlay is consumed after delivery;
- persistent experimental mutation remains false;
- experimental reinjection remains zero.

## Evidence order

`branch execution -> raw trace/journal freeze -> raw artifact upload -> v0.3 root-scoped structural derivation -> optional semantic review later`.

## Authorization boundary

The prospective-natural authorization is consumed and cannot be reused. Formal one-shot execution uses a distinct gate:

`CALL_REAL_R5MID_PROSPECTIVE_ONESHOT_API`

No repository update or offline prepare constitutes that authorization.
