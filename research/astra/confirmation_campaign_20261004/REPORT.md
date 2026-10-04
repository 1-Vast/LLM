> **File summary**
> - **Path**: `research/astra/confirmation_campaign_20261004/REPORT.md`
> - **Purpose**: main report of a bounded study (2026-10-04). It asks whether confirmation-aware
>   prediction improves measured confirmation yield beyond strong simple predictors when
>   historical information, campaign duration and the binding resource cap are identical, and
>   whether purchased target-line feedback improves relative action value rather than only the
>   response level.
> - **Core points**:
>   - Everything is EXPLORATORY: Jaaks et al. 2022 was opened by earlier studies. The campaign
>     contract was frozen before this study read any outcome.
>   - **Primary verdict: EXPLORATORY_WORTHWHILE_EXCLUDED → STOP.** R confirmed 110.5 discoveries and
>     the development-selected comparator C_mean 117.5: −5.96% [−13.36%, +1.67%] on 61 held-out lines.
>   - Additional information is where the benefit lies: two-orientation history beats one-orientation
>     history by +13.4% [8.4%, 18.8%].
>   - Feedback: EXPLORATORY_NO_RELATIVE_FEEDBACK_VALUE. Every feedback increment in candidate
>     ordering is about +0.01 AUC and every interval includes 0.
>   - Stopping (no screens that cannot be verified by the deadline) keeps yield and saves 20% of
>     measurements and 31% of custom plate starts. Two rounds dominate one round.
>   - No scheduler or agent headroom. One untouched dataset qualifies for a narrower estimand. It is
>     preserved unopened, because the registered stop rule applies.
> - **Interfaces / data**: `protocol/` (contract v2, freeze, partition, access log), `design/`,
>   `resources/`, `verify/`, `receipts/`, `RUN_MANIFEST.json`.
> - **Depends on**: frozen builder `../feedback_validation_20261003/jaaks.py`; frozen
>   `research/certified_discovery/world.py`; receipts of `../reproducible_allocation_20261003/`.

# Confirmation-aware prediction under an identical campaign contract

## 1. Answers

| Question | Answer (exploratory, Jaaks 2022, 61 evaluation lines unless stated) |
|---|---|
| How much benefit comes from additional information? | **Most of it.** Same simple ranking, two-orientation history (S_both) against one-orientation history (S): 118.5 vs 104.5 confirmed, **+13.4% [8.4, 18.8]** (+0.23 per line [0.14, 0.32]). |
| Does same-information prediction improve confirmed yield? | **No; a worthwhile gain is ruled out.** R (shrunk joint-call rate) against the development-selected C_mean: 110.5 vs 117.5, **−5.96% [−13.36, +1.67]**, −0.115 per line [−0.254, +0.033]. Against S_both: −6.75% [−14.94, +1.49]. Verdict EXPLORATORY_WORTHWHILE_EXCLUDED → STOP. |
| Does feedback improve relative action value beyond calibration? | **No resolved effect.** The line-level correction cannot reorder candidates. The single centred coefficient gave +0.091 AUC [−0.016, +0.187] on 23 lines, and P3 yield was unchanged (113.0 in every arm). Stronger existing rankings gain about +0.01 AUC from feedback, and every interval includes 0. Verdict EXPLORATORY_NO_RELATIVE_FEEDBACK_VALUE. |
| What changes after accounting for time, plates and stopping? | **Stopping saves cost without losing yield.** It keeps the yield (110.5) on 80% of the cap and 69% of the custom plates. **Time:** two rounds beat one on yield and on every resource; a third round adds about 2% for 66–72% more plates and up to 12 days. **Plates:** native and custom layouts differ by about 3.5× in yield per plate start at about 235 plate starts. The earlier 5-round verify-hits advantage does not survive a fixed deadline. |
| Is there demonstrated headroom for scheduler or agent innovation? | **No.** Same-information predictors face a real screen/verify/stop choice in 1.6–15.6% of campaigns, with an oracle bound of 3.2–3.8%, below the registered 5% indication rule. The remaining headroom is in prediction: an oracle choosing the round-2 screens gains +14–19%. That is not scheduling headroom. |
| Which data, conditions and units support each conclusion? | Section 7. |

## 2. What was executed

