# C2 v1.1 independent prefit amendment/code check

Date: 2026-10-30. This extends the saved independent initial assessment. No fit, source search, outcome read or treatment-count read was performed. Reviewed text only: protocol_v1_1.md, pilot.py and analyze.py, together with the already-read original protocol. The reviewed pilot includes the version receipts and round-trip/17-significant-digit CSV changes announced during review. Requested/effective runtime configuration remains inherited/unknown.

## Status

Scientific/procedure amendment: PASS. The three original computational ambiguities are resolved without changing the hypothesis, endpoint, anchor/query doses, scientific comparison or gate.

Model/data-boundary implementation: PASS by static inspection. Execution-record/time-guard implementation: PASS after the narrow prefit recheck recorded below. No material blocker remains for the one unchanged matrix. These were implementation corrections, not a scientific revision or permission to change settings after scores. No new source pass is needed.

## Reviewed bytes

| File | SHA256 |
| --- | --- |
| protocol.md | 687395da83d969e8887b532f0978b171838653f049e07894a11dd5be430cf297 |
| protocol_v1_1.md | c89b6bfc6a4eb45c7cb54d3ed19294293508dbd86c35d02fd95e577209fa54a1 |
| pilot.py | fe58e80d8f6c13024b2e1b5758ab01631dcc99eaa93227372478a9868dbc2ed1 |
| analyze.py | 03a4707ed2877e971e5c8cb2bf137b424e64f5b1636ed68df29be811cbb17271 |

These are prefit source-text hashes, not execution/results hashes. A changed implementation must be checked against this review before fitting. The analysis hash in this record freezes the currently inspected decision computation; it should also be included in the prefit run receipt for direct comparison later.

## Static checks that pass

- `SourceFit` slices responses to its explicit fit-background indices before constructing means, A/D, residuals, variances, anchor scales, covariance, tree models or Hill priors. Inner fits receive four backgrounds, outer fits five. The cache key is the complete fit-index tuple. Prediction does not mutate fitted means/priors from a held-out response.
- The target prediction interface receives only its 14-by-2 permitted anchor array. Full target responses appear in inner validation scoring or in outer output/scoring, not in prediction features. No HTS031 path is opened by either script.
- All twelve frozen methods are present. Every tuned method chooses one global configuration per outer fold by equal-mean inner-background macro pair regret. `np.argmin` gives listed-order exact ties. Wrong shape inherits the candidate penalty and rotates sorted-drug q by one place.
- Candidate scaling/penalty and zero-denominator fallback match the protocol. Pooled shape sums observations over drugs; its ridge denominator consequently has the matching background-by-drug count. Anchored ridge uses a population standard deviation floored at 0.1 and a centered residual/intercept. The shared variance is population response-column-centered and floored at 0.01.
- Covariance conditioning uses all 28 target anchors, with a sample-covariance-equivalent dual solve: multiplying the declared observation diagonal by `n_fit-1` before solving against the unnormalized centered Gram matrix is correct. The smooth GP uses fit-only means and the frozen kernel/noise grids. Source-neighbor scaling and weights are fit-only.
- Tree training rows use their own permissible anchor profiles and a source mean excluding their own background. Query means average all current fit backgrounds. Row feature/label ordering is drug-major then query-index-major in both construction paths.
- Hill source fits are bounded and clipped at initialization. A reported unsuccessful source fit uses that initial theta in the prior; none are dropped. Target MAP uses fit-only priors and the two anchor errors; an unsuccessful target uses its clipped prior mean. Non-success booleans and evaluation counts are collected. An ordinary thrown solver exception remains a panel execution failure, rather than a silent method omission.
- Pair rosters and full menus use exact physical-dose equality among query positions 2 through 7. They do not equate normalized dose indices for differently scaled drugs. Drug indices are sorted, so primary and full-menu ties choose the lexically earlier name. CSV input/output precision is sufficient to preserve the recorded float predictions and doses.
- Analysis reconstructs all twelve complete outer prediction arrays, checks dimensions/duplicates and recorded truth against the cache, and uses equal background weights. Technical-well scoring does not refit. Flip margins and cross-well signs match the frozen technical rule. All predicted outer values, hyperparameter choices/mean inner losses, pairwise choices, per-background metrics, complete best-drug menus and optimizer logs are saved on normal completion. Full-menu selections remain reconstructible from those prediction/truth arrays.
- The strongest ordinary rival excludes candidate and wrong shape and uses panel-order exact ties. It is reused for all corresponding safeguards. Absolute/relative margins, four positive background differences, exact `default_rng(1031)` 2,000-by-6 resampling, central linear percentiles, all three shape checks, best-drug loss and both technical-well guards match the frozen decision. The result is explicitly internal and conditional.
- Four-thread environment settings precede numerical imports and the main matrix is wrapped in `threadpool_limits(4)`. There is no installation, tuning expansion, source search or automatic second matrix in these files.

