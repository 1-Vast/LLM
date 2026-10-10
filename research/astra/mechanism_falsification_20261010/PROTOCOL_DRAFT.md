# Block M protocol (draft; becomes PROTOCOL.md with thresholds before the freeze)

## Units and tiers

* Unit: a drug (Repurposing Hub name) in `SPLIT.json`. Query drugs are scored; reference drugs fit.
* Open tier: reference (726) and development (358) drugs. Sealed tier: confirmation (502) drugs,
  in a separate file that `study.load_tier("sealed")` refuses until `FREEZE.json` exists.
* Hypothesis space H: all 424 classes of the universe. A class with reference drugs is represented
  by the data (or hybrid) compiler; a class without reference drugs only by the agent's hypothesis.
* Strata fixed before scoring: `referenced` (query class has reference drugs) and
  `knowledge_only` (it does not; 106 development, 106 confirmation drugs).

## Episode

Menu: the query's available options among 9 lines x {6 h, 24 h}. Budget B in {1, 2, 3, 4}; one
option per step; the set at budget k is {h in H : p_h(S_k) > alpha} computed on all k observations.
Named outcomes: SINGLE_SURVIVOR, HYPOTHESIS_SET_EXHAUSTED, BUDGET_EXHAUSTED.

## Arms

| Arm | Hypotheses | Rejection | Design |
|---|---|---|---|
| full (C4) | data/hybrid compile + agent EMHs for unreferenced classes | conformal | falsify |
| fixed / random / magnitude | as full | conformal | named rule |
| agent-design | as full | conformal | agent picks the option |
| world model only (C2) | data compile; unreferenced classes unrepresented (cannot be rejected) | conformal | falsify |
| agent only (C1) | agent states the surviving set | agent judgement | agent picks |
| interface (C3) | agent states the set after reading the falsifier's top p-values | agent judgement | agent picks |
| uncalibrated | as full | Gaussian-posterior credible set at 1 - alpha | as full |
| controls | class-permuted reference labels; EMHs permuted across classes | conformal | falsify |

## Metrics

* Coverage: fraction of queries whose true class is in the set (validity).
* Set size: number of non-rejected classes (falsification power); also the fraction of queries
  with a set of at most 5 classes.
* Exhaustion: rate of HYPOTHESIS_SET_EXHAUSTED when the true class is withheld from H, against the
  rate when it is present; recovery of the true class by agent revision against deterministic
  revision.
* Identifiability: agreement between predicted and realised single-option cross-rejection.
* Costs: observations (profiles) per query; provider calls and dollars reported separately.

## Statistics

Wilson intervals for coverage; paired bootstrap over drugs, resampling classes as clusters (2,000
draws, seed 20261010) for set-size differences.
