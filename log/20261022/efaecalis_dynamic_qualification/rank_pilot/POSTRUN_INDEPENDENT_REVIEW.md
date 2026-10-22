# Independent postrun review

Reviewer: `/root/functional_auditor`. Date: 2026-10-22 local.

Decision: **PASS_INDEPENDENT_ARITHMETIC_AUDIT; retain STOP_THIS_SOURCE_CONFIGURATION_FOR_FRAMEWORK_EXPANSION.** All 22 saved verification checks pass. No change to the frozen implementation, protocol, tests, or pre-open review was made. No original workbook or additional response coordinates were opened; the single-open main program was not rerun.

## Evidence and independent method

Inputs were `OPENED_RESPONSES.json`, `RESULT.json`, `SENSITIVITY.json`, `FREEZE.json`, and `READ_STARTED.json`, plus the previously reviewed code. Verification code is `research/efaecalis_dynamic_qualification_20261022/verify_rank_pilot_postrun.py`; its output is this directory's `POSTRUN_VERIFICATION.json`. That output includes input/code SHA256 values, all checks, exact rational utilities, population qualities, and frozen-file checks. The maestro interpreter ran the verification successfully with `-B` and exit code0.

The verifier does not import the pilot implementation. It computes midranks by sorting and grouping tied observations; it solves ridge as an augmented least-squares problem with a separate intercept column and identity penalty rows for slopes. This is algebraically equivalent to the registered centered alpha1 fit but uses a different numerical route. It reconstructs all six predictions and rosters, all 10000 paired bootstrap differences and their quantiles, and all 45 delete-two differences. All agree with saved outputs within absolute tolerance1e-12; roster IDs agree exactly. Exact rational ranks independently reproduce the utilities.

## Scope, split and information flow

The saved response object has exactly the 240 allowed unique coordinate keys D35:W40 and D42:W47, all plain finite decimal strings and finite after float conversion. The saved identity metadata matches days1–6, days8–13, and persistent IDs1–20. No day7/day14, OD, or AUC cells occur. Duplicate JSON keys are rejected by the verifier. Workbook cell type and duplicate-coordinate enforcement are established by the frozen reader and execution receipt, rather than a new raw-workbook inspection.

The independent salted SHA256 split is development `[16,17,14,12,6,9,15,1,10,2]` and test `[20,8,19,18,11,5,3,7,13,4]`, identical to the freeze and result. Training labels are future daily ranks within development only. Prefix ranks are within each cohort separately. Predictions use prefix data plus development future labels; test future ranks enter only scoring. Replacing all test futures with a constant leaves every independently recomputed prediction identical. The static main call uses the same separation. This verifies the disclosed historical-cohort simulation, not original-calendar prospective availability.

## Auditable utility arithmetic

Let each population's quality be one minus its average future midrank across the six evaluation dates. Roster utility is the mean of three such qualities. Larger utility is preferred.

| Method | Selected population IDs | Exact mean quality | Decimal utility |
| --- | --- | --- | --- |
| ridge6 | 19,20,18 | `(3/4 + 31/60 + 8/15)/3 = 3/5` | 0.600000 |
| day6 | 13,19,5 | `(2/3 + 3/4 + 7/20)/3 = 53/90` | 0.588889 |
| ridge1 | 13,19,5 | `53/90` | 0.588889 |
| prefix mean | 18,13,19 | `(8/15 + 2/3 + 3/4)/3 = 13/20` | 0.650000 |
| 3-neighbor | 19,5,20 | `(3/4 + 7/20 + 31/60)/3 = 97/180` | 0.538889 |
| calendar/hash roster | 7,11,19 | `(1/2 + 43/60 + 3/4)/3 = 59/90` | 0.655556 |

Each primary difference is `3/5 - 53/90 = 1/90 = 0.011111…`. For both registered comparators, the conditional bootstrap2.5/50/97.5 percentiles are `[-0.161111…, 0, 0.172222…]`; all saved draw differences match the independent recomputation. The delete-two difference range for both is `[-0.055555…, 0.145833…]`, with all 45 subset values matching. The point difference fails the registered minimum0.10, and the lower bootstrap quantile fails the strictly-positive requirement. Either failure suffices; both fail for both comparators. STOP is therefore unambiguous under the preregistered rule.

Prefix mean and the fixed calendar/hash roster have descriptively larger utilities on this small test cohort. They are reported for transparency, not selected after the fact as a new candidate, and do not justify reopening the failed gate.

## Freeze, single-open and budgets

The freeze timestamp is 2026-10-21 18:46:47.478866 UTC; READ_STARTED is18:46:54.589622 UTC; result is18:46:55.665469 UTC. This order is consistent with pre-open freezing and a started-read sentinel before result publication. All 11 execution freeze checks are true. I independently rehashed the ten nonworkbook frozen files and all remain unchanged, including the pre-open independent review and live helper modules. The raw workbook was deliberately not reopened or rehashed by this auditor: its identical expected hash is recorded in the freeze, started-read, opened-response metadata and the execution's successful check. These receipts establish consistency; they are not an independent second source read or a proof about unlogged external access.

Budget fields are consistent:60 development-prefix +60 development-future +60 test-prefix +60 retrospective evaluation-future =240 archived observations;18 nominal future verification slots per arm. Full test-future evaluation uses all60 values, so there is no verified prospective net assay saving. The result's approximately1.07s wall/1.05s processCPU ledger is explicitly the primary root execution only. The separate audit computation is excluded, as disclosed; it uses saved JSON and no API calls, source requests or additional biology.

## Interpretation and stopping

The bootstrap is conditional empirical sensitivity with a fixed trained fit and only ten test trajectories. Duplicate resamples are empirical mass, not new biological units; top-three selection is non-smooth. The recorded `nominal_CI_claim: false` and the protocol's language are appropriate. No nominal confidence coverage, biological replication, clinical efficacy, absolute sensitivity, or assay-cost benefit is established. Unknown population-specific normalization and earlier design/window/nonfinite-string exposure remain limits.

The saved claims correctly mark world model, agent, inheritance and RSI **NOT_TESTED**, and novel algorithm false. This result stops framework expansion from this source configuration. It does not refute every possible world-model or RSI design; it gives no empirical support for those capabilities and no basis to relax the registered gate, retune on these test outcomes, or claim a new mechanism.
