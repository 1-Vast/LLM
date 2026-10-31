# Replication and label construction contract

Status: source/design admission only. No count value or GI numerical cell has been opened. This document does not authorize numerical fitting. The machine-readable counterpart is `replication_label_contract.json`; exact files, columns, sample IDs, NTC names and guide identities are in `identity_design_projection.json`, `sample_binding.tsv` and `guide_identity.tsv`.

## Native object

For each of five conditions, the author source normalizes each biological replicate's construct counts to its matching T0, centers on NTC-NTC controls, divides by that condition/replicate's culture doublings, intersects passing constructs and averages Rep1/Rep2 phenotypes. AB/BA is then averaged, the query-specific quadratic is fitted to all paired phenotypes and residuals are scaled by query NTC residual SD. Gene maps average guide combinations. Consequently:

- Native pooled-map GI is not an average of independently fitted replicate-GI maps.
- A native environmental delta subtracts two separately fitted and scaled maps, not four raw log fitness terms.
- The deposited notebook exposes per-replicate processing paths, but commented Rep1 generation/output cells prevent any clean-run claim from static inspection alone.
- The native fit uses held-out double phenotypes if applied to the entire matrix. Training labels can depend on held-out pairs through shared query fits. Published fixed derived-map benchmarking must declare this coupling; strict raw-response holdout requires a different construction.

## Feasible new count endpoint

The design supports this symbolic alternative, to be frozen and challenged by the coordinator before computation. Let `C[a:b,c,r]` denote a count for the exact ordered guide pair, condition and replicate; `N` is the 13 source NTC guides; `u(e)` is the within-batch matched vehicle arm. Choose a fixed positive pseudocount `p` and fixed validity/aggregation rules before numerical access.

`D[a:b,e,r] = log2((C[a:b,e,r]+p)/(C[a:b,u(e),r]+p))`

`Q[a:b,e,r] = D[a:b,e,r] - mean_n D[a:n,e,r] - mean_n D[n:b,e,r] + mean_(n,m) D[n:m,e,r]`

All means here use exact source NTC identities with fixed equal weights. A symmetric guide-pair label can be `(Q[a:b]+Q[b:a])/2`; a gene-pair label can average its fixed guide combinations. The coordinator must settle missingness and exclusions before calculation. Target double counts construct the sealed label only. They must not fit a whole-query reference, features, imputation, scale, pair selection or hyperparameters.

This unscaled matched endpoint contrast is an environmental change in double-vs-single **differential enrichment**, not nativeGI. With identical log-count pseudocount construction, it equals subtraction of treated and reference T0-based enrichments because the same r-specific T0 cancels algebraically. It does not cancel when separate treatment/reference population-doubling divisors are introduced. Four contrast coefficients sum to zero, cancelling additive log-depth offsets for exact log abundance; pseudocount placement can still introduce depth dependence and must be fixed. A per-doubling version is a different endpoint and requires the original condition/replicate growthScores, not the unscaled formula above.

If target-environment gene-NTC singles are used as prediction features, the task is explicitly conditional on these measured singles. Their many constructs are within-culture measurements. An algebraic label does not make them independent cultures or identify death, adaptation, resistance or a mechanistic transition.

## Replication and grouping

There are two transduction/passaging biological replicates per batch. Pair each treated arm with the same batch and replicate's vehicle and T0. GI1 controls support ATR; GI2 controls support both etoposide and glucose deprivation. The latter contrasts share control noise and ancestry. Preserve this covariance; do not count the two environments, guides, AB/BA, NTC partners or matrix triangles as independent cultures. T0 is seven days after transduction and the final endpoint nine days later. There is no post-intervention trajectory.

Freeze unordered whole-gene-pair groups across all guides and both vector orientations. State whether the raw 313-gene or processed 303-gene identity universe is used. The 313-gene set includes one single-guide gene, CSRP2BP. Raw identity presence does not certify measurable depth or finite labels. Filter/missingness rules, biological replicate agreement, control nulls, practical-effect thresholds and useful headroom remain unaudited.

## Required coordinator decisions

Freeze development/held-out environments, the pair split, endpoint and scale, pseudocount, guide/NTC/orientation weights, count support and missingness rules, prediction-time measurements, ordinary baselines, null/noise and prioritization gates before any outcome access. Independently challenge the source/label dependence and protocol arithmetic. Any subsequent result is an internal known-environment held-pair test under this selected library unless a stronger independent resource is authenticated. Do not use unresolved MMC member identity, selected validation outcomes or historical protected outcomes to choose the endpoint or model.
