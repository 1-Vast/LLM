# CHALLENGE R7 — E008

All results reproduce; scripts `c1`–`c7` here.

## 1. LEAKAGE — fails as worded

Leave-two-cells-out is honest: training indicators come only from cell pairs excluding both held-out cells. But this is a **batch leak**. Every layout carries `Iteration = -1` (free text coerced to NaN), so there is **no day/batch key at all**. Of 1,827 compound×concentration identities in the nine layouts, **zero** recur in another layout; only 2 of 165 designs span ≥2 iterations, both with three cells, where leave-two-out leaves one training pair. **No cross-batch test is constructible from this file.** "Unseen cells" covers cell identity only — 11 cell lines, RPE present in 9/9 layouts. Plate map, dispense, day, QC are shared. Independent replication needs the same compounds re-plated in a new batch with permuted positions.

## 2. SPACING — holds

Pair-level spacing (mean `min(gap)` across training cells — the baseline the protocol omitted) gives AUC **0.812**, *below* the protocol's 0.828; adding M2 still yields +0.067 [0.050, 0.087]. AUC(M2) stays 0.90–0.94 within pair-gap quintiles. Removing the near-tie band *raises* AUC (0.869 → 0.904 → 0.965). Reversal between twin plates of the **same** cell line is near zero, far below the 3.1% cross-cell rate; random noise cannot manufacture this.

Caveat: the propensity reproduces across twin plates at r = 0.834, but a *stable* per-well bias gives that too; it excludes flicker, not bias. And the object is not the pair — per-well + spacing = 0.906 vs 0.921, so the pair term adds **+0.015**, positive in only 34% of cell pairs. "Drug-pair's ordering" over-specifies; it is a *regimen* crossing its partners'.

## 3. AUC AND LIFT — fails as a practical claim

0.916 is the n-weighted mean over **136 of 176** cell pairs; the 40 dropped are the zero-positive ones. Both sets hold the same 606 positives; the exclusion drops 4,092 negatives and **zero** positives, so the rise is mechanical (0.8746 vs 0.8691 pooled). Deployable: **0.869**. 38% of the 136 have one positive, 51% fewer than three. Positives sit on **195 of 1,928** readable unit pairs, so top 5% = 1,063 rows ≈ 100 pairs × 10 cell pairs: "57% recall" is 57% of *rows* over ~195 objects, and 11x restates R6's ICC 0.294. Prediction is retrospective — r(a,b) presupposes both were measured; a new cell line with 0–1 plates is untested (H013 concedes this). At 32% precision two of three flags are wrong.

## 4. POSITIONAL — fails

It removes 9.7% of observations, only **30** same-row; a rank statistic over 17k observations cannot respond, so 0.8746→0.8749 is a null from a powerless control. Wrong level too: a per-well bias belongs to each well, so excluding pairs whose two wells share a row or column leaves every pair containing the biased well. They found the artefact and read it backwards: same-column pairs reverse at 0.0292 vs 0.0542, same-row 0.0375 vs 0.0542 — rate depending on geometry *is* a layout signature. The check they skipped — perimeter enrichment — I ran: reversal pairs are **under**-represented at the edge (9.4% vs 15.2%), which disfavours the crude edge artefact but not identity ≡ position.

## 5. HETEROGENEITY — fails

Only **6 of 9** layouts contribute a scored cell pair; `"layouts": 9` is the number *built*, and the three dropped hold the only MDA-MB-231, MSKRMS-12808 and Wit49 data. Layout `7c8d0d499c92` has AUC 0.66 and d(M3−M1) = **+0.005**, positive in 50% of its 6 cell pairs — by H012b's own logic that regime supports only "spacing". 17.6% of cell pairs have a negative increment. The rule (weighted mean, clustered CI > 0) cannot fail on any single layout, so the protocol cannot report a failing regime; per-layout reporting was permitted, not required, and is omitted. Six clusters is too few for the bootstrap.

## 6. CHEAPEST FALSIFICATION

Cheapest, compute-only, decisive for the wording: **count compound identities shared between layouts → 0/1,827.** That kills "transferable" and "not a well-position artefact" without modelling. For the AUC I ran the four likeliest breaks (pair-level spacing, floor removal, within-plate flicker, per-well null); **none reduced 0.869**. Killer experiment: re-plate the same compounds in a new batch with permuted positions and new cells; new-batch AUC ≈ 0.5 while within-batch stays 0.87 ⇒ batch/position property, claim dead.

## Minimum requirements before this counts

1. Pooled 0.869 as headline; label 0.916 "n-weighted mean over non-empty cell pairs".
2. State `Iteration` is unusable; all evidence is one validation-plate set. Drop "transferable".
3. Replace "not a well-position artifact" with "untestable": 0 compound identities recur across layouts. Report the same-column gap and edge result.
4. Report all six contributing layouts, including `7c8d…` (0.66, +0.005); 3/9 contribute nothing.
5. Re-specify the unit as per-regimen instability, not per-pair; cluster the lift on ~195 pairs as retrospective.
6. Show one decision that changes, or withdraw the practical claim.
