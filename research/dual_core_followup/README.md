# Literature-guided dual-core experiments (2026-10-01)

This follow-up tests specific bottlenecks in the already connected [registered dual-core workflow](../dual_core_completion/README.md). It uses frozen, previously exposed data and existing predictors. It does not train a model, search combinations or promote a research result into the production selector.

Three agents independently implemented the policy replay, case-memory denominator audit and decision-value diagnostic. The main agent reviewed their contracts, integrated primary literature and checked the delivered evidence. [Literature synthesis](LITERATURE.md), [data review](DATA_LITERATURE.md) and [decision-contract interpretation](DECISION_CONTRACT.md) describe the limits of each comparison.

## Experiments and decisions

| Experiment | Fixed comparison | Result boundary |
|---|---|---|
| Anchored policy | Same ReferenceWorld, task rules and folds; one existing baseline-anchor option; permutation control | Completed 19,704 paths; no established terminal improvement over fixed |
| Case-memory denominator | Same 112 historical queries and selector; only outcome mode changes | Valid-readout prediction is available; complete attempted-experiment prediction is unsupported |
| Decision-value scope | Same 44,520 frozen reference forecasts; Bayesian versus registered one-step value | Information can change a Bayes action without authorizing terminal evidence |

### Case-memory denominator

The frozen population has 26 test units, 28 unit-cell readings and 112 contrast queries. The reference store has 65 disjoint units and 976 annotation-derived labels, all marked `valid_only`; these are not 976 independently observed experimental attempts. Every valid-readout query returned a forecast. Every attempted-experiment query refused with `insufficient_outcome_support`.

The production selector rejected all 112 valid-readout forecasts with `experiment_validity_probability_required`. Neither arm selected an action or changed evidence. This identifies a data/target boundary: a conditional distribution is available for its stated target, but the current data cannot price an entire attempted experiment. No QC success probability, terminal benefit or uncertainty interval is manufactured from the missing denominator.

The first research runner used an incorrect plan field, failed and was corrected in the new script. Its failed preregistration remains separate from the successful run. Production behavior did not change. Source hashes, queries, support and actual selector receipts are in `denominator_run/`.

### Bayesian value and registered terminal evidence

The diagnostic deduplicates available reference forecasts with empty history from the Round 2 probe channel. It analyzes 15,336 SciPlex3 B and 29,184 L1000 LT queries. Bayesian net value is positive while the registered one-step planner stops in 753 and 11,403 queries respectively. These are descriptive counts in a finite forecast bank, not independent biological trials or observed policy gains.

L1000's structural no-elimination folds contain 9,696 queries. Of these, 5,066 have positive Bayesian net value, but all have zero registered attempted gross utility and a -0.02 measurement charge. The posterior can change while the evidence gate remains closed. The objectives also use different loss/reward scales; the general counts are not a direct subtraction of equivalent utilities. The bank's adapter mode does not certify a complete real-world attempted-experiment sampling frame.

`expected_terminal_decision_value` now documents this scope explicitly. Its implementation and production defaults are unchanged. The diagnostic supports an interface clarification, rather than a claim that the existing Bayes-risk calculation is a runtime defect.

### Controlled anchored replay

The policy experiment retains the frozen five folds per task, legal action menus, budget, QC, endpoint and maximum measurements. Its four arms are fixed/no forecast, baseline/reference, anchored/reference and anchored/permuted. The sole new intervention sets the existing planner's baseline to the next legal fixed action and `deviation_z=1.645`. This approximate standard-error heuristic is not a safety certificate. The completed recovery run has 19,704 paths, 9,852 exact historical fixed/baseline parity checks, ten frozen fold checks and zero fitting calls.

Raw episode counts and cost sums follow. Utility is the **sum of gross terminal reward**, excluding cost. Chemical-unit estimates below use a different denominator.

