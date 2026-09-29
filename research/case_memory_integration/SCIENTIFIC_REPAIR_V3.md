# Scientific repairs: explicit outcomes, one smoothing step, scoped calibration

> - **Path**: `research/case_memory_integration/SCIENTIFIC_REPAIR_V3.md`
> - **Purpose**: record implemented scientific boundary fixes separately from uncompleted empirical validation.
> - **Core points**: version 3; one Dirichlet estimator; grouped development calibration; no external performance claim.
> - **Depends on**: `DESIGN.md`, historical `SHRINKAGE_DIAGNOSIS.md`, `tools/case_memory/validate.py`.

## Result and scope

The code now states what outcome is predicted, which measurements may be used as inputs, where
a fitted parameter applies, and which layer owns smoothing. It adds no neural network or parallel
world-model framework. The categorical estimator replaces two unfitted transformations with one
Dirichlet step and, optionally, one fitted scalar. Existing continuous calibration in
`src/virtual_cell/calibration.py` and its state adapter remains the separate implementation for
continuous predictions; no duplicate interval framework was introduced.

The default feature flag remains off. `calibration_status=uncalibrated` is intentional even when
`calibration_fit=development_only`. A development fit is not an external qualification receipt.
The runtime tool does not automatically load the experimental fitted profile; it is supplied
explicitly to `CaseMemoryOutcomeForecaster` during the development experiment.

## Working issue register

The twelve work items below group the concerns addressed in this repair. Engineering closure
means a behavior is implemented and tested; it does not mean biological validity was demonstrated.

| # | Issue | Current status | Remaining evidence or work |
|---|---|---|---|
| 1 | Raw expression treated as a signed effect | Contract fixed | `value_kind` admits declared signed effects/log-fold changes/differential z-scores; raw counts and normalized expression are refused. Upstream differential analysis must still be supplied. |
| 2 | Gene rows or technical repeats counted as biological replicates | Fixed | Distinct biological replicate IDs are required; duplicate feature/replicate pairs refuse; gene effects are averaged across biological replicates. Independence metadata must be accurate. |
| 3 | Multiple treatments or scales merged into one state | Fixed | Explicit condition selection, one cell/time/dose context and one effect scale; fatal input returns no state/actions. |
| 4 | Conditional valid readings confused with all experiment attempts | Contract fixed; data incomplete | Four-outcome `valid_readout` and five-outcome `attempted_experiment` are separate. Complete attempts require an explicit denominator. Real failure/missingness data remain necessary. |
| 5 | Future response signature used as initial state | Known builder and retrieval paths fixed | Mark generated signatures `outcome_only`; exclude them from directional retrieval, including known older proxy archives. Data owners must verify temporal availability for other legacy records. |
| 6 | Arbitrary temperature plus strong prior distort probabilities | Fixed | One Dirichlet update; no fixed temperature remains in production. Historical helper remains only for old diagnostics. |
| 7 | No independently fitted calibration parameter | Development fit completed | 44 training / 10 calibration compounds; one pseudocount fitted. Independent confirmation remains open. |
| 8 | User state has no demonstrated incremental predictive value | Open scientific validation | Compare real pre-action state against matched state-free frequencies on later outcomes. Synthetic wiring tests only prove the input reaches the model. |
| 9 | Too few independent evaluation units; repeated items inflate apparent size | Open scientific validation | Current evaluation has 11 compounds, not 156 independent samples. Obtain a new population; size it for paired compound-level uncertainty and domain coverage. |
| 10 | Curated mechanism labels substituted for causal or engagement truth | Admission boundary preserved; real labels missing | Obtain direct engagement/proximal readouts, perturbation/rescue or other appropriate measurements. Transcriptomic similarity remains a proxy. |
| 11 | Action selection lacks multiple comparable measured alternatives | Guards fixed; utility unvalidated | Obtain at least two legal measured actions per problem, with costs and outcome rules. Offline utility requires action coverage and appropriate selection assumptions. |
| 12 | No verified prospective user-data -> action -> observation loop | Open scientific validation | Prospective versioned episodes, frozen predictions before execution, qualified outcomes, error/abstention logs and audited updates. |

Previously completed removal of invented fallback probabilities, hypothesis-conditional support,
independent-unit deduplication, proxy-evidence separation and cache invalidation were preserved.

## The two interface audits

