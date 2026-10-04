# Statistical validity memo: reproducible allocation study

> **File summary**
> - **Path**: `research/astra/reproducible_allocation_20261003/review/statistics.md`; the machine-readable version is `statistics.json`.
> - **Purpose**: the review workstream's statement of which inferences the study's planned analyses can support. It covers units, bootstrap, exposed data, multiplicity, development leakage, proceed/futility/abstain rules, marginal versus conditional risk, fixed-time versus sequential certificates, the minimum meaningful gain for a future frozen 2×2, and its sample size.
> - **Inputs**: derived results of `../feedback_validation_20261003` (exposed Jaaks 2022 data, EXPLORATORY), and primary sources read at theorem level: Waudby-Smith & Ramdas (arXiv 2006.04347 v4) and Jin & Candès (JMLR 24(244), 2023).
> - **Written**: 2026-10-04, after a `date` reading of 02:33:07 +0800 (file time of the first version 02:35), by review (subagent 3 of 3). No outcome of any unopened release was read, and no provider API was called.

## 0. Evidence status

- Jaaks 2022 has already been opened: six times by the earlier study and at least once by this study's parent smoke test. Every number in this study that derives from it is **EXPLORATORY**. That includes the variances used below for sample sizing, which come from the earlier study's written per-line results (`results/jaaks_primary/lines.jsonl`, `followup_verification.json`).
- These inputs can **size** a future study. They cannot **confirm** anything: the design choices they informed (verify-hits, the menu, the budget) were themselves made after looking at the same data.

## 1. Units and dependence

| Item | Status | Consequence |
|---|---|---|
| Cell line | Unit of inference, stratified by tissue (51 breast / 45 colon / 29 pancreas) | Every interval resamples lines |
| SV and VS role assignments | Not independent. The SV validation call is the VS screen call of the same line. Static line totals correlate at r = 0.97 between SV and VS | Average them within the line. Averaging cuts the SD of a paired policy difference from 0.46 to 0.35 (screen-only feedback − static), because the two assignments' *differences* correlate at only r = 0.19. Two assignments per line are worth about 1.7 lines |
| Drug pairs | Recur across lines; the line bootstrap treats the pair menu as fixed | Scope is "new lines, this library". The earlier two-way (line × pair) bootstrap had 3.3× the variance of the line bootstrap. Its pair component (SE about 2.1 percentage points on G) does **not** shrink as lines are added |
| Plates, seeding events, culture expansions, technical repeats | Nested within line × pair; not independent experiments | Plate counts never enter n |
| Random-arm seeds | Monte Carlo replicates | Average within line |
| History = other lines of the same tissue | Every target's campaign uses the other targets' data, so units share history | Mild positive dependence that the line bootstrap ignores. Report per tissue and a leave-one-tissue-out sensitivity |
| Tissue heterogeneity | Static\* validated discoveries per line: breast 1.19, colon 1.91, pancreas 4.52 | The ratio-of-sums G is about 47% pancreas. Report per-tissue values and the absolute per-line difference next to G |
| Zero inflation | 29% of lines have 0 static\* validated discoveries; 79% of paired differences are 0 | Distributions are skewed and discrete. The percentile bootstrap is adequate at 125 lines but undercovers at about 15 lines (the size of the Nair validation set) |

## 2. Bootstrap choices

- The stratified percentile line bootstrap for G (ratio of sums, 10,000 resamples) is acceptable for exploratory work at n ≥ about 40 lines. Below that, use a studentized or BCa interval, or report the per-line mean difference with a t-interval as a cross-check.
- **Re-selecting static\* in every resample** guards against choosing the comparator after seeing the data, but it biases the contrast toward zero. In a frozen 2×2, pick the strong baseline in development, register it, and report the max-over-baselines version only as a sensitivity.
- The two-way (pigeonhole) bootstrap is a conservative sensitivity analysis: it counts the line × pair interaction in both margins. That is a standard property, not re-derived here. Use it only when the claim covers new drug pairs.
- Resampling-based power with a Gaussian-noise model truncated at 0 (`power_check.json`) is **biased**. With 29% zero-baseline lines, truncation adds about +2.5 points of spurious gain. It is superseded by joint empirical resampling of (baseline, difference) per line (`power_check2.json`), which agrees with the normal approximation within Monte Carlo error.

