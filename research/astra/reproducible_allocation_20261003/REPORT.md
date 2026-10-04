> **File summary**
> - **Path**: `research/astra/reproducible_allocation_20261003/REPORT.md`
> - **Purpose**: main report of the 2026-10-03/04 continuation
>   (`../direction_exploration_20261003_v2/NEXT_PROMPT.md`). It asks whether reproducibility-aware
>   predictions improve how a fixed budget is split between screening, independent verification
>   and stopping, beyond strong simple policies. Three subagent workstreams (repeats, allocation,
>   review) ran in separate folders under a file-ownership plan written first.
> - **Core points**:
>   - Everything measured here is **EXPLORATORY**. The only complete dataset, Jaaks et al. 2022,
>     was opened by the earlier feedback-validation study. No untouched dataset qualifies, so the
>     model × scheduler 2×2 is delivered as an executable protocol, not frozen and not run.
>   - At an equal, fully spent budget with a terminal verification round, verifying screen hits still
>     beats measuring both orientations of every pair (+17.7% [13.1, 23.1]). It needs 5 rounds where
>     paired measurement needs 1. At 2 rounds a development-selected fixed split is better.
>   - The repeat hierarchy is corroborated (plate → seeding date and culture expansion), not
>     authenticated.
>   - Target-line feedback with a fitted λ ≈ 0.3 improves squared error slightly. It does not improve
>     the ordering of candidates on the role-swapped measurement, so model complexity stops here.
>   - A static reproducibility-aware ranking raises confirmed discoveries by +6.5% [2.6, 10.6].
>     About two thirds of that comes from using both orientations of other lines' history. The
>     adaptive scheduler adds nothing. No LLM arm was run.
> - **Interfaces / data**: `protocol/` (study plan, access log), `allocation/`, `repeats/`,
>   `review/`, `receipts/`, `NEXT_PROTOCOL.json`, `RUN_MANIFEST.json`.
> - **Depends on**: `../feedback_validation_20261003/` (frozen builder and verdict bootstrap,
>   imported unchanged) and `research/certified_discovery/` (frozen world model).

# Reproducibility-aware allocation of screening and verification

## 1. Answer

Partly, and only on exposed data.

- **The predictor helps.** A static predictor that uses other cell lines' independent
  confirmations allocates a fixed budget better than the screen-label predictor: +6.5% [2.6, 10.6]
  more confirmed discoveries under the same scheduler. Most of that gain (+4.4% [2.0, 6.8]) comes
  from giving the static ranking both orientations of the history. Explicitly modelling
  confirmation adds +2.1% [−1.6, +6.1], which is not resolved.
- **Target-line feedback does not.** It does not improve which candidates to buy next.
- **The adaptive scheduler does not.** It adds nothing over verify-hits.
- **Verify-hits pays in time.** Its advantage over paired measurement and a fixed split at equal
  measurements depends on taking more rounds: at 2 rounds the fixed split is better.

None of this is confirmation: every number comes from Jaaks 2022, which was already opened. No
qualified untouched dataset exists, so the frozen 2×2 is blocked
(`receipts/phase3_blocking.json`).

## 2. What was executed, and what was not

| Kind | Item | Status |
|---|---|---|
| File ownership and rules | `protocol/STUDY_PLAN.md` (23:50, before any parallel edit) | Written |
| Phase 1 repair (allocation) | Reconciliation of the original follow-up; equal-budget replay with carry-over, terminal round, two budget units and two plate models; post hoc time matching; addenda 2 (predictor × scheduler) and 3 (information-matched rankings) | Executed; plans written before each outcome read |
| Phase 2 (repeats) | Repeat provenance from the authors' raw plate records; scalar correction `prior + λ × feedback` on role-swapped (125 lines) and same-condition (14 lines) targets; post-hoc R² correction | Executed |
| Review | Statistical validity, decision rules, threshold and power, data qualification, LLM decision, novelty, assumption challenges | Executed |
| Parent audits | Purchase-log audit of the replay (conservation, legality, confirmed counts); recomputation of the repeats contrasts from per-line records | Executed; all matched |
| Phase 3 2×2 | Frozen comparison on untouched data | **Blocked** (DATA_NOT_QUALIFIED, INSUFFICIENT_UNITS_FOR_TAU); executable protocol written and dry-run on synthetic data |
| LLM arm | — | Not run (no specific decision contribution identified) |
| Provider spend | — | USD 0 (no calls) |
| Physical experiment | — | None; nothing here is wet-lab evidence |

