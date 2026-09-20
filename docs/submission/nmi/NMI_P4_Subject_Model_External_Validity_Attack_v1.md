# NMI-P4 Reviewer Attack 08 — Limited Subject-Model External Validity

Date: 2026-09-21  
Status: **EXTERNAL-VALIDITY BOUNDARY HARDENED / NO NEW SUBJECT RUN**

## Attack question

> Are the observed Process Reality mechanisms specific to one subject model/provider/runtime rather than general properties of interacting AI systems?

This is a valid external-validity attack.

The correct response is not to treat domain diversity, evaluator diversity or repeated stochastic runs as substitutes for subject-model replication.

## 1. What the core subject evidence actually covers

The main formal subject programme uses one frozen subject-model family/configuration.

The relevant repository contracts bind:

- provider: `deepseek`;
- model alias: `deepseek-flash`;
- expected model version: `DeepSeek-V4.1-Flash`;
- common Arena/runtime family;
- common recording contracts.

The formal e-commerce Batch001 workflow freezes `arena/config/model_deepseek_v0.2.json`.

The 90 held-out natural trajectories across Finance, Supply Chain and Software Engineering use the same model config and explicitly lock:

> `same_model_provider_all_replication_domains = true`.

Canonical active R5 plans also use provider `deepseek`, and R7 subject execution binds the same model config/provider.

R6 is passive over already-frozen evidence.

Therefore the first paper has:

- meaningful **domain variation**;
- meaningful **stochastic trajectory variation**;
- meaningful **mechanism/repair variation**;

but not independent subject-model/provider replication.

## 2. Why fixing the model was scientifically useful

Using one subject model across the held-out domains is not itself a flaw in internal comparison.

It prevents domain contrasts from being confounded with a simultaneous model change.

The design can therefore ask:

> under one fixed model/runtime surface, does the process mechanism appear across distinct task domains and trajectory structures?

That is a useful mechanism-discovery question.

But the price is explicit:

> **cross-domain evidence does not establish cross-model robustness.**

## 3. Reviewer-model diversity does not solve subject-model validity

The repository contains historical cross-model semantic review.

Reviewer A and a blind DeepSeek reviewer disagreed materially on the same 70 frozen Authority-bearing events:

- C agreement: 0.700, Cohen κ = 0.158;
- P agreement: 0.729, Cohen κ = 0.318;
- R agreement: 0.729, Cohen κ = 0.486;
- 54 / 70 events had at least one label-set or authorization disagreement.

This is useful evidence about **measurement sensitivity**.

It is not evidence that different subject models naturally generate the same Process Reality mechanisms.

Canonical guard:

> **cross-model review != cross-model subject replication**.

A second reviewer can reinterpret the same trace.

It does not create an independent trace from a different subject model.

## 4. Same-model measurement-contract sensitivity reinforces the distinction

A historical same-model v1->v2 semantic transition on the same frozen 70 events produced dramatic label changes when the measurement contract changed.

That result shows:

> semantic operationalization is part of the measurement apparatus.

It therefore makes it even less defensible to treat evaluator/model diversity as a surrogate for subject-system robustness.

Subject external validity and measurement reliability are separate axes.

## 5. What can be claimed now

Allowed:

> Process Reality mechanisms are observed and experimentally interrogated in the studied multi-agent runtime.

Allowed:

> Domain-held-out evidence shows that relevant process structures are not confined to the original e-commerce task setting.

Allowed:

> The work provides a mechanism and measurement programme that can be independently replicated under other model families.

Not allowed:

- model-invariant C/P/R prevalence;
- provider-invariant mechanism frequency;
- universal robustness across frontier models;
- robustness across reasoning/non-reasoning modes;
- topology-invariant or memory-architecture-invariant behaviour;
- “multiple reviewers” as evidence of “multiple subject models.”

## 6. External-validity ladder

The current first-paper evidence can be classified as:

| Axis | Status |
| --- | --- |
| E-commerce -> Finance/Supply Chain/Software Engineering domain variation | **SUPPORTED** |
| Repeated stochastic trajectories under fixed runtime | **SUPPORTED** |
| Subject-model family variation | **NOT ESTABLISHED** |
| Provider variation | **NOT ESTABLISHED** |
| Reasoning-mode variation | **NOT ESTABLISHED** |
| Context-window variation | **NOT ESTABLISHED** |
| Agent-topology variation | **NOT ESTABLISHED** |
| Memory-architecture variation | **NOT ESTABLISHED** |
| Independent laboratory replication | **NOT COMPLETE** |

## 7. What a clean next replication should do

The next external-validity experiment should not rewrite the theory after each model.

It should freeze:

- task/domain fixtures;
- Arena/runtime protocol;
- evidence schema;
- structural observability contract;
- semantic audit contract;
- censoring policy;
- analysis outputs.

Then vary subject model/provider as the independent factor.

A clean first replication matrix could be:

`same tasks + same Arena + same audit -> different subject model/provider`.

Only after that should the study separately vary:

- routing/topology;
- memory architecture;
- context policy;
- tool surface.

This preserves interpretability of the robustness test.

## 8. Why this does not invalidate the first paper

The first paper is mechanism-first, not a benchmark leaderboard.

A mechanism paper can establish:

- existence;
- internal structure;
- diagnostic perturbability;
- lineage;
- repairability;

inside a bounded experimental realization before universal robustness is known.

The claim must simply remain at that level.

The attack would become fatal only if the paper claimed:

> “all modern LLM systems exhibit this mechanism at similar rates.”

It does not need that claim.

## Verdict

Attack:

**“The subject-model coverage is too narrow to claim generality.”**

Verdict:

**SUPPORTED AGAINST GENERALITY CLAIMS; DOES NOT INVALIDATE THE BOUNDED MECHANISM CLAIM.**

Canonical boundary:

> **Domain variation is supported; subject-model/provider robustness is not yet established.**

The paper should treat alternate-model subject replication as external validation, not as evidence already supplied by cross-model semantic reviewers.
