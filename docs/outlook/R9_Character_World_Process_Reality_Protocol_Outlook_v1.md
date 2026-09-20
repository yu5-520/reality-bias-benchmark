# R9 Outlook Note v1 — Character–World Process Reality Protocol

Date: 2026-09-20  
Status: **APPLICATION OUTLOOK / CONCEPTUAL INSTANTIATION / NO NEW EXPERIMENTAL EVIDENCE**  
Parent synthesis: `docs/reports/2026-09-20/R9_Inter_System_Process_Reality_Innovation_Synthesis_and_Outlook_Report_v2.md`

> **A long-lived AI game world should not be stabilized by repeatedly restating context. It should be stabilized by protocol-governed shared reality between character and world systems.**

## 1. Role inside the R9 outlook tree

This note does **not** create a third top-level outlook branch.

R9 v2 retains two broad application directions:

1. **Vibe Coding / AI software engineering** — repository formation reality, requirement drift, semantic lineage of code and interfaces;
2. **Business deployment / persistent operational systems** — long-running AI systems whose state, authority and identity must remain coherent over time.

The game setting belongs to the second branch.

Its value is that it makes **Inter-System Process Reality** unusually concrete:

`Character System <-> Process Reality Protocol <-> World / Social System`.

The game example is therefore a conceptual application of the system-to-system thesis, not new evidence for Dynamic CPR.

---

# 2. Two Different Persistence Problems

A persistent AI game must solve at least two different structural problems.

## 2.1 Character Reality

The character system maintains:

- identity;
- core values;
- stable traits;
- beliefs;
- relationships;
- episodic memory;
- current emotion / intention;
- action and dialogue.

Its core question is:

> **Why is this still the same character after many hours of changing context?**

## 2.2 World / Social Reality

The environment and social system maintains:

- world rules;
- geography and resources;
- institutional structure;
- law;
- factions;
- authority relations;
- economic and social conditions;
- public events;
- local environment state;
- historical revisions.

Its core question is:

> **Why is this still the same world after many characters and events have acted inside it?**

Character stability and world stability are not the same problem.

A character can remain internally coherent while the world drifts.

A world can remain internally coherent while a character drifts.

The protocol between them must therefore preserve **cross-system reality boundaries**.

---

# 3. Context Controls Expression; Structure Controls Identity

A useful design distinction is between fast-changing and slow-changing state.

## 3.1 Character time scales

| Layer | Typical contents | Expected change velocity |
| --- | --- | --- |
| Character Constitution | identity, core values, non-negotiable boundaries | very slow |
| Stable Traits | personality tendencies, long-term preferences | slow |
| Relationship / Belief | trust, hostility, commitments, uncertain beliefs | medium |
| Episodic Memory | experienced events and interpretations | accumulating / revisable |
| Current State | emotion, fatigue, local goal, immediate intention | fast |
| Generated Behaviour | current dialogue and action | very fast |

The important principle is:

> **A lower-level or faster-changing state should not automatically obtain permission to rewrite a higher-level or slower-changing identity state.**

A temporary fear response can influence current behaviour.

It should not automatically rewrite a stable trait into `cowardly`.

A single betrayal may change a local relationship state.

It should not automatically rewrite a core value.

Character growth remains possible, but durable structural change requires a stronger semantic lineage and a higher write threshold.

## 3.2 World / social time scales

| Layer | Typical contents | Expected change velocity |
| --- | --- | --- |
| World Constitution | physical / magical rules, technology floor/ceiling | near-immutable |
| Institutional Structure | political system, law, organizational rights, social roles | very slow |
| Public World State | war/peace, regime state, market state, public crises | slow / medium |
| Local Environment State | city shortages, road closure, local control | medium |
| Scene State | weather, present actors, immediate combat/event state | fast |

The same principle applies:

> **The world may change, but change must travel through an authorized causal path.**

A tavern fight may alter a scene or local reputation.

It should not directly rewrite the political constitution of the kingdom.

---

# 4. Shared Pools Instead of One Undifferentiated Context

The proposed architecture does not treat the game as one ever-growing prompt.

Instead, it maintains multiple shared-reality pools with different semantics and write permissions.

## 4.1 Character-side pools

- `CHARACTER_CONSTITUTION_POOL`
- `STABLE_TRAIT_POOL`
- `RELATIONSHIP_POOL`
- `BELIEF_POOL`
- `EPISODIC_MEMORY_POOL`
- `CURRENT_CONTEXT_POOL`

## 4.2 World-side pools

- `WORLD_CONSTITUTION_POOL`
- `INSTITUTIONAL_STRUCTURE_POOL`
- `PUBLIC_WORLD_STATE_POOL`
- `LOCAL_ENVIRONMENT_POOL`
- `SCENE_STATE_POOL`

The model may read from several pools.

It should not receive equivalent write authority over all of them.

This yields a general rule:

> **Retrieval is not authorization.**

A memory can be retrieved without being allowed to rewrite identity.

A rumor can be retrieved without being allowed to rewrite public world fact.

A generated action can be proposed without being allowed to mutate institutional reality.

---

# 5. Character–World Process Reality Protocol

The protocol layer governs what one system's output is allowed to become inside another system.

A generalized transfer object may contain:

`source_system`  
`semantic_object_id`  
`value / proposition`  
`epistemic_status`  
`authority_scope`  
`validity_window`  
`target_system`  
`permitted_operation`  
`lineage_address`  
`commit_condition`.

The protocol is therefore not only an API schema.

It is a **Semantic-Authority Interface Contract**.

## 5.1 Character -> World example

A character says:

> “I heard the king may be dead.”

That statement may enter:

`Character.BeliefPool`.

It must not directly write:

