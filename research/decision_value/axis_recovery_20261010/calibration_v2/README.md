# One adaptive supplementary axis calibration

The frozen supplementary panel provided enough nonzero observations, but **did
not establish unique coordinate identity**. Independent replay reproduced
16/39 passing coordinates in c44 and 23/39 in c45. The all-39 gate remains
blocked for both files. These are calibration results, not evidence for or
against the decision effectiveness of STATE, MAP or an agent.

## Design and provenance

This was one explicitly adaptive supplement following the preserved first-stage
index-support failure. Public named summaries guided conditions; they did not
authenticate hidden columns or establish detection probabilities. The source
revision remained `fdf87abece385feea6fa5e9944ab46e173b6af50`, with the same
39-coordinate endpoint, `log1p(stored normalized X)` transformation, absolute
tolerance `1e-5`, all-source-gene comparison and 2-discovery/1-holdout nonzero
criterion.

Offline cost review found that complete coverage of the named positive-hint
requirements required at least 10,652,056 index bytes under the registered
condition limit. Earlier six-condition and partial-cover planning freezes were
preserved. Before any supplementary indices were read, the root registered a
budget amendment from 25 to 28 MB combined known application-received bodies,
leaving the global 60 MB task cap unchanged. `inputs/BUDGET_AMENDMENT.json`
retains that decision. The final panel contained 15 new conditions plus the
prior seven, providing 3,354 full-QC cells. Actual sample, plate, label and cell
joins and all protected exclusions were independently reconstructed.

The frozen selection's original metadata/error reserve was a planning estimate
of 102,100 bytes. Actual supplementary metadata cost 456,928 bytes. The binding
28 MB cap allowed 950,044 bytes after the exact index projection and 4 MB paired
reserve. `BUDGET_RECONCILIATION.json` records this difference; the parent's
pre-index review hash-bound it without changing the selection or scientific
acceptance rule. `PREPARATION_FIX.json` also discloses a metadata-only mixed
list/tuple span error corrected before the index freeze. No source body or old
freeze was removed.

## Actual result and failure mechanism

The full combined index pool passed the necessary three-occurrence screen for
all 39 genes in each file. A compact greedy allocator reserved separate holdout
coverage, then discovery coverage; it did not fill every condition to an
arbitrary cell quota and does not claim global optimality. The paired freeze
contained 74 cells:

| File | Discovery | Holdout | Coordinates passing both checks |
|---|---:|---:|---:|
| c44.h5ad | 19 | 9 | 16/39 |
| c45.h5ad | 32 | 14 | 23/39 |

Every failing coordinate had at least two nonzero discovery values and one
nonzero holdout value. The obstruction was instead multiple source-gene
trajectories matching the discovery coordinate within tolerance. For example,
c44 CD38 had 20 matching source columns, CCND2 had 24, IFNB1 had 2 and TNF had 6.
c45 CD38 had 3, HGF had 11 and TNF had 3. A sparse panel chosen only to cover
positive occurrences can leave coincident single-count/co-expression patterns
indistinguishable. A public gene name or another file's identity does not resolve
that ambiguity.

This exposes a concrete limitation of the allocator: nonzero coverage is a
necessary condition for identity, not a sufficient one. An exploratory repair
could inspect the already retained index trajectories for cells that separate an
expected gene from competing genes, including informative zero contrasts. Such
a diagnosis is distinct from this completed failed protocol; its result cannot
replace the frozen discovery or consume the existing holdout as a new discovery
set without explicit disclosure.

## Cost, verification and scientific boundary

Supplementary known application-received bodies were 12,135,372 bytes: 456,928
metadata, 10,652,056 indices, 434,388 selected CSR values and 592,000 selected
complete X_hvg vectors. Combined with stage 1, the retained known total was
**24,533,272 bytes**, below the amended cap. The earlier stage-1 interrupted
metadata transport caveat remains: these are known application-delivered body
bytes, not a complete wire-traffic measurement.

Both immutable freezes, source hashes, ledger prefixes, original cache receipts,
official sample joins, deterministic index allocation, exact selected ranges,
all-source-gene discovery matching and fixed-index holdout checks were
independently replayed without producer imports or new network calls. The
separate receipt is `../design/CALIBRATION_V2_VERIFIED.json`.

`RESULTS.json` and `CERTIFICATE.json` record
`BLOCKED/INSUFFICIENT_COORDINATE_INFORMATION`. No full 2,000-gene axis, STATE
decoder axis, P0.6 sentinel gate, old 250-cell noise gate, biological functional
endpoint or decision benefit was certified. Production modules and model
weights remain unchanged.
