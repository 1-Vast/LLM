# Block M protocol (registered before the sealed run)

Written 2026-10-10 after development on the open tier and before `FREEZE.json`. Machine-readable
settings, arms, contrasts and rules are in `PROTOCOL_CONFIG.json`; `evaluate.py` reads only that
file. `PROBLEM.md` states the original design intent; this file records what development changed and
why, and fixes the confirmatory analysis.

## 1. Units, tiers, exposure

* Unit: a drug (Drug Repurposing Hub name) in `SPLIT.json` (seed 20261010, metadata only).
* Reference drugs (726) fit everything: basis, class prototypes, noise, potency prior, knowledge
  slopes, calibration (set and episode), simulation residuals. Query drugs are only scored.
* Development: 358 drugs (252 of classes with reference drugs, 106 of classes without).
  Confirmation: 502 drugs (396 + 106), in `block_m_landmark_sealed.npz`, refused by name
  (`TIER_SEALED`) until `FREEZE.json` exists. No confirmation value was read during development.
* Exposure: L1000 phase 1 was used by earlier MAESTRO blocks for other estimands (PROBLEM.md §6).
  The confirmation drugs are held out within this block, not never-seen data.

## 2. What development changed (all on the open tier)

| Step | Finding (development) | Change |
|---|---|---|
| Engine v1 (absolute NLL score, per-option-set calibration) | marginal coverage 0.88-0.94, but by drug activity 0.98-1.00 for weak drugs and **0.16-0.64 for the most active** (`dev_strata.py baseline`) | score made relative to the best hypothesis; Mondrian bins by observed energy (3) |
| Adaptive design (falsify) | coverage drifted down with steps (0.90 -> 0.87) and was lowest for active drugs | **episode calibration**: calibration drugs pass through the same adaptive procedure (`falsify.episode_calibration`); used for adaptive designs |
| Ranking ceiling (`dev_ceiling.py`, `dev_scorers.py`) | the true class's 90th-percentile rank among 212 classes is ~118 with four random profiles (6 for the most active drugs) | shrinkage kappa 1 -> 0.05, potency prior variance 10; the ceiling is reported, not engineered around |
| Batch check (`dev_batch.py`, `dev_block_check.py`) | 84% of queries share a plate collection with a class member, but excluding same-collection members moves the median true-class rank only 12 -> 14 (chance ~102) | none; recorded as a negative confound check |
| Knowledge calibration pool | mateless (76 drugs) vs classes <= 3 drugs vs all reference drugs scored against their own class's compiled hypothesis | `kcal = all` |
| Agent knowledge (`dev_programs.py`, `dev_describe.py`, `dev_analogy.py`, stage 4-5 runs) | gene programs, literature and critique give no set-size gain over shuffled hypotheses or a generic prototype; agent analogies carry class information (own-class rank 0.572 vs 0.503 shuffled) but enlarge sets by ~41 classes | primary system keeps the registered EMH compiler; analogies and a generic prototype are registered comparison arms |
| Identifiability simulation | potencies drawn from the wide prior over-predicted rejection 2.7x | potencies resampled from fitted reference potencies (1.7x remaining) |

Development compared roughly 25 configurations on the same 358 drugs; every one is in
`development/*.json` with its configuration. Confirmation tests the registered system once.

## 3. Registered system (arm `episode`, policy `falsify`)

* Basis: uncentred SVD, k = 64, reference drugs only. Hypotheses: all 424 classes. Classes with
  reference drugs: per-option class mean shrunk to the generic prototype (kappa = 0.05). Classes
  without: the agent's literature-grounded EMH compiled with slopes fitted on reference drugs.
* Score: relative profile NLL (potency lambda >= 0, prior N(1, 10), per-option diagonal noise).
* Calibration: split conformal, Mondrian by support bucket (K, 1, 2-3, 4+) and observed-energy
  tercile; knowledge bucket calibrated on every reference drug scored against its own class's
  compiled EMH; **episode calibration** of the falsify design. alpha = 0.10. Budget B = 4.
* Design: expected-survivor minimisation (40 survivor draws x 4 residual draws per candidate).
* Named outcomes per episode: SINGLE_SURVIVOR, HYPOTHESIS_SET_EXHAUSTED, BUDGET_EXHAUSTED.

## 4. Arms (all on the 502 confirmation drugs; B = 4; alpha = 0.10)

| Arm | What changes | Designs | Calibration | Purpose |
|---|---|---|---|---|
| episode | registered system | falsify, fixed, random, magnitude | episode | H1 validity; H3 design |
| set | per-option-set calibration | fixed, random, falsify | set | content contrasts; calibration comparison |
| naive | engine v1 settings (absolute score, no bins, kappa 1, mateless) | fixed, falsify | set | what a standard conformal set would claim |
| perm_classes | reference class labels shuffled | fixed, random | set | H2 control |
| perm_emh | EMHs shuffled across classes | fixed, random | set | H4 control |
| nolit | literature-free EMHs | fixed, random | set | H4 literature |
| critic | EMHs after one critique-and-revision pass | fixed, random | set | H4 single pass vs critique |
| generic | every unobserved class = generic prototype | fixed, random | set | H4: is EMH content better than no content |
| analogy / analogy_perm | agent analogies / shuffled analogies | fixed, random | set | H4 alternative knowledge route |
| c2_open | world model only; unobserved classes cannot be rejected | fixed, random | set | H7 C2 |
| c2_closed | world model only; unobserved classes dropped from H | fixed, random | set | H7 closed-world comparator |

