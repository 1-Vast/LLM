> **File summary**
> - **Path**: `research/astra/mono_pretraining_20261005/decisions/EVALUATION_DESIGN.md`
> - **Purpose**: nested, line-grouped evaluation design for the exploratory development of mono-pretrained ranking on exposed Jaaks
>   data: units, dependence, generalisation axes, primary comparison, minimum meaningful improvement (tau = 5%), power computed from
>   existing per-line variance receipts, continuation rules and what each outcome would and would not support.
> - **Core points**: unit = target cell line; the 125 exposed lines cannot formally rule out tau under pair dependence (need about
>   760-1230 lines at the observed contrast variability) and only barely under line-only dependence (about 150-250 lines); the
>   realistic outcomes are UNRESOLVED or WORTHWHILE_EXCLUDED unless the true gain is above about 10%. History-draw noise (about 4%)
>   must be modelled as its own random effect. New cell backgrounds is the only generalisation axis the design supports.
> - **Evidence status**: EXPLORATORY; E61 is exposed and read once after configuration freeze.

# Evaluation design

## 1. Estimand and unit

Estimand: for **new cell lines of the same three tissues** (breast, colon, pancreas), drawn from the Jaaks library, with **a random
n4 history of same-tissue lines**, does mono-pretrained ranking of the registered S x V menu give more measured confirmed discoveries
under the frozen P2 contract (fp 30, cap M, two rounds) than the nested-selected strong simple ranking and than the same model trained
from scratch?

Unit: the target cell line. Each line value is the mean over the two role assignments, then over history draws and model seeds
(neither adds units). Scope statement attached to every verdict: *this drug library, this assay, this lab, these three tissues, this
history regime and this selected comparator*.

## 2. Nested grouped design

| Layer | Rule |
|---|---|
| Mono pretraining | One GDSC2 fit per frozen configuration on non-Jaaks cell entities (S0 contract of agent B); step count and scale chosen on a mono-validation split of non-Jaaks cells; **no Jaaks combination label touches this layer**, so one pretraining serves all outer folds. The permuted controls use >= 20 independent permutation draws, not one. |
| Outer folds | The 64 HD lines in 5 tissue-stratified, line-grouped folds (both roles, every plate, every seeding event and repeat-line replicate of a line stay together), fixed seed, fold file hashed before any outcome is read. Evaluation unit = each HD line once, as an outer-test line. |
| History draws | Per outer fold, tissue and draw d: 4 lines sampled from the outer-training lines of that tissue (n4 primary; n8 and all as non-tuned transport). **>= 10 independent draws** per fold (the knowledge-transfer study used 3, seeds 11/23/47, which also seeded training). History-draw seeds and model-initialisation seeds are crossed and logged separately. |
| Combo training | Pretrained, scratch and permuted arms train on **exactly the same rows as the simple arms see** (the n4 histories). If the learned arms were allowed the whole outer-training set (about 51 lines) while simple arms see 4, the comparison is confounded; `PRETRAINING_PROTOCOL.json` is ambiguous on this and must be fixed in writing before freeze. |
| Inner selection | Inside each outer-training set only: strong-simple choice (six rankings plus D_add and M_pot), lambda, step count, inner-fold histories drawn from inner-training lines. Nothing selected on outer-test lines or E. |
| E61 | Read once, after the development configuration and code hashes are frozen, with histories drawn from HD lines only (E never serves as history). Labelled exposed exploratory transport; never tuned. |

Known limit that nesting does not remove: the n4 regime and the strong-simple baseline were framed after the E n4 numbers
(S_both 107.67 vs C_mean 97.67) were seen, and Jaaks has been opened by earlier studies. Nested folds reduce in-study tuning bias
only.

## 3. Dependence and resampling

| Source of dependence | Treatment |
|---|---|
| Role assignments SV and VS | One unit (identical joint-hit set); averaged. |
| Plates, seeding events, repeat lines (14: 8 E, 6 HD) | Nested inside the line; same-condition repeatability is descriptive only. |
| History draws | A separate random effect. Report the between-draw SD of the paired line-level difference; two-level bootstrap (draw, then line) as a sensitivity. Evidence of its size: n4 S_both seeds 102.5 / 111 / 109.5 (SD 4.5 = 4.2%), n8 strong baseline below the n4 one. |
| Model seeds | Averaged within line; "at least 2 of 3 seeds positive" carries almost no information (seeds are not independent units) and should be replaced by the across-draw sign proportion plus the interval. |
| Pairs recurring across lines | Registered line bootstrap (tissue-stratified, 10,000 resamples, contract seed) for the library scope **and** a line x pair two-way bootstrap (contract seed 20261005). Observed inflation of the interval width: 2.24 (R - C_mean, E) and, in the earlier allocation study, a variance ratio 3.34 (SE ratio 1.83). Under the two-way interval the R - C_mean verdict would be UNRESOLVED. Treat the two-way interval as co-primary for any claim wider than "this library". |
| Heavy ties and concentration | 74% of line differences are exactly 0 and the top 5 lines carry 45-54% of the oracle gap. Report a sign-flip permutation test on non-zero differences, leave-5-lines-out, and per-tissue contrasts (descriptive; Pancreas has 15 HD lines). |
| Shared histories across targets | Targets of one tissue in one fold share the history draw; the bootstrap over lines does not account for that, so the history-draw random effect above is needed. |

