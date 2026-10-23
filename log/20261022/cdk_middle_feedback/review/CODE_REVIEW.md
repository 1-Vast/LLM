# Pre-decode code and protocol review

2026-10-22. Reviewer: frontier_distinct. Read `NUMERICAL_PROTOCOL.md` and `research/cdk_middle_feedback_20261022/{prepare,evaluate,test_evaluate}.py`; also read the already qualified text-only sample bindings to verify treated stage labels and replicate types. No workbook numerical values, prepared arrays, results or another new review were opened. No tests, predictions, fits, downloads or API calls were executed by this reviewer.

**Decision: one source-decoding scope inconsistency must be resolved before execution/freeze; otherwise no blocking scientific/code defect found in this static inspection.** Retain the parent's selected primary complete-culture LOO and key index-blocked sensitivity, report both, and do not change the primary loss or introduce a functional usefulness threshold.

## Execution-before-freeze correction

`prepare.py` calls `workbook[sheet].iter_rows(values_only=True)` with no column selection. Openpyxl parses numeric values across each complete row before the code picks `row[col]`. Consequently it will decode vehicle Count/Fraction and treated Fraction cells on the two selected sheets, even though only treated Count values enter stored dictionaries and later analysis. This conflicts with the protocol's literal statements that only 36 treated Count columns are decoded and vehicle numerical arrays remain unopened.

Resolve before numerical execution in one of two honest ways: implement a cell-reference-selective XML reader that converts only the barcode ID and authorized treated Count cells, or append a pre-execution protocol correction acknowledging full numeric row parsing on the two sheets while restricting all retained/used biological arrays to the 36 treated Count columns. The latter is within the user's broad research authorization but changes the local decoding claim; it must not be silently described as selective decoding afterwards. No user permission question is needed for a transparent authorized correction. Neither option authorizes reading S4 or other sheets.

This issue was sent to the parent immediately rather than held for the final review. It is an integrity/scope issue, not a demonstration that the predictor uses vehicle information. The inspected predictor inputs contain only the retained treated compositions.

## Validity checks that pass static inspection

- The held-out End does not enter `predict`, kernel bandwidth computation, source target fitting or hyperparameter/class selection. `select` only iterates outer training cultures and removes each inner validation culture from its fitting source set. The main outer held-out End is read only for loss.
- Early-only prediction classes read no Middle values. The full selection routine computes Middle classes too, but `early_best` compares only the fixed EARLY family list. This does not create a Middle path into the Early prediction/choice under the inspected code.
- The fixed all-cohort Early union is a coherent explicitly transductive contract. It differs from the fold-only vocabulary proposed in the independent review but does not use End to enroll features. Both information arms share the same coordinate set and OTHER. All twelve Early assays being known must remain explicit in every resulting claim.
- Preparation sums all authorized barcode counts into either a known coordinate or OTHER before normalizing. It does not discard later-only mass or renormalize only the Early-known coordinates. The Hellinger and TV losses include OTHER.
- Treated sample bindings use the expected Early/Middle/Late_Resistant stage labels and integer suffixes 1/2/3; the inspected stage mapping and blocked fold construction therefore match the authenticated metadata.
- Condition centroids use only available source End labels with same-condition preference. Direct kernels/ridge receive the appropriate Early or Early+Middle compositional features and known condition, and their bandwidth scale uses source-source distances only. Ridge and stage outputs are explicitly converted to valid compositions by the declared clip/square/normalization rules.
- Nested model-family choice excludes the outer target label. Early and Middle selected procedures are genuine source-selected policies, not outer-target-selected oracles. The primary paired within-class comparisons are particularly important because the Middle-access family menu is larger than the Early family menu.

These are static-code conclusions, not independent execution verification. The three reported synthetic tests exercise normalized outputs, outer-label invariance and Early prediction's Middle invariance. This review did not rerun them.

## Scope/reporting qualifications, not execution blockers

The index-blocked outer test holds all four same-index cultures out of training. Its inner tuning is still leave-one-culture-out on the eight available source cultures. This is a valid held-out outer test of a policy tuned by source LOO, but it is not nested index-blocked tuning. The current protocol says inner validation leaves complete cultures, which matches the implementation. Do not call it index-blocked at every level. Changing inner tuning is optional future design work and unnecessary to preserve outer test validity.

The protocol promises four condition means and a leave-condition-out descriptive sensitivity of the paired difference; `evaluate.py` currently stores per-culture rows and overall means rather than automatically writing those summaries. The complete stored rows suffice to produce those reporting summaries without rerunning predictors. Include them before final interpretation and do not treat deleting a condition after observing its effect as a new favorable primary analysis.

The all-cohort Early vocabulary discloses that certain IDs exist in other cultures' Early samples. That is allowed here because the cohort's Early inputs are declared observed, but this forecast does not establish deployment to a wholly unseen cohort. Middle-discovered IDs outside that cohort-Early vocabulary stay in OTHER; the output consequently cannot resolve those individual clones.

Selecting the best Middle-access family has more candidate programs than selecting the best Early family. Nested source validation makes the outer result meaningful, but the selected-procedure contrast combines extra information and the allowed source-selected method portfolio. Retain all paired kernel/ridge/shrink contrasts so an apparent gain is not presented solely as an information effect when it depends on changing model family. No equal-search-budget, equal-wall-time or agent claim is warranted.

The code recomputes square-root feature products for many nested predictions. If runtime becomes problematic, cached prefix distances could preserve the mathematics, but this is an efficiency observation, not a reason to refactor before a bounded pilot. Log actual costs and do not silently change methods after decoding.

The loss formula is appropriate for normalized nonnegative vectors, and count validation fails rather than treating missing cells as zero. If the workbook violates those assumptions, preserve the failure and inspect its concrete encoding before any imputation; do not use a partially prepared subset as successful evidence.

## Final boundary

After the decoding-scope inconsistency is explicitly fixed or amended and the actual final code/protocol hashes are frozen, this reviewer supports running the finite ordinary baseline pilot. It evaluates a shared-ancestor composition information opportunity. It cannot establish functional drug utility, a novel world-model update, active acquisition, inheritance or RSI. There is no need to delay these baselines for full functional-source qualification or a new architectural proposal.
