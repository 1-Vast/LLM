# Component-conditioning noise scope

The sealed independent report's displayed component posterior mean assumes observation noise is independent between support and query inhibitors: R_QS=0. This is the ordinary diagonal/independent observation-noise case, not an assertion that all assay noises actually satisfy it. That assumption should have been explicit alongside the formula.

For a general jointly Gaussian response with correlated observation noise, use the total covariance T=B C B'+R and conditional mean mu_Q+T_QS T_SS^(-1)(y_S-mu_S). A direct model given that identical total covariance has the identical conditional mean. One must not grant a component method correlated-noise information withheld from its direct comparator. If predicting latent noiseless means rather than observed responses, define that distinct target and use its matching cross-covariance in both implementations.

This algebraic qualification does not establish that Beat AML satisfies the assumed Gaussian/linear/noise model, does not identify a biological component, and does not authorize a new numerical fit. Original report/seal preserved. No current-phase peer report read before this correction; the scope issue was noticed during self-review and sent to parent separately.
