# Protocol: measure-or-predict indication triage for new compounds (PRISM 24Q2)

Status: **DRAFT, not frozen.** Development on exposed PRISM 19Q4 is complete
(`DEVELOPMENT.json`, `POWER.json`). No PRISM 24Q2 response value has been downloaded or read.
Freezing needs the owner's review of this document, then `FREEZE.json`, then the steps in §0.

## 0. Conditions for opening the sealed tier

**Development gate at this draft: PASS.**

The sealed outcome file is requested only if all four hold:

1. **Development gate.** `POWER.json` reads `gate_verdict: PASS`:
   * G1: the development contrast (§12) is positive with one-sided sign-flip p < 0.05;
   * G2: resampled power at the sealed size (20 campaigns) is at least 0.80;
   * G3: the loop's yield certificate is violated in no more development campaigns than the 99th
     percentile of Binomial(campaigns, 0.05).
   The owner may override a failed gate. The override is recorded in `DEVIATIONS.json`, and the
   sealed run is then a falsification of the development result, not a confirmation.
2. **Freeze.** Every file of this folder except `DEVIATIONS.json` is hashed into `FREEZE.json`
   (LF bytes). The sealed runner (`confirm.py`, built before the freeze) refuses to run on a
   mismatch (`FREEZE_MISMATCH`).
3. **Lock.** Before the download, `confirm.py lock` writes `PREDICTION_LOCK.json`:
   * the world model fitted on all 4,528 19Q4 compounds (digest);
   * the sparse-design line order;
   * every tuned parameter (§8);
   * the complete follow-up lists of the arms that read no sealed value (`zero`, `structure`);
   * the campaign membership and every random-number salt.
4. **Authorisation.** The owner authorises the download of
   `Repurposing_Public_24Q2_Extended_Primary_Data_Matrix.csv` (Figshare file 46630984,
   72,456,953 bytes, MD5 `042b15d3ebcc138a80a571b9286451ae`, CC BY 4.0) into
   `tmp/indication_triage_20261016/sealed/`.

**Why the arms need the outcome file during the run.** Probing arms buy wells. In this
retrospective design a bought well is answered from the sealed matrix. So the file cannot stay
closed until every arm has finished, as it could for a pure prediction study. Instead:

* only `confirm.py`'s outcome oracle opens the file, once, after checking its MD5;
* arms call the oracle for each well they buy and never read the matrix;
* every oracle answer is appended to `tmp/.../sealed/oracle_log.jsonl` with a running SHA-256
  chain, and the final chain digest goes into `RESULTS.json`;
* grading starts only after every arm has returned its follow-up lists;
* the run is one invocation of the frozen code. `RESULTS.json` is write-once, and a second run is
  refused (`ALREADY_RUN`).

## 1. Question

> A campaign of new compounds arrives. Nobody has screened them before. For each compound, which
> of 545 cancer cell lines does it kill *selectively*? A small budget of single-dose primary wells
> is available, plus a fixed number of follow-up slots. Should each well measure, and where? Or
> should the campaign predict from what is already known? Does an adaptive
> measure-or-predict loop put more true selective events on the follow-up list than the strongest
> conventional workflow, at the same wells and the same list size?

This is indication triage: deciding where a new compound is worth following up. The readout is
viability (PRISM log2 fold change at 2.5 µM), not expression.

## 2. Hypotheses and verdicts

**H1 (the only primary hypothesis).** At the primary budget of 16 probe wells per compound and a
follow-up list of 32 pairs per campaign, `maestro_loop` puts more registered events on its
follow-up lists than the H1 comparator, **`two_stage`**. The comparator is the strongest arm on
the development tuning folds (§12), named here before any sealed value exists.

* Test: per-campaign difference in follow-up hits, one-sided paired sign-flip, α = 0.025.
* `CONFIRMED` if the mean difference is positive and p < 0.025.
* `NOT_CONFIRMED` otherwise.
* `INCONCLUSIVE_UNDERPOWERED` instead of `NOT_CONFIRMED` if fewer than `MIN_ACTIVE` sealed
  compounds are active (§13).