| Task / arm | Correct | Wrong | Undetermined | Deferred | Measurements | Days | Utility sum |
|---|---:|---:|---:|---:|---:|---:|---:|
| SciPlex3 B fixed | 792 | 51 | 435 | 0 | 1,921 | 11,526 | 690 |
| SciPlex3 B baseline/reference | 771 | 40 | 467 | 0 | 1,908 | 11,448 | 691 |
| SciPlex3 B anchored/reference | 792 | 50 | 436 | 0 | 1,923 | 11,538 | 692 |
| SciPlex3 B anchored/permuted | 783 | 50 | 445 | 0 | 1,921 | 11,526 | 683 |
| L1000 LT fixed | 211 | 15 | 3,422 | 0 | 7,209 | 40,518 | 181 |
| L1000 LT baseline/reference | 239 | 9 | 1,244 | 2,156 | 2,353 | 13,521.75 | 221 |
| L1000 LT anchored/reference | 211 | 13 | 2,212 | 1,212 | 4,783 | 26,864.25 | 185 |
| L1000 LT anchored/permuted | 151 | 14 | 2,121 | 1,362 | 4,492 | 24,908.25 | 123 |

The 1,278 SciPlex3 episodes share 105 skeleton units; the 3,648 L1000 episodes share 205 chemical components. Each estimate averages episodes within a unit, then weights units equally. Intervals use the predeclared 2,000 unit bootstrap draws, seed 20260930, separately by task.

| Candidate versus same-rule fixed | Unit-mean terminal utility difference | Chemical 95% interval | Mean source/result outer bounds |
|---|---:|---|---|
| SciPlex3 baseline/reference | -0.00537 | [-0.04358, 0.03859] | Point-identified in registered replay |
| SciPlex3 anchored/reference | 0.00156 | [-0.00394, 0.00766] | Point-identified in registered replay |
| SciPlex3 anchored/permuted | -0.00604 | [-0.01592, 0.00144] | Point-identified in registered replay |
| L1000 baseline/reference | 0.01370 | [-0.00957, 0.04077] | [-0.03934, 0.06675] |
| L1000 anchored/reference | 0.00159 | [-0.00240, 0.00665] | [-0.05146, 0.05463] |
| L1000 anchored/permuted | -0.01703 | [-0.03272, -0.00467] | [-0.07008, 0.03602] |

Both baseline/reference and anchored/reference comparisons include zero on each task. Sixty-seven L1000 episodes per arm have a potentially reachable source-unresolved condition; their cached point comparisons do not identify true source-resolved benefit. The reported outer bounds subtract marginal bounds and are deliberately conservative; they are not sharp coupled-policy bounds. Self-comparison bound columns in the machine table are merely this same marginal calculation and have no substantive treatment-effect interpretation.

**Decision: retain the anchor as a tested research option; do not change production selection defaults.** It moves SciPlex3 close to fixed while failing to establish higher utility. On L1000 it reduces baseline deferral and spends more than baseline, with no established gain over fixed. This is not a general decision improvement.

### Forecast content, selection and validator bottlenecks

| Task / reference policy | Sequence changed versus fixed, unit mean | Same terminal among changed-action episodes, unit mean |
|---|---:|---:|
| SciPlex3 baseline | 77.64% | 88.75% |
| SciPlex3 anchored | 1.35% | 36.67% |
| L1000 baseline | 96.27% | 32.65% |
| L1000 anchored | 43.42% | 44.41% |

The last column's conditional means average only units represented among changed-action episodes (15 for SciPlex3 anchored, 151 for L1000 anchored), not all task units. All ranking, first/later/sequence changes and uncertainty are retained in the task JSON and episode attribution table.

True versus permuted anchored forecasts change sequences in 3.93% of SciPlex3 and 16.08% of L1000 chemical-unit comparisons. Thus the content control does alter behavior. Their terminal contrasts are 0.00759 [-0.00189, 0.01824] and 0.01862 [0.00616, 0.03440], respectively. L1000's source-aware mean envelope is [-0.03443, 0.07167], so its positive cached-label contrast is not a source-resolved gain. The four arms do not identify a new full World x Policy factorial interaction; no missing cell is filled.

