# Independent initial B outcome interpretation

Date: 2026-10-30. Saved before reading the parent decision, final report, or any numerical-verifier conclusion.

## Evidence boundary

I read the frozen base/amended B protocols and only the authorized completed artifacts in `data/processed/virtual_cell_four_directions_20261030/pilot_b_maestro`: `result.json`, `summary.csv`, `scores.csv`, `source_precision.csv`, and `selection.json`. I independently aggregated the completed scores; no model was refitted, no training hit arrays or protected evaluation rows were accessed, and no new source search was performed. Arithmetic output is saved separately as `review/b_outcome_independent_numbers.json`.

The completed artifacts contain all five outer folds, 15 methods, 1,229 eligible tasks and 114 eligible canonical source groups, from the run's stated 1,231 input tasks and 115 input groups. Every method has the same all/rare task and source denominators. Eleven eligible tasks with zero rare hits were retained. Every inner validation score is finite, so the previously identified no-validation-task fallback was not triggered. Recomputed summary and source-precision values agree with the saved tables to about 1e-16. This confirms aggregation consistency, not full reconstruction of model fitting or proof of feature/label provenance; those remain the separate verifier's remit.

## Main finding and decision

**The candidate does not meet the frozen continuation gate. Stop this candidate's current capability claim and preserve the scoped negative.** The strongest supported alternative is that ordinary source weighting and conventional context-conditioned predictors already account for the useful prioritization available in this test. There is a retrospective context-associated signal, but no demonstrated need or advantage for the proposed scaled low-rank construction.

Source-macro ordinary P@50, where 50 picks are divided by 50:

| Method | Rare eligible genes | All-library genes on the same tasks |
|---|---:|---:|
| Full-rank ridge | 0.11575 | 0.20782 |
| Source-balanced rationale frequency | 0.11190 | 0.21954 |
| Nonlinear tree | 0.11074 | 0.21052 |
| Candidate scaled low-rank residual | 0.10086 | 0.20480 |
| Source-balanced global frequency | 0.10033 | 0.20993 |
| Unweighted global frequency | 0.08264 | 0.20587 |
| Permuted-context candidate | 0.08083 | 0.19361 |

Full-rank ridge is the best aggregate rare baseline. The candidate trails it by **0.01489 absolute, or 12.86% relative**. At this source-weighted aggregation the means correspond to approximately 5.04 recorded rare hits per 50 candidate picks versus 5.79 for full-rank ridge, a deficit of 0.74 hits. These are retrospective expected counts under the reporting weights, not prospective experimental yields.

Using the frozen 2,000 paired resamples of canonical groups, seed 1030, the candidate-minus-full-rank difference has a central 95% interval **[-0.02752, -0.00357]**. Every outer-fold difference is negative: -0.00069, -0.02972, -0.00194, -0.03983, and -0.01513. Individual-source performance is heterogeneous (34 positive differences, 41 ties, 39 negative differences), but neither the aggregate nor the fold criterion is close to a pass. These intervals are conditional summaries of the observed cross-fitted predictions; selecting the rival from this panel and shared training preclude a confirmatory biological inference.

## What the context and rarity controls do support

The real-context candidate exceeds its fixed permuted-context diagnostic by **0.02004** rare P@50 (conditional source-bootstrap interval [0.00816, 0.03236]). This supports an association between the allowed context and prediction quality for this construction in these historical tasks. It does not identify which field contributes, establish prospective availability of the annotations, or show that cellular background rather than phenotype/screen type carries the signal.

Against the stronger source-balanced global propensity, the candidate gains only **0.00053**, with conditional interval **[-0.00844, 0.00985]**. Its larger apparent gain over unweighted global frequency (+0.01823) therefore cannot be presented as evidence that a learned conditional low-rank model is necessary. Source balancing alone raises the global comparator from 0.08264 to 0.10033.

Conventional contextual models also carry useful internal signal: full-rank ridge exceeds balanced global frequency by 0.01542, and balanced rationale frequency exceeds it by 0.01157. Their conditional paired intervals are [0.00105, 0.03065] and [0.00215, 0.02100], respectively; these additional diagnostic comparisons are exploratory. Full-rank ridge exceeds balanced rationale by only 0.00385, so the identity of the numerically best model does not establish that full-rank regression itself is uniquely necessary. The evidence favors keeping strong ordinary baselines, not selecting a new mechanistic explanation.

