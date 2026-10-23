# Independent raw-CSV reconstruction of the frozen weekly diagnostic

2026-10-23. **PASS_ARITHMETIC_AND_SCOPED_GATE / ORDINARY_RECURRENCE_ONLY_NO_NEW_CORE_GO.** Independently rebuilt the diagnostic from the original commit-pinned CSV using a separate standard-library program, without importing or executing root's implementation. Read the frozen protocol, root's saved forecasts/results and raw CSV; this is independent calculation, not blind inference. No critic result audit was read before sealing this audit. No new prediction rule, fit, numerical experiment, API call or outcome search was performed.

## Actual audit

Code research/public_recovery_task_20261023/source/audit_result.py parses24design rows directly and checks four complete sample/schedule groups with labels1–6. It computes all20condition/time means with Decimal accumulation, every valid/missing/nonfinite/negative tally, baseline ratios, the four exact frozen formulas, all32method-by-condition-by-horizon errors, four-method MSE/MAE summaries and the strict two-intermittent-group gate. Decimal-to-float conversion and independent operation ordering deliberately differ from the root arithmetic.

Every condition/time contains six finite values; all120readouts are valid with no missing/nonfinite/negative entries. Consequently no individual-value filter, author7000cutoff, condition deletion or epsilon was required. The original7015.739value remains in the V600E Continuous day21 mean; this confirms that the author's excluded outlier was not silently removed in this diagnostic. CSV SHA256 is0370b090a0a81a55542616c25008fda7b0c23f000fb7797f9ac1b966848979b1.

All256compared numeric fields agree within fixed1e-12absolute/relative numerical tolerance; maximum absolute difference is2.842170943040401e-14. There are zero arithmetic or categorical discrepancies. Full rebuilt values, counts, errors and comparisons are retained in RESULT_AUDIT.json. All current bytes match the hashes in NUMERIC_FREEZE.json; the saved PREFIX_FORECASTS.json matches PREDICTION_SEAL.json. These hashes authenticate saved current bytes, not inaccessible outcomes, original assay truth or independent proof of chronology/query isolation.

| Frozen method | Day28 MSE | Two-horizon MSE | Day28 MAE |
|---|---:|---:|---:|
| Persistence |20.619102|16.655952|2.407817|
| Global exponential |10.207517|9.801355|1.993320|
| Latest interval |19.514912|13.313735|3.052335|
| First cycle |1.368184|3.654614|0.861854|

The gate correctly passes: in VectorControl Intermittent, cycle two-horizon MSE0.011055 is below latest-interval37.020041; in V600E Intermittent,2.882080 is below4.509580. It is a comparison against one fixed ordinary extrapolator in each intermittent group, exactly as frozen, not all-method superiority.

## Interpretation and strongest limitations

The most consequential limitation is visible in the full endpoints: in V600E Intermittent, persistence has lower two-horizon MSE1.076988 than cycle2.882080 and lower day28MSE0.222201 than cycle2.751433. The cycle rule predicts a day21ratio2.044738 whereas the observed group ratio is0.309018. Thus the aggregate table does not establish uniformly accurate phase prediction, superiority in every group or every biologically interesting condition. The gate was narrowly relative to latest-interval repetition and must stay narrow.

Continuous cycle equals latest-interval by definition. Intermittent cycle day28 equals global exponential day28 by definition. These identities reduce the number of distinct predictions and are not extra independent validations. All rules predict zero for the VectorControl Continuous query because its day14mean is zero; the observed released query is also zero. A zero CTG-derived estimate does not prove no physical cells remain. The common initial values across schedules and the unresolved destructive-well/replicate mapping preclude treating the24rows or8query endpoints as independent biological experiments.

This is prediction of a released CellTiter-Glo-derived assay response ratio. Neither accurate physical live counts, individual death, resensitization-state identity nor a reversible cellular world has been validated. The actual500nM on/off schedule is known, while300nM biological cohorts remain unqualified. No future-calibrated ProcessData/growth_rates matrix or author full-trajectory model fit was used in the rebuilt formulas.

The completed positive is a reproducible ordinary recurrence calculation on four exposed-development group readouts, with a correctly implemented predeclared gate. It is not a discovered new algorithm, independent confirmation, improved updater, strong-direct/model-refit/CL/AL/equal-budget-search comparison, agent contribution, inheritance effect, joint gain or improved-improver result. Full research goal remains ACTIVE / NOT_ACHIEVED. Retain the scoped positive and the V600E persistence counterexample; do not rescue or expand the recurrence configuration based on these outcomes.
