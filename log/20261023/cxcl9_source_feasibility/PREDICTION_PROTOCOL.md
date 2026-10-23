# Frozen development comparison: P12 to P14 fluorescence response

## Scope and endpoint

This is a new raw-data baseline diagnostic, not a new method test or confirmation. No functional statistic has yet been printed/read by root or peers; four raw payloads have been downloaded and only schemas/categories/counts inspected. AL1/AL2 remain unfetched. Independent method/biology reviews support a scoped passage-transfer diagnostic; construction/cross review rules out action-versus-edge attribution from the planned feedback alone.

For each of AsPC1 and BxPC3, P12 is source; P14 is target (per author metadata, not an independent new cell background). Two Condition labels per screen are duplicate wells/samples with biological independence unresolved. FACS events are capture-bead measurements, never independent cultures or tasks.

Primary endpoint per well/condition: log10 of arithmetic mean PE fluorescence after IQR trimming **within that well/condition**, minus the corresponding no-cytokine/no-inhibitor well log-MFI. This measures a fluorescence log-ratio, not calibrated secretion fold change, per-cell secretion or apoptosis-corrected efficacy. All four no-inhibitor cytokine controls are acquired in each target sample. No positive-anchor division, screen-wide min/max, assay-maximum clipping or death correction is used. Recompute with no trimming as the prespecified sensitivity; this is not a faithful reproduction of author's pooled trimming/global normalization.

Schema must have 24 unique cytokine/inhibitor conditions and two Condition labels in each file. Literal `None` must be preserved. Fail rather than infer if means are nonpositive/nonfinite, conditions missing, or control mapping absent. IQR boundaries are inclusive. Paper states all screened samples contain 1% DMSO, including blank; raw schema does not independently authenticate vehicle dosing. This assumption limits interpretation if contradicted later.

## Information and costs

Source: all 24 conditions × 2 samples (48 wells) at P12. Target feedback: all 4 no-inhibitor controls and all 5 drugs under IFNG_TNFA × 2 samples (18 wells). Test: each drug under None, IFNG, TNFA (15 condition means; 30 wells). Test values are used only for the frozen losses, never selection. Feedback selection is fixed and not agent-controlled. No unseen-drug extrapolation claim.

All methods may see the same source/feedback; source/control-only references deliberately ignore some acquired labels. All target outcomes are measured historical data; masking is retrospective replay, not new experiments. Every target group is summarized separately, so another test group's outcome does not change its transform. The target blank is shared known feedback; losses are correlated.

## Fixed conventional methods

Source table is mean of two independently blank-centered source samples. Enumerate all methods with no test-dependent additions:

1. source_copy: exact source table response.
2. control_affine: ordinary affine least squares using the four paired controls.
3. control_anchored_copy: target control for stimulus + source drug-minus-control effect.
4. global_affine: ordinary affine least squares using all nine feedback conditions.
5. drug_shift: control-anchored copy plus the drug's residual at IFNG_TNFA, constant across other stimuli.
6. drug_slope: rescale each source drug-minus-control effect by a scalar fit to that drug's one feedback, ridge toward 1; penalty grid 0.0001, 0.01, 1 in squared log10-fluorescence units.
7. residual_kernel: control-anchored copy plus Hamming-kernel ridge interpolation of the nine observed residuals. Kernel exp(-(cytokine_mismatch+drug_mismatch)/length); lengths 0.25,1,4; ridge penalties 0.0001,0.01,1.
8. half_shift: fixed 50/50 mix of control-anchored copy and drug_shift.

This is strong within-menu direct transfer/calibration, including an ordinary action-effect scalar, nonlinear kernel and simple mixture. No world-model forward, model training claim, active acquisition, continual-learning or equal-budget program-search victory is tested. Those controls remain required before any later full-goal claim.

Tune drug_slope and residual_kernel separately per cell using only the two P12 duplicate directions (sample1→sample2 and reverse): same 9→15 protocol. Select the adaptive method among global_affine/drug_shift/drug_slope/residual_kernel/half_shift by source-only mean MSE with deterministic declared ordering for ties. Report every model, source tuning scores, configuration counts and selected method; tiny correlated source pseudo-tasks are exploratory, not independent task inheritance. No root outcome inspection before all predictions are saved.

## Metrics and decisions

Primary MSE over 15 target condition means; also report loss per each of three stimulus menus and each target duplicate. Drug decision: among six already defined inhibitors/no-inhibitor options per each None/IFNG/TNFA context, choose largest predicted log-ratio, ties lexicographic. Report true best-minus-selected fluorescence regret and selected action. No-inhibitor response is known feedback and included for every method. Three correlated menus are not independent trials. This is secretion-assay selection, not cancer treatment utility.

Feedback utility earns only a directional DEVELOPMENT_SUPPORTED label if the source-selected adaptive method improves MSE over control_anchored_copy in **both** cell lines, does not worsen mean menu regret in either, and these directions hold in the no-trim sensitivity. Otherwise mark NOT_SUPPORTED/MIXED as appropriate. Also explicitly compare each adaptive result with the strongest frozen conventional result; no post-hoc winner becomes a new method. No significance test on beads or random split of events. No numerical magnitude threshold or functional-mechanism success is invented. Stronger evidence and new independent tasks are needed beyond any directional result.

STOP this fixed pilot after one run plus saved-result audit, regardless of direction. Do not search extra feedback designs, transformations or candidate gates on its 15 heldout values. Preserve any useful conventional result; it never establishes novelty, WM necessity, agent, inheritance, joint or improved-improver benefits. No action/edge causal interpretation: 4 controls + 5 independent drug shifts can span the 9 feedback values.
