# Protocol: where does the feedback gain come from? (study `feedback_attribution_20261017`)

Written and frozen on 2026-10-17, before any outcome of the groups below was computed. Beat AML 2.0
is exposed: it informed the context-transfer confirmation, its post-hoc lookahead repair and this
design. **Everything here is development evidence.** No result of this study can confirm a method.

## 1. Question

The context-transfer confirmation (`research/context_transfer_20261017`) found one supported
effect. Measuring the Virtual Cell's top four inhibitors first and updating the low-rank model on
their readouts improved the other twelve choices: +0.073 hits per sample [+0.025, +0.127] over no
update. Its claims amendment (`CLAIMS.json`) records what that does not show.

This study asks three things only:

1. **Q1.** Can functional feedback without RNA explain most of that gain?
2. **Q2.** Does a structured low-rank update beat a simple update of overall sensitivity?
3. **Q3.** Does a corrected, fully tuned exploit-first design still capture nearly all of the
   procedure gain?

It also asks whether the RNA prior has value on its own (H3). Prior, planner, endpoint and budget
are not changed together: every primary contrast changes one of them.

## 2. Already seen (disclosure)

Seen before this protocol:

* **Confirmation and post-hoc results.** Every number in the confirmation's RESULTS.json,
  REPORT.md, CLAIMS.json and the post-hoc POSTHOC_*.json files. These include the Beat AML means of
  `vc0` (0.777), `item` (0.785), `b_exploit` (0.850), `knn`, the shuffled controls, the corrected
  lookahead (0.850) and every inner mean.
* **Design audits** (COST_UNITS.json, MISSINGNESS.json). These read measured masks and design
  columns, never response values.
* **Synthetic tests** (test_science.py), on simulated data only.

Not seen:

* any group below with population-chosen probes;
* the global-sensitivity update;
* the deranged control;
* the strong state models;
* the coherent scorer and the reference planner on real data;
* the tuned arms and the calibrated selector;
* the design and panel80 tasks.

With vc0's own top four as probes, groups D and C reproduce the confirmed `b_exploit` and `vc0`;
that configuration is a parity check, not a finding.

## 3. Data, units and tasks

* **Domain.** Beat AML 2.0, built by `context_transfer_20261017/data_beataml.py`:
  * 520 RNA-seq samples from 479 patients x 165 inhibitors;
  * probit AUC, 62.4% of pairs measured.

  The release census lists 166 included inhibitors. One of them is measured only in samples
  without RNA-seq, so the analysed matrix has 165.
* **Endpoint.** The frozen selective event:
  * G is the sample's median AUC;
  * each inhibitor is residualised on [1, G];
  * an event is a robust z of at most −3, with no absolute gate;
  * the inhibitor must be measured in at least 100 samples.

  This endpoint measures unusual relative sensitivity, not absolute efficacy or selectivity for
  malignant over normal cells.
* **Units.** One query is one archived 7-dose AUC profile (Tyner et al. 2018). The design has no
  replication; 16 queries stand for 112 treatment wells, plus plate controls. Rounds are counted
  separately; a second round adds about 72 h and needs banked cells (COST_UNITS.json).
* **Tasks:**
  * `archive` (primary).
    * Menu: all 165 inhibitors.
    * An unmeasured pair is a spent query with no readout and no hit.
    * Availability weight q_i: source archive coverage.

    This is the utility of querying recorded responses.
  * `design` (secondary).
    * Menu: the inhibitors on the panels each sample was actually run with (design metadata).
    * A scheduled pair with no QC-passed record is a failed assay: spent, no readout, no hit.
    * Weight: source success rate given scheduled.

    No response is imputed. QC removals and too few cells cannot be told apart in the release
    (MISSINGNESS.json).
  * `panel80` (secondary). Archive rules on the 93 inhibitors scheduled for at least 80% of samples.

## 4. Design

* **Folds.** The confirmation's five patient-disjoint folds (salt `context-transfer-subject`). The
  promoted `BridgedTransferModel` is refitted on each fold's source patients:
  * fixed common rank 20 for every group;
  * 15 EM-SVD rounds;
  * at least 100 measured samples per inhibitor.

  Rank 20 was the confirmation's most frequent choice (3/5 folds); this is disclosed. Ranks 10 and
  40 are sensitivity configurations.
