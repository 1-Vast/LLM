# Repair-information opportunity: independent read-only novelty audit

Date: 2026-10-22. Reviewer: frontier_distinct. Status: **conditional developmental falsification gate; not a new core mechanism or confirmatory study**.

No new model predictions, numerical summaries, fits, simulations, API calls, downloads, or biological outcome decoding were performed for this audit. In particular, I did not open the scalar contents of either `Q_per_background.csv`. This document audits the saved experiment's code and reports and proposes the protocol that the parent must freeze before computing a new derived envelope. All PTV backgrounds are already exposed. The historical scientific STOP remains in force.

## 1. What is and is not a new question

The assertion that historical experiments never compared state-only, head-only and joint repair on common support is incorrect. The original Experiment Q already does exactly this at the specified parameter/loss level:

- `research/dual_core_innovation_validation_20261021/ptv_feedback.py`: `support_split` selects the same three training-prior-uncertain support drugs; `fine_tune` has explicit `TRAJ_PARAMS` and `HEAD_PARAMS`; `func` updates head parameters using support labels, `mol` updates trajectory parameters using masked 24 h proteomes, and `both` updates both using the declared weighted losses. Each arm starts from a copied common model.
- `research/dual_core_innovation_validation_20261021/eval_Q.py`: every arm is evaluated on the same remaining target drugs of the same background, with per-background `prec5`, Brier and AUROC stored. It also evaluates fixed B1/M0/W scores, functional kernel updates, and a measured-state conditional predictor `Cmol` using kernel-imputed support state.
- `research/dual_core_innovation_validation_20261021/final_eval.py`, function `part_Q`: the saved final Q run evaluates the three frozen update arms at 10 steps and learning rate 1e-4, plus no update and conventional arms. The broader standalone `eval_Q.py` entry point has a three-configuration grid, but that does not mean all nine updates exist in the final saved file.

Repair1 is a different update contract. `repair_model.py::FeedbackBackend` uses all model parameters with sequential accumulated observations. `run_replay.py::transfer` reserves two drugs but reveals a functional observation of support[0] and a molecular observation of support[1]; the combined arm executes both observations sequentially. Thus repair1's f/m/both labels are not a clean trajectory/head/joint parameter-block comparison. Its report also states that these transfer changes did not change precision@5. This does not supply a cross-background residual-to-repair-benefit test.

Two genuinely unreported questions remain distinguishable from the old fixed-arm mean contrasts:

1. **Necessary opportunity:** does even a target-label-informed selector among a frozen menu have enough per-background gain over a strong comparator to reach the already declared useful margin?
2. **Available information, only if 1 survives:** can pre-repair support residuals predict which repair has greater target benefit on backgrounds excluded from fitting, beyond the strongest equally simple conventional use of that information?

An average negative effect for every fixed repair does not logically answer 1: different repairs could help different backgrounds. Conversely, a positive oracle envelope does not answer 2: the best arm may be unidentifiable from paid observations or may merely fit noisy target labels. Neither question establishes a new algorithm, a world-model advantage, an agent advantage, inheritance, or RSI.

## 2. Execute the saved-result necessary gate first

Use only the original final Q file for the primary developmental gate:
`research/dual_core_innovation_validation_20261021/RUN/final_eval/Q_per_background.csv`.
The selection/development files are separate strata and must not be pooled into a new independent final evaluation. Never import selection rows to manufacture extra final grid arms. Do not train missing configurations or acquire diagnostics before this gate is decided.

Freeze the primary endpoint to **precision@5 on the original Q target set**, with historical useful margin **delta = 0.09 precision@5**. On a top-five scale this is 0.45 target hits; the separate end-to-end Experiment E margin of 0.40 hits is not the same threshold. The Q contrast is a prediction/nomination endpoint after paid support; it is not five confirmed discoveries within the original total screening budget. All three dual-modality support assays would cost 3 F + 3 M = 4.5 units at the hypothetical M/F ratio 0.5, leaving insufficient budget for five target confirmations. Do not turn the Q envelope into an end-to-end screening gain.

For background i let v_i(a) be saved precision@5 for legal menu action a. With a frozen candidate set A and fixed comparator c, compute

`upper(A,c) = lineage-weighted mean_i [max_{a in A} v_i(a) - v_i(c)]`.