Every outcome reading is in `protocol/access_log.jsonl`: 8 entries, each labelled with its owner,
purpose and EXPLORATORY status. The earlier study's freeze was verified intact at every reading, and
its vault log was not written.

**Interruption.** The three subagents stopped at a session usage limit right after launch, at
about 23:51. They were resumed at 02:12 and had written nothing before the stop.

## 3. Phase 1: the repaired verification-allocation comparison

### 3.1 Why the original +16% was not an equal-consumption estimate

`allocation/results/reconciliation.json` reproduces every published total of
`../feedback_validation_20261003/results/followup_verification.json` exactly: 3,958 vs 3,762
measurements and 238.5 vs 205.0 verified discoveries. The instrumented copy agrees on 1,500/1,500
runs.

- **Paired measurement lost 196 units.**
  - 48 were unavoidable: 48 lines have an odd budget M, and pair-only actions leave 1 unit.
  - 148 were avoidable: the per-round `budget // 2` remainder was never carried forward. 117 lines
    lost something.
- **Final-round hits were never verified.** The original verify-hits left 64.5 hits from its last
  round unverified, and 23.0 of them would have validated.
- **Wells did not match either.** At the builder's charge of 14 wells × plates, verify-hits used
  80,794 combination wells (68,460 screening, 12,334 verification) against 76,412 for paired.

### 3.2 Repaired design (`allocation/plan.json`, written 02:19–02:20, before the 02:31 reading)

- **Budget.** M = ceil(0.20 × menu) orientation measurements per line; every arm spends exactly M.
  Paired spends M − (M mod 2), and that remainder is recorded as unavoidable. Unused capacity carries
  forward.
- **Physical version.** The budget is combination wells instead, W = 81,507 in total; a purchase
  costs 14 × the plates behind it in the release.
- **Terminal capacity.** In round R, screening is limited by a reserve sized from history
  screen-call rates. A verification-first terminal round R+1 follows. Capacity left after it buys
  "terminal screens", which cannot be verified and are reported separately. The extra round counts
  as elapsed time.
- **Strong baselines.**
  - Full-feasible-budget paired.
  - A fixed split, with f selected leave-one-tissue-out: breast 0.35, colon 0.40, pancreas 0.30.
  - Verify-hits with terminal round.
  - Historical confirmation probability per cost.
  - Screen-only and random as zero arms.
- **Resource accounting by branch.**
  - Dose points, combination wells and native Jaaks plates.
  - A custom 1,536-well plate model with 200 documented control wells per plate and single-agent
    wells per distinct drug role.
  - Failures, unused capacity, rounds and wall time.

### 3.3 Results (125 lines; each line is the mean of the SV and VS role assignments)

| Arm (measurement budget) | Spent | Screens / verifications | Screen hits | Confirmed | Confirmation rate | Rounds |
|---|---:|---:|---:|---:|---:|---:|
| screen_only | 3,958 | 3,958 / 0 | 694 | 0 (277.5 hidden validated) | – | 1 suffices |
| paired_full | 3,910 (48 unavoidable) | 1,955 / 1,955 | 499 | 214.5 | 0.430 | 1 suffices |
| fixed_split_dev | 3,958 | 3,401.5 / 556.5 | 638 | 231.5 | 0.416 | 2 suffice |
| verify_hits_terminal | 3,958 | 3,344 / 614 | 632.5 | 252.5 | 0.411 | 5 |
| conf_per_cost | 3,958 | 3,381.5 / 576.5 | 585 | 268.0 | 0.465 | 5 |
| verify_hits without terminal round | 3,958 | – | – | 238.5 | – | 4 |
| random ranking, verify-hits (20 seeds) | 3,958 | 3,774.5 / 183.5 | 192.5 | 59.3 | – | 5 |

