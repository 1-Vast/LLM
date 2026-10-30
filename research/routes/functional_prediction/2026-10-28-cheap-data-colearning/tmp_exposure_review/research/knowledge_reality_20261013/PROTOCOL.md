# Protocol: does real biological knowledge add drug-specific information for strict cold-start compounds?

Status: **frozen** by `FREEZE.json` before any PRISM 24Q2 response value was downloaded. The
registered development stage (`DEV_PLAN.md`, run as `develop.py`, result `DEVELOPMENT.json`) came
first, on exposed PRISM 19Q4 data. This document fixes stage 2, the confirmatory test on a sealed
release, and the condition under which a stage 3 may exist.

## 0. Conditions for running stage 2

**Status at the freeze: not met.**

* The development gate reads `FAIL`: G1 and G3 pass, G2 fails.
  * Against coverage-matched gene relabelling, the knowledge gain sits at the null mean
    (empirical p 0.95).
  * The gain comes from which drugs share annotations, not from the targets' biology in each line.
* Stage 2 is therefore not run, and the 24Q2 outcome file is not requested.
* The protocol is frozen anyway, so a later decision to run it is bound by these rules.

Stage 2 runs only if all three hold:

1. **Development gate.** The gate in `DEVELOPMENT.json` reads `PASS` (G1, G2 and G3).
   `confirm.py predict` refuses with `GATE_NOT_PASSED` otherwise. The owner may override with
   `--despite-gate`. The override is written into `PREDICTION_LOCK.json` and must be disclosed in
   `DEVIATIONS.json`. The test then becomes a falsification of the development result, not a
   confirmation.
2. **Authorisation.** The owner authorises downloading the outcome file:
   `Repurposing_Public_24Q2_Extended_Primary_Data_Matrix.csv`, Figshare file 46630984,
   72,456,953 bytes, MD5 `042b15d3ebcc138a80a571b9286451ae`, CC BY 4.0.
3. **Order.** Predictions are locked (`PREDICTION_LOCK.json`) before the download. The download
   goes to `tmp/knowledge_reality_20261013/sealed_outcomes/`. `confirm.py evaluate` refuses if the
   file's MD5, the freeze or the predictions' digest differ.

## 1. Question

> For compounds the model has never seen screened, does provenance-qualified, relation-typed,
> context-conditioned target knowledge improve the prediction of *which cell lines a compound
> kills selectively*? Is the improvement larger than that of degree-, set- and
> coverage-matched randomised knowledge? Does it improve a cold-start nomination decision?

The outcome is functional: viability, measured as PRISM log2 fold change. It is not expression.
The perturbation is pharmacological, not genetic. The claim tier is **T0, strict cold start**: no
response of the query compound in any assay or modality is read.

## 2. Hypotheses

Each hypothesis is tested one-sided at α = 0.025, Bonferroni over the two.

* **H1, drug response (primary).** On active sealed compounds, the per-compound Pearson r between
  the predicted and the observed selective profile is higher for `know_full` (chemistry plus typed
  knowledge plus target context) than for `chem_full` (chemistry only). Both conditions must hold:
  * the paired mean Δr > 0, with a family-cluster sign-flip p < 0.025;
  * the observed gain exceeds the 95th percentile of the gain under each of the three knowledge
    controls (§6), 20 seeds each.
* **H2, discovery utility.**
  * Setup: in simulated cold-start campaigns of 64 sealed compounds, each arm nominates 32
    (compound, line) pairs, at most 3 per compound, by its predicted selective score. Each
    nomination costs one confirmation well.
  * Hypothesis: `know_full` finds more selective events in total than `chem_full`, with a
    campaign-level sign-flip p < 0.025.
  * The zero arm (generic 19Q4 sensitivity, no compound information) is reported beside both.

Verdicts:

* `CONFIRMED` if every condition of the hypothesis holds.
* `NOT_CONFIRMED` otherwise.
* For H1 only, `INCONCLUSIVE_UNDERPOWERED` instead of `NOT_CONFIRMED` when fewer than
  `MIN_ACTIVE` active compounds are measured (§9).

## 3. Sealed data

* **Release.**
  * PRISM Repurposing Public 24Q2 (Figshare 25917643, published 2024-05-31, CC BY 4.0).
  * Screen REP.1M, one row per Broad core at 2.5 µM, the same dose as the 19Q4 primary.
  * Processing (from the release README): log2 fold change against same-plate negative controls,
    ComBat per treatment, QC filter, median over replicates.