## 4. Generalisation axes: what the design supports

| Axis | Supported? | Why / what it would need |
|---|---|---|
| **New cell backgrounds** (held-out lines, same library) | **Yes, primary.** | The grouped folds and E. 125 lines available. |
| New runs / plates / seeding events | No | Plates are nested in lines; 14 repeat lines give descriptive same-condition checks only. |
| New drug pairs | No | Every menu pair recurs in many lines; held-out pairs need a whole-pair-across-lines split and change the comparator history. The two-way interval is only a sensitivity, not a pair-holdout. |
| New drugs | Not in the primary. **The only axis where mono labels have a structural edge** (a held-out drug has no combo history but has GDSC2 mono labels). A separate frozen protocol: leave-drug-out folds (about 25-54 drugs per tissue), strong comparator M_pot, units = drugs and lines jointly, very few independent drug units. | Do not fold into the primary. |
| New tissues | Descriptive only | 3 tissues; leave-one-tissue-out has 3 groups. |
| New labs / screens | No | Vis 2024 stays sealed (19-pair menu, cap 4 per line). GDSC2 and Jaaks come from the same institution and fitting pipeline, so success could be within-lab transfer only. |

## 5. Primary comparison and endpoints

- **Primary**: W_pre - S1, relative gain of confirmed yield on the 64 HD outer-test lines, regime n4, P2 fp 30, with the registered
  verdict function and tau = 5% (`campaign_contract.json: decision_rules_primary`, prefix EXPLORATORY_).
- **Co-primary attribution**: W_pre - W_scratch (same architecture, inputs, rows, steps, seeds).
- **Required for any continue**: both intervals above 0, W_pre above the 95th percentile of the >= 20-draw permutation
  distributions (drug and cell), no leakage or budget invariant failing, no extra first-round screens or changed endpoint.
- **Secondary (no verdict)**: E61 transport; n8 and all; pooled 125 lines (descriptive, E after freeze); actions changed and
  correct/wrong changes; call Brier / log loss over the menu; within-line AUC; mono held-cell error; coverage-conditional gain;
  line-level predicted propensity vs measured joint hits within tissue; native plate and wells accounting.
- **Minimum meaningful improvement**: tau = 5% of the comparator yield (0.10 confirmed per line; 5.4 confirmations across 61 lines
  at the n4 baseline), inherited, not re-tuned.

## 6. Power from existing per-line variance receipts

Per-line contrast variability (SD of the line-level difference divided by the comparator mean; `headroom_from_receipts.json`,
`design/results/dev_*/dev_summary.json`, `REPORT_ZH.md` intervals converted with SE = half-width / 1.96):

| Contrast (source) | SD_rel |
|---|---:|
| R - C_mean, full history, HD (registered influence SD) | 0.219 |
| R - C_mean, full history, E (from the bootstrap interval) | about 0.30 |
| S_both - S, E / HD (naive) | 0.22 / 0.20 |
| C_mean - C_s, E (naive) | 0.18 |
| S_both - C_mean, n4, E | about 0.28 |
| static network - strong simple, n4, E | about 0.25 |
| TF similarity - strong simple, n4, E | about 0.09 |

Two-sided 95% half-width (HW), minimum detectable effect with 80% power for L > 0 (MDE), true effect needed for P(L > tau) = 0.8
(DEMO), and P(U < tau) when the true effect is 0:

| SD_rel | n lines | scope | HW | MDE | DEMO | P(U < tau given 0) |
|---:|---:|---|---:|---:|---:|---:|
| 0.09 | 64 | line | 2.2% | 3.1% | 8.2% | 0.99 |
| 0.09 | 125 | line | 1.6% | 2.3% | 7.3% | 1.00 |
| 0.09 | 125 | two-way (x2.24) | 3.5% | 5.0% | 10.0% | 0.79 |
| 0.15 | 64 | line | 3.7% | 5.2% | 10.2% | 0.76 |
| 0.15 | 125 | line | 2.6% | 3.8% | 8.8% | 0.96 |
| 0.15 | 125 | two-way | 5.9% | 8.4% | 13.4% | 0.38 |
| 0.22 | 64 | line | 5.4% | 7.7% | 12.7% | 0.44 |
| 0.22 | 125 | line | 3.9% | 5.5% | 10.5% | 0.72 |
| 0.22 | 125 | two-way | 8.6% | 12.3% | 17.3% | 0.20 |
| 0.28 | 64 | line | 6.9% | 9.8% | 14.8% | 0.30 |
| 0.28 | 125 | line | 4.9% | 7.0% | 12.0% | 0.51 |
| 0.28 | 125 | two-way | 11.0% | 15.7% | 20.7% | 0.14 |