- **Failures.** None of the purchased measurements failed. The release is already QC-filtered: 0
  rows were excluded, so plates the authors dropped before export cannot be seen.
- **Screen-only.** Zero observed confirmations follows from the reporting rule; it does not mean zero
  biological hits.

Contrasts use the line-stratified bootstrap (10,000 resamples, seed 20261003), shown as relative
gain [95% interval].

| Contrast | Measurement budget | Wells budget |
|---|---|---|
| verify-hits-terminal − paired_full | +17.7% [13.1, 23.1] | +17.2% [13.0, 22.1] |
| verify-hits-terminal − fixed_split_dev | +9.1% [5.4, 13.5] | +7.5% [3.9, 11.5] |
| verify-hits-terminal − conf_per_cost | −5.8% [−9.3, −2.1] | −5.3% [−8.6, −1.7] |
| terminal round − none | +5.9% [3.8, 8.3] | +7.5% [5.3, 9.9] |
| feedback ranking − static ranking, under verify-hits | −1.4% [−4.6, +1.7] | −1.6% [−5.7, +2.1] |

**Elapsed time.** The raw records give 4 calendar days from seeding to read-out on all 3,106
plates, so each round takes at least 4 days. Culture expansion before seeding is not recorded.

| Rounds compared | Result |
|---|---|
| verify-hits needs 5 rounds (≥ 20 days); paired gets the same result in 1, the fixed split in 2 | – |
| verify-hits squeezed to 2 rounds | 210.5 |
| verify-hits at 3 rounds | 246.5 |
| post hoc, both at 2 rounds: verify-hits vs fixed split | −9.1% [−14.3, −3.4] |
| post hoc: verify-hits at 3 rounds vs fixed split at 2 | +6.5% [3.0, 10.6] |

**Physical resources by branch** (`allocation/receipts/accounting.json`; measurement version,
screening / verification):

| Arm | Combination wells | Custom plates | Control wells (custom) | Native plates touched |
|---|---|---:|---|---:|
| screen_only | 80,752 / 0 | 927 | 185,400 | 1,111.5 |
| paired_full | 40,173 / 39,200 | 1,696 | 173,400 / 165,800 | 1,981.5 |
| verify_hits_terminal | 67,711 / 13,034 | 1,484 | 202,000 / 94,800 | 1,619.5 |
| fixed_split_dev | 68,775 / 12,012 | 1,293.5 | 216,500 / 42,200 | 1,597.5 |
| conf_per_cost | 67,515 / 12,355 | 1,452.5 | 198,300 / 92,200 | 1,607.5 |

- **Equal wells is not equal plates or controls.** Custom plates differ by up to 2.2× between arms
  (review challenge A1), and no plate-budget replay was run.
- **The controls figure is the documentation's, not the raw layout's.** The custom-plate model uses
  the 200 control wells per plate the documentation states. The authors' raw layout has 216–254
  (`repeats/receipts/provenance.json`).
- **Per-pair purchase is a custom-plate hypothetical.** On the native Jaaks plates the purchased
  orientations fill only 6–11% of the combination wells.

## 4. Phase 2: what feedback can generalize

### 4.1 Repeat provenance (`repeats/receipts/provenance.json`): CORROBORATED_NOT_AUTHENTICATED

The status rule was written into `provenance.py` before it ran.

