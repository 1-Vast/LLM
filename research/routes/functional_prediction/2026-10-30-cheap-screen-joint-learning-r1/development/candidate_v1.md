# C1 v1: does a shared conditional cytokine gain survive inhibitor intervention?

2026-10-30. **Frozen developer candidate for coordinator examination. Proposed empirical restriction; no observed support, novelty clearance, test admission, Agent advantage, or main-mechanism recommendation.** This is the only frozen developer candidate in this round. The coordinator and an independent challenger must decide the experiment contract. The proposer is not the reviewer.

## Scientific question and use

In one PDAC cell line at one stated cytokine dose, inhibitor dose, endpoint and time, is the extra CXCL9 assay response to IFNγ in the presence of TNFα an approximately fixed multiple of the IFNγ response without TNFα, even when different inhibitor interventions alter their own basal and single-cytokine responses?

The useful scientific distinction is between **a shared cytokine amplification relation** and **inhibitor-specific changes in how cytokine inputs combine**. If the restriction holds on inhibitor conditions excluded from calibration, it supplies a compact, testable way to predict those dual-cytokine responses from their single-cytokine controls. If it fails, the pattern identifies the scope in which the shared rule must be withdrawn and direct dual-cytokine assays retained. It does not identify molecular mediation. The output is a conditional prediction of the source's CXCL9 bead-assay signal, not tumor killing, immune-cell recruitment, or secretion per live tumor cell.

The affected user is a signaling or functional-screening laboratory already characterizing basal and individual-input responses. The proposed practical use is to decide which dual-input measurements still require direct testing and which inhibitor follow-up is justified by a supported functional rule. The actual net assay savings are unknown and **not claimed**: buying three new inhibitor-specific controls to avoid one target measurement is inferior to directly measuring that target when it is the only desired decision.

## Source and exact observation contract

The immediate source is *Active learning-guided mechanistic modeling reveals context-specific regulators of CXCL9 expression in pancreatic cancer cells*, DOI `10.1038/s44320-026-00221-w`, PMC13434641; local original `../evidence/active_mechanistic.body` and selected extraction `../evidence/active_mechanistic.selected.txt`.

The source already owns a prior-knowledge signaling network, logic-ODE cell models, an ensemble refitted from experimental feedback, and greedy/uncertainty/combined acquisition of drug conditions. Par16–20 also report cytokine synergy and inhibitor/cell-specific changes, including PI3Ki in BxPC3 and IKKi in AsPC1. **Generic functional virtual cell plus Agent learning is therefore direct prior art, not our candidate.** The proposal does not repeat the source's selected-hit discovery as new work.

According to inspected Methods and the coordinator/investigator's identity audit, the four acquired initial-screen files contain 4 cytokine backgrounds × 6 inhibitor choices: none, JAKi/momelotinib, IKKi/BMS-345541, PI3Ki/taselisib, MEKi/trametinib, and RASi/salirasib. They have two technical samples per condition and two source-described independent screens per cell line: BxPC3 E3CA/P12 and E3CB/P14; AsPC1 E3DA/P12 and E3DB/P14. The experiment lasts 24 h, inhibitor dose is 5 μM, and cytokine dose is line-specific, 1 ng/mL in BxPC3 versus 10 ng/mL in AsPC1. Cross-line label equality is not matched physical exposure.

Raw events are LEGENDplex capture **beads**, not tumor cells. Event counts must not be treated as cell counts, biological replicates, or evidence of cellular heterogeneity. Technical samples are aggregated within each biological preparation; independent preparation is the highest available repeat unit. The source's later combined-inhibitor AL outcomes, synthetic outcomes, and apoptosis-adjusted endpoint are outside this first test. Par61's summed/rescaled CXCL9 plus Caspase-3 quantity does not establish secretion per survivor and is unnecessary here.

