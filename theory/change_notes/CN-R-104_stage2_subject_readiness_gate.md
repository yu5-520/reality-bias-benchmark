# CN-R-104 — Stage-II common subject-readiness gate

Date: 2026-09-25

After v7.8 verified all seven native runners, the remaining boundary is separated into provider readiness and scientific collection.

v7.9 adds a single manual, one-call provider handshake for the frozen common DeepSeek subject binding. The handshake uses no T1–T3 task, no checkout trajectory, no multi-agent execution and no evaluator. It records provider response/usage plus exact subject and model-config hashes, but cannot mutate the registry.

This is intentionally not repeated once per X. X1–X7 share one frozen subject binding; their different system execution paths were already established by their own native engineering smokes. Repeating the same connectivity check would create cost and sampling without a new system condition.

A handshake receipt still does not imply `SUBJECT_READY`. Promotion requires a reviewed commit carrying the receipt hash and exact execution/config identities. X6 and X7 remain additionally blocked until their real study embedding/compressor manifests are frozen and verified.

Natural trajectories remain zero.
