# R1 — Theory Stress Test Report
## Reality Bias × Authority Penetration

**Case count:** 42  
**Synthetic counterexamples:** 34  
**Literature-derived stress patterns:** 8

### Internal adjudication summary
- CLEAR under the contract: **32/42**
- BOUNDARY but explainable with explicit rule: **7/42**
- CONTRACT_THREAT found: **3/42**

> These counts are conceptual stress-test counts, not statistical evidence and not inter-annotator agreement.

## Main finding

R1 found one genuine structural defect in `theory_contract_R0_v0.1`:

> **Authority class cannot be used as a direct proxy for Bias class.**

The v0.1 Step-D rule risked turning generic Information/Invocation/Temporal authorization failures into C/P/R, which would collapse Reality Bias into a broad agent-safety taxonomy.

Three decisive counterexamples were:
- **P04:** wrong action inside a fixed authorized graph;
- **S01:** prompt-injection-induced unauthorized action without completeness-driven expansion;
- **S05:** risky wrong-recipient tool action without scope expansion.

All can involve tool/action risk, and some can involve authorization failure, but none necessarily satisfy the Perfection mechanism.

This triggered **CN-R1-001**, which was accepted.

## Post-patch theory state

The revised contract now requires two independent conditions for a realized C/P/R label:

1. invalid Authority transition; and
2. corresponding Bias mechanism.

This preserves the proposed primary mapping while preventing overreach:

`C mechanism + invalid I promotion → C`  
`P mechanism + invalid V expansion → P`  
`R mechanism + invalid T reopening → R`

Generic authorization failures remain outside the taxonomy unless the Bias mechanism is present.

## Stress question results

### Q1 — Is there an obvious fourth Reality dimension?
**Current result: no.**

The 42-case set did not force a fourth system-reality target beyond:
- fact/context,
- invocation/action graph,
- historical/task state.

However, this does not prove exhaustiveness. V26 traces and future domains could still reveal a fourth target.

### Q2 — Do Information and Invocation always co-occur?
**No.**

Cases P01/P05/S06 show invocation expansion without prior factual promotion.  
Cases C01/C03/C05 show informational completion without invocation expansion.  
T01/A02 show they can also occur sequentially as C→P.

This supports keeping I and V separate.

### Q3 — Is Temporal merely an Invocation consequence?
**No under the current contract.**

R01/R04/A04 realize temporal reopening directly through history/state mutation.  
No new Agent/tool is required for R to occur.

This supports retaining T as an independent Authority class.

### Q4 — Can Generation and Realization be separated?
**Yes conceptually.**

C05 and G04 are explicit generation-only cases.  
C01/R01/P01 are realized cases.

The distinction is therefore operationally meaningful, but R2 instrumentation must prove it can be measured reliably in actual runs.

### Q5 — Can single-gate controls plausibly displace risk?
**Yes as a falsifiable mechanism.**

A05: I gate can induce a V workaround.  
A06: V gate can induce an I workaround.

These are synthetic counterexamples, not evidence that displacement occurs in real runs. They justify keeping the R5 hypothesis test.

## Transition-system result

The stress set supports preserving the full 3×3 transition matrix rather than hard-coding only the ring:
- core hypotheses: C→P, P→R, R→C;
- plausible exploratory paths: C→R, P→C, R→P.

Therefore the `C→P→R→C` loop remains a **specific emergence hypothesis**, not a definitional assumption.

## External-security boundary

AgentDojo-style prompt injection, ToolEmu-style risky tool use, and memory-poisoning literature create important adjacent cases.

R1 conclusion:
- external malicious state is not automatically Reality Bias;
- risky action is not automatically Perfection Bias;
- memory persistence is not automatically Completion or Retrospective Bias;
- these become Reality Bias only when the model itself performs the relevant probabilistic promotion/expansion/reopen mechanism.

This boundary materially strengthens discriminant validity.

## What R1 did not establish

- No independent human/second-researcher inter-annotator agreement was measured.
- No V26 raw execution trace bundle was ingested in this pass.
- No API model runs were performed.
- No empirical prevalence or effect size is claimed.
- Literature-derived cases are stress patterns, not reproductions of each paper's benchmark items.

## R1 recommendation

**PROCEED, WITH PATCH.**

The three-dimensional model survives conceptual counterexample pressure after CN-R1-001.

The theory is sufficiently discriminant to design R2, but before a formal large run:
1. import real V26 traces when available;
2. conduct an independent annotation pass over a blinded subset;
3. freeze the patched v0.2 contract for R2.

R2 should now test whether the theoretically distinct pathways produce **selective intervention effects**, rather than assuming the distinction from labels.
