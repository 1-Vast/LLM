> **File summary**
> - **Path**: `research/astra/mono_pretraining_20261005/decisions/DECISION_SPACE.md`
> - **Purpose**: define the candidate scientific decision tasks for the mono-pretraining study on qualified data only, quantify
>   free-versus-forced decisions and oracle headroom from existing aggregated receipts, and choose ONE primary task.
> - **Core points**: primary task = A (screen ordering of S x V pairs in a new line under the frozen two-round contract).
>   Headroom exists only in prediction (oracle +28.5% E / +21.9% HD over C_mean, in 30% of lines); every scheduling or
>   evidence-acquisition decision has an oracle bound below the registered 5% rule or has no measured data; mechanism
>   discrimination has no qualified data.
> - **Evidence status**: everything is EXPLORATORY (Jaaks 2022 exposed). No raw outcome column and no vault ticket was used in
>   this phase. Numbers are reproduced by `headroom_from_receipts.py` (same folder; reads scalar fields of the existing
>   campaign receipts) and quoted with the receipt they come from.
> - **Depends on**: `confirmation_campaign_20261004/{REPORT.md, design/results, resources/results, protocol/campaign_contract.json}`,
>   `knowledge_transfer_20261004/REPORT_ZH.md` (n4/n8 numbers), `knowledge_optimization_20261004/PRETRAINING_PROTOCOL.json`.

# Decision space of the mono-pretraining study

## 0. Facts every task shares (Jaaks 2022, frozen builder, contract v2)

| Quantity | E (61 lines) | HD (64 lines) | Source |
|---|---:|---:|---|
| Mean menu size (QC-conditioned S x V pairs per line) | 158.2 | 154.7 (min 32) | design campaign records |
| Cap M = ceil(menu/5) orientation measurements | 32.0 | 31.3 | same |
| Round-1 screens at fp 30 (n1 = floor(0.7 M)) | about 22 | about 21 | contract `P2_primary_fixed_split` |
| Confirmed discoveries per line, C_mean (P2, fp 30) | 1.93 (117.5 / 61) | 2.10 (134.5 / 64) | `eval_summary.json`, `dev_summary.json` |
| Oracle confirmed per line | 2.48 (151.0) | 2.56 (164.0) | same |
| Menu joint hits per line (mean / median) | 2.49 / 2 | 2.69 / 1 | campaign records (`menu_joint_hits`) |
| Lines with zero joint hits | 15 | 17 | same |

Role assignments SV and VS share the same joint-hit set (the VS screen call is the SV verification call), so they are one unit.
Pairs recur across lines: the two-way (line x pair) bootstrap interval of the primary was 2.24 times wider than the
line bootstrap (width 33.6 vs 15.0 percentage points, `eval_summary.json`; the earlier study measured a variance ratio of 3.34,
`reproducible_allocation_20261003/review/statistics.md`).

## 1. Candidate tasks

### Task A - intervention selection: ranking S x V pairs to screen in a new line (PRIMARY)

