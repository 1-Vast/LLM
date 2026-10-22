# Independent finite-C4 protocol/code review

2026-10-22. Scope: authorized ordinary opportunity diagnostic, not cardiac mechanism or innovation review. No demand that a new world first beat a direct model. No biological outcome arrays opened by this reviewer. Reviewed current `strategy_rethink/PROTOCOL.md`, `ROOT_REVIEW.md`, schema/manifest preparation, `screen.py`, and `check_boundaries.py` before freeze/execution.

**Conditional disposition: execute after the concrete small repairs below.** The inspected solver/feedback logic has no observed terminal-label path to nomination or deployment. This is a same-class learned proposal checkpoint experiment, with limited claims correctly stated.

## What identifies the intended comparison

- Old and new are both categorical distributions over the same eleven non-S0 programs, sampled without replacement; old logits are zero, new logits are source-trained. There is no within-target score-driven logit update. This is learned ordering, not strategy invention.
- All arms share exact target calibration rows, fitted S0 and its development score. They receive four distinct non-S0 evaluations; development scores select deployment with the same tie rule. Cache sharing makes same-episode fits identical and is disclosed separately from logical requests.
- Source checkpoint scores are generated only from source calibration fits/source development scoring. Target calibration truths are used for the target solver; target development truths only return candidate scores. `nominate` receives target descriptors and source record-derived quantities, not target development vectors or terminal scores. Source evaluation is not scored.
- Target terminal scoring and finite-grammar audit occur after an on-disk deployment/source checkpoint hash seal. Source-best, contextual ridge, nearest-source history, cyclic, old/uniform, refit and mixture are actual comparators. Offline terminal oracle is not passed to any proposal arm.

## Precise overlap, exposure, and dependence

For each program `j`, `mean_e(score[e,j]-score[e,S0]) = mean_e(score[e,j])-constant`. Thus learned softmax ranking is **exactly** the source-best ranking; only stochastic sampling differs. A new-vs-old gain alone measures ordinary source-conditioned ordering. Comparing against source-best/contextual/history is essential, and a tie does not pass this opportunity gate. Full-dictionary refit is also grammar program10, not an independent architectural alternative.

`np.load(...)["truth"][take]` decompresses/decodes the whole NPY member before masking, including unselected folds and terminal/source-evaluation rows. It returns only selected arrays to the fitting code. Therefore this is an exposed-data, software-masked experiment: distinguish full-array decoding from selected-value use, human inspection, scoring, and learner access. The protocol's added explicit full-decode statement is appropriate. Never report this execution's terminal values as numerically unopened. Historical route construction also crosses the new partition, as already disclosed; top-layer disjoint IDs do not remove that dependence.

The manifest was revised before freeze to bind exact archive row indices, correcting the initial ID-only draft. Original compound IDs remain the partition unit; folds, lines and seeds are not independent biological replicates. The public pack contains all cal/dev data, but the inspected procedural call graph keeps each solver's fitting set and each score's feedback set separate.

## Concrete repairs sent immediately to strategy agent and root

1. **Permutation null:** initial `permutation(12)` followed by excluding S0 loses one eligible candidate's logit and introduces S0's zero gain into the eligible multiset. Permute only the eleven non-S0 candidate logits, keeping S0's slot fixed. This preserves candidate probabilities up to content reassignment as intended.
2. **Stop condition:** initial runner sets `positive = new>old and new>best_ordinary` but omits the registered requirement `oracle_mean>S0_mean`. Oracle includes S0 and can equal it, while all dev-selected deployments fall below S0. The original runner could then ALLOW a relatively best but ineffective search. Add the explicit oracle condition; no result has been inspected to motivate this fix.
3. **Seal semantics:** initial `terminal_loaded=False` and comment that terminal values enter only after seal conflict with full-member NPZ decoding. Use precise `terminal_selected_for_scoring=False`, `terminal_returned_to_learner=False`, and disclose `npz_all_truth_decoded=True` before the scoring seal. This is an exposure-description repair, not evidence of a label-feedback path.

Existing synthetic prediction-sentinel tests verify predictions do not read prediction-target truth. They do not alone constitute an end-to-end sentinel substitution test of source learning and all policy trajectories; the function signatures/call graph support isolation, but report the actual tested boundary precisely. Check exact common-start calibration hashes and compound-weighted scoring from saved row results in the post-run audit, as required by protocol.

At the time of this review, the exact final freeze and completed experiment were not yet available. This document does not certify unseen future code or report scientific success. An addendum can bind the final reviewed hashes and confirmed repairs without changing the pre-execution criticisms above.