| Step | Owner | Status |
|---|---|---|
| File-ownership plan; design-only partition (E 61 / HD 64 lines); draft contract | parent | 12:33–12:36 |
| Independent pre-freeze challenge: 2 blocking, 6 high, 8 medium, 5 low items | verify | 12:42; all adopted |
| **Contract v2 frozen** (`protocol/freeze.json`, 0 outcome reads before it) | parent | 12:43:42 |
| Development on HD lines: C* and fp* selection, power, feedback gate and fit | design | 13:01–13:04; `selection.json` hashed before any E read |
| Evaluation on E lines: primary, registered secondaries, feedback diagnostic | design | 13:04–13:05 |
| Receipt reproduction; 1/2/3-round custom and native frontier with explicit stopping; scheduler-headroom diagnostic | resources | 13:03–13:08 |
| Independent re-implementation of the primary and the selection; poisoning, budget, identity and reproducibility checks; data qualification | verify | 13:09 onward; see section 6 |
| Post hoc matched static control for the strongest feedback comparator | design | 15:52, labelled POST HOC |
| Usage-limit stop | all | about 13:12 to 15:50; agents resumed with context; no file lost |
| Provider API calls, physical experiments, commits | — | none |

All outcome readings are in `protocol/access_log.jsonl`, each logged with its owner and purpose.
Each reading checked both the contract freeze and the earlier builder freeze.

## 3. Campaign contract (frozen v2, `protocol/campaign_contract.json`)

- **Action menu.** Per target line and role assignment, the registered S × V pairs. The actions are:
  - screen(i);
  - verify(i), only for a screen hit from an earlier round, measured as the other orientation on
    disjoint plates;
  - stop. The cap does not have to be spent.
- **Endpoint.** Measured confirmed discoveries: screen call and verification call both revealed by
  purchase before the deadline. No future-information utility is registered.
- **Legal information.** The history is the HD lines of the tissue, both orientations; evaluation
  lines are never history. The target line contributes only earlier purchases. The other role
  assignment of the same line is never used.
- **Units.** Cell lines, with the two role assignments averaged within a line.
- **Cap.** M = (menu + 4) // 5 orientation measurements, with a wells-cap sensitivity. **Deadline:**
  2 rounds.
- **Primary policy P2.** Screen the first ((100 − fp) × M) // 100 candidates. Then verify round-1
  hits until the cap is used or the hits run out. No round-2 screens.
- **Comparator.** Selected on HD lines only, among S_both, L_v, C_s, C_v, C_mean and C_prod.
  τ = 5%, inherited from the earlier review. Decision rules distinguish harm, worthwhile excluded,
  small benefit, benefit detected, worthwhile, and unresolved.
- **R.** The shrunk empirical joint-call rate. It is a simple model, not a world model.

## 4. Results

### 4.1 Development selection (64 HD lines; `design/selection.json`)

C* = **C_mean**: the mean of the shrunk screen- and verification-call rates. fp* = **30**, and R's
own HD-best fp is also 30, so the own-split secondary equals the primary.

| fp (%) | 20 | 25 | 30 | 35 | 40 |
|---|---:|---:|---:|---:|---:|
| C_mean | 126.0 | 132.5 | **134.5** | 133.5 | 130.0 |
| S_both | 121.0 | 131.5 | 133.5 | 130.0 | 124.0 |
| C_prod | 123.5 | 128.5 | 132.5 | 131.5 | 130.0 |
| R | 118.5 | 123.0 | 124.0 | 122.5 | 119.5 |
| S | 114.5 | 121.0 | 124.5 | 122.5 | 120.5 |
| oracle | 153.0 | 160.0 | 164.0 | 166.0 | 170.0 |

**Power** was computed before E was used, from the development per-line variance. At n = 61, the
95% half-width of the relative gain is ±5.5%.

| True effect | P(L > 0) | P(L > τ) | P(U < τ) |
|---|---:|---:|---:|
| 0 | 0.025 | – | 0.43 |
| +5% | 0.43 | – | – |
| +10% | 0.95 | 0.43 | – |
| +15% | – | 0.95 | – |

To rule out τ at 0.95 power with no true effect needs about 250 lines. The development contrast was
−7.8% [−12.9, −2.9], but that estimate is in-sample and biased toward C*.

### 4.2 Primary and registered secondaries (61 E lines, P2 at fp 30; `design/results/eval_20261004_130452/`)

