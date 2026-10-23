# Fixed accounting protocol before computation

Use only saved B0/B1-selected and B0/B1-study-exclusion arrays, matched to y[30:40,:,:8] from the exposed first40 cache. NPZ materializes first40 responses, no closed/reserve values exist in that cache. All inputs and script hash are written before computing results. No refits, choices, hyperparameters or correction rules.

Per cell, e[p,d]=pred−truth, q[p]=mean_d e, m=mean_p q. Three terms: G=m², C=mean_p(q−m)², D=mean_pd(e−q)². Require G+C+D equal per-cell saved MSE at abs tolerance1e-12. C includes scale error, so it is not pure ranking error. G and D cannot change pairmean ranking by definition; they are not certificates of assay calibration or biological state.

For each matched source variant, reproduce stable top89 selections and saved cell regrets. Define entrants=B1selection\B0selection, exits=B0selection\B1selection; require equal counts and (sum true means entrants − sum true means exits)/89 equal regret_B1−regret_B0 within1e-12. Record all cells' swaps, no subgroup selection or extra threshold. Truth is retrospective evaluation only; no swap selection is a deployable policy.

Report signed component improvements B0−B1 and complete per-cell values for both variants separately. Main all-source ranking improvement and sensitivity ranking deterioration must not be conflated. Stop interpretation on any identity/metric mismatch. Passing only establishes descriptive accounting, not functional improvement of a new rule, novelty, inheritance, world-model or agent necessity. Preserve all prior STOPs and protected partitions.
