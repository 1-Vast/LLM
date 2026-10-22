# Independent implementation review — CiPA calibration probe

2026-10-22. **ALLOW_FREEZE_AND_ORDINARY_PROBE; no prefreeze code blocker identified.** This is an independent code-only review, conditional on root freezing the reviewed versions and required inputs before real fitting. I read the protocol, endpoint contract, preceding skeptical reviews, `endpoint_contract.py`, `preserve.py`, the complete `model_probe.py`, `PREPARE_AUDIT.json`, and the implementer's synthetic tests. I have not opened numerical source/development bundle targets, forecasts, results, or later-site outcomes. My own five synthetic tests perform no solver fits and read no assay files.

Reviewed SHA256 bindings:

- `model_probe.py`: `447f7a16cfe1697b427719a5d794b1a6abed1e47f57c9f04f8f9489f6f12bc93`.
- `PROTOCOL.md`: `498d0664ae1aa09dc582144b99fd0de1070ee4508de64b516992f8a16d8f5e3e`.
- `PREPARE_AUDIT.json`: `ee72e23f6292b55bc0490e11413a813b15ccaf2369e20ba84260f2457f9aef44`.
- Independent `test_skeptic_boundaries.py`: `0c8558d61df28f9351ebf5a23cdfcd320519d11a455705c850e7211ea024c54f`.

## Endpoint conversion reviewed

The endpoint code skips sites8/9 and sequential-addition site10 before G/H decoding. It validates exact binary numeric EAD, finite numeric H, and illegal-value eligibility, preserves missing observations, computes EAD on its valid-G denominator, H on its finite-H denominator, and availability on every released row. Missing H is not assigned zero or pathology. The retained full XML and shared-string acquisition is already disclosed; this is computational withholding rather than global human blindness. No additional endpoint-code blocker was identified.

The runner must verify endpoint audit PASS and bound input/artifact hashes. Artifact existence alone is not evidence of eligibility. `preserve.py` reads predecessor inventories and hashes their files rather than interpreting their numerical results.

## Predictive data flow and evaluation

`metadata()` projects only the exact identity schema. `labels_for()` filters authorized IDs before accessing endpoint fields. The JSON loader necessarily parses the converted source/development container, as disclosed by the protocol; no terminal numerical target/count/mask is supplied to prediction or proposal functions. `feature_keys()` and `predict()` reject extra metadata fields. Risk, Type_of_EADs, released-row counts and observed measurement masks are absent from features.

`source_cv()` excludes the entire held-out physical site from its source labels and Summary. Only each held-out context's eight fixed controls enter `predict()` as paid feedback; its terminal truth is used by the CV evaluator. All same-site contexts are processed under the same source fold. Fold IQR/SD/fallback scale, global and stratified lookups, and nested summaries use that fold's source sites only. Nested augmented features exclude the entire source row's physical site, including the inner scale. A source row's own outcome cannot enter its derived vector. Outer-CV terminal outcomes legitimately select source hyperparameters; development terminal outcomes do not.

Lookup drug/dose entries average the released context bundles equally; there is no exported-row-count weighting. The all/cell/cell-platform fallback sequence and per-head finite-value fallback are implemented. Missing source H stays absent when computing its summaries. Source uncertainty uses only source-context responses, normalized H, population variance and the predeclared zero fallback for fewer than two available values.

`make_manifest()` enforces four controls times four dose codes, a common24-drug/four-code terminal pool, the sole authenticated source95 exception, and disjoint pools. Fixed and random policies use eight distinct pool bundles; source uncertainty and linear design also enforce eight distinct legal bundles. Linear design starts at8I, uses only source-predicted vectors, updates design information, and breaks ties by stable ID. All policies predict the same terminal IDs. The prepare identity audit reports two contexts at every source physical site and one at each development site: source pseudo-target cost is16 per physical site, development cost8 per physical site per policy.