| Contrast | Totals | Per line [95%] | Relative [95%] |
|---|---|---|---|
| **R − C_mean (primary)** | 110.5 vs 117.5 | −0.115 [−0.254, +0.033] | **−5.96% [−13.36, +1.67]** |
| R − S_both | 110.5 vs 118.5 | −0.131 [−0.295, +0.025] | −6.75% [−14.94, +1.49] |
| R − C_prod | 110.5 vs 117.0 | −0.107 [−0.271, +0.057] | −5.56% [−13.75, +2.96] |
| R − C_v / C_s / L_v | vs 111.0 / 109.5 / 106.0 | – | −0.45% / +0.91% / +4.25% (intervals ±8–10%) |
| S_both − S (information package) | 118.5 vs 104.5 | +0.230 [0.139, 0.320] | **+13.40% [8.40, 18.75]** |
| R − S (information package plus target) | 110.5 vs 104.5 | +0.098 [−0.066, +0.262] | +5.74% [−3.97, +16.02] |
| P3 (3 rounds): R − C_mean | 113 vs 120 | −0.115 [−0.262, +0.025] | −5.83% [−13.60, +1.21] |
| Wells cap: R − C_mean | 110.5 vs 116.5 | −0.098 [−0.238, +0.049] | −5.15% [−12.55, +2.62] |
| All 125 lines, leave-one-line-out history | 257.5 vs 254.5 | +0.024 [−0.040, +0.096] | +1.18% [−2.03, +4.66] |
| Two-way line × pair bootstrap of the primary | – | – | [−22.84, +10.73] |

- **Primary verdict: EXPLORATORY_WORTHWHILE_EXCLUDED → STOP** for this history library and selected
  comparator. U = +1.67% < τ = 5% and L ≤ 0. The own-split secondary agrees, so no "at the
  C*-optimal split" qualification applies.
- **The larger-history sensitivity agrees.** Using all 125 lines, with shared histories, the upper
  bound (+4.66%) is also below τ.
- **The two-way bootstrap is wider**, because pairs recur across lines: it admits both −23% and +11%.
  Under that dependence structure the verdict would be UNRESOLVED.
- **Ordering.** Within-line concordance of the screen score with the joint outcome (46 lines
  defined): R 0.838 vs C_mean 0.908, −0.071 [−0.113, −0.032]. S_both 0.892, C_prod 0.909.
- **Calibration** of the joint call over the menu:
  - R: Brier 0.01443, log loss 0.0702.
  - C_prod: Brier 0.01419, log loss 0.0663.
  - R − C_prod: Brier +0.00024 [−0.00021, +0.00065].
  - **Reading:** R is calibrated about as well as the independence product, but it orders worse,
    because joint hits are rare (152 in the E menus, 1.7% of the menu) and the joint rate of a pair is
    estimated from few history lines.
- **Consumption at the 1,954-measurement cap (R / C_mean):**

  | | R | C_mean |
  |---|---:|---:|
  | Spent | 1,563.5 | 1,591.5 |
  | Screens | 1,326 | 1,326 |
  | Screen hits | 240.5 | 272 |
  | Verifications | 237.5 | 265.5 |
  | Confirmation rate | 0.465 | 0.443 |
  | Missed, never screened | 39.5 | 32.5 |
  | Missed, screened but not verified | 2 | 2 |
  | Rounds used per line | 1.90 | 1.93 |
  | Native plates touched per line | 12.9 | 13.2 |

### 4.3 Resource frontier (`resources/`; E lines; R / C_mean)

The stop rule was replayed as its own policy, not obtained by subtracting historical terminal-screen
charges. Each "spend-all" arm is that policy run with its last-round screens bought anyway.

| Campaign | Confirmed | Spent of 1,954 | Combination wells | Custom plate starts (200 controls) | Native plates | Min days (max) |
|---|---|---:|---:|---:|---:|---|
| P1, 1 round, paired | 106 / 106 | 1,932 (22 unavoidable) | 40,460 | 261 | 1,031 | 4 |
| **P2, 2 rounds, stop** | **110.5 / 117.5** | 1,563.5 | 33,159 | **234** | 787.5 | 7.6 (8) |
| P2 spend-all reference | 110.5 / 117.5 | 1,954 | 40,859 | 341 | 804.5 | 8 |
| P3, 3 rounds, stop | 113 / 120 | 1,891 | 39,578 | 388.5 | 816 | 9.5 (12) |
| P3 spend-all reference | 113 / – | 1,954 | 40,887 | 460.5 | 817.5 | 12 |
| oracle (P1 / P2 / P3) | 152 / 151 / 152 | – | – | – | – | – |