**G-CERT (validity gate, not a hypothesis).** The loop's yield certificate (§9) is exact by
design. On the sealed tier, it is `VALID` if it is violated in at most the 99th percentile of
Binomial(20, 0.05) campaigns, which is 3; otherwise `INVALID`. An `INVALID` reading means the
implementation or the audit's randomisation is broken. Certificates are then not used for any
claim.

## 3. Sealed data

Inherited unchanged from `research/knowledge_reality_20261013/PROTOCOL.md` §3 and its
`SEALED_CENSUS.json`:

* **Release.** PRISM Repurposing Public 24Q2, screen REP.1M, one row per Broad core at 2.5 µM.
  Processing: log2 fold change against same-plate negative controls, ComBat, QC filter, median
  over replicates.
* **Compounds.** 1,229 eligible: absent from PRISM 19Q4 by Broad core, stripped name and InChIKey
  connectivity. Their structures come from the Repurposing Hub sample file of 2020-03-24.
* **Lines.** The 545 panel lines that are in 24Q2, in the 19Q4 panel and in CCLE 19Q4. The
  development tables use exactly these 545 lines.
* **Campaigns.** Cores are ordered by a salted hash (`campaign`) and cut into groups of 64:
  19 full campaigns and one of 13 compounds.
* **Not used.** The 285 new-context lines enter only a descriptive analysis (§11). The 24Q2
  file's own annotations are not read.

## 4. Information each arm may read

`maestro.information_tier` tiers. No arm reads any 24Q2 annotation.

