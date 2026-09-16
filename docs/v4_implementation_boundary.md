# v4 Implementation Boundary

Date: 2026-09-16

The current v4 update adds theory, measurement interfaces, registries and offline validation scaffolding. It intentionally does not yet rewrite the live Arena runtime event format.

Runtime integration should occur through source-version-specific adapters so frozen raw traces remain unchanged.