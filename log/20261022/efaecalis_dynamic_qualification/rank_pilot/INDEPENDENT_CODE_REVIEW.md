# Independent pre-open code review

Reviewer: `/root/functional_auditor`. Recorded 2026-10-21 18:45 UTC (2026-10-22 local).

Decision: **NO_BLOCKING_CODE_ISSUE_FOR_THIS_EXPLORATORY_GATE**, for the exact files below and subject to the pre-open freeze and synthetic-test requirements in the protocol. This is permission to evaluate the registered resource gate, not evidence for efficacy, a novel mechanism, a world model, an agent, inheritance, or RSI.

## Scope and exposure

I inspected the protocol, `rank_pilot.py`, `test_rank_pilot.py`, and existing identity receipts. I did not open the source workbook, biological response arrays, or outcome/result files; I did not run an experiment or change the protocol or implementation. The root reports 12 successful synthetic tests; this review independently inspects the tests but does not independently execute them. The existing identity receipt reports 275 design-only coordinates, the authenticated source hash, and unchanged previous freezes; it does not certify finite response quality for the 240 coordinates about to be opened.

Reviewed SHA256:

| File | SHA256 |
| --- | --- |
| `log/20261022/efaecalis_dynamic_qualification/rank_pilot/PROTOCOL.md` | `504b1d8f17c18f309b2a160613dfcf35fd446c4b3f46c41d2a3389b39076c771` |
| `research/efaecalis_dynamic_qualification_20261022/rank_pilot.py` | `446b87a7dc7acf58cfc396d37774e0e0bef7f2278cd76989f108960fb58cf251` |
| `research/efaecalis_dynamic_qualification_20261022/test_rank_pilot.py` | `7d16af191d7c68b4eb873cd22910c1ca77a00e023e54d8dc4d0077294a004768` |

## Checks and conclusions

1. **Coordinates and units.** `response_allowlist` and `read_responses` use Fig4B D35:W40 and D42:W47, exactly 20 populations by 12 dates = 240 cells. These match the identity receipt's persistent IDs D34:W34 and day mapping C35:C48. Day7, day14, raw OD panels, and AUC summaries are excluded. Arrays are six prefix dates and six future dates in persistent source-column order. The reader's plain-numeric/type checks are inherited from the previously qualified helper; the pilot additionally rejects float conversion overflow/nonfinite results.

2. **No test-future input to fitting.** `predict` receives all prefixes, development future only, and frozen IDs. Development and test prefix ranks are computed separately, and the target uses development futures only. The main path passes only development future columns to `predict`; test futures enter evaluation afterward. This is a completed-historical-cohort simulation, as disclosed, rather than a prospective claim about the original parallel experiment.

3. **Mathematics and comparator definitions.** Midrank code implements `(count_less + 0.5*count_equal)/n` along the population axis and preserves observed ties. Ridge centers X/y, applies alpha=1 to coefficients, and leaves the intercept unpenalized. Ridge6, ridge1, day6, mean-prefix, uniform three-nearest-neighbor, and calendar outputs match the protocol. Squared Euclidean distance gives the same neighbor ordering as Euclidean distance. Rosters select the three lowest predictions with the registered deterministic hash tie break. Evaluation quality `1 - mean_future_midrank` and mean roster utility have the registered direction and meaning. No tuning or model selection appears.

4. **Sensitivity calculations.** Bootstrap draws ten complete test trajectories with replacement, holds fitted predictions fixed, re-ranks the sampled futures, and uses three selected draw positions. Repeated biological IDs can occupy multiple positions; this is correctly disclosed as empirical mass and not additional biological replication. The paired differences and percentiles implement the registered conditional sensitivity calculation. All 45 delete-two subsets contain eight distinct original test populations and retain three slots. Neither calculation supplies guaranteed nominal confidence coverage or training uncertainty. The protocol and result fields state those limits, so no statistical interpretation blocker was found.

5. **Budgets and claims.** The 60 development-prefix + 60 development-future + 60 test-prefix + 60 evaluation-future ledger sums to 240 archived readouts. The nominal verification budget is 3 populations by 6 future dates = 18 per arm; all 60 test futures are nevertheless opened for retrospective evaluation. No prospective assay, cost, time, or clinical benefit follows. Execution wall/CPU fields now make their scope explicit and exclude prior qualification and reviewer inference. All six methods receive equal available information, with fixed fitting specifications. This narrow direct-predictor gate does not substitute for the broader framework's required comparisons against retraining, continual learning, active learning, mixing, or equal-budget program search.

6. **Freeze and one-open path.** The current freeze list (implementation lines114–120) includes protocol, code, tests, synthetic receipt, raw source, numerical reader/helper modules, transitive local `redirect_followup.py`, this independent review, the prior scientific review, and the identity receipt. This resolves the earlier omission of live reader dependencies/current code review. Execution checks all frozen hashes before response reading and again before successful result publication. It creates `READ_STARTED.json` before `read_responses`; the previously audited exclusive-create helper and the initial existence check prevent another run after a started read, including a failed one. A partial failure must remain stopped; no deletion/retry is authorized by this review. `freeze` hashes source bytes but does not decode response cells.

7. **Stop rule and test adequacy.** PASS requires both registered point improvements at least0.10 and both bootstrap2.5th percentiles strictly above0. Otherwise the code stops this source configuration, including inconclusive outcomes. Tests cover split completeness/determinism, monotone-transform invariance, observed ties, invalid ranks, a constant-target ridge case, test-future separation, equal-prediction paired sensitivity, roster ties, exact240 synthetic scope, and missing/formula/nonfinite responses. The out-of-scope invalid synthetic D41 value is correctly used to check response-scope restriction. No new tests are necessary to resolve a specific observed code defect.

## Remaining limits and handoff

The finite response values are still unreviewed by this auditor. Small sample size (ten test populations), fixed training fit, non-smooth selection, unknown population-specific normalization, prior published-figure/window exposure, and earlier nonfinite-string exposure remain scientific limits already disclosed in the protocol. The conclusion applies only to exported relative-readout ranks. A favorable gate would justify one narrow follow-up and another mechanism review; it would not validate framework expansion. Freeze this exact review and current files before the first response decode, preserve all failures, and audit output interpretation against these limits after execution.
