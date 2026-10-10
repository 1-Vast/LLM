# Block M: calibrated falsification of mechanism hypotheses (2026-10-10)

The question is whether an LLM agent and a virtual-cell world model can together **falsify**
mechanism hypotheses for a perturbation with a calibrated error rate. Three further tasks follow:
* choose observations that falsify more;
* say when mechanisms cannot be separated;
* say when no candidate fits.

The mechanism is the drug's Drug Repurposing Hub class. The observations are L1000 landmark
profiles, one line and time at a time.

The problem and design intent are in [PROBLEM.md](PROBLEM.md), written before any value was read.
The literature is in [LITERATURE.md](LITERATURE.md), the development diagnosis in
[DIAGNOSIS.md](DIAGNOSIS.md) and the registered protocol in [PROTOCOL.md](PROTOCOL.md) with
`PROTOCOL_CONFIG.json`. The protocol was frozen on 2026-10-10T13:52:43Z (`FREEZE.json`, 2,224
files). The confirmation drugs were evaluated once. Results are in `RESULTS.json`, independent
checks in `VERIFIED.json`, and a labelled post hoc diagnosis in `posthoc/`.

## Data and units

| Source | Identity | Use |
|---|---|---|
| LINCS L1000 GSE92742 Level 5 (MODZ) | `EXTRACT_RECEIPT.json` (source sha512 `6a3115cf...`) | 978 landmark genes; 9 core lines x {6 h, 24 h} at 10 uM = 18 options; 35,145 signatures |
| Drug Repurposing Hub 2020-03-24 | file header (non-commercial use) | single-mechanism annotations: 424 classes, 1,586 drugs |
| Agent hypotheses | `emh/{nolit,lit,lit_critic}/`, `analogy/`, `literature/` | DeepSeek `deepseek-flash`, written before any L1000 value was read; citations restricted to retrieved PMIDs |

* The unit is a drug, assigned by `SPLIT.json` (seed 20261010, metadata only): 726 reference,
  358 development and 502 confirmation drugs.
* Of the 502 confirmation drugs, 396 belong to the 212 classes that have reference drugs and 106
  to the 212 classes that do not ("knowledge-only": they exist only as agent hypotheses).
* The confirmation tier was a separate file refused by name (`TIER_SEALED`) until the freeze.
* Exposure: earlier MAESTRO blocks used L1000 phase 1 for other questions, so these drugs are held
  out within this block, not never-seen data.

## System under test (registered arm `episode`, design `falsify`)

* **Hypotheses.** All 424 classes. A class with reference drugs is a per-option prototype in a
  64-dimensional basis fitted on reference drugs. A class without them is the agent's
  literature-grounded executable mechanism hypothesis (EMH), compiled to the same form with
  slopes fitted on reference drugs.
* **Score.** Profile likelihood with one potency shared across options, made *relative* to the
  best hypothesis.
* **Calibration.** Split-conformal p-values, Mondrian by reference support (K, 1, 2-3, 4+) and
  observed-energy tercile. Adaptive designs use **episode calibration**: calibration drugs pass
  through the same adaptive procedure.
* **Decision.** Reject a mechanism at p <= 0.10. Budget: 4 profiles. Named outcomes:
  SINGLE_SURVIVOR, HYPOTHESIS_SET_EXHAUSTED, BUDGET_EXHAUSTED.

Development (358 drugs, about 25 configurations, all in `development/`) changed three things:
* **Relative score.** An absolute score covered weak drugs at 0.98-1.00 but the most active at
  0.16-0.64.
* **Episode calibration.** The adaptive design drifted below nominal under per-set calibration.
* **Shrinkage.** The settings were tuned on development drugs only.

## Results (502 confirmation drugs, budget 4, alpha 0.10)