| Field | Definition |
|---|---|
| Action menu | Per target line t and role r in {SV, VS}: the registered menu (about 158 pairs, builder order). Decision variable under study: **the round-1 screen order only** (which n1 of about 158 pairs to buy). Verification order, fp = 30, two rounds, stop-at-cap are held at the strong-simple choice for every arm (as in `PRETRAINING_PROTOCOL.json`, `first_stage_changes`). |
| Outcome and utility | u = measured confirmed discoveries: pairs whose screen call and other-orientation call are both revealed by purchases before the deadline and both synergistic (authors' rule). Line value = mean over the two roles. No utility for unverified screens or predictions. |
| Independent unit | Target cell line (125; 64 development, 61 evaluation, stratified by tissue). Roles, plates, seeding events, history seeds, model seeds are nested, not independent. Pairs recur: broader-than-library claims need the two-way sensitivity. |
| Information before the decision | History lines of the same tissue (both orientations; n4 / n8 / all), public GDSC2 mono labels of non-Jaaks lines, static line covariates (14 PROGENy scores). Never the target line's unpurchased outcomes, never its other role, never E lines as history. |
| Costs | One purchase = one orientation measurement (cap M). Reported, not matched: plate starts, wells, controls, days (4 per round). Compute and API disclosed (see `AGENT_ROLE.md`). Prices and labour stay null. |
| Failure handling | The release is QC-prefiltered: 0 measurement failures in 296,707 rows (`feedback_validation REPORT 4.2`). The failure path of the production framework is therefore **unexercisable** here; say so rather than claim robustness. Model failure (NaN, unmapped drug, refusal) falls back to the strong-simple score for the affected pairs and is counted. |
| Abstention consequence | An abstaining pair/line inherits the comparator ranking, so its contribution to the contrast is exactly 0. The abstention rate is reported with the coverage-conditional gain; the covered-subgroup win is descriptive, never a replacement primary. |
| Minimum meaningful improvement | tau = 5% relative confirmed yield (inherited, `campaign_contract.json: worthwhile_gain`): 0.096-0.105 confirmed per line, 5.4-5.9 confirmations across 61 lines. |
| Continue / revise / stop | Use the registered verdict function (`decision_rules_primary`) on the nested-development contrast: L > tau or 0 < L <= tau <= U continue to a frozen exposed-transport read; L <= 0 <= U < tau stop; L <= 0 and U >= tau revise only by the one development repair the protocol allows. Details in `EVALUATION_DESIGN.md`. |

**Quantified headroom (E / HD, P2, fp 30, line = unit).**

| Quantity | E | HD |
|---|---:|---:|
| Oracle / C_mean | 151.0 / 117.5 = +28.5% | 164.0 / 134.5 = +21.9% |
| C_mean yield as a share of the oracle yield | 77.8% | 82.0% |
| Gap closure needed for tau = 5% | 17.5% | 22.8% |
| Lines with any headroom over C_mean | 19 (31%) | 19 (30%) |
| Lines already at the oracle ceiling (with hits) | 27 (44%) | 28 (44%) |
| Lines with zero joint hits (no policy can win) | 15 (25%) | 17 (27%) |
| Gap concentration: top 5 / top 10 lines | 45% / 73% | 54% / 73% |

So a ranking change can move the yield in at most about 30% of the lines, and about half of the total gap sits in 5 lines. The
per-line difference between two rankings is zero in most lines (R vs C_mean: better 6, worse 10, tied 45 of 61 in E, i.e. 74%;
3 / 14 / 47 of 64 in HD, i.e. 73%; S_both vs C_mean in E: 4 / 5 / 52; C_prod vs C_mean: 1 / 2 / 58). Differences between near-identical rankings
are therefore nearly uninformative, and the effective sample is the 19 headroom lines per half.

**Regime dependence.** At full history the strong simple ranking is already at 78-82% of the oracle. In the sparse regime the
mono-pretraining question targets (n4, `knowledge_transfer_20261004/REPORT_ZH.md` section 4) the HD-selected strong simple
(S_both) confirms 107.67 in E, against 117.5 at full history and an oracle of 151: the oracle gap is +40%, the n4-to-full-history
gap is only +9.1%, and tau = 5% (5.4 confirmations) needs the new model to recover **55% of the whole gap between 4 and 64 history
lines** (or 12.4% of the gap to the oracle). History-draw noise is of the same size as tau: the three n4 history seeds gave
S_both 102.5 / 111 / 109.5 (SD 4.5, i.e. 4.2%) and the n8 strong baseline (102.67) is below the n4 one, so the baseline itself is
a noisy target.

**Where prediction binds (and what has been tried).** Prediction is the only channel with headroom. The measured record of
prediction attempts on this task is negative or null: R (shrunk joint rate) -5.96% [-13.36, +1.67] vs C_mean (E, full history);
static network transfer at n4 -8.67% [-14.93, -2.39], TF background similarity -1.86% [-4.21, +0.16], network x background 0.0
(zero weight selected) (`REPORT_ZH.md` section 4); feedback-learned drug-in-line effects fail to transfer across orientations
(cross-orientation r 0.16-0.36, R^2 < 0; `feedback_validation REPORT 4.3`). The only positive signal is information, not
modelling: continuous history at n4 (S_both vs C_mean +10.2% [+3.9, +17.8], two-way [-3.0, +27.7]) and two-orientation history
(+13.4% [8.4, 18.8]). A mono-pretraining gain therefore has to beat a baseline that is already the best of six rankings
re-selected for the sparse regime.

### Task B - evidence acquisition under a fixed total budget

What actually exists as **measured** data in Jaaks, and how often a genuine choice arises (E campaigns unless noted; `resources/results/*/headroom.json`,
`summary.json`):

| Candidate action | Exists as measured, priced data? | Frequency of genuine choice | Oracle bound | Verdict |
|---|---|---|---:|---|
| screen(i) vs not (round-1 ordering) | Yes: every menu pair has both orientations | 122/122 campaigns choose about 22 of 158 | +28.5% (Task A) | prediction problem, Task A |
| verify(i) of a round-1 hit | Yes (other orientation, disjoint plates) | **Forced** unless hits exceed capacity M - n1: binding in 6/122 (4.9%) for C_mean (E), 4/128 (3.1%) HD, 2/122 for R | perfect verify order +1.7% (E), +0.7% (HD) | no headroom |
| stop (leave cap unspent) | Yes (cap is a cap) | Cap partly unused in 113/122 (93%) of C_mean campaigns, with **no** yield effect because a last-round screen cannot be verified before the deadline | 0% yield; saves 20% of measurements, 31% of custom plate starts | forced, not a decision |
| fp split (screen share) per campaign | Parameter of the contract | Hindsight-best fp per campaign vs fixed fp 30 | +3.8% (E, C_mean); +3.4% S_both; +3.2% R; HD +3.7% / +2.2% / +4.4% | below 5% |
| round-2 screens with pending hits (P3, 3 rounds) | Yes | Real in 122/122 campaigns (110 with both pending hits and unscreened candidates); screen-vs-verify index crossing in 19/122 (15.6%) | oracle round-2 screens: E +13.7% (C_mean), +14.6-16.7% others; HD +10.9% (C_mean), +12.5% (S_both), +18.8% (R, the registered gate) | prediction headroom; realised feedback gain +1.7% [-1.4, +5.3] (post hoc), registered verdict NO_RELATIVE_FEEDBACK_VALUE |
| buy target-line mono panel | **No priced action.** Single agents are co-produced on the same Jaaks plates; GDSC2 mono for the 125 lines exists but as retrospective public data (excluded from pretraining by design) | none | not definable | only a fixed information ablation (see below) |
| replicate / repeat measurement | Only 14 repeat lines (8 E, 6 HD) | rare | - | unit count too small |
| native plate-set choice (2-7 screen and 2-7 verify components per line and role) | Yes (whole plate sets, co-produced outputs credited) | 100% of campaigns, but only about 2-7 coarse actions | oracle N2 at 20% cap: 59.0 vs C_mean 30.0 | not powered: 0.49 confirmed per line, 95% half-width of R - C_mean +-24% at 20% cap, +-13% at 30%, +-11% at 50% (280-1450 lines to rule out tau at only 50% power) |
| cross-line budget allocation (which new lines get budget) | Yes in replay: every line has a fully measured menu, so any allocation is replayable without imputation | open-ended | barren-line foresight bound **+7.2% (E), +6.2% (HD)** (25-27% of lines have zero joint hits; chord of the C_mean cap curve at the equivalent cap 26.5-27.2%) | exceeds 5% only under perfect foresight of barren lines; sequential detection from about 16 purchased screens (about 1 hit) is not credible. Optional exploratory secondary (see below) |

**Target-line mono as information, not as an agent decision.** GDSC2 contains fitted mono responses for all 125 Jaaks SIDMs
(63 of the 65 imported drugs have a GDSC2 DRUG_ID; `PRETRAINING_PROTOCOL.json` census), but the protocol deliberately excludes them to keep "new
cell background" honest. A variant that feeds the target line's own GDSC2 mono profile is a different estimand (a cell background
with a cheap measured profile). It can be reported as a fixed information ablation with cost null; it is not a priced choice in the
data, so no decision frequency or saving can be claimed.