- **Stopping.** It keeps the yield and saves 20% of measurements, 19% of combination wells and 31%
  of custom plate starts. In 116 of 122 E campaigns the cap is left partly unused.
- **Time.** At the same cap, two rounds beat one in both yield (R +4.2%, C_mean +10.8%) and every
  physical resource. A third round adds about 2% for 66–72% more plate starts.
- **Controls and single agents.**
  - Control wells scale with plate starts: 46,800 at 200 controls per plate, or 59,436 at the raw
    layout's 254, for R under P2.
  - Single-agent wells come to 43,345 for R under P2. These are shared single-agent assays.
  - Failures are 0, because the release is pre-filtered.
- **Native plates are a different economy.** Every co-produced measurement on a bought plate is
  credited once.
  - At about 235 plate starts, native N2 confirms 31.5, against 110.5 for the custom P2 (R).
  - At 832 starts, native N2 confirms 132.5, but with 560,018 combination wells against 33,159.
  - The custom per-pair layout is a hypothetical; the authors never ran one.
- **Historical receipts reproduce exactly** (`resources/receipts/reproduced_totals.json`). The
  fixed split's 231.5 included 789.5 terminal screens and 199 custom plates spent on them.
  Paired's 48-unit shortfall is entirely the odd-cap residue.

### 4.4 Feedback diagnostic (gated; `design/feedback_*`)

- **Gate passed.**
  - With R's round-1 purchases fixed, an oracle choosing the round-2 screens gains +18.8% on HD.
  - 128/128 HD campaigns bought round-2 screens.
- **Fit on HD only.**
  - F0: b = 0.625.
  - Fm: c_m = 0.276.
  - Ff: c_f = 0.271, interval [0.179, 0.345], so it is kept.
- **E, role-swapped transport** (122 campaigns; AUC among eligible round-2 candidates, defined in 23
  lines):

  | Ranking | AUC | P3 confirmed |
  |---|---:|---:|
  | R = F0 = Fm | 0.608 | 113.0 |
  | Ff | 0.699 | 113.0 |
  | U_V0 (static validation prior) | 0.790 | 116.0 |
  | U_lambda | 0.798 | 116.5 |
  | U_screen_static (static world prior) | 0.785 | 117.0 |
  | U_screen_post | 0.795 | 119.0 |

- **Feedback increments, matched pairs:**
  - Ff − Fm: +0.091 [−0.016, +0.187]. This is the registered decision, giving
    EXPLORATORY_NO_RELATIVE_FEEDBACK_VALUE.
  - U_lambda − U_V0: +0.008 [−0.005, +0.020].
  - U_screen_post − U_screen_static (post hoc): +0.010 [−0.018, +0.038]; yield +1.71% [−1.43, +5.29].
- **Level correction.** Fm against F0 log loss: −0.00077 [−0.0016, +0.0001]. Fm changes
  calibration, not order.
- **Same-condition repeatability** (14 repeat lines, development grade; coefficients transported,
  not refitted):
  - U_screen_post's AUC lead over U_V0 (0.867 vs 0.760) is almost entirely static: U_screen_static
    alone reaches 0.861.
  - Feedback increments are +0.006 [−0.009, +0.028] and +0.011 [−0.004, +0.026].
  - P3 yield: 44.5 vs 44.0, and 41.0 vs 41.0.
- **Conclusion.** The earlier same-condition U_lambda 9.0 vs U_V0 7.5 is not reproduced as a
  feedback effect once the matched static control is used. The apparent ordering gains belong to the
  static priors.

### 4.5 Scheduler and agent headroom (`resources/`)

The pre-registered indication rule requires at least 10% of campaigns to face a real choice AND an
oracle bound of at least 5%.

| Predictor | Campaigns with a real choice | Oracle bound | Indicated |
|---|---:|---:|---|
| R | 1.6% (verification capacity binds in 2 of 122) | 3.2% | no |
| C_mean | 15.6% | 3.8% | no |
| S_both | 10.7% | 3.4% | no |

