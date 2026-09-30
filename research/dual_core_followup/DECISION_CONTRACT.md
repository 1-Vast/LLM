# Decision-value scope diagnostic — 2026-10-01

The existing `expected_terminal_decision_value` is a Bayes-loss calculation. It can assign value to an informative reading that removes no hypothesis, because a Bayes action can change among several surviving hypotheses. The registered replay permits a terminal decision only after its real reading triggers a registered elimination. These are different objectives and decision permissions. This diagnostic documents that distinction; it does not establish a production defect or change a policy to improve research scores.

## Contract evidence and the smallest change

`src/maestro/acquisition.py::_posterior_decision` explicitly chooses among defer and surviving hypotheses by posterior loss. Its default wrong loss is 2 and defer loss is 1. `expected_terminal_decision_value` averages that posterior loss and returns the reduction from the prior loss. Its existing zero-value test uses identical branch distributions for two non-eliminating labels; it does not assert that informative, non-eliminating labels have zero Bayes value.

`research/belief_planning/planner.py::plan_measurement` explicitly follows the registered runner: the first elimination terminates, correct is +1, wrong is −2, and stop is 0. Non-eliminating labels can update the planning belief and enable a future measurement; at the diagnostic horizon of one they cannot create a terminal outcome. Forecasts do not update `EvidenceState`. The default production orchestrator does not call the Bayes EDV API; opt-in `case_update.rank_actions_by_decision_value` does. Its output therefore needs the Bayes interpretation, rather than interpretation as evidence permission or registered replay utility.

The only production-file change adds five docstring lines to `expected_terminal_decision_value`. It explicitly names the Bayes objective and its boundary with evidence and the validator. No function behavior, endpoint, QC rule, forecast, selection default, or frozen result changed.

The synthetic contract examples are:

| Identical forecast, uniform prior | Bayes value before cost | Registered one-step attempt gross utility | Registered best choice |
|---|---:|---:|---|
| Two informative non-eliminating labels with likelihoods .9/.1 and .1/.9 | .8 | 0 | Stop |
| Two eliminating labels correct with probability .8 and wrong with .2 | .6 | .4 | Assay |

In the second row, the Bayes loss reduction is `1 − 2 × .2 = .6`, while registered reward is `.8 − 2 × .2 = .4`. Comparing these as if they were the same utility would also be incorrect even when the reading eliminates a hypothesis. The new tests preserve both semantics.

## Frozen real-query diagnostic

The diagnostic streamed the existing Round 2 banks under `outputs/identifiability_round2_20260930/interventions/`. It retained only `forecast=reference`, `channel=probe`, `available=true`, no refusal, and empty history. It recomputed every retained query and content hash and deduplicated by `input_sha256`, rejecting inconsistent repeated outputs. It loaded one JSONL row at a time, not the million-call bank into memory. The deduplication state stores hashes. No model constructor, fitting call, or policy replay was executed.

Each admitted query was checked against its frozen compound availability, action-day cost, budget, and nonzero maximum measurements. Episode chemical unit identifiers were read from the frozen path-attribution CSV. Fold `validator.eliminates` gates its existing registered rules: SciPlex3 B folds 0–4 allow elimination; L1000 LT folds 0 and 3 allow none. On those two folds the consequences map is empty. The forecast itself, including small probability mass on structurally unavailable match labels, is retained without alteration or renormalization beyond the existing calculation APIs. Such probability mass grants no terminal permission.

Both calculations receive the same forecast and uniform prior, with a one-step horizon. The registered one-step planner uses its existing `.02` price **per measurement**, separately from assay-day cost and the frozen endpoint utility. This diagnostic does not evaluate a two-measurement policy, compute a new termination rule, or claim its selected action is an implemented strategy.

| Task | Unique action queries | Episodes | Chemical units | Bayes net positive, registered one-step stops |
|---|---:|---:|---:|---:|
| SciPlex3 B | 15,336 | 1,278 | 105 skeleton units | 753 |
| L1000 LT | 29,184 | 3,648 | 205 component units | 11,403 |

These counts are a finite census of frozen forecast queries, not independent biological replicates or observed decision outcomes. The last column can reflect both decision permissions and objective scales, so it must not be interpreted as an error count or pure non-elimination effect. Chemical unit identifiers remain in the query table. No biological, policy-benefit, or causal confidence interval is claimed. Physical plate/batch inference is not estimated; the earlier source-link and shared-plate limits remain applicable.

