# Independent initial challenge of A version 1

Date: 2026-10-30. Initial verdict saved before discussion with the coordinator, implementation of A, or any A model outcomes. Reviewed protocol hash and metadata/source receipts are recorded in `a_protocol_initial_receipt.json`.

## Verdict

**AMEND BEFORE EXECUTION; a bounded retrospective countertest is defensible.** There is no scientific reason to prohibit the one cheap matrix once the response-panel definition and comparator set below are frozen. It can test whether a fixed rank-32 output projection improves native-call recovery over the specified ordinary prediction panel on these already exposed development compounds. It cannot identify a distinct teacher mechanism, extra functional information, a novel algorithm, general non-forgetting, pharmacological mechanism, or practical laboratory benefit.

The narrow test has useful negative outcomes: projection may fail, ordinary concatenated prediction may suffice, or the annotation may contribute little under this coverage. A positive result would remain retrospective development evidence for this fixed estimator. The initial review does not endorse a new candidate, rank search, additional phenotype acquisition, or reopening a protected outcome.

## Material objections and smallest fixes

### 1. Freeze which response columns construct the teacher

Protocol lines 15 and 30 leave `Y` ambiguous: is PCA constructed on all 18,415 masked genes, or on that source fold's eligible rare genes? These are different estimators. Common genes that are excluded from Top20 can otherwise determine the teacher directions. Direct per-gene Ridge is unaffected by fitting unused output columns, whereas the projected candidate is affected. Thus “same queries/candidate genes” at scoring does not settle the question.

Smallest fix: explicitly define the teacher's columns, gene order, and output scaling before implementation. The source-eligible rare panel is the immediate reading of the stated endpoint; alternatively the full masked panel is a permissible fixed hypothesis if declared. Do not choose between them after either scores or spectra. Mean, covariance, rank and modes must use only source compounds and the declared source-derived panel in every aligned/null fit. State that responses are raw binary calls, with source centering only and no per-gene variance normalization. Carry over the terminal insufficient-support rule if any aligned or null source fold has fewer than 20 eligible genes.

The fixed numerical eigenvalue tolerance is already given. Also freeze behavior if the rank-32 boundary cuts an exactly/numerically tied eigenspace; an arbitrary basis in a cut tied space can change predictions. This needs only a deterministic rule or a declared terminal ambiguity, not a new rank search.

### 2. The strongest direct comparator should include the existing ordinary controls

The primary maximum in line 36 excludes chemical-only and pharmacology-only Ridge, although both are already in the fixed matrix. A projection could beat every concatenated-input setting while remaining below an ordinary chemical-only predictor. Availability of both inputs does not require an ordinary learner to use every column. That result would answer the restricted concatenated panel question but would not support the practical claim “beyond ordinary prediction with the same available information.”

Smallest fix: include all already planned ordinary methods (frequency, chemical-only, pharmacology-only, joint Ridge 1/10/100 and RBF1) in the primary maximum, with a frozen tie order, and repeat that identical maximum in each null draw. This adds no fit and does not reopen the parked chemical-only candidate. If the narrower maximum is retained, the conclusion must explicitly say “over this concatenated-input panel” and a gain below either ordinary control cannot be called useful predictive improvement.

### 3. Annotation coverage is too sparse to interpret a gain as transfer of pharmacological content

A metadata-only audit of the frozen identity roster found:

| Quantity | Count |
|---|---:|
| Annotated development compounds | 54 / 231 |
| Unmatched structures | 177 / 231 |
| Target/MOA indicators | 213 |
| Indicators appearing in only one development compound | 183 |
| Indicators appearing in at most two development compounds | 206 |
| Annotated queries with no positive target/MOA indicator present in their source fold | 29 / 54 |

The last count is 10/19, 14/24 and 5/11 in folds 0, 1 and 2. There are only 25 annotated queries with a positive indicator shared with their source fold. Training folds contain 35, 30 and 43 annotated compounds. These are metadata counts, not label-dependent subgroup discoveries. Absence patterns and the availability flag can still affect predictions, so this is not a proof of zero predictive information.

For a feature absent from every training compound, a centered linear Ridge has zero coefficient. In the RBF rival, a query-only positive feature can still increase all query-to-source distances despite having no learned positive semantic correspondence. Freeze and disclose that behavior; do not interpret it as transfer of a new target. The fixed query-vocabulary construction itself uses permitted metadata rather than query outcomes and is not response leakage.

Most queries have the same all-zero pharmacology vector. Availability can mark compound curation, chemistry or screen composition, and the 213 content columns are predominantly rare identity-like markers. The all-compound denominator is appropriate, but a candidate gain can arise from output regularization on chemistry or annotation availability. The planned joint-vs-chemical full-rank comparison does not separate content from availability.

Smallest fix without expanding the matrix: freeze these coverage descriptors and restrict the second question to the descriptive effect of adding this entire metadata package under its actual missingness pattern. Do not assert that target/MOA content helps. If the coordinator needs that content attribution, the minimum additional *control* is chemical features plus the availability flag with the same direct Ridge-100 fit; that control is not a replacement candidate and should be added before launch. No favorable subgroup becomes a new primary endpoint. Keep unmatched rows as missing annotations, not inactive targets or negative pharmacology.

The exact-parent rule and conservative conflicting-signature policy are reasonable for this limited question. Source stereochemistry, parent handling, purity and stock correspondence remain limits already disclosed. The preparation code ignores an alias with no drug-annotation row when other aliases have a signature, which is slightly weaker than the written “absent signatures are missing” rule. The current frozen 54 annotated rows have no such absent drug alias, so this discrepancy does not invalidate this roster; preserve the written policy rather than silently generalizing the implementation.

