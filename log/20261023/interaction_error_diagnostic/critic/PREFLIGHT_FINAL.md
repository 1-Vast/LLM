# Final static preflight: proceed with scoped development diagnostic

2026-10-23. Reviewed amended run.py and test_pipeline.py without running the biological program or reading assay values. No remaining execution-blocking defect identified within this static scope. The requested fixes are present: calibration fits once in raw source-mean units; pipeline calls, estimator fits and kernel solves are logged separately; per-pair truth/predictions, support/inner/query indices, development-only score matrix and incidence matrix are retained in log/PREDICTIONS.npz with pair IDs and byte hashes.

Reviewed hashes:

- run.py: ad31d0d83df0262de45be328376d3cb2ecaef9b6a326532f9fe24d9c3a36fe11
- test_pipeline.py: 967523a4b18ee72720f1449ccb00688f232fd25e0bb6b81b18d65d5fdea4d7a5
- PLAN.md: 38aea4b6229b2db07439fc4fb2c66a6d94706548394363d77bb6ede5638d4b9f
- AMENDMENT_BEFORE_VALUES.md: 89edf88d5e6c3b740f4c77ad845e0efdd5bb98d747883173bcdd533864b6e3ad

Test source meaningfully checks nonnumeric lung poison rejection avoidance, mirror mismatch stopping and control/self exclusion, target-query-response mutation independence for all SCORE/IDENTITY fit_predict variants, and nested support/query disjointness. Parent reports3tests passed; critic inspected source but did not independently rerun or inspect a test execution receipt. The query-response test covers estimator calls, not an exhaustive main-loop/dataframe security guarantee. Source checks plus static main-loop review support the scoped access contract.

Amendment's source-feature-only all-row scaling is lawful for declared completed-source-screen features. Model fitting/validation reads only target-support labels; query outcomes enter final metrics/retained evaluation arrays. Lung cells never pass value/float; XML-byte contact remains disclosed. Within each salt Q excludes S512for both budgets; across salts Q differs and is masking robustness only. Endpoints absent from support have zero/shrunk prior behavior. Ranking uses stable tie order and evaluation-only bottom20oracle in published GI units.

Proceed within these exact code/protocol hashes and inherited scope. If mirror/value availability conditions abort, preserve the attempt and numerical exposure before any amended rerun; do not silently relax them. The both-budget heuristic only decides this fixed lead, so preserve separate512signal and coverage if128fails. Positive identity-aware performance can nominate ordinary recurring score error, including normalization effects; it is neither a new algorithm nor a world/agent/RSI result. No lung opening follows automatically.
