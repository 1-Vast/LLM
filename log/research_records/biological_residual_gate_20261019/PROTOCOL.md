# P0 Biological Residual Information Gate: protocol

Status: FROZEN (FREEZE.json) before `p0.py` ran. Written 2026-10-19.

Scope:
- Data: the exposed Jaaks 2022 data only, with the same cells, evaluation units and exclusions as
  `../action_substitution_20261019` (PROTOCOL_P2: composites excluded; 37 candidate implementations, 27 evaluable;
  1,950 partner-level units).
- Development evidence only.
- Nothing in `../action_substitution_20261019` is modified.
- Kinobeads (Klaeger 2017) quantitative profiles are not used here. A separate session
  (`../kinobeads_substitution_20261019`) runs that pre-registered test; this study only reports its coverage.

## Information contracts

- **Scenario A, functional panel available.** The held-out implementation X has its single-agent response in every
  screened line: `LIBRARY_AUC` (library role) or `ANCHOR_VIABILITY` (anchor role). X has no combination measurement.
  - Cost: in Jaaks the single-agent curves come from the same plates as the combinations. As a separate purchase this
    is about 125 lines x one 7-point curve, about 875 wells.
  - This is **not** zero-shot or zero-cost generalisation.
- **Scenario B, low-cost priors only.** Target-set and pathway annotations of X (GDSC annotations, fixed with the screen
  in 2022), plus the reference combination data of other drugs. No single-agent panel, and no potency of X in any line.

## Families and clustering

Family = connected component of the any-target-overlap graph over non-composite drugs. Every uncertainty interval is a
cluster bootstrap over **families** (primary, 2,000 draws), with the implementation-level bootstrap reported beside it.

**UNDERPOWERED rule:** fewer than 8 families with at least one evaluable unit makes Gates 1 and 2 UNDERPOWERED,
whatever the point estimates.

## P0-A: decompose B5

All arms use identical units and identical reference cells: every drug at the same (role, partner, line) except X.
Each predicts y(X,P,c) as sum_d w_d y(d,P,c) / sum_d w_d.

| Arm | Weight w(X,d) | Scenario |
|---|---|---|
| F | exp(-(1 - rho(X,d))/0.2); rho = Pearson correlation of single-agent line profiles, at least 10 shared lines, else 0 | A |
| T | 1 + 2 J(X,d); J = target-set Jaccard | B |
| F+T (= B5) | F x T, the historical B5. It must reproduce `lofo_units` d_B5 to 1e-9, or the study stops. | A |
| F+T-shuffled, pathway-preserving (primary null) | F x (1 + 2 J_perm). Target sets are permuted among drugs **within the same annotated pathway**, preserving set sizes, annotation density and pathway structure; 200 permutations. | A |
| F+T-shuffled, global | Target sets permuted among all non-composite drugs; 200 permutations | A |
| B0, B1, B1p | As in PROTOCOL_P2 (sibling copy, partner mean, same-pathway mean) | B |

- Endpoints: interaction S (`SYNERGY_DELTA_AUC`, primary) and efficacy E (`SYNERGY_OBS_AUC`, secondary).
- Metrics, partner-level Delta:
  - MSE;
  - failure AUROC (|Delta_obs| > 0.03);
  - sensitivity, specificity and balanced accuracy at |Delta_hat| > 0.03;
  - calibration slope (regression of Delta_obs on Delta_hat).
- Per-family MSE is reported.

**Gate 1 (independent biological information, S): PASS** if all three hold:

1. rel = (MSE_F - MSE_F+T) / MSE_F >= 0.05, with family-bootstrap lower bound of MSE_F - MSE_F+T > 0;
2. MSE_F+T is below the 5th percentile of the pathway-preserving shuffle distribution (one-sided permutation
   p < 0.05);
3. balanced accuracy of F+T >= F.

Other outcomes:
- **UNDERPOWERED**: the family-bootstrap interval of rel contains both 0 and 0.05.
- **FAIL**: otherwise.

## P0-B: biological residuals of B5

