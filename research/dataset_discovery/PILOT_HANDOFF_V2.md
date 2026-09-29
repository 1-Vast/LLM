# sciplex_pilot_v2 — Handoff (repair of sciplex_pilot_v1)

Status: **COMPLETE** — v2 built under `CONSTRUCTION_PROTOCOL_V2.md`, QA acceptance gate
**15/15 passed** (exit 0), 28 focused regression tests pass, byte-level deterministic
rebuild verified (two consecutive builds produced identical output file hashes).
This is a repair protocol written **after** exposure to v1 results and
`PILOT_REVIEW.md`; it is not prospectively registered. Development-only. Not committed.

## 1. What the v2 products are

`data/processed/sciplex_pilot_v2/`:

| File | Contents |
|---|---|
| `pilot_manifest.json` | protocol pointer; source/sheet/HGNC/builder/QA sha256; preprocessing provenance; grouping & control rules; mapping census; quarantine counts; output content hashes; use restrictions; built_at (separate from content hashes) |
| `observation_provenance.csv` | 238 condition rows: full two-intervention identity, cell/plate, control key + matching rule, availability, unavailability reason, n_cells, n_wells |
| `condition_classification.csv` | complete classification per condition (vehicle / agent1_only / agent2_only / combination) |
| `well_summaries.csv` | 816 per-well records (192 sciPlex2 + 624 sciPlex4) with cell counts |
| `response_arrays.npz` | means/effects per study on the ORIGINAL 58,347-feature axis, plus per-well mean blocks; effects use NaN exactly where contrasts are unavailable |
| `response_genes.txt` / `response_index.csv` | original feature axis; per-row availability/contrast kind |
| `gene_mapping.csv` | row-level stable-ID-first mapping (columns per protocol §6) |
| `quarantine_ledger.csv` | 569 cells (529 sciPlex2 dose+well missing; 40 sciPlex4 all-fields missing) with source row ids and reasons |
| `unavailable_contrasts.csv` | 144 sciPlex4 contrasts without same-plate control, with reasons |
| `rescue_contrast_ledger.csv` | 576 records (96 combinations × 6 registered contrast kinds), all unavailable |
| `sample_sheet_reconciliation.csv` | real key-level join records at condition and well level |
| `typed_evidence.csv` | evidence layering; design type separated from evidence; no promotion |

QA outputs `outputs/sciplex_pilot_v2/`: `QA_REPORT.md`, `qa_report.json`, six figures
(visually inspected and corrected: legend/color/axis fixes in figs 1, 3, 6).

Tools: `tools/datasets/sciplex_v2_lib.py` (shared logic),
`build_sciplex_pilot_v2.py`, `qa_sciplex_pilot_v2.py` (nonzero exit on gate failure);
tests `tests/test_sciplex_pilot_v2.py`. v1 implementations hash-archived at
`tools/case_memory/archive_v1/`; v1 data/QA artifacts and `PILOT_HANDOFF.md` (superseded
addendum appended) untouched as historical evidence.

## 2. Required handoff statements

- **Actual cell lines and observed conditions**: sciPlex2 — A549 only (32 conditions =
  4 agents × 8 dose tokens, zero-dose included). sciPlex4 — A549 and MCF7 (206
  identifiable conditions at cell×plate level: 80 agent1_only, 28 agent2_only,
  96 combination, 2 DMSO/DMSO baselines).
- **Source cells vs eligible cells**: sciPlex2 24,262 source → 23,733 identifiable
  (529 quarantined: dose+well missing). sciPlex4 98,437 source → 98,397 identifiable
  (40 quarantined: all seven identity fields missing). Quarantined cells never grouped,
  never counted, never in effects. (v1 had manufactured the sciPlex4 40 into a
  "nan::nan" qualified condition and the sciPlex2 529 into "control::nan".)
- **Valid contrasts vs unavailable**: sciPlex2 — 28 treatment-vs-vehicle (same-agent
  zero-dose rule; fallback never needed) + 4 baseline self-contrasts. sciPlex4 — 60
  treatment-vs-vehicle with same-cell **same-plate** DMSO/DMSO (A549 plate10: 31
  conditions incl. baseline; MCF7 plate5: 31) + 144 unavailable with reasons (96
  combinations + 48 agent1_only on plates 3/9/11 and 3/4/8). Cross-plate borrowing and
  batch correction were NOT applied.
- **Biological replication status**: unverified and treated as absent. Hash/index rows,
  wells and cells are not replicates; sciPlex4 combinations are single-plate. No
  replicate uncertainty is reported. Aggregation estimand: "well-unweighted mean of
  per-well mean log1p-CP10K" — descriptive, not a count-summed replicate pseudobulk.
- **Mapping rows vs unique mapped genes**: 42,483 rows mapped to 41,869 unique targets;
  15,743 unresolved; 121 ambiguous (unselected); 71 stable-ID/symbol conflicts resolved
  to the stable ID; 324 collision groups (38 shared-Ensembl, 286 differing-Ensembl).
  Anchors verified by tests: MUM1/ENSG00000160953 → PWWP3A (IRF4 alias trap avoided);
  AC000061.1/ENSG00000083622 → CFTR-AS2 via stable ID. Original feature axis preserved;
  no column merging.
- **Rescue contrasts**: **not constructible from the qualified subset.** All 96
  combination conditions lie on plates without same-plate DMSO/DMSO or single-treatment
  references. Task B is delivered as an explicit blocker ledger (576 unavailable-contrast
  records); the rescue **design** label applies to the experiment, not to any observed
  rescue effect.
