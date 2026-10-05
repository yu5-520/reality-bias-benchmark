# Stage II evidence-selection gate contrast

Date: 2026-10-05

Status: IMPLEMENTATION/PREFLIGHT ONLY — B PROVIDER ATTEMPT NOT YET REGISTERED.

## Question

The field-link line is closed. Its v3 first attempt (`37324115903`) already had
unambiguous IDs, version time, one message-write surface, host-derived message
value, direct capability limits and explicit read-versus-witness rules. The
model nevertheless read only the pending message, selected no witness, explicitly
stated that the current files had not been verified, and then submitted a
`SOURCE_BOUND_CLAIM` repair. The host rejected it at
`CURRENT_MESSAGE_WITNESS_REQUIRED`.

This contrast asks a different question: **when the interface is already clear,
does a stronger decision-gating instruction change evidence-selection behavior?**
It is a model/tool-use strategy test, not another field-link revision.

## Frozen A arm

A is the retained v3 first attempt. It is never rerun.

- run: `37324115903`
- head: `f55cf0e2176d006b6786f10adc519e29c3df5487`
- artifact: `11350259380`
- provider responses: 2
- source reads: current pending message only
- selected witnesses: 0
- failure: `CURRENT_MESSAGE_WITNESS_REQUIRED`
- native repair actions: 0

## B intervention

Everything remains unchanged except one appended planning instruction:

> EVIDENCE-SELECTION CONTRAST ONLY: FINAL is forbidden unless the complete
> current pending message has a selected witness and every distinct source_ref
> and destination_ref that will appear in a SOURCE_BOUND_CLAIM has a selected
> witness. If the gate is not satisfied, return another TOOL call instead of
> FINAL. Do not weaken, omit, or rename a claim merely to bypass this gate.

This changes no field name, tool, tool argument, source version, task capability,
write permission, repair action, model profile or call budget.

## Execution boundary

B is one planning-only first attempt. There is no repair dispatch, subject
continuation or paid reviewer. A B outcome is frozen whether it succeeds,
fails, stops unresolved or exhausts its original planning budget. No second B
attempt is permitted.

Primary observations are the actual tool sequence, actual source reads, selected
witness refs, first FINAL (if any), host compilation result and provider-call
count. Authorization creation is an observation, not a repair-success claim.

## Interpretation

If B selects the required evidence before FINAL, that supports the narrow claim
that a stronger decision gate can change tool-use behavior in this frozen case.
It does not show universal reliability or repair efficacy.

If B again submits FINAL without the required witnesses, the result strengthens
the classification of the remaining failure as model evidence-selection behavior
rather than field ambiguity.

Either outcome leaves the field-link baseline frozen.
