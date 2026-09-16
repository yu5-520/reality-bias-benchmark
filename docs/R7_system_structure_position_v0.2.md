# R7 System Structure Position v0.2

Date: 2026-09-16  
Status: FORWARD CANDIDATE

## 1. Repositioning

R7 is the system-structure / boundary-condition layer, not merely a late-stage Free-vs-Structured comparison.

Relevant variables include:

- routing ownership;
- topology density;
- stage boundary placement;
- context continuity/reset/compression;
- dynamic invocation surface;
- proposal/commit separation;
- Agent count;
- shared-state visibility.

## 2. Existing v0.1 comparison

The existing conditions remain preserved:

- Emergent / Free Routing;
- Structured / System-Owned Routing.

Their current offline comparison remains engineering-only because fixture scripts differ and the v0.1 design contains multiple orchestration differences.

## 3. Forward role

R7 asks how system structure changes:

- first-Jump location;
- Jump type distribution;
- propagation topology;
- operational-boundary crossings;
- penetration criteria;
- post-Jump inertia;
- recovery distance/cost.

It does not ask which architecture is universally “better”.

## 4. Relationship to R5/R6

R5, R6 and R7 are sibling experimental directions over the common R2–R4 behavior evidence layer.

They do not require strict execution order:

```text
R2/R3/R4 common observation layer
        ├── R5 causal manipulation
        ├── R6 recovery / recurrence
        └── R7 system-structure conditions
```

## 5. Registry binding

Forward R7 conditions should bind `ORCHESTRATION_STRUCTURE` or later system-structure variables in:

`configs/experimental_variable_registry_v0.1.json`

and use registered measurement boundaries where applicable.

## 6. Paid-run boundary

Existing exact R7 real-run authorization remains:

`CALL_REAL_R7_API`

This document authorizes no provider call.