# R7 Runtime Integration Checklist

Use this checklist before wiring or launching any formal R7 subject run.

## Existing-runtime reuse
- [ ] Existing Arena/branch continuation entry point identified.
- [ ] Existing one-shot overlay path identified and reused for C1.
- [ ] Existing event/trace emitter identified and reused for all arms.
- [ ] Existing parent-state freeze/hash verification identified and reused.
- [ ] No duplicate runtime engine introduced.

## C1 one-shot
- [ ] Exactly one eligible post-J0 exposure.
- [ ] Overlay consumed immediately after delivery.
- [ ] Reinjection count remains zero.
- [ ] Frozen parent state remains immutable.

## C2 persistent field
- [ ] Same payload hash as C1.
- [ ] Same payload exposed at every eligible post-J0 turn within horizon.
- [ ] Every exposure is logged.
- [ ] Frozen parent state remains immutable.

## C3 ALR
- [ ] Earliest authority-violating ancestor is inspectable.
- [ ] Registered dependency relation is explicit/versioned.
- [ ] Affected dependency closure is computed deterministically.
- [ ] Preserved and affected sets are disjoint.
- [ ] Preserved successful nodes remain immutable.
- [ ] Matched semantic correction is applied to the authority/provenance condition.
- [ ] New revision identity is emitted.
- [ ] Only affected closure is reopened/re-executed.
- [ ] Original evidence remains append-only and addressable.

## Cross-arm comparability
- [ ] Same frozen parent.
- [ ] Same J0/source event.
- [ ] Same semantic payload.
- [ ] Same task/data.
- [ ] Same agent pool and prompts.
- [ ] Same model/provider binding.
- [ ] Same horizon.
- [ ] Same Process Reality measurement schema.

## Evidence freeze
- [ ] Raw trace saved before derivation.
- [ ] Raw trace hash recorded.
- [ ] Config hash recorded.
- [ ] Code SHA recorded.
- [ ] Parent-state hash recorded.
- [ ] J0/source event recorded.
- [ ] Arm-specific structural-control record saved.
- [ ] Derived structural measurements saved separately.
- [ ] Semantic review is append-only.
- [ ] Reviewer failure cannot trigger subject rerun.

## Formal launch
Formal launch remains blocked until every required item above is machine-checkable or explicitly evidenced in CI/artifacts.
