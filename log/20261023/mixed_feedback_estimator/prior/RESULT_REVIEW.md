# Independent saved-result review

2026-10-23. Reviewed after root explicitly confirmed extraction and prediction were terminal exit 0. No peer result report was read before this independent seal. Access was restricted to saved OOF predictions/truth, score/selection/cost/extraction records and previously reviewed code. No raw matrix, functional outcomes, development/protected profile output or model refit was accessed.

## Recomputed result and decision

**STOP_CURRENT_DIAGONAL_MIXED_LAW_CONFIGURATION.** The predeclared scientific state capability gate fails; there is no justification to add a functional head or an agent around this fixed restriction.

For log1pCP10K A-to-B, the diagonal model's pooled OOF MSE is **0.0036309922144720777**, against **0.0035264761005517715** for the strongest of six conventional controls, linear_ridge. The diagonal model is **2.963755% worse**, with **0/5** positive folds against that same conventional arm. It misses both the required >=5% reduction and >=4 positive folds.

For reverse-log B-to-A, the corresponding MSEs are **0.003958594968607071** and **0.0038584316228594566**; diagonal is **2.595960% worse**, with **1/5** positive folds. Thus the separately required strict reverse advantage also fails.

The prespecified CP10K sensitivity does not rescue the result: A-to-B diagonal is **2.8862071442997195** versus linear_ridge **1.0524632978895925** (174.233520% higher error); B-to-A diagonal is **3.9611023686441698** versus **1.4356187279042651** (175.916042% higher). One CP fold contributes particularly large diagonal error; it is retained. These numbers cannot justify dropping that fold, choosing a favorable direction/coordinate system, or searching new penalties on the exposed labels.

## Arithmetic and selection audit

The independent script recomputed all **28 pooled and 140 fold scores** from OOF_STATE.npz, including all six controls: additive, mean, full-q ridge, linear ridge, bilinear ridge and fixed mixture. Every saved score and RESULT.json score agrees to the declared numerical tolerance. Weighted fold aggregation equals the pooled metric. Additive predictions are exactly zero residual; the fixed mixture is exactly 50/50 saved diagonal/q-ridge predictions.

Pair counts are 73 with folds [15,16,14,12,16]. Independently reproduced SHA256 first-eight-byte big-endian outer folds and inner ordering. All 100 selection records have the prescribed disjoint train/assessment and inner/validation IDs. Every selected candidate is the first argmin of its saved validation-loss list, and every menu matches the fixed recipe. The first-argmin check audits the saved selection operation, not a fresh optimizer fit.

All **600 fit-cost rows** align in execution order with 500 candidate fits and 100 outer refits, including deterministic mean calculations. Breakdown: mean 40, diagonal 140, q-ridge 140, linear ridge 140, bilinear ridge 140. Recorded summed fit time is **0.649758100080362 s**; prediction wall time **1.951197599999432 s**; extraction wall time **187.63393568992615 s**. Timed fit costs are unequal and exclude extraction/design; equal menu length is neither equal compute nor equal penalty meaning. The measured cost does not alter the failed predictive gate.

The extraction receipt reports all 20,395 candidate pair cells and 40,247 single/control cells retained after fixed UMI QC, all 1,416 required groups, 103 readouts, two full raw-matrix passes. This review checks the saved receipt, not raw extraction recomputation. Raw excluded triplets were numerically materialized as prospectively disclosed; no claim of leaving all heldout RNA unopened is made.

## Review execution and correction

review_saved.py was run twice, both exit 0, without model refits. The first pass checked OOF/selection arithmetic but omitted the newly available FIT_COSTS.json from its cost inspection and reported only inferred calls. Before sealing, the reviewer added direct cost-row verification plus extraction-receipt checks and reran the same saved arithmetic. This only corrects review coverage; it did not change experimental code, predictions, penalties, folds, gate or interpretation. Final SAVED_REVIEW.json includes hashes of all seven inspected input artifacts.

## Scope

This rejects the fixed named-coordinate shared diagonal product restriction under the frozen feature, regularization, panel, split and normalization recipes. It does not establish absence of all shared mixed-response structure or failure of all nonlinear world models. The stronger ordinary linear control's modest performance is not an agent or novel-algorithm contribution. The 73 historically selected source pairs and 103 target readouts in one K562 map are exploratory, gems are batches, and the 5% gate is a design margin rather than significance. No drug-function, world-model necessity, agent, inheritance, joint or improved-improver claim is supported. Preserve previous STOPs and the full active goal.