The cleanest real permission distinction occurs on the two structurally non-eliminating L1000 folds:

| L1000 LT fold | Unique queries | Bayes value > .02 | Registered attempt gross utility | Registered attempt net utility |
|---|---:|---:|---:|---:|
| 0 | 4,608 | 2,334 | 0 for every query | −.02 for every query |
| 3 | 5,088 | 2,732 | 0 for every query | −.02 for every query |

Thus, 5,066 of these 9,696 existing real forecast queries have positive Bayes value after the existing measurement price, while the registered one-step terminal value stays zero before price. This is a forecast/rule semantics result. It supplies no measured evidence about biological correctness or real QC calibration.

The first qualifying bank example, without selecting a best-performing example, is L1000 LT fold 0, compound `BRD-A01643550`, contrast `EGFR inhibitor` versus `glucocorticoid receptor agonist`, action `A549|006h|10000nM`. Its Bayes value is `0.07261994085961254`, Bayes net value `0.05261994085961254`, registered attempt gross utility `0`, net utility `−.02`, and registered best choice is stop. Its input hash is `b60416cdb5f47a787a5f4e15b1925a7beb074131941845d09fc1100b573b18c2`; content hash is `9c5f4c12512ebea59d641482e62c9399f6108acdd56ccc14a5f02b4e7c46773b`.

The table also reports a diagnostic component, `noneliminating_bayes_gain`: under the stated two-hypothesis prior and losses, each non-eliminating label contributes `|P(label|h1) − P(label|h2)| / 2` to the Bayes risk reduction. This decomposition uses the original forecast, not a forecast conditioned on a selected label subset. It does not measure an observed utility gain.

## Actual bank schema and artifacts

The Round 2 JSONL schema contains `task`, `episode` (`fold|compound|h1|h2`), `policy`, `task_input`, `forecast`, `compound`, `h1`, `h2`, `action`, `history`, `channel`, `input_sha256`, `output_sha256`, `available`, `refusal`, `content`, and `calls`. `content` contains `branches[{hypothesis, probabilities, support}]`, `refusal`, `version`, `basis`, and `action`. Its five probability labels are `profile_matches_h1`, `profile_matches_h2`, `profile_unresolved`, `no_detectable_response`, and `quality_failed`. The retained backend is reference, version `belief-planning-1`, not production STATE, WorldV2, or a new case-memory backend.

The earlier `maestro_vc_v1/replay/forecasts/*` bank has a different schema: `compound`, `dataset`, `fold`, `h1`, `h2`, `key`, `nn_class`, `nn_similarity`, `prior_h1`, `tier`, `truth`, `unit`, `worlds`, and `y`. Each world has ordered `h1`/`h2` vectors and `support`. Its truth and actual reading are evaluator fields. This diagnostic does not consume that bank, and those fields must not enter policy inputs.

Completed artifacts are under `outputs/dual_core_followup_20261001/decision_contract/`:

- `sciplex3_B_queries.csv` and `l1000_LT_queries.csv`: one row per retained query, episode and chemical unit, original input/content hashes, forecast version, frozen permission/day cost, and named values from both objectives.
- `summary.json`: per-fold counts and sums, retaining structural no-elimination folds explicitly.
- `manifest.json`: exact command, execution environment, baseline commit, actual working-tree source hashes before/after the run, six input hashes, three output hashes, selection rules, and scope.

Input bank SHA-256 values are `b8f813789cc42abc87855a7368bebb7c7a4b02beed2284bba124018de7b5fbae` (SciPlex3 B) and `779fc9ae2b76b97d5557a0a9a5c8072535a080b9bba855e80878f74fbc9a3a04` (L1000 LT). All six diagnostic input hashes were also matched against the expected entries in the committed baseline artifact ledger, read directly with `git show 5d98207:research/identifiability_audit/results/20260930/artifact_ledger.json`. The summary SHA-256 is `c910c3af5efd4ffbc8b253201359aaa4c772171f3343b240519c7e295bf16043`. Full ledgers are in the manifest rather than a selectively truncated source list.

