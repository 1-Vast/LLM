# Estimand clarification after initial review

2026-10-29. This bounded clarification leaves `initial_assessment.md` unchanged. No additional source, outcome file, network request or experiment was accessed.

Independent destructive endpoint cultures can estimate schedule-specific population means at 0/48/96 hours. This requires valid matched/randomized preparation, comparable sampling and observation, and the intended complete schedule prefixes at the later endpoints. Longitudinal measurement of the same physical dish is not required for a test of a prespecified recurrence among those population means. Lack of longitudinal pairing alone does not invalidate that test.

The null must name its estimand. With `mu_k = E[Y_k]`, a mean-recurrence test can assess `mu_2 = mu_1^2/mu_0`, where `mu_0 > 0`. This is distinct from `E[Y_2 - Y_1^2/Y_0] = 0`, from a mean of within-preparation cycle ratios, and from equality of two means of such ratios. Preparation-specific multipliers can satisfy a within-preparation scalar rule while their aggregated means fail the scalar recurrence. A common multiplier across preparations would imply the mean recurrence, under the corresponding observation assumptions. These are different scientific claims.

Original P3 Sec15 defines normalized density change as `(CDt2 - CDt1)/CDt1 * 100`. Consequently, an average of preparation-level normalized changes is generally not the normalized change of population-mean occupied areas. Published mean percent changes cannot automatically be substituted for the absolute endpoint means needed by the stated mean-recurrence null, nor chained into a population trajectory without an appropriate weighting/joint-data contract. This does not establish that the unread workbook lacks the necessary information.

Raw preparation/pair identifiers determine which observations share biological variation or references and therefore affect covariance, uncertainty and resampling units. Valid independent endpoint groups can support uncertainty estimates without within-dish pairing, provided the design and actual independence are established. Pair identifiers and paired raw measurements are additionally necessary for estimands or variance calculations that specifically use within-preparation ratios/products. Row alignment alone supplies neither.

This clarifies observation design and estimands; it does not establish that a particular source layout qualifies, that its outcome satisfies or violates a recurrence, or that rejection would change a consequential decision.