**Line-level propensity (level, not order).** Line joint-hit counts are strongly overdispersed within tissue (variance/mean 2.3
Breast, 2.9 Colon, 3.0 Pancreas; Poisson dispersion test p < 1e-6 in each tissue; top 20% of lines hold 58% of hits; 26% of lines are
barren). Menu composition varies by line, so this overstates a pure line effect. A mono-pretrained model may predict line level
better than within-line order (within-line order is where the existing evidence is null and the within-line signal is
orientation-specific). The decision it would support is the cross-line allocation row above, with a perfect-foresight ceiling of about
6-7%. Record the model's line-mean predicted hit probability for every line as a free secondary diagnostic (Spearman with the
measured joint-hit count within tissue); do not make it primary.

### Task C - mechanism discrimination

No qualified data. Jaaks provides synergy calls on single drug pairs; it contains no outcome that discriminates between competing
mechanistic hypotheses, no hypothesis-conditional readout and no pre-registered mechanism label. GDSC2 mono labels carry no
mechanism contrast either. The production framework's core selector (`discrimination`, `expected_coverage`) cannot be exercised
here. Any "mechanism" statement made from this study would be an annotation exercise, not a decision with an outcome. Verdict: no
decision task C; do not describe results as mechanism discrimination.

## 2. Primary task and honest role of an agent

