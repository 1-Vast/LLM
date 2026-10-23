# ALMANAC's saved diagnostics do not yet identify the decision-relevant error component

2026-10-22. **NO_CANDIDATE for a new mechanism from these records.** Existing results establish that ordinary feedback improves pointwise prediction while its ranking benefit is unstable under the stated source-study sensitivity. They do not establish which error component improved or why the top-set decision degraded. An exact decomposition would be a finite-cost descriptive audit, not a new centering/ranking algorithm. This review performs no such recomputation, reads no response arrays/reserve, runs no model, requests no network source, and reads no current-stage peer draft.

Re-read the full mandatory objective and query_teacher_resolution/CONTINUATION.md, DECISION.md, ROOT_FINDINGS.md and local VERIFICATION.json. Existing historical scoped STOPs remain. The first objective read used a mistyped attachment suffix and failed; the corrected full source and its final sections were subsequently read. No inference was drawn from that path error.

## What was already measured

ALMANAC feedback pilot DECISION.md defines a precise, limited task: FF laboratory, known drug-sample pairs in new cells, common 887-pair catalog and eight unmeasured dose-grid points per pair. Target B0 uses six single-drug measurements; B1 additionally uses that pair's high-high combination observation. A cell's B1 budget is 887 separate anchors, not one common scalar. Cross-target-pair anchor pooling was prohibited. Lower mean growth is preferred for the fixed decision metric.

Frozen source-selected B0 versus B1 development MSE is .0094443827 to .0084953821 (about 10.05% improvement). Pair selection uses each pair's **mean growth across the eight query points**, then chooses the lowest 89 of 887 pairs. Main top-10% mean-growth regret is .0086369803 to .0077671489, improving in six of ten cells. In the same-pair source-study-exclusion sensitivity, MSE remains improved (.0100466787 to .0094438057), but regret is .0096032022 to .0097194522, improving in only four cells. Thus “MSE good but ranking bad” must be scoped to the sensitivity comparison; the main average regret improves modestly and is not a uniformly negative result.

The absolute sensitivity regret worsening is approximately .00011625 in fractional growth, not evidence of a large universally harmful intervention policy. No independent-study biological significance or clinical decision improvement is established. Reusing the same predictions for descriptive decompositions cannot upgrade that evidence level.

DESCRIPTIVE_DIAGNOSTICS.json and skeptic/RESULT_DIAGNOSTICS.json report per-candidate MSE/MAE/regret, per-cell improvements, per-query MSE gains, pair improvement counts and concentration. The reported 82.45% gain in three dose positions near the high-high anchor is suggestive of local information, but those positions contribute to the pair mean too. It does not by itself show that the gain is entirely shape-only or irrelevant to pair decisions.

## Existing centering is a different operation

DIAGNOSTIC_SCOPE.md, root/ERROR_DIAGNOSIS.json, and the saved error_diagnosis.py show the later exploratory source20-to-tune10 diagnostic. For each cell and each query location separately, it centers innovation and errors **across 887 pairs**, then computes their covariance-derived slope and correlation. The prediction error is pred minus truth; innovation is observed anchor minus source-only B0 anchor prediction. Remaining negative associations are consistent with incomplete statistical response to feedback, but not with a uniquely identified biological failure.

The function relation uses errors.mean(axis=1), where axis 1 is pair. It does not first average errors across the eight query positions within each pair, and it does not partition MSE into squared mean error and centered shape error. It returns slopes, correlations, their cell summaries and sign counts; it does not save the full error covariance across query positions or the centering means/variances needed to reconstruct the proposed MSE decomposition. The older diagnostics.py likewise saves dose-wise and pairwise **MSE gains**, not pair-mean prediction-error moments or selection-boundary errors. A search of this pilot's existing Markdown/JSON records for mean residual, centering, decomposition, bias and related terms found no saved exact decomposition of the required kind. This is a bounded audit of these records, not a claim that no other file anywhere could contain one.

The source model's centered residual target relative to NCI is a third, separate use of “residual.” Training-output centering is not a measured decomposition of pred-minus-truth error on held-out cells. All three operations must be kept distinct.

Existing readers already disclosed that the old diagnostic materialized the full permitted 40-cell NPZ before selecting 30 cells. This review reads only reports and source code, not that NPZ or saved prediction arrays. The protected later 20 cells remain unopened. The earlier source/tune diagnostic reused tune cells after program selection; it is exploratory, and it differs from the main 30-source-to-10-development comparison in source count and evaluation cells. Its correlations cannot be substituted as an explanation of development ranking failures.

## Exact decomposition that the summaries do not supply