- **Rankings outside the same-information set.** The E-line flags for S, L_v and C_s come from
  information gaps and a hindsight-best split, not from a legal choice. On HD, the development set,
  nothing is indicated.
- **The pipeline diagnostic** p_sv/(c_s + p_s·c_v) changes nothing under the measurement cap
  (R − pipeline 0.0%). It is not an optimal policy.
- **Decision:** no scheduler or LLM arm, and no API call.

## 5. Corrections and boundaries relative to earlier reports

- **The +2.1% [−1.6, +6.1] for R − S_both** (`../reproducible_allocation_20261003/`) was a 5-round
  verify-hits replay with leave-one-line-out history. Under the frozen 2-round contract with a
  separate history library, R is below S_both and C_mean, and a worthwhile gain is excluded. The
  larger-history sensitivity (+1.18% [−2.03, +4.66]) agrees with the exclusion.
- **The +6.5% for R − S** measured an information package, not modelling.
- **Earlier "verify-hits beats paired/fixed split" claims** relied on extra rounds and unverifiable
  terminal screens. Under a 2-round deadline and stopping, P2 dominates P1, and P3 adds little.
- **The same-condition feedback signal** (U_lambda 9.0 vs U_V0 7.5) does not survive matched static
  controls.

## 6. Independent verification and data qualification (`verify/`)

- **Independent re-implementation, without importing design or resources code** (`verify/receipts/verification.json`):
  - The primary is reproduced exactly: 110.5 vs 117.5, per line −0.1148 [−0.2541, +0.0328], relative
    −5.96% [−13.36, +1.67], the same verdict.
  - The full HD development table and the selection (C_mean, fp 30) are reproduced exactly.
  - E totals for all predictors match: S 104.5, S_both 118.5, C_prod 117.0, oracle 151.0.
  - **Poisoning.** In 244 campaigns, flipping the target's unpurchased calls and randomising every
    other E line's rows changed 0 purchases.
  - **Condition identity** holds in all three tissues: the SV verification is the VS screen, and
    the reverse.
  - **Reproducibility.** A rerun gives the identical digest.
- **Two further independent agreements:**
  - The resources engine matches design purchase for purchase: 4,224 HD and 976 E campaigns, 0
    mismatches.
  - The verify agent's independent P1, P2-grid and P3 engines match every resources and design
    record: 0 mismatches across 20,972 design campaign records.
  - A read-only rerun of design's code, with the target line's unpurchased outcomes, its other role
    assignment and every other E line scrambled, changed 0 purchases in 366 campaigns.
  - All 23,868 screen reveals and 4,398 verification reveals equal the builder's values.
  - Not independently re-implemented:
    - the feedback models and their fits (only their invariants and the R-arm records were checked);
    - the wells-cap, pipeline and all-lines sensitivities (invariants only);
    - the resources native-plate replay and its accounting.
- **Data qualification** (`verify/data_qualification.json`):

  | Source | Verdict | Reason |
  |---|---|---|
  | Vis et al. 2024 Cell Rep Med 5:101687 (DOI 10.1016/j.xcrm.2024.101687), pan-cancer anchored screen | **Qualified, conditionally,** for a narrower estimand. Never opened in this repository; only design columns read | 19 ordered combinations measured in two separate screening projects at identical concentrations, on different plates, in 730 lines. Screen = one project, confirmation = the other: cross-run, same-condition confirmation |
  | Nair et al. 2023 | Not qualified | Too few units; outcome-selected menu; changed conditions |
  | BATCHIE | Not qualified | No same-condition second measurement; no pair history for a joint rate; single-well units |
  | GDSC matrix releases | Not qualified | Incomplete repeats, likely technical; tiny menus |
  | Jaaks × Vis cross-screen | Not qualified | Incomplete menu; too few units |
- **Decision on Vis.** The registered rule for an EXPLORATORY_WORTHWHILE_EXCLUDED verdict is STOP,
  and a confirmatory protocol is frozen only after a continue-type verdict. The Vis outcomes therefore
  stay sealed. Spending the only qualifying untouched release on a hypothesis that development has
  already stopped would waste it. `receipts/evaluation_blocking.json` records the minimum missing
  evidence and the conditions under which Vis should be used.