- **Per-plate records.** The authors' raw plate records (figshare 19141916; md5 matches; design
  columns only, intensities never read) give each plate one seeding date (`DATE_CREATED`), one
  read-out date, one culture expansion (`CELL_ID`), a seeding density and a drug set. The CancerRxGene
  gdscIC50 vignette defines these fields. All 3,106 fitted plates match on barcode, line and SIDM.
- **Seeding events.** The 606 (line, seeding date) events correspond one-to-one with the fitted
  release's day-1 normalisation groups. 2,999 plates have exactly one same-day day-1 plate
  (figshare 19141919); 107 plates in 26 events have none. That missing link is why the status is not
  AUTHENTICATED.
- **The 14 repeat lines.** Supplementary Table 2 ("Replicate cell line") names exactly the 14 lines
  that have multiple seeding events per doublet.
- **"Seeding event = the paper's biological replicate" is UNKNOWN.**
  - Minimum (2) and median (4) events per combination match the Methods. The maximum per
    combination is 5; the documented 18 is reached only per anchor concentration in a line.
  - "Three technical replicate plates per biological replicate" (peer-review file) does not hold for
    combinations: most (line, doublet, event) cells hold 1 plate.
- **Independence.** Repeats are separate seedings on different dates, each with its own day-1
  reference, dosing and read-out. In 9 of the 14 lines all of them come from one culture expansion,
  so they are re-seedings of one stock, not independent frozen stocks. Plates within an event are
  technical repeats.
- **Controls per plate** (raw tags, identical on every plate): 6 untreated, 114 DMSO plus 0–38
  DMSO-only positions, 28 blank, 34 MG-132 and 34 staurosporine. The documentation states 200 control
  wells.

### 4.2 Scalar correction (`repeats/plan.json` 02:37, before the 02:50 reading)

The model is `validation prediction = static validation prior V0 + λ × feedback`, with λ fitted on
development lines and λ = 0 allowed.

- **Feedback, unpurchased candidates (U):** the frozen TransferWorld posterior minus its prior, given
  the line's purchased screen labels.
- **Feedback, purchased candidates (P):** the candidate's own screen residual.
- **Folds:** 5 tissue-stratified line folds on the role-swapped target; leave one repeat line out on
  the same-condition target.

**Fitted λ.** No fold selected λ near zero.

| Target | λ_U (what to buy next) | λ_P (which purchases to trust) |
|---|---|---|
| Role-swapped, 125 lines | 0.263–0.304 | 0.371–0.395 |
| Same-condition repeat, 14 lines | 0.238–0.364 | 0.580–0.619 |

Contrasts are λ model minus comparator, line-stratified bootstrap; lower squared error is better.

| Target, estimand | Squared error vs strongest simple | Ordering (concordance) | Decision metric |
|---|---|---|---|
| Role-swapped, U | −0.71 [−1.10, −0.34] of 44.3 | −0.0006 [−0.0020, +0.0008] | top-10% validation-call rate −0.001 [−0.005, +0.002]; 2-round validated discoveries +3.05% [−0.93, +7.27] |
| Same-condition, U | −0.81 [−1.83, +0.15] of 43.5 | +0.0065 [0.0029, 0.0101] | 9.0 vs 7.5 validated discoveries (14 lines) |
| Role-swapped, P | −12.2 [−15.0, −9.6] | +0.031 [0.023, 0.038] | verifying the top 25% by λ_P confirms 1.74 per line, against 1.97 for "screen hits first" |
| Same-condition, P | −13.5 [−19.9, −7.9] | −0.002 [−0.009, +0.004] | 3.0 vs 3.36 for "screen hits first" |

- **Full-weight feedback is worse than none.** Feedback at λ = 1, the registered model's implicit
  weight, predicts the independent measurement much worse than the static prior. Its squared error is
  65.7 for the registered screen posterior, against 44.3.
- **For unpurchased candidates the gain is a level shift.** The correction looks like a per-line
  shift: squared error improves, but ordering does not on the role-swapped measurement. On
  same-condition repeats there is a small ordering gain, but its squared-error interval includes 0,
  so the pre-specified stop rule fires for that cell.