Lines needed to rule out tau (U < tau) when the true effect is 0:

| SD_rel | 50% power | 80% power | 80% power, two-way |
|---:|---:|---:|---:|
| 0.09 | 12 | 25 | 127 |
| 0.15 | 35 | 71 | 354 |
| 0.22 | 74 | 152 | 762 |
| 0.28 | 120 | 246 | 1,234 |

(The registered design table, SD_rel 0.2188, gives 250 lines for 0.95 power and matches these formulas.)

**Consequences.**

1. The development set (64 lines) can detect a gain only above about 8-10% (line scope) and cannot demonstrate tau unless the true
   gain is about 13-15%. The same holds for E (61 lines). Pooling to 125 lines lowers MDE to about 5.5-7.0% but E is exposed
   and used only after freeze; the pooled number is descriptive.
2. Jaaks has 125 lines in total: a formal rule-out of tau is feasible only for contrasts with SD_rel <= about 0.15 in the line scope
   (blends with small lambda), and for none in the two-way scope. For a full-sized contrast (SD_rel 0.22-0.28) the most probable
   outcomes are UNRESOLVED (L <= 0, U >= tau) or EXPLORATORY_WORTHWHILE_EXCLUDED when the point estimate is near or below 0.
3. A contrast against **scratch** has a smaller SD_rel (same architecture; expect 0.09-0.15) so it is better powered, but its true
   effect is also likely smaller than 5%; a precisely estimated 1-3% gain gives "small benefit", not a continue.
4. The history-draw component is not in these numbers. With >= 10 draws per fold its contribution to the SE is about
   4.2% / sqrt(10) = 1.3% per baseline yield, smaller for a paired difference, and it should be estimated on HD (Gate 0 in
   `DECISION_SPACE.md`).
5. Prior probability: every earlier prediction attempt on this task is at or below the strong simple baseline
   (-5.96% [-13.4, +1.7], -8.67%, -1.86%, 0.0%); information gains (+10 to +13%) came from data, not modelling. Plan for a null.

## 7. Continuation, revision and stopping rules (before any outcome)

| Outcome on HD outer folds (n4) | Action |
|---|---|
| W_pre - S1: U < 0 | EXPLORATORY_HARM, stop. |
| 0 <= U < tau and L <= 0 | WORTHWHILE_EXCLUDED, stop (state the scope). |
| L > 0 and U < tau | small benefit: report as a free development default; stop pursuing confirmation. |
| 0 < L <= tau <= U, or L > tau, **and** W_pre - W_scratch lower bound > 0, **and** permutation test passes | continue: freeze the E transport read; E never changes the decision rule. |
| L <= 0 and U >= tau | UNRESOLVED: no claim. One development-only repair allowed (target alignment); otherwise stop. Estimate the lines a clean test would need (table above) before spending any sealed or new data. |
| Gate 0 fails (baseline not reproduced, coverage below 50%, or history-draw SD >= tau without averaging) | do not run the pretrained arms. |
| Any leakage/budget/poisoning invariant fails | invalidate the run, keep the failure on record. |

## 8. What each outcome would and would not support

| Outcome | Supports | Does not support |
|---|---|---|
| Continue (W_pre better than S1 and scratch, permutations worse) | Within-lab, within-library evidence that GDSC2 mono labels transfer to new cell backgrounds in a sparse-history regime, exploratory, adaptive | Biological mechanism, new drugs or pairs, other labs, dense history (full-history baselines are already at 78-82% of oracle), a physical saving, confirmation |
| W_pre better than S1 but not than scratch | The learner (continuous heads, drug-additive structure) helps; mono adds nothing | Value of pretraining; a mono-based claim |
| W_pre better than scratch but not S1 | Mono helps a model that is itself worse than a simple ranking | A decision-relevant gain |
| W_pre better than S1 only on covered pairs | Descriptive, coverage-conditional | A replacement primary |
| WORTHWHILE_EXCLUDED | No 5% gain over the strong simple ranking for this library and regime; STOP | That mono data are useless in general |
| UNRESOLVED | Nothing (the design is underpowered for the observed variability) | Any directional statement |
| Agent arms (A0, A1) equal to W_pre / S1 | No decision-policy headroom beyond deterministic fallback on this task | A statement about agents on other tasks |