`World.King.Status = DEAD`.

A protocol representation could be:

`source_system = Character_A`  
`object = king_status`  
`status = rumor`  
`authority_scope = private_belief`  
`target_system = World`  
`permitted_operation = NONE`.

Only an independently authorized world event may commit:

`status = confirmed`  
`authority_scope = public_world_fact`  
`permitted_operation = WORLD_STATE_COMMIT`.

This is a concrete system-level **C boundary**.

## 5.2 Character -> Social authority example

A local lord may announce:

> “Mobilize the national army.”

The character system can emit the proposal.

The world/social system must check:

- office;
- jurisdiction;
- law;
- institutional state;
- current delegation;
- exceptional authority.

Speech does not equal execution permission.

This is a concrete system-level **P boundary**.

## 5.3 Historical state re-entry example

An old regime rule may still exist in archived memory or an old world-state summary.

If later retrieval causes the current world to behave as though the obsolete rule remains active, historical reality has regained operational authority without a valid re-entry path.

This is a concrete system-level **R boundary**.

---

# 6. Persistent Character Reality

The research target is not an immutable NPC.

The target is:

> **Persistent identity under contextual change.**

A useful formulation is:

> **Context controls expression; structure controls identity.**

The character may:

- change tone;
- change emotion;
- change immediate goals;
- change relationships;
- learn;
- grow;
- revise beliefs.

But durable identity-level change should require an explicit lineage.

Example:

`repeated betrayal events`  
-> `relationship deterioration`  
-> `new protective strategies`  
-> `persistent belief revision`  
-> `identity-level revision candidate`  
-> `authorized new character revision`.

The system should preserve:

`prior_revision_hash -> change lineage -> new_revision_hash`.

This makes character development traceable rather than accidental.

---

# 7. Persistent World and Social Reality

The world system should also maintain structural inertia.

Its goal is not to freeze the world.

Its goal is to prevent **local generation from silently acquiring global write authority**.

A social world is particularly important because many facts are collectively maintained.

For example, “the king has taxation authority” is not merely a sentence in one Agent's prompt.

It is supported by:

- legal structure;
- institutional recognition;
- administrative systems;
- military / enforcement capacity;
- other actors' recognition;
- historical continuity.

Thus social reality is a form of:

> **Collectively Maintained Process Reality.**

A single character claim should not directly overwrite such a state.

A legitimate structural change may require a lineage such as:

`local conflict`  
-> `large-scale unrest`  
-> `institutional fracture`  
-> `authority transfer`  
-> `public-state revision`  
-> `new institutional revision`.

---

# 8. Why This Is a System-to-System Protocol Problem

The game application makes one R9 claim concrete:

> **Interacting systems do not merely exchange information; they exchange representations that may carry different permissions to become reality.**

Character and world systems therefore need rules for:

- what may be believed;
- what may be written;
- what may be executed;
- what may alter identity;
- what may alter public reality;
- what historical state may act again;
- what evidence is required for revision;
- which descendants must be recomputed after correction.

The same protocol structure can later be studied in:

- Human <-> AI;
- Agent <-> RAG;
- Agent <-> Database;
- Workflow <-> ERP;
- Service <-> Service;
- AI coding Agent <-> repository.

The game setting is valuable because the distinction between **private belief**, **character identity**, **public world fact**, **institutional authority** and **historical state** is unusually visible.

---

# 9. Connection to the Semantic Process Integrity Stack

A future implementation can reuse the same abstract stack already developed in the first-paper repository:

`semantic object`  
-> `content address`  
-> `hash / evidence lineage`  
-> `functional semantic lineage`  
-> `authority history`  
-> `affected closure`  
-> `repair packet`  
-> `selective recomputation`  
-> `preserve unrelated semantics`  
-> `re-entry watch`.

In the game context, this could support:

- locating the exact character belief/trait/world fact that drifted;
- tracing how it entered downstream dialogue, relationships, quests or institutional state;
- invalidating only the affected lineage;
- recomputing only dependent decisions;
- preserving unrelated character memory and world state;
- watching for old invalid authority to re-enter through memory retrieval.

The engineering shift remains:

> **Do not reset the whole character or world when one semantic lineage is wrong. Repair the addressable lineage that carried the wrong reality.**

---

# 10. Research Questions Opened by the Game Scenario

This application suggests several future research questions:

1. How should write permissions differ across character identity, belief, relationship and current-context pools?
2. What evidence threshold should permit a fast state to modify a slow state?
3. How should Character Reality and World Reality negotiate conflicting representations?
4. Can Dynamic C/P/R be reproduced at Character <-> World system boundaries?
5. How should social/institutional reality be represented when authority is collectively maintained?
6. Can semantic-lineage repair preserve hundreds of hours of unaffected world and character history?
7. Which system boundary failures are caused by context truncation, and which persist even with perfect retrieval because the underlying permission protocol is wrong?
8. Can long-lived game worlds provide a controlled experimental setting for Persistent Identity and Persistent Social Reality?

---

# 11. Claim Boundary

This note establishes no new experimental result.

It does **not** claim:

- that current game AI universally suffers from formally adjudicated CPR;
- that the proposed Character–World protocol has been implemented or benchmarked;
- that the architecture outperforms prompt-based character systems;
- that human identity or social systems are literally equivalent to the proposed software architecture.

Its role is:

`APPLICATION OUTLOOK / CONCEPTUAL INSTANTIATION`.

The stronger point is structural:

> **Character Reality and World/Social Reality are different persistent systems, and their interaction requires an explicit protocol governing how semantic status, authority and historical state cross the boundary between them.**

That is a concrete business-deployment instance of the broader R9 direction:

> **Inter-System Process Reality.**
