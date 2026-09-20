# NMI-P4 Structural Scout Recall Attack Report v1

Date: 2026-09-20  
Status: **CALIBRATED ON FROZEN HELD-OUT DATA / NO NEW SUBJECT OR SEMANTIC ADJUDICATION**

## 1. Reviewer attack

> **How do you know that structural pre-screening did not omit semantically important process-reality problems? If it did omit them, what was the miss rate?**

This attack is valid because the forward engineering chain uses structural machinery to reduce the semantic-audit surface:

`All Events -> Structural Scout -> Candidate Regions -> Semantic Audit`.

A structural scout is useful only if its compression does not silently become an exhaustiveness claim.

The attack therefore separates two different failure modes:

1. **evidence omission** — the structural packet no longer contains the later relevant process region;
2. **selection omission** — the structural evidence is present, but a deterministic high-risk rule fails to nominate the relevant semantic mechanism.

These must not be conflated.

---

# 2. Frozen comparison design

No Agent trajectory was rerun.

No provider or evaluator call was made.

The comparison uses the same **90 held-out natural trajectories** from Finance, Supply Chain and Software Engineering.

### Earlier structural stages

The original structural layer generated:

- **2,127** repair-anchor candidate rows;
- deterministic triage reduced these to **167** localized-audit cases;
- FORMATION anchors: 90;
- PROPAGATION anchors: 90;
- AUTHORITY_REVIEW anchors: 85.

Candidate-surface retention:

`167 / 2,127 = 7.8514%`.

Candidate-surface compression:

`1 - 167/2,127 = 92.1486%`.

This is **compression**, not semantic recall.

### Narrow B2 high-risk structural selector

The earlier B2 window selector used deterministic structural shortcuts:

- C: explicit same-key status transition into `fact`;
- P: reviewer boundary followed by first activation of a previously unused Agent;
- R: reviewer boundary followed by Agent re-entry and/or first activation.

It selected:

- C windows: 21;
- P windows: 15;
- R windows: 44;
- unique trajectories selected by any B2 rule: 52 / 90.

### Later reference audit

The later R8 trajectory-first audit reviewed the full 90 natural trajectories.

Within that frozen cohort it supported:

- high-confidence Dynamic C: **0**;
- Dynamic P: **13** trajectories;
- retrospective-generative Dynamic R: **12** trajectories;
- unique P-or-R-supported trajectories: **13**.

These supported counts are used only as a **conditional calibration reference**. They are not converted into a new prevalence claim.

---

# 3. Structural-selector calibration

## 3.1 P selector

Among the 13 trajectories later supported for Dynamic P, the narrow B2 P rule selected 4.

`capture = 4 / 13 = 30.7692%`

`miss = 9 / 13 = 69.2308%`

Captured:

- `v5-xd-supply_chain-fr001-0011`
- `v5-xd-supply_chain-fr001-0012`
- `v5-xd-software_engineering-fr001-0001`
- `v5-xd-software_engineering-fr001-0002`

Missed:

- `v5-xd-finance-fr001-0027`
- `v5-xd-supply_chain-fr001-0014`
- `v5-xd-supply_chain-fr001-0019`
- `v5-xd-supply_chain-fr001-0029`
- `v5-xd-software_engineering-fr001-0007`
- `v5-xd-software_engineering-fr001-0013`
- `v5-xd-software_engineering-fr001-0025`
- `v5-xd-software_engineering-fr001-0027`
- `v5-xd-software_engineering-fr001-0029`

Interpretation:

> **Agent-count / first-new-Agent activation is a weak structural proxy for process-side P.**

A collaboration can exceed its original goal while using already-active Agents to create additional monitoring, verification, ownership or execution obligations.

That is why Dynamic P is defined semantically by:

`original_goal <-> authorized_boundary <-> realized_process_scope <-> result`

rather than by Agent count.

## 3.2 R selector

Among the 12 trajectories later supported for Dynamic R, the narrow B2 R rule selected 9.

`capture = 9 / 12 = 75.0%`

`miss = 3 / 12 = 25.0%`

Missed:

- `v5-xd-software_engineering-fr001-0007`
- `v5-xd-supply_chain-fr001-0019`
- `v5-xd-supply_chain-fr001-0029`

Interpretation:

> **A reviewer boundary is not the general form of retrospective process re-entry.**

The later R8 definition is broader:

`prior closure -> retrospective / late-event boundary -> regenerated process -> new C/P`.

Natural late-event reopening can therefore support R even when there is no reviewer boundary.

## 3.3 Union of the earlier high-risk rules

There are 13 unique trajectories later supported for P and/or R.

The union of all earlier B2 high-risk structural rules selected 10 of them.

`conditional capture = 10 / 13 = 76.9231%`

`conditional miss = 3 / 13 = 23.0769%`

Thus the earlier narrow structural high-risk selector had a **23.08% conditional trajectory-level miss rate** against the later full-trajectory P/R-supported reference set.

This is the calibrated number that may be reported for this specific selector and frozen cohort.

It is **not** a universal structural-scout miss rate.

## 3.4 C

R8 supported no high-confidence Dynamic C in the 90 held-out natural trajectories.

Therefore C recall cannot be estimated from this held-out cohort:

`positive denominator = 0`.

No artificial recall number is reported.

---

# 4. The three misses: evidence loss or selector loss?

The most important result is that the three union misses were **not absent from the broader structural triage**.

## 4.1 Software Engineering 0007

Run:

`v5-xd-software_engineering-fr001-0007`

Later R8:

- P = SUPPORTED / HIGH;
- R = SUPPORTED_RETROSPECTIVE_GENERATIVE_R / HIGH.

Frozen structure:

- natural late event: turn 1;
- reviewer turns: none;
- triage FORMATION + AUTHORITY anchor: turn 4, `telemetry_assessment`, provisional;
- triage PROPAGATION anchor: turn 6, `sre_release_assessment`;
- preserved downstream summaries extend through turn 24.

Why B2 missed it:

The P/R B2 selectors required a reviewer boundary. This trajectory has none.

Conclusion:

> The structure preserved the continuation; the narrow selector did not nominate it.

## 4.2 Supply Chain 0019

Run:

`v5-xd-supply_chain-fr001-0019`

Later R8:

- P = SUPPORTED / HIGH;
- R = SUPPORTED_RETROSPECTIVE_GENERATIVE_R / HIGH.

Frozen structure:

- natural late event: turn 1;
- reviewer appears only at turn 32;
- triage PROPAGATION + AUTHORITY anchor: turn 2, `late_event_west_forecast`, provisional/unreconciled;
- visibility spans eight actors;
- downstream evidence reaches turn 32.

Why B2 missed it:

The relevant generative continuation occurs after the natural late event, long before the reviewer boundary used by the selector.

Conclusion:

> The broad structural packet captured the correct process region, but the reviewer-centred rule was temporally misaligned.

## 4.3 Supply Chain 0029

Run:

`v5-xd-supply_chain-fr001-0029`

Later R8:

- P = SUPPORTED / HIGH;
- R = SUPPORTED_RETROSPECTIVE_GENERATIVE_R / HIGH.

Frozen structure:

- natural late event: turn 4;
- reviewer turns: none;
- one triage packet carries FORMATION + PROPAGATION + AUTHORITY roles;
- the packet begins from `draft_plan` and preserves downstream evidence through turn 32.

Why B2 missed it:

Again, no reviewer boundary exists.

Conclusion:

> The later semantic mechanism is visible in the broader trajectory, but not expressible by the narrow reviewer-boundary rule.

---

# 5. Broad triage preservation proxy

For the 13 trajectories later supported for P and/or R:

- every trajectory had deterministic triage packets;
- every trajectory had at least one selected packet whose preserved downstream call evidence extends **at or beyond the frozen natural late-event boundary**;
- post-late structural-packet coverage proxy: **13/13 = 100%**;
- 12/13 selected packet sets reached the final trajectory turn;
- Software Engineering 0007 reached turn 24 of 32 but still crossed the natural late-event boundary and preserved the continuation region.

This is evidence that the broader triage retained relevant structural access in these cases.

However:

> **13/13 post-late packet coverage is not exact semantic-episode recall.**

The R8 v0.1 record schema does not attach exhaustive event-level semantic episode anchors to every supported and unsupported semantic episode. Exact candidate-level semantic recall therefore cannot be reconstructed without a new event-level annotation exercise, which is not authorized for the first submission.