- **Verify's proposal for Vis** (`verify/untouched_plan.json`): development first on 412 lines,
  with 298 lines sealed (H/E proposal, not frozen).
  - Before any use it must validate the call rule, because the release has no synergy column.
  - Its expected 95% half-width is ±8–17%, so a small effect would likely come out UNRESOLVED.

## 7. Data, conditions and units behind each conclusion

| Conclusion | Data | Conditions | Units and dependence |
|---|---|---|---|
| Information benefit (+13.4%) | Jaaks 2022 fitted release (exposed), breast/colon/pancreas | P2, cap 20% of menu, 2 rounds; history = 64 HD lines | 61 E lines, role assignments paired; fixed history library; pairs recur (two-way bootstrap wider) |
| R not worthwhile over C_mean | same | same; sensitivities P3, wells cap, all-lines history | same; verdict "for this history library and selected comparator"; under pair dependence it would be UNRESOLVED |
| No relative feedback value | same; same-condition: 14 repeat lines from seeding-event roles (corroborated, not authenticated) | P3, round-2 decision; frozen TransferWorld, context off; coefficients fitted on HD | 23 E lines with defined AUC (76 of 122 campaigns undefined); same-condition development grade |
| Stopping and time frontier | same; raw plate records for 4-day rounds | custom per-pair layout (hypothetical) and native plates | E and HD lines; prices, labour and capacity unknown |
| No scheduler or agent headroom | same | registered indication rule | E and HD lines |

## 8. Continue, change, stop

- **Stop:**
  - pursuing R or other joint-rate predictors as a contribution over simple marginal-call rankings;
  - feedback models for relative action value;
  - scheduler and LLM arms for this problem.
- **Continue:**
  - two-round fixed-split campaigns with explicit stopping;
  - C_mean or S_both rankings on two-orientation history;
  - physical accounting by branch, reporting plates and controls next to measurements.
- **Change:**
  - acquiring or using confirmation-orientation history is where gains lie. Any future predictor
    must be compared against S_both and C_mean under this frozen contract.
- **Blocked:**
  - confirmatory claims about any surviving hypothesis, until it passes development and the sealed
    Vis release (or another qualified source) is used under a frozen builder and analysis;
  - authentication of biological replicates;
  - physical experiments.

## 9. Deviations

- **Readings applied without the parent's reply.** The design workstream applied Q1–Q9 of
  `design/questions.json`; none changes an estimand. The most consequential are the same-count
  oracle for the gate, coefficients transported to the same-condition target, and seed 20261005 for
  the two-way bootstrap.
- **Resources deviations D1–D8**, among them:
  - wells-cap P1 and P3 are its own extensions;
  - four control-count values were run;
  - a summer-time timestamp artefact.
- **Verify:**
  - the comparison script became `check_design.py` and also reruns and scrambles the design code;
  - P1 and P3 checks were added in an addendum;
  - `design_census.py` was patched after its first run to exclude BATCHIE control wells;
  - an estimated timestamp was corrected to the file time.
- **Parent.** I first typed an estimated time ("12:40") into the study plan and corrected it to the
  file time before the freeze.
- **Usage-limit stop** from about 13:12 to 15:50.
- **Post hoc.** Design addendum 2 is labelled POST HOC.

## 10. Reproduce

```powershell
$env:PYTHONPATH = 'src;.'
$py = 'D:/anaconda/envs/maestro/python.exe'
$m = 'research.astra.confirmation_campaign_20261004'
& $py -m "$m.protocol.make_partition"                      # refuses to overwrite
& $py -m "$m.design.stages" dev; & $py -m "$m.design.stages" feedback_dev
& $py -m "$m.design.stages" addendum; & $py -m "$m.design.stages" eval; & $py -m "$m.design.stages" feedback_eval
& $py -m "$m.design.addendum_2_screen_static"
& $py -m "$m.resources.reproduce_totals"; & $py -m "$m.resources.run" --stage hd
& $py -m "$m.resources.run" --stage eval --c-star C_mean --fp-star 30 --r-fp 30
& $py -m "$m.verify.independent_check"
& $py -m pytest -o addopts= research/astra/confirmation_campaign_20261004
```

Each stage logs an access and refuses to overwrite its outputs. `--dry DIR` or `all_dry` runs on a
synthetic release. Hashes, runtimes and environment are in `RUN_MANIFEST.json`.
