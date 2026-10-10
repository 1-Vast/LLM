# Offline adaptive supplementary calibration planning

The first frozen index screen examined 1,042 full-QC calibration cells and found
fewer than three CSR-index occurrences for five c44 genes and ten c45 genes.
Those results remain unchanged. The supplementary proposal uses only already
consulted plate-1 named summaries, exact retained source-QC code arrays, and CSR
row pointers. No new network request, CSR-index acquisition, raw value, or HVG
read occurs in this directory.

The initial frozen greedy plan favored deficit-weighted positive hints and
selected six conditions costing 8,141,672 index bytes. It left seven hint
requirements unmet. `cost_review/` then solved the binary condition multicover
problem before any supplementary acquisition: minimize bytes, with at most eight
new conditions per file. Complete named-hint coverage requires at least
10,652,056 bytes; it cannot fit the original 8.5 MB index allocation. A budgeted
fallback reduced total hint shortfall to three, using 8,241,100 bytes. Both
planning stages and their freezes remain retained.

The parent selected one full supplementary attempt and raised the combined
calibration body limit from 25 MB to 28 MB before any supplementary indices were
read. The overall discovery limit remains 60 MB. `cost_review/full_cover/`
contains the final canonical minimum-cost full-hint proposal: seven c44 and eight
c45 conditions, 2,312 full-QC rows, and 10,652,056 projected index bytes. Including
the prior 12,397,900 bytes, 4 MB reserved for paired raw/HVG values, and 102,100
bytes for metadata/errors gives 27,152,056 bytes. The separate parent budget
amendment and calibration freeze govern actual acquisition.

Full-hint selection first minimizes exact integer index bytes. It then fixes the
minimum cost and prefers bit 1 whenever feasible, in ascending file/label order,
to produce a unique panel. Every candidate has at least 50 exact full-QC cells,
matches official plate/sample/condition metadata, excludes protected sentinel
labels and pooled samples, and excludes the seven old selected conditions in
its own file. The old seven conditions remain available as screened support.

These are planning claims about positive named deltas. They do not imply that
the selected source rows contain enough nonzero observations or that any hidden
HVG column is correctly named. Actual index support and independent paired
numerical authentication still determine whether the axis gate passes. All
consulted plate-1 units remain excluded from independent terminal decisions.
The endpoint, uniqueness requirement, model weights, and paired-cell cap of 256
are unchanged.

Offline checks:

```powershell
python research/decision_value/axis_recovery_20261010/informative_v2/verify.py
python research/decision_value/axis_recovery_20261010/informative_v2/cost_review/full_cover/verify.py
```

The first check reconstructs all 156 candidates' source-QC rows and byte costs,
and the initial greedy plan. The second independently re-solves the final
multicover objective and checks all 15 hint constraints, proving the finite
planning minimum with zero network calls and no acquisition-producer imports.
