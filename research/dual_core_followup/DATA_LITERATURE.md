# Data qualification, literature, and the frozen denominator experiment

Reviewed on 2026-10-01 in `D:/MAESTRO`, starting from Git revision `5d982070fe88e04a2fb1ee5212a8eed39e8df405`. This is an exposed-data, no-training research audit. Condition response prediction (STATE), reading prediction (WorldV2), case-memory outcome frequencies, and hidden-result diagnostic oracles have different targets and evidence boundaries.

## Verified primary sources and transferable checks

These five entries were checked against original papers or official benchmark pages. The proposed repository checks are methodological adaptations, not replications of the publications. No benchmark software, external dataset, or model was downloaded or installed.

| Primary source | Verified point and minimal repository adaptation | Limits and access |
| --- | --- | --- |
| [PerturBench, arXiv v4](https://arxiv.org/html/2408.10609v4), 2025 | Rank metrics expose collapsed predictions that can score well on global fit metrics. Separate covariate transfer from combination prediction. Inspect constant and context-permuted forecasts alongside reading quality and action ranking. | Full HTML read. Its transcriptomic distances are different from discrete reading probabilities; do not reuse its model search or test-fitted PCA in this audit. |
| [Systema](https://www.nature.com/articles/s41587-025-02777-8), DOI `10.1038/s41587-025-02777-8` | Shared shifts from controls can inflate evaluation. Perturbation-specific centroids and centroid discrimination assess specificity. Compare existing expression predictions with a frozen mean baseline before claiming biological content. | Publisher-indexed original text verified; direct article fetch returned an internal error in this session. Genetic perturbation results do not establish chemical MoA or terminal decision benefit here. |
| [Ahlmann-Eltze, Huber, and Anders](https://www.nature.com/articles/s41592-025-02772-6), Nature Methods, 2025 | Simple no-change, additive, mean, and linear comparators matter; more complex models did not consistently surpass the paper's baselines. Keep strong frozen comparators and inspect feature selection based on outcome knowledge. | Original publisher-indexed methods and results verified; direct publisher fetch was unreliable. These cancer-cell genetic tasks have different targets and splits from the local chemical reading benchmark. No new baseline is fitted here. |
| [State original paper](https://www.sciencedirect.com/science/article/pii/S0092867426009219), DOI `10.1016/j.cell.2026.07.052`, 2026, with [official Cell-eval](https://github.com/ArcInstitute/cell-eval) | State addresses response prediction across cellular contexts. Cell-eval requires predicted and real AnnData and explicit controls; its documented ceiling uses disjoint cell halves to avoid shared-cell artifacts. Preserve feature identity and measurement targets; keep biological replicate dependence separate from cell self-splits. | State publisher summary verified; direct full-paper access was blocked. Official Cell-eval README read. The local checkpoint/registered context is independently constrained; current publication claims cannot expand the adapter's registered queries. No Cell-eval run is claimed. |
| [Official Virtual Cell Challenge 2026](https://arcinstitute.org/news/virtual-cell-challenge-2026) | The declared task supplies unperturbed basal profiles and intervention IDs while withholding measured responses in unseen perturbed contexts. This gives a concrete information boundary for a future decision-time state contract. | Full official page read on the review date. CRISPRi and 10x Flex differ from local chemical perturbations and L1000. Existing outcome-only signatures cannot stand in for pre-action basal measurements. No challenge entry or external OOD result is claimed. |

## Current local data and backend eligibility

The reviewed readiness inventory is [data_readiness.json](D:/MAESTRO/research/dual_core_completion/data_readiness.json), SHA-256 `5e05780ea2babd6d3d4b1d5252a5f8bc06b2905c3f1ded3ecfc8ce2721755a0e`. It is a prior review snapshot, with its own source hashes and Git revision, rather than a claim that every code hash always equals current production. The current [virtual-cell registry](D:/MAESTRO/data/virtual_cell/registry.json) was also read, SHA-256 `7c27e4e80ac3259ce1fbacc84c4332c255b249b9f2a56a8fa1b3a69306a49dde`.

| Data/backend | Target, units, and source boundary | Currently feasible without training |
| --- | --- | --- |
| SciPlex3 B | Real chemical response signatures and derived contrast readings. Skeleton groups provide the chemical dependence level; plates and shared controls provide a different physical dependence structure. A recorded low-cell QC failure is an observed attempted action, not a missing counterfactual. | Frozen menu replay and matched reading/action diagnostics within registered conditions. Preserve the Round 2 source and QC coverage qualification. STATE's registered Tahoe context does not supply SciPlex3 forecasts. |
| L1000 LT | Historical expression signatures and derived MoA contrast readings. Chemical connected components differ from physical plate components. Unresolved cache-to-source joins prevent point identification of affected comparisons. | Same-menu frozen replay with declared utility bounds for source-affected results. Keep the four unresolved well differences and the additional unresolved plate difference visible. Resolve source keys before any broader claim. |
| `model_experiment_v1` | Public query episodes plus separately held replay outcomes; multiple contrasts/actions share source units. Existing folds have an exposure history and are not a newly untouched evaluation population. | Real frozen readings can test selector/validator contracts and paired paths. Truth belongs in the replay evaluator, not in predictor input. A full-menu result dictionary does not resolve upstream source discrepancies or establish pre-action state availability. |
| LINCS2020 case memory | Level 5 signatures grouped by chemical block, curated mechanism classes, and derived validator labels. The v3 reference bank stores successful-readout records only. | The completed experiment below calls the saved reference bank through the production outcome forecaster. It can serve conditional valid-reading distributions, but supplies no complete attempted-experiment denominator. This bank is distinct from L1000 LT and cannot inherit its results. |
| Production STATE | The registry binds Tahoe `c39`, NCI-H596, `X_hvg`, and one existing checkpoint. Its checkpoint digest is recorded by the registry, not newly rehashed or re-inferred in this experiment. The registry notes probable checkpoint exposure to the context and exposed evaluator holdouts. | Registered-condition interface sensitivity checks only. This audit does not establish an unmeasured chemical, time, dose, or new-context capability. No SciPlex3/LT STATE arm is registered here. |
| Research WorldV2 | Reading predictions from an in-context world. Existing selected-step outputs can be compared with their recorded labels; the inspected implementation fits transition pairs at runtime and lacks a verified saved all-menu transition bank. | A fresh-output diagnostic can call `run(out)` in [round2_cached_world.py](D:/MAESTRO/research/identifiability_audit/round2_cached_world.py). That module's reviewed SHA is `6e35194d0f2da7b7d14fded1e9ee8e3fae5336cec8403305d6d4833cd4466486`. Cached selected steps cannot identify a new all-menu policy swap. This diagnostic was not rerun here. |

The [frozen Round 2 report](D:/MAESTRO/outputs/identifiability_round2_20260930/ROUND2_REPORT.md), SHA-256 `7298108bbec47ddddf090b27c89047871a2c9478ee4f4751c278d01f60537816`, remains the source for its menu, linkage, and physical dependence qualification. The present experiment adds no physical independence. No decision-time state arm was run: measurement time, availability time, and sample relations have not been established for the required state inputs.

## Executed minimal intervention

The predeclared population consists of all unique `(unit, cell, own, decoy)` keys in the historical `scalar` arm of `outputs/case_memory_integration/forecast_items.jsonl`. Other historical arms are read only to check that their recorded labels agree; their forecasts and oracle distributions never enter a predictor or selector. The actual frozen expression matrix is `data/processed/case_memory_integration/pack_arrays.npz`; no `test_matrix_v3` file was found or reconstructed.

The three test denominators are **26 chemical blocks, 28 block-cell readings, and 112 contrast queries**. The frozen reference has **65 independent blocks and 976 derived labels**, all `derived_annotation_proxy` and `sampling_frame=valid_only`. Its statuses are 805 qualified, 111 ambiguous, and 60 undetected. These label counts reuse measurements across contrasts and are not independent experimental attempts. Undetected means a completed valid reading with insufficient signal, and does not define a QC failure.

Both arms use `CaseMemoryOutcomeForecaster`, `FeatureArm.SCALAR`, `research_mode=True`, `calibration=None`, the same hypotheses, action, public context, and initially open evidence. Only `outcome_mode` changes. The action keeps the frozen case schema's cost of 8 wells, runs at its recorded cell context, 24 hours and 10 uM, and is affordable under budget 8. Production `select_discriminating_action` is actually called on each arm's forecast and the same one-action menu. This tests target admission; it does not compare a multi-action acquisition policy.

The historical calibration split, fitted profile, calibration items, thresholds and pack manifest are frozen as metadata. The historical profile belongs to a different reference split/snapshot and is not loaded as current calibration. No centroids, thresholds, labels, calibration profiles, or model weights are reconstructed or fitted. Test vectors and outcome codes are evaluator-only receipts and never enter UserStateContext, forecasting, or selection.

| Target | Queried | Available | Available test units | Production selector reason | Selected actions |
| --- | ---: | ---: | ---: | --- | ---: |
| `valid_readout` | 112 | 112 | 26 | `forecast_refused:experiment_validity_probability_required` for all 112 | 0 |
| `attempted_experiment` | 112 | 0 | 0 | `forecast_refused:insufficient_outcome_support` for all 112 | 0 |

All 112 attempted-experiment requests refuse with `insufficient_outcome_support`. Each available valid-readout branch uses 10-17 independent reference units (Kish effective support is also 10-17); these are reference units, not query units or posterior concentration. Every reading descriptor and outcome label is preserved. All before/after evidence hashes agree, with no observations or evidence updates appended. QC success probability, terminal benefit, and benefit confidence intervals are deliberately null. The observed result identifies a missing denominator, and confirms that production selection prevents conditional forecasts from being used as complete experiment forecasts.

All data and labels in this audit were previously inspected in September 2026. The chemical reference/test block sets are disjoint, but that boundary does not erase prior evaluation exposure or establish independent physical plates. No confirmatory, biological causal, generalisation, or scientific-benefit claim follows from these software contract results.

## Reproduction and preserved outputs

Run from `D:/MAESTRO`, using a **new** output directory; existing directories are refused:

```powershell
D:/anaconda/envs/maestro/python.exe -m research.dual_core_followup.denominator --out outputs/dual_core_followup_20261001/denominator_run_replay
D:/anaconda/envs/maestro/python.exe -m pytest tests/test_real_case_memory_denominator.py -q
```

The actual successful run used `--out outputs/dual_core_followup_20261001/denominator_run`. [predeclared.json](D:/MAESTRO/outputs/dual_core_followup_20261001/denominator_run/predeclared.json) was persisted before either target or selector was called. It records the exact command argv, interpreter and package versions, Git revision, code hashes, all 13 frozen input hashes, the population, exclusion claims, and stop conditions. [query_paths.jsonl](D:/MAESTRO/outputs/dual_core_followup_20261001/denominator_run/query_paths.jsonl) records each query's input/output, vector, selector, and evidence hashes. [ledger.json](D:/MAESTRO/outputs/dual_core_followup_20261001/denominator_run/ledger.json) pins the output and source/code hashes.

| Successful-run artifact | SHA-256 |
| --- | --- |
| `predeclared.json` | `bc1f2d0989e2c5bf02bb4cd43e6eedef3c8112e0db65bbc66b5861b177d7ce6f` |
| `query_paths.jsonl` | `695a733d7ed60ae69f7abda9f196bf12cf7fe565ed908edffe9bfdae341a84e2` |
| `summary.json` | `0e9dd8561fac2fb55a18b88f39ec74ab1cae9d373a2502589f900199aec43cff` |
| `ledger.json` | `13187dd18d901179302d43e0db2836e8db9c37c75eb82b339831dfafb2242964` |
| `research/dual_core_followup/denominator.py` | `be0c76647193de311bee5743c6a0493265df58257a49490ac56b14a8bdf47fd4` |

All frozen input and runtime code hashes match before and after the successful run. The five tests in [test_real_case_memory_denominator.py](D:/MAESTRO/tests/test_real_case_memory_denominator.py) passed. They check actual calls of both targets and the production selector, population separation, refusal without an attempted-experiment denominator, evidence preservation, rejection of changed frozen inputs, and refusal to overwrite output.

One earlier research-output attempt stopped because the new reporter used `BudgetedEvidencePlan.selected`; the existing production API names the field `actions`. The one-line behavioral correction changes `plan.plan.selected` to `plan.plan.actions` in the new reporter, without a production change. Its original predeclaration is preserved in `outputs/dual_core_followup_20261001/denominator_run_failed_01`, SHA-256 `dd8a3adc6488b0f0ba00cef8ca6650fb946d587e3b77452a0cf84ba973eef393`. The [error receipt](D:/MAESTRO/outputs/dual_core_followup_20261001/denominator_run_failed_01/error_receipt.json), SHA-256 `b7f8c066e21d5947c4aeb4421d3ac06ba5eda51e366ac2a233a6816d7ff3b497`, records the captured failure and correction. The predecessor source was not retained during its first execution; it was later reconstructed only inside the failed directory and labeled as a reconstruction. Its SHA-256 `03f67e1d9236c0cd2532619f4fb0920b19f9cd8435c1cab268243604856f10e9` exactly matches that failed predeclaration's code hash. No successful frozen result was overwritten.

## Remaining scope

Completed: primary-source literature review, local target/source qualification, frozen real-data denominator intervention, production selector admission check, and five contract tests.

Not run: new training or calibration, external benchmark installation/evaluation, STATE decision benefit on SciPlex3/LT, a newly fitted WorldV2 swap, a new reading-quality comparison, or a decision-time state gain arm.

Not identifiable from these files: all-attempt QC rate, the effect of unobserved/missing reachable outcomes, a new all-menu WorldV2 policy benefit, independent physical uncertainty in the connected control/plate structure, or untouched OOD generalisation.

The next useful work is to resolve source joins and acquire a verified complete attempt ledger with planned, failed, valid and missing statuses plus timestamps and sample relations. Such a ledger must retain failed and incomplete attempts and keep its target separate from the successful-readout bank. Until that data exists, leave attempted-experiment forecasts refused. Frozen reading/action path diagnostics can continue within their existing coverage bounds.