The source-macro random-ranking expectation on rare libraries is 0.04768. Candidate enrichment above that expectation shows useful historical ranking structure, but all leading simple rivals also exploit that structure. Being above random or above the weakest global prior is insufficient for the frozen scientific question.

## Phenotype and drug utility

Both required subsets are large enough to evaluate; failure is not due to the minimum-ten-group rule.

| Rare-gene subset | Tasks / canonical groups | Candidate | Best subset baseline | Candidate difference |
|---|---:|---:|---:|---:|
| Non-fitness | 321 / 90 | 0.07352 | Coarse-phenotype frequency: 0.09093 | -0.01741 |
| Drug / Chemical / Environmental Response | 209 / 49 | 0.08643 | Coarse-phenotype frequency: 0.10764 | -0.02122 |
| Fitness (diagnostic) | 908 / 33 | 0.17877 | Balanced rationale frequency: 0.21801 | -0.03924 |

Within non-fitness and Drug, the candidate also falls below source-balanced global frequency (0.08226 and 0.09897, respectively). Its real-minus-permuted differences are small in these subsets: approximately +0.00140 for non-fitness and +0.00209 for Drug, versus +0.06859 in Fitness. Because source groups can contain multiple categories, these group counts overlap; they are not independent subgroup experiments or additive counts. The pattern is consistent with much of the observed context diagnostic being associated with the fitness tasks, and does not support improved drug-conditioned rare-gene prioritization.

The Drug category is a gene-perturbation response endpoint. It does not provide a calibrated small-molecule response curve, an untreated-versus-treated causal gene dependency, or a drug target's clinical efficacy. No claim about selective drug-induced dependency follows from the candidate's precision here.

## Gate and sensitivity

The candidate fails the required +0.05 absolute advantage, +20% relative advantage, positive bootstrap lower bound, improvement in at least three folds, and superiority in both non-fitness and Drug. It passes the real-versus-permuted sign check and the all-library noninferiority tolerance against the fixed rare-best rival (all-library difference -0.00302, within the -0.02 allowance). Passing those two checks does not offset the other failed conjunctive requirements.

The preset exclusion of source component 29083409 and source 30971826 leaves 510 tasks and 112 eligible groups. The candidate remains below the same best baseline: **0.09701 versus 0.11217**, difference **-0.01516**. The scoped negative therefore persists after removing those two sources from the score. This is a score sensitivity with the original fits; it does not certify that all learned effects of large sources or all provenance dependencies have been removed.

Task-weighted candidate rare precision is 0.24031 rather than the primary source-macro 0.10086, illustrating the influence of large studies. The full-rank value is 0.24125 and balanced rationale is 0.26194 under task weighting, so changing to that secondary weighting does not reveal a candidate advantage either.

## Scientific interpretation ceiling and next action

The conservative five-publication calibration component and whole-publication folds improve the internal comparison. They do not certify independently prepared cultures, donors, laboratories or processing pipelines across every remaining source. Hit calls have heterogeneous source-specific significance criteria; benchmark QC, direction curation, gene-symbol harmonization and valid-score masks were retrospective. Rare training hit frequency does not demonstrate cell specificity, nonessentiality, causal selectivity or biological novelty. Missing measurements were mean-imputed residuals, so fitted modes can also reflect assay/library coverage rather than pathways.

This test does not isolate why the candidate loses. Compression, variance scaling, finite rank, regularization and noisy text are possible explanations; no matched factorial ablation establishes one as the mechanism. The chosen ranks (64 in four folds, 16 in one) are descriptive selection results, not grounds for expanding the grid after scores. Nor is the result a universal impossibility statement about low-rank methods or virtual cells.

The appropriate action is to record **NOT_PASSED for this frozen B candidate**, retain the verified data/protocol/predictions and strong-baseline insight, and avoid presenting it as an externally validated capability or a reason to promote core/Agent work. A scientifically different future candidate would need its own prospective justification and frozen protocol; the present result does not authorize reopening official validation/test or LaTest under the claim that B1 passed. Independent arithmetic/leakage verification should finish before any final scientific report is accepted.
