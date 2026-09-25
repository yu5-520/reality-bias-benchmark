# CN-R-096 — Stage-II X1 AutoGen native runner verification

Date: 2026-09-25

X1 has crossed the first v7 engineering gate without collecting a natural trajectory.

The frozen AutoGen source commit `027ecf0a379bcc1d09956d46d12d44a3ad9cee14` was installed from upstream and the probe-specific runner used AutoGen AgentChat `AssistantAgent`, `Swarm`, native handoffs and native tool calls. The non-study smoke completed the handoff/tool/return path with AutoGen's upstream replay client and preserved an isolated checkout change. The passive event observer returned the exact event bytes it received and only wrote content-addressed copies.

The passing smoke is recorded as workflow run `36127178838` on code commit `c2365939e738b95ee24061020be227c48b03744a`.

This does **not** authorize X1 subject collection. X1 is now `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING`. A real-provider readiness check on the exact forward execution commit remains required before any X1–T1/T2/T3 cell can be reserved.

The integration rule is also sharpened: X1/X2 are multi-agent framework conditions, X3 is an inter-agent protocol condition, and X4–X7 attach at their natural capability boundaries. No requirement is introduced that MCP, RAG, MemoryBank or LongLLMLingua behave as schedulers merely to fit a common experiment interface.
