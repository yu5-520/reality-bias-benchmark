# Stage-II X4 MCP native attachment — R Plan v7.3

Date: 2026-09-25. Status: **X4 NATIVE RUNNER VERIFIED; SUBJECT GATE CLOSED; ZERO NATURAL TRAJECTORIES**.

v7.3 continues the v7.2 architecture without changing T1–T3, the nine Software Engineering roles, the frozen checkout, the DeepSeek subject profile, the X definitions, or the one-natural-trajectory-per-cell rule.

## 1. X4 stays a tool/resource protocol condition

X4 does not become a scheduler. The frozen `software_engineering_host_v1` keeps the role queue, mailbox and action semantics, while the checkout operations cross the official frozen MCP client/server boundary.

The X4 implementation is probe-specific:

- `stage2/native_v7/x4_mcp/server.py` exposes the frozen bounded checkout operations through the official MCP server;
- `client_call.py` uses the official MCP `ClientSession` over stdio;
- `runner.py` attaches that MCP boundary to `software_engineering_host_v1`;
- no historical `stage2.mcp_workspace`, `CodingArena` or `RoleMailboxTransport` adapter is used by the X4 runner.

Other X systems are not required to implement the X4 attachment interface.

## 2. Exact wire observation is external

The MCP SDK owns protocol serialization. `wire_proxy.py` is a transparent stdio relay between the official client and official server. It copies the exact client-to-server and server-to-client newline-delimited protocol bytes to the observer directory while forwarding the same bytes.

The relay does not parse or synthesize agent decisions, does not rewrite MCP messages, and is outside the checkout. Process-boundary observation remains outside the X4 child runner.

## 3. Non-study verification

Workflow `36130515655` on candidate commit `7db8159c22c1616f2cb45c8fb230b7ea88e2369a` installed the exact frozen MCP Python SDK commit `f1b6589088534632fef92238ee9750951e3c0185` and protocol source commit `5f5440bb26a62e2cf3440b92da5a667efa03b267`.

The scripted T2 smoke compared the direct de-instrumented host with the MCP-attached host. Both reached `finalized` in seven turns with the same checkout effects. X4 crossed four MCP tool calls and preserved four client-to-server plus four server-to-client raw wire captures. Final checkout digest: `b0a9d3ec7846f204bbe72062aa062358a9174d7bd66fb1908aa43c4c15087ba3`.

This is an engineering gate only. No paid subject model was called.

## 4. Forward state

X1 and X4 are now `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING`. X2, X3, X5, X6 and X7 remain `PENDING_NATIVE_RUNNER`.

No natural cell is open. X4 must still pass a real-provider subject-readiness check on the exact forward execution commit before any X4–T1/T2/T3 cell can be reserved.

Stage-II natural trajectory count remains **zero**.
