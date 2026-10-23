# Final code and protocol approval before response parsing

2026-10-23. APPROVE root freezing and executing the final narrow descriptive diagnostic. Read NUMERIC_PROTOCOL.md and weekly_diagnostic.py; read only header/design projections earlier. Did not run code/tests or read raw response values. Computing the raw input SHA256 reads bytes but does not decode or inspect assay outcomes.

Bound files (SHA256):

- protocol log/20261023/public_recovery_task/NUMERIC_PROTOCOL.md: 4c3549527f976054e036a6d6d4dcf51d3dcc5fa8dab8c18200d08c493fe64415
- implementation research/public_recovery_task_20261023/weekly_diagnostic.py: 02a07a364cae94f429de70f25b87841d90f1bae2d890c9b620008a5b1f5430c5
- fixed-commit raw CSV log/20261023/public_recovery_task/root/count_header_source.body: 0370b090a0a81a55542616c25008fda7b0c23f000fb7797f9ac1b966848979b1

This final version supersedes the initial draft's individual-nonnegative eligibility and main-score suggestion while preserving that sealed draft. After source's substantive objection, all finite values, including negatives, contribute to means; negative counts are descriptive subsets. This is a documented pre-outcome correction, not an outcome-driven rescue. The final primary is day28 squared error; two-horizon MSE is secondary and defines the fixed recurrence gate. Neither metric was chosen after query values were read.

Implementation review: exact24 design rows are grouped by the two samples/two schedules, six distinct replicate labels each; no per-row trajectory is assumed. Float conversion of days0/7/14 occurs first. All finite means, missing/nonfinite/negative tallies and at-least-three-value rules match protocol; invalid required baseline/denominator/square-root aggregates stop execution. Missing-token conventions and unknown-token exceptions are explicit. Negative query means remain allowed. Means are normalized by group day0 mean, not matched row baselines.

All four formulas match the final protocol. First-cycle equals latest-interval for Continuous and equals global-exp at Intermittent day28; the code checks these identities before query conversion. Forecasts are computed for every group, persisted, hashed and sealed before days21/28 are converted. The CSV decoder still materializes future TEXT before that point, so this is computational-use separation, not cryptographic blindness; the final protocol correctly says so. No fitted author matrix or whole-trajectory parameter is used.

My code review requested saving both per-horizon errors and rejecting nonfinite normalized truths/scores. Root implemented both before this approval, and I reread the changed block. Scores retain day21/day28 squared and absolute errors, plus day28 and equal-horizon summaries; group summaries weight the four conditions equally. Forecast/truth/score finiteness is checked. The gate requires strictly improved two-horizon MSE in EACH of the two predeclared Intermittent groups; there is no subgroup selection or impossible strict superiority over all methods at the identical day28 endpoint. Complete four-method results must be retained even if the gate fails.

Freeze/input-hash checks precede response parsing. Existing prefix output prevents accidental rerun; failure at any stage must remain logged externally rather than deleting partial artifacts and retrying. No unnecessary new tests or simulations are required for these short reviewed formulas. This review authenticates code logic, not biological independence, physical count calibration or source assay quality.

The result can support or reject only this ordinary first-cycle assay-response recurrence on an exposed four-condition development panel. It cannot establish novel world-model utility, improved updater, agent, inheritance, synergy or RSI. A failure triggers the stated STOP without clipping, new period, shrinkage or alternate scale. A pass remains ordinary descriptive utility with no new-core GO.