* **Common probes.** Every sample gets the same four probe queries in all groups of a configuration,
  and their hits count for every group. Primary probes are the top four of the population item
  prior (source event rate x q_i, tie-break by the confirmation's hashed order). No RNA enters the
  probes. The probe queries count against every group's budget, including groups that ignore their
  readouts.
* **Groups.** Each group chooses the other twelve queries, excluding the probes.

  | Group | Prior | Update from the four readouts | Rounds |
  |---|---|---|---|
  | A_item | population item prior (empirical) | none | 1 |
  | A | model population state (no RNA) | none | 1 |
  | B | model population state | low-rank posterior (same engine as D) | 2 |
  | C | RNA state (basal-expression prior) | none | 1 |
  | D | RNA state | low-rank posterior (the confirmed engine) | 2 |
  | E_pop / E_rna | population / RNA state | overall sensitivity only (`global_posterior`) | 2 |
  | F | RNA state | low-rank posterior on readouts deranged within the sample | 2 |
  | S_ridge / S_gbm | drug-specific ridge / gradient-boosted model on the same 30 basal PCs | none | 1 |
  | *_coh | as A, B, C, D, E_rna | same, scored by the coherent scorer | as base |

  * **Scoring.** All groups except *_coh and S score with the promoted
    `q_i x BridgedTransferModel.event_prob`, so the primary contrasts change only the prior or the
    update.
  * **S models.** Event probability from Var(Y_d − b_d G) = Var(r_d) + b_d² Var(r_G) − 2 b_d
    Cov(r_d, r_G), on out-of-fold source residuals.
  * **F.** A cyclic derangement keeps the readout positions, their number, missingness and the
    multiset of values. With fewer than two returned readouts, F equals D.
* **Planner arms.** Primary configuration only; coherent scorer, RNA state; compared on all 16
  queries.
  * `vc0_coh`: no intermediate experiment.
  * `x2_coh`, `x4_coh`, `x8_coh`: exploit-first with k fixed.
  * `plan_l0`, `plan_l05`: the joint-Monte-Carlo reference planner chooses k in {0, 2, 4, 8} per
    sample by Δ = EVSI − OC − round cost. The round cost is 0 or 0.05 hits; 128 draws with common
    random numbers.
* **Tuned arms** (`tuned.py`, Q3). Ranks 5, 10, 20, 40 with patient-grouped inner replays (inner
  salt `procedure:<fold>`, corrected lookahead).
  * `vc0_t`, `exploit_t`, `look_t`: each at its own best inner rank.
  * `hybrid_c`: the promoted hybrid selector with the corrected lookahead.
  * `cs_l05`, `cs_l0`: calibrated selectors. Generation and calibration use disjoint halves of the
    source patients. The simultaneous one-sided 95% lower bound uses z = 1.96. They adopt the best
    bridge only if its lower bound on net gain over vc0 is positive, at a round cost of 0.05 or 0.

  Inner `vc0` and `b_exploit` means must equal the confirmation's (parity).
* **Configurations:**
  * `primary`: rank 20, archive, population probes, all groups and planner arms;
  * `rank10` and `rank40`;
  * `probes_vc`: vc0's own top four as probes; parity with the confirmed records on the rank-20
    folds;
  * `design` and `panel80`.

## 5. Hypotheses, analysis and decisions

**Outcome.** Hits among the twelve follow-up queries per sample. This equals the difference in
total hits because probe hits are shared.

**Analysis.** Every contrast is a paired difference over samples with:

* a cluster bootstrap 95% interval over patients (2,000 draws);
* a one-sided sign-flip p over patient means (10,000 draws, seed 20261017).

This is the confirmation's `paired`.

**Primary family** (configuration `primary`). Holm-adjusted at one-sided α = 0.025:

| Id | Contrast | Question |
|---|---|---|
| H1 | B − A | does feedback help without RNA? |
| H2 | D − B | does RNA add once feedback is present? |
| H3 | C − A | does the RNA prior help without feedback? |
| H4 | D − E_rna | does the structured update beat overall-sensitivity calibration? |

**Evidence levels.** Each contrast is reported at three levels:

1. **positive.** For H1–H4: Holm p < 0.025 and the lower bound > 0. For other contrasts: the
   unadjusted lower bound > 0.
2. **exceeds_min_useful.** Lower bound > 0.05 hits per sample.
3. **net_of_round_cost.** Lower bound − 0.05 x (extra rounds) > 0. The value of 0.05 hits per
   extra round is a declared judgement, not a price.

**Decisions** (written by the code as stated):

* **Q1:**
  * RNA_COMPLEMENTS_FEEDBACK if H2 is positive;
  * otherwise NO_RNA_FEEDBACK_SUFFICES if H1 is positive and the upper bound of D − B < 0.05;
  * otherwise INCONCLUSIVE.
* **RNA prior:**
  * RNA_PRIOR_HAS_INDEPENDENT_VALUE if H3 is positive;
  * otherwise RNA_PRIOR_ADDS_LESS_THAN_MIN_USEFUL if the upper bound of C − A < 0.05;
  * otherwise INCONCLUSIVE.
* **Q2:**
  * STRUCTURE_BEATS_CALIBRATION if H4 is positive;
  * otherwise GLOBAL_CALIBRATION_SUFFICES if the upper bound of D − E_rna < 0.05 and the lower
    bound of E_rna − C > 0;
  * otherwise INCONCLUSIVE.
* **Q3:** exploit-first remains the default unless some arm beats `exploit_t` with a lower bound
  > 0. This covers `look_t`, `hybrid_c`, the `cs_*` selectors and, in the planner block, `plan_*`
  against `x4_coh`. A selector that only equals exploit gives no evidence of selection value.

**Secondary** (unadjusted, reported in full):

* D − F (expected positive if the response mapping matters);
* D − C (the feedback gain with population probes);
* E_rna − C and E_pop − A;
* every group against A_item, and C against S_ridge and S_gbm;
* *_coh against base, and the coherent versions of H1–H4;
* the planner contrasts;
* the tuned contrasts;
* every primary contrast in each sensitivity configuration.

**What the outcomes would mean** (from the assessment that motivated this study):

* **No-RNA feedback suffices:** prioritise low-cost functional state identification.
* **RNA has independent value:** study state-conditioned response structure.
* **Global calibration suffices:** simplify the model and look for tasks that need structure.
* **Structure clearly wins:** develop joint learning of response relationships and procedures.
* **No planner beats exploit:** keep exploit as the default and move innovation to cross-task
  learning.

## 6. Power

**Expected standard errors.** The confirmation's paired contrasts suggest about 0.026 hits per
sample for an update against no update (b_exploit − vc0) and about 0.015 between two update
variants (llm − maestro).

**Detectable effects.** At Holm's worst case (one-sided 0.00625, z = 2.50) with 80% power, the
minimum detectable effect is about 0.05–0.09 hits per sample.

**Consequences:**

* Effects below that are reported as INCONCLUSIVE, unless an equivalence-style rule above is met.
* The equivalence rules need an upper bound below 0.05, which this sample size reaches only for
  well-correlated contrasts.

## 7. Development diagnostics, reported in full after the run

These are diagnostics. They are not hypothesis tests, and each is reported whatever it shows.

* **Coherence** (COHERENCE.json):
  * the synthetic counterexample;
  * for held-out samples, the martingale gap of the promoted and the coherent score;
  * the calibration (Brier score, log loss, mean predicted against observed) of the promoted
    score, the coherent score and the Monte Carlo reference against realised events on measured
    pairs.
* **Decomposition** (DECOMPOSITION.json):
  * the variance of AUC split into inhibitor mean, sample-wide sensitivity (b_d G), drug-by-state
    interaction and residual;
  * technical noise from replicate profiles in the raw file;
  * how well each prior predicts G and the interaction on held-out patients, before and after the
    four readouts.
* **Outcome-related missingness:** whether a sample's G differs between scheduled pairs with and
  without a record.

## 8. Costs and limits

* **Costs.** No wells, no paid calls, no downloads; local compute only.
* **Limits:**
  * Development evidence on exposed data. Workflow transfer within Beat AML, not knowledge
    transfer.
  * The archive task conflates biology with archive coverage; the design task cannot separate QC
    removals from missing material.
  * The static replay cannot test whether a banked sample keeps its response state between rounds.
  * A model with inhibitor-specific loadings cannot speak to unseen inhibitors.

## 9. Integrity

* **Freeze.** FREEZE.json hashes this protocol and the study code (`freeze.py`, once). `verify.py`
  checks the hashes and recomputes the registered analysis from the cached records.
* **Write-once results.** RESULTS.json is written once by `attribution.py --summary`.
* **Deviations.** Any deviation goes to DEVIATIONS.json, which the freeze does not hash.
