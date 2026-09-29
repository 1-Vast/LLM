# Viability-Contrast v5b: Variance Fix, Blend Variants, Oracle Decomposition

Date: 2026-09-28. Block: `research/viability_contrast/`. Protocol: `protocol5b.json`
(`viability-contrast-5b`), frozen at 2026-09-28T11:39:31Z (`freeze5b.json`).
Run: `outputs/viability_contrast_20260928/run5b/` (81 min CPU). Spend: $0, 0 wells,
0 downloads.

## 1. Purpose

An external review of the frozen v5 results (README section 3.6) raised one numerical
defect and three inference weaknesses. This run executes the four registered
corrections with pre-stated revision criteria: C1 full posterior-covariance quadratic
form; C2 fusion-rule variants (precision / holdout-selected weight / template-only);
C3 oracle decomposition into oracle_reading and oracle_label; C4 Clopper-Pearson
one-sided 95% UCB reporting next to the v5 point-estimate rule (tau_emp vs tau_ucb).

## 2. Pre-run verification of the review (all four claims confirmed)

- C1: `world5.py` line 63 `np.einsum("pr,rr,pr->p", V, sig, V)` reads only diag(sig).
  Reproduced on a random PD matrix: diag-only 1.99 / 8.88 vs full 0.77 / 3.60.
- C2: `prec = 1/bv + 1/pv` mechanically returns a variance below either channel although
  template and completion are fitted on overlapping training data.
- C3: tau selection = decided >= 20 and point estimate <= 0.05 (qualify2 constants).
  CP one-sided 95% UCB of 0 wrong in 20 = 0.1391, matching the review's 13.9%.
- C4: `qualify2.run_episode_v2` oracle maximises the TRUE class's margin over the true
  term matrix T — reading access AND label access jointly.

## 3. Registration and freeze discipline

protocol5b.json written before any v5b score; each correction carries a pre-stated
"what would change the conclusion" criterion. Synthetic smoke (`tmp/smoke5b.py`)
exercised every code path (three blend modes, three acquisition rules, both oracle
modes, the gated genetic branch, calibration machinery) printing shapes only. Freeze
written after the smoke; v5 freeze re-verified intact after the freeze.py extension
(v5b added as version 6; frozen files untouched).

## 4. Design notes

- run5b imports the frozen run5 acquisition functions instead of copying them, so the
  acquisition semantics are byte-identical to v5; the calibration split-half assignment
  is keyed by the v5 hash, preserving identical halves for cross-run comparability.
- planner_precision_* differs from v5's planner_learned_* ONLY through C1.
- Holdout weight: one scalar w in {0, 0.25, 0.5, 0.75, 1.0} per fold, selected on
  training compounds by the same simulated-episode machinery as rank selection.
- oracle_reading: label-blind, sees T, buys max realised top1-top2 margin.
  oracle_label: sees the label, steers the true class's expected margin under its own
  template, can be charged QC failures like a realistic arm.

## 5. Headline measurements

- Gate v5b FAILED: no realistic arm reaches a finite tau_emp in any fold (check 1);
  oracle_reading is not above the best realistic arm (check 2); shuffled controls
  abstain (check 3 passed).
- C1: frontier 0.57-0.86 wrong (v5: 0.55-0.81) — the frontier conclusion survives the
  fix. Rank selection changed (16/8/8/16/16 vs all-16). MI < margin at tau 8 in 5/5
  folds for the precision blend (v5-comparable), 3/5 for holdout.
- C2: holdout weight w = 1.0 in 4/5 folds, 0.75 in fold 0 (training predictive LL
  prefers completion-only), yet holdout qualifies nothing and off_mi posts a better
  frontier than holdout_mi in 4/5 folds (0.61-0.71 vs 0.58-0.83). The registered
  retirement criterion for the completion channel at the decision level is met.
- C3: oracle_reading 0.77-0.87 wrong at tau 34 (89-134 decided per fold) — perfect
  response prediction without the label qualifies nothing and is worse than several
  realistic arms. oracle_label 0.26-0.40 wrong at tau 13. oracle_full 0.002 held-out
  (512 decided, 1 wrong, CP UCB95 0.0092). The v5 sentence "the compound-level accuracy
  needed approaches knowing the readings themselves" is RETRACTED per the registered
  criterion.
- C4: under tau_ucb nothing realistic or partial-oracle qualifies (0/20 UCB = 0.139;
  5%-grade evidence needs >= 59 zero-wrong decisions); oracle_full remains
  certification-grade post hoc (UCB 0.0092).

## 6. Interpretation

The v1-v5 'oracle ceiling' measured the value of selecting evidence to fit a known
answer, not an upper bound on world-model quality. Label-blind perfect prediction
under margin acquisition is aggressive Goodhart (it always finds noise-driven
separation for SOME class among 39 x 443). The world-model lever on this task-policy
pair is measured dead: zero qualified decisions under perfect response prediction.

## 7. Consequences for the register

- The completion channel is retired at the decision level on this task (Measured).
- Any future 'certification' claim requires UCB-grade evidence (>= 59 zero-wrong
  decisions or sequential methods with stated assumptions).
- Any future ceiling design must include a reading-only decomposed control; a full
  oracle alone misattributes label access to prediction quality.
- The paired two-compound contrast direction (section 3.6 register) is unchanged but
  now justified differently: response prediction is measured non-binding here.

## 8. Files

- Code/protocol: `research/viability_contrast/{protocol5b.json, world5b.py, run5b.py,
  freeze5b.json}`; freeze.py extended (version 6), v1-v5 verifies re-passed.
- Outputs: `outputs/viability_contrast_20260928/run5b/{episodes.csv, summary.json,
  gate.json, world_fit.json}`.
- Records: `research/viability_contrast/README.md` section 3.7 (+ sections 1, 3.6
  retraction marker, 5); this file; `log/INDEX.md`.

## 9. Verification

- `freeze --v5b --verify`: all_match true. v5 verify: all_match true (after the
  freeze.py edit).
- `pytest tests/test_repository_shape.py`: log-index test passes; the two markdown
  tests fail in this sandbox only because git is unavailable and the fallback scan
  sweeps pre-existing CJK files outside this block's ownership — every file written
  in this run was directly verified CJK-free.

## 10. Cost and reproducibility

$0, 0 wells, 0 downloads. 81 min CPU (`maestro` env). Reproduce:
`python -m research.viability_contrast.freeze --v5b --verify` then
`python -m research.viability_contrast.run5b`.
