# Pre-response normalization confound review

2026-10-23. Root explicitly requested this supplement before the source state falsifier. No new matrix values read; the formula below is mathematical, not fitted evidence. The previously sealed independent and cross files remain unchanged.

Let a single coordinate in linear CP10K obey exact additivity, C_ab=C0+d_a+d_b, with nonnegative observable endpoints. Define single log effects x_a=log(1+C0+d_a)-log(1+C0), and similarly x_b. The mixed log contrast is

    r_log = log(1+C0+d_a+d_b)-log(1+C0+d_a)
          - log(1+C0+d_b)+log(1+C0).

For small effects, r_log approximately equals -d_a*d_b/(1+C0)^2, while x_a*x_b approximately equals d_a*d_b/(1+C0)^2. Thus the proposed diagonal law can give theta approximately -1 from coordinate transformation alone even when the underlying linear CP responses are exactly additive. A strong log-space result cannot establish biological mixed curvature or a causal regulatory interaction.

Prespecify and save the linear CP10K state endpoint from the same cells, with the same single/control definitions, equal gemgroup weighting, pair splits, fixed source panel and model menus. Repeat the same contrast/product predictions there as a sensitivity, not as an endpoint to choose after inspection. A primary log result stays primary whether the CP result is favorable or unfavorable. If only log wins, the appropriate interpretation includes transformation-induced predictability; no gene/endpoint selection rescue follows.

Important implementation detail: mean(log1p(cell_CP10K)) and log1p(mean(cell_CP10K)) are different estimands. The linear CP endpoint must be separately accumulated before the per-cell log, not reconstructed by exponentiating the mean log. For residuals use the same declared averaging order within each endpoint. Data QC and observation membership must be common.

Linear CP itself retains compositional closure: changing total RNA changes relative CP fractions, so additive absolute abundance need not be additive in CP. Passing both endpoints still only supports a useful descriptive restriction in the declared normalized observation space, not identified biological curvature. No currently available absolute-molecule calibration resolves that claim.

An analytic CP-additivity-transformed-to-log predictor could be a future comparator, but cannot be silently added after values. It needs a prospective handling rule for negative additive CP predictions and for the noncommutation of cell averaging and logs. The fixed linear CP sensitivity is a sufficient immediate scope guard without inflating this single falsifier into a broad preprocessing search.