- Residual: e = Delta_obs - Delta_hat_B5 per partner-level unit. Scoring only; never a feature.
- A **consequential error** is a B5 decision at epsilon 0.03 that differs from the observed one.
- Pre-decision features per unit, summarised over X's siblings S present at that unit:
  - **Bio-mismatch set:**
    - mean (1 - J(X,S));
    - any exact target-set match;
    - any shared first-listed (primary) target;
    - functional-similar-but-target-different = max_S rho(X,S) x (1 - J(X,S)).
  - **Generic set:**
    - mean rho(X,S);
    - mean |mean_c m(X) - mean_c m(S)| (potency mismatch);
    - kernel effective n = (sum w)^2 / sum w^2;
    - disagreement |Delta_hat_B5 - Delta_hat_B1|;
    - disagreement |Delta_hat_B5 - Delta_hat_B4|, with B4 from the frozen phase-2 tables;
    - partner shares X's pathway;
    - role.
- Models:
  - L2 logistic regression (C = 1, standardised) for consequential error;
  - ridge (alpha 1) for e.
  - Both are trained **leave-one-family-out**: features and labels of the held-out family are never in training.
- Arms: generic, bio, generic+bio.
- **Gate 2 (S): PASS** if both hold:
  1. AUROC(generic+bio) - AUROC(generic) >= 0.05, with family-bootstrap lower bound > 0;
  2. the residual-corrected B5 (Delta_hat_B5 + ghat from generic+bio) beats B5 on MSE with lower bound > 0 **and**
     does not reduce balanced accuracy.
- Otherwise FAIL, or UNDERPOWERED per the rule above.

## P0-C: decision opportunity

- **Decision.** An original drug A was measured with partner P in line c and is now unavailable or replaceable. Choose
  one alternative implementation from A's family (the other family members measured at the same key) to advance.
- **Choice set:** a key (role, partner, line) with A plus at least 2 alternatives. Each member of the family in turn is
  A; the alternatives are held out together.
- **Predictions.** F, T, F+T, B1 and B0 predict each alternative from the reference minus all alternatives (A stays
  in). B0 copies A, so every alternative ties and the choice is random.
- **Primary endpoint.** Efficacious combination benefit, ECB-like:
  - formula: min(single-agent value of X, partner's single-agent value) - observed combination AUC;
  - this is the benefit over the better single agent on the viability-AUC scale, after Vis et al. 2024 (ECB is their
    concept; this is an HSA-type approximation over the library dose range);
  - under Scenario A the method's predicted ECB uses X's known single-agent value and its predicted E;
  - also reported: absolute efficacy (lowest E) and S.
- **Metrics:**
  - realised value of the chosen alternative minus the mean over alternatives (random choice);
  - oracle opportunity (best observed minus random);
  - **reproducible opportunity**: choose by the half-1 observed value, score on half 2, from lines with seeding-date
    halves;
  - wrong-advancement rate: the chosen alternative has ECB <= 0 while some alternative has ECB > 0.02.
- **Minimum useful decision gain:** 0.02 viability-AUC units of ECB per decision over random. That is 2% absolute
  viability averaged over the dose range, the smallest change a follow-up experiment of one combination block (one
  partner, one line, about 70 wells) would plausibly be worth.
- **Gate 3: PASS** if all three hold:
  1. reproducible opportunity >= 0.02;
  2. F+T selection gain over random >= 0.02 with family-bootstrap lower bound > 0;
  3. F+T - F selection gain lower bound > 0 (the biological component changes decisions).
- Otherwise FAIL (no usable action space, or no biological contribution).

## Feedback against the strongest prior (descriptive, S)

- PROTOCOL_P3 refinement (one probe line per unit, w = tau^2 / (tau^2 + sigma_w^2)) is rerun with prior B5 (F+T) in
  place of B0, on the same units and probe lines.
- Reported:
  - MSE of the remaining-line mean for B5 with and without the probe, and for B0 with and without the probe;
  - decision confusion of each.
- The epsilon 0.03 conclusion of PROTOCOL_P3 is not revisited. No new threshold is tested here.

## Advancement decision

| Outcome | Decision |
|---|---|
| Gates 1, 2 and 3 all PASS | GO |
| Any gate PASS, but not all | NARROW |
| Gate 1 or Gate 2 UNDERPOWERED and none PASS | UNDERPOWERED |
| All FAIL | STOP |

Independent confirmation is reported separately: BLOCKED_INDEPENDENT_ENDPOINT unless an untouched qualified tier
exists. Untouched outcomes are checked at metadata level only.
