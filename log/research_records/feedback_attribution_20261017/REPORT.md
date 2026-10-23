# Report: where does the Beat AML feedback gain come from? (`feedback_attribution_20261017`)

**Status: DEVELOPMENT.** Beat AML 2.0 is exposed: it shaped the confirmation, its post-hoc repair
and this design. Nothing here confirms a method or inherits the confirmation's CONFIRMED label.

**Run.**

* Protocol, code and the three promoted modules were frozen at 2026-10-17T06:45:10Z, before any
  group outcome. The runs started 8 s later.
* `RESULTS.json` was written once by `attribution.py --summary`, and `verify.py` recomputes it.
* Deviations are in `DEVIATIONS.json`. None touches a registered number.
* Cost: 0 wells, $0, no downloads, no provider calls; local compute only. The registered runs
  took about 18 min of wall-clock time in parallel (primary 430 s, tuned 1,021 s, the five
  sensitivity configurations about 40 s).

**Units.**

* A query is one archived 7-dose AUC profile; 16 queries stand for about 112 treatment wells.
* A two-round arm adds about 72 h and needs banked cells.
* "Hits" are frozen selective events (residual robust z ≤ −3).
* The outcome is hits among the twelve follow-up queries per sample. All groups share the same
  four probe queries, which return 0.383 hits per sample, and 87.4% of probes return a readout.
* n = 520 samples, 479 patients.

## 1. Registered result

### Primary family

Configuration `primary`: rank 20, archive task, probes are the population item prior's top four.
Follow-up hits per sample:

| Group | Prior | Update | Follow-up hits |
|---|---|---|---|
| A_item | empirical population item prior | none | 0.402 |
| A | model population state | none | 0.312 |
| B | model population state | low-rank | 0.408 |
| C | RNA state | none | 0.385 |
| D | RNA state | low-rank (confirmed engine) | 0.473 |
| E_pop / E_rna | population / RNA | overall sensitivity only | 0.315 / 0.392 |
| F | RNA state | low-rank on deranged readouts | 0.358 |
| S_ridge / S_gbm | drug-specific ridge / boosted trees on 30 basal PCs | none | 0.450 / 0.365 |

Holm-adjusted at one-sided 0.025:

| Id | Contrast | Mean [95% CI] | Holm p | Positive | > 0.05 at the lower bound | Net of round cost |
|---|---|---|---|---|---|---|
| H1 | B − A | +0.096 [+0.047, +0.155] | 0.0016 | yes | no | no (one extra round) |
| H2 | D − B | +0.065 [+0.030, +0.105] | 0.0016 | yes | no | yes |
| H3 | C − A | +0.073 [+0.033, +0.113] | 0.0016 | yes | no | yes |
| H4 | D − E_rna | +0.081 [+0.033, +0.131] | 0.0016 | yes | no | yes |

**Registered decisions:**

* `Q1`: RNA_COMPLEMENTS_FEEDBACK;
* `Q_rna_prior`: RNA_PRIOR_HAS_INDEPENDENT_VALUE;
* `Q2`: STRUCTURE_BEATS_CALIBRATION.

No contrast reaches the minimum useful effect (0.05) at its lower bound.

**Sensitivity configurations.** All four hypotheses are positive in every one:

* ranks 10 and 40;
* vc0's own probes;
* the `design` task (scheduled panels, failed assays as failures, 96.9% probe return);
* `panel80` (93 high-coverage inhibitors).

The means range from +0.056 to +0.104.

**Parity.** With vc0's own top four as probes, D reproduces the confirmed `b_exploit` and C plus
probe hits reproduces the confirmed `vc0`. This was checked exactly on all 297 samples of the three
folds where the confirmation ran at rank 20.

### Registered secondary contrasts (unadjusted)

| Contrast | Mean [95% CI] | Reading |
|---|---|---|
| D − F | +0.115 [+0.061, +0.177] | which inhibitor gave which readout matters; deranged readouts are worse than no update (F 0.358 < C 0.385) |
| D − C | +0.088 [+0.042, +0.137] | the feedback gain with population probes (the confirmation's +0.073 used vc0's probes) |
| E_rna − C | +0.008 [−0.008, +0.024] | an overall-sensitivity update gives nothing measurable |
| E_pop − A | +0.004 [−0.008, +0.015] | the same without RNA |
| A − A_item | −0.090 [−0.148, −0.038] | the model's population state scores far below the empirical item prior |
| B − A_item | +0.006 [−0.051, +0.062] | feedback on the population state only climbs back to the item prior |
| C − A_item | −0.017 [−0.073, +0.042] | the RNA prior does not beat the item prior (as in the confirmation, −0.008) |
| D − A_item | +0.071 [+0.013, +0.130] | the confirmed engine beats the item prior |
| C − S_ridge | −0.065 [−0.109, −0.023] | a drug-specific ridge on the same 30 PCs beats the Virtual Cell RNA prior |
| C − S_gbm | +0.019 [−0.031, +0.069] | — |
| S_ridge − A_item | +0.048 [−0.004, +0.108] | — |