| Task / forecast-policy | All-menu CE | All-menu Brier | Selected CE | Selected Brier | Selected argmax accuracy |
|---|---:|---:|---:|---:|---:|
| SciPlex3 reference/baseline | 0.82183 | 0.44642 | 0.97553 | 0.51400 | 65.93% |
| SciPlex3 reference/anchored | 0.82183 | 0.44642 | 1.05947 | 0.55841 | 62.40% |
| SciPlex3 permuted/anchored | 1.07507 | 0.59624 | 1.34057 | 0.73498 | 46.76% |
| L1000 reference/baseline | 0.19977 | 0.08589 | 0.31720 | 0.15426 | 88.01% |
| L1000 reference/anchored | 0.19977 | 0.08589 | 0.40076 | 0.16701 | 90.65% |
| L1000 permuted/anchored | 0.24524 | 0.09952 | 0.40096 | 0.16086 | 92.08% |

Conditional reading fit and selected-action metrics do not determine the same ranking of policies. On SciPlex3 the reference's better fit than permutation mostly encounters the conservative forecast-to-selection boundary; baseline often changes actions without changing the terminal result, consistent with a menu/validator bottleneck. The frozen L1000 no-elimination folds exhibit a structural evidence bottleneck. These observations localize loss of influence; they do not prove that relaxing the validator would improve biological decisions.

### Coverage, risk and cost

L1000 anchored/reference has the same raw correct count as fixed and fewer measurements, with 1,212 deferred episodes. In the common-decided subset it adds no correctness or risk advantage:

| Same episodes decided by anchor/reference and fixed | Episodes / chemical units | Correct unit mean, both | Wrong unit mean, both | Measurements, candidate / fixed | Days, candidate / fixed |
|---|---|---:|---:|---|---|
| SciPlex3 | 837 / 83 | 86.50% | 13.50% | 1.30150 / 1.29936 | 7.80897 / 7.79618 |
| L1000 | 220 / 18 | 75.96% | 24.04% | 1.57937 / 1.58333 | 8.73264 / 8.75000 |

These are outcome-selected, descriptive equal-coverage subsets, not an implementable threshold or calibrated selective-risk guarantee. Their intervals and the common-acted comparisons are in `task_summary.json`. Whole-population L1000 cost savings should therefore be described together with deferral and coverage, rather than as general correctness improvement. These comparisons change selection as well as abstention: baseline/reference's raw correct count differs from fixed. They do not isolate abstention's causal effect, and a blanket cost-only description would conceal the correctness changes.

Rankings come from actual planner evaluations, including continuation value. Fixed has no forecast ranking, so a ranking difference against fixed is a process difference rather than evidence of model content. Later rankings follow each arm's purchased history; they are observed-path comparisons, not forecasts evaluated at identical subsequent contexts. First-step comparisons and the explicitly declared permutation contrast must be interpreted separately.

Reading scores use the true proxy-hypothesis branch after execution. They average scored readings within an episode, then episodes within a chemical unit. They are conditional registered-label CE/Brier/argmax accuracy, rather than expression reconstruction, a pooled action-weighted loss or external probability calibration. Source-unresolved labels remain descriptive cached-label scores. Structural no-elimination folds are excluded from quality claims because their reference parameters were placeholders.

## Data, dependence and exposure

SciPlex3 B and L1000 LT remain exposed development replays. LINCS2020 proxy data is a separate population with a separate hypothesis-conditional target. ReferenceWorld benefits cannot be assigned to production STATE, research WorldV2 or case-memory. No hidden-result oracle is a candidate policy.

Chemical skeleton/component analysis is separate from physical plate/batch analysis. Both replay tasks have one connected physical component, so an independent physical confidence interval is not estimable. The conservative follow-up source envelope includes unresolved well **or plate** links, including the fifth L1000 record whose duplicate well is explained but whose plate link remains unresolved. Missing reachable outcomes receive declared bounds; a model does not complete them to claim point identification.

The registered replay's reported terminal utility uses +1 correct, -2 wrong and 0 unresolved/deferred; it excludes cost. Measurements and assay days are reported separately. The planner subtracts a 0.02 price **per measurement** when selecting actions; assay days separately constrain the budget. The diagnostic explicitly reports its corresponding gross and net values. These estimands are not silently combined.

