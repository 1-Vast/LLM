# Independent biological interpretation of frozen pilot

2026-10-23. Read PREDICTION_PROTOCOL.md, PREDICTION_FREEZE.json, saved PREDICTION_RESULTS.json and the structure/source-target/prediction records of PREDICTIONS.json. Read relevant predict.py lines to confirm that acquired no-inhibitor responses overwrite predictions for every decision menu. Did not rerun any model, preprocessing, or prediction; did not inspect another agent's result review. Reported percentages are arithmetic ratios of saved aggregate losses. Initial independent, FINAL and CROSS seals preserved.

## Frozen criterion: not passed

The source-only selector chooses global_affine in both trimmed cell lines. Relative to control_anchored_copy, its MSE worsens from 0.0455954 to 0.0645319 in BxPC3 and 0.0167113 to 0.0171034 in AsPC1. BxPC3 mean menu regret stays 0.0432056; AsPC1 worsens from 0.00843245 to 0.0122583. Without trimming, BxPC3 again selects global_affine and worsens MSE (0.0606524 to 0.0733720); AsPC1 selects residual_kernel and improves MSE slightly (0.0810930 to 0.0806751), with unchanged regret 0.295730. Hence the frozen requirement of both-cell MSE improvement, no regret worsening, and preserved directions under no trimming fails. The saved NOT_SUPPORTED_OR_MIXED is appropriate. This is a failure of this source-duplicate-selected conventional adaptive menu, not a universal impossibility of feedback learning.

## Positive evidence that should be retained

The four-control affine calibration improves MSE over source_copy in both cell lines under both preprocessings: trimmed BxPC3 0.0572772→0.0358381 (37.43%), trimmed AsPC1 0.0266812→0.0119212 (55.32%); untrimmed BxPC3 0.0606517→0.0490493 (19.13%), untrimmed AsPC1 0.0871579→0.0735803 (15.58%). This is useful conventional context/assay calibration and a strong baseline. It is not evidence that the drug-action mechanism, internal signaling trajectory, or research program improved. It uses only four of nine legally available target conditions; ignored drug feedback is a disclosed restriction, not a data-access advantage.

This calibration does not improve mean menu regret for BxPC3, improves trimmed AsPC1 regret (0.0122583→0.00843245), and leaves untrimmed AsPC1 regret unchanged. Predictive MSE improvement therefore does not uniformly imply better selection. The protocol's menu choices use known no-inhibitor controls, so this is not an artifact of withholding an already acquired control action.

A local positive operation is drug_slope: in trimmed BxPC3 its MSE is 0.0358081, 21.47% below control_anchored_copy but only 0.084% below control_affine; in trimmed AsPC1 it is 0.0158221, 5.32% below anchored copy but 32.72% worse than control_affine. Untrimmed BxPC3 retains a larger conventional slope gain (0.0369462, 39.09% below anchored copy and 24.68% below control_affine). Untrimmed AsPC1 slope loses to anchored copy (0.0816141 vs 0.0810930). Thus a plausible drug-specific rescaling can be helpful locally. It was not the source-selected operation, does not win across contexts/preprocessing, and cannot be promoted by picking it after evaluation.

## Decision sensitivity prevents a clean discovery claim

The fixed half_shift mixture has zero trimmed BxPC3 regret and trimmed AsPC1 regret 0.00302013, while drug_shift has zero trimmed AsPC1 regret. Both have worse MSE than the control-affine reference. More importantly, half_shift BxPC3 regret deteriorates to 0.0876301 untrimmed, worse than control_affine 0.0344828. AsPC1 untrimmed regrets cluster near 0.29 across methods, much larger than trimmed regrets. This does not identify which preprocessing is biologically correct; it establishes that these functional decisions depend materially on bead-tail handling. Neither trimming nor an untrimmed winner can be chosen after this result as validation of a new operation.

Primary and sensitivity endpoints are fluorescence log-ratios, not CXCL9 concentrations, secretion per viable cell, or apoptosis-corrected benefit. Large trim sensitivity could arise from analytical events, assay artifacts, or real distribution structure; the saved aggregate losses cannot resolve these explanations. No claim that an inhibitor actually improves antitumor immunity follows from selecting its highest fluorescence outcome. Three correlated menus per cell and two unresolved duplicate wells do not support a reliable population-level rank statistic or significance test.

## Independence and scientific scope

The source and target are two passage contexts in each of two familiar cell lines. The 15 condition means are correlated through shared drugs, cytokines, blanks and plate/screen factors. They are not fifteen independent biological tasks, nor are capture-bead counts biological n. The two source duplicate directions used for selection are correlated pseudo-tasks; their preferred operation failed to generalize consistently to P14. This is informative about that specific transfer/selection design but not broad procedure inheritance or an improved improver.

The one-feedback-per-drug design remains unable to distinguish action strength, additive residual, stimulus gate, or internal network-edge repair. Good local slope performance supports at most its predictive inductive bias under this endpoint. No cell-state trajectory, alternative simulator, graph contribution or agent-controlled acquisition was evaluated, so world-model, agent, joint, inheritance and RSI benefits remain unestablished.

## STOP scope and next evidence boundary

STOP this fixed pilot now as preregistered: do not search other feedback contexts, new mixtures, outlier cutoffs, reverse passage directions, or candidate edge edits on these 15 evaluated outcomes. Retain control affine as a useful baseline and the local slope gains as development evidence. STOP promotion of source-selected adaptive transfer as robust feedback benefit under the frozen criterion. This does not stop every action-restricted predictor or all CXCL9 tasks; it stops using this pilot as positive proof of one.

Any later mechanism must be independently specified and supported by new untouched evaluation contexts; after this inspection the initial P14 heldouts are development data. AL1/AL2 remain separate protected outcomes, not an automatic unbiased confirmation (designers have seen primary-paper methods and possibly broader historical literature). A later acquisition benchmark still requires counterfactual real outcome coverage and explicit assay costs. No proposal to open these protected data is made here.

## Review-read failures

Initial path lookup used shorthand RESULTS.json/FREEZE.json and returned absent paths; corrected to the actual PREDICTION-prefixed files. One PREDICTIONS record inspection assumed a list and returned KeyError 0; corrected to its dictionary structure. These were read-only inspection failures, with no experimental reruns or mutations to frozen artifacts.
