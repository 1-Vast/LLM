# Independent static implementation review

2026-10-23. Reviewed research/depmap_state_increment_20261023/run.py and PROTOCOL_RESOLUTION.md. Did not import or execute fitter, read numeric state/label payloads, fit models or access network. No tests were executed by this reviewer. Initial test_run.py read failed because that file did not yet exist; this is a missing implementation check, not a test failure. Original independent/cross files remain unchanged.

## Core mathematics and information flow

No observed hidden outer-query-label path into training predictions or selection. all_grid computes gene prior/residual from the supplied tr only; nested supplies inner fit/validation partitions and recomputes every kernel. Inner selection uses heldout source labels, then outer refit uses all outer source labels. Selecting lambda and program on the same source validation losses is legitimate for honest outer predictions. G mixes separately selected C/E, with the previously disclosed greater component-search opportunity.

The center helper correctly forms globally source-centered train and query cross Grams. C applies that helper separately within source-target groups, yields zero off-target entries and source-target-specific feature centering; unobserved query target contributes zero gated correction. The protocol's global-context fallback has no numeric effect when there are no matching source targets, since the target gate is zero. B source zscores and normalizes mean source diagonal; D/E source-center and normalize likewise. F/H source-only positive-distance median, exp(-d/(2*median)), zero-distance fallback1, clipping and target gate on H match the resolved specification. Uncentered RBF is intentional. Spectral clipping of negative eigenvalues is numerical PSD stabilization; it is not a new learned feature.

Gene prior includes each training sample in its own source mean; that is the predeclared two-stage ordinary estimator, not hidden-query leakage. Final query missing source gene falls back to source overall mean. No unpenalized residual intercept is introduced. KRR divides by n*lambda as specified.

Metrics use equal-line MSE, per-line lexical-tied most-negative top10 regret and equal-line summaries for both outer schemes. Gate compares source-selected full/restricted procedures, >=5% primary gain, >=12 strict line wins, positive batch gain and nonworse mean top10 in both schemes with1e-12 arithmetic tolerance. It does not salvage a best observed method. Top10 labels are explicitly genetic dependency, not drug response.

## Evidence-storage gaps to fix before run

1. Draft requires all inner predictions/choices/losses. Current nested returns only the selected-lambda prediction for each program; inner npz discards the other lambda predictions even though scores remain in CHOICES. Save full validation grids as well as selected outputs. This is a contract weakening unless explicitly amended before outcomes; saving grids is simpler.
2. PREPARED reports line coverage but not gene coverage, dropped label pair identities or missing-gene fallback counts for inner validation. Protocol requests line/gene coverage/missingness and fallback occurrence reporting. Add these identifiers/counts without changing eligibility or predictions.
3. Library metadata currently only numpy/pandas; record scipy/threadpoolctl and Python plus runtime thread limit and actual grouping inventory, since eigensolver and CPU/thread setting affect reproducibility/cost. Group identities may be reconstructed from prepared arrays, but explicit group sizes improve audit.
4. Synthetic tests were not available at this review point. Required non-leakage, source-prior recomputation, degenerate-feature, translation and target-gating checks remain unverified until actual tests run. Existence of FREEZE.json is only a guard, not content-hash verification; root's audit must confirm code hashes and prefit ordering.

No detected need to change fitting formula, gate or selected menu. These storage/verification gaps should be repaired before numerical access, and re-reviewed changes recorded in a new addendum rather than editing this sealed opinion.

## Scope of structural NaN amendment

Read the documented root explanation that author generate.py286-301 removes allzero transcripts per line before union concatenation. Current preparation fills NaN only for transcript columns missing across every selected target within a line, and fails mixed missingness; it also rejects infinity, negatives and nonintegers. This implements the described sparse-union exception rather than unrestricted count imputation. I did not independently re-open author source in this code review and therefore treat its author-provenance citation as root-supplied evidence pending independent source check. Padding counts do not establish biological zero for arbitrary missing data.

The fixed-menu interpretation and unresolved nonlinear-QC/global-context explanations from CROSS remain. Correct code alone supplies no new performance, novelty or full-goal evidence.