**Prediction versus planning uncertainty.** The forecaster returns both the probability mean and
`posterior_concentration`. Posterior branches are not smoothed again by the planner; interpretation
rules cannot invent mass for extra outcome labels. Legacy empirical branches retain their previous
Jeffreys update. The case-memory ranking no longer subtracts an additional low-support penalty
from already regularised branches. Nonpositive net utility is inadmissible. A report-only
discrimination calculation now uses Jensen-Shannon divergence instead of a difference of maximum
log probabilities, which could miss mirrored, highly discriminating distributions.

This does not eliminate legitimate decision-risk calculations. Kish concentration is an
approximation for weighted frequencies. Current variance does not include shared-training branch
covariance, fitted-parameter uncertainty or arbitrary domain shift. The normal lower bound is not
an empirically verified 95% coverage guarantee. Any explicitly supplied adaptation-risk allowance
must not repeat uncertainty already included elsewhere.

**Calibration transfer.** A `FrequencyCalibration` profile binds to the exact assay, readout,
cell context, laboratory, time and dose tuple, plus outcome mode/count, feature arm, estimator
version and reference-store snapshot. Changing these produces a named refusal; train/calibration
unit overlap is rejected. Numerical time/dose values use a canonical representation. Unknown
laboratory matches an unknown slot only; it does not prove same-laboratory data or transportability.
These are necessary scope checks, not proof that each listed context is adequately calibrated.
Control design, biological system and measurement type also pass through existing retrieval
compatibility rules. Full input truthfulness cannot be inferred from a metadata declaration.

## Outcome and preprocessing contracts

`valid_readout` predicts `P(readout | valid measurement, hypothesis, context, action)`. Its four
labels cannot be used as `P(outcome | attempted experiment, ...)`. The planner and pipeline refuse
that substitution with `experiment_validity_probability_required`.

`attempted_experiment` uses only explicitly declared `sampling_frame=all_attempts` records, includes
QC failure, and refuses known missing or unmapped outcomes instead of quietly deleting them from
the denominator. A successful declaration does not itself prove sampling completeness: upstream
attempt registries and exclusions must be audited. The implementation does not invent an assay
success model or treat lack of publicly reported failures as zero failure probability.

For user expression data, form a matched-control contrast upstream. Do not treat a positive raw
count or standardized abundance as upregulation. Preserve biological replicate, batch, cell,
time, dose and control identity. Collapse technical repeats before this compiler. Single-cell
measurements should normally be summarized at the independently randomized sample/well/donor
level for inference; a million cells do not supply a million independent drug experiments.
The legacy `signed_effect` default preserves compatibility; incorrectly labeling raw input as an
effect remains a caller error that the compiler cannot automatically discover.

## Executed development calibration

Command: `python -m tools.case_memory.validate calibration`.

Only the original 65 reference compounds are used: **44 training, 10 calibration, 11 evaluation**.
The evaluation compounds are the previously inspected development holdout. The frozen external
26-compound population is not used for fitting or scoring this experiment. Training-only data
rebuilds class centroids, norm thresholds and leave-one-compound-out reference labels; calibration
and evaluation responses are evaluator-only. The forecaster is state-free (`FeatureArm.SCALAR`).

For empirical frequency `f_y`, Kish support `n_eff`, K outcomes and positive pseudocount alpha:

`p_y = (n_eff * f_y + alpha) / (n_eff + K * alpha)`.

The baseline uses alpha=0.5. The fitted candidate uses **alpha=1.9883073606**, optimized on
calibration data with equal mean loss per compound. Both models use identical training counts,
the same four labels and the same evaluation items. The evaluator asserts equality between direct
Dirichlet calculations and the actual production forecaster. This is a calibration comparison
within a frequency model, not evidence that a complex world model beats a simple baseline.

| Evaluation metric | Default alpha=0.5 | Development-fitted alpha |
|---|---:|---:|
| NLL per item | 1.360717 | 1.305401 |
| Multiclass Brier | 0.732615 | 0.708332 |
| Equal-compound mean NLL | 1.344871 | 1.295877 |
| Scored items / offered items | 156 / 156 | 156 / 156 |
| Independent evaluated compounds | 11 | 11 |
| Per-branch support | 4-12 | 4-12 |

Six compounds improve and five worsen; equal-compound mean paired NLL change is **-0.048993**.
There is no confirmatory significance or cross-domain claim. NLL measures overall probabilistic
prediction quality, not calibration alone. Some branches remain below the planning support gate;
100% forecast scoring coverage does not imply 100% action applicability.

Do not compare these values directly to the old 1.372004 versus 1.353464 experiment: its label
space and training population differed. The old files under `scientific_fix/` remain historical.