| Input | Tier | Arms |
|---|---|---|
| Query structure (Morgan r2, 2,048 bits) | T0 | all model-based arms |
| Training compounds' 19Q4 responses | T0 | all arms |
| Probe wells bought in the campaign (the query's own 2.5 µM readout) | T2, costed | probing arms |
| Query L1000 profile | T1 | L1000 substudy only (§11) |

## 5. Cost model

Costs are in laboratory units. API calls and model spend are reported separately (§11).

* **Probe well.** One compound, one line, one dose (2.5 µM), single-dose primary readout. Every
  probing arm spends the same budget: on average w = 16 wells per compound, so 1,024 wells per
  64-compound campaign. The arm decides where they go. A probe on a missing value is a failed
  well: spent and logged, with no information.
* **Follow-up slot.** One (compound, line) pair sent to the confirmation assay that defines the
  endpoint. Every arm gets the same 32 slots per campaign, at most 3 per compound. Both numbers
  are inherited from knowledge_reality H2.
* **Turnaround.** Counted in assay cycles; one cycle is the PRISM 120-hour (5-day) assay.
  * `zero`, `structure`: 1 cycle (follow-up only), 5 days.
  * Fixed-panel arms: 2 cycles, 10 days.
  * `two_stage`, `maestro_loop`: 3 cycles, 15 days.
  * Using the certificate to decide whether to follow up the rest of the list adds one cycle.
* **Reference, not equal cost.** `full_panel` measures all 545 lines of every compound: 34,880
  wells per campaign, 34 times the budget.
* **Pooled-format sensitivity (descriptive).** In a pooled PRISM-style screen, the expensive unit
  is the compound, not the line. The budget curve (§11) is reported so that this reading is
  possible. No verdict depends on it.

## 6. Endpoint

Inherited unchanged from knowledge_reality §5, implemented in `common.py`:

* **Outcome.** Y, the published log2 fold change per (compound, panel line).
* **Generic profile.** G, the per-line median of Y.
  * Sealed: median over the eligible sealed compounds.
  * Development: median over the training folds' compounds.
* **Selective residual.** S = Y minus the compound's own least-squares intercept and slope on G.
* **Event.** Robust z of S per compound ≤ −3, and Y ≤ −1.
* **Active compound.** At least 5 events.
* **Follow-up hit.** A follow-up pair that is an event.

## 7. Probe simulation

A probe is answered as if it were a fresh replicate-collapsed measurement:
*probe = Y + σ(Y) · ε*.

* ε is a standard normal, frozen per (compound, line) by a salted hash (`probe`). Every arm that
  buys the same well sees the same value (common random numbers).
* σ(Y) = √(2 × f) × σ_rep(bin of Y), where:
  * σ_rep is the within-condition replicate SD of the PRISM 19Q4 secondary screen at 2.5 µM,
    pooled over 1,394 conditions and 535,084 (condition, line) cells (`BUILD.json`), by bin of
    the published value:

    | bin | Y ≤ −2 | −2 < Y ≤ −1 | −1 < Y ≤ 0 | Y > 0 |
    |---|---|---|---|---|
    | σ_rep | 0.863 | 0.646 | 0.546 | 0.491 |

  * f = 0.4497 is the variance of the median of three normal replicates, by simulation.
* The models assume a single pooled noise level, σ_probe = 0.59. Misspecification is the
  models' problem, not the grader's.
* Noise is larger at strong kills. Using the pooled value for the simulated reads would favour any
  arm that probes candidate events directly, so the binned value is used.

## 8. Arms

Each arm is fitted on all 19Q4 compounds for the sealed run, with the parameters below, which
were tuned on development folds 0 and 1.

| Arm | What it does | Probe wells | Tier |
|---|---|---|---|
| `zero` | nominates the lines with the most negative training G (no compound information) | 0 | T0 |
| `structure` | world-model prior from structure alone; ranks pairs by P(event) | 0 | T0 |
| `fixed_panel` | the first 16 sparse-design lines for every compound; ridge completion; conventional call score | 16/compound | T2 |
| `random_panel` | 16 random lines per compound; ridge completion; call score | 16/compound | T2 |
| `probe_knn` | fixed panel; average of the 10 nearest training profiles on the probed lines; call score | 16/compound | T2 |
| `fixed_calibrated` | fixed panel; MAESTRO world-model posterior; ranks by P(event) | 16/compound | T2 |
| `two_stage` | conventional adaptive screen: 2 fixed lines for all, then 8 more lines for the most-killed compounds, chosen by their own ridge completion; call score | 16/compound on average | T2 |
| `maestro_loop` | 2 seed lines for all; posterior; compound triage by event uncertainty; 16 adaptive lines per selected compound (likely-event rule); ranks by P(event); random audit of 8 of its 32 follow-up pairs | 16/compound on average | T2 |
| `full_panel` | measures all 545 lines; ranks by observed call score (reference) | 545/compound | T2 |
| `oracle` | nominates true events (ceiling) | 0 | — |

**World model** (`world.py`), shared by `structure`, `fixed_calibrated` and `maestro_loop`:

* a structure prior (10 nearest training compounds by Tanimoto, shrinkage 1);
* a rank-48 factor plus diagonal covariance of residuals across lines;
* a per-compound activity scale with a 10-point prior over training quantiles, updated by the
  probes' likelihood (a Gaussian scale mixture);
* 64 posterior samples per compound. Each sample is scored with the endpoint rule itself, so
  P(event) is the probability of the registered event.

**Loop refusals.**

* `POSTERIOR_INACTIVE` counts compounds with P(active) < 0.01 after the seed round. They come last
  in the adaptive order and get wells only if no other compound can absorb them, so the budget is
  always spent in full.
* `FAILED_WELL`: a probe on a missing value.

Ridge completion in the conventional arms is the single-scale Gaussian conditional mean of the
same covariance, with the probed values plugged in. The conventional arms differ from the loop
in three ways: no scale mixture, no event probability, no uncertainty-driven triage.

## 9. Certified yield

* **Audit.** After the loop fixes its 32-pair follow-up list, 8 pairs are drawn uniformly at
  random (`maestro.certification.draw_audit`, seeded by a salted hash of the campaign) and
  followed up first.
* **Claim.** `yield_lower_bound(32, 8, audit hits, δ = 0.05)`: a 95% lower bound on the events
  among the 24 pairs not yet followed up. It is exact for any ranking, because the audit is a
  uniform draw from a list fixed before any label was seen.
* **Price.** The audit is drawn from the follow-up list itself, so it costs no follow-up slots and
  no hits. Its only cost is one extra cycle, and only if the bound is used to decide whether to
  follow up the remaining 24.
* **Report.** Coverage, mean bound, and mean realised remainder hits, per arm. All arms are
  certified descriptively with the same audit draw; only the loop's certificate enters G-CERT.

## 10. Analysis

* **Unit.** The campaign: 20 sealed campaigns.
* **H1 test.** Exact sign-flip if 2^20 draws or fewer are needed, otherwise 20,000 draws, seed
  20261016. A campaign-bootstrap 95% interval (4,000 draws) is reported.
* **Tie-breaks.** A salted hash per compound (`tie`), identical for every arm.
* **Missing data.** Compounds with no sealed measurement stay in their campaigns. Their wells fail
  and their follow-up pairs cannot be events. No compound is removed because of its outcome.

## 11. Secondary and descriptive analyses (no verdicts)

* **Budget curve.** Every arm at w ∈ {4, 8, 16, 32}.
* **Full-panel recovery.** Loop hits ÷ `full_panel` hits, and the ratio of wells spent.
* **Measure versus predict.** Loop minus `structure`, and best fixed-panel arm minus
  `structure`.
* **Ingredients.**
  * `fixed_calibrated` minus `fixed_panel`: what calibrated P(event) buys.
  * `maestro_loop` minus `fixed_calibrated`: what adaptivity and triage buy.
  * `maestro_loop` minus `two_stage`: MAESTRO's adaptivity versus conventional adaptivity.
* **Indication level.** Distinct (compound, lineage) pairs with at least one follow-up hit.
* **Turnaround.** Hits per cycle and per day.
* **Replication ceiling.** For the 48 overlap compounds (knowledge_reality §8), the correlation
  between the 19Q4 and 24Q2 selective profiles. It bounds what any transfer from 19Q4 can reach.
* **New-context lines (285).** For loop-selected compounds only: the share of their events on new
  lines. These lines are not in the follow-up population, because no arm has training data for
  them.
* **L1000 substudy (registered, development not run).**
  * Population: the 126 sealed compounds with an L1000 compound signature (123 in GSE92742, 13 in
    GSE70138; census of 2026-10-16, IDs only).
  * Contrast: the loop with an L1000-transfer prior (`virtual_cell.transcriptional_transfer`, T1)
    against the loop with the structure prior and k extra probe wells. An L1000 profile is priced
    at k ∈ {1, 4, 16} wells.
  * About 40 actives are expected, so this is a pilot. It is reported descriptively and its
    verdict-free status is fixed now.
  * Development requires extracting GSE92742 signatures for the 19Q4 compounds. Until that
    development exists, the substudy is `DEV_NOT_RUN` and is not run on sealed data.
* **LLM agent arm (registered, not run).**
  * Design: a deepseek-flash ReAct agent with the same tools (buy probes, read the world-model
    posterior, submit the follow-up list), the same wells, slots and cycles.
  * Prompts present ranked candidates with at most three-digit identifiers and ask for small fixed
    k. Exact-k selection failed with four-digit identifiers in an earlier study.
  * Estimated spend: about 130 calls per campaign. At block Q's observed USD 0.0015 per call,
    that is about USD 4 for development (70 campaigns) and USD 4 for the sealed run.
  * It runs only after the owner authorises the spend and it passes the same development gate.
    Its contrast with the loop is secondary and cannot change H1's verdict.

## 12. Development results (exposed 19Q4; exploratory, never quoted as confirmation)

`develop.py` ran once, in 612 s. Estimation used folds 2-4: 2,398 compounds, 708 active, 39
campaigns. Each fold was predicted from a world model fitted on the other four, and the
development G is the training folds' median.

**Choices made on tuning folds 0 and 1** (w = 16):

* **`maestro_loop`:** k1 = 2, k2 = 16, likely-event rule, with 359 tuning hits.
  * It tied with the uncertain-event rule (359). The tie went to the first option in the listed
    order.
  * Settings with no seed wells (k1 = 0) reached 356.
* **`two_stage`:** k1 = 2, k2 = 8 (229 hits).
* **`probe_knn`:** 10 neighbours.
* **H1 comparator:** `two_stage`, with 229 tuning hits. The others: `fixed_calibrated` 205,
  `fixed_panel` 185, `probe_knn` 172, `random_panel` 135, `structure` 98.

**Primary budget, estimation folds** (39 campaigns, 1,248 follow-up slots per arm):

| Arm | Follow-up hits | Hit rate | Probe wells | Failed wells | Cycles | Certificate violations | Mean bound / realised (24 unaudited) |
|---|---|---|---|---|---|---|---|
| `zero` | 26 | 0.021 | 0 | 0 | 1 | 0 | 0.00 / 0.46 |
| `structure` | 96 | 0.077 | 0 | 0 | 1 | 1 | 0.10 / 1.72 |
| `random_panel` | 139 | 0.111 | 38,368 | 878 | 2 | 1 | 0.15 / 2.59 |
| `fixed_calibrated` | 225 | 0.180 | 38,368 | 1,812 | 2 | 2 | 0.51 / 4.41 |
| `fixed_panel` | 238 | 0.191 | 38,368 | 1,812 | 2 | 0 | 0.41 / 4.56 |
| `probe_knn` | 239 | 0.192 | 38,368 | 1,812 | 2 | 0 | 0.41 / 4.64 |
| `two_stage` | 293 | 0.235 | 38,368 | 906 | 3 | 1 | 0.74 / 5.79 |
| **`maestro_loop`** | **395** | **0.317** | 38,368 | 4,010 | 3 | 2 | 2.03 / 7.54 |
| `full_panel` (reference) | 746 | 0.598 | 1,306,910 | 31,418 | 2 | 0 | 6.97 / 13.97 |
| `oracle` (ceiling) | 1248 | 1.000 | 0 | 0 | 1 | 0 | 16.00 / 24.00 |

**Primary development contrast.** `maestro_loop` minus `two_stage` is +2.62 hits per campaign
(campaign-bootstrap 95% interval [+1.67, +3.62]), one-sided sign-flip p = 5.0e-05.

* The loop was better in 26 of 39 campaigns and tied in 4.
* Overall it found 35% more hits.

**Where the gain comes from.**

* `fixed_calibrated` minus `fixed_panel`: −0.33 per campaign (p 0.80). Ranking by calibrated
  P(event) buys nothing on the same lines.
* `maestro_loop` minus `fixed_calibrated`: +4.36 (p 5.0e-05).
* `maestro_loop` minus `two_stage`: +2.62.
* Compound triage plays a small part: 2,100 of the 2,398 compounds received adaptive wells, and
  96 were `POSTERIOR_INACTIVE`.
* The gain therefore comes from **which lines each compound is measured on**: lines chosen by the
  posterior probability of the registered event, rather than by a ridge completion's call score.

**Budget curve** (follow-up hits over 39 campaigns; the H1 comparator was fixed at w = 16):

| w | `maestro_loop` | `two_stage` | loop − two_stage, p | Best other arm |
|---|---|---|---|---|
| 4 | 161 | 122 | 0.012 | `two_stage` 122 |
| 8 | 265 | 243 | 0.155 | `two_stage` 243 |
| 16 | 395 | 293 | 5.0e-05 | `two_stage` 293 |
| 32 | 513 | 365 | 5.0e-05 | `fixed_calibrated` 495, `probe_knn` 492 |

* The advantage is not uniform. At w = 8 it is not significant.
* At w = 32 the fixed panels catch up with the loop (513 against 495). This is untested, but it is
  the same pattern as block Q's fixed sparse design.

**Measure versus predict.**

* The loop finds +7.67 hits per campaign more than `structure`.
* It recovers 53% of `full_panel`'s hits with 2.9% of its wells.

**Probe-noise sensitivity** (w = 16):

* Without noise: loop 754, `two_stage` 573.
* At twice the noise: loop 245, `two_stage` 182 (p 0.0018).

**Certificate.**

* The loop's bound held in 37 of 39 campaigns. G3 allows 6 violations.
* The mean bound was 2.03 events, against 7.54 realised among the 24 unaudited pairs. It is
  valid but loose: it certifies about a quarter of what is there.

**Known weakness.** 10.5% of the loop's wells fail (4,010 of 38,368), against 4.7% for the fixed
panels. The likely-event rule targets (compound, line) cells that the published matrix leaves
missing. Training-set missingness per line is T0 information and could be used. Any such change
goes back through tuning folds 0-1 and is disclosed.

**What development does not show.** Development compounds are 19Q4 compounds held out by MoA
family: same release, same processing. The sealed tier adds a release and batch shift (2024,
ComBat). The replication ceiling (§11) is its only measurement.

**Disclosures about the development path.**

* Fixed before any development run: the primary budget (w = 16), the endpoint, the campaign size,
  the list size and the cap.
* A first smoke run, on one sixth of the compounds of all five folds, was seen before the full
  run. After it, three changes were made. Each makes H1 harder:
  * the conventional `two_stage` arm was added to the comparator pool;
  * probe noise became dependent on effect size, larger at the strong kills where the loop
    probes;
  * the loop grid was extended to k1 = 0 and k2 = 64.
* A second smoke run was seen before the full run (w = 16: loop 60, `two_stage` 56).
* The full run was run once. `DEVELOPMENT.json` is its output.

## 13. Power

`power.py` writes `POWER.json` from `DEVELOPMENT.json` and `SEALED_CENSUS.json` only.

* **Development effect.** +2.62 hits per campaign, SD 3.23 over 39 campaigns.
* **Required.** 12 campaigns for 80% power at one-sided α = 0.025. The sealed tier has 20.
* **Power at 20 campaigns:**
  * 0.95 by normal approximation;
  * 0.93 by resampling development campaigns and applying the registered sign-flip test.
* **Activity shift** (an assumption, not a measurement). If the sealed active share is a fraction
  r of development's 29.5%, the mean difference is scaled by r and its SD by √r:

  | r | 1.0 | 0.75 | 0.5 |
  |---|---|---|---|
  | power | 0.93 | 0.86 | 0.69 |

* **`MIN_ACTIVE` = 227**: 12 campaigns × 64 compounds × 0.295. Below this, H1 reads
  `INCONCLUSIVE_UNDERPOWERED`. About 363 sealed actives are expected at the development share.
* **Development gate: PASS.**
  * G1: p = 5.0e-05.
  * G2: power 0.93 ≥ 0.80.
  * G3: 2 violations ≤ 6 allowed.

## 14. Stop rules

* **Before the sealed tier.** Gate `FAIL`: the tier is not opened for H1, and nothing in this
  study is promoted. The tier stays sealed for a better-justified hypothesis.
* **H1 `NOT_CONFIRMED`.** The adaptive-loop claim stops. The H1 comparator becomes the
  recommended workflow for this task. No further adaptive or agent layer is built on this task
  without a new development signal.
* **H1 `INCONCLUSIVE_UNDERPOWERED`.** No claim either way. The tier is spent, and that is
  recorded.
* **H1 `CONFIRMED`.** Only then may the loop be promoted, and only within scope: PRISM, 2.5 µM,
  545 panel lines, primary-screen endpoint. A prospective wet-lab round is the next step;
  generalisation to other assays is not claimed.
* **G-CERT `INVALID`.** Certificates are withdrawn from every claim until the defect is found.

## 15. What does not count as evidence

* **Primary-screen events are not confirmed discoveries.** REP.1M is a single-dose primary
  screen. A follow-up hit means the pair is an event in the published matrix. No dose-response or
  orthogonal assay exists for these compounds.
* **The probe is simulated** from the published value and a frozen noise model. A real campaign's
  wells would carry their own batch and plate effects.
* **Development numbers** (§12) are exploratory on exposed data and are never quoted as
  confirmation.
* **The certificate is exact for the published matrix as truth.** It says nothing about a
  different assay.

## 16. Exposure and competing claims on the tier

* **PRISM 19Q4 is exposed.** Blocks N and P, knowledge reality and selective hit triage all read
  it. Development uses it knowingly.
* **24Q2 metadata was read on 2026-10-13** (knowledge_reality): compound list, treatment and
  cell-line metadata. The 2026-10-16 L1000 overlap census read compound IDs only. No 24Q2 response
  value has been read by anyone (`verify.py` checks that the outcome file is absent).
* **Competing claim.** knowledge_reality's stage 2 is frozen against the same tier. Its gate failed
  and its power is about 52%, so it is not scheduled to run. Opening the tier for this study ends
  the tier's sealed status for that protocol too. Choosing between the two is the owner's call.

## 17. Deviations

After the freeze, any change breaks `FREEZE_MISMATCH`. Every deviation, including disclosures made
between this draft and the freeze, goes into `DEVIATIONS.json`, which the freeze does not hash.
Negative results are kept and reported.
