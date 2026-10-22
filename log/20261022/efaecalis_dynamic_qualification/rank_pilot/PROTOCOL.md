# Frozen-prefix relative-readout allocation gate

Registered 2026-10-22 before the first finite Fig4B response read. This is a small exploratory resource gate, not a new algorithm, a prospective experiment, or evidence for a world model, agent, inheritance, or RSI. Independent review: `../RANK_PILOT_INDEPENDENT_REVIEW.md`.

## Task and source

Application: conditional on an existing completed historical cohort and routine early monitoring, choose three new CRO-selected E. faecalis populations for sustained DOX relative-readout verification over six future dates. A single roster is selected at day6 and used for days8–13. Low **exported relative IC50** is preferred; neither absolute drug sensitivity nor clinical efficacy is asserted. The previously proposed individual-AUC and absolute-error IC50 gates remain NOT_EXECUTED. Published day8–13 relevance was designer-exposed; this is not window discovery.

Source is the official S1 Data workbook, `../redirect_followup/pbio.3002970.s001.raw.xlsx`, SHA256 `273cc82c826f245be228a7fd21673fca13eaee1b949183f3b179b86bbce1fb27`. Fig4B D34:W34 contains persistent population IDs1–20; C35:C48 contains days1–14. Open only D35:W40 (days1–6) and D42:W47 (days8–13): exactly240 response coordinates. Do not open day7/day14 or the OD/AUC panels. Plain finite numeric cells are mandatory. Any missing, formula, error, string, duplicate or nonfinite response stops this configuration; no imputation, exclusions, substitute endpoint, or rerun.

The unresolved ratio versus log2(ratio) storage does not affect daywise order under a common increasing transform. Unknown population-specific normalization prevents an absolute-IC50 interpretation. Existing published figures, prior string/nonfinite exposure and source-design audits mean this is not sealed independent confirmation, although these240 finite values have not previously been interpreted by the current team.

## Split, information and cost

Sort IDs1–20 by SHA256 of UTF-8 `efaecalis-rank-gate-v1|split|{id}`; first10 are development, last10 test. Freeze the ordered lists in FREEZE.json before opening responses. All downstream tie breaks use SHA256 of `efaecalis-rank-gate-v1|tie|{id}`. Units are populations, not dates, pairs or cells.

This simulates completed historical development populations followed by new test populations under the same protocol; it does not claim that original parallel populations' future was available at original day6. Development receives60 prefix and60 future population/day IC50 observations. Test receives60 prefix observations. Every arm receives the same inputs, training labels and future verification budget (3 populations ×6 dates=18 slots). Full retrospective test scoring additionally opens all60 test future values; those are evaluation-only. This is240 archived population/day cells total, not a claim of prospective net assay saving. No money, wells or elapsed-time advantage is inferred from cell counts.

## Target, models and allocation

Within development and test cohorts separately, compute each day's observed midrank percentile `(count_less + 0.5*count_equal)/n`. Development future labels are computed using only development future values. No future test normalization enters training. Each population's target is its mean future percentile across days8–13. Utility of a roster is mean `1-target` for its three selected test populations; larger is better. Ties in observed values retain midranks. Predictions are lower-is-preferred and their ties use the frozen ID hash.

Candidate is **ordinary ridge6**, six daily prefix-percentile features, fixed alpha=1, centered X and y, unpenalized intercept, no scaling or tuning. Two gate comparators are day6 rank persistence and ordinary ridge1 with only day6 rank and the identical ridge specification. Also report mean-prefix persistence, uniform3-nearest-neighbor prediction using six ranks (Euclidean distance; development ID hash resolves distance ties), and calendar-only prediction (all0.5; hash resolves roster). No model selection or ensemble is made. Ridge6 is a direct predictor used to test headroom; a pass is not a world-model contribution.

## Uncertainty and stopping

Primary point differences: ridge6 utility minus each of day6 persistence and ridge1. For each of10000 deterministic bootstrap draws (NumPy default_rng seed20261022), draw10 complete test-population trajectories with replacement; keep fitted models/predictions fixed, recompute future daily midranks within the draw, and select the lowest3 predicted draws. Duplicate draws represent empirical mass, never additional independent biological trajectories; exact prediction ties use ID hash then draw position. Record paired differences and2.5/50/97.5 percentiles. This is **conditional empirical-bootstrap sensitivity**, not a confidence interval with guaranteed nominal coverage. It omits training uncertainty and is limited by non-smooth top-k selection and only10 test populations.

Also evaluate all45 delete-two subsets of8 unique test populations, re-rank futures, retain the fixed budget3, and report paired differences. These are roster-sensitivity analyses, not45 independent experiments or the original3/10 decision.

PASS_TO_ONE_NARROW_ALLOCATION_FOLLOWUP only if BOTH gate comparisons have point improvement at least0.10 and bootstrap2.5th percentile strictly above0. Otherwise STOP_THIS_SOURCE_CONFIGURATION_FOR_FRAMEWORK_EXPANSION, including inconclusive results. Report all delete-two values without using them to move the threshold. A pass purchases one limited allocation follow-up and new mechanism review; it does not purchase architecture expansion, novel-method status or an RSI claim. Never retune from test responses.

## Execution and verification

Implementation and tests are under `research/efaecalis_dynamic_qualification_20261022/`. Synthetic tests cover monotone-transform invariance, split determinism/disjointness, tied observations, strict response scope/type checks, fixed-fit test-future separation and equal-prediction sensitivity. Run synthetic tests, freeze protocol/code/tests/source/review/identity receipts and split, then open responses and execute exactly once with the maestro interpreter and `-B`. Preserve raw readouts, predictions, rosters, sensitivity arrays, source hashes, runtime and any failure in this log directory. No HTTP or API calls are needed. An independent reviewer will inspect the code and output before interpretation.
