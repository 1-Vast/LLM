# Constructive multi-agent exploration — 2026-10-04

## Objective

The user explicitly redirected this discussion toward **solving the current prediction–action–feedback problem**, rather than strengthening the previous stop verdict. Three agents investigated batch acquisition, information-preserving prediction, and independent measurement recovery. This report proposes new executable questions; it does not rerun or reinterpret the frozen confirmation-campaign study.

The most practical next task is **two-stage acquisition of native plate sets**. In parallel, recover independent raw-response targets and test whether retaining potency and efficacy information helps the predictor. Vis evaluation outcomes remain unopened during this exploration. No production code, model experiment, API inference, commit or push was made.

## Solution A — Optimize the action that can actually be purchased

### Why this is a new opportunity

`../confirmation_campaign_20261004/resources/native.py` already maps a plate-set action to all measurements it produces. However, `screen_pass` and `verify_pass` walk individual pair rankings and then buy the corresponding whole component. They do not maximize the aggregate value of that purchase.

The parent independently summarized the design-only `resources/receipts/design_facts.json`: HD targets have 2–7 screen components and 2–7 verification components per role. Each side has at most 128 subsets. Mean menu outputs per screen component are 22.52 (Breast), 25.39 (Colon), and 25.45 (Pancreas). This is small enough for exact enumeration. A group purchase can confirm multiple pending hits; indivisible costs and shared outputs create a decision problem absent from independent pair acquisition.

### Minimal first experiment

Keep the original first-round purchases, two-round deadline, plate cap, measured menu and predictor unchanged. For each unpurchased verification component k, define:

`value(k) = sum of q_i over pending screen hits whose verification belongs to k`

`cost(k) = number of original design plates in that component`

Use a legal historical verification probability as q, initially the same frozen marginal p_v for all policies. C_mean is a ranking score, not a conditional probability: do not silently interpret it as P(verification succeeds).

Compare the existing pair-first policy, pending-hit-count per cost, aggregate expected yield per cost, and exact budgeted subset selection. Each candidate belongs to one verification component, so expected values add without assuming independent successes. Enumerating at most 128 subsets avoids a new optimizer framework or LLM.

Evaluate **measured confirmations from the newly selected plate sets**, actual consumed plates, controls/single-agent accounting, leftover cap and changed actions. With fixed first-round purchases, a hindsight optimizer using actual verification outcomes supplies a valid bound for this narrowly defined second-round problem; it is not a bound for every scheduler.

If this stage shows acquisition headroom, optimize first-round plate selection. Enumerate screen subsets and evaluate their downstream verification decisions using whole-line donor patterns from training data. Preserve correlated hit patterns and fold isolation; do not simulate independent Bernoulli hits as if that were an observed joint distribution. Restrict to a genuinely common measured menu rather than imputing missing donor outcomes.

### Dual-core contribution

The world model supplies comparable per-action response/confirmation predictions and uncertainty. The agent/planner groups those predictions into executable plate purchases and adapts after the first reveal. Initially hold predictions fixed to isolate planning contribution. Only after that test add one conditional predictor and compare it against the same planner using simple historical probabilities.

This does not require an LLM: an exact small planner is an appropriate strong baseline. Successful algorithmic coordination would establish a bounded dual-core contribution, not biological mechanism identification or prospective wet-lab savings.

## Solution B — Recover the information discarded by the current target

The current Jaaks builder learns `max(mean SYNERGY_DELTA_EMAX)` as one continuous label. TransferWorld predicts this screen-direction label; subsequent shrinkage/calibration does not reconstruct a missing potency channel.

The parent checked the fitted file header: potency shift `SYNERGY_DELTA_XMID`, combination IC50 `SYNERGY_XMID_uM`, observed efficacy `SYNERGY_OBS_EMAX`, and multiple AUC fields exist. AUC documentation has an apparent EXP/OBS ambiguity identified by the model agent, so exclude AUC from the first candidate until reconciled. Growth rate and doubling time involving day-4 controls are not untreated decision-time state.

### First recover independent measurement targets

Raw Jaaks intensities are already local:

- `data/external/jaaks2022_provenance/Original_screen_All_tissues_raw_data.csv.zip` (figshare article 19141916, file 34010816).
- The day-1 raw archive and earlier plate→seeding-event hierarchy are also available.

The parent read only the raw header: BARCODE, scan/seeding dates, CELL_ID, assay/duration, position/TAG, compound/dose and INTENSITY are present. No raw intensity values were read in this exploration.

Freeze a small recovery study before reading them. Map blank/no-cell and vehicle/negative controls using the author's protocol; do not equate a killing positive control with background. Normalize plate-locally, for example `(I - background)/(vehicle - background)` when that convention is validated. Preserve out-of-range values, denominator failures, missing controls and QC failures; do not clip or exclude them to manufacture signal.

