# CN-R-057 — Root-Scoped Canonical Topology

Date: 2026-09-17

## Problem

The v0.2 derivation correctly fixed source-Arena-event to BehaviorEvent root binding, but two forward-analysis risks remained:

1. path signatures could inherit per-run identifiers from final-state/message/invocation/turn targets, creating false A/B topology differences;
2. cross-actor counts over all post-branch relations could mix unrelated activity with selected-Jump inherited inertia.

## Decision

Measurement v0.3 separates two graph scopes:

- **root-descendant topology** — only source-backed lineage descending from the selected natural Jump and entering the post-branch continuation; this is the mechanism/inertia scope;
- **full-post context topology** — all post-branch structural activity, retained only as context diagnostics.

Canonical signatures preserve stable role/interface structure while removing run/event/message/invocation/turn identity. Shared-state keys and target Agent roles remain because they are stable structural interfaces.

## Interpretation boundary

A cross-actor source-backed relation is a mechanical structural relation. It is not, by itself, semantic responsibility transfer, authority penetration or CPR-positive evidence.

## Provenance

v0.1 and v0.2 derived artifacts remain immutable. v0.3 is a new deterministic derivation over the same frozen raw evidence and requires no subject-provider or evaluator call.
