# VERIFY 61 supplemental arithmetic recheck

- status: **PASS**
- original `VERIFY_61_REPORT.md`/`.json` is preserved and remains FAIL.
- scientific_gate: **INCONCLUSIVE**

Applied `POSTRUN_CLARIFICATION.md`: raw/ridge rank by descending `-R(p,g)`, decision ranks by direct score, oracle by descending `-R(y,g)`, stable ties, and regret uses observed residualized sensitivity.

All 1,403 queries and 3 methods were recomputed from saved predictions. Maximum row errors: `{'top10_overlap': 0.0, 'selection_regret': 0.0, 'raw_threshold_hit': 0.0}`. Maximum aggregate summary error: `0`.

Worst rows: `{}`.

This is an arithmetic supplemental check only; it does not rewrite the frozen protocol, model outputs, original verifier verdict, or scientific gate.
