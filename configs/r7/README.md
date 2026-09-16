# R7 execution fixtures

This directory contains frozen, inspectable fixtures for the three-arm R7 protocol. Fixtures must preserve the semantic correction payload across arms and vary only propagation/recovery structure.

Planned arm labels:
- `C1_ONE_SHOT`
- `C2_PERSISTENT_FIELD`
- `C3_ALR`

No paid model call should be launched from a fixture that has not passed the offline integrity validator.
