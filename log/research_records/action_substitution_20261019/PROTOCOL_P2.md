# Phase 2 protocol: can partner-specific substitution failures be predicted for an unseen implementation?

Status: FROZEN before `lofo.py` was run. Digests are in FREEZE.json. Written 2026-10-19, after the reproducibility
decomposition (`DECOMP.json`, see section 0) and before any held-out-implementation prediction was computed.

## 0. What the gate showed and why this is the question

Gate data: interaction endpoint S = `SYNERGY_DELTA_AUC`, target-overlap swaps, replicate units split by seeding date,
composite anchors excluded.

- **Reproducible.** Unit reliability r = 0.29 (1,027 units).
- **Where the reproducible variance sits.** Cross-half covariance:

  | Component | Covariance |
  |---|---|
  | Pair main effect | 0.00009 |
  | **Partner-specific** | **0.00052** |
  | Line-specific | 0.00008 |
  | Partner x line | 0.00007 (line-bootstrap CI -0.00008 to 0.00014) |

- **Partner-level reliability.** Averaged over lines, swap contrasts reproduce at r = 0.36 to 0.43.
- **Annotation helps but does not decide.** Target-overlap swaps have about half the reproducible SD of unrelated swaps
  (0.019 vs 0.039 at partner level).
- **Efficacy endpoint.** For E (`SYNERGY_OBS_AUC`), line-specific and pair effects dominate, consistent with
  single-agent potency.

So the substitution relation that exists in this screen is **partner-conditional, not context-conditional**: drug A'
replaces A with some partners and not others, consistently across lines.

**This phase's question:** can that partner-conditional failure be predicted for an implementation **never measured in
combination**, better than the obvious baselines?

## 1. Data and units

- Source: Jaaks 2022 original screen, fitted file (MD5 786589e5…), exposed in October, so this is **development
  evidence**.
- Exclusions: composite anchors ("X|Y").
- **Cell.** Each row contributes two perspectives:
  - library perspective: (drug = library drug, role L, partner = anchor@concentration, line);
  - anchor perspective: (drug = anchor, role A, partner = library drug # anchor-concentration rank, line).
  - Cell value y = mean `SYNERGY_DELTA_AUC` over plates.
  - Single-agent values: library role `LIBRARY_AUC`; anchor role `ANCHOR_VIABILITY`.
- **Held-out implementations X.** Every non-composite drug with at least one target-overlap sibling (shared annotated
  target) in the same role. One fold per X.
  - In each fold, every cell where X is the drug or the partner leaves the training and reference tables.
  - X's single-agent profile stays available, mirroring a new compound that has single-agent screening but no
    combination data.
- **Evaluable test cell.** A cell (X, role, P, c) where at least one sibling S has a reference cell (S, role, P, c).
- **Partner-level unit.** (X, role, P), averaged over evaluable lines.
  - Observed: Delta_obs = mean_c [y(X,P,c) - mean_S y(S,P,c)].
  - Each method's Delta_hat is computed the same way from its cell predictions.

## 2. Methods (identical information; each fit only on its fold's training table)

| Id | Prediction of y(X,P,c) |
|---|---|
| B0 sibling copy (annotation equivalence) | mean_S y(S,P,c) |
| B1 partner-line mean | mean over all reference drugs D of the same role of y(D,P,c) |
| B1p same-pathway copy | mean over reference drugs in X's annotated pathway (falls back to B1) |
| B2 potency-matched copy | B0 + beta_role * (m(X,c) - m(S,c)), beta fit by OLS on training sibling swaps |
| B3 functional neighbour | y(D*,P,c), D* = reference drug of the same role whose single-agent line profile has the highest Pearson correlation with X's (at least 10 shared lines) |
| B4 cold-start regression | ridge: B1, m(X,c), mean m(X), m(P,c), shared-pathway(X,P), target-Jaccard(X,P), one-hot pathway(X) x pathway(P) |
| B5 kernel smoother (GP-mean style) | weighted mean of y(D,P,c), weight = exp(-(1 - corr(X,D))/0.2) * (1 + 2 * targetJaccard(X,D)) |
| **M learned substitution model** | mean_S [y(S,P,c) + Delta_hat(S->X,P,c)]; Delta_hat from ridge (alpha 1, standardised) trained on up to 300,000 training swaps of any class (target, pathway, unrelated; same role, partner, line) |
| M-noP ablation | M without the partner-specific features f6-f8 |

M's swap features:

- f1 = m(X,c) - m(S,c)
- f2 = mean_c m(X) - mean_c m(S)
- f3 = 1 - corr(profiles)
- f4 = target Jaccard(X,S)
- f5 = same pathway(X,S)
- f6 = f1 * m(P,c)
- f7 = sharedPathway(X,P) - sharedPathway(S,P)
- f8 = targetJaccard(X,P) - targetJaccard(S,P)
- f9 = y(S,P,c) - B1
- f10 = B1
- intercept per role

## 3. Endpoints and decision

- **Primary.** Partner-level MSE of Delta over all evaluable partner-level units, weighting folds by their units.
  - Contrast: MSE(best baseline) - MSE(M), where "best baseline" is whichever of B0-B5 has the lowest MSE on this same
    evaluation. That choice is post hoc and therefore conservative.
  - Uncertainty: cluster bootstrap over held-out implementations X, 2,000 draws.
- **Learnability label:**
  - **LEARNABLE**: lower 95% bound > 0 and relative reduction >= 5%.
  - **NOT_BEYOND_BASELINE**: upper bound < 5% relative.
  - **INCONCLUSIVE**: otherwise.
- **Partner conditioning.** MSE(M-noP) - MSE(M), with a bootstrap CI. Partner-specific features help if the lower bound
  is > 0.
- **Equivalence decisions** (secondary).
  - A swap fails with partner P when |Delta_obs| > epsilon = 0.03 AUC. That is about 1.5x the partner-level noise SD,
    fixed here.
  - Reported per method: AUROC of |Delta_hat| for failure, and decision accuracy at the threshold |Delta_hat| > 0.03,
    against B0's constant "holds".
- **Noise ceiling.** Half-split partner-level reliability for the evaluable units in the 46 replicate lines, reported
  descriptively.
- **Efficacy endpoint E.** The same analysis is rerun with `SYNERGY_OBS_AUC`, descriptive only.
- **Within-Jaaks replication (secondary).** The Jaaks validation screen (separate measurement; its exposure in October
  cannot be ruled out, so it is **not independent confirmation**). Fold parameters come from the original screen; the
  reference cells come from the validation screen with X removed. The same primary contrast is computed there.

## 4. What this cannot show

- Independent confirmation: the only untouched candidate (Vis 2024 Data S1) is not local and has 19 combinations.
  **BLOCKED.**
- Context-conditional substitution: the gate found no reproducible partner x line structure, so it is not modelled.
- Mechanistic (Level M) equivalence: there is no measured target-engagement truth locally.
- Agent value: not run here. No paid-call authorisation is recorded for this brief, and MAESTRO's LLM arms have been
  null. A deterministic refinement design is tested in phase 3 only if phase 2 is LEARNABLE or partner-specific
  features help.
