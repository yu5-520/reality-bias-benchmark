# Minimal Experimental State-Control Layer v0.3

Status: FORWARD OFFLINE ENGINEERING / ONE-SHOT TRANSIENT INTERVENTION  
Date: 2026-09-17  
Supersedes for forward work: v0.2. Historical v0.1/v0.2 records remain unchanged.

## 1. Core correction

v0.2 correctly separated frozen parent state from a post-intervention branch-start state for persistent state interventions.

The forward R5-MID mechanism protocol is different: the intervention must not become persistent Arena state.

Therefore v0.3 supports:

```text
parent_state_hash == branch_start_state_hash
+ transient one-shot intervention envelope
```

## 2. One-shot envelope

The envelope is external experimental metadata binding:

- target natural Jump/event;
- target state key/source event;
- original status;
- one-shot overlay status;
- delivery policy;
- temporal scope;
- direct-exposure limit;
- persistence/reinjection prohibitions;
- envelope hash.

It is not stored into `shared_state_metadata` as persistent runtime state.

## 3. Delivery lifecycle

`PENDING -> DELIVERED -> CONSUMED`

A delivery record freezes actor, turn, before/after runtime-view hashes and the exact prompt-visible field path changed by the experiment.

Forward invariant:

- direct experiment-origin exposure count = 1 for B;
- = 0 for control;
- reinjection count = 0;
- persistent experimental mutation = false.

## 4. Runtime transformation

The Arena may apply an optional runtime-view transform after it has read the real persistent state but before prompt construction. The one-shot transformer changes only the copied runtime view. State and later views remain natural unless Agents themselves change them.

## 5. Branch manifest v0.3

A v0.3 manifest binds:

- frozen parent/start state identity;
- condition identity;
- intervention spec/hash;
- optional one-shot envelope hash;
- temporal scope/direct exposure limit;
- persistent-state-mutation=false;
- provider-internal-state-replayed=false.

## 6. Scientific interpretation

Same-parent + one transient overlay does not make A/B identical counterfactual worlds because provider randomness is not replayed. Repeated matched branches estimate conditional structural variability.

## 7. Historical compatibility

Persistent `set_shared_state_status` remains available only for historical protocol replay/verification. It is not the forward R5-MID mechanism intervention.
