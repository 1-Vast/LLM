# Phase 1 gate: are conditional substitution contrasts reproducible? (written before any response column was read)

2026-10-19. Jaaks et al. 2022 anchored screen, exposed in October 2026, so this is development evidence only. The
design-only census (`census.py`, `CENSUS.json`) and the plate table (`cache/plates.csv`: seeding date, cell stock per
plate) were produced without reading any response value.

## Units and endpoints

- **Substitution unit** u = (A, A', B, c, side).
  - A and A' are alternative implementations. Families come from the design census: shared annotated target
    (`target`) or the same annotated pathway without a target overlap (`pathway`). A third class, `unrelated`, is drug
    pairs in different pathways and serves as a control.
  - B is the common partner in the other role. c is the cell line.
  - Library side: A and A' are library drugs, combined with the same anchor B at the same anchor concentration.
  - Anchor side: A and A' are anchors at their own fixed concentrations, combined with the same library drug B. Both
    anchor concentrations are kept as separate units.
- **Endpoints** (both on the 0-1 viability AUC scale over the library dose range):
  - **E (efficacy):** `SYNERGY_OBS_AUC`, the observed combination viability.
  - **S (interaction):** `SYNERGY_DELTA_AUC`, the expected-under-Bliss AUC minus the observed AUC.
  - Both are reported; **S is primary**, because single-agent potency differences drive E.
- **Contrast.** Delta_u = R(A', B, c) - R(A, B, c).

## Independent replicates

Measurements are split by seeding date (`DATE_CREATED`) within each line. Distinct dates are sorted and assigned
alternately to half 1 and half 2. A unit is a **replicate unit** when both A+B and A'+B are measured in both halves.
Delta is computed separately in each half (mean over that half's plates).

## Estimands

1. **Unit-level reliability of Delta:** the correlation between half-1 and half-2 Delta over replicate units.
   - Reproducible SD = sqrt(cov). Noise SD of one half = sqrt(var(difference)/2).
   - Computed per family class and endpoint.
2. **Conditional (partner x context) component.** Within each drug pair, the additive structure
   Delta = a(pair, B) + b(pair, c) is fitted separately in each half by alternating means, with at least 2 partners and
   2 lines. The estimand is the correlation of residuals across halves, and the conditional share = cov(residuals) /
   cov(Delta).
3. **Single-agent baseline (library side, E and S):** how much of the half-2 Delta the half-1 single-agent difference
   (`LIBRARY_AUC` of A' minus A in the same line and half) explains (R^2), compared with the half-1 Delta itself.
4. **Annotation as a substitutability predictor:** reproducible variance of Delta (cov across halves) in the `target`,
   `pathway` and `unrelated` classes.

Uncertainty comes from a cluster bootstrap with 2,000 draws, resampling lines. For the `target` class, a drug-pair
cluster bootstrap is also reported. The decision uses the wider of the two intervals.

## Decision rule (S endpoint, `target` class, library and anchor sides pooled)

| Condition | Label |
|---|---|
| fewer than 300 replicate units | BLOCKED |
| reliability 95% upper bound < 0.20 | REJECTED (contrast dominated by noise) |
| reliability lower bound > 0 but conditional residual correlation lower bound <= 0, or conditional share < 0.25 | CONDITIONALLY QUALIFIED (substitution differences exist but are partner- or context-generic; a pair-level effect model suffices) |
| reliability lower bound > 0, conditional residual correlation lower bound > 0, and conditional share >= 0.25 | QUALIFIED for Phase 1 learnability tests |

Not decided here: whether the structure is learnable beyond baselines for **unseen** implementations. That is Phase 1
proper and needs its own frozen protocol.
