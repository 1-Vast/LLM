# Independent static implementation check before the single Stage 1 run

Date: 2026-10-30. Overall goal: ACTIVE / NOT_ACHIEVED.

Reviewed CURRENT candidate `stage1.py` SHA-256 `2187f989756f6a6bbb4a016d0aef5ee2adff577a41f459afe2728c78f2cdb75c` and current `stage1_protocol_v1_1.md` SHA-256 `f0ac8bdc5e0e219c5ae4b9a8abf8474c9fbceb2c201f80486b24f447a2b2b480`. The latter includes the pre-access RNG and metric conventions appended after the prior amendment review. I read the actual `stage1_output_contract.md` (the requested `output_contract.md` basename does not exist), preserved metadata/freezes, and the full candidate code. Initial and amendment reviews remain unchanged.

The first static draft read script hash `80657bee113a079b396317c23eb7e3ee1aa3dc7a2d794c6a8faa86ae95c162be`. Before this review was delivered, root reported and patched a floating-point selection/tail-comparison tie hazard. I then read the complete CURRENT code and verified its integer-count correction. Original line references below identify the first-read script; the unchanged access/retention control flow remains the subject of C1–C4. C5 concerns the remaining bootstrap zero-boundary issue in the current script. This review update is still before any reviewer call/score access or real-data execution.

## Disposition

**HOLD BEFORE DEVELOPMENT-LABEL ACCESS for C1–C3 and C5 below.** The principal model/selection computations and the static XML access branch conform to the amended design after the verified integer-total correction. The unresolved items concern enforcement of the frozen access inputs, retention on a predeclared terminal failure, the hard runtime/failure contract, and exact zero handling in the selected bootstrap interval. These can be fixed without changing the model, endpoint, null, threshold or scientific hypothesis. C4 is a small output-contract completion item to include in the same implementation correction.

No real-data run, candidate-module execution, label extraction or held-out access was performed in this review. A single explicitly allowed synthetic Ridge equivalence case passed; details are below.

## Outstanding implementation items

### C1. Verify frozen input equality before the first authorized label is decoded

At lines 191–209 the implementation records current split/universe/source hashes but does not compare them with `identity_freeze.json`, `gene_universe_freeze.json` or the authenticated source manifest. The feature NPZ is not hashed in the run receipt and is opened only after labels. Cardinalities such as 231 compounds do not enforce the frozen membership: a changed split could still have that size and cause a previously held-out screen to be decoded.

My metadata-only checks establish that the current identity split, chemical feature NPZ and gene roster match their frozen hashes. The current S1 workbook matches the authenticated `6e9fd89d0f62d6bd7601515b92bdaccc703f79cbd3d88c99f45ef8e94ade2d0a` hash. Thus no current input drift was detected. The remaining problem is that the executable access path does not enforce those equalities.

Before `extract_labels`, compare split and feature hashes against the identity freeze, the gene roster hash against its freeze, and the exact selected workbook hash against its manifest. Record those expected/actual equalities and the feature hash. A binding metadata-only preflight in the actual launch is also acceptable if it prevents the run on mismatch and retains its receipt; merely logging hashes after the fact is insufficient. This is especially relevant to enforcing the 63-compound boundary, not a request for secure blinding or new descriptors.

### C2. Retain already produced results when a null draw or runtime check fails

At lines 224–235 aligned and completed null results are held in memory. `ranks.npz`, summary and decision are written only after all 49 nulls finish (lines 261–264). The exception handler records a failure string but drops the already completed aligned/null results, the completed-draw count and the actual assignment archive. A predeclared insufficient-support exception in a later permutation or a deadline exception can therefore destroy outcomes that have already been produced. This conflicts with retaining failures and all outcomes, and prevents independent review of a terminal partial run.

Persist the assignment matrix before evaluation and preserve completed aligned/null results plus their completed-draw count on an exception or periodic checkpoint. Distinguish partial artifacts from complete 49-draw outputs. If extraction itself fails after authorized values have been converted, retain an access/failure receipt and counts rather than silently losing that exposure record. The failure must remain terminal: do not skip the offending draw, alter rarity, complete the missing draws in another scientific run, or treat partial inference as a passed gate.

### C3. Enforce the 30-minute limit and prevent a failed run from leaving a successful gate

