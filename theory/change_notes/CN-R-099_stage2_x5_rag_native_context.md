# CN-R-099 — Stage-II X5 frozen RAG context attachment verification

Date: 2026-09-25

X5 has crossed the v7 native-runner engineering gate without collecting a natural trajectory.

The frozen software-engineering host remains responsible for roles, scheduling, mailbox communication and checkout actions. X5 changes only the retrieval/context boundary. It calls the frozen `stage2.retrieval.retrieve` implementation (SHA-256 `baf19cd7f7dde0a2f7ebfde254bffac6690e018b88d8d9ea4a811d37a53b12c4`) over the frozen fixture corpus and exposes the ranked hits as `retrieved_context` to the current role.

The v6 `RAGContext` capture machinery is not reused. The v7 attachment checks frozen corpus hashes and uses a passive observer only after retrieval has returned, copying the query/result serialization without feeding observation data back into ranking or prompt construction.

The non-study T3 smoke passed in workflow `36131773869` on candidate commit `c8db6e1b3188de7b05e6bfb521aa2a148aa9596e`: one turn, one retrieval call, three ranked hits, identical scripted control result and checkout effects relative to the direct host, and checkout digest `15200a4ce5b6a09127f25371b55d9b4ae3b1f2071af78c3a7f37b6fcad8303e2`.

X5 is therefore `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING`, not `SUBJECT_READY`. The real-provider gate remains closed and the Stage-II natural trajectory count remains zero.