- **Unresolved dose/time semantics**: dose values are unverified tokens (no unit field in
  sheets or h5ad; no nM/µM assumption). Exposure time unavailable.
- **Sample-sheet reconciliation**: real join — sciPlex2 192 sheet rows → 32/32
  conditions matched; sciPlex4 624 rows → 206/206 matched (declared DMSO→control token
  normalization). Any sheet condition absent from a future processed source would be
  recorded `expected_not_observed_in_processed_source`, not treated as a failed
  experiment.
- **Model-interface consumability**: Task A observation/response/typed-evidence tables
  conform to the current observation/response/evidence contracts for **development
  plumbing tests** (schema compatibility). The hypothesis-conditional forecaster is NOT
  eligible: no outcome labels, no conditioning hypotheses, no qualified experimental
  evidence, no attempted-experiment denominator. QA figures/counts may serve as
  descriptive diagnostics only.
- **Prohibited uses**: any efficacy, mechanism, target-engagement, calibration,
  performance, decision-utility or untouched-evaluation claim; genetic-rescue claims;
  treating wells/cells/hash rows as biological replicates; cross-plate or
  cross-condition comparisons of the unavailable (NaN) contrasts as measured zeros;
  treating thresholded feature counts as differential-expression discoveries.

## 3. Corrected v1 defects (traceability)

| Review finding | v2 resolution |
|---|---|
| P1 cross-plate control mismatch (144 contrasts) | same-plate rule enforced; 144 contrasts NaN-masked with reasons; ledger delivered |
| P1 40 unknown-identity cells → qualified condition | pre-coercion validation; quarantine ledger; no 'nan' identities (QA-verified) |
| P1 28 agent2_only mislabeled vehicle | complete two-intervention classification + regression test + QA gate |
| P1 `np.abs(effect > t)` counted positives only | `abs_above` fixed (np.abs(effect) > t); positive+negative fixture test; dose table reports abs/pos/neg separately |
| P1 ambiguous gene mapping, 75 stable-ID conflicts, first-wins aliases | row-level stable-ID-first mapping with conflict/ambiguity/collision status; 71 conflicts recomputed; ambiguous aliases unselected; HGNC sha256 pinned |
| P2 v1 masks/misdescribed missingness | NaN-masked effects verified ⟺ availability; baseline self-contrasts distinguished from unavailable |
| P2 sample-sheet "comparison" counted lines | real key-level join with per-step counts and scoped statuses |
| P2 QA not an acceptance gate | 15 gates; nonzero exit proven by invalid-package regression tests; biology demoted to descriptive diagnostics |
| P2 handoff inaccuracies (cell lines, statuses, hash binding) | this handoff states actuals; manifest binds sources, sheets, HGNC, builder/QA, outputs by sha256; byte determinism verified |

## 4. Reproduction commands (Windows / Git Bash; PowerShell: replace `D:/anaconda/envs/maestro/python.exe` accordingly)

```bash
cd /d/MAESTRO
# build (requires data/external/sciplex_family/* and data/external/hgnc/hgnc_complete_set.txt;
# checksums verified against the pinned values in the manifest):
D:/anaconda/envs/maestro/python.exe -m tools.datasets.build_sciplex_pilot_v2
# QA acceptance gate (exit 0 required; regenerates figures):
D:/anaconda/envs/maestro/python.exe -m tools.datasets.qa_sciplex_pilot_v2
# focused regression tests:
D:/anaconda/envs/maestro/python.exe -m pytest tests/test_sciplex_pilot_v2.py -q
```

Reuses the existing verified downloads (Zenodo 13350497 h5ad, hash sample sheets, HGNC
complete set); no new large downloads were required. Output files are byte-for-byte
deterministic across rebuilds in the same runtime (verified); Python, NumPy, SciPy and
compression-library changes can alter archive serialization. `pilot_manifest.json` differs in
`built_at` and implementation-hash bookkeeping.

### Module consolidation follow-up

The consolidation audit found that `wells::sciplex2` and `wells::sciplex4` were stored
as pickled sparse objects rather than numeric arrays. The builder now serializes both as
two-dimensional `float32` matrices. All six matrix value hashes are unchanged after this
serialization repair. The entire archive loads with `allow_pickle=False`; QA materializes
each block once, verifies the per-well dimensions and finite values, and rejects object
arrays. The rebuilt manifest records the dataset implementation and the shared hashing
provider `tools/case_memory/__init__.py`.
The updated QA passes 15/15 gates, with an additional object-array rejection regression test
bringing the focused suite to 29 tests. These updates do not create outcome or mechanism labels.

## 5. Verification summary

- Build: deterministic; source MD5/SHA256 match pinned values; 238 condition rows,
  816 wells, 58,347 mapping rows, 569 quarantined cells.
- QA gate: 15/15 (checksums, shapes/axis, NaN-missingness correspondence, identity
  quarantine, two-intervention classification, same-plate matching, rescue eligibility,
  mapping reconciliation + anchors, both sheet joins, no evidence promotion, provenance
  values, well summaries, package readability).
- Tests: 28 focused regression tests (identity, classification, abs arithmetic, suffix,
  sheet parsing, mapping anchors, invalid/tampered package failure, real-package gate).
- Existing repository suites (`test_repository_shape.py`, `test_structured_tools.py`,
  `test_tool_boundaries.py`, 92 tests) pass — their scope is repo/tool shape, separate
  from these data checks.
- Figures visually inspected; corrections applied (per-agent colors and legend in the
  dose-response figure, plate colors in coverage, unclipped quarantine title).
- Model/forecast/calibration/planner/activation-gate code: untouched. Nothing committed
  or pushed.