- **For purchased candidates λ_P is plain test-retest shrinkage.** It does not beat "verify screen
  hits first".

**Decision.** Feedback improves prediction slightly but not the action comparison that allocation
needs. Following the brief's rule, no latent effect blocks or more complex models were added.

### 4.3 Correction to the earlier report's post-hoc R²

The earlier report quoted "cross-orientation R² −0.03 to −0.05" (`../feedback_validation_20261003`,
section 4.3). That figure is the variance ratio 1 − var(e)/var(res), not squared-error R². The
squared-error R² is −0.097 / −0.143 / −0.080 (breast / colon / pancreas), and the skill against
no correction is −0.037 / −0.016 / −0.028 (`repeats/receipts/posthoc_r2_check.json`). The
conclusion, no transfer, is unchanged.

## 5. Phase 3: predictor and scheduler

### 5.1 Exploratory 2×2 on exposed data (`allocation/results/addendum_2x2.json`, post hoc)

- **Predictor S:** screen-label history mean.
- **Predictor R:** historical P(screen call AND verification call) from other lines' both
  orientations.
- **Scheduler V:** verify-hits with terminal round.
- **Scheduler I:** index scheduler, verifying in order of P(confirm | hit) per cost and screening
  in order of P(hit and confirm) per cost.

All four cells spend exactly 3,958 measurements in 5 rounds.

| | Scheduler V | Scheduler I |
|---|---:|---:|
| Predictor S | 252.5 | 250.5 |
| Predictor R | 269.0 | 268.0 |

| Contrast | Measurement budget | Wells budget |
|---|---|---|
| Predictor under V | +6.5% [2.6, 10.6] | +5.2% [1.3, 9.0] |
| Predictor under I | +7.0% [3.8, 10.4] | +7.1% [4.0, 10.5] |
| Scheduler under S | −0.8% [−4.0, +2.5] | −1.4% [−4.8, +2.0] |
| Scheduler under R | −0.4% [−0.95, 0.0] | +0.4% [−0.5, +1.3] |
| Interaction, per line | +0.008 [−0.060, +0.072] | +0.036 [−0.028, +0.104] |

- **The index scheduler never deferred anything.** In the measurement version it never left a
  pending hit unverified because a screen ranked higher. Verification nearly always beats screening
  per unit of cost, so the scheduler collapses to verify-hits.
- **R works by being more selective.** It buys fewer screen hits (585 against 632.5) that confirm
  more often (0.467 against 0.411).

### 5.2 Information or modelling? (`allocation/results/addendum_3_information.json`, post hoc)

| Ranking under scheduler V (same history data as R unless stated) | Confirmed |
|---|---:|
| S (screen-orientation history only) | 252.5 |
| S_both: mean of both orientations' labels | 263.5 |
| S_valid: verification-orientation label | 255.5 |
| S_vrate: verification-call rate | 253.5 |
| R: P(screen call AND verification call) | 269.0 |

| Contrast | Result |
|---|---|
| S_both − S | +4.4% [2.0, 6.8] |
| R − S_both | +2.1% [−1.6, +6.1] |

In a role-swap panel, another line's verification-orientation label is that line's screen label in
the other role assignment. So S_both partly averages two measurements of each pair, which reduces
noise. That is legitimate history, but it is not "reproducibility awareness".

### 5.3 Why the 2×2 is not frozen

The full reasoning is in `receipts/phase3_blocking.json` and `review/data_qualification.json`.

