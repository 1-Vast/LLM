# Phase 2 independent verification (agent C): findings

Independent code: `VERIFY_lib.py`, `VERIFY_1_reproduce.py`, `VERIFY_3_wiring.py`, `VERIFY_4_contrasts.py`, `VERIFY_5_info.py`, `VERIFY_6_ceiling_curve.py`, `VERIFY_7*.py`, `VERIFY_8_own_full.py` (outputs `VERIFY_*.json`). Imported from the study only: the frozen campaign engine, the builder, `common.history_draw`, and (as test subjects, checks 3 and 5) `combo`/`run_s2`/`bilinear`. HD only, E masked at load (`ACCESS_PHASE2.md`).

## Verdicts

| # | Check | Verdict | Severity |
|---|---|---|---|
| 1 | Simple rankings reproduce | **MATCH exactly** | none |
| 2 | D_add 89.25 | **Real property, not a bug** | none |
| 3a | own_h6 wiring | **Correct** | none |
| 3b | Mono leakage | **No leakage** (one note) | low |
| 3c | Independent mono retrain | **MATCH** | none |
| 3d | Poisoning | **Pass** | none |
| 4 | Contrasts and gate logic | **MATCH to 1e-15; gate logic correct** (two reporting caveats) | low |
| 5 | Comparator fairness, G2 ceiling | **G2 failure is a grid artefact, not absence of information; the practical conclusion stands** | medium |

## 1. Reproduction of the simple rankings

My own history/score code (pair-level shrunk rates, k0 = 2) fed to the frozen engine, using `history_draw` for the 10 draws (units equal `run_s2.units`, 150 units; my fold rule equals `common.fold_of`).

- 8,960 / 8,960 campaigns (7 rankings x 64 lines x 2 roles x 10 draws): purchase lists identical, confirmed identical.
- Totals (HD, fp 30): S_both 120.8, L_v 111.5, C_s 103.9, C_v 103.55, C_mean 112.9, C_prod 111.1, D_add 89.25; max abs difference to `s2_dev_selection.json` 0.0. Base choice S_both reproduced.
- Within-line Spearman: 4,480 records, max abs difference 0.0. Mean concordance S_both 0.4853, L_v 0.427, C_mean 0.304, C_prod 0.303, C_v 0.257, C_s 0.233, D_add 0.357.

## 2. D_add

Two independent implementations (5-sweep backfitting as in the study, and an exact joint ridge, k0 = 2) give 89.25 and 89.25; concordance 0.3574 / 0.3574; with the S_both verification order 89.30. It is a property of additive structure, not a bug:

- n4 history: additive 0.356 vs pair mean 0.488; full outer-training history: additive 0.398 vs pair mean 0.555; even fitted **in-sample on the target's own labels** (diagnostic only) an additive drug model reaches only 0.631.
- Joint hits are pair-specific rare events; concordance 0.357 is above C_mean (0.304) but yield is lower (89.25 vs 112.9) because a mean-label additive ranking puts the wrong pairs at the top of a 21-pick list.
- Consequence: D_add is a weak comparator; the base choice is unaffected.

## 3. Wiring

