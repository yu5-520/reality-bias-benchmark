# Stage-II v7.24: T2 first-attempt row frozen 7/7

Date: 2026-09-26. Status: **T1 7/7 FROZEN; T2 7/7 FIRST ATTEMPTS FROZEN; TOTAL RAW NATURAL ATTEMPTS 14/21; C1+C2 2/4; T2 POST-HOC AUDIT NEXT; T3 CLOSED**.

The complete prospective T2 row has been collected exactly once per X condition from source run 36177945998 at execution SHA 04c66a5a9774610f057eda166cb37ab07db6058c. All seven artifacts are frozen under stage2/natural_v7/X1-T2 through X7-T2. No cell is rerun.

Five runners completed normally. X4 and X6 are also valid frozen first attempts, but their native runners returned 1 after the DeepSeek JSON response remained malformed after two identical-request attempts. Their outer collection command still returned 0 because the collector's responsibility is to preserve the failed attempt; the later reporting assertion intentionally made those two matrix jobs red rather than relabeling the runner failures as successful.

The source workflow therefore concludes failure by design while still containing seven immutable first-attempt artifacts. This is an evidence-accounting state, not permission to resample X4-T2 or X6-T2.

T2 was collected prospectively after Action Contract v2 removed the two T1 parser-admission omissions. X1 retains its native AutoGen interface; X2-X7 use the frozen prospective contract where applicable. Raw freezing does not classify CPR and consumes no additional contrast.

The next operation is a read-only seven-cell T2 semantic/process audit. It should compare scope growth, inter-role propagation, native layer activity, checkout consequences, process closure and the two preserved provider-format failures. T3 remains closed until that audit is frozen.
