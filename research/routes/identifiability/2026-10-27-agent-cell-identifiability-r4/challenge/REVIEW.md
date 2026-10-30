# REVIEW — E004 noise calibration and the A673/BJ order crossing

Independent re-analysis of `PAIR_SCREEN.csv` (139,764 rows), then an audit of `PROTOCOL.md`,
`PROTOCOL_AMENDMENT_001.md`, `e004_noise_calibration.py`, `E004_RESULTS.json`. Stage-1 output was
written before any was opened.

## Stage-1 numbers

Same-layout, same-cell replicate plates give a truncation-free handle. With diff(w) = y₁−y₂ and
E[diff] = 0, D = diff(w₁)−diff(w₂) has Var(D) = 2Var(d). At the probes' geometry and band
(0.55–0.95, unclipped, **n = 5,355** adjacent-column pairs): **Var(d) = 0.003516,
SD(contrast) = 0.0593**.

d̄(A673) = **+0.277476** (0.303136/0.251816); d̄(BJ) = **−0.034535** (−0.020518/−0.048552).
SE = SD/√K, K = 2 → A673 t = **+6.62**, BJ t = **−0.73**. Across eight defensible estimates
(SD(contrast) 0.0577–0.0947): A673 significant **8/8** (t 4.15–6.81), BJ **0/8** (t −0.52 to −0.85).

## Verdicts

**1. Decomposition — holds with caveat.** σ√(2/K) is right and the plate offset does cancel in-file
(mean |offset| 0.0114, correct σ_b 0.0113; Var(mean Δ) predicted 0.000270 vs 0.000256 observed).
But N2's σ_b = 0 is a **structural artefact**: the offset is constant within a file pair, so it
cannot enter a variance taken across wells; √(SD²/2−σ_e²) is zero in expectation (I get −0.000116).
Reporting 0 as a measurement is wrong. The genuinely omitted components — level heterogeneity and
borrowed σ_e — both shrink SE, so the negative BJ verdict is conservative and the positive A673 one
over-confident.

**2. Exchangeability — fails.** All 4,883 duplicate pairs come from validation-format plates (rounds
10 and 15); **none** from the four probe files or any stage-11 primary plate. Probes sit in a 16×24
grid, duplicates in 2×2 quadrants. σ_e has no support from the design it is applied to. The author's
positional check (same column 0.0378 → adjacent 0.0394 → ≥2 apart 0.0457) points the safe way and my
stage-11 figure (0.0472) agrees — benign here, but asserted, not tested.

**3. Controls and 0/1 — holds.** Reproduced: σ_e 0.018023 (n = 233,696) with anchors, 0.044587
(n = 4,883) without; anchors are 96.25% of naive pairs. In the same [0.75,1] window, keeping clipped
wells gives 0.034894 vs 0.040762 after dropping — dropping raises σ 17%, the right direction.
Survivors stay ceiling-truncated, biasing σ low: anti-conservative, protecting the negative claim.
The amendment's counts are wrong: 231 files have exactly 16 high controls (not 462); 234,240
both-anchor pairs (not ~5.5×10⁴); 43.8% exact zeros (not 99%).

**4. Level matching — wrong window for A673; conclusion unaffected.** The amendment justifies
[0.75,1] by pair means (0.78/0.81) while noting the wells span 0.63–0.94. A673's O2 sits in
[0.5,0.75), where σ_e = 0.0589. Level-mixing gives √(0.0589²+0.0408²) = 0.0716 vs √2·0.0408 =
0.0577, so A673's t = 6.81 should be ≈5.5. BJ's wells are both inside the window, so its matching is
sound. No verdict flips.

**5. Probe extraction — holds exactly.** All eight wells verified: names, both doses, Iteration 11,
Failed QC False, y matching to **0.00e+00**. Per-plate d to 4 dp: A673 +0.3031, +0.2518; BJ −0.0205,
−0.0486. Caveat: the assertion compares only *sorted* drug names and *sorted* doses, so it would
pass if doses were swapped — harmless at 0.1/0.1 µM but weaker than it looks. Both cells also probe
the **same compound pair with Drug1/Drug2 swapped**, which no text records.

**6. Power — arithmetic holds, interpretation does not.** 1.96·SE and 2.4865·SE reproduce to the
digit (0.07989, 0.10135); plates-needed reproduces 17.226. But one-sided power is applied against a
**two-sided** 1.96 criterion — the consistent figure is 21.9, 27% larger. A673's 0.267 plates is not
reportable. Worst, it conditions on the observed d̄ as truth: for BJ, whose d̄ is inside the noise
band, "17 plates" presupposes an effect not established — and no further replicate plates exist.

## Decision rule and overstatements

Correctly applied: |d̄_BJ| 0.0345 < 1.96σ_e 0.0799 → "crossing not established", the pre-registered
branch. The amendment is an honest, validity-driven correction that strengthens the negative claim,
and the author says so. Two overstatements: `empirical_placement` compares a 2-plate mean against a
single-pair |Δ| null (SD σ, not √2σ), so A673's "0.0008 tail" is wrong by orders of magnitude and is
not parameter-free for the statistic used; `cells_quiet_enough` pits other cell lines' σ against
|d̄_BJ|/1.96, a ~9%-uncertain descriptive sensitivity presented as evidence. The
difference-of-differences is 0.3120 ± 0.0577, t = 5.4: the contexts clearly *differ* — heterogeneity,
not a sign reversal. The author is right to test BJ against zero, but the distinction bounds how the
negative result reads.

## The observation that would overturn it

Both error terms are blind to a **deterministic row/column effect shared by all replicate files**: it
cancels from σ_e (duplicates share positions) and from σ_b (identical layouts), yet enters the BJ
contrast directly, since N22 and O22 differ by one row. A row-O − row-N offset of ≥0.035 would
explain the entire BJ effect. I bounded it at **+0.0082 ± 0.0038** (t = 2.18) from the high-control
strips — four times too small — so the conclusion survives, but this is the component the design
cannot see.

## Ran vs. reasoned

**Ran:** probe extraction; five noise families (eight estimates); exact re-implementation of N1/N2 —
all six published σ_e values and pair counts reproduce; level bins; clipped-kept vs dropped;
duplicate provenance by iteration; correct σ_b; truncation-free raw-count contrast; row/column
detrending; difference-of-differences; all power arithmetic. **Reasoned only:** which column is the
true readout — `Viability` is not an affine function of `Raw count` (residual 2.4–4.5%,
row-structured) and the two imply contrast SDs of 0.059 and 0.090; I bracketed verdicts across both.
No biological interpretation is offered.