CV components pool bundles within a physical site and select by the equal mean of five physical-site combined losses, with lexical exact ties. The three lookup variants, all residual-calibration grids, direct Ridge and128-tree ExtraTrees with the requested target weights, nested-vector augmented Ridge, source-CV-best updater, fixed50/50 sourcebest/refit mixture, five random policies, uncertainty and linear design controls are present. Portfolio includes the seven source-tuned families (best lookup plus six update/refit families), four balanced two-bundle hash folds, common truth masks, equal fold averaging, and refitting its chosen family on the eight paid controls. It never receives terminal truth.

`losses()` implements `p*p - 2*p*y + y` for E/M, conditional finite-H bundle MAE divided by the fold/source scale, native H MAE and valid/total coverage. A missing H does not create a zero truth or an abstention opportunity. All predictions must be finite; E/M clipping occurs before every scoring path. Reduced-head portfolio losses use the same actual held-out truth masks for all candidates. Development sourcebest comparisons use that frozen sourcebest's development forecasts on the same terminal population. The two development contexts are the two physical sites, so the reported site differences do not accidentally multiply site replicates.

## Fit budget and sealing

The frozen loops enumerate28 configurations: three lookups and25 fitted configurations. With ten source contexts, source CV permits at most750 head-solver fits; unavailable paid heads may reduce residual-calibration fits. Each of two development contexts permits18 fixed-family fits,72 portfolio-validation fits, at most3 portfolio-final fits, and21 fits for seven additional policies: at most114 per context,228 development and978 total head-solver fits. Three heads per ExtraTrees fit configuration means each logged tree head additionally builds128 estimators; this is not978 individual trees. Summary construction count is31 (25 CV and six all-source/nested development). Actual head fits and CPU/wall times are logged individually, summaries separately, and total CPU/wall is also recorded. Lookup reuse and fixed/refit aliases do not inflate the actual solver count. There is no equal-compute claim.

`verify_freeze()` checks required protocol/code/audit/converted-input/query-manifest hashes before fitting and verifies every additional file root includes. Root should include the endpoint input/artifact seals and this review in the final freeze provenance. Source choices are computed before development feedback, and each context's full policy list is proposed from source-only summaries before that context's paid feedback is requested. `fit_predict()` writes choices, all ordered feedback, all policy lists, portfolio choices, forecasts and fit ledger, then hashes them in `FORECAST_SEAL.json`. The separate `score()` verifies freeze and the forecast seal before extracting development terminal targets. No code path converts later-site numerical outcomes.

## Independent synthetic checks and disposition

Executed `python research/cipa_calibration_probe_20261022/test_skeptic_boundaries.py`: **5/5 PASS**, with zero model fits. Tests use poisoned unpaid dictionaries to detect forbidden field access, exact synthetic28-drug pool construction, numerical Brier/conditional-H assertions, rejection of nonfinite predictions, whole-own-site perturbation of nested features, and a complete five-site CV run with the predictor mocked to assert physical-site and paid-label boundaries. The mocked CV includes a physical site with two contexts and confirms equal physical-site loss aggregation. The implementer's tests additionally exercise a synthetic residual update, extra-field rejection and source-global fallback.

**Blocking items: none in the reviewed implementation.** Freeze is still a required operational step; this review does not authorize fitting an altered implementation under the old hashes. Postrun auditing must verify ledger counts, seals and the registered comparison without choosing new models from development results.

**Nonblocking limits:** if every terminal H in an entire development evaluation population were absent, `losses()` correctly returns no H score, but `score()`'s component-difference subtraction would stop on `None`; this was not established for the actual data and is not a reason to inspect unpaid truth or modify this frozen probe. Any such runtime failure should be recorded without inventing H performance. The experiment remains ordinary known-drug development calibration and cannot establish clinical utility, a novel world/agent mechanism, or C4.

No ordinary model's lack of novelty is a reason to block this development test. No performance-dependent design revision is authorized by this review.