## 3. Exposed data and development leakage

- Every parameter selected on Jaaks is **development**: the scalar correction λ, the fixed-split f, reserve sizes, scheduler thresholds, the 2×2 arms and τ. Evaluating them on Jaaks again is in-sample and optimistic: picking the best of K variants inflates the winner by E[max].
- Leakage at the study level is unavoidable. The whole design (verify-hits, role-swapped verification, the 20% budget) was chosen after Jaaks outcomes were seen. A Jaaks replay of "verify-hits versus paired" therefore re-tests a hypothesis generated on the same data.
- Leakage within an analysis must be blocked by construction:
  - no target-line hidden label reaches any purchase decision;
  - the SV validation (that is, the VS screen) of the target line is never history;
  - development selection is leave-one-tissue-out or uses separate lines.

  The allocation plan already does all three. Its tests must use synthetic data only.
- A hidden validation label cannot be used to adapt a model and also to evaluate it. When verification observations update the model, evaluate prequentially (predictions frozen before each reveal) or on a third, untouched measurement.

## 4. Multiplicity

- The allocation replay has 6 contrasts × 2 budget versions, plus per-tissue and time sensitivities. Its intervals are descriptive, with no adjustment and no verdict categories.
- For a future frozen 2×2:
  - Register **one** primary contrast: the combined arm (repeat-aware predictor + proposed scheduler) against the registered strong baseline.
  - The model main effect, the scheduler main effect and their interaction are secondary, with Holm adjustment.
  - If the model and scheduler contributions are both to be claimed, use simultaneous intervals. Bonferroni over 3 contrasts multiplies n by 1.33.
  - The interaction has about twice the variance of a main effect. Do not make "separate contributions" depend on an interaction test.
- Certificates across lines: a per-line guarantee is not simultaneous. Use α/L per line, or a pooled bound on a pooled, uniformly drawn audit. The earlier receipts show simultaneous coverage across 60 lines of 0.0 for per-line bounds, against 0.95 for Bonferroni.

## 5. Decision rules: proceed, futility, abstain

Let G be the relative gain in independently confirmed discoveries, with a two-sided 95% interval [L, U], and τ the minimum meaningful gain (section 8).

| Category | Condition | Action |
|---|---|---|
| MEANINGFUL | L > τ | Proceed with the component |
| POSITIVE_UNRESOLVED | 0 < L ≤ τ ≤ U | Real gain of unresolved size. Do not claim meaningful; more units are needed |
| SMALL | L > 0 and U < τ | Real but below the bar. Adopt only if it is free at equal rounds and wells; do not pursue complexity |
| FUTILE | L ≤ 0 and 0 ≤ U < τ | Stop pursuing the component; no meaningful gain |
| HARM | U < 0 | Stop |
| UNRESOLVED | L ≤ 0 and U ≥ τ | Abstain. This is **not** evidence of no effect |

A lower bound below τ never establishes futility. Futility needs an upper bound below τ.

## 6. Marginal versus conditional wrong-action risk

- Let a certificate give a lower bound B on yield Y with P(B > Y) ≤ δ, and let the rule act when B ≥ τ. Then
  - **P(act and Y < τ) ≤ δ**: the marginal wrong-action probability is controlled;
  - **P(Y < τ | act) ≤ δ / P(act)**: the risk conditional on acting is *not* controlled. It can be large when acting is rare.
- The earlier receipts show this concretely. In the confirmatory LLM-named arm, marginal FDR was 0.043 while FDP given a non-empty list was 0.77; only about 5.6% of lists were non-empty.
- To control conditional risk at γ, one of these is needed:
  - δ ≤ γ · p_min, with p_min a development lower bound on P(act), registered in advance;
  - a selective (conditional-on-selection) procedure;
  - a Bayesian posterior risk, which is labelled as such and carries no frequentist guarantee.
