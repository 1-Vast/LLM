# Minimal two-history × two-randomized-action action-contrast design

Date: 2026-10-31 (Asia/Shanghai). This is a design and identifiability audit only. No numerical fitting, protected outcome opening, or change to `src/`/`tools/` was performed.

## Question and claim boundary

The smallest useful question is:

> After two defined prior-treatment histories, does a small early functional panel preserve the later choice between two supported actions, on an explicitly defined outcome scale, in independently prepared cultures?

Let H ∈ {H0,H1} be the prior history, A ∈ {A0,A1} the randomized next action, S the pre-action panel measured on diagnostic sister cultures, and Y the later growth-corrected viability endpoint. Define

`τ(h,s) = E[Y(A1) − Y(A0) | H=h,S=s]` and `Δ(s) = τ(H1,s) − τ(H0,s)`.

The minimum claim is conditional action-contrast invariance, Δ(s) ≈ 0, on a declared common-support region. This can preserve a two-action choice while both histories shift absolute viability. It does not establish a universal cell state, mechanism, total effect of the prior treatment, safety equivalence, or transport to an unsupported action or unseen history.

The two-history design can test the contrast difference between these two histories and a held preparation block. It cannot establish generalization to arbitrary histories. A third history is a separate extension, not silently inferred from this experiment.

## Easy, auditable input and fixed assay contract

Use one authenticated parental cell model with a routine bulk plate/flow assay. The input is intentionally small:

- cell count and confluence at the history start and action start;
- growth-rate estimate from a matched untreated sister (or two time points);
- four pre-action functional measurements on destructive diagnostic sisters: ATP/metabolic viability, caspase-3/7 activity, membrane permeability/death, and mitochondrial-potential or cell-cycle stress readout. The exact four assays must be frozen before the final blocks and run identically in both histories;
- history identity, action identity, physical dose, exposure duration, washout duration, plate and preparation-block identifiers.

No single-cell, spatial assay, transcriptome, large model, or learned probe selection is required. A cheaper two- or three-probe panel is acceptable only if selected before holdout and costed as a real assay reduction.

The primary endpoint is growth-rate-corrected viable-cell fraction at a fixed post-action time, with a predeclared death endpoint as a secondary check when the action is cytotoxic. Do not mix ATP, cell count, and death as if they were the same outcome. The action contrast is on the one primary scale; absolute viability and any toxicity threshold remain separate decision constraints.

## Histories, dose, time, and carryover

Choose H0 as vehicle and H1 as one sublethal, reversible prior exposure. Choose the history compound and dose from a separate dose-finding run, never from the final blocks: 24 h at approximately 0.5× an independently estimated IC20, followed by 24 h washout. The final protocol must record the actual concentration, lot, temperature, seeding density, and elapsed time.

Choose two later actions A0,A1 from a supported, non-identical action menu. For the first feasibility run, keep the history compound chemically distinct from both later actions; reusing it as an action requires a separately declared cross-resistance question. Fix each physical dose and 72 h endpoint time before opening final outcomes; a separate dose-response run may select doses near 0.8× an estimated IC50, but cannot be used to tune the contrast after seeing final blocks. Include vehicle only as an assay/control arm if needed; it is not a third action in the primary contrast.