**Coherent scorer against the promoted score** (same prior and update):

| Group | Gain |
|---|---|
| A | +0.079 [+0.026, +0.138] |
| B | +0.054 [+0.008, +0.102] |
| C | +0.042 [+0.000, +0.085] |
| D | +0.044 [+0.008, +0.080] |
| E_rna | +0.044 [+0.004, +0.087] |

Coherent follow-up hits: A_coh 0.390, B_coh 0.462, C_coh 0.427, D_coh 0.517, E_rna_coh 0.437.

**Coherent versions of H1–H4:**

| Hypothesis | Contrast | Mean [95% CI] |
|---|---|---|
| H1 | B_coh − A_coh | +0.071 [+0.019, +0.121] |
| H2 | D_coh − B_coh | +0.056 [+0.014, +0.096] |
| H3 | C_coh − A_coh | +0.037 [−0.012, +0.090], not positive |
| H4 | D_coh − E_rna_coh | +0.081 [+0.033, +0.133] |

### Planner block

Coherent scorer, RNA state, total hits over all 16 queries:

| Arm | Probes k | Total hits | Rounds |
|---|---|---|---|
| vc0_coh | 0 | 0.808 | 1 |
| x2_coh | 2 | 0.867 | 2 |
| x4_coh | 4 | 0.900 | 2 |
| x8_coh | 8 | 0.965 | 2 |
| plan_l0 | chose 8 for 520/520 | 0.965 | 2 |
| plan_l05 | chose 8 for 519/520 | 0.965 | 2 |

* **Against the four-probe arm.** `plan_* − x4_coh` = +0.065 [+0.021, +0.112], which meets the
  registered Q3 planner rule.
* **Against the eight-probe arm.** The planner's choice is the same for every sample and equals
  `x8_coh` (post hoc: `plan_l05 − x8_coh` = 0.000). So the gain comes from larger probe sets, not
  from per-sample planning.
* **Choice of k.** The planner picked the largest k on its menu, so the best k may be above 8.
* **Model value against realised gain.** Exploit-first probes are the top items, so the opportunity
  cost is zero by construction.

  | k | Model EVSI | Realised gain over vc0_coh |
  |---|---|---|
  | 2 | 0.032 | 0.060 |
  | 4 | 0.060 | 0.092 |
  | 8 | 0.105 | 0.158 |

  The model under-states the realised gain by 1.5–1.9x, consistent with its thin Gaussian tails
  (§3).

### Q3: tuned procedures and the calibrated selector

