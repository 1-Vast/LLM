# Independent review of persisted artifacts after final scoring failure

2026-10-31. **The admitted pipeline failed; its surviving arrays nevertheless support a descriptive negative capability comparison for I054.v1.** This review does not certify a completed original pipeline, rerun scoring, repair code, fit a model or authorize further execution.

## Actual provenance and arithmetic scope

Read the preserved repair traceback/launch receipt, prediction manifest and source-fit record, then only `run_repaired/predictions.npz` and `run_repaired/scored_labels.npz` for the already-declared MSE, coverage, source-profile and secondary ranking arithmetic. Independent extraction code is `challenge/read_persisted_artifacts.py`; numerical details are preserved in `challenge/persisted_artifact_arithmetic.json`. This is an explicitly **post-failure descriptive/exploratory extraction**, not a score-stage rerun. No raw counts, new responses, author code, refits, new model selection, changed thresholds or HTTP were accessed.

The original admitted launch failed during CSV parsing after 5.594 seconds. The sole repair subsequently completed fit with return code 0 at 213.453 seconds, then score returned code 1 at total 237.672 seconds. Aggregate numerical runtime was 243.266 seconds, below the shared 1800-second budget. The preserved affinity mask was 15 (four logical CPUs).

The repair traceback ends in `save_json(out/'results.json',result)`, `json.dumps(...,allow_nan=False)`, raising `ValueError: Out of range float values are not JSON compliant: nan`. The code saves `scored_labels.npz` immediately before that final JSON operation. Thus the successful fit, frozen predictions and saved scored arrays precede a failed reporting operation; `results.json` is not a completed original result artifact.

Independently verified the v5 freeze SHA `2b86e5d5d1b10a244fd84b202ee839ae7440810cfc0add0fc7c39faff26dac52`, the experiment/protocol bindings, and every prediction-manifest file hash. The prediction manifest binds predictions, source fit and fitted-model bytes to the admitted code/protocol; I hashed the pickle without loading/executing it. The scored-label file is generated later and is **not** itself a prelabel prediction-manifest member. Its independently recorded post-failure SHA-256 is `c328fd64e64bb2bb68cf3a4e03f49e7ce425e946a9fab88618bfb7b1faa3dbac`.

Verified shapes: predictions `(3,2,2,5,47894)`, labels `(3,2,2,47894)`, matched-observed `(3,2,47894)`, paired squared losses `(3,2,2,5,47894)`. Prediction values are finite. Matched-observed exactly equals finite labels in both cultures. Persisted losses exactly equal `(prediction-label)**2`, including the same unavailable-label NaNs. There are 9,612 fixed test pairs.

## Why the JSON result failed

The traceback's earlier `ConstantInputWarning` is consistent with an exact constant source-mean predictor passing the code's floating-point `np.std(p)>0` guard. In saved ETOP predictions, that model has peak-to-peak range exactly zero, but the computed standard deviation is `2.168404344971009e-19` for each culture and pooled. The guard therefore evaluates true; Spearman correlation of a constant array is undefined and returns NaN. This supplies a concrete undefined correlation capable of causing the final strict JSON serialization failure. It is a reporting defect, not evidence of NaN MSE or of biological prediction failure. This review does not modify it or certify the absence of every other undefined summary in the unsaved result dictionary.

## Primary fixed-pseudocount comparison

All MSEs below are original-Q units on exactly matched whole pairs in both ancestries. This is the observed subset; coverage does not establish random missingness.

| Model | ETOP source-held MSE (9,564 pairs) | Glucose MSE (9,444 pairs) | Glucose culture 1 / culture 2 MSE |
|---|---:|---:|---:|
| Common coordinate, selected lambda 0.70 | 0.1009649204 | 0.0744988868 | 0.0742956328 / 0.0747021408 |
| Q=0 | 0.1124721153 | 0.0793452303 | 0.0789181228 / 0.0797723378 |
| Source mean | 0.1124702342 | 0.0791546416 | 0.0787537073 / 0.0795555760 |
| Ordinary Ridge | 0.0404797239 | 0.1450061499 | 0.1583605793 / 0.1316517204 |
| Ordinary HGB | 0.0412665907 | 0.0314840248 | 0.0308338796 / 0.0321341701 |