| Dataset | Verdict | Reason |
|---|---|---|
| Jaaks 2022 original screen | Exposed | Opened by the earlier study |
| Jaaks validation rescreen | Not qualified | Exposed, and its menu was selected from outcomes |
| GDSC portal anchored files | Not qualified | Same data as Jaaks |
| Nair et al. 2023 | Not qualified | Primary repeats are same-day technical duplicates. Independent validation covers 27 author-selected combinations × 15 lines, with a changed lab, assay, time and doses |
| GDSC matrix 007–010 | Not qualified | Only 4–7% of cells repeated, mostly consecutive barcodes; 25–28-pair menus; different assay |
| Sandpiper-01 | Not qualified | 2 pairs per line |
| BATCHIE | Not qualified | Adaptive menu covering 12.9% of the space |
| AstraZeneca–Sanger DREAM | Unverified | Needs an account |

**Sample size.** At the recommended τ = 5%, resolving the decision in both directions needs about
150–180 lines with two role assignments. The largest complete anchored screen, Jaaks, has 125, and
it is exposed.

`NEXT_PROTOCOL.json` is the executable protocol for the first qualified release:
- **Primary contrast:** (R+V) − (S+V), at fixed rounds, measurements and wells.
- **Secondary:** the scheduler contrasts, the interaction, the S_both information control, paired and
  fixed-split baselines, and time-matched comparisons at 2 and 3 rounds.
- **Feedback arm:** a λ-feedback arm (λ_U = 0.27, frozen now) only if the release has qualified
  same-condition repeats.
- **Runner:** dry runs pass on a synthetic release.

## 6. Statistical boundaries (`review/statistics.md`, `review/statistics.json`)

- **Units.** The unit is the cell line, stratified by tissue. Role assignments, plates, seeding
  events, seeds and repeated analyses are not independent units. Drug pairs recur across lines, so
  the line bootstrap supports only "new lines, this library"; the two-way bootstrap has 3.3× the
  variance.
- **Decisions.**
  - lower bound > τ: proceed;
  - upper bound < 0: harm;
  - lower bound ≤ 0 and 0 ≤ upper bound < τ: futile;
  - lower bound ≤ 0 and upper bound ≥ τ: unresolved, an abstention. A lower bound below τ never
    establishes futility.
- **Risk.** A certificate controls P(act and wrong), not P(wrong | act). The earlier receipts show
  how far apart these can be: marginal FDR 0.043, but FDP 0.77 among non-empty lists.
- **Waudby-Smith & Ramdas.** Optional stopping is allowed only on a population fixed in advance and
  audited in uniformly random order. Verify-hits audits in score order, so sequential certificates
  are not justified here. Any certificate decision starts at one fixed time.
- **Threshold.**
  - The historical 10% rested on fourfold latency against a one-round comparator. It is not
    inherited, because verify-hits is itself multistage.
  - τ = 5% is recommended at fixed rounds and wells. That is a judgement: it sits above accounting
    artefacts of about 1.5–5% and above the +2–3% screen gains that failed to transfer earlier.
  - Rounds are a priced resource. Verify-hits gains +17.1% going from 2 to 3 rounds.

## 7. Answers

### 7.1 Was budget matching achieved?

**For measurements and combination wells, yes. For plates, controls and rounds, no.**

- **Measurements.** Every arm spends exactly M orientation measurements per line (3,958 in total).
  Paired spends M − (M mod 2), and its 48 unavoidable units are reported. The original's 148
  avoidable units are eliminated by carry-over.
- **Wells.** In the wells version, every remainder is smaller than the cheapest still-available
  action.
- **Not matched:**
  - custom plates and their control wells, up to 2.2× apart;
  - native plates;
  - rounds, from 1 to 5.

These are reported per arm and branch, not matched. Prices, labour, culture capacity and days
beyond the measured 4-day assay are unknown and kept null.

**Scope:** Jaaks 2022, 125 lines, a 20% budget, 4 decision rounds plus a terminal round, both
plate models (the custom one is a hypothetical). Exploratory.

### 7.2 Was independent repeat provenance authenticated?

**No: CORROBORATED_NOT_AUTHENTICATED.**

- **What holds:** plate → seeding date and culture expansion comes from the authors' documented raw
  fields for 3,106/3,106 plates. The day-1 link exists for 2,999 plates.