Each procedure is tuned at its own best inner rank (ranks 5, 10, 20, 40; patient-grouped inner
replays with the confirmation's salts). Inner `vc0` and `b_exploit` means equal the confirmation's
in 5/5 folds (parity).

**Choices per fold:**

| Fold | Tuned ranks (vc0, exploit, lookahead) | hybrid_c | cs_l05 | cs_l0 |
|---|---|---|---|---|
| 0 | 40, 10, 10 | exploit@40 | exploit@20 | exploit@20 |
| 1 | 10, 10, 10 | exploit@10 | vc0@5 | exploit@10 |
| 2 | 20, 10, 40 | exploit@20 | vc0@20 | exploit@10 |
| 3 | 20, 10, 20 | lookahead@20 | vc0@20 | vc0@20 |
| 4 | 20, 40, 40 | exploit@20 | exploit@40 | exploit@40 |

**Total hits over 16 queries per sample:**

| Arm | Hits | Mean rounds |
|---|---|---|
| vc0_t | 0.777 | 1 |
| exploit_t | **0.871** | 2 |
| look_t | 0.860 | 2 |
| hybrid_c | 0.840 | 2 |
| cs_l05 | 0.806 | 1.43 |
| cs_l0 | 0.835 | 1.84 |

**Contrasts:**

| Contrast | Mean [95% CI] |
|---|---|
| exploit_t − vc0_t | +0.094 [+0.038, +0.154] |
| look_t − exploit_t | −0.012 [−0.072, +0.052] |
| hybrid_c − exploit_t | −0.031 [−0.061, +0.000] |
| cs_l05 − exploit_t | −0.065 [−0.122, −0.019] |
| cs_l05 − vc0_t | +0.029 [−0.010, +0.064] |
| cs_l0 − exploit_t | −0.037 [−0.061, −0.013] |
| exploit_t − b_exploit@20 | +0.017 [−0.013, +0.048] |
| vc0_t − vc0@20 | +0.008 [−0.010, +0.025] |

**Q3 (registered rule).**

* **Tuned block.** No tuned arm or selector beats `exploit_t`, so exploit-first stays the default.
  * The corrected lookahead ties it.
  * The source-verified hybrid selector, now with the corrected lookahead, loses 0.031 by choosing
    worse ranks and once the lookahead.
* **Calibrated selector.** It behaves as designed: it bridges only where a patient-level lower bound
  on half the source patients is positive (2/5 folds at a round cost of 0.05). That costs 0.065
  hits per sample against always bridging. At the declared 0.05 hits per round, the 0.57 rounds it
  saves are worth about 0.029, so it is still worse on the mean. Halving the source patients for
  calibration makes the bound too wide for this effect size.
* **Planner block.** The planner beats the four-probe arm only by always choosing eight probes (§1).

So a corrected, fully tuned exploit-first design captures all of the procedure gain that any
selector here found. Among procedure changes, only more probes helps. The coherent score (§1) is a
separate, scoring-level gain.

## 2. Post-hoc contrasts (not registered; computed after the registered analysis)

| Contrast | Mean [95% CI] |
|---|---|
| D − S_ridge | +0.023 [−0.029, +0.077] |
| D_coh − S_ridge | +0.067 [+0.012, +0.129] |
| S_ridge − C_coh | +0.023 [−0.015, +0.061] |
| B_coh − A_item | +0.060 [+0.004, +0.116] |
| C_coh − A_item | +0.025 [−0.023, +0.078] |
| D_coh − A_item | +0.115 [+0.056, +0.178] |
| x8_coh − x4_coh | +0.065 [+0.021, +0.112] |
| x4_coh − x2_coh | +0.033 [−0.000, +0.068] |

**Unmeasured follow-up queries per sample** (archive task):

* promoted groups: 1.7–1.9;
* coherent groups: 2.7–3.2;
* S_ridge: 2.65;
* A_item: 2.25.

The coherent score spends more queries on rarely archived pairs and still gets more hits.

## 3. Diagnostics (PROTOCOL.md §7; reported in full)

**Coherence** (`COHERENCE.json`):

* **Counterexample.** On the one-factor, three-item counterexample, the promoted score falls from
  0.163 to 0.000178 after any readout.
* **Martingale gap.** On held-out Beat AML samples, the promoted score's expected change is −0.0026
  over all unprobed items and −0.0067 over the top 50. The coherent score's is +1.6e-5 and +6.6e-5,
  which is zero within Monte Carlo error.
* **Calibration** on measured pairs. The observed event rate is 0.021 before the readouts.

  | Score | Mean predicted | Log loss | AUROC before | AUROC after |
  |---|---|---|---|---|
  | Promoted | 0.028 | 0.0975 | 0.729 | 0.756 |
  | Coherent | 0.018 | 0.0988 | 0.740 | 0.763 |
  | Monte Carlo, exact endpoint | 0.015 | 0.1065 | 0.737 | — |

  The model's own Gaussian tails are too thin for a z ≤ −3 event. Coherence improves ranking, not
  calibration.

**Decomposition** (`DECOMPOSITION.json`):

* **Variance split.** Of the AUC variance over measured pairs:
  * inhibitor mean: 41.7%;
  * sample-wide sensitivity: 15.2%;
  * residual: 43.0%.
* **Inside the residual:**
  * within-run replicate noise is about 41% of it, a lower bound on technical noise;
  * a ridge on 30 basal PCs predicts 9.8% of it out of fold.
* **What each state predicts on held-out patients:**

  | State | G (r) | Residual (mean within-inhibitor r) |
  |---|---|---|
  | Population, no update | −0.08 | 0.00 |
  | RNA, no update | 0.37 | 0.25 |
  | Population, four readouts | 0.42 | 0.18 |
  | RNA, four readouts | 0.51 | 0.30 |

**Outcome-related missingness.** Scheduled profiles without a record come from samples that are
more sensitive overall: mean G z −0.63 against recorded samples, in 95% of 135 inhibitors.

## 4. Interpretation

1. **The functional update is real in development, and it uses drug-specific structure.**
   * Feedback helps with or without RNA (H1, and its coherent version).
   * Deranging the readouts removes the gain and costs more (D − F).
   * Updating overall sensitivity alone does nothing (E − C ≈ 0).
   * On a G-residualised endpoint, an overall-sensitivity update is close to rank-neutral by
     construction. So H4 shows that the readouts carry information beyond overall sensitivity; it
     is not a fair test of "calibration" in general.
2. **The RNA prior's registered "independent value" is relative to a defective comparator.**
   * The model's population state under the promoted score (A) is 0.090 below the empirical item
     prior. Most of A's deficit is the promoted score's incoherence: A_coh is within 0.012 of
     A_item.
   * Against the item prior, the RNA prior does not help (C − A_item −0.017). Its coherent version
     is not positive (C_coh − A_coh +0.037 [−0.012, +0.090]). A drug-specific ridge on the same PCs
     beats it (C − S_ridge −0.065).
   * The registered label stands as computed. The scientific claim "the basal-RNA prior adds value
     beyond population information" is **not established**.
3. **RNA helps once readouts arrive (H2 and its coherent version).**
   * RNA plus four readouts predicts the residual better (r 0.30) than population plus four
     readouts (0.18).
   * This fits the RNA prior locating the sample's response factors, which the readouts then
     refine. It is a correlation, not a mechanism.
4. **The confirmed engine is not shown better than a strong static state model.**
   * D (two rounds) against S_ridge (one round) is +0.023 [−0.029, +0.077], post hoc.
   * Only the coherent version beats S_ridge (+0.067 [+0.012, +0.129], post hoc).
   * The confirmation's "feedback gain" is measured against the low-rank model's own weak prior.
     Ridge plus feedback was not built.
5. **The largest single improvement is the coherent scorer**, at +0.04 to +0.08 per group. It
   follows from fixing an identified defect, it is development-grade, and it is not calibrated.
6. **Probe count matters more than planning.** Eight probes beat four (+0.065).
   * Eight coherent probes against none (+0.158 [+0.103, +0.216]) is the only registered contrast
     whose lower bound clears 0.05 and stays positive net of the round cost.
   * The reference planner's only contribution was to pick the largest k, the same choice for every
     sample. Per-sample adaptivity shows no value.
7. **Selection adds nothing over tuned exploit-first** (Q3).
   * Tuning each procedure's own rank adds +0.017 [−0.013, +0.048] to exploit-first.
   * The hybrid and calibrated selectors lose to it.
   * The calibrated selector's safety (bridge only on a positive patient-level lower bound) costs
     more hits than the rounds it saves are worth at the declared value.

## 5. What this does not show

* Any result on unexposed data: all of this is development on the confirmation domain.
* Knowledge transfer from PRISM: every model is refitted within Beat AML.
* Clinical benefit, absolute efficacy, selectivity for malignant over normal cells, or causal
  mechanism. The endpoint is unusual relative sensitivity.
* Whether a banked sample keeps its response state across a second 72 h round.
* Whether the archive-coverage weight q_i reflects real assay feasibility. In the design task,
  failed assays are informative (§3), and `design` gives the same conclusions.
* LLM value. No provider call was made.

## 6. Next decision gate

**Blocked or missing for the next step:**

1. **Independent data.** No unexposed domain with basal state, functional readouts and uneven
   measurement is local.
2. **PRISM 24Q2 REP.1M independence is unverified.** The small release metadata files (README,
   cell-line, treatment and compound tables, figshare 25917643) are not on disk, and fetching them
   needs authorisation. The 72.5 MB outcome matrix stays sealed whatever they show. Even if
   REP.1M is independent, inhibitor-specific loadings cannot score its 1,229 new compounds, so a
   test there would be workflow transfer on source lines.
3. **Not installed or not local.** XGBoost (CellHit-style comparator) and the Beat AML malignant
   cell-type scores.

**Gate G1 (development, Beat AML, no new data, $0).** Pre-register one candidate before computing
it:

* the coherent score, plus exploit-first probes with k ∈ {4, 8, 12} chosen on source patients;
* together with "S_ridge + feedback", a ridge prior updated by the same readouts;
* tested against A_item, S_ridge and D.

Proceed only if the candidate beats S_ridge, the strongest one-round model, by more than 0.05 hits
per sample at the lower bound, net of 0.05 per extra round. Otherwise stop the low-rank state
model, and keep only the feedback design pattern on whichever prior is strongest.

**Gate G2 (confirmation).** Only after G1 passes and a new, independent, powered domain is named.
The frozen G1 candidate is run once there, with this study's power assumptions (MDE about
0.05–0.09). Until then, the strongest supported wording stays the brief's: under the Beat AML replay
endpoint and query budget, querying a few high-scoring inhibitors and updating a low-rank model on
their responses improved later choices. The value of the procedure selector and the LLM is not
established.
