# Correction: repair method was not ready when the diagnostic trial ran

The user correctly identified a design mismatch. The enhanced monitor's complete node graph was supposed to become the input to an overall route repair plan. The implemented terminal trial instead placed graph queries ahead of a legacy local process-revision executor. It narrowed the scope to the terminal account and preserved all application files, then retained the old continuation monitor and a post-action delta. A complete repair plan, native multi-node executor and enhanced post-repair graph did not exist.

The 21 calls are reclassified as a premature diagnostic-harness trial. All raw records and exact execution source remain available. No native repair action occurred, so these outcomes cannot test whether the intended new repair method works. The previous focus on archive-path usability was incomplete: path mapping was a prerequisite failure inside a larger method-design failure.

Corrective actions:

- Disable the old live CLI and provider builder; replace its workflow with offline preparation and historical validation.
- Preserve frozen code hashes in a separate historical source snapshot, without rewriting old requests, responses or results.
- Make the complete-node repair design and missing readiness gates machine-readable.
- Implement a read-only complete graph context with exact current/historical application source mappings and clock-qualified observations.
- Require route diagnosis → coordinated plan → native plan execution → enhanced monitoring → full post-repair graph comparison before a new experiment is frozen.

Offline source preparation verifies 1,194 MCP nodes and 224 A2A nodes, with 12 and 14 terminal file mappings and 456 and 26 captured checkpoint file versions respectively. The MCP app.js file versions expose the actual change at checkpoint-ledger model decision 10; this is captured evidence, not a conclusion supplied by an audit. A historical structural eligibility annotation is kept distinct from the native checkpoint event it references.

No new model calls or repairs were made during this correction. Twenty-five tests passed, including current/historical source lookup, checksum rejection, annotation separation, and blocking live execution before output/source access. The old 39 queries and 21 model request/response pairs still reproduce from sealed data and archived execution source.

The next unimplemented component is source-grounded route diagnosis and the coordinated plan contract. The system is explicitly not ready for live route repair. [Replacement design](../protocols/StageII_Complete_Node_Route_Repair_Design.md).
