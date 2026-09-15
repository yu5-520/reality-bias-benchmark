# CN-R2-018 — Arena evidence integrity repair

Supersedes Arena v0.1 engineering readiness, not the frozen primary R2 scientific evidence.

The state transport discarded evidential status/basis; evaluator input omitted communication
and actual per-turn visibility; missing codes passed validation; consecutive finalize actions
could terminate before a late signal was read; counterfactual replay counted failed actions
as realized. These are environment/measurement defects, not observations of model Bias.

v0.1.1 preserves metadata, logs actual inputs, requires complete typed coding, ends each
response at finalize, reserves next-turn late-event delivery, respects queue delivery failures,
and separates baseline failures from realized/blocked replay events. Analysis counts only
realized unauthorized mechanism-coded events. Seven offline regression cases pass.

No subject or evaluator API was called. Four domains and free collaborator selection remain.
Complexity/information/pool-size randomized experiments remain future work. The existing
R2 mechanism/Authority separation and immediate-containment interpretation are unchanged.
