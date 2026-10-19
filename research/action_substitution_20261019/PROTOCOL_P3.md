# Phase 3 protocol: do counterexamples refine a substitution, and is it partner-specific?

Status: FROZEN (FREEZE_P3.json) before `refine.py` was run and before any Phase 2 result (LOFO_*.json) existed or was
read. Written 2026-10-19 while Phase 2 was running.

## Question

The gate (REPRO.json, DECOMP.json) found the reproducible part of a substitution contrast is partner-specific and
context-generic. If so, one measured counterexample should correct the prediction for the other lines of the same
partner, and should do so better than an equally sized probe of a different partner (a generic implementation offset).

- Partner-specific refinement → the substitution relation should be stored per partner: A ~ A' holds for partner set
  B_set.
- Generic refinement only → a scalar potency or interaction offset per implementation suffices, and partner-level action
  units add nothing.

## Units

- Endpoint S = `SYNERGY_DELTA_AUC` (primary); E = `SYNERGY_OBS_AUC` is reported descriptively.
- Held-out implementations X, cells, siblings and exclusions are as in PROTOCOL_P2, reusing `lofo.cells`, `Ref` and
  `Drugs`.
- Unit: (X, role, partner P) with at least 3 evaluable lines.
  - Each evaluable line in turn is the **probe line** l.
  - Target: the mean over the remaining lines of Delta_obs = y(X,P,c) - mean_S y(S,P,c).

## Arms

All arms share the same prior Delta_prior(c):

- **B0**, annotation equivalence: Delta = 0. This is the PHAROS mechanism-matched assumption.
- **B2** (reported as a second prior): potency-matched, Delta = beta_role * (m(X,c) - m(S,c)), with beta fit on
  training sibling swaps.

| Arm | Prediction for the remaining lines of (X, P) |
|---|---|
| R0 none | prior |
| R1 partner-specific | prior + w * (Delta_obs(X,P,l) - prior(l)) |
| R2 generic (control) | prior + w * (Delta_obs(X,P',l') - prior(l')), where (P', l') is a probe of a different partner of the same X and role. Every other partner with a probe is used in turn, and results are averaged. |
| R3 pooled-generic | prior + w_X * mean over all other partners' single probes |

Shrinkage: w = tau^2 / (tau^2 + sigma_w^2).

- tau^2 (between-partner variance of mean Delta) and sigma_w^2 (within-partner cell variance) are estimated per fold.
  The data are training sibling swaps (pairs not involving X) grouped by (pair, role, partner):
  - sigma_w^2 = pooled within-group variance;
  - tau^2 = max(var of group means - mean(sigma_w^2 / n_g), 0).
- R2 uses the same w, so R1 and R2 differ only in **which** probe is read.
- R3 uses w_X = tau_X^2 / (tau_X^2 + (tau^2 + sigma_w^2)/n_probe). tau_X^2 is the between-pair variance of the pair
  mean Delta, estimated the same way over pairs.

## Endpoints and decision (S, prior B0)

- Primary metric: MSE of the remaining-line mean Delta, averaged over probe lines within a unit, then over units.
- Uncertainty: cluster bootstrap over X, 2,000 draws.
- Contrasts:
  - C1 = MSE(R0) - MSE(R1);
  - C2 = MSE(R2) - MSE(R1);
  - C3 = MSE(R3) - MSE(R1).

| Condition | Label |
|---|---|
| C1 lower > 0 and C2 lower > 0 and C3 lower > 0 | PARTNER_SPECIFIC_REFINEMENT |
| C1 lower > 0 but C2 or C3 lower <= 0 | GENERIC_REFINEMENT_ONLY |
| C1 lower <= 0 | NO_REFINEMENT_VALUE |

- **Decision metric (secondary).** Accuracy of "the swap fails" (|remaining-line mean Delta| > 0.03) under each arm,
  plus the share of units where R1 flips the R0 decision correctly versus incorrectly.
- **Design (secondary, deterministic designer; no LLM).** With a budget of probing 25% of an implementation's
  partner units (at least 1), compare decision accuracy over **all** that implementation's units under two selections:
  - random partner selection (200 draws);
  - an ambiguity designer that probes the partners whose prior |Delta| has the largest posterior probability of
    crossing epsilon, i.e. the smallest |(|Delta_prior| - epsilon)| / sqrt(tau^2).

  Unprobed units keep the prior. The probe line is the first evaluable line in sorted order.

## Limits

- Development evidence on exposed Jaaks data.
- Probes are re-reads of existing cells, not new experiments; the cost of a probe is one combination block (one
  partner, one line).
- An LLM or agent designer is not run, because no paid-call authorisation is recorded for this brief.
