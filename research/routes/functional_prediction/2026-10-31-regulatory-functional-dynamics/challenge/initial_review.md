# Independent initial challenge of A1 v1

Saved before feedback, rebuttal, implementation access, or a final prior search. Date: 2026-10-31. Reviewer is a fresh subagent. Requested model/effort: inherited; effective identity, token use and cost are not exposed by runtime metadata. This is a protocol assessment, not a result assessment or novelty PASS.

## Reading and exposure

Read `brief.md` (45 lines), `a_protocol_v1.md` (47 lines), selected identity/design fields from `egi_admission/identity_design_projection.json`, source-only notebook cells in `egi_admission/local_source_projection.json`, and original XML Methods sections S21, S23, S24, S31, S32, S33, S34. Section-title enumeration also exposed non-Methods section headings, but no outcome text or numbers. S32/S34 contain published analysis settings and matrix dimensions, not matrix values. No count value, GI numerical cell, notebook output, proposer/scout note, old result, conversation, or current synthesis was opened. No HTTP request, external code/model execution, installation, API model call, or index edit was performed for this initial assessment.

## Initial assessment

Source identity and experimental ancestry are sufficiently supported to construct an explicitly new raw abundance endpoint. They do not establish that this endpoint measures a change in per-division genetic interaction. The prediction problem is interpolation within a preselected ATR-response library and one compound, with full untreated measurements, environmental singles, and approximately 80% of environmental pair outcomes available for fitting/selection. Useful screening value remains unproved. An ordinary graph residual smoother is a reasonable falsifiable probe of that limited capability; this is not an independent scientific novelty finding.

I do not yet recommend numerical launch under v1 as a fully interpretable screening protocol. The main reason is a mismatch between cross-culture transfer and the primary signed-hit event: the event still uses the source-culture response that shares the untreated denominator with prediction features. Several computational choices also need an exact freeze before the single permitted run. These objections concern the evaluation contract and its interpretation, not a request for a new scientific core.

## Specific objections

### T1 — Cross-culture prediction does not remove the source-denominator shortcut from the primary metric

**Locators:** protocol lines 19, 29, 35, 43. **Affected premise:** cross-culture transfer prevents an untreated-denominator noise shortcut from determining a screening PASS.

For a single simplified construct, write the source untreated feature as `x1 = b + u1 - t1` and its source response as `y1 = theta + d1 - u1`. Even with independent cultures and zero true environmental effect, `Cov(x1,y1 | b,theta) = -Var(u1)` when component errors are independent. The primary hit requires the source `y1` as well as target `y2`. A predictor associated with `-u1` can preferentially select source-confirmed signs and source threshold exceedances; only the target part of the event is independent of that denominator. Using both transfer directions does not fix this, because each direction again evaluates against its own feature-sharing source response. Shared guide/NTC terms add gene-level dependencies rather than remove this issue.

This is a concrete limitation even if all methods have the same allowed data: a smoother may exploit correlated baseline/control noise differently from a direct scalar regression. A five-hit margin over one permuted graph does not establish absence of that shortcut. **Minimal resolution:** make target-culture-only signed strong-effect precision the inferentially decisive event in each direction, keeping joint source/target confirmation descriptive; alternatively retain the existing event but withdraw the claimed elimination of the denominator shortcut and freeze a decisive denominator/noise falsification criterion before launch. The event definition must be settled before real responses are read.

### T2 — The new response does not identify environment-specific rewiring of an underlying interaction

**Locators:** protocol lines 7, 11, 19; original XML S24.p3, S31.p1–p4, S33.p1. **Affected premise:** a predictable nonzero response can be interpreted as a change in genetic interaction rather than a fixed-time abundance contrast.

The native study adjusts phenotypes by condition-specific population doublings and then fits query-guide quadratic nulls. A1 deliberately omits both. In the idealized multiplicative-growth case, let `g_ab` be an unchanged per-division interaction and let treatment/control accumulate `d_D` and `d_U` doublings. Then the new four-term contrast can equal `(d_D-d_U) * g_ab` even when the interaction itself is identical across environments. Original S24.p3 explicitly describes a substantial treated/control population-doubling difference at endpoint. Depletion floors and single-guide effects can create additional nonlinear deviations. Good prediction would therefore not establish rewiring, regulatory dynamics, or interaction-specific conditional sensitivity beyond the chosen abundance definition.

**Minimal resolution:** keep the explicit raw-endpoint boundary in every claimed conclusion, including any PASS; recognize baseline rescaling as a principal biological null. The existing direct baseline feature and nonlinear rival help test prediction beyond simple rescaling, but they cannot turn this endpoint into a per-division mechanistic estimand. If the intended central question requires true interaction rewiring, this endpoint cannot answer it without a different measurement contract.

### T3 — Fixed raw pseudocounts do not give sequencing-depth-invariant labels

**Locators:** protocol lines 15–23; original XML S31.p1–p4. **Affected premise:** cancellation of library-size log offsets is sufficient control of abundance/depletion artifacts.

