# CN-R-098 — Stage-II X4 official MCP stdio attachment verification

Date: 2026-09-25

X4 has crossed the v7 native-runner engineering gate without collecting a natural trajectory.

The capability-layer background substrate remains `software_engineering_host_v1`. X4 changes only the checkout tool boundary: the host invokes an official MCP `ClientSession`, which communicates over stdio with an official MCP server exposing the frozen bounded checkout operations. MCP is not used as the role scheduler and no frozen upstream MCP source is modified.

A transparent stdio relay preserves byte-identical client-to-server and server-to-client protocol traffic outside the checkout. It does not parse decisions or rewrite protocol messages.

The non-study T2 smoke passed in workflow `36130515655` on candidate commit `7db8159c22c1616f2cb45c8fb230b7ea88e2369a`: seven turns, four MCP tool calls, four bidirectional wire-capture pairs, final status `finalized`, and checkout digest `b0a9d3ec7846f204bbe72062aa062358a9174d7bd66fb1908aa43c4c15087ba3`.

X4 is therefore `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING`, not `SUBJECT_READY`. The real-provider gate remains closed and the Stage-II natural trajectory count remains zero.