* **Eligible compounds** (`sealed_census.py`, `SEALED_CENSUS.json`): 1,229 REP.1M compounds absent
  from PRISM 19Q4, primary or secondary. Absence is checked three ways: Broad core, stripped name
  and InChIKey connectivity.
  * 49 compounds were refused as present in 19Q4: 23 by core, 11 by name and 15 by connectivity.
  * Each eligible compound has a structure in the Repurposing Hub sample file dated 2020-03-24.
  * REP.300 compounds (241, newer) are not in that snapshot and are not eligible.
  * The 49 overlap compounds (`sealed_overlap.csv`) are used only for the replication ceiling (§8).
* **Lines.**
  * *Panel*: the 545 lines that are in 24Q2, in the 19Q4 panel and in CCLE 19Q4 expression. This
    is the primary population.
  * *New context*: the 285 lines outside the 19Q4 panel with CCLE expression. Reported separately
    (§8); never pooled with the panel.

## 4. Information admitted at prediction time (T0)

`maestro.information_tier.require` checks every arm's declared inputs before anything is fitted.

| Input | Source | Tier |
|---|---|---|
| Query structure (Morgan r2, 2,048 bits) | Hub 2020 sample file, CXSMILES stereo block stripped | T0 |
| Query knowledge, `hub2020` snapshot (primary) | Hub 2020-03-24 targets, MoA, relation from MoA text | T0, time-matched (four years before the outcome release) |
| Query knowledge, `all_t0` snapshot (sensitivity) | adds MAP-KG 2026 curated mechanism, aggregate binding and biochemical-assay edges | T0, **not** time-matched (postdates the outcomes) |
| Lines' basal state | CCLE 19Q4 expression, hotspot and deleterious mutations | T0 (not an outcome) |
| Training compounds' outcomes | PRISM 19Q4 primary, all 4,528 parsable compounds | T0 (other compounds' responses) |

**Not admitted:**

* any 24Q2 response value;
* the sealed compounds' 2024 file annotations (`file24_target`, `file24_moa`), which are recorded
  for audit only;
* MAP-KG cell-engagement edges (T1);
* growth, viability or death assay edges (outcome-proximal), and metabolic relations.

## 5. Endpoint

The endpoint is defined identically for every arm. The generic profile, G, sets the target. It is
not an input to any arm.

* **Outcome.** Y is the REP.1M log2 fold change per (compound, panel line).
* **Generic profile.** G is the per-line median of Y over the eligible sealed compounds.
* **Selective residual.** S = Y minus the compound's own least-squares intercept and slope on G.
* **Selective event.** The robust z of S (per compound) is ≤ −3 and Y ≤ −1.
* **Measured.** At least 100 finite panel lines.
* **Active.** Measured, with at least 5 selective events.
* **Accuracy.** Per active compound, the Pearson r between the arm's prediction, residualised on
  [1, G] in the same way, and S.
  * A refused prediction (no finite value) scores r = 0, so refusals cost accuracy rather than
    shrinking the population.

## 6. Arms and controls

* **Fitting.** Every arm is fitted once on all 19Q4 compounds, with the code and hyperparameters
  frozen in `develop.py` and `models.py`.
  * Inner three-fold family CV on 19Q4 sets the chemical-ridge penalty and the non-negative stack
    weights.
  * The 19Q4 generic profile, from training compounds, residualises the training targets.

| Arm | Routes | Role |
|---|---|---|
| zero | generic 19Q4 sensitivity only | lower bound for H2 |
| `chem_full` | Tanimoto kNN + Tanimoto kernel ridge | **comparator** |
| `annot_full` | chem + Hub target/MoA Jaccard kNN | annotation baseline |
| `rkt_full` | chem + block Q's knowledge route (signed edges + MoA) | prior MAESTRO method |
| `know_full` | chem + provenance-weighted typed kNN + target-context ridge | **candidate** |
| `know_only` | typed kNN + target-context ridge | knowledge alone |
| `density_full` | chem + annotation-count ridge | annotation-density control |

**Knowledge controls.** They are built on the `hub2020` snapshot, applied to the whole combined
graph (19Q4 and sealed), with the sealed compounds as their own stratum. There are 20 seeds each,
generated by `develop.control_edges`.

* **Degree-preserving.** A curveball swap within each (relation, source) layer and stratum. MoA
  edges are swapped the same way.
* **Stratified set permutation.** Whole knowledge bundles are permuted among compounds of the same
  stratum, target-count bucket and measured-edge flag.
* **Coverage-matched gene relabelling.** Genes are permuted within strata of degree bin,
  expression-SD tertile and hotspot frequency.

A time-matched control is achieved by design here: the primary snapshot predates the outcome
release. The `all_t0` snapshot, which postdates it, is the contrast.

## 7. Analysis