- Report both quantities, and state which one the decision controls.
- Every certificate controls the **declared measured label**: here, a synergy call in the verification orientation. It does not control biological reproducibility or efficacy.

## 7. Fixed-time versus sequential certificates (theorem-level check)

**Waudby-Smith & Ramdas, *Confidence sequences for sampling without replacement* (arXiv 2006.04347 v4; NeurIPS 2020).**

- Observation model (1.2): the population x₁..x_N is fixed and nonrandom. Each X_t is drawn uniformly from the items not yet observed. The order is the only source of randomness.
- Results used here:
  - Theorem 2.1 (binary, prior–posterior-ratio martingale with a beta-binomial working prior and the hypergeometric likelihood) and Theorem 3.1 (bounded values, a Hoeffding-type supermartingale with predictable λ) each give a (1−α) confidence sequence that is valid uniformly over t ∈ [N]. The running intersection is also valid.
  - By their equation (1.1), uniform validity is equivalent to validity at arbitrary stopping times. This is what licenses repeated looks and optional stopping.
- Conditions this study must meet to use them:
  1. The audited population (for example a shortlist remainder) is fixed before the first audited label.
  2. The audit order is uniformly random without replacement. **Verify-hits verifies in screen-label order, so it does not satisfy this.**
  3. Labels are fixed numbers per item: the measurement the audit would return. The sequence covers that measured-label total.
  4. Values are bounded; binary calls qualify.
- Not covered:
  - adaptive shortlist changes: the population changes, so a new sequence must start and α must be split across restarts (an α-spending sum or e-process merging, which this paper does not provide);
  - score-ordered audits;
  - simultaneous claims across lines, which need α/L, or one pooled sequence on a uniformly drawn pooled population.

**Jin & Candès, *Selection by prediction with conformal p-values* (JMLR 24(244):1–41, 2023).**

- Theorem 3: if the score V is monotone, calibration and test data are i.i.d., and the stated mutual-independence condition holds, then cfBH (conformal p-values + BH) has FDR ≤ q.
- Theorem 6 relaxes i.i.d. to exchangeability of {V₁..V_n, V_{n+j}} conditional on the other test scores. That covers calibration drawn without replacement from a fixed library.
- The prediction model must be trained independently of the calibration and test samples; the paper conditions on the training process.
- FDR is a marginal expectation over calibration and test draws, for a **one-shot** selection.
- Not covered:
  - calibration labels obtained by score-based verification: verify-hits labels exist only for screen hits, so they are not exchangeable with untested candidates;
  - repeated re-selection as calibration grows;
  - FDR conditional on a non-empty selection.
- ACS (Gui, Jin, Nair & Ren 2025, arXiv 2507.15825) permits some adaptivity under its information-control principle. That was checked at full-text level by the earlier WS4; it was not re-read here.

**Recommendation.** Use one fixed evaluation time: a terminal decision after the last screening round, with a fixed-time hypergeometric bound on a uniformly audited, pre-fixed population.

Do **not** implement sequential certificates now. They would be justified only if all of these hold:
- the protocol fixes the audited population before auditing;
- audits are drawn uniformly at random (a dedicated audit stream, separate from verify-hits);
- α is pre-allocated across any restarts.

The earlier empirical check found coverage as low as 0.83 under optional stopping with fixed-time bounds (WS3), which is why optional stopping must not be added informally.

## 8. Minimum meaningful gain for the frozen 2×2

**Why the historical 10% does not carry over.** It priced feedback's 4-fold elapsed time against a one-round static arm. The new comparator, static verify-hits, is multistage itself. It needs at least 2 rounds; it ran with 4, and with a 5th verification-first terminal round in the repaired replay.

**Incremental resources of the proposed arms over static verify-hits (measured or by design):**

