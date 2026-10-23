# Source-schema addendum: mean AUC plus SE

2026-10-23. Post-independent inspection only: ATTACHMENT_SCHEMA.json, PDF_CAPTIONS.json and PDF_STRUCTURE.json. Root's source message also reports the authenticated EPMC ZIP inventory lacks the separate workbook. I have not read other role opinions or root's decision, new response numbers, source PDFs or a workbook. This is a new addendum; the independent opinion is not edited.

## What changed

Verified metadata contradicts the tentative assumption that mmc2 contains TableS7. The authenticated DOCX is methods/resources, with no embedded object. Caption extraction from mmc1 page21 identifies TableS7 as "Summary table of 100 compound mean AUC + SE"; page1 says supplementary tables are a separate Excel file. mmc4 repeats that table legend as part of article-plus-supplement content. The inspected PDFs have no embedded attachment. No actual TableS7 header, rows or values have been authenticated.

Thus the current strongest source claim is that the authors describe a summary response table, not that this retrieval has delivered a usable matrix. The EPMC package not carrying that separate workbook is an endpoint-specific retrieval gap. It does not prove the workbook is globally unavailable or absent from the publisher. Root's publisher-link investigation may change availability; it should not retroactively change this frozen source state.

## If an authentic mean-AUC table is obtained

Mean AUC can support a well-defined offline component: observe a donor's measured summary response for a small subset of eligible drugs, update a predictor, then rank or predict withheld measured summary responses for that donor. It can test transfer of an updater beyond ordinary empirical Bayes, covariance completion and refitting. The assay feedback unit is then **one drug's declared curve-summary assay**, potentially encompassing several concentrations and repeats; it is not one well or one dose unless source methods establish that equivalence. Count assay cost at that unit, and report limitations when concentration/repeat costs are unknown.

SE may describe precision of the reported mean, but the caption alone does not establish its denominator, whether independent experiments or technical wells underlie it, or whether error is independent across drugs. It therefore cannot be promoted into known Gaussian noise, an exact inverse-variance likelihood, a clinical confidence interval or an independent donor replication count. Do not fabricate replicate outcomes by sampling the reported SE. A deterministic summary-label replay remains possible without such a noise model; it measures prediction of reported means, not the reliability or value of one future noisy assay.

The main utility can be a fixed-size shortlist under the authors' authentic AUC convention, once direction and comparability are checked. High versus low sensitivity cannot be inferred from the word AUC: viability AUC and inhibition AUC have different directions. Dose range, integration scale and treatment duration must be aligned or explicitly represented, and normal/tumor selectivity needs matched donor endpoints on the same scale. The caption does not establish IC50 availability, raw concentration response, or a common complete 100-by-model matrix.

## Specific missing raw-data limitations

- Without dose points, no response-curve refitting, Hill-slope/EC50 estimation, dose interpolation or extrapolation, IC50 censoring audit, or dose-resolved intervention-response claim is justified. AUC comparisons can still be valid if the authentic integration conventions are fixed and matched.
- Without replicate/run labels, one cannot hold out a future experimental repeat, estimate passage/batch transfer from this table, check correlated plate artifacts, or estimate future measurement-noise utility. The task remains summary-label completion grouped by donor.
- Without control wells and normalization details, one cannot authenticate whether normalization is deployment-available or fitted using held-out outcomes, independently recalculate AUC, or test a claimed control-preserving update. Fixed assay controls are not inherently leakage; a global response-dependent rescaling needs separate justification or lawful reconstruction.
- Without post-intervention molecular state or timecourses, an AUC table does not identify cell-state dynamics, causal target action, recovery, adaptation or a unique mechanistic interpretation. These omissions limit WM claims, not every predictive updater experiment.
- Without actual row/column identifiers and response coverage, a budgeted replay still lacks a lawful oracle. Missing drug labels cannot be imputed and then scored as observed ground truth. An estimated summary can be an input feature only when explicitly distinguished from measured terminal labels.

## Updated methodological decision

CONTINUE_BOUNDED_SOURCE_SEARCH, NO_NUMERICAL_GO_YET. Authenticate the separate workbook and its provenance if an official route exists. Once found, expose headers/identifiers/missingness semantics under a fresh schema protocol before fitting; response access remains a separate numerical step. If the workbook remains inaccessible after bounded official-source attempts, stop this dataset-task qualification at that retrieval boundary and retain the metadata result. Do not convert a missing file into a biological null result or keep adding modules.

A genuine mean-AUC matrix could qualify a useful updater component without raw curves or new foundational mathematics. A table caption alone qualifies no numerical experiment. No new biological result, novelty clearance, world-model contribution, agent contribution, inheritance result or RSI result is asserted.
