# Stage 1 — independent noise estimate and identifiability verdict

Input: `research/eight_directions_20261026/evidence_audit/raw/PAIR_SCREEN.csv` (139,764 rows,
371 files, 19 cell lines, 20 iterations). Script: `stage1_noise.py`. Machine output:
`independent_estimate.json`, `stage1_log.txt`. Written before opening any result file of the
audited analysis.

## Contrast under test

d = Viability(w1) − Viability(w2) within one file; the reported quantity is the mean over K = 2 files.

## Data hazards found, and what I did about them

1. **Truncation at the normalisation bounds.** 30,259 wells (21.6%) are exactly 1.0 and 6,646
   (4.8%) exactly 0.0; 26.4% of all rows sit on a bound, and no value falls outside [0,1]. The
   upper bound is not rare at the probe level — in Plate 157, 15% of wells in the probe column
   band are clipped at 1.0. Any noise estimate that pools raw `Viability` differences is therefore
   biased **downward**, because pairs of wells that both sit at 1.0 contribute a difference of
   exactly 0. *Handling*: I estimate noise on (a) unclipped wells only and (b) raw counts, which
   are never truncated, and I report the clipped and unclipped estimates side by side so the size
   of the bias is visible rather than assumed.
2. **"High control" / "low control" rows are degenerate.** All 16 high-control wells per plate are
   forced to exactly 1.0 and all low controls to 0.0 in 61.5% of files; overall 2,528 of 8,576
   high-control wells (29.5%) are below 1.0 and 2,329 of 8,576 low controls (27.2%) are above 0.0,
   in the 143 files whose normalisation used a wider denominator than the plate's own control mean.
   Using control wells as replicates would be using a quantity that the normalisation defines,
   not measures. *Handling*: controls and `dmso` rows are excluded from every noise estimate.
3. **Normalisation is not uniform across the archive.** Viability ≈ (Raw − mean LC)/(mean HC − mean LC),
   clipped at [0,1]: regressing Raw on Viability per file gives slope/(HC−LC) median 1.0039
   (IQR 0.9982–1.0139) and intercept−mean LC median −13.7 counts, over 371 files. But the relation
   is *not exact*: residual SD is 2.4–4.5% of the mean count and is dominated by a row gradient
   (residual correlates with row at r ≈ −0.5, with column at r ≈ −0.06). So `Viability` is not an
   affine rescale of `Raw count`; it appears to have absorbed a row-position correction. I used
   `Viability` as the readout (as instructed) and used the raw-count ratio as an independent
   cross-check of each contrast (see §5).
4. **Duplicated values.** There are no duplicate `Well` labels within a file and no exact duplicate
   rows, so the "duplicates" are not data corruption. The duplication is *experimental*: repeat
   wells of the same condition. These exist in 143 files but **not in the four probe files** — the
   stage-11 primary-screen plates (Plate 157/158, 147/148) contain exactly one well per condition,
   so their only within-plate replicates are the control strips.
5. **Positional effects.** Rows A–P of the primary screen *are* the Drug-2 identity and columns are
   the Drug-1 identity, so at a single well a position effect cannot be separated from a compound
   effect. Two things *can* be measured: (i) the high-control strip spans all 16 rows at one column
   and shows a smooth row gradient from +0.024 (row A) to −0.034 (row M) in viability units
   (SD across rows 0.019); the row-O − row-N offset is +0.0082 (SD 0.072, n = 368, t = 2.18).
   (ii) In the 143 plate formats that place high controls in two or more *adjacent columns*
   (cols 1–2, or 11–12–13), the mean adjacent-column offset is −0.0010 viability units
   (col 1 vs col 2: −0.0014, n = 1,992) — i.e. **no measurable column-position bias** at the control
   level. The apparent column-1 depression in the marginal means (0.27 vs 0.57) is *compound
   composition*, not position, and is not evidence of an edge artefact. *Handling*: I report the
   row offset as a bias term for the BJ contrast (its two wells are 1 row apart) and treat
   column-position bias as bounded by ±0.002.
6. **QC.** 3,828 rows (2.7%) are flagged `Failed QC`; none of the eight probe wells is flagged.
   Flagged wells are excluded from every noise estimate.
7. **Replicate files are independent plate preparations, not re-reads.** Plate 157 vs 158 and
   Plate 147 vs 148 share an identical well→condition layout but share no raw count (0% identical
   values; correlation 0.988–0.996). They are usable as replicates; a re-read of one plate would
   not have been.

## Noise model and estimators

V_i(w) = mu(w) + p_i + e_i(w): p_i is a plate offset, which cancels inside a within-plate contrast;
e_i(w) has SD sigma with within-plate correlation rho between two well positions. Then
Var(d_i) = Vd = 2·sigma²·(1−rho) and SE(dbar) = sqrt(Vd/K); with K = 2, SE = sqrt(Vd/2).
The model family used by the audited analysis is the case rho = 0, SE = sigma·sqrt(2/K).

**Primary estimator P — direct measurement of Vd.** Replicate plates give diff(w) = V_1(w) − V_2(w)
with E[diff] = 0 for the same well. For two wells, D = diff(w1) − diff(w2) has E[D] = 0 and
Var(D) = 2Vd, so Vd = Var(D)/2 — with no assumption about rho, no assumption that the two wells have
equal variance, and no leakage of the true compound effect (which differences out). I evaluate it on
the (row, col) grid at the two geometries that match the probes and inside the viability band the
probes actually occupy (0.55–0.95, both wells unclipped, neither QC-flagged).