The first time check is before the first null (lines 223–228), after all feature-side ridge fits and aligned evaluation. A long feature fit or a single long null can exceed the 30-minute maximum before the next check; the code currently detects an overrun rather than enforcing the stated cap. A documented launch watchdog with a hard timeout and a terminal failure receipt is sufficient; it need not change model code or add a scientific run. Its scope must include label access and the model matrix, and completed outcomes must survive it as far as already written checkpoints permit.

The implementation also writes a potentially true `information_gate_pass` before its final deadline check (lines 257–266). On that failure path, `run.json` becomes failed while `decision.json` can still contain a successful information gate. Ensure a failed/incomplete run cannot be consumed as a successful gate: publish the completed gate only after successful final checks, or overwrite/qualify it on every terminal failure and require complete status in downstream verification. Held-out release is already hard-coded false and must remain so.

### C4. Complete the declared run receipt

The output contract asks `run.json` to record settings and complete shapes. The current receipt has counts but no explicit shapes for calls, aligned ranks/scores, null ranks/scores and assignments. Add the actual shapes, core fixed settings/seeds and the feature input hash (also needed by C1). The arrays themselves are appropriately retained on the successful path; this item makes the promised receipt self-describing rather than changing an analysis.

### C5. Use exact recovered-count gains for the bootstrap zero boundary too

The current script correctly obtains integer total recoveries before choosing the aligned winner and comparing null gains with the observed gain. The same exactness is not yet used for the paired interval: `differences = precision[best] - precision[0]` is summed in floating point within scaffold groups and again across sampled groups. These differences are rational multiples of 1/20, so an exactly zero sampled total can acquire a tiny nonzero residual. Because `conditional_interval_above_zero` uses strict `interval[0] > 0`, that residual can change the stated zero-boundary interpretation.

Use integer per-compound recovered-count differences (already recoverable from the current rounded integer counts), sum them by scaffold and across the unchanged bootstrap samples, then divide each sampled numerator by `20 * sampled_member_count` before the specified quantile. This preserves the exact frozen bootstrap estimand and RNG order; it is a numerical implementation correction, not an additional test or threshold tolerance chosen from results. No extra synthetic experiment is needed.

## Checks that passed

### XML boundary, gene identities and call semantics

The S1E row loop first reconstructs only the screen identity (lines 64–69). It skips every unselected screen before constructing the gene-cell lookup, decoding the HGNC(2020) gene, converting score/FDR, or recording a hit pair. Among selected representative development screens it skips identities outside the fixed included universe before score/FDR conversion (lines 73–80). This implements the intended numerical access boundary, conditional on the exact frozen membership enforced in C1. It does not read S2 numerical values.

XML/shared-string container characters are parsed globally, so this is controlled extraction rather than secure blinding. That matches the protocol caveat. The code does not summarize rejected screen counts, reconstruct rejected screen/gene pairs or convert their numeric score/FDR cells. No dynamic test of this parser on a real workbook was performed.

The included HGNC(2020)-to-canonical lookup uses the fixed roster, not corrupted EKO strings. Canonical genes are sorted lexically, and the prior full metadata mapping/uniqueness checks passed. The Boolean target is initialized as call absence and set only for the selected S1E row's own `score < 0` and `fdr < .05`. Nonfinite authorized scores/FDRs stop rather than become absent calls. This supports the literal published-call endpoint; zero remains a non-call, not a demonstrated biological negative. Multiple instances of the same admissible binary call, if any, cannot multiply its matrix value.

### Source-only eligibility, metrics and ties

`source_eligible` uses only `truth[train]`, retaining genes with at least one source call and call count at most 10% of the source compounds. Each aligned and null evaluation recomputes this universe. Fewer than 20 eligible genes is terminal; no draw is dropped. For the aligned case there is also a pre-fit support check.

For each query, recovered calls are counted at the 20 retained eligible gene indices. P@20 divides by 20. Oracle is `min(20, number_of_eligible_query_calls)/20`. Descriptive recall divides by eligible query calls and is zero if none; the appended convention now explicitly identifies that denominator. These are eligible-call recovery statistics, not recall of every biological vulnerability or every unmasked author call. Zero-call query drugs stay in the macro denominator. Macro means are over all 231 drugs, not equally weighted fold means.

`genes` is sorted; eligible indices are increasing; stable score sorting therefore provides lexical canonical-gene ties. Representative rows are sorted by compound ID before source indices are generated. Stable descending Tanimoto sorting consequently breaks neighbor ties by compound ID. Nearest-five uses the mean of the five profiles with equal weights. Fingerprint intersections/unions use floating-point counts, avoiding small-integer dot-product overflow. No outcome-derived distance or feature is present.

