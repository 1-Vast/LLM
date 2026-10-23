# Statistical review and corrected interpretation of the original validation

This review uses only the saved results, configuration, and implementation in `innovation_validation_20261020`. No models were refitted, no new evaluation outcomes were generated, no API was called, and no previously sealed outcome was opened. The registered statistics and scientific results are preserved. This document and `STATISTICAL_AUDIT.json` provide interpretation corrections and post hoc sensitivity analyses; they do not establish the effectiveness of the repaired algorithm.

## Conclusions retained and narrowed

| Question | Corrected interpretation |
|---|---|
| H1: does the original implementation beat the conventional comparator by 0.01? | **NO_SUPPORT**; the negative result is robust within the current synthetic task distribution. |
| H1: is the repaired algorithm effective? | **NOT_TESTED**; old outputs cannot evaluate a new algorithm. |
| H2: does inheritance beat the more expensive restart? | The original registered **NO_SUPPORT** result is retained. |
| H2: does inheritance contribute under equal resources? | **NOT_TESTED**; the original comparison did not equalize cumulative compute budgets. |
| H3: incremental benefit of the joint method | The original registered **NO_SUPPORT** result tests the increment from policy adaptation when structure evolution is enabled. |
| H3: factorial interaction | The post hoc diagnostic provides no evidence of a positive interaction and cannot replace the original primary test. |
| H4: independent measured drug-discovery utility | **NOT_TESTED**; the original public-data replay is development evidence. |
| Witness specificity | The current decoupling intervention does not separately identify this contribution. |

## Compute budgets and resource counts

The original `iv_run.py:234` permits at most 12 candidates per generation for inheritance, versus `12 * generation` for restart. The cumulative four-generation caps are 48 and 120. Sharing raw data and validation rules does not equalize compute. The current results show that a more expensive search from scratch can match inheritance; they do not establish that inheritance has no benefit at equal resources.

| Saved-result subset | Inherit candidates | Restart candidates | Inherit validation replays | Restart validation replays |
|---|---:|---:|---:|---:|
| 96 normal streams | 1,482 | 4,714 | 5,912 | 18,732 |
| All 144 streams | 3,004 | 10,222 | 11,972 | 40,724 |

The original report incorrectly labels the second row as 96 normal streams. The JSON contains the complete counts for every arm.

The original `iv_run.py:110` and `:125` use `time.perf_counter()`. The 115,883.356 seconds are **summed stream elapsed time**, approximately 32.19 hours, rather than measured process CPU time. Multiplying 26 processes by 78.9 minutes gives 34.19 process-capacity hours, which also does not measure actual CPU use. Replace the original claim of "2.3 times the CPU" with "approximately 2.3 times the recorded arm elapsed time"; end-to-end compute efficiency is not established. GBM training for contract E is charged entirely to `gbm_var`, contract T training lacks the corresponding charge, and some shared fitting costs are not allocated. The existing arm columns therefore cannot directly compare complete method costs.

A future equal-resource comparison must separately freeze an incremental per-generation or cumulative end-to-end budget, account for candidate discovery, fitting, validation, retries, and shared costs, and record both process CPU and wall time. Truncating saved candidate lists cannot reconstruct a fair control. This review did not run that new comparison.

## Paired stratified sensitivity analysis

The original `iv_stats.py:58` resamples whole streams and retains repeated draws, correcting the earlier study's bootstrap deduplication problem. The three pooled primary tests use 98.333% intervals; the Bonferroni convention is reasonable for those three comparisons. It does not automatically cover secondary analyses, individual families, anchors, or mechanistic attribution.

This review fixes 24 alias and 24 compose streams, assigns each family weight 1/2, and resamples paired differences within each family. The statistical unit remains one independent synthetic stream. Its 12 contract E task outcomes from generations 2-4 are averaged first. Streams are ordered by filename; family order is alias, then compose. Each contrast reinitializes NumPy `default_rng(20261020)`, uses 20,000 resamples, and takes primary sensitivity quantiles `0.05/6` and `1 - 0.05/6`.

| Contrast | Mean | Stratified 98.333% interval |
|---|---:|---|
| H1: inh_kg - lat_aopt | +0.001697198 | [-0.001950897, +0.005670922] |
| H2: inh_kg - rst_kg | -0.000049681 | [-0.000774588, +0.000610349] |
| H3: inh_pol - inh_kg | -0.001275910 | [-0.003786427, +0.000491126] |