Start with matched doses and separate seeding events in the 14 repeat lines. Direct observed viability can bypass shared curve fitting. Direct Bliss excess requires matched measured single-agent controls and a separately declared purpose; it is not fitted Emax and can share noise with its components. Choose one primary diagnostic readout before outcome inspection. Missing day-1 links must be accounted for rather than fabricated.

This distinguishes four possibilities: preprocessing coupling, condition changes, threshold compression, or a genuinely weak transferable response signal. Reusing raw values from already exposed experiments remains exploratory, even if these particular values were previously unread.

### One small information-preserving predictor

If units and endpoints are authenticated, compare one two-output regularized predictor of screen and verification response using efficacy and potency channels with an Emax-only version. First reproduce the actual source's call convention; do not apply the proposed Jaaks formula to Vis by analogy. Keep the historical Synergy endpoint and verdict intact. Continuous targets train the new predictor; they do not replace an unfavourable confirmation endpoint after evaluation.

Use only legal history and purchased measurements, whole-line nested development folds, a small fixed feature set and no latent-effect expansion. Compare strong simple rankings and the existing TransferWorld as well as the candidate. Isolate new readout information from model contribution by giving comparators access to the same fields. Compare static versus feedback versions with matched first purchases and priors. Measure action contrasts and actual selected-action outcomes, not just MSE.

Develop first on exposed HD data. Previously inspected E lines cannot supply fresh confirmation. Retain purchase→freeze prediction→reveal→score→update order, and keep untreated baseline state distinct from post-intervention functional feedback.

## Solution C — Make Vis usable through measurement recovery

Vis contains a useful same-condition cross-project menu, but its fitted project scores share upstream parameters. Policy-level hiding of columns does not remove upstream information mixing. The practical recovery target is raw per-well measurements with controls, single agents, dose/layout, dates/lineage, QC failures and the original fit implementation. Fit each project separately and never borrow withheld-project or unpurchased target measurements to build an exposed input.

Public code starting points identified by the data agent:

- https://github.com/CancerRxGene/gdscIC50
- https://github.com/NKI-CCB/MixedIC50
- Vis article: https://europepmc.org/articles/PMC11384948

These are starting points, not a certified drop-in combination fitter. The public Vis analysis bundle references a fitted RDS that is not included. Prepare a precise missing-asset request; no message to an author was sent or authorized in this task. Meanwhile, Solution B can proceed using local Jaaks raw records.

The parent independently read only author source code from `mmc7.zip/data-code/00_preproc.R` (SHA256 e04f9ccb6ccd351fe857ccb2ac993ebdcef4c55ae099c61171dbf9a0667e264f). Lines 67–72 use strict RMSE filtering, average fitted records before classification, and:

`(SYNERGY_DELTA_XMID > 3 AND SYNERGY_XMID <= 10) OR SYNERGY_DELTA_EMAX > 0.2`

This differs from the existing proposed Vis builder in units, parentheses and aggregation. This source-code inspection opened no fitted outcome values or supplementary outcome tables. A project-specific endpoint can be defined, but must be justified and frozen explicitly. Do not overwrite the historical proposed plan; issue a new version.

If independent raw reconstruction remains unavailable, a new Vis study can still target held-out-identity prediction of published fitted scores. That lower-tier question must not be represented as independent confirmation, legal online feedback, or untreated state value.

## Recommended sequence and deliverables

1. **Immediate development:** native verification plate-set optimization under fixed first purchases and predictions. Deliver changed actions, measured yield and complete plate accounting. This is the cheapest direct test of an untested planning contribution.
2. **Parallel data/model diagnosis:** independently reconstruct a small same-condition Jaaks subset; retain potency/efficacy information and test one minimal paired-response model if the reconstruction supports it.
3. **Then integrate:** if either component shows credible development benefit, compare the model and planner with matched strong baselines in the new batch-action task. The original pair-action verdict is preserved.
4. **Independent evaluation:** prepare Vis raw recovery and a successor endpoint/builder. Freeze its development/evaluation access before opening outcomes; use it to test the surviving new hypothesis, not to relabel the old R experiment.

A gain is not promised. The goal is to resolve specific failure mechanisms and build a task in which predictions and actionable batch choices can both make measurable contributions. Hold budgets, legal inputs and deadlines fixed for component comparisons. Report information-use gains separately from prediction and planning gains.

No new inferential verdict, raw-response reconstruction, campaign replay or model training was executed this turn. Prior test counts (481/354/22) belong to the supplied study and were not rerun. Historical freezes were checked separately; evidence and discussion artifacts are listed in `EXPLORATION_RECEIPT.json`.