Artifacts: `outputs/case_memory_integration/calibration_v3/summary.json`, `profile.json`,
`split.json`, `items.jsonl`, `development_comparison.png`, `tests.xml`. The chart was inspected:
left-hand labels match the summary, right-hand bars are one per independent compound and include
the worsened cases. Training snapshot:
`6ec27b814fa5ee635d417475e0596ac2d0deadf8a4da344ae08c6d2a05add066`.

## Tests and preservation

Executed full regression:

```powershell
python -m pytest tests research/case_memory_integration -q -o addopts= --junitxml=outputs/case_memory_integration/calibration_v3/tests.xml
```

**1,553 passed**, exit 0. Coverage includes preprocessing errors and aggregation, input visibility,
outcome estimands, unknown attempt outcomes, laboratory filtering, probability/concentration
ownership, legacy compatibility, calibration scope and overlap, tool receipts and orchestrator
paths. Shared test helpers were extracted into `tests/fixtures/`, without importing test modules
from each other or weakening the repository check.

The new reference archive is `episodes/proxy_reference_cases_v3.jsonl.gz`, built with
`builder_version=loo-proxy-3`; it contains 65 cases. Snapshot:
`3e526884881770128df9580bda572a8240fc394eb8c9b795cea030e5e6db08a9`.
Older archives, frozen protocol and external results are not rewritten. New default output
directories prevent overwriting the earlier diagnostic. This work does not stage or commit the
many unrelated existing workspace changes.

Preservation checks verified the frozen protocol SHA-256
`3758bf2e40a5f67d962fb645b673c875d178b12011cd6dccbbe164e3e7730231` and the prior development
summary hash recorded in the new split manifest. The latest code reran the development experiment
with identical fitted alpha and reported metrics. Checks are in `calibration_v3/preservation_checks.json`.

## Next data acquisition and validation

Use the existing `research/dataset_discovery/DATASET_SEARCH_REPORT.md` and acquisition plan rather
than start another catalogue. Prioritize the missing contracts:

1. **Attempt denominator:** instance/plate manifests with executed, failed, missing and valid
   outcomes. LINCS instance metadata is a candidate; verify that missing or excluded attempts are
   represented before calling it a complete denominator. Cell-level QC alone is insufficient.
2. **State gain:** independently observed pre-action state or explicitly population-level baseline,
   matched controls and later outcomes. Sci-Plex-type dose experiments can supply measured menus;
   destructive samples are not same-cell trajectories. Split by independent compounds/donors and
   batches as required by the intended generalisation claim, before fitting normalization or labels.
3. **Calibration and transfer:** disjoint training, calibration and untouched evaluation units;
   evaluate new cells/labs as separate domains. Define overlap relative to the whole dual-core
   system. The local discovery audit records Tahoe overlap with the State checkpoint; new-to-memory
   does not make Tahoe an untouched virtual-cell evaluation.
4. **Decision utility:** at least two feasible measured alternatives, explicit costs, valid/invalid
   outcomes and adjudication rules. Freeze action predictions before revealing their outcomes.
   For incompletely observed action menus, no simple replay can establish counterfactual benefit.
5. **Mechanism evidence:** keep curated annotations, derived transcriptomic proxies, engagement,
   proximal function and distal phenotypes in separate typed fields. Rescue strengthens a
   mechanism-specific inference under its assumptions; it is not a binding/occupancy measurement.

Run the state-free frequency baseline first, then add pre-action state with identical labels,
splits and support. Use grouped uncertainty estimates and prespecified abstention/cost rules.
Only after state information gain and domain calibration survive an untouched evaluation should
the action loop be considered for default activation. No extra network complexity is justified
by the current evidence.

## Literature informing the boundary decisions

- [Guo et al., On Calibration of Modern Neural Networks, ICML 2017](https://proceedings.mlr.press/v70/guo17a.html):
  temperature scaling is fitted on held-out validation data. This supports fitting/calibration
  separation; it does not establish that temperature scaling or Dirichlet counts are optimal here.
- [Ovadia et al., Can You Trust Your Model's Uncertainty? NeurIPS 2019](https://arxiv.org/abs/1906.02530):
  uncertainty quality changes under dataset shift; within-domain fitting is not transfer validation.
- [Tibshirani et al., Conformal Prediction Under Covariate Shift, 2019](https://arxiv.org/abs/1904.06019):
  transfer guarantees require explicit shift assumptions and appropriate weighting. This is not
  permission to transfer probabilities across arbitrary cells, assays or laboratories.

These sources motivate minimal, auditable contracts. They are not substitutes for new biological
measurements or external validation of this implementation.