---

# 6. What the attack changes scientifically

The attack rejects the proposition:

> structural pre-screening can be treated as an exhaustive detector of Reality Bias.

Instead, the evidence supports a layered role separation:

### Structural layer

Use structure to:

- preserve chronology;
- expose addressable state;
- trace reads/writes;
- nominate broad candidate regions;
- reduce audit cost.

### Semantic layer

Use complete-trajectory semantic review to decide:

- whether uncertainty was preserved;
- whether operational permission increased;
- whether process scope exceeded the authorized goal;
- whether historical process was regenerated;
- whether one dimension drove another.

This yields a stronger methodological statement:

> **Structural scouting is a recall-oriented localization layer, not the semantic verdict layer.**

And a second statement:

> **The primary failure risk is not necessarily loss of structural evidence; it can be a structurally narrow selector that encodes the wrong semantic proxy.**

The P selector demonstrates this directly: first activation of a new Agent captures only 4/13 later P-supported trajectories because scope expansion can be carried by already-active Agents.

The R selector demonstrates the same point more mildly: reviewer-boundary re-entry captures 9/12 later R-supported trajectories but misses natural late-event reopening.

---

# 7. Repository-integrity finding

The first CI attack also found that the repository copy:

`results/r8_trajectory_first_second_audit_v0_1/trajectory_second_audit_records.jsonl.gz`

is not byte-identical to its frozen manifest.

Current repository object:

- size: 14,999 bytes;
- SHA-256: `c047ae222f6bd4a58e57c109d9c573b0180e0fa3ea5c48ad4f49857098deb508`;
- gzip readable: false.

Frozen manifest declares:

- compressed SHA-256: `d8e51328f23ff6619fef5dce37f5768de319d16c3be0e7b478d27c7b614d9957`;
- uncompressed SHA-256: `f4b1ee053d47fb3fe5b681831acd37469549af0f741660b81e28fb0df54f3e61`;
- uncompressed size: 629,892 bytes.

A previously frozen external package was recovered and verified:

`r8_second_audit_with_ecommerce_discovery_v0_2.zip`

Package SHA-256:

`cf4d3d8158cc1bbd76649e6f236217283c4f5b3a33d3531ae400325141b44966`.

Its internal R8 record file is:

- gzip size: 90,834 bytes;
- compressed SHA-256: `d8e51328f23ff6619fef5dce37f5768de319d16c3be0e7b478d27c7b614d9957`;
- gzip readable: true;
- uncompressed size: 629,892 bytes;
- uncompressed SHA-256: `f4b1ee053d47fb3fe5b681831acd37469549af0f741660b81e28fb0df54f3e61`;
- JSONL records: 141.

The recovered copy exactly matches the frozen manifest hashes.

The current repository object must **not** be silently overwritten. P6 should append a recovered canonical copy and mark the current object as a repository-ingest integrity defect.

---

# 8. Manuscript defence

A concise Methods/Limitations defence can now state:

> Structural candidates were used for localization, not as semantic verdicts. In a retrospective calibration on the same 90 held-out natural trajectories, an earlier narrow structural high-risk selector captured 10 of 13 trajectories later supported for Dynamic P and/or R by complete-trajectory review (76.9%), missing 3 (23.1%). The misses were not absent from the broader structural records: deterministic triage packets preserved post-late-event evidence in all 13 later-supported trajectories. This calibration motivated the final trajectory-first audit and prevents us from claiming that structural pre-screening is exhaustive.

The percentages are conditional calibration values for this selector and frozen cohort, not estimates of CPR prevalence.

---

# 9. P4 verdict

Attack:

**“Structural pre-screening may omit semantically important trajectories.”**

Verdict:

**SUPPORTED AS A REAL RISK / QUANTIFIED FOR THE EARLIER NARROW SELECTOR.**

Calibrated result:

- narrow B2 union selector conditional capture: **76.92%**;
- conditional miss: **23.08%**;
- P-specific selector miss: **69.23%**;
- R-specific selector miss: **25.00%**;
- broad triage post-late evidence-preservation proxy: **100% (13/13)**.

Scientific consequence:

> The paper must never present the structural scout as exhaustive. The full-trajectory semantic audit is methodologically necessary, not decorative.