| Resource | Predictor swap (model contribution) | Proposed scheduler (scheduler contribution) |
|---|---|---|
| Wells | 0 by design (equal budget; tolerance ≤ 0.5%) | 0 by design |
| Rounds / delay | 0: updates happen at existing round boundaries | 0 if it keeps the comparator's rounds. Each extra round is ≥ 4 days (24 h attachment + 72 h drug, protocol minimum) and is handled by time-matching, not priced into τ |
| Plates and controls | 0 | More, smaller rounds mean more partly filled custom plates at 200 control wells each. This is measurable and must be charged |
| Compute | Seconds per campaign (earlier Jaaks stage: 32.6 s for 14 arms × 250 records) | Seconds |
| Provider spend | 0 (no LLM arm, `llm_plan.json`) | 0 |
| Decision overhead | A development repeat dataset (one-off) plus software maintenance; price unknown (null) | Same |
| External requirement | None found: no published or regulatory threshold for gains from a screening policy | None found |

**Headroom at the Jaaks 20% budget (exploratory):**
- **+35.8%** is the ceiling over static verify-hits: all 324 validated pairs in the menus, against 238.5 confirmed.
- **+9.6%** is the scheduler-only ceiling with the same screened pairs (261.5 hidden-validated screen hits against 238.5 confirmed).
- **+16.8% [10.7, 23.4]** is the predictor ceiling on screen-only purchases (oracle against static\*).

**Recommendation: τ = 5% relative gain in independently confirmed discoveries.** At the verify-hits baseline of 1.91 per line, that is about 0.095 per line, or about 12 per 125 lines. It applies to both the model and the scheduler contribution, and only when the proposed arm spends equal wells (±0.5%) in no more rounds than the comparator.

What is measured:
- the proposed arms cost about zero additional wells, rounds and compute;
- the headroom is as above.

