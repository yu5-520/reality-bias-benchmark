# Behavior Event v0.1 Notes

Date: 2026-09-16

`RB-BEHAVIOR-EVENT-v0.1` is a derived structural record, not a replacement for raw Arena trace/journal evidence.

Rules:

1. retain source trace/journal immutable;
2. behavior event must point back to source refs where possible;
3. unknown semantic meaning remains `NOT_ADJUDICATED`;
4. proposal/realized/blocked/failed states stay distinct;
5. missing source-version data is not invented;
6. adapters are source-version-specific when event shapes differ.