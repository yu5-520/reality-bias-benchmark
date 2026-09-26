# Stage-II R7 Monitor-Derived Package Assembly v1

Date: 2026-09-26  
Status: **STRUCTURAL EPISODES FROZEN / ACTIVE REPAIR NOT AUTHORIZED**

- raw structural candidates retained: **244**;
- structurally merged repair episodes/packages: **24**;
- cells represented by packages: **15/21**;
- repair gate counts: `{"LINEAGE_GAP_BLOCKED": 7, "NO_REPAIR_REQUIRED": 1, "PARENT_RECONSTRUCTION_BLOCKED": 16}`;
- semantic audit used in assembly: **NO**;
- case-specific package rule: **NO**.

Candidate rows are not discarded. Package assembly only merges structurally connected signals so R7 operates on pressure/support episodes rather than treating each repeated file, message or carrier observation as an independent repair experiment.

## Package accounting

| Package | Cell | Pressure refs | Support refs | Allowed surfaces | Gate |
| --- | --- | ---: | ---: | ---: | --- |
| X1-T1:monitor-episode:01:package:v1 | X1-T1 | 20 | 22 | 13 | PARENT_RECONSTRUCTION_BLOCKED |
| X1-T2:monitor-episode:01:package:v1 | X1-T2 | 7 | 7 | 3 | PARENT_RECONSTRUCTION_BLOCKED |
| X1-T2:monitor-episode:02:package:v1 | X1-T2 | 13 | 15 | 8 | PARENT_RECONSTRUCTION_BLOCKED |
| X1-T3:monitor-episode:01:package:v1 | X1-T3 | 14 | 19 | 12 | PARENT_RECONSTRUCTION_BLOCKED |
| X1-T3:monitor-episode:02:package:v1 | X1-T3 | 1 | 2 | 1 | PARENT_RECONSTRUCTION_BLOCKED |
| X2-T2:monitor-episode:01:package:v1 | X2-T2 | 1 | 2 | 1 | PARENT_RECONSTRUCTION_BLOCKED |
| X2-T2:monitor-episode:02:package:v1 | X2-T2 | 9 | 23 | 15 | PARENT_RECONSTRUCTION_BLOCKED |
| X2-T2:monitor-episode:03:package:v1 | X2-T2 | 2 | 2 | 1 | PARENT_RECONSTRUCTION_BLOCKED |
| X2-T2:monitor-episode:04:package:v1 | X2-T2 | 6 | 6 | 1 | PARENT_RECONSTRUCTION_BLOCKED |
| X2-T2:monitor-episode:05:package:v1 | X2-T2 | 2 | 2 | 2 | PARENT_RECONSTRUCTION_BLOCKED |
| X2-T3:monitor-episode:01:package:v1 | X2-T3 | 3 | 22 | 12 | PARENT_RECONSTRUCTION_BLOCKED |
| X2-T3:monitor-episode:02:package:v1 | X2-T3 | 2 | 11 | 2 | PARENT_RECONSTRUCTION_BLOCKED |
| X2-T3:monitor-episode:03:package:v1 | X2-T3 | 2 | 2 | 1 | PARENT_RECONSTRUCTION_BLOCKED |
| X3-T2:monitor-episode:01:package:v1 | X3-T2 | 5 | 6 | 5 | PARENT_RECONSTRUCTION_BLOCKED |
| X3-T2:monitor-episode:02:package:v1 | X3-T2 | 3 | 15 | 6 | PARENT_RECONSTRUCTION_BLOCKED |
| X3-T3:monitor-episode:01:package:v1 | X3-T3 | 6 | 13 | 7 | PARENT_RECONSTRUCTION_BLOCKED |
| X4-T3:monitor-episode:01:package:v1 | X4-T3 | 1 | 2 | 1 | NO_REPAIR_REQUIRED |
| X5-T1:monitor-episode:01:package:v1 | X5-T1 | 4 | 42 | 1 | LINEAGE_GAP_BLOCKED |
| X5-T2:monitor-episode:01:package:v1 | X5-T2 | 4 | 42 | 1 | LINEAGE_GAP_BLOCKED |
| X5-T3:monitor-episode:01:package:v1 | X5-T3 | 7 | 45 | 1 | LINEAGE_GAP_BLOCKED |
| X6-T1:monitor-episode:01:package:v1 | X6-T1 | 3 | 24 | 1 | LINEAGE_GAP_BLOCKED |
| X7-T1:monitor-episode:01:package:v1 | X7-T1 | 4 | 21 | 1 | LINEAGE_GAP_BLOCKED |
| X7-T2:monitor-episode:01:package:v1 | X7-T2 | 8 | 20 | 1 | LINEAGE_GAP_BLOCKED |
| X7-T3:monitor-episode:01:package:v1 | X7-T3 | 5 | 19 | 1 | LINEAGE_GAP_BLOCKED |

The gate remains fail-closed. No package may enter active repair until its parent reconstruction is machine-verified and any lineage gap between an immutable foreign carrier and a legal downstream repair surface is resolved without modifying the foreign system.
