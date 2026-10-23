# Exact diagnostic result review

The single pre-frozen Fraction execution completed successfully. With the stipulated stationary response y=x, an intercept-only predictor and target input pointmass at +1, the original two-point unweighted fit has theta=0 and target squared risk=1. Adding eight negative-action observations changes the fit to theta=-4/5 and target risk=81/25. Ordinary oracle known-design importance weighting gives theta=1 and risk=0. All three exact empirical derivatives vanish, and oracle weights sum to 10.

This is a counterexample to the inference that deterioration after adding observations requires a changed conditional response law. A misspecified model and a changed empirical action distribution suffice. It does not establish the cause of the actual OLA deterioration, identify a biological or measurement change, or validate an acquisition policy.

The weighted result uses declared exact design probabilities, not estimated weights from biological sampling logs. It does not execute or validate the proposed regularized moment-matching QP. In particular that penalized QP need not recover these oracle weights, and moment matching alone neither identifies conditional shift nor certifies overlap. The oracle comparator is an ordinary method, not our innovation.

Protocol and script were hashed before this execution in MATH_FREEZE.json. No biological data, old experiment imports, tuning, HTTP requests or API calls were used. No execution failure or retry occurred.
