# CN-R-040 — R3 Structural Compaction v0.2

Date: 2026-09-15  
Status: **PASS — R3 DOWNSTREAM CONTEXT DEDUP VALIDATED**

## Decision

Reviewer-v2 R3 packets may use the `R234-REVIEWER-V2-R3-COMPACT-PACKET-v0.2` representation as a lower-volume semantic-review interface.

The v0.2 change is structural deduplication only. It does not alter:

- the frozen subject trace;
- R2 candidate selection;
- machine lineage relations;
- the target candidate;
- the target Agent call;
- Reviewer boundary fields;
- the one-ref bounded context-expansion contract;
- historical Reviewer A/B records.

## Why this optimization was added

The provider-independent volume profile showed that R3 dominates the compact review material. Under compact v0.1, the 70 R3 packets occupied `4,307,878` serialized bytes and the upper tail was driven by repeated downstream-call context.

Repeated state snapshots and output-action payloads are not themselves additional semantic evidence when the same structurally relevant target state and Agent output are already represented once.

## v0.2 structural rule

For downstream calls reached through `state_version_visible_in_input`:

- retain the structurally selected state value(s) and metadata;
- retain the full shared-state key list and state hash;
- retain Agent identity/role and active-Agent context;
- hash omitted private/inbox context;
- preserve the exact full call as an allowed bounded-expansion ref.

For downstream calls reached through `message_read_into_input`:

- retain inbox content because the machine lineage records a direct message-read path.

For downstream outputs:

- retain `decision_summary` and structured actions once;
- retain event refs, Authority class and realization metadata;
- do not duplicate the same action payload again in output-event metadata.

These rules depend only on machine structural relation type, not on C/P/R labels or reviewer outcomes.

## Validation

Workflow `34992079531` completed successfully.

- packet count: 70
- source compact-R3 bytes: `4,307,878`
- v0.2 bytes: `2,962,081`
- v0.2 fraction of v0.1: `68.76%`
- additional reduction: **31.24%**
- deterministic output hash: `b1abe2510bce774a3d9f5792aaa8353b60781090894c6ba0bade7d4f5955a765`
- artifact ID: `10406156673`
- artifact digest: `sha256:7f6aacd8c2330941b327510d819a159d52e67a9a05a7fb67348fbf4d771f5fc1`
- provider calls: 0

The CI gate verified that machine lineage, target candidate, target call, boundary fields and context-expansion contract are unchanged packet-by-packet.

## Interpretation boundary

The 31.24% reduction is serialized byte reduction only. It is not an exact provider-token reduction and is not a monetary-cost result.

If the reduced downstream context is insufficient for semantic adjudication, the Reviewer must return `UNCERTAIN` or request the existing one permitted frozen-ref expansion. The reviewer must not infer omitted evidence.

## Current gate

R3 context volume is no longer a reason to alter the subject experiment or semantic definitions. The current scientific gate remains the same: decide whether to authorize a paid semantic Reviewer-v2 pass over the frozen Base evidence.

No paid review and no K=2 subject run are authorized by this Change Note.
