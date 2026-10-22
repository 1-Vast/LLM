# Residual writeback equivalence audit

2026-10-22. Root preregistration before running this audit. This addresses the
first explicit construct in the independently drafted `ADVOCATE.md`, not an
unknown future method. No source response values, HTTP, model API or fitting to
biological data is used. It is an algebra/implementation check, not held-out
generalization, performance, drug utility, inheritance or RSI evidence.

Test the claim that gene-coordinate Gaussian residual writeback induces exactly
the same drug predictions as a same-information kernel posterior. Include full
rank, dependent drug features, zero features and rank-deficient covariance;
noise variances 0.01, 0.1 and 1. Check a batch update and two query orders of
sequential mean/covariance updates against the same batch posterior. All arms
share features, covariance, mean, observations and noise. Do not compare against
an incorrectly fixed covariance or repeatedly reuse a feedback observation.

Success: every maximum prediction discrepancy is below 1e-9; a negative control
that omits a nonidentity covariance produces a discrepancy above 1e-3. Failure:
retain numerical output, identify which claimed equality failed and do not
declare equivalence on that case. Use a fixed random seed 20261022, 7 genetic
coordinates, 9 drugs and five distinct queried drugs. No adaptation after
viewing results. The ordinary mutation-selection equation in the second
construct is already an explicit conventional model; this audit does not test
its biological assumptions or approximate every future evolutionary model.