### 4. Name the null and interval according to what they actually condition on

The coherent whole-scaffold reassignment, consistent source/validation truth, rebuilding of teachers/eligibility, and repeated comparator selection are substantially better than a training-only shuffle. Exact integer recovered-call totals can define both the maximum and the primary gain because all methods retain the same 231 queries and denominator 20. Preserve the actual mappings, mobility and fixed strata. With 49 randomizations, the attainable p-values have step 0.02; p <= .05 means p is .02 or .04.

However, profile reassignment tests the specified feature/profile alignment under within-stratum block exchangeability. It is **not** a randomization test of the general superiority null “projected estimator has no greater predictive performance than direct estimation.” Max-selection in every draw accounts for the listed direct-panel selection within this conditional statistic; it does not calibrate adaptation to the previously exposed development data or all earlier attempts.

The bootstrap resamples aligned cross-fitted differences against the comparator selected on those same labels. It neither refits learners nor reselects the maximum and does not represent training instability, comparator selection, shared-training dependence, independent cultures or a future population. Calling it conditional exploratory uncertainty is appropriate; make “fixed saved predictions and fixed selected comparator” explicit. No extra fitting is necessary to report that limited interval.

Smallest fix: label the p-value a conditional alignment randomization diagnostic and the interval a fixed-prediction, fixed-comparator descriptive interval. Preserve gain > 0 plus p <= .05 solely as the frozen development continuation gate. Neither passing nor an interval above zero licenses confirmation, robust superiority, protected-label release or practical benefit. A negative or immobile result must not become a reason to alter strata, rarity, rank, inputs or the comparator panel.

## Exact operator equivalence settles the mechanism question analytically

For source-centered inputs `Xc`, binary responses `Yc`, and alpha 100, direct Ridge has `B = (Xc' Xc + alpha I)^(-1) Xc' Yc`. Fitting the same Ridge to `Yc Vr` gives coefficients `B Vr`. Decoding therefore gives `mean(Y) + (direct_prediction - mean(Y)) Vr Vr'`. This holds when the same source rows, response columns, feature scaling, penalty and unpenalized intercept are used. It holds before clipping; nonlinear clipping must occur only after reconstruction.

Thus the candidate is a fixed spectral regularization of an ordinary predictor. There is no distinct functional-teacher mechanism for a performance experiment to separate from this operator. This conclusion is analytical non-novelty of the concrete candidate, not an empirical claim that low-rank regularization cannot help. Its source responses are the very supervised labels already available to the direct fit; they are not extra privileged experimental function. Ordinary Ridge-100 versus its projected version remains a useful paired ablation, while the maximum-direct contrast checks practical headroom within the frozen panel.

The planned independent synthetic identity/count-tie fixture is necessary and sufficient for the bounded operator check if it includes a nonzero output mean, source/query separation, rank truncation, zero-variance input columns and clipping order. It should check floating identity before clipping and exact recovered-call arithmetic separately. Do not call a Top20 check full-profile identity. No actual fixture or model fit was executed in this initial review.

## Endpoint, leakage, novelty and practical interpretation

The endpoint is recovery of published negative-CRANKS/FDR calls among source-eligible rare genes, not physical four-term interaction, calibrated sensitivity/specificity, validated biological negatives or effect magnitude. Keeping zero-call queries and the identical candidate universe is appropriate. Report oracle headroom and absolute recovered-call differences; a small numerical win cannot establish laboratory utility. Unknown global construction of published labels is not repaired by training-only student normalization or the conservative chromosome mask.

No query response may construct source eligibility, PCA, means, scaling, modes, tuning or teacher targets. Query annotations themselves are allowed under the declared deployment contract. Already exposed development outcomes mean this is a retrospective amendment and comparison, regardless of the freezing performed now.

The original Omni passages I checked (§1, §3.1, §3.3–3.4 and Limitations; local original text and cosine-distillation implementation) support per-instance caption-target alignment into an unchanged backbone. They do not support treating an SVD of the same binary training labels as new function or as a reproduction of that donor. The saved biological source contract also places generic training-only distillation within existing biological precedents. No new search is needed to establish the exact linear operator's ordinary form; this review makes no exhaustive literature novelty claim.

Keeping the archived chemical path frozen gives an engineering invariant. A does not update or evaluate an established old biological learner, so it cannot show non-forgetting. A 32-dimensional target can reduce representation/compute burden but does not reduce the genes assayed, independent source measurements or real assay cost. No agent, shared core, broad multimodal claim, mechanistic interpretation or general practical benefit follows from this matrix.

## Access and budget record

Read the episode brief, A v1, pharmacology freeze/preparation/identity roster, original-source evidence contract, scout handoff, selected original Omni passages/implementation, and parent pre-label protocol amendments plus selected source code for null/eligibility definitions. Performed one metadata-only count audit. Did not read the root record/synthesis or any new model outcomes; no protected 63-compound calls, S2 numerical values, HTS031, GI or CPJUMP phenotype values were opened. No labels array was opened in this review, including already exposed development labels.

Network use: **0 requests, 0 completed decoded body bytes, 0 known partial bytes** from shared pass 6. No fits, installation, new agents, shared-index edits, core edits or external messaging. Only this initial review and its receipt are written. Preserve this verdict unchanged before any coordinator response or revision.
