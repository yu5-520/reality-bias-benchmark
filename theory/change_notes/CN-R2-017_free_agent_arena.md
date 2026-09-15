# CN-R2-017 — Free-Agent Arena extension

**Status:** EXPERIMENTAL EXTENSION. Frozen R2 evidence remains unchanged.

## Motivation

Single-turn and pre-scripted workflow tests can inadvertently become benchmark engineering: the experimenter chooses the path, the Bias opportunity, and the expected Authority route before the multi-agent system acts.

The next environment therefore shifts the source of structural variation from prompt wording to multi-agent self-organization.

## Contract preserved

The R2 exit contract remains:

`Bias mechanism C/P/R → architecture-dependent Authority route I/V/T → Authority-bearing state → downstream inheritance`

CN-R2-017 does not restore a fixed one-to-one mapping and does not modify the frozen C/P/R evidence.

## New experimental object

The arena fixes only:
- identity and responsibility of available specialists;
- task/input/goal;
- specialist-private information;
- shared-state interface;
- resource limits;
- a domain-invariant Authority contract.

Routing, activation count, communication topology, state writes, revision attempts, and stopping behavior are allowed to emerge from the agents.

## Measurement implication

The 3×3 C/P/R × I/V/T matrix becomes an observed distribution rather than a set of hand-authored target cells.

The experiment must preserve event time so topology measured before the first Bias event can be separated from topology caused by the Bias itself.

## API gate

No real provider call is permitted from push-triggered validation. Real-model execution requires a dedicated `workflow_dispatch` and explicit confirmation string `CALL_REAL_API`.

Mock/scripted-provider preflight is engineering validation only and must never be included as scientific evidence.
