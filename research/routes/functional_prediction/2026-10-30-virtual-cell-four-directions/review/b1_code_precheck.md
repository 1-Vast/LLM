# B1 unexecuted implementation check

Date: 2026-10-30. Read only `pilot_b.py` after saving `b1_initial.md`; no model was executed and no hit arrays or result files were read. No source code was edited. This check concerns the version whose main ends at line 242 and whose canonical mapping at lines 193-195 merges only 27260156 into 29083409.

**Decision remains STOP pending the initial review's known-dependence and gate/rival clarifications.** Several mathematical ambiguities are now resolved by the implementation, provided these choices are included in the frozen protocol/receipt.

## Correct constructions visible in code

- `evaluate:75` uses ordinary P@50 = n_hit/50, not positive-count-normalized precision. A library with no eligible true hits stays at zero precision; recall is NaN with its denominator recorded. The all and rare subsets each independently require at least 50 eligible measured genes (`65-69`). Declare that secondary-task population explicitly; it differs from requiring rare eligibility for both subsets.
- `prior_and_rare` uses observed-mask, screen-weighted propensity and support from at least three canonical source groups (`51-58`). The source-balanced global comparator is separately calculated at line 111.
- The KRR kernel is the ordinary dot product of L2-normalized TF-IDF rows. The algebra at `95-102` correctly implements source-weighted kernel ridge. Candidate modes come from SVD of sqrt(W) times the scaled residual matrix; task coefficients are correctly computed as unweighted standardized residuals times V (`145-151`). This avoids carrying sqrt(W) into the task-response target.
- The nonlinear comparator fits only training TF-IDF and residual decompositions and supplies source weights to ExtraTrees. Candidate, full-rank and tree fits all use the same source-balanced weights. Propensities, vocabularies, rare masks and modes are recomputed in the inner fit and again in the final four-fold fit. No query hit labels enter `predictions`.
- The control permutes fit-task context while leaving target arrays, masks and weights attached to their original rows, and reuses the selected candidate setting (`152-159`). No target label anchor is used.
- Hyperparameter selection uses source-macro rare precision on inner validation (`86-92`, `207-218`), and the final pooled summary first averages within source and then across sources (`231`). Scores, masks and tie breaking are shared across methods. Train membership and metadata/CSR task order are asserted.

## Remaining changes or declared policies required

1. Canonical grouping still omits the documented gold-standard calibration links identified in the initial review. The rare support count will automatically respect a corrected canonical mapping.
2. The three smoothed conditional frequencies and same-information neighbors currently use unweighted screen counts (`113-138`). Source-balanced versions, or explicit source-balanced replacements for the matched variants, remain absent. Preserve the official-style unweighted neighbor as a reproduction comparator.
3. The program generates predictions and summaries but does not implement the requested source bootstrap, largest-source sensitivity, per-fold rival differences, exact non-fitness/Drug gate, context-control criterion or continuation decision. Freeze these arithmetic rules before reading scores, even if a separate analysis script computes them later. The gate must not waive required but unscoreable subsets.
4. If inner rare validation has no eligible rows, selection returns -infinity and silently retains the first setting (`89-90`, `214-215`). Declare this as an unscoreable fold/INCONCLUSIVE case rather than ordinary successful tuning. Record task/source eligibility funnels, including libraries omitted for fewer than 50 eligible genes. They can be derived from roster/score differences, but explicit audit records are preferable.
5. The uniform ranking expectation is available as each task/subset's `prevalence`, but is not yet a named comparator in the aggregate summary. Include it when reporting the frozen panel. Initial receipt hashing should cover the original protocol and any amendment/gate analysis code, rather than hashing only an obsolete base protocol after amendments are adopted.

No additional numerical claim follows from this static review. Independent arithmetic verification remains necessary after execution, and passing development gates remains internal capability evidence only.