| Test | Result | Verdict |
|---|---|---|
| **H1 validity** (registered arm) | coverage 0.892 [0.862, 0.917]; activity tiers 0.898 (n 236), 0.912 (n 217), **0.776 (n 49)**; mean set 354 of 424 | **FAIL**: the most active tier is below the 0.80 floor |
| Uncalibrated comparator (Gaussian-posterior 90% credible set) | coverage 0.217, mean set 29.6 | fails, as predicted |
| H2 class content: true vs shuffled reference labels | -19.0 [-29.2, -8.6] classes (coverage 0.890 vs 0.898) | PASS |
| H3 falsify design vs fixed / random / magnitude | +11.1 [-2.8, 24.6] / +8.4 [-5.4, 21.7] / +9.6 [-3.9, 23.7] | NOT_SUPPORTED: the planner's sets are not smaller |
| H4, knowledge-only drugs (106): EMH vs shuffled EMH | 0.0 [0.0, 0.0]; coverage 0.943 vs 0.943 | NOT_SUPPORTED |
| H4: EMH vs one generic prototype | +7.9 [1.8, 17.7] (EMH sets larger; coverage 0.943 vs 0.906) | NOT_SUPPORTED |
| H4: literature vs no literature; critique vs single pass | -0.02 [-0.05, 0.0]; +0.02 [0.0, 0.06] | NOT_SUPPORTED |
| H4: agent analogies vs shuffled analogies | -1.5 [-5.2, 1.4] | NOT_SUPPORTED |
| Analogies vs EMH, all drugs (no rule) | +29.1 [22.0, 36.8] (coverage 0.944 vs 0.890) | analogies make sets larger |
| H7 full system vs world model only (unobserved classes unrejectable) | -24.1 [-31.4, -17.6] | PASS, but a single generic prototype gives the same (365.7 vs 368.2 mean set) |
| H8 ranking, world model minus kNN-1, four random profiles | -0.9 [-5.6, 3.5] ranks among 212 classes | not passed (no difference) |
| Ranking with all profiles: world model minus kNN-1 / minus class-mean cosine / minus shuffled labels | -5.0 [-8.9, -1.1] / -1.4 [-4.8, 1.7] / -35.6 [-44.1, -28.2] | world model better than kNN-1 here; equal to class-mean cosine |
| H5 identifiability: predicted cross-rejection AUC, pair vs pair-blind | 0.581 vs 0.577, difference [-0.009, 0.019]; predicted rejection rate 0.260 vs realised 0.143 | NOT_SUPPORTED |
| H6 adequacy: exhaustion inside vs outside the library | 0/396 vs 0/106 | FAIL: exhaustion never fired |
| H6 revision for outside-library drugs (compiled top 5) | 0.019 vs random 0.021 vs permuted 0.009 | no revision value |

Set-size contrasts are mean differences in surviving classes (a - b; negative means a falsifies
more), with 95% class-cluster bootstrap intervals over 2,000 draws.

**Four configurations** (B = 4 profiles):

| Configuration | Coverage of the true mechanism | Mean set |
|---|---|---|
| C1 agent alone (100 drugs) | 0.00 [0.00, 0.04] | 0.18 |
| C2 world model alone (`c2_open`, 502 drugs) | 0.912 | 392 |
| C3 agent reading the falsifier's p-values (100 drugs) | 0.79 [0.70, 0.86] (0.38 and 0.29 at B 2-3) | 353 |
| Full registered system (502 drugs) | 0.892 [0.862, 0.917]; most active tier 0.776 | 354 |
| Agent chooses observations, falsifier decides (100 drugs) | 0.93 [0.86, 0.97] | 381 |

**Post hoc** (`posthoc/h1_tier_diagnosis.json`, labelled):

* **Where the coverage failure sits.** It is in the top two activity deciles: 0.74 (n 19) and
  0.64 (n 14) for the registered arm. It spans every support bucket.
* **What the repair bought.** It shrank, but did not remove, the failure of the uncorrected
  engine. With the fixed design on the same drugs, the uncorrected engine reached 0.29 in the top
  decile and 0.449 in the top tier; the per-set relative engine reached 0.735 in the top tier.
* **What the named outcomes amount to.**
  * Only 18 of 502 registered episodes ended with a single survivor, and 10 of those were the
    true mechanism.
  * 350 of 502 episodes rejected nothing at all.
  * No episode exhausted the hypothesis set.
