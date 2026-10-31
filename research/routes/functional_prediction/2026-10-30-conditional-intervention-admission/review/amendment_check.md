# Independent check of Stage 1 pre-score amendment v1.1

Date: 2026-10-30. Overall goal: ACTIVE / NOT_ACHIEVED.

Reviewed `stage1_protocol_v1_1.md` SHA-256 `54381dd0f96dd2c775d28123d942626b8506c2e5512703309286e5b87f377acb`, the preserved initial protocol/review, `gene_universe_freeze.json`, and the complete metadata-only `gene_universe.tsv`. This check was saved before candidate implementation exposure or any CGI call/score access by this reviewer. The initial review is retained unchanged.

## Disposition

**The amendment resolves B1–B3 at the protocol level. No remaining scientific protocol blocker is identified for the one bounded development-only published-call diagnostic. Implementation and access-boundary checks are still required before the run.** This is acceptance of a pre-label design correction, not evidence that a model works or that the overall research goal has been achieved. It does not authorize access to the 63 held-out compound outcomes.

## B1: coherent scaffold-block null

The new procedure assigns one complete profile vector per development compound using a single scaffold-block reassignment for each null replicate, applied consistently to every training and validation role. This removes the original inconsistency in which the same compound could have different pseudo-labels in overlapping source sets while keeping its original validation label.

Matching block size and the ordered round tuple, then moving complete blocks, preserves within-block profile dependence and the round at each matched position. Recomputing source eligibility, rarity, frequency, predictions and evaluation from the same reassigned data is necessary: a block may move across the fixed development folds, so source frequencies need not remain fixed. The amendment now requires that recomputation. It also predeclares a terminal insufficient-support result if any aligned or null source fold has fewer than 20 candidates, preventing favorable deletion of draws or post-label rarity changes.

This is a coherent finite-group conditional randomization design if block-profile vectors are exchangeable within the fixed size/ordered-round strata. Uniform within-stratum block permutations, sampled independently according to the fixed RNG procedure, and the same complete statistic in every replicate are implementation requirements. Repeated mappings or identity mappings must remain admissible; they must not be removed because they produce inconvenient null values. The plus-one tail comparison includes ties.

Block exchangeability remains a scientific assumption, not an experimental fact. Shared round controls, compound curation, regimen selection, coverage and unknown preprocessing can violate a broader biological interpretation. Fixed singleton strata and restrictive matching limit which structure/profile alignments can be challenged. Movable units, fixed strata, actual mappings and distinct mappings must be reported, as the amendment requires. Low permutation mobility would limit power and the claim; it must not trigger a post-result relaxation. A pass is conditional association in this processed panel, and a failure does not establish absence of chemical information.

## B2: identical family selection

The aligned statistic is now explicit: maximum full-development macro P@20 over nearest-five and ridge alpha 1, 10 and 100, minus the full-development frequency score. Every null replicate repeats that same four-method maximum and subtracts its own recomputed frequency score. There is no per-fold alpha winner or unreported inner search. This resolves the selection ambiguity identified in B2.

The same-fingerprint, same-source-label comparison remains fair for the information question. Source-only standardization and the population-SD/zero-variance rules are specified. Computing the prediction operator by fitting identity outputs, then multiplying by the output-label matrix, is algebraically legitimate for ordinary multioutput ridge with the stated intercept and fixed feature transformation. Clipping must occur after that multiplication, and source-only eligibility/ranking must use the appropriate aligned or null labels. Static review must verify those details; no numerical method-equivalence experiment was performed in this review.

The selected predictor remains development-selected. The paired scaffold bootstrap remains exploratory and conditional on the fitted procedure and selection. A nominal randomization result, or a bootstrap interval excluding zero, would not provide population coverage or a practical biological-effect threshold. With 49 draws the plus-one p-value resolution remains 0.02; no extra draws should be added because the result is borderline.

## B3: identity and artifact mask verification

I independently parsed the full metadata roster and existing HGNC snapshot without reading labels or candidate implementation. The following checks passed:

