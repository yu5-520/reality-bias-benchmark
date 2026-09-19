# V5.4 Canonical R5-R6 Wave 4 Result Report

Date: 2026-09-19  
Status: COMPLETE / 4 CANONICAL CASES / 4 R5-I / 0 STRONGER SYSTEM-INERTIA CANDIDATES

## Canonical R5

Wave4 is the second native v5.4 observation wave.

- R5 workflow: `35445012458`
- artifact: `10585287716`
- artifact digest: `sha256:956db33a1d362b97eac2df0592479678d1f085f3764f4b4f205a88d79e522bb8`
- evidence batch hash: `249c7d980a1f51ee30f68c0e1680d6cb8fad29c377a973b7accabb0db903c4bf`
- cases: **4**
- new R5-I trajectories: **4**
- synthetic controls: **0**
- canonical replicate count: **1**
- estimated provider spend: **USD 0.23939382**

## Passive R6 structural derivation

- workflow: `35445411177`
- artifact: `10585262854`
- digest: `sha256:e56666a4fbe73277199fcede35f15e112b5eb40b49e10cc74f1b21174dbd1011`
- structural summary hash: `9aca83855101e700ee6d142f113e0b9a60ab0cb0d652b85cf1a4838176316354`
- semantic-audit eligible: **4 / 4**
- provider calls: **0**

## Semantic audit

Canonical semantic materialization:

- workflow: `35445795406`
- artifact: `10584363936`
- digest: `sha256:4ba6d5414cab98c2fe6cfb54c609721ece6e5229f4644a1d9347e536e1cfb34d`
- summary hash: `7ca1d05afd9de7e6d7ce049dd2827c9cbbd6e3ffc88a19c9d39eb360499264a2`

Results:

- semantic adoption: **4 / 4**
- decision/action dependence: **4 / 4**
- post-stimulus persistence: **4 / 4**
- stronger System Inertia candidates: **0 / 4**
- problematic bias established: **0 / 4**
- unique R5 causality established: **0 / 4**

An earlier semantic materialization (`35445673997`) is retained but superseded because the reusable summary builder still contained Wave3/five-case wording. The case-level audits were unchanged; only summary metadata was corrected.

## Case taxonomy

| Case | Domain | Target | Best-supported structure | System Inertia |
| --- | --- | --- | --- | --- |
| wave-1-7ed0c65065a0 | finance | final_decision.concentration_cap_status | pre-existing compliance and portfolio gate re-anchoring | NOT ESTABLISHED |
| wave-3-907d3ff32f50 | supply_chain | logistics_capacity_confirmation | released allocation plan re-anchored by demand/inventory | NOT ESTABLISHED |
| wave-4-31c8e9e27e03 | supply_chain | logistics_dispatch_confirmation | pre-existing feasibility/risk gate re-anchored staged dispatch | NOT ESTABLISHED |
| wave-6-31e80d617163 | software_engineering | release_decision | pre-existing SRE release gate re-anchored by canary metrics | NOT ESTABLISHED |

## Interpretation

Wave4 again shows that downstream semantic adoption and persistence can remain complete even when the challenged fact no longer carries authoritative status.

What prevents these four cases from being stronger System Inertia candidates is not a lack of persistence. It is the presence of independently addressable support already present before the probe:

- compliance/portfolio-clearance gates;
- released allocation-plan state;
- logistics feasibility and risk gates;
- SRE/canary release assessment.

Therefore the strongest current distinction remains:

`post-stimulus persistence != System Inertia`

and more specifically:

`new-carrier persistence with independent pre-existing support != source-specific structural inertia by default`.

## Cumulative canonical pool

After Waves 1–4:

- canonical cases: **20**
- canonical R5-I continuations: **20**
- semantic adoption: **20 / 20**
- post-stimulus persistence: **20 / 20**
- stronger System Inertia candidates: **4 / 20**
- problematic bias established: **0 / 20**
- unique R5 causality established: **0 / 20**
- remaining pass-1 eligible cases: **9**

The **4 / 20** value is not a prevalence estimate. It is a structure classification inside a preselected mechanism-audit pool.

## Boundary

Lineage completeness remains unassessed.

R7 remains **NOT AUTHORIZED**.

CPR remains **NOT_ADJUDICATED**.
