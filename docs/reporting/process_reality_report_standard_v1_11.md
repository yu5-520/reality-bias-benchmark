# Process Reality Report Standard v1.11

Date: 2026-09-26  
Status: **FORWARD ACTIVE / DUAL GENERAL-CHAPTER GOVERNANCE**  
Predecessor: `RB-PROCESS-REALITY-REPORT-STANDARD-v1.10`

Historical reports remain immutable.

This version retains v1.10 and adds two peer normative parent chapters plus principle-ID citation requirements for G2-G5.

## 1. Dual parent chapters

### Experimental parent

`docs/reports/2026-09-26/StageII_Experimental_General_Chapter_Process_Reality_Methodology_and_Principles_v2.md`

Registry:

`configs/stage2_experimental_general_principles_v2.json`

### Engineering parent

`docs/reports/2026-09-26/StageII_Engineering_General_Chapter_Process_Integrity_Monitoring_and_Repair_v1.md`

Registry:

`configs/stage2_engineering_general_principles_v1.json`

The parents are peers.

Experimental reports use EXP-* principles. Engineering reports use ENG-* principles. Mixed reports must state which rule source governs each section.

---

## 2. Required principle references

Every forward G2-G5 report must include a machine-readable or tabular principle reference section.

At minimum it lists:

- adopted EXP-* IDs;
- adopted ENG-* IDs where engineering evidence is present;
- any principle intentionally not applicable;
- any deviation, with prospective protocol-version justification.

A report may not replace a substantive explanation with an ID alone. The ID provides provenance to the governing rule.

---

## 3. Experimental child-report requirements

Every natural/semantic G2-G5 report includes:

### Relation to Experimental General Chapter

1. group ID;
2. 21-cell population accounting;
3. exact launch/horizon version;
4. adopted EXP-* IDs;
5. termination-class accounting;
6. complete-route evidence;
7. semantic lineage evidence;
8. negative evidence;
9. hypotheses/CPR structures informed;
10. explicit non-claims.

---

## 4. Engineering child-report requirements

Every monitor/repair G2-G5 report includes:

### Relation to Engineering General Chapter

1. group/cell ID;
2. adopted ENG-* IDs;
3. observed surfaces and coverage;
4. warning/candidate source;
5. lineage localization;
6. checkpoint class;
7. parent freshness;
8. repair eligibility;
9. immutable package ID if B exists;
10. repair-boundary watcher result;
11. post-repair watch result;
12. preserve-set audit;
13. terminal outcome separately;
14. explicit non-claims.

---

## 5. Natural membership versus repair eligibility

Every forward publication-facing table must keep these populations separate:

- natural observation population;
- repair-eligibility population;
- active intervention population.

For G2-G5:

`natural observation population = 21 cells/group`.

All 21 enter repair eligibility accounting.

The active intervention population is a legal subset and may be <=15 under the current X1/X3 native-preservation boundary.

Do not label X1/X3 as missing merely because they do not enter active B.

---

## 6. Termination reporting

Forward reports may not use a single generic “failed” field when source evidence distinguishes the stop.

At minimum report:

- natural terminal closure;
- horizon-censored non-closure;
- provider/transport failure;
- framework/runner exception;
- measurement-interface artifact;
- other source-bound termination.

Task outcome and termination cause must be separately visible.

---

## 7. Horizon reporting

G1's historical 32-turn boundary is retained as historical evidence.

G2-G5 target 64 logical model decisions after wrapper-equivalence validation.

A horizon-censored trajectory must not be reported as framework failure without independent evidence of framework failure.

---

## 8. G1 use in forward reports

G1 may be used as:

- discovery evidence;
- calibration evidence;
- historical comparison;
- source of protocol-design lessons.

G1 T1 X2-X7 must carry the interface-dominated caveat.

G1 X4-T2 and X6-T2 must carry the provider-format-failure caveat.

---

## 9. Anti-circularity remains active

General Chapter principle IDs define rules and interpretations.

They do not prove a child report's empirical claim.

Every empirical claim still binds source evidence.

---

## 10. Evidence chain

Experimental:

`Frozen Natural Evidence -> Complete Route -> Semantic Lineage -> Node/Edge Audit -> Group Comparison -> Claim Boundary`.

Engineering:

`Raw Evidence -> Monitor Candidate -> Lineage Localization -> Checkpoint -> Eligibility -> Repair Package -> Boundary Watch -> B Continuation -> Post-repair Audit -> Claim Boundary`.

---

## 11. Authorization boundary

This standard authorizes no subject/provider call, active repair, paid evaluator, or natural rerun.

It governs reporting and evidence structure only.
