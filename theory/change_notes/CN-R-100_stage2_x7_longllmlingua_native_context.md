# CN-R-100 — Stage-II X7 official LongLLMLingua boundary verification

Date: 2026-09-25

X7 has crossed the v7 native-runner engineering gate without collecting a natural trajectory.

The frozen software-engineering host still owns roles, scheduling, mailbox communication and checkout actions. X7 changes only the historical model context and uses the official `microsoft/LLMLingua` source at commit `5a4c78ae18ab17a98cf997e8259354e546081d64`, package version `0.2.2`, through `PromptCompressor.compress_prompt`.

The compression call preserves the previously frozen X7 semantics: `rate=0.5`, task request supplied as the LongLLMLingua question, and `rank_method="longllmlingua"`. Only serialized inbox/tool-history context is compressed; user request, role identity and action contract remain intact.

Workflow `36132656916` passed on candidate commit `f73b11b1f7136917cd47052c88a296c7b5d9fae5` using a deterministic six-file tiny local checkpoint constructed only for non-study engineering verification. The direct and X7 scripted T3 runs both finalized in one turn with identical checkout effects. One official compression call was observed; the post-return observer sealed immutable input/output copies. The smoke reported 79 origin tokens and 135 output tokens, which is intentionally not treated as a performance result because the synthetic checkpoint exists only to exercise the native code path.

X7 is therefore `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING`, not `SUBJECT_READY`. A separate study checkpoint directory plus exact file-hash manifest is still required, as is the real-provider readiness gate. Stage-II natural trajectory count remains zero.