The run used baseline commit `5d982070fe88e04a2fb1ee5212a8eed39e8df405` plus the separately hashed working-tree diagnostic and docstring. Python was Anaconda 3.11.16, NumPy 2.4.6, SciPy 1.17.1, pandas 2.3.3, pytest 9.1.1, on Windows. All underlying data, calibration, forecasts, and development folds had existing exposure. No untouched evaluation set, new checkpoint, fitting, test-fold policy selection, or oracle policy is claimed. The bank has no `outcome_mode`; the explicit `attempted_experiment` constructor argument is only an adapter to an API that requires that mode. It does not retrospectively establish the bank's sampling frame or real-world attempted-experiment calibration.

Executed commands from `D:\MAESTRO`:

```powershell
& 'D:/anaconda/envs/maestro/python.exe' research/dual_core_followup/decision_contract.py
& 'D:/anaconda/envs/maestro/python.exe' -m pytest -q tests/test_decision_value_scope.py tests/test_decision_sensitive_acquisition.py tests/test_forecast_planner_uncertainty.py tests/test_belief_planning.py
```

All 36 tests passed, comprising five new scope/hash/filter contracts and 31 existing tests. Output hashes were independently rechecked, and CSV row, episode, unit, and stop counts were independently recomputed. To repeat without overwriting these outputs, supply a new leaf directory with `--output`; the script refuses an existing directory.

## Original papers and supported scope

All three sources were accessed as full primary PDFs on 2026-10-01; no review, secondary summary, or search snippet is the evidentiary basis below.

- Roy and McCallum, ICML 2001, *Toward Optimal Active Learning through Sampling Estimation of Error Reduction*. The author's PDF title uses “Monte Carlo Estimation.” Sections 1–2 support selecting information by the downstream loss, rather than assuming uncertainty or version-space reduction optimizes the evaluation target. Its algorithm retrains a classifier for candidate labels; it is not implemented here and does not justify violating the no-training restriction or granting validator evidence from a forecast. [Author-lab PDF, 8 pages](https://groups.csail.mit.edu/rrg/papers/icml01.pdf).
- Golovin, Krause and Ray, NeurIPS 2010, *Near-Optimal Bayesian Active Learning with Noisy Observations*. Sections 3–4 support distinguishing decision-equivalence classes under a specified loss, including noisy observations and nonuniform test costs. The paper also gives failure cases for greedy information gain and myopic decision-theoretic value, so it supplies no generic optimality guarantee for MAESTRO's one-step EDV or anchor threshold. Its theory does not establish biological calibration or a safety guarantee for our planner. [Conference PDF, 9 pages](https://proceedings.neurips.cc/paper_files/paper/2010/file/1e6e0a04d20f50967c64dac2d639a577-Paper.pdf).
- Grimm, Barreto, Singh and Silver, NeurIPS 2020, *The Value Equivalence Principle for Model-Based Reinforcement Learning*. Definition 1 distinguishes models by their Bellman effects on specified policies and value functions. This supports separately checking forecast fidelity, action changes, and registered terminal value; it does not show these MAESTRO backends are value-equivalent or confer biological mechanism fidelity or policy improvement. The value-equivalence diagnostic connection is our interpretation, not a theorem proved for this replay. [Conference PDF, 12 pages](https://proceedings.neurips.cc/paper_files/paper/2020/file/3bb585ea00014b0e3ebe4c6dd165a358-Paper.pdf).

## Next decision experiment and remaining limits

The parent-led minimum intervention is the already available reference-forecast planner with baseline anchoring. It can compare its proposed action against the next legal fixed action using the existing threshold, while preserving the forecast, menu, budget, QC, endpoint, and evidence path. That is a policy comparison and needs actual paired terminal outcomes, coverage-matched risk/correctness/cost, and the previously declared chemical dependency intervals. The anchor's immediate forecast-standard-error heuristic has no certified safety guarantee. This scope diagnostic does not add another policy to that comparison or change EDV to manufacture a score improvement.

Run: five synthetic scope/hash/filter contracts and the real frozen reference-query/rule census. Not run here: new models, any policy grid, terminal-benefit replay, oracle strategies, production STATE sensitivity, WorldV2 inference or replacement, real pre-decision-state gain, and physical plate/batch inference. Not identified here: real biology from forecast posteriors, the causal value of information, prospective generalization, real QC calibration, and utility of unobserved policy-reachable results. These would require evidence or a separately valid protocol beyond this diagnostic.