For a fixed cell c, pair p and one of Q=8 query positions q, define e_cpq=prediction_cpq-truth_cpq. With P=887 common pairs, let

    m_cp = mean_q e_cpq
    a_c = mean_p m_cp
    b_cp = m_cp - a_c
    s_cpq = e_cpq - m_cp .

Then e_cpq=a_c+b_cp+s_cpq, mean_p b_cp=0 and mean_q s_cpq=0. Under the experiment's equal cell/pair/query weighting, the cross terms vanish and

    MSE = mean_c a_c^2 + mean_cp b_cp^2 + mean_cpq s_cpq^2 .

Here a is the cell-common pair-mean prediction offset; b is the centered **pair-mean error**; s is the within-pair query-shape error. This is an arithmetic identity for the existing equal-weight metric, not a causal model, estimator or learned mechanism. With missing points/unequal weights the projectors and weights must be redefined consistently, rather than applying this identity unchanged.

For the actual pair-mean decision, the predicted score is true_mean_cp + a_c + b_cp. The cell-common a cancels from every pair comparison, and the within-pair s averages to zero. Only b, relative to true pair-score margins, can affect the within-cell ordering. This does **not** mean that a pair-specific curve shift is irrelevant: that shift appears in m_cp, and its variation across pairs is precisely b. Merely subtracting a common cell mean from all predictions leaves the selected pairs unchanged.

Even a decrease in mean b^2 does not guarantee lower top-89 regret. Errors near the selection boundary can change the selected set despite improvement on many irrelevant pairs, and direction/true margins matter. If T is the true lowest-K set and S the predicted lowest-K set, regret is

    [sum_{p in S} true_mean_cp - sum_{p in T} true_mean_cp] / K .

The common selected members cancel; the remaining error is determined by wrongly included versus wrongly omitted pairs and their true response gaps. This describes a precise decision-relevant discrepancy but is not itself a new loss or update rule. Nothing in the saved total MSE, per-dose MSE, pair-count gains or innovation correlations identifies these swaps and their causes.

Consequently, the current summaries cannot determine whether feedback mostly reduced a, s, or broadly b while worsening boundary errors. They also cannot distinguish biological response correction from shared measurement normalization. Those are competing explanations, not findings. Reporting one of them as the established recurring failure would overstate this audit.

## Finite-cost implication and mechanism decision

The exact a/b/s audit of already-authorized frozen prediction/truth arrays would require one linear pass O(C*P*Q), no refit and no new response collection. Existing sorting or partial selection yields top-set swap summaries. It could falsify the narrow hypothesis “the MSE benefit is mainly common-offset or shape improvement rather than pair-mean improvement.” This review only specifies that check; it does not load arrays or compute a new result. An oracle mean derived from hidden query truth would be legal for retrospective diagnosis but not a deployable correction.

No concrete nonstandard repair follows from a hypothetical outcome of that audit. Ordinary calibrated regression, pair-mean regression, ranking objectives, top-set loss, residual covariance and source-only stacking already express the obvious alternatives. Re-labeling those operations as “functional error inheritance” would not establish an algorithmic contribution. The existing stop explicitly excludes fitting another anchor-transport corrector merely because residual correlation remains. A new evaluation identity is not evidence that this restriction has been overcome.

The one actionable distinction here is therefore **diagnostic**, not a proposed new updater: separate error components aligned with the exact decision target before attributing a failure to feedback propagation. There is presently no supported finite-cost/statistical mechanism beyond ordinary methods, no new biologically certified state relation, and no evidence of world-model, agent or improved-improver necessity. **NO_CANDIDATE / NO_PROMOTION**, preserving both the useful ordinary functional-feedback MSE result and STOP_CURRENT_ANCHOR_TRANSPORT_NOVELTY_AND_RSI_EXPANSION. No global claim that feedback/ranking/virtual cells cannot work is made. Full objective ACTIVE / NOT_ACHIEVED.

## Read and resource record

Historical sources read: ALMANAC DECISION.md; DIAGNOSTIC_SCOPE.md; DIAGNOSTIC_READER_SCOPE.md; root/DESCRIPTIVE_DIAGNOSTICS.json, root/ERROR_DIAGNOSIS.json (schema/search and initial stored entries); skeptic/RESULT_DIAGNOSTICS.json; both old DIAGNOSTIC_REVIEW.md files and assay/DIAGNOSTIC_CROSS.md; saved research/almanac_feedback_pilot_20261022/error_diagnosis.py and diagnostics.py. Search matches additionally inspected the pilot's old implementation/protocol review passages. No current-stage peer draft was read. New network requests 0; models fitted 0; new diagnostics executed 0; response-array/reserve access 0. Originals unchanged.
