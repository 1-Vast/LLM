# Deviations and disclosures

1. **Composite anchors in the gate.** `repro.py` (PLAN_P1) did not exclude the pre-combined anchor "Afatinib|Trametinib"
   (5,527 rows, colon). Its target-overlap annotation made it a "sibling" of Afatinib, Sapitinib, Erlotinib, Lapatinib
   and Trametinib.
   - Effect: the gate's target class has 1,568 replicate units instead of 1,027.
   - The secondary decomposition (`repro_decomp.py`), phase 2 and phase 3 exclude composites.
   - Without them the gate label is unchanged: the conditional (partner x line) component's line-bootstrap CI crosses 0,
     and its share is about 0.09, below 0.25.
2. **Secondary decomposition added after PLAN_P1.** `repro_decomp.py` was written after the plan and before
   `REPRO.json` was read. It ran in parallel with the gate and uses 500 bootstrap draws rather than 2,000.
3. **Phase 2 was designed after the gate.** PROTOCOL_P2 section 0 cites the gate and decomposition numbers. Its question
   (predicting partner-specific failures for unseen implementations) was chosen *because* the gate located reproducible
   structure at the partner level. It was frozen (FREEZE.json) before any held-out prediction was computed.
4. **Phase 3 was frozen before phase 2 finished.** PROTOCOL_P3 and `refine.py` were written and frozen (FREEZE_P3.json)
   while phase 2 was still running and no `LOFO_*.json` existed. Phase 3 ran before phase 2 finished.
5. **Evaluable implementations.** 37 drugs have a target-overlap sibling in the same role, but some folds have no
   evaluable cell: the sibling was never measured with the same partner in the same line (e.g. Camptothecin/Irinotecan,
   Oxaliplatin/Temozolomide, Nilotinib/Dasatinib). Phase 2 and phase 3 statistics use only folds with evaluable cells.
6. **Missing experiment.** The CHEK1-vs-CHEK2 inhibitor series described in the Jaaks paper is not in the public
   fitted file. Only AZD7762 is screened, so no CHEK family exists for this study.
7. **All data exposed.** Jaaks 2022 (original and validation screens) was opened by MAESTRO studies in October 2026.
   Every result here is development evidence. The validation-screen replication in phase 2 is a separate measurement,
   not an untouched tier.