For the seven historical final backgrounds there is one stock per lineage. If additional strata contain multiple stocks per lineage, first freeze the estimand: equal lineage weighting is required; within-lineage stock choices may remain separate if the deployed selector may choose separately. Max-after-lineage-averaging would be an overly restrictive bound for a stock-level selector.

This is a deterministic finite-menu upper envelope on the **saved sample**, conditional on the stored model, target sets, labels and metric. Any selector restricted to exactly that menu has at most this sample gain over c, whether it uses residuals, a language model or target labels. It is not a noise-free population ceiling or a confidence bound for new backgrounds.

Freeze and report distinct candidate sets rather than switching their interpretation after seeing results:

- **R, pure repair:** saved M1 none/func/mol/both at the frozen update setting. This answers whether choosing among these world-model repair actions could beat `B1:none` and, separately, `Cmol` on this sample.
- **R plus B1 fallback:** R union `{B1:none}`. This is the necessary bound if the intended router may safely revert to B1. It can exceed the pure-repair envelope because fallback removes backgrounds where every world-model option loses. Therefore a small pure-repair envelope alone cannot stop a router whose actual legal menu includes B1 fallback.
- **R plus declared conventional fallbacks:** add `Cmol`, saved kernel/direct arms or a saved blend only if those are legal future actions with compatible same-target Q scores. This is an intentionally broader bound. If it fails too, it can stop that broader finite menu. If it passes, the gain could be entirely conventional and must not be attributed to trajectory repair.
- **Any broader saved update grid:** only if verified to exist for the same background/model/support/target context. Its envelope is more optimistic and can strengthen a negative necessary-gate result. A selection-stage grid, another checkpoint, a changed pool or repair1's sequential process is not such a compatible superset.

Report `upper(A,B1:none)` and `upper(A,Cmol)` separately, along with each comparator's mean and the per-background paired differences. Do not put B1 or Cmol inside the max and then call the max's advantage a pure repair effect. Equally, do not exclude a legal fallback merely to obtain a stronger STOP. The envelope must match the scope of the selector being ruled out.

Also report `mean_i max_a v_i(a) - max_a mean_i v_i(a)` for the declared A as descriptive menu heterogeneity. It is relative to a hindsight-selected best fixed menu member and is different from gain over the named strongest conventional comparator. It cannot replace the named-baseline gate.

**Stop rule:** if the frozen envelope for the actual allowed menu is strictly below delta over either required strong comparator, no selector from that menu can reach the intended margin against both on these saved backgrounds. Stop this bounded routing configuration; do not collect residual diagnostics or fit a router. Equality is a prespecified numerical-boundary case, not a robust GO. A positive envelope gives permission only to investigate available information; it is not performance validation. None of these finite-menu negatives rules out other world models, new repair actions, different data or future statistical innovations.

## 3. Oracle noise, selection and integrity constraints

The max is chosen using the same target outcomes on which it is scored. Label noise is unknown and there are no authenticated replicate IDs or repeated functional assays. Max-selection can reward noise, lucky drug composition and seed-specific behavior. A high envelope is therefore an optimistic screening opportunity, not evidence that real deployable information exists. A low envelope is still a valid conditional sample bound; it does not establish a universal population impossibility.

Bootstrap intervals around the max do not remove this target-label selection bias. More grid arms can inflate the oracle; they are useful as an optimistic necessary bound, not as evidence for a better learned method. Do not select a checkpoint, seed, endpoint, support rule, arm subset, comparator or margin after opening the numbers. If multiple fixed seeds are later considered, average each arm's utility across frozen seeds before selecting the arm; the oracle must not choose a deployment seed with target labels unless that is explicitly the legal action.

Before calculation, check column schema, uniqueness of background/arm keys, complete paired background coverage, identical n_support and endpoint eligibility, and the expected arm names implied by the saved code. Preserve input hashes. A missing Cmol row is missing, not zero; do not silently drop hard backgrounds or change the denominator. If compatible paired coverage is absent, report NOT_COMPUTABLE for that comparison. Scalar Q rows alone do not prove target-identity integrity, so use the saved run context and original code/freeze provenance; do not merge heterogeneous rows solely because arm names match.