- The roster preserves all 19,031 original matrix identity pairs in their original order.
- Exactly 18,415 included rows map to 18,415 unique canonical genes.
- Exclusions are 486 source rows for 7p/21q, 87 for multiple source rows per canonical identity, and 43 for unmapped/ambiguous identity. These sum with the included rows to the complete source roster.
- No included canonical gene has another source row, no included HGNC(2020) key maps to multiple canonical genes, and no included row has an empty canonical identity or location.
- No included row is assigned to 7p or 21q in this annotation.
- Independently reconstructing approved-symbol, then unambiguous previous-symbol, then unambiguous alias resolution from the frozen HGNC snapshot reproduced every roster mapping; annotation locations also matched exactly.
- The four Excel-corrupted EKO cases are correctly separated by the explicit HGNC(2020) field into MARCHF1, MARCHF2, MTARC1 and MTARC2. The corrupted EKO strings are not treated as unique gene keys.
- Roster SHA-256, original source-identity SHA-256 and HGNC annotation SHA-256 match the freeze. The included-ID hash matches the sorted canonical IDs joined by newlines without a terminal newline.

One retained annotation is BAGE5 at `13cen GRCh38 patch`. This is a known chromosome-13 assignment rather than an unknown chromosome; it cannot overlap the specified 7p/21q artifact arms and is not an exclusion failure for this mask. It does not establish a precise assembly-independent locus or general artifact absence.

Verified roster SHA-256: `775bc1b1afc732724a6d1873a1d28dd116f519301503637eec39eb8fd6fae57a`.

Verified included sorted-ID SHA-256: `cca1ac12566776c4eaf597e3548a583f70b05ac49d44ce62aafd8044f2fa7ba2`.

Verified HGNC snapshot SHA-256: `12363916be36f8f6f91879b0faade4eeaac973722de7136ec61329b77f2c2f91`.

## Remaining limits and implementation checkpoint

The original scientific limits are unchanged. The endpoint is the author's S1E significant negative call, not a four-term fitness effect or a verified biological negative/positive. Absence from that list can be zero only for the literal published-call endpoint. The final implementation should make this convention explicit and record the denominators for eligible-call recall versus all unmasked native-call recall; these descriptive definitions must be fixed before numerical execution. They must not replace or modify the primary P@20 endpoint.

The conservative arm mask does not reconstruct the unknown author correction or establish prospective label-construction independence. Original source regimens include GI30 selection and adaptive schedules. The data remain one curated panel in one cell background, with shared round controls and source processing. Exact Murcko scaffold separation does not establish distant chemistry, mechanism, cell-background or external biological transfer. Training rarity is call rarity within each source fold and excludes previously uncalled genes from the task.

Static code review must check that a source screen is recognized as development before a hit pair or numeric score/FDR is reconstructed; excluded/masked identities must not enter model targets. It must also check exact split/feature/roster hashes, complete-block permutation coherence, recomputed per-null source eligibility/baselines, identical model maximum, compound-weighted macro P@20, deterministic tie handling, oracle/recall formulas, scaffold bootstrap units, stopping rules, time/thread controls and retention of every outcome. This list verifies already frozen requirements and does not introduce additional modeling options.

Even a positive development gain and conditional null pass can support only planning a later protocol. Repeatability, physical-effect support, oracle headroom and actual assay-cost evidence can still prevent practical admission. They must be assessed before a later fixed threshold and independent challenge; no result of this run releases the 63 held-out labels. No novelty, agent, mechanism, pharmacological-combination or promotion claim follows.

## Access and traffic

This amendment check used existing local protocol and identity/annotation files only. Candidate implementation, S1E hit rows, CGI score cells, held-out values and desired numerical results were not read. Checks were metadata integrity/mapping checks, not a new numerical response-data experiment. New public traffic: **0 HTTP attempts, 0 completed response-body bytes, 0 known partial bytes**. No install, delegation, external model bridge, source-library/index/core edit or model run occurred. The only new saved artifact from this follow-up is this review.

The review can now proceed to the separately requested static implementation/access-boundary check while preserving the initial objections, amendment and all claim limits. Overall status remains ACTIVE / NOT_ACHIEVED.
