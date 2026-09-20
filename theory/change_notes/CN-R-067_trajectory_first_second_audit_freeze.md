# CN-R-067 — Trajectory-First Second Audit Freeze

Date: 2026-09-20
Status: ACCEPTED / APPEND-ONLY

Freeze the 141-trajectory trajectory-first Dynamic CPR second audit.

Results: C high-confidence anchors=2, P supported=19, retrospective-generative R supported=13; C_DRIVES_P=2, R_GENERATES_P=13, P_REINFORCES_C remains candidate in 2 episodes.

69 active-censored trajectories retain positive-prefix evidence and prohibit negative-tail claims.

The complete per-trajectory adjudications are stored as compressed JSONL and content-addressed in the result manifest. No subject rerun, provider call, paid evaluator call or raw-evidence mutation occurred.