Repeated support choices, target drugs, proteins and model seeds do not create new independent backgrounds. Confidence intervals, if supplied, are explicitly descriptive lineage-level intervals on exposed data. Do not claim a valid confirmatory p-value from treating drug/protein rows as independent. No supplementary endpoint may rescue a failed primary precision@5 gate.

## 4. Conditional minimal information test, not authorized before the gate

If the exact allowed-menu bound survives, the smallest substantive next test is a **paired differential prediction** rather than a high-dimensional multi-arm router. Start with a frozen S-versus-H contrast; include J and no-update only after the pairwise opportunity is demonstrably large. State-only, head-only and joint must keep their parameter/loss definitions explicit; state-loss-only is not automatically state-parameter-only, and joint sequential adaptation differs from one common batch update.

For a predeclared pair define target differential `D_i = target_loss_i(H) - target_loss_i(S)`; positive means S is better. This controls the easy/hard-background effect more directly than regressing each arm's raw loss on residuals. Pre-repair diagnostics may contain at most two frozen scalar summaries: source-normalized masked molecular residual and source-normalized functional residual. Scaling, masks, support choice and diagnostics are fixed using source data only. A functional squared residual from two or three binary labels conflates calibration error and irreducible binary uncertainty; a molecular residual can reflect measurement/mask/scale error. Neither identifies a biological failure cause by itself.

Conventional same-information controls must receive exactly those residuals, all legal scores and the same paid observations: source-best full fixed repair program; unchanged model; ordinary same-data refit; source-tuned shrinkage/kernel feedback; source-tuned direct conditional predictor using measured support state; simple frozen blend; and an at-most-two-feature heavily regularized linear differential predictor or a single predeclared threshold. Compare intercept-only, functional-only, molecular-only and both residuals on the same held-out lineage predictions. The incremental value of molecular residual beyond functional residual is a particularly direct falsifiable claim. A complex proposed router that cannot beat this tiny conventional predictor has no supported distinct contribution.

All fitting/regularization/action choices exclude the evaluation lineage and all its stocks. Existing repair1's model was trained on five development lineages, so scoring those five as if held out would be leakage. Reusing only its held-out selection/final backgrounds yields fewer than 17 independent lineages; evaluating all 17 would require appropriately cross-fitted base models and source-only diagnostics, a separate declared compute cost. Leave-one-lineage-out does not restore historical blindness, and its overlapping training folds make naive independent-fold significance claims inappropriate.

Report out-of-lineage differential prediction error, direction agreement when the pair has a nontrivial frozen effect, and actual selected-action utility minus the strongest same-information conventional control. Show every paired lineage result and leave-one-lineage-out sensitivity. Repeated support draws must be averaged within lineage for uncertainty and cannot inflate n. Do not search feature subsets, many thresholds, protein PCs or neural routers across 12-17 backgrounds. Any feature/direction revision is a new exposed development iteration, logged as such.

If the diagnostic model does not improve out-of-lineage differential prediction over the intercept/source-best and functional-only controls, or if selected-action gains miss the frozen useful margin after costs, stop this diagnostic contract. If uncertainty is unresolved, record INCONCLUSIVE and require new independent backgrounds; do not keep tuning until a positive exposed score appears. Even a positive result supports only a low-dimensional repair-information opportunity. New core mechanism, agent contribution, inheritance and improved-improver RSI need their separate matched-resource interventions.

## 5. Review decision

**GO only for the saved-result necessary upper-envelope calculation after its protocol is frozen.** This is inexpensive, newly informative derived evidence that does not duplicate the old fixed-arm means. It should precede all new diagnostics or fits. The historical common-support repairs themselves are old; the new opportunity is only their unreported selectable heterogeneity and, conditionally, whether genuinely available residual information predicts it. Preserve the old STOP and do not equate a positive opportunity bound with novelty.

Read-only sources: original `REPORT.md`, `PROTOCOL.md`, `ptv_models.py`, `ptv_feedback.py`, `eval_Q.py`, `final_eval.py`; repair1 `REPORT.md`, `AMENDMENT.md`, `repair_model.py`, `prepare_replay.py`, `run_replay.py`. Source-file inventory was inspected without opening saved Q scalar metrics. One initial Windows wildcard search and one nonexistent filename search failed; they were corrected to directory/glob and actual source names. No numerical operation followed those read errors.