- **What is unknown:** whether a seeding event is the paper's "biological replicate".
- **What the repeats are:** in 9 of the 14 lines they are re-seedings of one culture expansion, not
  independent stocks.

So the same-condition analyses are a plate- and seeding-level diagnostic with that independence
limitation.

### 7.3 Did feedback improve independent prediction and action comparisons?

**Prediction slightly; action comparisons, no.**

- **Prediction.** With the development-fitted λ_U of 0.26–0.30, squared error on the role-swapped
  measurement improves by −0.71 [−1.10, −0.34] out of 44.3, about 1.6%.
- **Ordering and top-k:** unchanged.
- **Same-condition repeats (14 lines):** ordering +0.0065 [0.0029, 0.0101], but squared error is not
  resolved, so the stop rule fired.
- **Verification choice:** "screen hits first" is better than the λ-shrunk prediction.
- **The registered full-weight feedback (λ = 1)** is clearly worse than the static prior.

**Scope:** frozen TransferWorld (`WorldConfig(context=False)`, shrink 2.0), the 20% purchased set
ranked by history mean, Jaaks 2022.

### 7.4 Did the model improve confirmed discovery yield?

**The static reproducibility-aware history model did; target-line feedback did not.**

- **Static history model.** R raised confirmed discoveries by +6.5% [2.6, 10.6] over S under
  verify-hits, and +5.2% [1.3, 9.0] under the wells budget.
  - Using both orientations of history accounts for +4.4% [2.0, 6.8].
  - Modelling confirmation itself adds +2.1% [−1.6, +6.1], unresolved.
- **Target-line feedback.**
  - Under the verify-hits scheduler it changes nothing: −1.4% [−4.6, +1.7].
  - In a 2-round test with the λ model it gave +3.05% [−0.93, +7.27].

**Scope:** post hoc and exploratory, on exposed Jaaks data. The planning effect for a future test is
about +5–7%, below what a 125-line study can separate from a 5% bar.

### 7.5 Did the scheduler add value beyond strong simple policies?

**No.**

- **The index scheduler adds nothing** beyond verify-hits with a terminal round (−0.8% [−4.0, +2.5]
  and −0.4% [−0.95, 0.0]); it never deferred a verification in the measurement version.
- **Verify-hits itself** beats full-budget paired measurement (+17.7% [13.1, 23.1]) and the
  development-selected fixed split (+9.1% [5.4, 13.5]) at equal measurements. It buys that with
  5 rounds against 1 and 2.
- **At 2 rounds** the fixed split is better (−9.1% [−14.3, −3.4] for verify-hits, post hoc).
- **The terminal round** adds +5.9% [3.8, 8.3].

**Scope:** custom per-pair purchasing (a hypothetical lab), Jaaks role-swapped verification.
Exploratory.

### 7.6 Did an LLM contribute independently?

**Not tested, by decision.** `review/llm_plan.json`: DO_NOT_RUN.

- The verify and stop decisions are low-dimensional, and the numbers they depend on are already in
  the state. The earlier gate showed deepseek-flash echoes displayed order and scores.
- On public data, knowledge cannot be separated from memorisation.
- There is no qualified dataset, and the scheduler-only ceiling is +9.6%.

No provider call was made; new spend is USD 0 of the USD 3 cap.

### 7.7 Continue, change, stop, or blocked?

**Continue:**
- verify-hits with a reserved terminal verification round as the default, when rounds are cheap;
  a development-selected fixed split when only 2 rounds are available;
- reproducibility-aware static history: rank by P(hit and confirm) from complete history panels,
  and always report the information-matched S_both control;
- physical accounting by branch, with plates and controls reported next to wells.

**Change:**
- declare the binding resource (measurements, wells, plates or rounds) and fix rounds across arms in
  any comparison;