| estimator | definition | SD of contrast (√Vd) | n |
|---|---|---|---|
| **P adjacent column** | replicate plates, wells (r,c),(r,c+1), band 0.55–0.95 | **0.0593** | 5,355 well-pairs |
| P adjacent row | replicate plates, wells (r,c),(r+1,c), band 0.55–0.95 | 0.0664 | 5,264 |
| P adjacent column, stage 11 only | as above, iteration 11 | 0.0510 | 955 |
| P adjacent column, all levels | band 0–1 | 0.0493 | 19,722 |
| E1 all levels | SD(Δ)/√2 over same-well replicate diffs | 0.0668 | 35,674 |
| E1 stage 11 | as above, iteration 11 | 0.0513 | 6,048 |
| E1 band 0.55–0.95 unclipped | as above | 0.0808 | 11,089 |
| E2 within-plate duplicates, all levels | SD/√2 | 0.0540 | 10,248 |
| E2 within-plate duplicates, window [0.75,1] | SD/√2 | 0.0491 | 6,981 |
| E2 within-plate duplicates, band, unclipped | SD/√2 | 0.0752 | 2,550 |
| E3 adjacent high-control columns, raw counts | SD/√2 ÷ (HC−LC) | 0.0720 | 2,664 |
| E4 Poisson counting floor | √(raw)/(HC−LC) | 0.0052 | 70,036 |

**The primary number: Vd = 0.003516 (adjacent column, probe band), SD of the per-file contrast
0.0593, n = 5,355 well-pairs, mean D = −0.0010 (i.e. E[D] = 0 verified).** Reading noise (E4) is
~11× smaller than this: the well-level variance is dominated by preparation/dispensing, not photon
counting, so a count-noise model would be wrong by an order of magnitude.

## Results

Probe extraction verified against the raw CSV (both drug names and both doses, all eight wells):

| cell | plate | w1 | condition | V | w2 | condition | V | d |
|---|---|---|---|---|---|---|---|---|
| A673 | 157 | O1 | Dexrazoxane 0.1 + Axitinib 0.1 | 0.934329 | O2 | Lestaurtinib 0.1 + Axitinib 0.1 | 0.631194 | +0.303136 |
| A673 | 158 | O1 | Dexrazoxane 0.1 + Axitinib 0.1 | 0.937061 | O2 | Lestaurtinib 0.1 + Axitinib 0.1 | 0.685245 | +0.251816 |
| BJ | 147 | N22 | Axitinib 0.1 + Dexrazoxane 0.1 | 0.879078 | O22 | Axitinib 0.1 + Lestaurtinib 0.1 | 0.899596 | −0.020518 |
| BJ | 148 | N22 | Axitinib 0.1 + Dexrazoxane 0.1 | 0.858444 | O22 | Axitinib 0.1 + Lestaurtinib 0.1 | 0.906996 | −0.048552 |

So the two supposedly different probes are the *same pair of compounds* — Dexrazoxane vs
Lestaurtinib, both 0.1 µM, against Axitinib 0.1 µM — with the Drug1/Drug2 roles swapped between
cell lines. That is a property of the data, not of the analysis.

dbar(A673) = **+0.277476**, dbar(BJ) = **−0.034535**.

| | SE (primary) | t | verdict |
|---|---|---|---|
| A673 | 0.0419 | **+6.62** | distinguishable from zero |
| BJ | 0.0470 | **−0.73** | not distinguishable from zero |

**Verdict.** A673's contrast is detectable under **all 11** estimators (t = 4.86–7.70 for every
physically plausible one; the Poisson floor gives t = 75). BJ's is detectable under **1 of 11** —
only the Poisson counting floor, which is not a defensible model of well-level error here
(it is ~11× too small). Under ten independent estimates with SD of the contrast between 0.049 and
0.081, BJ's t ranges −0.99 to −0.60, all non-significant. The A673/BJ distinction is therefore
**not** an artefact of the noise model: it holds for every defensible choice and the primary
direct estimate puts A673 at 4.7 SD of the per-file contrast.

## Two facts that limit how far this can be pushed

* **Bias check on the readout.** Using raw counts instead of Viability — d_raw = (raw1−raw2)/(mean HC − mean LC),
  which is immune to the truncation and to whatever correction `Viability` carries — gives
  dbar(A673) = 0.283806 (vs 0.277476, Δ = 0.0063) and dbar(BJ) = −0.035033 (vs −0.034535,
  Δ = 0.0005). Both leave the verdicts unchanged, but the per-file agreement is only 0.003–0.016.
* **A positional bias the design cannot remove.** The BJ wells differ by one *row*, and the
  high-control row profile shows a row-O − row-N offset of +0.0082 (t = 2.18). That biases BJ's d
  downward by ≈0.008, moving it to −0.026 — still non-significant. For A673 the two wells differ by
  one *column*, and the adjacent-column control offset is −0.0014 ± 0.0023, so a column-position
  artefact of the size needed to explain 0.277 (11 SE) is excluded.
  Because rows and columns of this screen *are* compound identity, the possibility that a
  plate-position effect is aliased with compound identity can be bounded but not eliminated from
  this archive alone. Note also that the same compound pair, inverted in sign, gives +0.277 in one
  cell line and −0.035 in another at the same doses; no noise model can attribute that difference
  to measurement error, but this analysis makes no claim about what does cause it.