Every episode row also carries the uncalibrated comparator: the smallest Gaussian-posterior
credible set at 1 - alpha from the same compiled models.

LLM arms (100 confirmation drugs: 60 of observed classes, 40 of unobserved classes, drawn with seed
20261010 from sorted names, before any value is read): C1 agent alone (states its non-rejected
set), C3 interface (agent reads the falsifier's top p-values), agent-chosen design (agent picks
options; the falsifier with per-option-set calibration decides). The agent never sees drug names.

Ranking (H8, world model vs strong baselines): the true class's rank among the 212 observed
classes on each confirmation drug of an observed class, with all available profiles and with four
drawn at random: world-model NLL, the same with shuffled class labels, nearest reference member
(kNN-1, gene-space cosine) and class-mean cosine; paired rank differences with class-cluster
bootstrap.

Identifiability (H5): single-option cross-rejection predicted from reference drugs vs realised on
confirmation drugs of observed classes; AUC against a pair-blind predictor, 500 drug-level bootstrap
draws. Adequacy and revision (H6): library-only hypothesis set (observed classes), falsify design,
budget 4; exhaustion rates for queries inside vs outside the library; compiled, permuted and random
revision; agent revision for exhausted out-of-library queries.

## 5. Decision rules (`PROTOCOL_CONFIG.json["rules"]`)

* **H1 validity** PASS if the registered arm's coverage at B = 4 has Wilson 95% lower bound >= 0.85
  and every activity tier with n >= 30 has coverage >= 0.80. Tiers: drug activity (mean percentile
  of its signature norms among reference norms at the same options) [0, 0.5), [0.5, 0.75), [0.75, 1].
  The uncalibrated comparator "fails" if its coverage < 0.85.
* **Contrasts** (paired by drug at B = 4; mean of a - b; 2,000 bootstrap draws resampling mechanism
  classes as clusters): PASS if the 95% interval lies entirely below zero **and** both arms have
  coverage >= 0.85; INVALID_COMPARISON if the interval is below zero but an arm is invalid;
  otherwise NOT_SUPPORTED. Contrasts: H2 class content (set/fixed vs perm_classes/fixed); H3
  falsify vs fixed, random and magnitude (episode arm); H4 on drugs of unobserved classes: EMH vs
  shuffled EMH, EMH vs generic, literature vs no literature, critique vs single pass, analogy vs
  shuffled analogy; H7 full vs world model only (c2_open). Reported without a rule: analogy vs EMH
  (all drugs).
* **H8** PASS if the world model ranks the true class better than kNN-1 with four random profiles
  (95% interval of the mean rank difference entirely below zero).
* **H5** PASS if the bootstrap 95% interval of AUC(pair) - AUC(pair-blind) is above zero.
* **H6 adequacy** PASS if the Wilson intervals of exhaustion outside vs inside the library do not
  overlap (outside higher). Revision success is reported descriptively.
* LLM arms: reported with Wilson intervals; an arm is VALID if its Wilson lower bound >= 0.85.

## 6. Development estimates (predictions for the sealed run)

| Quantity | Development value | Expected verdict |
|---|---|---|
| Registered arm coverage / mean set (B = 4) | 0.894 / 351 of 424 (tiers 0.88, 0.91, 0.97, 0.84) | H1 PASS, marginal |
| Uncalibrated credible set coverage / size | 0.22 / 29 | fails |
| Class content (fixed) | -24.1 [-37.3, -11.8] | H2 PASS |
| Falsify vs fixed (episode) | +3.8 classes (falsify not smaller) | H3 NOT_SUPPORTED |
| EMH vs shuffled / generic / no literature (unobserved classes) | +1.9 [-0.2, 5.9] / -2.4 [-9.8, 3.1] / +1.3 [-1.5, 5.7] | H4 NOT_SUPPORTED |
| Analogy vs shuffled analogy (unobserved) ; analogy vs EMH | +0.2 ; +41 (larger sets) | NOT_SUPPORTED ; worse |
| Full vs world model only | -30.3 [-38.3, -22.4]; the generic prototype gives the same gain | H7 PASS, not attributable to agent content |
| Critique minus single pass (unobserved) | +0.5 [0.0, 1.5] | NOT_SUPPORTED |
| Ranking, 4 random profiles: world model vs kNN-1 / class-mean cosine / shuffled | +7.8 [2.6, 13.2] / +5.4 [1.1, 9.6] / -28.5 [-39.6, -18.6] ranks (`development/ranking_dev.json`) | H8 FAIL: the world model ranks worse than nearest-neighbour retrieval |
| Identifiability AUC pair vs pair-blind | 0.578 vs 0.574 | H5 likely NOT_SUPPORTED |
| Exhaustion inside / outside library | 0 / 0 | H6 NOT_SUPPORTED |
| C1 agent alone; C3 interface; agent design (80 drugs) | coverage 0.025; 0.24-0.86; 0.91 (set 375) | C1 and C3 invalid |

## 7. Costs

Lab units: four profiles per query (one L1000 landmark profile = one line x time at 10 uM). Provider
spend to the freeze: $4.26 (EMH three variants $2.18; development agent arms $1.76; analogies
$0.26), ledger `tmp/mechanism_falsification_spend.json`, ceiling $10. The sealed LLM arms are
expected to cost about $2.

## 8. Order of the sealed run

`freeze.py` -> `evaluate.py` (once) -> `verify.py` (freeze hashes, arithmetic, exact rerun of the
arms set, naive and perm_classes, poisoning of the fixed design). Deviations after the freeze go to `DEVIATIONS.json`.