All three upper bounds remain below the original 0.01 margin. This sensitivity analysis does not replace the registered analysis, change the original implementation's results, or resolve H2's unequal resources.

## What H3 says about interaction

The original H3, `inh_pol - inh_kg`, measures the increment from adding policy adaptation when structure evolution is already enabled. It is not a factorial interaction. The minimal four-arm interaction is:

`I = (inh_pol - inh_kg) - (fix_pol - fix_kg)`.

The four arm means, in that order, are `0.8868147326242389`, `0.8880906431133685`, `0.8863034000854313`, and `0.8868211469668802`. The mean interaction is `-0.0007581636076808169`; it is `-0.00042647027406591637` in alias and `-0.0010898569412957175` in compose. The post hoc 95% interval from the stratified bootstrap above is `[-0.0026456085072635075, +0.0007887272996844284]`.

This analysis is `POST_HOC_DESCRIPTIVE_NOT_CONFIRMATORY` and provides no evidence of a positive interaction. Even a positive interaction in a future study would require the joint method to beat strong single-adaptation and conventional baselines under equal resources before supporting a useful innovation.

## Decoupling does not complete the current mechanistic attribution

The original `iv_worlds.py:73-84` replaces the compose late gates' normal activation probabilities of 0 early and 0.55 late with 0.5 in all decoupled tasks and anchors. The intervention therefore changes cross-class dependence, temporal structure, marginal distributions, and task difficulty together. Contract T also divides probes and targets within each class, so information can still transfer within a class.

Narrow the original conclusion, "the advantage did not disappear, therefore it is not witness-specific," to: **the current control does not separately identify the contribution of the cross-class witness mechanism**. A future control intended for causal attribution should preserve activation marginals within each phase and preserve nuisance/noise, while disrupting only the specified dependence. This review does not use new control outputs to rewrite the old evaluation.

## Withdraw the unsupported recommendation for 12 backgrounds

The original report requires at least 12 backgrounds, with 8 released as history, leaving only 4 evaluation backgrounds. The qualification file simultaneously requires 16-24 held-out backgrounds; these prescriptions conflict. The 48 synthetic streams are independently generated worlds with different drugs, hidden gates, and tasks. Their stream-level standard deviation cannot be substituted for the standard deviation of an individual measured background.

The original `(1.96 * s / 0.01)^2` approximates planning for confidence-interval half-width rather than a superiority test with specified power. Requiring a lower bound above a useful-gain margin `delta` needs an anticipated true gain `Delta > delta`. A simple independent-unit approximation is `n ~= ((z_(1-alpha) + z_(1-beta)) * s / (Delta - delta))^2`; the actual independent units, correlated backgrounds, replicates, multiplicity, and small-sample behavior still require treatment.

Withdraw the specific "12 backgrounds and approximately 350 pairs" experiment-size recommendation without proposing a new wet-lab purchase. H4 remains **NOT_TESTED**. Only observation-structure requirements can currently be retained: a common comparable action pool, traceable measured responses, and separation of history from evaluation. Measured variance, independent units, and sample size remain undetermined.

## Further interpretation limits

- "Strongest conventional method" means the tested pipeline selected on development data, not the strongest of all possible algorithms. Using the frozen development-selected comparator for H1 is reasonable.
- The per-stream post hoc best-of uses evaluation results to select a method. It is an oracle reference, not a deployable baseline; its set also includes acquisition variants using the inherited library.
- `demonstrated` is an internal promotion rule on four validation backgrounds, not independent scientific proof. Evaluation on subsequent tasks can still assess the entire selection procedure; this issue does not invalidate every primary result.
- The known `compose_8/rst_kg/gen4` anchor-program inconsistency did not affect the primary task comparisons. Retain the exception and report anchor sensitivity rather than claiming unconditional software validity.
- Secondary analyses such as H5 are outside the multiplicity correction for the three primary tests. A small post hoc positive difference cannot replace the failure to meet the useful-gain margin.

## Rebuild

```powershell
.venv/Scripts/python.exe research/innovation_validation_repair1_20261020/r1_statistics.py --out research/innovation_validation_repair1_20261020/STATISTICAL_AUDIT.json
```

The script reads only saved files from the original package. It produces reproducible JSON containing the registered summary, stratified sensitivity analysis, post hoc interaction, resource counts, and input SHA-256 hashes. It neither executes the original experiment nor updates the original package.
