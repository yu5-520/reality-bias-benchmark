# CN-R-101 — Stage-II X3 native A2A nine-role service verification

Date: 2026-09-25

X3 has crossed the v7 native-runner engineering gate without collecting a natural trajectory.

Unlike capability-layer X4–X7, X3 does not inherit the frozen baseline software-engineering host. All nine frozen Software Engineering roles are independently exposed as official A2A v1.0 services. The launcher submits only the initial task to `release_lead`; subsequent inter-role delegation is initiated from inside the role services through official A2A `SendMessage` calls and returned Task/Artifact objects.

This removes the main v6 ambiguity: A2A is no longer a transport wrapper around `CodingArena` or `RoleMailboxTransport`. The old `stage2.a2a_transport` remains historical provenance only.

External observation is implemented as a separate transparent HTTP-body relay in front of each role service. The relay copies Agent Card and JSON-RPC request/response bodies while forwarding the same bodies to/from the official service backend. It does not decide actions, schedule roles, or synthesize protocol objects.

Workflow `36134380842` passed on candidate commit `ba8b71cd7450007751432df3a54d6e3c62db96b6`: nine role services, seven scripted model turns, three A2A task calls, three captured JSON-RPC requests, three captured task/artifact responses, twelve observed Agent Card responses, `finalized` terminal state, and checkout digest `15200a4ce5b6a09127f25371b55d9b4ae3b1f2071af78c3a7f37b6fcad8303e2`.

X3 is therefore `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING`, not `SUBJECT_READY`. Stage-II natural trajectory count remains zero.
