# Frozen scientific falsifier: shared diagonal mixed response

2026-10-23. Full objective ACTIVE / NOT_ACHIEVED. This is a prerequisite source-state structure test, not a substitute for functional drug/target decision, agent, inheritance or RSI validation. Three independent reports and actual cross discussions conditionally permit a small empirical test of a concrete restriction, while declining novel-algorithm promotion. No new primitive is required to falsify a scientific constraint. Self-copying the same objective under a different model name cannot settle the constraint's finite-sample usefulness; ordinary same-information alternatives still can.

## Hypothesis and legal data

For each of 103 fixed named target-expression coordinates k, the mixed response is predicted by one shared coefficient:

    r_ab,k = theta_k * q_ab,k;
    q_ab,k = mean_g[(mu_a,g-mu_c,g)_k * (mu_b,g-mu_c,g)_k];
    r_ab,k = mean_g[(mu_ab,g-mu_a,g-mu_b,g+mu_c,g)_k].

The restriction says cross-coordinate inputs are unnecessary for this prediction; it is a conventional diagonal second-order identification hypothesis. It is not an independently identified intracellular mechanism or a novel estimator. Cross-gene curvature, selection, guide differences and transformed coordinates are plausible failures. The prior potential and inverse-update STOPs are unchanged.

Use exactly the 73 source unordered pairs with identity-QC double cells in support/SOURCE_PAIR_METADATA.csv, chosen before expression access. Use the unchanged 103 exact raw readout indices of reciprocity_resolution/IDENTITY.json, never expression aliases. Every guide/mirror/cell of a pair stays in the same outer fold. No functional, development or protected outcome file is read. Source pairs were selected by the original study and source functional values influenced previous research: this is exploratory internal capability, not blind confirmation.

Identity QC and the three controls match the prior single extraction. Apply per-cell UMI >=2000 from all raw genes; any required pair/single/control-by-gem group empty afterward stops extraction without removing that group or changing the threshold. Preserve all eight gemgroups separately and both mean per-cell log1pCP10K and mean per-cell CP10K. They are not interchangeable transformations of the same mean. Existing single orientation selection is retained; multiple double guide strings remain a disclosed pair mixture.

The efficient parser materializes every numerical triplet in each of two full raw matrix passes, including excluded cells. This is numerical contact, not a claim that non-source RNA remains unopened. Only fixed source pair/old single/control totals and their 103-readout state sums are accumulated. No heldout functional label is touched. The already downloaded whole-pool data are charged as complete retrospective extraction; no sparse wet-assay cost saving or adaptive experimental query is claimed.

## Independent-noise directions and coordinate sensitivity

Primary: A={1,2,3,4} provides single-state inputs; B={5,6,7,8} provides mixed-state targets. Center within gemgroup first, then weight the four groups equally. Never use target pair cell counts as input weights. This separates input single/control measurement noise from the single/control terms subtracted in the target. B-to-A is a fixed required direction sensitivity, not an alternative chosen after observing scores. These are technical batch strata in one K562 context, not independent biological tasks.

Primary coordinate space is mean per-cell log1pCP10K. Repeat exactly the same recipe in mean per-cell CP10K as a prespecified sensitivity. Even additive CP response can produce a negative diagonal product in log coordinates; CP also has compositional closure and cannot authenticate absolute biological curvature. Do not choose the favorable space afterward or claim that a predictive coordinate law is causal biology.

## Models, selection and evaluation

Five outer folds take the first8 bytes of SHA256('MAESTRO_MIXED_DIAGONAL_V1|'+pair), interpreted as an unsigned big-endian64-bit integer, modulo5. Within each outer training set sort by the first8-byte big-endian value of SHA256('MAESTRO_MIXED_INNER_V1|'+pair), use first75% for inner training and last25% for validation. This pre-execution clarification matches the original predictor implementation; the earlier reviewed wording is retained in STATE_PROTOCOL_PREFIT_SNAPSHOT.md. All scale, intercept and fit parameters use only the corresponding train split; assess labels never enter selection.

Compare additive state (zero residual), training mean residual, diagonal law, full q-vector-to-all-readouts ridge, direct linear ridge on mean single sums and absolute differences, and full symmetric bilinear ridge. The full bilinear feature is mean_g sym(s_a,g s_b,g^T); its diagonal is exactly q. Do not use outer products of averaged singles instead. Add a fixed50/50 mixture of the independently inner-selected diagonal and q-ridge predictions, without choosing its weight from outcomes.

The diagonal law has no intercept and uses one common relative ridge shrinkage: theta_k=sum(q_k r_k)/[(1+lambda)sum(q_k^2)], zero if the denominator is zero. Other ridge designs center/standardize each feature on train, use K=XX^T/dimension and fit all readouts with a train target intercept. Shared lambda menu [.001,.01,.1,1,10,100], minimum validation MSE with first-grid tie break; then fresh outer refit. Fixed finite menus have equal candidate count, not equal computation across models. Report costs and retain all predictions/selections. No outcome-driven optimization, feature, panel, penalty or fold changes.

Primary metric is mean squared mixed-state error over all heldout pairs and all103 readouts. Compare the candidate with the strongest conventional pooled OOF MSE (a predeclared conservative posthoc envelope, not a deployable model selector), from the exact list additive, mean, q_ridge, linear_ridge, bilinear_ridge, fixed_mixture. A source predictive gate passes only if log A-to-B diagonal MSE is >=5% lower and improves in >=4/5 folds against that conventional arm, AND reverse-log direction is strictly better than its strongest conventional arm. Five percent is a design margin, not measurement-calibrated significance. Otherwise STOP_CURRENT_DIAGONAL_MIXED_LAW_CONFIGURATION. Report CP results regardless; log-only support cannot establish coordinate-independent biological law. No significance test treating genes/cells as independent trials.

Passing this gate permits only consideration of a separately reviewed function/ranking falsifier. It does not qualify a new algorithm, world-model necessity or RSI. Failure closes the fixed diagonal law without trying cross terms, new coordinates, thresholds or a fitted head to rescue these outcomes. Later nonlinear/multitask candidates need a substantive new restriction and new protocol. Strong direct prediction, refit, CL, AL, mixture and equal-budget program search remain mandatory for any eventual core utility claim; this precursor does not pretend to have tested the unexecuted agent/RSI comparisons.

## Execution and review

HEAD47a0e2dea5a7dd42379fa17eb3621caf6bd0114c. Maestro Python -B; one CPU thread for fitting, deterministic hashes, no GPU/random training/API/wet experiment. Existing extraction and prediction start receipts forbid duplicate execution. Review code/protocol before freezing hashes and extracting. Run meaningful synthetic access/symmetry/heldout tests first; obtain independent saved-result arithmetic and actual result cross discussion after completion. All new records/data stay in log/, code/tests in research/. Historical global provenance drift remains unresolved by local hashes.