The coefficients of the four-term contrast sum to zero, so an added common log offset cancels. However, `log(c+1)` is not equivariant under rescaling raw counts: `log(k*c+1)-log(c+1)` depends on `c`. T0-only eligibility intentionally does not prevent UT or DRUG counts reaching this floor. Reproducible baseline depletion, read depth, and guide-specific reference uncertainty can consequently generate reproducible pair-level apparent changes, including structure in the graph. Cross-culture transfer prevents an identical realized target UT counting error from being a feature, but does not eliminate shared depletion biology, common guide/reference effects, or the source-metric issue in T1.

**Minimal resolution:** predefine the promised abundance/depletion QC numerically and its consequence for interpretation before access. Report top-ranked hit support from their underlying ordered constructs and control reference coverage. Do not infer mechanism or robust assay prioritization from a PASS dominated by floor-limited constructs. This is not a suggestion to filter adverse outcomes after inspection or to choose a new endpoint later.

### T4 — The current specification is not yet an exact executable freeze

**Locators:** protocol lines 21, 23, 31, 35, 37, 39, 45, 47. **Affected premise:** the one allowed real matrix and its gate are uniquely determined by v1.

Unsettled choices that could change results include:

- Whether the 500 reproducible strong-effect detectability threshold is evaluated only on training pairs (the preceding Spearman explicitly is) or across all pairs. Reading held-pair labels for a run/admission choice must be avoided or explicitly declared before access.
- Whether every guide/NTC and NTC/NTC retention mask uses the same two-culture T0 threshold of 30; how ties/even-sized medians and pooled guide/orientation singles are computed; and what happens when a guide survives but a particular pair/control reference lacks enough retained constructs. Eligibility uses target-culture T0 values, an explicit exception to the otherwise absolute sentence that no target values enter fitting/graph/tuning.
- The meaning of “median-zero imputation”; whether the graph and SVD use the same eligible gene universe/map; SVD centering, coordinates (`U`, `U*S`, or another convention), ordering, solver and seed; profile handling at zero norm.
- “Soft-impute” is normally a singular-value-shrinkage algorithm. Only rank and iteration grids are stated here. Freeze the actual shrinkage or hard-rank operation, initial missing-entry values, diagonal constraint, centering/intercept, symmetry operation and final restoration/prediction rule, with an honest algorithm name.
- Freeze unobserved residual entries and diagonal to zero, masks and normalization in both products of the smoother; the graph permutation convention; all relevant estimator defaults/version/seed; a convergence-warning/failure policy; whether selected models are refit after validation (which changes the anchor mask).
- Define the leave-one-gene-out descriptive calculation: removing pairs from a frozen ranking and refilling top 100 is different from dropping genes and refitting. The latter is not authorized by a single fixed matrix.

**Minimal resolution:** settle these choices in a versioned protocol/code freeze and synthetic-only arithmetic/access review. These are implementation/contract clarifications, not grounds to expand the model grid.

### T5 — Sparse follow-up utility and generalization remain limited

**Locators:** protocol lines 7, 9, 27, 29, 37, 43; original XML S23.p2. **Affected premise:** an interpolation result is a useful or novel functional-screening advance.

The original focused library was selected using ATR response and the strongest guides in that nominating experiment, plus DNA-damage genes. Whole-pair holdout is appropriate for the stated within-library task, but genes/guides, source library and one ATR condition remain shared. Training plus source validation consumes about 80% of eligible pair outcomes; this is dense completion with a full untreated map and environmental singles. No new compound, cell background, gene, sparsity regime, culture batch, assay savings or biological gain is validated. Gene-additive, direct regularized, nonlinear and low-rank rivals are sensible ordinary explanations. One random graph is one negative control, not a null distribution or proof of functional specificity.

**Minimal resolution:** retain the narrow claim and cost contract. Even a strict gate PASS supports only incremental screening performance for this fixed assay information budget. No novelty PASS, time dynamics claim or broadly transferable biological mechanism follows.

## Admission findings that did not fail

- Identity projection lines 78–97 pin the six GI1 headers; lines 499–588 bind them to independent Rep1/Rep2 culture ancestry, T0, matched DMSO and ATR inhibition. Original S24.p1 supports independent transduction/passaging; S24.p3 supports the ATR regimen and day-nine endpoint. The cultures are biological replicates, not independent compound/background experiments.
- Identity projection lines 121–159 supports one shared construct identity grid, 13 NTC identities, 312 two-guide gene identities, and the source-local REV3/REV3L alias distinction. Raw input identity scope is preferable to adopting a published outcome-filtered gene subset.
- The protocol explicitly separates its new endpoint from published standardized GI and does not pretend the graph smoother or contrast is novel.
- Whole unordered pairs stay together across orientations/cultures, target responses are excluded from fitting, and test-time method expansion is forbidden. Those are appropriate protections if the frozen implementation enforces them.

## What would change this initial verdict

A precise preaccess response addressing T1 and freezing the choices in T4 can make a bounded numerical screening probe reviewable. T2/T3/T5 remain material interpretation limits after any computational clarification. A strong result would still need its raw support and ordinary explanations assessed; no result has been seen. A final bounded closest-prior search may refine overlap/importance, but will not substitute for these endpoint and access arguments.