Washout is a hard gate. Use a predeclared number of medium exchanges and a fixed washout interval. At action start, assay both medium and cell lysate for the history compound when an analytical assay is available. If LC-MS is unavailable, use a validated carryover bioassay with a stated detection limit. Residual concentration must be below the predeclared threshold (for example, below 1% of the history concentration and below one tenth of the action assay's separately measured effect threshold). If this fails, the two actions are not interpretable as randomized next actions; record failure and stop.

## Minimal physical layout

Use at least four independent preparation blocks. A block is a separately seeded culture preparation on a separate day/passage or independently thawed aliquot, with both histories represented in that block. Three blocks are source/development blocks; the fourth is sealed as the prospective holdout before its action outcomes are opened. Four blocks are a feasibility floor, not a powered efficacy study.

Within every block:

1. Randomize wells to H0 or H1 after matched seeding and plate-position balancing. Apply the history exposure under the same schedule.
2. Wash out and verify residual drug at the action-start time.
3. Split each history into exchangeable sister cultures. Diagnostic sisters receive the pre-action panel and baseline/growth controls; they are destructive and are never subsequently assigned a drug action.
4. Independently randomize the remaining endpoint sisters to A0 or A1, stratified by history, plate position, and starting cell count. Every history has both actions in every block. Keep action labels blinded during panel processing where practical.
5. Measure Y at the fixed 72 h endpoint. Technical wells are averaged within a block; the independent unit for uncertainty is the preparation block, not the well.

A practical feasibility layout is at least four endpoint wells per history × action per block plus two diagnostic sisters per history. Increase wells only to estimate within-block assay noise; do not count them as additional biological replicates.

The action randomization occurs after the state measurement time but before action exposure. The state panel is therefore pre-action for A. It is not legitimate to measure a destructive probe after A and call it a state predictor.

## Admission, holdout, and fair baselines

Freeze panel transformations, missingness rules, strata, and dose labels using the three source blocks. Freeze the practical equivalence margin before any final-block outcomes are opened, from an independent assay-precision/headroom pilot or an externally justified decision threshold; do not estimate it from source or holdout action outcomes. Do not use the holdout block's outcomes for probe choice, normalization, threshold choice, or model selection.

The primary source comparison has exactly the same S, history labels, action labels, block IDs, and optimization budget for every arm:

1. **Action-contrast baseline:** block-aware ridge/ordinary linear contrast regression from S, with history and action included only as prespecified covariates.
2. **Direct full-input baseline:** ridge or PLS from baseline/growth, recorded history, dose/time, and S.
3. **History-only/kinetic baseline:** cell count, growth, history identity, dose/time, and no functional panel.
4. **Ordinary panel response-panel baseline:** multivariate ridge predicting both action outcomes or their contrast from S, with additive/shrinkage fallback when data are sparse.
5. **Fixed-panel controls:** a prespecified expert panel and a random panel at the same number of measured probes and the same wells, reagent, instrument, and time cost.

The proposed compact contrast map may use only source-frozen coarse strata (for example, low/high stress) or a small prespecified linear model. Do not estimate a separate effect at every noisy continuous s with this sample size. A collapsing encoder cannot create common support.

Before opening holdout outcomes, the source-frozen map predicts each holdout block's action contrast and a preferred action or tie. Score (i) absolute contrast error, (ii) action-selection regret relative to the observed better action, (iii) sign/tie accuracy with a predeclared abstention rule, and (iv) uncertainty by independent preparation block. Report assay cost and coverage: a lower-cost claim requires actually omitting assays in a prospectively frozen panel, not deleting coordinates retrospectively.

## Equivalence margin and decision rule

Let Δ̂ be the history difference in the two-action contrast on the growth-corrected viability scale. Freeze

`δeq = 0.10`

as an absolute viability-fraction difference, or replace it before final-block unblinding by a source-independent margin justified from the assay's decision headroom. The margin must be biologically consequential and recorded before the final holdout is opened.

For the two-history equivalence gate, require the 95% confidence interval for Δ to lie entirely in [−δeq,+δeq], using block-level paired contrasts and a method appropriate to the small number of blocks. A non-significant history-by-action interaction is not equivalence. If the interval is wider than the margin, report inconclusive. If the action contrast is near zero, apply the predeclared tie/abstain rule rather than claiming preserved choice. Separately report absolute endpoint differences and any minimum efficacy or toxicity failure.

The holdout is a prospective block check, not an independent unseen-history test. A later unseen-history test needs a third history selected before outcomes and a separate source-frozen mapping.

## Conditions that make the experiment unidentifiable or invalid

Stop or label the result non-identifying when any of these occur:

- panel distributions for the two histories have no common support, or one action has no observations in the overlap region (positivity failure);
- history exposure is confounded with passage, thaw, day, plate, density, or block, so H is not separable from preparation;
- residual history compound exceeds the carryover threshold or washout duration differs by history;
- diagnostic and endpoint sisters are not exchangeable because splitting occurs after a history-specific selection, density correction, or assay perturbation;
- an action is assigned before the stated state time, or a destructive probe is measured after action exposure;
- technical wells are treated as independent blocks, or a target block is used to tune the map before its prospective score;
- action dose, uptake, endpoint time, or assay semantics differ across histories;
- endpoint floor/ceiling, near-zero contrast, missing wells, or broad confidence intervals make the margin unresolvable;
- the probe panel was selected using holdout outcomes, or a target action was used as an input while claiming target-independent transfer;
- the two actions do not share a declared decision scale, or absolute toxicity/safety constraints are omitted;
- only failure to reject an interaction is reported without an equivalence margin and support audit.

Even a successful equivalence result is limited to the eligible surviving population at action assignment. It does not identify the prior history's total effect on cells that died or detached before randomization.

## What this design can and cannot establish

A positive result would support a bounded statement: in this cell model, history pair, action pair, dose/time window, washout rule, assay contract, and preparation range, a small pre-action functional panel preserved the randomized two-action contrast within δeq and predicted the held preparation block better than the declared ordinary baselines at matched cost. It would not establish a new representation theory, a mechanism, universal history transfer, unseen-action generalization, or a Virtual Cell.

A negative or inconclusive result is informative. If the panel and ordinary response-panel ridge perform equally, the biological measurement may still be useful but the special compression claim fails. If no reproducible history-by-action reversal exists, the proposed decision use case is absent in this regime. If overlap or washout fails, the experiment did not identify the contrast and should not be rescued by a larger model.

## Audit trail

This design was checked against:

- `2026-10-31-crossfield-state-learning/REPORT.md`, which limits the candidate to action-contrast sufficiency, warns that destructive tests require sister cultures, and requires overlap, randomization, margins, and held preparation/chemistry support.
- `2026-10-31-crossfield-state-learning/CHALLENGE.md`, whose independent challenge rejects broad novelty, calls for a two-history × two-action randomized skeleton, independent preparation blocks, ordinary response-panel and DBP rivals, and a predeclared practical margin.
- `2026-10-31-task_sufficient_transfer_mvp_20261101/REPORT.md`, which records that existing exposed data lack matched history/action/outcome joins and cannot admit this experiment.
- `2026-10-31-context-dependent-functional-rules/report.md`, which records that common-coordinate restrictions were not independently demonstrated and that any numerical discrepancy is an engineering issue, not biological evidence.

No existing report was accepted as proof. The protocol is a proposed falsification design, not a completed experiment.
