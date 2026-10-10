# P0.5R Extension: historical union and targeted identity discrimination

Both pinned data files now qualify their specified 39 endpoint coordinates:
**39/39 c44 and 39/39 c45**, uniquely matched against every one of 62,710
source genes with the original absolute tolerance of 1e-5. This is data-axis
qualification, not independent biological validation or decision benefit.

| File | Evidence used | Unique coordinates | Maximum mismatch | New RNA body bytes |
|---|---|---:|---:|---:|
| c44 / SW 1088 | 224 old controls + 19 exposed discovery + 9 exposed consistency cells | 39/39 | 1.441582098138383e-7 | 0 |
| c45 / SW 1271 | 32 old discovery + 11 newly frozen rows; 14 exposed consistency cells | 39/39 | 1.4611107745921004e-7 | 133,564 |

Source: `arcinstitute/State-Tahoe-Filtered` revision
`fdf87abece385feea6fa5e9944ab46e173b6af50`. The transformation is
`log1p(stored normalized X)` exactly once. In the inherited endpoint description,
"raw X" means this stored source matrix, not raw counts. The scalar endpoint has equal
positive weights +1/39; it is not apoptosis, viability or causal pathway activity.

## Registration and actual execution

The supplied exploratory archive was CRC/hash checked and retained under
`provided/`. Its scripts are evidence, not instructions. A separate registered
c44 audit reproduces the historical union. Without its nine exposed consistency
cells, the 243-cell union reaches only 38/39; TNF remains aliased with SDK2.
Adding those cells supplies identifying contrasts, not a new holdout.

Before acquiring c45, the proposed eleven rows were checked for source identity,
QC, discovery/consistency overlap and protected sample exclusions. A zero-gap
MILP proves a minimum of eleven added cells and a minimum gross payload of
133,564 bytes at that count **within the retained candidate pool and binary
alias constraints**. It does not prove global or numerical optimality.
`C45_FREEZE.json` binds rows, code, exact ranges and budget before acquisition.

One HEAD and 22 exact HTTP 206 ranges deliver 45,564 CSR value bytes and 88,000
complete HVG bytes. No retry or extra metadata/index acquisition occurs.
This is 60.7% less new expression payload than the old 340,068-byte proposal;
it is not a 60.7% saving in total research cost.

The initial frozen parser fails on an unretained HDF5 `X/indptr` metadata page.
`C45_NUMERIC.json` and `CERTIFICATE.json` preserve that failure. The separately
frozen `OFFLINE_REPAIR_AMENDMENT.json` uses already retained physical row ranges
and pointer arrays, adding **zero network bytes** and changing no scientific gate.
`C45_NUMERIC_RECONSTRUCTED.json` records the numerical result.

`repair_verify.py` reconstructs c45 through logical pointer offsets and HDF5
data/index slices, then compares all genes in blocks rather than using the
producer's row-by-row filtering. It shares the hash-checked retained-byte reader.
`VERIFIED.json` and `QUALIFIED_CERTIFICATE.json` record agreement and preservation
of all 3,334 protected old files. A separate agent reviews scope and hashes;
that review is distinct from the parent-run arithmetic reconstruction.

## Reproduction and release limits

The standalone `P05R_EXTENSION_REPLAY.zip` includes retained input bytes, freezes,
the original failed receipts and an offline replay runner. Extract into a new
directory and run `python verify_extension_replay.py` with the versions in
`requirements-extension-replay.txt`. The runner blocks sockets, regenerates the
four extension numerical receipts only in that copy and requires byte equality.
Five scientific counterexamples cover ambiguous positive trajectories, exposed
consistency, zero/duplicate names, tolerance and immutable output/cost accounting.

The old P0.5R and V3 conclusions remain unchanged. No full 2,000-gene axis or
STATE checkpoint output axis is certified. The old c40/c44 250-cell noise plan
remains blocked. P0.6's c44/c45 data-axis prerequisite is satisfied, but its new
controls, reference weights, shared-sample accounting, ranges and execution cost
still require a separate freeze; see `P06_READINESS.md`. No P0.6 expression or
P2 acquisition runs, production promotion, STATE inference or LLM experiment
is part of this extension. Its supported advance is cheaper elimination of
explicit competing coordinate identities, not a tested autonomous-agent advantage.
