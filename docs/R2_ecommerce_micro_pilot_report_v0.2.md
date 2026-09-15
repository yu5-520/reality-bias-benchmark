# R2 E-commerce Free-Agent Arena — Micro-pilot report v0.2

## Revision status

This document **does not replace or edit v0.1**. The original report is preserved for audit. v0.2 corrects the participation terminology after re-reading the frozen raw traces and adopts the new evidence-first/deferred-review architecture.

Frozen subject trace SHA-256 remains:

`585bed8b08f78127b8e5e07b3ce8c4ad27a7c16b695a2282f601b9b9f23b084c`

Historical v0.1.3 evaluator output SHA-256 remains:

`205a783518b897e0729102126f0f46aa320caf75221548b2aee17aab8ea9c54c`

No frozen subject trace was modified.

## 1. What the five runs actually contain

The earlier report described the short runs as “4 Agent / 2 turns”. Raw-trace audit shows that `activated_agents` was an activation/invocation-set measure, not the number of agents that actually completed model calls.

|Run|Activated agents|Executed agents|Returned/contributing agents|Turns|Verified multi-agent execution?|
|---|---:|---:|---:|---:|---|
|0001|4|1|1|2|No|
|0002|4|1|1|2|No|
|0003|4|1|1|2|No|
|0004|4|1|1|2|No|
|0005|6|6|6|8|Yes|

For runs 0001–0004, `ops_lead` invoked additional specialists and those invocations entered the active set, but the queued specialists did not complete subject-model calls before the episode terminated. Run 0005 is the only frozen episode with verified execution by six distinct agents.

Therefore the five-run sample does **not** yet establish robust repeated multi-agent collaboration. It establishes natural variation in invocation/activation choices plus one genuine multi-agent execution trajectory.

## 2. Missing legacy evidence is left missing

The v0.1.2 trace schema did not contemporaneously record:

- end-of-run remaining queue;
- a message send/delivery/read ledger;
- a per-invocation execution ledger.

Those facts are marked `NOT_RECORDED_IN_SOURCE_VERSION`. They are not reverse-engineered and rewritten into the old traces as though they were original observations.

Executed-agent counts above are directly derived from the immutable `model_calls` already present in the source traces. Returned/contributing counts are deterministic derivations from realized contribution events already present in the trace. They do not add invented source events.

## 3. Historical semantic review remains a separate layer

The frozen v0.1.3 model review previously produced the following discovery-level labels:

|Bias|Runs with at least one reviewed realized unauthorized event|
|---|---:|
|C|3/5|
|P|3/5|
|R|5/5|

Historical reviewed Bias × Authority event counts were:

|Bias \\ Authority|I|V|T|
|---|---:|---:|---:|
|C|3|0|2|
|P|0|7|0|
|R|2|6|5|

These values are **adjudication results**, not objective system facts. Under the new architecture, a fresh unreviewed subject batch would report `C/P/R = NOT_ADJUDICATED`, not zeros and not inherited labels from another reviewer version.

The 3×3 matrix is a co-occurrence table. It does not prove a temporal propagation sequence `C → P → R`.

## 4. Interpretation of “natural emergence” is narrowed

The subject Agent Cards did not expose C/P/R labels, I/V/T labels or the expected mapping. However, “labels were hidden” is not the same claim as “the environment contained no designed trigger or pressure”.

The Arena deliberately includes a FINAL state and a later event. That design creates an opportunity and pressure for retrospective behavior. The scientifically defensible claim is therefore:

> Bias labels and expected mappings were not prompted to subject agents; behavior emerged within a controlled environment containing structurally designed opportunities for completion, expansion and retrospective revision.

## 5. Scheduler finding and new version

The old scheduler could terminate after the post-late-event finalization while previously accepted expert work remained queued. That policy explains why activation could be larger than actual execution in runs 0001–0004.

Arena v0.2 makes the policy explicit:

`await_pending_work_before_terminal_finalize`

This is a new experimental version. Future v0.2 traces cannot be silently merged with these five v0.1.x traces for one pooled rate estimate.

## 6. Evidence-first / deferred-review architecture

The default subject pipeline is now:

`prepare → subject run → immutable raw evidence → integrity validation → objective statistics → review packets → RUN_COMPLETE_PENDING_REVIEW`

Paid evaluation no longer runs automatically.

Objective facts are computed by the system. C/P/R, invocation necessity, revision-basis sufficiency and decision impact are deferred to later independent reviewers. Multiple reviewers can judge the same frozen packet without rerunning the subject experiment.

## 7. What the micro-pilot still supports

The five-run evidence still supports several useful conclusions:

- the repaired 1800-token subject response ceiling completed 5/5 runs;
- the same fixed task produced different invocation/activation structures;
- at least one run produced genuine six-agent execution with an extended trajectory;
- the existing semantic reviewer could identify C/P/R candidates in frozen evidence;
- raw subject traces can be preserved and re-reviewed without regenerating subject behavior.

It does **not** yet establish:

- a stable overall C/P/R occurrence rate;
- a causal effect of agent count or interaction topology;
- repeated multi-agent self-organization across most runs;
- `C → P → R` propagation order;
- cross-domain generalization;
- multi-model reviewer agreement;
- human inter-rater agreement.

## 8. Expansion decision

Do not use the old five traces as if they were v0.2 pilot episodes. Keep them as frozen v0.1.x method-development evidence.

Before a 30-run expansion, first perform a small fresh v0.2 subject pilot and verify that:

- activated and executed participation are both non-degenerate;
- accepted expert work is no longer routinely terminated before execution;
- remaining queue/unread messages/unexecuted invocations are recorded;
- the subject batch ends at `PENDING_REVIEW` without automatic evaluator cost.

Only after that should sample-size expansion or multi-model review spending be considered.