### Ridge and the one permitted synthetic equivalence check

Source means and `std(ddof=0)` are used, and zero feature SD becomes one. The feature transformation is fitted on source compounds only. `Ridge(..., fit_intercept=True, solver="cholesky")` fits identity outputs for alpha 1, 10 and 100. Multiplication of its query prediction operator by the source call matrix preserves both the centered linear term and the intercept. The operator is independent of outcomes, so it can be reused across null label assignments while reproducing the full-rank fit. Clipping is after label multiplication, as required. The operator row-sum assertion is an additional intercept consistency check.

I performed exactly one tiny synthetic case at alpha 10 with eight source rows, five features including a constant feature, three query rows, and four output columns including constant-zero and constant-one outputs. Ordinary direct multioutput Ridge predictions and identity-operator predictions differed by at most `1.1102230246251565e-16`, both before and after clipping. This checks the relevant algebra in the existing environment; it is not a biological experiment or a candidate performance test. No real source feature, call or score was used, and the candidate module was not imported/executed.

### Coherent null, selection, bootstrap and RNG order

Main sorts compounds by ID. `np.unique(groups)` yields lexical scaffold-hash order, and member indices retain compound order. Strata are ordered round tuples, implicitly fixing size. Iteration over sorted strata and `rng.permutation(len(names))` for every stratum, including singletons, matches the appended RNG conventions. Each mapping is destination row to source row, moves a whole block and is applied once as `calls[mapping]` before the complete evaluation. Source profiles and validation truth thus come from the same coherent reassignment. All genes move together. Identity/repeated mappings are retained.

Frequency predictions are the mean of each replicate's current source calls. Eligibility and frequency therefore change when blocks cross fixed folds, as required. The same four chemistry methods are scored over the complete development set. In the CURRENT script aligned and null selection use exact integer recovered totals; `np.argmax` on those totals provides the listed chemistry-method tie order. Means/gains are reported as counts divided by `20 * N`. Null integer gain counts are compared with aligned integer gain count using `>=`, then the p-value adds one and divides by 50. This resolves the floating-point method/null tie hazard reported by root. There is no per-fold alpha choice or additional selector.

Bootstrap gains pair the selected aligned model with aligned frequency per drug. Groups use lexical `np.unique` order. A single `(2000, number_of_groups)` integer draw array consumes RNG in the same row-major order as 2,000 successive group-index draws. Summing selected group gains and dividing by selected member counts implements complete-scaffold resampling with compounds retained. NumPy's default quantile is the specified linear percentile calculation. The interval remains selected-development and exploratory.

### Successful-path shapes and replay guard

Successful arrays have the declared forms: calls `(231,18415)`, aligned indices/scores `(5,231,20)`, null indices/scores `(49,5,231,20)`, mappings `(49,231)`, and labels with explicit compounds, genes, folds, groups and rounds. All method rankings and query rows are retained; no zero-call query filtering occurs. Actual shape fields still need C4.

The existing `run.json` guard prevents automatic execution over an earlier successful or failed run. Normal exceptions produce failed status and re-raise. No retry, parameter switch, candidate replacement, held-out release, novelty claim or core promotion exists in the script. Preserve this behavior while resolving C1–C5. The source finite-support stop is not a reason for scientific replay.

## Scientific limits and access record

The initial and amendment reviews' scientific limits are unchanged: conditional block exchangeability is an assumption; published-call recovery is not a physical fitness contrast, prospective label-construction independence, pharmacological efficacy, practical assay savings, mechanism transfer or external biological validation. Source-selected GI30/adaptive regimens, one cell background, shared controls, unknown global correction, source-only call rarity and limited scaffold separation remain material. A conditional p-value or selected bootstrap interval cannot establish robust biological benefit. A completed positive development result would allow only a later protocol to be designed and challenged; all 63 held-out compound calls remain unread and unreleased.

Review activities were full static reading, AST parsing without execution, metadata/file-hash checks, and the one synthetic Ridge check described above. No workbook outcome was decoded, no real-data model ran, no candidate code or shared library/core/index was edited, and no additional agent/external model bridge/install was used. New public traffic: **0 HTTP attempts, 0 completed response-body bytes, 0 known partial bytes**.

The coordinator should resolve the concrete execution/retention items and obtain a static recheck of the changed sections before its single development run. Do not soften the scientific limits or reopen the held-out boundary to resolve them. Overall goal remains ACTIVE / NOT_ACHIEVED.