What is judgement:
- **Choosing a positive bar rather than "any gain with L > 0".** With zero physical increment, the bar exists to keep complexity (a repeat-aware model, a new scheduler) from being adopted for gains of the size that have **not** transferred in this repository. Screen-level gains of +2–3% (ALMANAC, Jaaks S1) and +9–15% (O'Neil) vanished on independent measurement, while the verify-hits allocation effect survived.
- **Placing it at 5%.** It sits above plausible residual accounting artefacts: the odd-budget pairing remainder is ≤ 1 unit of about 32, about 1.5% averaged over lines, and the old comparison's avoidable underuse was 4.95%. It is also about one-seventh of the attainable headroom and half the scheduler-only ceiling.
- **Rejecting 10%.** A 10% bar would make a pure scheduler contribution with unchanged screens nearly impossible by construction (ceiling 9.6%).

The historical 10% and pure superiority (τ = 0) are reported as sensitivities. The historical threshold and verdict stay unchanged.

## 9. Sample size (verify-hits scale, two-sided 95%, power 80% / 90%)

Inputs:
- The paired-difference SD per line is 0.411 with two role assignments averaged per line. It is back-calculated from the follow-up interval for feedback-verify-hits − static-verify-hits (half-width / 1.96 × √125), and agrees with verify-hits − paired (0.422).
- With one assignment per line the SD is 0.533, scaled by the observed single/averaged ratio of 1.30.
- Baseline mean: 1.908 confirmed per line.

| Claim | True G | n lines, 2 assignments/line (80% / 90%) | n lines, 1 assignment/line (80% / 90%) | Power at 125 lines (2 / 1) | Power at 81 lines (2 / 1) |
|---|---:|---:|---:|---:|---:|
| L > 0 | 5% | 146 / 195 | 245 / 328 | 0.74 / 0.52 | 0.55 / 0.36 |
| L > 0 | 10% | 37 / 49 | 62 / 82 | 1.00 / 0.98 | 0.99 / 0.90 |
| L > τ = 5% | 10% | 146 / 195 | 245 / 328 | 0.74 / 0.52 | 0.55 / 0.36 |
| L > τ = 5% | 15% | 37 / 49 | 62 / 82 | 1.00 / 0.98 | 0.99 / 0.90 |
| U < τ = 5% (futility) | 0% | 146 / 195 | 245 / 328 | 0.74 / 0.52 | 0.55 / 0.36 |
| U < 10% (futility) | 0% | 37 / 49 | 62 / 82 | 1.00 / 0.98 | 0.99 / 0.90 |

- **Check.** Joint empirical resampling of (static\*, other-arm) line pairs on the screen-only scale (`power_check2.json`, 400 × 400) agrees with the normal approximation. For example, L > 0 at G = 10% with 40 lines gives power 0.85–0.98 by resampling (three difference sources × two designs) against 0.87–0.98 predicted.
- **Multipliers:**
  - ×1.33 if three contrasts must hold simultaneously (Bonferroni);
  - ×3.3 in variance if the claim covers new drug pairs, and the pair component cannot be bought down with lines;
  - a larger n if the proposed scheduler changes many more decisions than feedback did. The observed SDs come from policies that differ on about 21% of lines; a random-ranking contrast has SD 1.94, an extreme upper bound.
  - Re-estimate the SD on the allocation workstream's repaired replay before freezing n.
- **Consequence.**
  - Resolving the 5% bar in both directions needs about **150 lines with two role assignments per line, or about 250 with one**. That is more than any single anchored screen: Jaaks has 125 lines, Nair 81, and Nair's validation 15.
  - A frozen 2×2 at Jaaks size should pre-register **UNRESOLVED as the likely outcome for true gains of 0–10%**, rather than raise τ to manufacture a decision.
  - A 60-line gate is arbitrary in both directions: too many for a 15% effect (37 lines), too few for the 5% bar.

## 10. What the planned analyses can and cannot support

- **Allocation replay (exploratory, exposed).** Can show:
  - whether the +16% verify-hits advantage survives budget conservation, the terminal round and physical charging;
  - the size of the accounting artefact.

  Cannot:
  - confirm the advantage;
  - choose the 2×2's strong baseline and then test it on the same data.

  At the native plate granularity, per-pair purchases are hypothetical (`challenges.json` C1).
- **Repeats: scalar correction λ (exploratory).** Can estimate whether λ = 0 is adequate on the 14 author-named repeat lines. Constraints:
  - With 14 units the percentile bootstrap undercovers; use a t-interval or a cluster-robust SE and report the line count.
  - λ estimated on same-condition repeats does not transfer to role-swapped verification. The estimands differ (`challenges.json` C4).
  - λ from the same pair's own residual is a reliability (regression-to-the-mean) coefficient. A cross-pair transfer λ is the feedback-generalization question. Keep the two separate (C6).
- **2×2.** Not executable as an untouched evaluation: no dataset qualifies (`data_qualification.json`). Freeze an executable protocol and a blocking receipt.

## Addendum 1 (2026-10-04, file time 02:41 +0800, after the parent forwarded the allocation replay)

The sections above are unchanged. `statistics_addendum_1.json` refines sections 8 and 9 using the repaired replay, which is EXPLORATORY.

- **Line-level SDs of paired contrasts.** These are back-calculated, with two role assignments averaged per line:
  - 0.24 to 0.48 for arms with the same number of rounds (C6 0.24, C4 0.35, C2 0.42, C1 and C3 0.48);
  - 0.67 to 0.72 for contrasts that change the number of rounds (T1, T3).

  The 0.411 used above lies inside the equal-round range.
- **Rounds carry a cost.** Verify-hits gains +17.1% going from 2 to 3 rounds and +2.4% going from 3 to 5. The fixed split reaches its result in 2 rounds, and paired in 1.
  - The 2×2 must therefore fix the number of rounds R for all four cells, and choose its strong simple baseline at that R: the fixed split at R = 2, verify-hits or conf_per_cost at R ≥ 3.
  - With R fixed, the incremental delay of the proposed arms is zero, and τ = 5% stands.
- **The binding resource must be declared.** Matching combination wells leaves custom plates unmatched by up to 2.2× (`challenges.json` A1).
- **Updated sample size.** With the strongest R = 5 baseline (2.0 to 2.1 confirmed per line) and an SD of 0.48, resolving τ = 5% in both directions at 80% power needs:
  - about 160 to 180 lines with two role assignments per line;
  - about 265 to 300 lines with one.

  A 10% effect against 0 needs about 40 to 45 lines (two assignments) or 66 to 75 (one).
- **Headroom at R = 5.** If every validated pair in the menus were confirmed, the gain would be +28.3% over verify-hits with a terminal round and +20.9% over conf_per_cost.