* **Units.** H1's unit is the active compound. Its clusters are the first Hub 2020 MoA string, the
  development family rule; compounds without an MoA are their own cluster. The sign-flip test uses
  10,000 draws, or is exact when that is smaller. A cluster bootstrap with 2,000 draws gives the
  95% interval. The seed is 20261013.
* **H2's unit is the campaign.** Campaigns are formed by a salted hash of the core, giving 20
  campaigns of up to 64 compounds. Wells of compounds that were not measured cannot be nominated.
* **Tie-breaks.** A salted hash per compound (`develop.tie_break`), identical for every arm.

## 8. Secondary and descriptive analyses (no verdicts)

* **Strata, H1 contrast on active compounds:**
  * with a Hub 2020 target;
  * **strict new target**: no target gene shared with any 19Q4 compound;
  * **MoA unseen** in 19Q4;
  * no annotation at all.
* **Other contrasts:**
  * `know_full` against `rkt_full`, `annot_full` and `density_full`; `rkt_full` against
    `chem_full`; `know_only` against `chem_full`;
  * the `all_t0` snapshot's H1 contrast;
  * biological specificity: own-profile r minus the mean r with other active compounds' profiles.
* **Calibration.** For every arm, the locked 19Q4 logistic calibrator turns the predicted score
  into P(selective event). Brier score and ECE are computed over measured panel wells.
* **Context shift.** On the 285 new-context lines, only the target-context route can predict;
  chemistry routes average 19Q4 profiles, which do not exist there. Reported:
  * its mean r on compounds that are active there and have a target;
  * the 95th percentile of the same quantity under each control.
* **Replication ceiling.** For the overlap compounds (48 with a 19Q4 primary profile), the r
  between the 19Q4 and the 24Q2 selective profiles. It bounds the r any predictor can reach
  across the batch shift.
* **Assay shift** is reported separately from context shift. The 19Q4 primary and the 24Q2 REP.1M
  differ in screening year and processing release. The replication ceiling is its only measurement
  here; no assay-shift correction is applied.

## 9. Power

`power.py` writes `POWER.json` from `DEVELOPMENT.json` and `SEALED_CENSUS.json` only.

* **Development effect** (`know_full` − `chem_full`, 1,460 active compounds): Δr = +0.0056. The
  family-cluster bootstrap gives a standard error of 0.00145.
* **Required for 80% power** at one-sided α = 0.025: **762 active compounds**. This is
  `MIN_ACTIVE`; below it, H1 reads `INCONCLUSIVE_UNDERPOWERED`.
* **Expected.** About 396 active sealed compounds: 1,229 eligible times the development active
  share of 32%. Power at that size is about 52%.
* **Consequence.** The sealed tier cannot confirm an effect of the development size even if one is
  present. It could only refute a much larger one. This is a second, independent reason not to
  spend the sealed tier on this hypothesis (§0).
* **H2.** It has no power estimate: in development, `know_full` and `chem_full` nominated almost
  the same number of selective hits (143 and 142 of 1,000).

## 10. What does not count as evidence here

* **Event counts are not confirmed discoveries.** A selective event in REP.1M is a primary-screen
  result on held-out compounds. H2 measures how well a cold-start campaign would have nominated
  them. It is not confirmed discovery: no dose-response or orthogonal assay is available for these
  compounds, and running one is an external experiment that needs authorisation.
* **The `all_t0` snapshot postdates the outcomes.** A gain that appears only there could reflect
  knowledge curated *from* such screens.
* **Development numbers** (`DEVELOPMENT.json`) are exploratory on exposed data, and are never
  quoted as confirmation.

## 11. Stage 3 (conditional, not built)

An LLM decision layer is permitted only if H1 and H2 are both `CONFIRMED`. Its protocol would then:

* freeze `know_full` as the numerical model;
* compare, at equal information (the same T0 inputs) and equal cost (the same wells and
  turnarounds):
  * deterministic acquisition on the frozen scores;
  * ordinary retrieval-augmented generation over the same knowledge text;
  * a structured-evidence agent that may only cite typed, provenance-qualified edges;
* use deepseek-flash only, with paid calls authorised in advance;
* score confirmed selective candidates, false GO and false NO-GO, abstention, and wells and
  turnarounds spent;
* run on fresh data that neither this study nor stage 2 has opened.

If either hypothesis is `NOT_CONFIRMED`, stage 3 is not built, and the recommendation is to
stop investing in knowledge-conditioned prediction on this task.

## 12. Deviations

Any change after the freeze breaks `require_freeze` (`FREEZE_MISMATCH`), so no stage-2 step can
run on changed code. Every deviation, including ones before the freeze that touch the registered
development run, is recorded in `DEVIATIONS.json`, which the freeze does not hash. Negative
results are kept and reported.