**Primary: Task A, nested development on HD, then fixed-config exposed transport to E, regime n4 (n8 and all as transport checks).**
Reasons: (i) it is the only decision with oracle headroom above 5% (28.5% / 21.9%); (ii) it is a pure prediction question, which is
what mono-pretraining changes; (iii) outcomes are measured for every candidate, so no counterfactual is manufactured; (iv) it
reuses the frozen contract, engine and baselines, and the baselines reproduce receipts (E 117.5, HD 134.5, n4 107.67 vs 97.67).

**What an agent can and cannot do.**

| Decision | Free? | Oracle bound | Realised evidence | Agent value |
|---|---|---:|---|---|
| Round-1 ordering | Free | +28.5% / +21.9% | prediction attempts null or negative | Prediction, not agent |
| Verification order / stop | Forced in 93-97% | 0.7-1.7%; 0% | - | none |
| fp per campaign | Parameter | 3.2-3.8% hindsight | - | below 5% |
| Per-line best-of-two ranking (hindsight, R vs C_mean) | - | +5.1% E, +2.2% HD | not realisable: about 1 round-1 hit per line to judge reliability | none credible |
| Round-2 screening feedback (P3) | Free | +10.9-18.8% (oracle, by predictor and half) | feedback AUC +0.01, yield +1.7% [-1.4, +5.3] | prediction/feedback, not scheduling |
| Cross-line allocation | Free in replay | +6.2-7.2% (perfect foresight) | no test | exploratory, optional |

The registered scheduler/agent indication rule (choice frequency >= 10% AND oracle bound >= 5%) is not met by any same-information
predictor at fp 30 (R 1.6% / 3.2%, C_mean 15.6% / 3.8%, S_both 10.7% / 3.4%, `resources/results/summary_20261004_130800/summary.json`).
This study should therefore **not** claim an agent contribution; it can only use a deterministic gating/abstention rule as the
smallest agent-like arm (`AGENT_ROLE.md`).

## 3. Continue / revise / stop for the study as a whole

- **Gate 0 (before any mono label is read, development only):** (a) coverage: fraction of E and HD menu pairs with both drugs mapped
  and unmapped lines (S0, agent B); coverage below 50% of the menu caps any possible gain at coverage x headroom; (b) history-draw
  noise: SD of the strong-simple yield across >= 10 independent n4 history draws (HD only); if SD >= tau the primary must average
  >= 10 draws; (c) baseline reproduction: 117.5 / 134.5 (full history), 107.67 / 97.67 (n4) within +-0.5. Failure of (c) stops the study.
- **Stop** (registered, per contract): U < tau with L <= 0 on the nested contrast against strong simple, or the pretrained arm
  not above the scratch arm with both intervals' lower bound > 0. State what the stop covers: this library, this history regime,
  this selected comparator.
- **Revise** (one repair only): a development-only repair of target alignment (for example the LN_IC50 transform or the scale of the
  drug bias) in a new frozen version; the original failure stays on record. No new model family.
- **Continue** (to a frozen exposed-transport read, never to a confirmatory claim): the requirements of
  `PRETRAINING_PROTOCOL.json: continue_gate`, with the amendments of `EVALUATION_DESIGN.md` and `VERIFICATION_PLAN.md`.
- A confirmatory claim needs an untouched, qualified source. The only candidate on record (Vis 2024) has a 19-pair menu and a cap of 4
  per line and stays sealed; nothing here changes that.
