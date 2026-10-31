# Post-run metric clarification

This file does not rewrite `PROTOCOL.md`, `FREEZE.json` or any saved output. It records
an ambiguity found by the independent verifier and fixes the metric interpretation for
a supplemental arithmetic recheck.

For each query, let `g` be the reference-fold generic profile and let `R(x,g)` be the
centered least-squares residual of vector `x` on `[1,g]`, preserving the finite mask.
The observed sensitivity used for the oracle is `-R(y,g)`.

- `raw_k20` and `ridge_raw` produce calibrated profile predictions `p`; their ranking
  score is `-R(p,g)`.
- `decision_top10_ridge` produces a top-membership score `s`; its ranking score is `s`
  directly and it is not residualized again.
- The predicted set is the first `round(0.10 * n_finite)` lines under descending ranking
  score, with stable original line order for exact ties.
- `top10_overlap` is the intersection with the observed oracle top set divided by the
  selected count.
- `selection_regret` is the observed oracle mean sensitivity minus the observed mean
  sensitivity of the predicted set.
- `raw_threshold_hit` is the fraction of selected lines with raw observed LFC `<= -1`.

The clarification changes no input, model, fold, threshold, output or scientific
decision. The original verifier failure remains preserved. A supplemental verifier may
use this explicit interpretation to determine whether the saved metrics are arithmetically
reproducible; if it still fails, the primary result remains unverified.
