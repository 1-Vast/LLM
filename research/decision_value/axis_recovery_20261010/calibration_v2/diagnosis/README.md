# Why positive-occurrence coverage did not identify the axis

This frozen **offline diagnostic** found a concrete defect in the compact cell
allocator. The existing index pool contains enough distinguishing support
patterns, but the allocator selected cells to cover nonzero occurrences rather
than to distinguish gene identity. No new source bytes, CSR values or X_hvg
vectors were requested or decoded for this diagnostic. The registered numerical
failure and certificates remain unchanged.

For every expected endpoint gene, the diagnostic compares its binary CSR-index
presence trajectory with **all 62,710 source genes**, separately in each file.
The sparse implementation does not construct a dense cells-by-genes array.
It compares current discovery patterns, full already retained calibration-pool
patterns and a prospective expanded discovery panel. Existing holdout cells
are excluded from the expanded discovery allocation.

| File | Current discovery cells | Unique binary trajectories now | Unique trajectories in full retained pool | Additional distinguishing discovery cells | Prospective discovery cells |
|---|---:|---:|---:|---:|---:|
| c44.h5ad | 19 | 15/39 | 39/39 | 11 | 30 |
| c45.h5ad | 32 | 17/39 | 39/39 | 11 | 43 |

The deterministic greedy diagnostic chooses a row that removes the largest
inverse-competitor-weighted collection of current binary aliases, then prefers
a lower projected paired byte cost and a fixed hash. It adds informative
**presence/absence contrasts**, without filling condition quotas. All 39 binary
trajectories become unique in both prospective panels, within the previously
declared discovery ceiling. Existing holdout rows remain fixed at 9 and 14.
The method is a heuristic, not a proof that 11 is the smallest possible count.

The frozen numerical result had 16/39 and 23/39 passing coordinates, whereas
the binary diagnostic has 15/39 and 17/39 unique current patterns. Those numbers
need not agree: different positive magnitudes can separate equal binary
patterns. Conversely, explicit stored zeros or tiny values can make index
presence an imperfect proxy for numerical trajectories. Therefore binary
uniqueness is **not** a coordinate certificate and cannot replace the registered
value-level discovery and holdout checks.

The prospective extra raw-value ranges total 164,068 bytes and complete HVG
vectors 176,000 bytes. Their exact projected cost is **340,068 bytes**, giving a
hypothetical combined application-known total of 24,873,340 bytes. This is only
a range projection; none of those additional observations was read.

`FREEZE.json` bound the diagnostic code, protocol, result inputs and relevant
index bodies before output. `RESULTS.json` includes every binary competitor
count, proposed row, allocation step and projected cost. The closure excludes
changes to the parent execution evidence, whose completed failure remains
intact. This diagnostic identifies how a future protocol could select better
calibration cells; it does not reopen the completed one-supplement experiment,
release P0.6 or establish any decision gain.