- fit any feedback weight on development data. λ ≈ 0.3, not 1;
- describe the earlier post-hoc statistic as a variance ratio;
- describe the old +16% as not budget-matched. The repaired figure is +17.7%, but at 5 rounds
  against 1.

**Stop:**
- adding latent effect blocks or more complex feedback models (no action gain);
- the adaptive index scheduler (no gain over verify-hits);
- LLM selector or scheduler arms for this problem;
- treating seeding repeats from one culture expansion as independent biological experiments.

**Blocked:**
- the frozen 2×2: no qualified untouched release, and too few lines for τ = 5%;
- authentication of biological replicates: no published plate → replicate table, and 107 plates
  lack a day-1 plate;
- cross-lab data behind an account (DREAM);
- any physical experiment.

## 8. Novelty (`review/novelty.json`)

None of the methods is new.

- **Prior art already covers each component:**
  - screen/verify budget allocation: two-stage genotyping, 10.1002/gepi.10260 and 10.1038/ng1706;
    multi-stage virtual screening, 10.1016/j.patter.2023.100875; replicate-or-explore design,
    10.1080/00401706.2018.1469433; HTS confirmation, 10.1177/1087057107312628;
  - adaptive combination screening: BATCHIE 10.1038/s41467-024-55287-7 and RECOVER
    10.1016/j.crmeth.2023.100599;
  - reproducibility modelling: 10.1214/11-AOAS466 and 10.1093/bib/bbab251;
  - certificates: Waudby-Smith & Ramdas; Jin & Candès.
- **What a bounded search did not find:** an equal-budget, independently verified comparison of
  verification schedulers in combination screens. That is an empirical application, and it needs a
  qualified dataset.

## 9. Deviations and failures (details in each workstream's `receipts/deviations*.json`)

- **Usage-limit stop.** The subagents stopped at about 23:51 and resumed at 02:12. Nothing had been
  written before the stop.
- **Post hoc analyses.** The time-matched replay and allocation addenda 2 and 3 were defined after
  results had been seen. Each had its plan written before its own reading and is labelled post hoc.
- **Accidental data row.** The repeats workstream printed one data row of the fitted release,
  outcome columns included, while reading the header (D1). The release was already exposed.
- **Repeats deviations:**
  - D2: a figshare ID correction (19141922 is the validation raw data; the day-1 data is 19141919);
  - D4: an addendum time-zone bug, corrected in v2;
  - D6: one baseline-selection fit out of 70 in the sensitivity analyses included the held-out line's
    pooled call rate;
  - D11: the free-text independence label overstates the match to the paper's "biological
    replicate"; this report uses the corrected wording.
- **Allocation deviations:**
  - D1: the field planned as "QC-excluded plates" does not measure QC;
  - D7: native plates are charged at first touch;
  - other deviations are recorded in the receipt.
- **Review.** Its `written_at` fields first carried estimated times; they were corrected to file
  times and labelled. Nair's supplements were not downloaded, because no count in them could remove
  the disqualifying design facts.
- **Europe PMC timeout.** The first supplementary-files download timed out after 300 s; the second
  attempt succeeded.

## 10. Reproduce

```powershell
$env:PYTHONPATH = 'src;.'
$py = 'D:/anaconda/envs/maestro/python.exe'
$m = 'research.astra.reproducible_allocation_20261003'
& $py -m "$m.repeats.provenance"                 # refuses to overwrite; logs an access
& $py -m "$m.repeats.model_id" --workers 20
& $py -m "$m.repeats.posthoc_r2"
& $py -m "$m.allocation.replay"                  # --dry DIR for a synthetic release
& $py -m "$m.allocation.posthoc"
& $py -m "$m.allocation.addendum_2x2"
& $py -m "$m.allocation.addendum_3_information"
& $py -m pytest -o addopts= research/astra/reproducible_allocation_20261003
```

Environment, hashes, runtimes, downloads and tests are in [RUN_MANIFEST.json](RUN_MANIFEST.json).