* **Agent-chosen observations, paired on the same 100 drugs.** Sets were larger than with the
  fixed order, by +18.4 [-7.7, 46.8], and larger than random, by +24.0 [-1.4, 49.1]. The same
  per-set calibration was used for all three.

**Verification** (`VERIFIED.json`). Four checks passed:
* freeze hashes, with no file changed after the freeze;
* an independent pandas recomputation and cluster bootstrap of every summary and contrast;
* exact reruns of three arms;
* poisoning: random values left the fixed design's options unchanged while the outcomes changed.

No deviations (`DEVIATIONS.json`).

## Interpretation and limits

* **Calibration is necessary, and marginal calibration is not enough.**
  * The agent's own eliminations are not falsifications. Alone, it kept the true mechanism in 0
    of 100 drugs at B = 4.
  * A likelihood credible set kept it in 22% of drugs.
  * A conformal test reached nominal coverage on average, but it fails exactly where it rejects
    most: drugs with strong responses, where sets shrink to about 230.
  * A guarantee that holds only on average is not a licence for the cases a scientist would act
    on.
* **What the world model contributes.**
  * Class content falsifies: true labels gave 19 fewer survivors than shuffled labels.
  * As a ranker, the world model equals class-mean cosine. It beats nearest-neighbour retrieval
    only with all profiles, not with four. The development estimate that kNN-1 wins by 7.8 ranks
    did not reproduce.
* **What the LLM contributed, as measured here: nothing that survived the controls.**
  * Literature, critique, analogies and EMH content did not change falsification.
  * A generic prototype did as well as the agent's hypotheses for unobserved mechanisms.
  * As a planner, choosing observations, the agent stayed valid but did not reduce sets.
  * As a reader of p-values, it lost coverage.
* **Design and adequacy did not work.**
  * The expected-survivor planner did not beat a fixed order.
  * Predicted identifiability did not beat a pair-blind predictor and over-predicted rejection
    1.8-fold.
  * Exhaustion never fired, so this system cannot say "no candidate fits" from four profiles.

**Limits:**
* Four profiles per drug, and one dose (10 uM).
* Class-level mechanism labels, which are a coarse proxy for mechanism.
* The 49-drug most active tier gives a wide interval: [0.64, 0.87].
* Set-size H4 contrasts are nearly invariant to permuting knowledge across classes. They had
  little power by construction (`DEVIATIONS.json`), and coverage showed no content effect.
* LLM arms used 100 drugs.
* Prior exposure of L1000 phase 1 in other MAESTRO blocks.

## Not promoted

A reimplementation of the calibrated falsifier, with episode calibration, was written for `src/`.
It matched the frozen engine's p-values and episode tables on synthetic data. It was **not
promoted**, because its registered validity rule (H1) failed. No `src/` or `tools/` file changed.
The frozen engine (`falsify.py`) remains the reference implementation for the next attempt.

## Costs

* **Lab units.** Four L1000 profiles per query drug. One profile is one line x time at 10 uM.
  Public data only; no wet-lab spend.
* **Compute.** CPU only. The sealed evaluation took 3,113 s; verification took about 13 min.
* **Provider spend.** $6.47 of the $10 ceiling (`tmp/mechanism_falsification_spend.json`;
  priced usage plus 7 unknown-charge reservations, not an invoice). Of this, $4.26 was spent
  before the freeze (EMH three variants, development agent arms, analogies) and about $2.21 on
  the sealed LLM arms.

## Reproduction

```bash
python extract.py          # once; writes the open and sealed tiers and EXTRACT_RECEIPT.json
python -m pytest test_block_m.py
bash run_sealed.sh         # freeze.py -> evaluate.py -> verify.py -> make_receipt.py (one-time)
python posthoc/h1_tier_diagnosis.py
```

Run the commands from this folder. Bulk tiers are in
`data/external/lincs_l1000_gse92742/derived/` (git-ignored). The receipt is
`log/20261010/MECHANISM_FALSIFICATION.json`.
