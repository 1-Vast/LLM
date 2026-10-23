# Independent development-data and fixed-OOF result audit

2026-10-22. **PASS for the audited scope.** This is an independent XML/metric reconstruction and static code review, not an independent reproduction of all model fits. Code: `research/decrypte_feedback_audit_20261022/audit.py`; machine result: `review/RESULT_AUDIT.json`.

## Exact data and scope checks

All10 hashes in the before-value FREEZE.json match the files actually audited, including the pre-value amendment, implementation, synthetic checks and independent review. This verifies current local bindings; it is not recovery of historical global provenance drift or independent authentication of the time before values were opened.

The auditor independently resolved workbook sheet relationships, selected the frozen48development drugs' Jurkat rows, and decoded only their A/B/U identities and J:T numeric payloads. All144rows and1584numeric cells agree exactly with DEVELOPMENT_VALUES.json, including original payload text, cell coordinates and floating values. Extracted coordinates agree in order and contain no duplicates. All primary five-dose values agree exactly. No other96drugs' responses or primary-T-cell responses were numerically decoded. The saved shared-string table was parsed structurally, but only requested identity string indexes were interpreted; Effect labels were not used. No root model module was imported.

## Independent numerical recomputation

For each of15method/budget prediction arrays, all48×3query entries have the declared shape and finite values. Independent MSE/MAE/dose-MSE/drug-MSE reconstruction checks795scalar components with maximum absolute difference0. The loss targets are exactly10/100/1000nM; supports are B0none, B1highest, B2lowest+highest, with no overlap.

All14stored paired comparisons were reconstructed using independently formed per-drug squared-error differences. Bootstrap uses10000draws, seed20261022,42scaffold groups and equal probability of drawing each group; every drawn group's drugs are retained and normalization divides by the number of drawn drugs. The auditor formed explicit drug weights from group multiplicities rather than reusing the root group-total calculation. Means,95%intervals, adjusted97.5%intervals, dose directions, positive-drug counts, largest absolute-gain drug identities and deletion means all agree (maximum absolute difference1.3877787807814457e-17).

The gates remain **B1PASS / B2FAIL**, unchanged from the amended frozen rule. B1selected versus B0selected mean MSE gain0.0128533250; adjusted interval[0.0020420856,0.0300054199], all three dose-wise mean gains positive,34/48drugs improve. Individually deleting each of the three largest absolute-gain drugs leaves positive average gain. B2gain0.0099501579 has adjusted interval[−0.0021622940,0.0272857755], so fails despite positive mean and all three dose directions. No thresholds or menus were changed by this audit.

## Static implementation / selection review

Inspection ofrun_pilot.py confirms:

- The outer training set excludes every member of the target scaffold group; inner validation excludes every member of that inner group from the remaining source set. Per-target inner errors are aggregated equally over drugs.
- Prediction reads source response rows fromtrain and target responses only from explicit target_support. Covariances, output means, support scales and kernel-centering statistics use the actual current source fold. Target-query labels appear in evaluation/inner validation risk, not in that target fold's fit or selection.
- Hyperparameter ties retain listed grid order. Per-budget method selection retains simple/gaussian/direct/library order. Cached entries include exact ordered source indexes, target index, budget, method and hyperparameter; no fold identity collision was found.
- B1/B2portfolios are separately selected at their own budget. The auditor independently checked all126outer portfolio-selection records against stored source inner scores and their chosen method's prediction rows. This is consistency verification of saved inner scores, not independent recomputation of those scores.
- Missing-structure chemistry behavior, fixed grid, variance floors, query/support indices and bootstrap quantiles match the pre-value amendment. Gaussian/libraryB0are both source means as declared.
- The selective root reader gates onallowed row before converting any numeric value; itsallowed identity list is frozendevelopment×Jurkat. The separate metadata/identity source is not blind to qualitative literature exposure, which remains disclosed.

The saved synthetic test changes a target's query values and checks unchanged predictions/selection for that target, plus flat-source finite behavior and support/query disjointness. It uses single-member synthetic groups, so is not by itself a multi-member-group leakage test; actual group exclusion is established here by source inspection and saved choices, not by claiming a new synthetic test was run.

No obvious implementation violation was found. I did **not** independently rerun all regressions, inner searches, fingerprint/scaffold construction or synthetic model tests. Model arithmetic remains supported by source review and the root execution, with independent data and result arithmetic verification as above.

## Interpretation and remaining limits

This is a positive development result for predicting published functional entries with ordinary feedback conditioning. The interval is conditional on fixedOOFpredictions and these observed curves; it does not include full training/selection or measurement uncertainty. The development gate licenses further source/mechanism investigation, not biological replication, functional assay-cost superiority, clinical utility, world-model necessity, inherited-rule benefit orRSI. B2portfolio failure does not imply additional information is inherently harmful: it tests a particular finite learned/selected procedure, and B2could always implement a B1policy if its program explicitly allowed ignoring the low-dose entry.

The root protocol requested error concentration at high-response tasks but did not freeze a numerical definition ofhigh-response. Current summary provides all per-drug errors and ranges; no single threshold-based concentration statistic was audited or silently invented. If reporting concentration, label a transparent descriptive rank-based analysis as such, preserving the primary whole-population result and frozen gate.

Normalization compatibility is not equivalent to authenticated dose-local experimental acquisition; no repeat/noise model was established. Remaining96responses stay unopened. The next molecular experiment requires its own real connection and same-information contract; this audit does not reopen the previous profileMAP/OED noveltySTOP.

Audit command completed successfully inmaestro Python via`-B`; no bytecode/test files outsideresearch were created. `git diff --check` for this audit/review scope returned no errors. Audit/script evidence should be included in the root's final local bindings.
