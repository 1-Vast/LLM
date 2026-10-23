# Conditional covariance: exact zero-innovation comparator

Parent supplied the precise inference identity; source accepts it by symbolic substitution, without another label read or fit:

prediction = mu + scale * Sigma[:,S] (Sigma[S,S] + I)^(-1) z_S.

For the same purchased index set S and query mask, substituting z_S=0 (each purchased drug's source-expected standardized response) yields prediction=mu exactly. Therefore source mean is also the same conditional solver's zero-innovation comparator, not only a separate lower-capacity program. In this fixed replay, the reported 23.49% MSE and 15.07% shortlist-regret improvements can legitimately be described as the **algorithm-specific predictive utility of the numerical support deviations from source expectation**, relative to zero innovation under the same mask.

This does not isolate causal value of measuring or purchasing assays, establish a benefit for arbitrary samples/panels, randomize missingness, or separate shared biological sensitivity from measurement factors. The existing availability/missingness selection constrains the target population and panel. It would be inaccurate to claim that the difference is wholly due to mask differences, since the zero-innovation substitution holds the mask fixed. The earlier strongest-caution wording in result cross-examination is narrowed accordingly; no new model, empirical comparison, or causal attribution is introduced.
