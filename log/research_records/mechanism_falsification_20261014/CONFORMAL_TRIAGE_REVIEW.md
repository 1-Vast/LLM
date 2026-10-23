# Conformal selection for drug triage: review

Labels throughout: **guarantee** (a theorem under stated assumptions), **simulation** (synthetic, seeded),
**exploratory observation** (real data that earlier studies exposed). They are never merged. The
selective-hit-triage study is frozen; nothing here changes it, and its 38 `ML+context` hits are a post hoc,
exploratory T1 comparator, not independent confirmation.

## 1. Guarantee (theory, RECALLED)

Conformal p-values for a binary outcome (Jin and Candès 2023): for test unit j,
`p_j = (1 + #{calibration non-hits with score >= score_j}) / (n + 1)`. With calibration and test units
**exchangeable** and the p-values PRDS, Benjamini-Hochberg at level q controls the false discovery rate at q for the
*test* selection. Weighted p-values extend this to covariate shift when `P(Y|X)` is unchanged and the density ratio
is known. Nothing else is guaranteed. Marginal 90 percent coverage per unit does not bound the ratio of false to total
selections.

## 2. Simulation ([conformal_sim.py](conformal_sim.py), 300 repetitions, q = 0.1)

| Scenario | Mean FDP | Share of runs with FDP > q |
|---|---|---|
| Exchangeable | 0.092 (se 0.004) | 0.46 |
| Covariate shift, unweighted | 0.176 | 0.97 |
| Covariate shift, true-ratio weights (plain weighted p-values + BH) | 0.074 | 0.39 |
| Conditional shift (P(Y\|X) weaker in test), unweighted | 0.224 | 0.86 |
| Conditional shift after covariate weighting | 0.171 | 0.69 |
| Clustered test units (shared latent) | 0.150 | 0.61 |
| Interval selection (90 percent lower bound > c), exchangeable | 0.022 | 0.10 |
| Interval selection, conditional shift | 0.069 | 0.33 |

Reading: the exchangeable row is the theorem working (mean at about q; a 0.46 share of runs above q is expected for
an FDR, which controls the mean). Unweighted shift, conditional shift and clustering each break it, and weights on X
do not repair a conditional shift. The interval-selection rule was conservative in these settings (low power); the
simulation does **not** show it failing, only that no theorem covers it. The weights are the true ratio, not the
pruned WCS procedure, and real ratios must be estimated.

## 3. Real data ([conformal_triage.py](conformal_triage.py)): exploratory, exposed, post hoc

Unit: compound-cell pair. Outcome: the registered validated selective hit in CTRP v2. Scores: `ML+context`, `ML`,
`D3` (deterministic), line prior. 10 random repeats per regime; test base rate 1.99 percent (1,076 validated of
54,130 evaluable pairs; 128 compounds).

| Regime | Setting | What conformal+BH did at q = 0.1 / 0.3 (ML+context) |
|---|---|---|
| R1 | random compound split inside development | selected 4.9 / 41.4 pairs; FDP 0.26 / 0.35 |
| R2 | development split by mechanism family | selected 40.6 / 384; FDP 0.58 / 0.69 |
| R3 | development to the frozen family-disjoint test | selected 4.3 / 20.9; FDP 0.58 / 0.70 |

Observed FDP exceeds q in every regime, including the one nearest exchangeability (R1), where pairs of one compound
remain correlated. Weighted p-values in R3 selected **nothing**. The exploratory conclusion is that BH-on-conformal
does not deliver its nominal level here, and that the failures match the three broken assumptions in section 2
(clustering, family shift, a base rate that moves between splits: development 2.86 percent, test 1.99 percent).

### Structural power limit (arithmetic, not an estimate)

The smallest conformal p-value is `1/(n+1)`. BH rejects k units only if `1/(n+1) <= q k / m`. For m = 54,378 test
pairs and q = 0.1, rejecting a single pair needs **n >= m/(q k) = 543,780 calibration units**; there are 15,955. The
procedure can reject only when the pool is small or the calibration set is far larger than any assay here provides.
That is why R3 selects so few.

### Matched-budget top-k, development-fit models, frozen test ([CONFORMAL_TRIAGE.json](CONFORMAL_TRIAGE.json))

Hits among the top k pairs over the whole test pool. These counts are **not comparable** with the frozen study's 38,
which came from per-campaign nominations of 16 compounds.

| k | ML+context | ML | D3 | line prior | ML+context minus D3 (95 percent bootstrap) |
|---|---|---|---|---|---|
| 50 | 15 | 13 | 8 | 2 | +7 [-3, 24] |
| 100 | 34 | 19 | 11 | 2 | +23 [8, 43] |
| 250 | 63 | 46 | 28 | 14 | +35 [11, 67] |
| 500 | 105 | 77 | 47 | 24 | +58 [21, 107] |
| 1000 | 145 | 116 | 80 | 33 | +65 [25, 112] |

`ML+context` has more hits than the deterministic D3 at every budget, with an interval that excludes zero from
k = 100. Against `ML` the intervals include zero at every k. False discovery proportions stay at 0.66 to 0.85, and
65 to 79 percent of selections fall in pan-active compounds (compounds that hit across many lines), which is the
easy region. Clustering is strong: at k = 500 one mechanism family supplies 30 hits from 110 selections, another 0
from 19. All of this is **exploratory**: the same split was exposed to the frozen study, and choosing `ML+context`
was itself post hoc.

## 4. What may and may not be claimed

* May claim: the conformal-selection guarantee does not apply to this pool as built (exchangeability fails;
  structural power bound; family shift), and observed FDP exceeded nominal q in all three regimes on exposed data.
* May not claim: that conformal selection cannot work for triage in general; that `ML+context` is validated
  (it is an exploratory comparator); that any FDR control, "no-harm guarantee" or calibrated error rate exists for
  the heuristic gates in this repository.
* What could change it: calibration on the order of 5 x 10^5 labelled pairs, or a much smaller candidate pool; a
  split that is exchangeable by design (families as the unit, calibration families drawn like test families); a
  pre-registered, untouched test release. None is available here without a download that was not authorised.