## Initially required bounded corrections — resolved before fitting

1. **Preserve an interrupted/failed matrix as an explicit inconclusive execution.** In reviewed pilot.py, predictions, selections and optimizer logs are written only after the entire matrix (lines 291-293), with no exception/finalization path. A timeout or thrown method error therefore leaves `run.json` at `running`, without the collected arrays, error reason or final timings. Reviewed analyze.py asserts `status == complete` and exits on this state; it does not create the frozen INCONCLUSIVE decision. This fails the explicit requirement to retain panel execution failures and distinguish them from scientific rejection. Add a deterministic failure/finalization path that saves the available arrays/logs and current method/configuration/fold context, sets a noncomplete terminal status with exception/timeout and elapsed time, and produces or allows analysis to produce `INCONCLUSIVE` with gate false and no HTS031 release. Preserve the no-overwrite rule and do not rerun automatically. Include solver status codes and target background identity/context in optimizer records: fit-cell tuple plus drug/penalty alone does not distinguish the two possible held-out targets of a reused four-background fit. This adds audit metadata and does not change fitted predictions.

2. **Check the cooperative deadline after final-fit methods and before declaring complete.** `check_clock()` is currently called after inner validation predictions and at the start of an outer fold, but not inside the final twelve-method loop (lines 280-287) or before `status=complete` (line 294). The final outer fold can therefore cross 900 seconds and still be recorded as a complete eligible matrix. Call the same cooperative check after each final method and before the complete transition, with the failure path above retaining results. Individual numerical calls may finish before a cooperative check; a detected over-budget matrix must remain inconclusive. No hard kill, new worker or changed 15-minute allowance is required.

Once these narrow changes are statically rechecked, the one unchanged matrix can proceed. This review does not claim numerical correctness from executing synthetic or real examples; the planned independent arithmetic check remains necessary after complete outputs exist.

## Narrow prefit recheck and executable PASS

Rechecked the failure-finalization and final-method time-check changes only, without executing imports, fits, synthetic cases, analysis or source acquisition. The initial code review used pilot SHA256 `a6743650899c55b154c30d565f1b2dfcfc8396584a05759df10f98750cfab446`; the corrected pilot is `fe58e80d8f6c13024b2e1b5758ab01631dcc99eaa93227372478a9868dbc2ed1` (16,701 bytes). Analyze remains unchanged at `03a4707ed2877e971e5c8cb2bf137b424e64f5b1636ed68df29be811cbb17271` (8,405 bytes).

The matrix loop now catches ordinary method exceptions and cooperative timeouts, then writes all collected prediction rows, selections and optimizer entries. It records a terminal `inconclusive` run with exception type/message and timing, writes `INCONCLUSIVE_NO_HTS031_RELEASE` with `gate_pass=false`, and re-raises the original exception for the execution log. No method is omitted and no rerun is initiated. Source and target optimizer logs now include SciPy termination status; target entries include the target background ID, used only as log context. The existing analysis guard preserves an already-written inconclusive decision and refuses a noncomplete run.

The same cooperative clock check now follows each final prediction method and the final outer loop. A further check after array persistence prevents an over-budget matrix from being declared complete merely because scoring output was still being written. A single numerical call may run until the next cooperative boundary, consistent with the explicitly cooperative guard; crossing the allowance yields an inconclusive matrix.

Both material prefit blockers are resolved. **Executable PASS for exactly this corrected pilot, unchanged analysis and frozen protocols**, subject to the already-declared canonical interpreter/four-thread/one-matrix scope. This is a static protocol-conformance decision, not an observed prediction or numeric-validation result. The initially raised details about an explicit failure context are adequately bounded by retained partial arrays, optimizer target IDs and the re-raised execution trace; no further logger feature is required before this matrix. The planned independent arithmetic review still follows complete outputs. No source pass 8 request was used.