The source's raw-to-MFI extraction/gating status must be qualified before numeric work. Par60's later min–max scaling is not to be silently refitted on held-out target values. A raw or control-only affine scale is sufficient for the narrow contrast, provided the same transformation applies to every condition within the preparation. Nonlinear fluorescence-to-concentration calibration is a separate issue: without it, the relation remains about MFI.

## Inputs → operative rule → prediction

Let `Y[p,b,i,t]` be the mean assay signal for preparation `p`, inhibitor `b`, and binary IFNγ/TNFα inputs `i,t`. Each mean must come from the source-qualified technical samples; `b=0` denotes no inhibitor. Keep the inhibitor-specific baseline `Y[p,b,0,0]`.

Define two conditional IFNγ effects:

```
U[p,b] = Y[p,b,1,0] - Y[p,b,0,0]
V[p,b] = Y[p,b,1,1] - Y[p,b,0,1]
```

The candidate restriction is:

```
H_gain: V[p,b] = kappa[p] * U[p,b]
kappa[p] = V[p,0] / U[p,0]
```

The no-inhibitor IFNγ denominator must first be signal-qualified using controls only. A nonzero machine-level value is not adequate qualification. If it fails the frozen control gate, the preparation is non-evaluable under this parameterization, not an empirical rejection or a reason to choose another denominator. No inhibitor-target outcome may determine the gate or the tested family.

After calibration, the target prediction for each of the **five** inhibitor interventions is:

```
Yhat_gain[p,b,1,1] = Y[p,b,0,1]
                         + kappa[p] * (Y[p,b,1,0] - Y[p,b,0,0])
```

Its inputs exclude that inhibitor's dual-cytokine outcome. Neither `kappa[p]` nor a membership filter is fit to those targets. Inhibitors that suppress IFNγ nearly to zero are not divided by their own small effects; they are retained unless an independently frozen assay-quality condition makes their source observation invalid. No favorable subset may be selected after outcomes.

The restriction is invariant to a common positive affine readout transformation `Y' = aY + z` within a preparation: U and V both multiply by a, kappa is unchanged, and the prediction transforms consistently. By contrast, the uncorrected quantity `Y11 - Y10 - Y01` changes by `-z`. This observation motivates the baseline-corrected estimand; it is standard factorial algebra, not a new method.

The gain may differ between preparations. Therefore use of no-inhibitor controls from P14 constitutes **calibration-conditioned target holdout**, not an entirely unseen preparation. Repetition on P14 after a rule fixed without its target values provides limited preparation-transfer evidence. Four preparation records across two lines do not establish a population-level replication claim.

## Exact ordinary equivalence and rivals

For each preparation, stack the pairs `(U[p,b], V[p,b])` across inhibitors. H_gain says the two-column matrix has rank at most one, with the no-inhibitor row fixing the slope. Equivalently every calibrated minor obeys:

```
V[p,b] * U[p,0] - U[p,b] * V[p,0] = 0.
```

This is ordinary rank-one/separable response modeling and a special restriction of a sufficiently flexible joint model or logic network. Estimation, feedback updating, and action selection can all be ordinary regression/model criticism/design. The archive's MuSyC product-state and invariance work is a warning against presenting separability as a new algorithm. No new mathematical form or priority claim is made here, and an exact mapping to every MuSyC parameterization has not been proved in this assignment.

Two minimal rivals distinguish the scientific restriction using exactly the same condition-level inputs:

```
Additive: Yhat_add = Y10_b + Y01_b - Y00_b.

Constant interaction:
I0 = Y11_0 - Y10_0 - Y01_0 + Y00_0
Yhat_const = Y10_b + Y01_b - Y00_b + I0.
```

H_gain says the extra untreated interaction scales with the inhibitor's single-IFNγ effect. H_const says it remains an additive amount. Their predictions differ by:

```
Yhat_gain - Yhat_const = I0 * (U_b / U_0 - 1).
```

Thus a preparation with negligible I0 or an inhibitor with U_b close to U_0 is weakly discriminating. Agreement in those cases is not strong evidence for the gain relation. The predicted differences and observed errors must be reported, without retrospectively selecting only informative or favorable cases.