(a) **own_h6.** Training rows: 100% have an observed own shift for both drugs; target menus 95.0% (the rest involve the unmapped drug 2265 or the composite). Shifts equal `clip(y_rel - beta, +-4)` with `y_rel = (ln IC50 - ln MAX_CONC)/ln 2` (recomputed from raw columns: max diff 1.8e-15; my independent shift vs the study's `Fitter._uo`: 8.9e-16 over 22 units). The own table has 7,448 records, 126 lines, 0 duplicate (sidm, drug). The target line's own labels enter only through its own menu features; the combination label is the residual of history rows only.

(b) **Mono leakage.** I re-derived eligibility from the Jaaks CSVs' design columns (original 125 + validation screen, SIDM, COSMIC and normalised name): 48,618 eligible records, 0 disagreements with the S0 flag, 0 eligible rows with a Jaaks SIDM, COSMIC id or name. HPAF-II (SIDM00669) has 52 records, none eligible and none in any training pool. For F0..F4 and E, the exact `train_pool` sets equal my re-derivation; held-out lines in training: 0 in every configuration; alias hits in training: 0. Note (low): the dev configs F0..F4 train on the GDSC2 mono labels of the 61 E lines (mono only, no combination outcome); the E config excludes them. This does not leak combination outcomes but "E sealed" is not complete at the mono level.

(c) **Retrain of F0 'pre'** with my own minimal implementation (same model, loss, winsorisation, weights, 600 steps, l2 1e-3; three of my own random initialisations): held-out fold-0 Jaaks within-cell Spearman 0.7702 / 0.7702 / 0.7702 vs 0.7702 from the study's `F0_pre.npz` (corr of predictions 0.99999999); drug-mean baseline 0.7312. Inside tolerance (+-0.02: difference < 0.0001). `s1_g1.json` stores only the pooled value (0.7289 over folds 0-4 and E), not fold 0, so the comparison is with the study's own fold-0 parameters.

(d) **Poisoning.** For three units (Breast fold 0 draw 3, Breast fold 4 draw 7, Pancreas fold 0 draw 1) I replaced every outcome of the targets and of all HD lines that are not history with noise/flipped calls (4,109-6,773 rows) in a copy of the tissue data and ran `run_s2.score_unit` for pre_h6 and a scratch arm: max abs score difference 0.0 (6-12 score vectors per unit).

## 4. Contrasts and gates

Recomputed from `s2_dev_records.pkl` with my own bootstrap (tissue-stratified, 10,000 resamples, contract seed): all concordance means, CIs and relative-yield means and CIs equal `s2_dev_summary.json` to 7e-16.

| Contrast | Concordance gain [95% CI] | Yield (a vs b), relative [95% CI] |
|---|---|---|
| pre_h6 - S1 | -0.0086 [-0.0125, -0.0051] | 118.35 vs 120.80, -2.03% [-4.45, -0.36] |
| pre_h6 - scratch (10 members) | -0.0009 [-0.0045, +0.0024] | -0.72% [-2.87, +0.91] |
| pre_h6 - drug-permuted (10) | -0.0046 [-0.0083, -0.0012] | -1.04% [-3.26, +0.69] |
| pre_h6 - cell-permuted (10) | -0.0003 [-0.0030, +0.0022] | -0.96% [-2.67, +0.32] |
| own_h6 - S1 | +0.0005 [-0.0038, +0.0049] | -2.11% [-3.69, -0.61] |
| pot_p3 - S1 | -0.0007 [-0.0009, -0.0004] | -0.41% [-0.91, 0.00] |

Gate logic against PROTOCOL_V1 section 7: "above all permutations" compares the concordance gain of pre_h6 (-0.00862) with each member's mean line-level gain (the same quantity): correct. It fails because **all 10 drug-permuted, 5 of 10 cell-permuted and 6 of 10 scratch members have a higher gain than the real pretrained arm**. G2, G3 recomputed false, G1 true, E sealed: agreed. Swap analysis: 2,154 of 27,180 purchased screens swapped (7.9%), 35 confirmed gained, 84 lost.

Reporting caveats: the "HARM" class uses the line bootstrap only; the study's own line-by-pair sensitivity for pre_h6 - S1 is [-5.9%, +0.4%], whose upper bound is above 0, so under pair dependence the class would be UNRESOLVED, not HARM. The yield harm is a regularisation artefact (section 5).

## 5. Comparator strength, fairness and the G2 ceiling

Learned arms are not handicapped on information, rows or units: they use the same 4 history rows as S_both, the same S_both prior, centre g within the line, and rescale g to label units (std(g)/std(prior) = 0.16 for pre, 0.14 dperm0, 0.12 scratch, 0.01 pot_p3), with the verification order of the base. Pairs with unmapped drugs abstain (3.9% of menu rows). No unit mismatch found.

What is unfair, or at least fragile:

1. **No zero-weight fallback and too little shrinkage in the registered grid.** Every family picks the strongest registered penalty (l2_theta 30, l2_init 300). Extending it with the study's own pipeline (30-unit subset): pre_h6 gain -0.0091 (theta 30), -0.0048 (300), -0.0002 (3000), -0.00007 (30000); dperm0 -0.0098 / -0.0063 / -0.0019 / -0.0002; scratch0 -0.0080 / -0.0007 / -0.00004 / +0.00001. The measured "harm" of pre_h6 is therefore overfitting of theta on 4 history lines (4 cell contexts), not misleading mono information; it vanishes under stronger shrinkage. This is also why real pretraining is worse than shuffled mono (larger feature variance overfits more).
2. **G2 does not measure an information ceiling.** On all 150 dev units: own_h6 gain +0.0005 [-0.0038, +0.0049] at the registered theta 30, +0.0012 at 300, +0.0023 [-0.0008, +0.0056] at 3000 and **+0.0023 [+0.0009, +0.0040] at 30000** (CI above 0). An independent ridge on own-mono pair features with the same 4-line histories gives +0.0032 [+0.0001, +0.0063] (alpha 300) and +0.0032 [+0.0013, +0.0051] (alpha 1000). The closed-form ridge on the study's own h6 features matches the Adam solution (max theta difference 1.7e-5), so the fit is converged; the failure is conditioning/regularisation, not an optimiser or wiring bug. My recomputation of the registered own_h6 cfg 2 reproduces the recorded concordance exactly (110 records, max diff 0.0).
3. **Information exists across lines but is small.** Drug-in-line association over the 64 HD lines (own mono sensitivity of a drug vs the line-level residual synergy of pairs containing it, within tissue): mean Spearman +0.189 over 75 (tissue, drug) groups (79% positive) against a permutation null of -0.002 (95th percentile of the null mean 0.039); a synthetic positive control (injected drug-in-line effect) is detected by the same pipeline (+0.095 concordance). With full HD history a ridge on own mono gives +0.0074 [+0.0029, +0.0119] (pair features) and +0.0022 [-0.0006, +0.0050] (drug slopes); the learning curve for pair features is +0.0040 (n4), +0.0059 (n8), +0.0070 (n12), +0.0079 (all other HD lines), all CI above 0. The decision-relevant ceiling is nil: P2 yield with the full-history ridge is 134.0 vs 133.5 (+0.4% [-2.1, +3.3]) and 133.0 (-0.4% [-2.3, +1.0]).

So "if even the line's own measured mono cannot move the ranking, mono-derived information is exhausted" is not literally supported (the ranking moves by +0.002 to +0.008 Spearman, 0.4-1.6% of the base 0.49), but the study's practical conclusion is robust: the ceiling gain is far below tau = 5% in yield, and any predicted-mono model (held-out per-drug skill 0.23) sits below that ceiling.

Other points a reader should know: S1 is selected on the same 64 HD lines it is later compared on (S_both over C_mean by 7.9 confirmed); that does not disadvantage the learned arms because they are built on S_both. The G2/G3 CIs treat lines as independent; recurring pairs widen intervals by about 2 (the study's own two-way result agrees).

## Bottom line

The study's negative result is reproduced and its code is wired as documented (no leakage, no poisoning sensitivity, exact reproduction of every number checked). Two things should be stated alongside it: (i) the HARM class and the G2 failure are artefacts of an under-regularised fixed grid (no zero fallback), not evidence that mono is uninformative or misleading; (ii) independent tests find a small real cross-line signal in own mono that does not translate into a yield gain near tau.
