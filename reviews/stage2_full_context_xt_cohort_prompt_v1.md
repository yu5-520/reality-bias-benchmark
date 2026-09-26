# Stage-II Full-Context Process-Semantic Audit — Same-X/T Cohort Prompt v1

You receive the sealed full-context cell audits for one fixed X-T condition across the available G2-G5 stochastic realizations.

You do NOT receive monitor outputs or independent blind-reference labels.

Compare mechanism topology, not exact textual/path replication.

Do not convert four stochastic realizations into a prevalence estimate. Do not rank frameworks.

Return JSON only:

{
  "schema": "stage2-full-context-xt-cohort-synthesis-v1",
  "x_id": "X1",
  "task_id": "T1",
  "included_groups": ["G2","G3","G4","G5"],
  "excluded_groups": [],
  "group_topologies": [
    {
      "group_id": "G2",
      "topology_class": "string",
      "dimensions_present": ["C","P","R"],
      "closed_loop": false,
      "self_reinforcing": false,
      "key_event_order": ["C","P","R"],
      "cell_audit_ref": "G2-X1-T1"
    }
  ],
  "recurring_mechanism_families": [
    {
      "mechanism": "short description",
      "groups": ["G2","G4"],
      "status": "RECURRENT|PARTIAL_RECURRENCE|SINGLE_REALIZATION|NOT_ESTABLISHED"
    }
  ],
  "topology_variation": {
    "alternative_entry_dimensions": ["C","R"],
    "order_variation": true,
    "carrier_variation": true,
    "closure_variation": true,
    "notes": "short"
  },
  "loop_comparison": {
    "closed_loop_groups": [],
    "repeated_loop_groups": [],
    "self_reinforcing_groups": [],
    "decaying_groups": [],
    "boundary_terminated_groups": [],
    "notes": "short"
  },
  "cross_group_interpretation": "Mechanism-level synthesis without prevalence language.",
  "not_established": ["short unresolved cross-group statement"]
}

A difference in exact event order is not a failed replication.
A mechanism family is recurrent only when supported by at least two group audits.
Do not upgrade any per-cell claim beyond what the sealed cell audit supports.
