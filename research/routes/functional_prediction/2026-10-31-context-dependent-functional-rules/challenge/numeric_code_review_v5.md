# Independent admission of the single schema repair — v5

2026-10-31. **Scoped repair execution admitted** for exact numeric freeze SHA-256 `2b86e5d5d1b10a244fd84b202ee839ae7440810cfc0add0fc7c39faff26dac52`, through `launcher_v5.py` only. This is the one implementation-only repair after the preserved initial 5.594-second CSV parse failure. V4 was reviewed but never launched; completing its prelaunch corrections did not consume another numerical attempt. Another execution failure stops this matrix under the frozen rule.

## Independent verification

Read `review/complete_missing_repair.py`, the actual exact diffs from v4 to `experiment_v5.py`, `protocol_v5.md`, `launcher_v5.py` and `check_arithmetic_v5.py`, and the actual v5 freeze. Independently hashed all eight frozen files and checked their byte sizes: all match. Independently computed the freeze SHA: it matches the value above. Data hashing remained opaque byte access; no count/response values were displayed or decompressed for inspection.

Independently executed only the artificial-data `check_arithmetic_v5.py`, exit 0 PASS. This includes inversion for the frozen grid, exact raw-Q algebra, identity zero, nonlinear example, target-double poison invariance, guide-orientation averaging, empty versus observed-zero handling, and rejection of artificial nonempty tokens `nan`, `inf`, `-1`, `0.5`, `NA`. No experiment/launcher stage, model fit, scoring, HTTP, installation, author code, weights or protected resource was executed/accessed by the reviewer.

The previous current admission was copied byte-for-byte to `review/execution_admission_v3.json` before replacement. Its preserved SHA-256 is `74409b04172066fa3d958605286c769e9feaa9a5e1c7fd6b187570bd371f03a8`. The original v3 frozen files and failed run evidence are preserved; v4 frozen bytes are also unchanged.

## Resolution and retained checks

The two outstanding v4 conditions are resolved. Only stripped-empty strings now produce NaN. Every nonempty parsed value is immediately required to be finite, nonnegative and integer-valued, so a nonempty NaN token cannot disappear through subsequent missing-value exclusion. The new synthetic rejection cases test that contract.

The fit record now saves counts for original T0-only passing constructs, those remaining after UT availability, final common-paid-control availability, and each availability removal step, plus source-development unobservable pairs by culture and train/validation totals. These quantities derive only from already allowed inputs/source labels. Their recording does not alter masks or model selection.

The substantive v4 repair checks remain valid: input masks depend on T0/paid UT and paid single/NTC availability only; target and held-source double availability cannot select predictions; common control identities are shared across conditions/cultures and raw/transformed contrasts; source fitting uses complete whole-pair labels; scoring uses unchanged construct weights and identical matched observable pairs for every model. Missing labels remain NaN and have explicit denominators/coverage. Prediction-side support/identification gates retain the full prediction denominator. Ranking keeps the original top 100 and separates confirmed hits, assessed nonhits and unassessable selections. No unavailable pair becomes a biological zero or a replacement ranking candidate.

The repair does not change the transform family, source/target roles, pair hash, source-only hyperparameters, primary utility margin or ordinary rival information. It preserves a meaningful test of the same restricted functional hypothesis. Its additional label-coverage gate is prospective and conservative; it does not establish random missingness.

## Exact scope and limits

One repaired staged matrix is admitted in the supplied Windows maestro environment, with inherited affinity limiting execution to at most four allowed logical CPUs, four threads per numerical pool, and aggregate **1794.4059999999881 seconds** remaining for fit plus score. The launcher checks this exact freeze and current admission before launching `experiment_v5.py`. New output is `run_repaired`; new logs/receipt are separately named. This admission does not permit old launchers, automatic reruns, a fresh 1800-second allowance, target calibration, family enrichment or unplanned scientific rescue.

Any utility result is **internal and restricted to the observed matched subset**. >=80% label coverage is not evidence for performance on unavailable pairs. A common-coordinate result does not establish novel algorithm, exact latent invariance, molecular mechanism, independent biological replication, prospective sparse-library savings, new-drug efficacy or general Virtual Cell capability. Both source ancestries train the model; shared T0/UT, count/pseudocount dependence and selected genes remain material limitations. No Agent/core promotion follows this matrix.

The initial scientific review, v1 code review, v3 admission and missing-data scope note remain the scientific interpretation context. No numerical scientific result is claimed by this pre-execution admission.
