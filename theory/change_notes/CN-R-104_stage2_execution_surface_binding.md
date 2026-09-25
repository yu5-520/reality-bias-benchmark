# CN-R-104 — Per-probe execution-surface binding before live Stage-II readiness

Date: 2026-09-25

The Stage-II subject-readiness gate now binds each potentially promoted X to a content-addressed execution surface rather than assuming the later control-plane promotion commit has the same Git SHA as the paid readiness run.

The per-probe digest covers the common DeepSeek adapter/provider/config, frozen task/role/subject inputs, collection and observation boundary, fixture tree, the selected X runner/helper files, and immutable upstream/source/SDK refs plus launch argv. Mutable authorization fields are excluded.

A common provider receipt may therefore be followed by a reviewed metadata-only `SUBJECT_READY` commit without weakening provenance: natural collection recomputes the probe digest before creating a cell directory and refuses execution if the scientific surface changed.

This change performs no provider call and opens no natural cell by itself.
