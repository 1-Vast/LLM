# Selection-rule choice: pre-declared criterion

Written 2026-10-17T04:21Z, before the two proxy menu runs (`v2_menu_w16_b4`,
`s_v2_menu_w16_b4`, running since 03:44Z) had written any output. This file is hashed by the
freeze.

## What had been seen when this was written

The PRISM 19Q4 selector menus (W = 32, k = 8, version-2 fit), for both rules of `procedure.choose`:

| Regime | Rule | Folds that bridge | Ranks | Mean hits per line |
|---|---|---|---|---|
| Line holdout | evidence | 5 of 5 | 20–40 | 2.643 |
| Line holdout | max | 5 of 5 | 20–40 | 2.644 |
| Lineage holdout | evidence | 2 of 5 | 5–10 | 1.903 |
| Lineage holdout | max | 5 of 5 | 10–40 | 2.190 |

For reference, the fixed lookahead bridge at rank 40 gives 2.673 (line) and 2.275 (lineage), and
the Virtual Cell alone at rank 40 gives 2.298 and 1.935.

Also seen earlier: selector variant A (`procedure_variant_a.py`) on both proxies. That rule
switched to a bridge on any positive inner gain and fell below a fixed Virtual Cell.

So the evidence rule is too conservative when whole lineages are held out: both its one-SE
rank rule and its z threshold cost hits there. A no-margin rule followed inner noise on the
proxies.

## Candidate rules

All three are pure functions of the same inner records, so no new compute is needed:

* `evidence`: the one-SE rank rule on `vc0`, then a bridge only if its inner z > 1.645.
* `max`: the best mean rank on `vc0`, then any positive inner bridge gain.
* `hybrid`: the best mean rank on `vc0` (as `max`), then a bridge only if its inner z > 1.645
  (as `evidence`).

## Criterion

There are four development settings: PRISM line, PRISM lineage, proxy random and proxy
structured. In each setting S:

* The best fixed pipeline F*_S is the highest mean outer hits of any single (rank, procedure)
  over {5, 10, 20, 40} × {`vc0`, `b_exploit`, `b_lookahead`}. It is read from the menu's outer
  records and used for every fold. This is a hindsight comparator.
* A rule's relative regret in S is (F*_S − rule mean hits) / F*_S.

The frozen rule is the one with the smallest maximum relative regret over the four settings. A
difference of less than 0.5 percentage points counts as a tie. Ties go first to `evidence`, then
to `hybrid`, because both spend fewer extra assay rounds than `max`.

The criterion and the result are reported in PROTOCOL.md §9.5. No other rule is considered.