Review found a historical labeling discrepancy: Round 2's predeclaration calls the planner price per assay day, and its separate probe-ranking diagnostic subtracts price times days, whereas the actual planner subtracts price once per measurement. The follow-up preserves the actual policy, terminal scoring and costs for parity, uses named policy evaluations for action rankings, and records the distinction without rewriting the frozen receipt. Final outcomes remain determined by observed readings and the registered validator.

## Reproduce

Use the existing maestro environment from `D:\MAESTRO`, with the registered local assets. Each output directory must be fresh:

```powershell
& 'D:\anaconda\envs\maestro\python.exe' -m research.dual_core_followup.denominator --out outputs/dual_core_followup_rerun/denominator_run
& 'D:\anaconda\envs\maestro\python.exe' -m research.dual_core_followup.decision_contract --output outputs/dual_core_followup_rerun/decision_contract
```

The completed policy run used this fresh recovery directory after an execution interruption:

```powershell
& 'D:\anaconda\envs\maestro\python.exe' -m research.dual_core_followup.anchored freeze --out outputs/dual_core_followup_20261001/anchored_recovery_root_01
& 'D:\anaconda\envs\maestro\python.exe' -m research.dual_core_followup.anchored probe --out outputs/dual_core_followup_20261001/anchored_recovery_root_01
& 'D:\anaconda\envs\maestro\python.exe' -m research.dual_core_followup.anchored full --out outputs/dual_core_followup_20261001/anchored_recovery_root_01
& 'D:\anaconda\envs\maestro\python.exe' -m research.dual_core_followup.tables --run outputs/dual_core_followup_20261001/anchored_recovery_root_01/full --out outputs/dual_core_followup_20261001/tables
```

Use new output leaves for reproduction. [tables.py](tables.py) produces inspectable raw sums and existing unit estimates without new fitting or inference. The denominator script verifies 13 hardcoded historical hashes before calling the targets and selector. The diagnostic verifies forecast input/output hashes and frozen legal menus. Each script records local input hashes, actual code hashes, environment, command and exposure; a baseline commit alone is not claimed to include the working-tree script.

Full regression: 1,543 passes, one inherited historical Markdown-language failure, no errors/skips and two fitting checks deselected. All 17 new contracts pass. Historical preservation checks retain 333 frozen files and 39 data-review source hashes. Independent [path verification](validate_paths.py) checks every full episode/metric row, 9,852 historical comparisons, 39,408 attribution rows, frozen inputs/sources and arm unit means. All probe bank contents are checked; full banks receive byte-hash verification, not a claimed full semantic census. Initial incomplete policy/regression outputs and interruption receipts remain separate and unused for effect estimation.

The final focused publication check has 67 passes and one explicit exclusion for the inherited prose rule. All 59 copied/compressed publication records match their staged Git bytes; six larger or incomplete banks remain local with hashes. Eight linked Markdown documents have no broken local links. [Publication checks](results/20261001/publication_checks/manifest.json) preserve the command, code hashes, test output and independent copy/link receipt. Counts overlap with the full suite.

Small durable artifacts are published under [results/20261001/](results/20261001/manifest.json). [snapshot.py](snapshot.py) copies bytes into a fresh destination and checks their hashes; larger text tables are losslessly gzipped. Compressed banks larger than 45 MiB and interrupted-stage banks remain local with their complete file hashes. The publication manifest distinguishes copied, compressed and local-only files. A clone without the registered local assets cannot reproduce these runs; missing inputs must fail rather than silently produce synthetic replacement evidence.

## Completed and blocked analyses

Completed: primary literature review, real-data denominator comparison, frozen-query value-scope diagnostic, four-arm controlled policy replay, independent path verification and regression. Unsupported: unconditional case-memory experiment probabilities without all-attempt records; independent physical intervals; new WorldV2 swaps without saved fitted transitions; true-state gain without pre-decision measurement/availability times and sample relationships; new-compound/dose/time support inferred from STATE interface tests.

The engineering core is connected within registered contracts. Biological decision superiority, external probability calibration and prospective generalization require additional evidence. This follow-up retains refusals and negative findings as results.