Stronger ordinary alternatives for a subsequent capability claim are the source logic-ODE model, an unconstrained inhibitor×cytokine interaction model with shrinkage, and drug-specific response transfer from the earlier preparation using equal calibration information. Direct target measurement and a fixed validation panel remain the operational comparators. The first minimal test can falsify H_gain without rebuilding all of them. Beating only additive or constant-interaction predictors would not establish superiority to the source model, a new algorithm, or an Agent advantage.

## Why test it despite the close prior?

The original already observes cytokine cooperation and context-specific inhibitor effects. The possible new content is solely whether the **same quantitative conditional gain** transfers across inhibitor interventions after their own baseline and single-input effects are accounted for, and whether that restriction survives a separate preparation. This exact empirical difference is unresolved: the selected original passages do not explicitly test the above restriction, but uninspected material or earlier work may already do so. No absence or novelty claim follows.

Par19 reports significant versus non-significant combo-versus-sum tests using biological and technical observations together, while acknowledging n=2 biological screens. A difference in those significance labels is not itself a test of the inhibitor's change in conditional gain. Conversely, this statistical point supplies no evidence that the proposed gain is preserved. The raw matched four-condition contrasts are needed. The candidate could agree with, qualify, or fail alongside the authors' qualitative interpretation; none may be presumed.

A positive result would retain a narrow empirical lead about functional input combination, worth a closest-prior and broader resource check. A negative result would stop this all-five-inhibitor sharing rule and identify where a common amplification approximation fails in the actual assay. A result too noisy or nondiscriminating to separate the rules is inconclusive. None of these outcomes achieves the overall Agent × virtual-cell research goal by itself.

## Minimum decisive test and Agent link

The coordinator's proposed first test is scientifically worthwhile as a bounded exploratory discrimination, with four preparations and all five inhibitor target conditions fixed before raw target inspection. Qualify source preprocessing, source-versus-technical repeat identities, and the no-inhibitor signal gate first; then calculate the three predictions from permitted control/single-input observations and evaluate each withheld dual-input target once. Report preparation-resolved residuals and continuous errors on a fixed control-derived scale. Report the technical-sample spread as descriptive measurement variation; do not bootstrap bead events or technical samples into biological confidence intervals. The exact signal gate, error scale, thresholds and file/column whitelist must be frozen by the execution protocol before values are decoded.

Source-reported response directions have already been read by this developer and coordinator. The analysis is therefore exploratory public-data reanalysis, not untouched confirmatory biology. No target-guided tuning, drug removal, alternate normalization search or rerun to recover a positive result is justified.

In a future joint-learning loop, observing one calibration dual-input condition changes kappa and consequently changes predictions for still unmeasured inhibitor conditions. A contradictory inhibitor outcome withdraws the common-gain restriction instead of merely counting as another fitted point. That can change an Agent's next action from reuse to direct assay. The update and choice remain ordinary; whether they improve decisions or save assays is a separate, unperformed question. If the available workflow only needs one target response, direct measurement is likely the stronger action.

## Ancestry, revisions and current limits

`initial_note.md` D0 compared rescue suppression, chemical-mimic transport and preparation-stable functional structure. The CAF branch is not selected: its double-assay criterion and selected transfers are source-owned, and a reusable paired matrix is unqualified. C1 uses the newly acquired CXCL9 intervention crossing and is a change of scientific object within functional screens, not a rescue of an old negative sampler. The coordinator suggested the shared cytokine-gain family while source evidence was exchanged; this candidate is **not blind development**. The initial-note ordering failure remains explicitly recorded.

This is the initial frozen C1 version; zero substantive revisions so far, at most two allowed. No raw fluorescence outcomes or experiment results have been read or executed by this developer. No current effect, independent validation, savings, molecular explanation, clinical utility, or novelty is established. No source/index/core files were edited. Local reasoning and development records only; zero network requests, external model calls, installed dependencies or new agents.