Source label coverage is 9,564/9,612 = 99.5006% (48 unassessable); glucose is 9,444/9,612 = 98.2522% (168 unassessable). Primary prediction-support coverage over the full fixed prediction universe is 99.6879% for source and 99.4174% for glucose. On the primary supported/observed glucose subset, coordinate MSE is 0.0728189637 versus HGB 0.0307952362; restricting to declared support does not reverse the comparison.

The coordinate improves glucose MSE by approximately 6.1% against zero, below the frozen >=10% practical margin even before comparison with ordinary HGB. HGB has much lower glucose error in each ancestry and pooled. Consequently the frozen positive capability criterion cannot pass. The poor Ridge transfer cannot rescue the candidate by selecting a weaker rival after outcomes. The ordinary nonlinear rival is both admissible and substantially better in these saved predictions.

The source-validation optimum is lambda 0.70, with pooled MSE 0.1012004387. Both culture-specific profiles also minimize at 0.70. The descriptive 1%-loss-compatible grid is {0.65, 0.70, 0.75}; the saved fraction of test pairs with mean-culture compatible prediction spread >0.5 is 0. This passes the prospective weak-profile flag, but does not prove statistical identification of a biological coordinate. Glucose centered pair variance is 0.0753052167, versus culture disagreement 0.0241651366. The descriptive headroom check passes; it is not a biological noise-floor estimate.

## Secondary frozen top-100 observations

| Model | Confirmed glucose signed strong hits | Assessed nonhits | Unassessable selections |
|---|---:|---:|---:|
| Coordinate | 21 | 59 | 20 |
| Zero | 0 | 94 | 6 |
| Source mean | 0 | 94 | 6 |
| Ridge | 23 | 51 | 26 |
| HGB | 33 | 44 | 23 |

Each row retains its original 100 predicted selections; missing labels were not replaced. The observed-label ceiling is 50, not the unknown optimum over unobserved pairs. The relatively high missingness within ranked tails (20–26 selections for the informative models despite 1.75% overall missingness) is especially relevant: these counts are confirmed yield/lower bounds, not complete precision estimates or therapeutic hits. HGB's 33 versus the coordinate's 21 is descriptive; no new ranking significance claim or success threshold is inferred.

## Prespecified pseudocount sensitivity and an additional diagnostic limitation

Without refitting or changing the selected lambda, saved glucose coordinate/zero/HGB MSEs are respectively 0.0751630572 / 0.0799221079 / 0.0318172083 at p=0.5, and 0.0733121682 / 0.0783074380 / 0.0311648642 at p=2. The same capability ordering remains. These are arithmetic on already-frozen predictions and matching labels, not a new preferred analysis.

Source inspection reveals a separate bookkeeping limitation: in the alternate-pseudocount iterations the local loop variable `lam` is left at the grid endpoint 2 before `supported` and inverse-sensitivity diagnostics, rather than reset to the selected 0.70. The candidate predictions themselves use the correct frozen grid `choice` column, and the primary p=1 diagnostics use the selected lambda. Therefore primary MSE/support comparisons and alternate-pseudocount MSEs remain interpretable, but **alternate-pseudocount support/inverse-sensitivity outputs are not validated selected-coordinate diagnostics**. I do not use those support fractions for a scientific claim and do not propose a repair/rerun. This limitation should remain visible alongside the JSON failure.

## Supported disposition

The surviving artifacts support a **descriptive negative result for the claimed added capability of this v1 restriction on the observable internal panel**. The coordinate has modest improvement over Q=0 and source-held improvement, but falls short of the declared utility margin and is much worse than the equally informed ordinary nonlinear predictor. This is stronger than an unexplained implementation failure alone because the fitted model, frozen predictions, matched labels and exact losses are all persisted and internally coherent.

This does not establish that a common coordinate is mathematically impossible, identify molecular rewiring, or reject all monotone/multidimensional latent models. HGB itself receives the full coordinate-grid predictions plus raw summaries; its success does not show every element of coordinate preprocessing is dispensable. The result instead shows that this **single selected invariant-coordinate transport restriction** did not supply the promised advantage over the ordinary readout with the same information.

Nor does HGB's lower internal error establish general Virtual Cell success, independent biological validation, sparse-library savings, drug efficacy or agent advantage. Shared T0/UT, both-culture source training, selected K562 genes, observed-subset scoring and the retrospective assay setup remain. Preserve `PIPELINE_FAILED` separately from `POST_FAILURE_DESCRIPTIVE_NEGATIVE_CAPABILITY`; no additional repair, matrix run, source retuning or target calibration is justified by this review.
