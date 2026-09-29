# Construction protocol v2: sci-Plex contract pilot repair (development-only)

> **File summary**
> - **Path**: `research/dataset_discovery/CONSTRUCTION_PROTOCOL_V2.md`
> - **Purpose**: repair-protocol construction choices for `sciplex_pilot_v2`, resolving the
>   findings in `research/dataset_discovery/PILOT_REVIEW.md`.
> - **Status**: repair protocol written 2026-09-29 **after** full exposure to v1 results, the
>   v1 arrays, QA figures and the independent review. This is **not** a prospectively
>   registered protocol and must not be described as one.

- **Version**: sciplex-pilot-construction-2
- **Exposure statement**: every rule below was chosen with knowledge of v1 outcomes
  (condition counts, effect distributions, mapping statistics) and of the review findings
  P1/P2. No inferential threshold, outcome label or biological cutoff is fitted to make QA
  pass; descriptive diagnostics use pre-stated token thresholds and are labeled descriptive.

## 0. Products and scope (unchanged scope, sharpened separation)

| Product | Definition | Status in v2 |
|---|---|---|
| A. Descriptive population response | declared treatment-vs-control contrast with explicit cell/plate context, grouping and control provenance | constructed only where the declared matching rule is satisfied |
| B. Chemical/metabolic rescue contrasts | combination vs matched single-treatment references (and interaction contrasts) requiring same-plate single-treatment and vehicle references at matching doses | constructed only where all references exist; otherwise named unavailable-contrast records |
| C. Gene identity mapping | row-level, traceable, stable-ID-first mapping preserving original feature identity | delivered as an artifact |
| D. Quarantine / unavailable-contrast records | unknown identities, unsupported control matches, missing references, sheet/h5ad discrepancies | delivered as ledgers |

Prohibited claims (unchanged from v1 and restated): no genetic rescue, no target engagement,
no calibrated probabilities, no causal mechanism confirmation, no prospective action-selection
benefit, no attempted-experiment denominator, no untouched external validation, no biological
replication that the design does not supply.

## 1. Identity validation (before any coercion)

- Required fields are validated **on the raw obs values** (never after `astype(str)`):
  sciPlex2: `perturbation, dose_value, cell_line, well`; sciPlex4: `perturbation, dose_value,
  perturbation_2, dose_value_2, cell_line, plate_id, well_id`.
- Missing is: actual null/NaN, the strings `"nan"`, `"None"`, `""`, whitespace-only.
- Cells with any missing required field go to `quarantine_ledger.csv` with: study, source row
  identifier (h5ad obs index), the missing-field list, and reason `missing_identity_fields`.
  Known v2 counts to re-verify at build: sciPlex4 = 40 cells (all seven fields missing);
  sciPlex2 = 529 cells (`dose_value` and `well` missing; perturbation/cell present).
- Quarantined cells: never grouped, never a `"nan::nan"` condition, never counted as known
  wells, never assigned measurement/evidence status, never enter any effect computation.
- Missing treatment identities are never inferred from response profiles.

## 2. Condition definition and two-intervention classification (sciPlex4)

- Condition key: `(perturbation, dose_value, perturbation_2, dose_value_2, cell_line,
  plate_id)`. Plate is part of the key because the declared control is plate-matched.
- Classification of the **complete** intervention, verified by regression test:
  - `vehicle_vehicle`: first = control AND second = control
  - `agent1_only`: first active, second = control (metabolic intervention alone)
  - `agent2_only`: first = control, second active (HDAC inhibitor alone) — **28 such
    conditions exist; v1 mislabeled these as vehicle controls**
  - `combination`: both active
  - `unresolved_identity`: any required identity missing (quarantined, not grouped)
- Design type, observed response, derived rescue contrast and rescue interpretation are
  separate fields. Samples from a rescue-design experiment are not "demonstrated rescues".
- Dose values remain unverified unit tokens. Units are not assumed (no nM/µM inference); the
  sample sheets and h5ad contain no unit field (sheet key format
  `{dose1}_{agent1}_{dose2}_{agent2}_{cell}_{plate}_{well}`); this is recorded as unresolved.

## 3. Control matching and contrast availability

- sciPlex2: control = same-agent zero-dose wells in the same cell context; fallback to the
  `control` token only if the agent-specific zero-dose is absent, with the rule actually used
  recorded per contrast. Cell context is included in the key even though the processed file
  contains A549 only (verified in v2).
- sciPlex4: control = DMSO/DMSO wells in the **same cell line and same plate**. Verified
  source facts: A549 DMSO/DMSO exists only on plate10; MCF7 only on plate5. A contrast with
  no same-plate control is **unavailable**: the treatment population is preserved in the
  census and provenance, the effect is NaN-masked, and the reason is recorded. Cross-plate
  borrowing and batch correction are out of scope (no separate justified design exists).
- Every constructed contrast records: treatment condition + source members (wells, cells),
  treatment cell/plate, control condition + members, control cell/plate, matching rule,
  availability status, and unavailability reason where applicable.
- A smaller valid response table is preferred to a larger confounded one.

## 4. Aggregation estimand (named explicitly)

- Preprocessing (deterministic, unchanged): per-cell CP10K then log1p, from raw counts in X.
- Per-well summaries are computed and retained where well identity is known
  (`well_summaries.csv`): per-well mean log1p-CP10K per gene plus cell count.
- Condition summary = **unweighted mean of per-well means** ("well-unweighted mean of
  per-well mean log1p-CP10K"), plus `n_cells` and `n_wells`. This is a descriptive
  population summary. It is **not** a count-summed biological-replicate pseudobulk and it
  carries no replicate uncertainty; biological replication remains unverified (hash/index
  rows are not replicates; sciPlex4 combinations are single-plate).
- Source matrix scale is validated before normalization: X is checked for count-like
  properties and the available layers are enumerated in the manifest with the observed
  provenance; integer/nonnegative checks alone are not claimed to prove raw preservation.

## 5. Rescue contrasts (Task B) — constructibility rule

- Registered contrast definitions, each requiring same-plate, same-dose, same-cell
  references: (i) combination vs vehicle; (ii) agent1 alone vs vehicle; (iii) agent2 alone
  vs vehicle; (iv) combination vs agent1 alone; (v) combination vs agent2 alone;
  (vi) interaction = (combo − vehicle) − (agent1 − vehicle) − (agent2 − vehicle).
- A rescue contrast is constructed **only** if every required reference exists with the
  declared matching. Otherwise a named `unavailable_contrasts` record is emitted with the
  reason. Expression magnitude, trajectory plausibility and pathway agreement never
  substitute for a missing reference.
- If none survive, Task B is completed as **"not constructible from the qualified
  subset"** with the blocker ledger. (Pre-stated from source inspection: all 96 combination
  conditions lie on plates without any same-plate DMSO/DMSO control or single-agent
  reference; the 62 plate-matched eligible conditions comprise 60 active treatment
  conditions (agent1_only/agent2_only) plus 2 vehicle baselines. The build must recompute
  and report these counts from metadata, not assume them.)

## 6. Gene identity mapping (stable-ID first)

- Both sources carry `var.ensembl_id` (58,347 rows; 58,302 distinct). Mapping is row-level
  over the original feature axis; columns are never summed, averaged or overwritten.
- Mapping table `gene_mapping.csv` columns: feature_index, feature_name, ensembl_id,
  name_suffix_stripped (only the verified pattern `:\d+$` is stripped, for lookup only),
  symbol_lookup_name, stable_id_candidates, symbol_candidates, mapping_method (mutually
  exclusive: `stable_id`, `stable_id_ambiguous`, `symbol_approved`,
  `symbol_prev_or_alias_unique`, `symbol_alias_ambiguous`, `unresolved`),
  selected_hgnc_id, selected_symbol, ambiguity_status, conflict_status, collision_group,
  shared_ensembl_in_collision.
- Rules: stable ID is primary; exact approved symbol is identity evidence; prev/alias used
  with explicit ambiguity handling (multi-candidate aliases stay ambiguous — never
  first-wins); stable-ID/symbol disagreement is recorded and resolved **in favor of the
  stable ID** with `conflict_status=stable_id_vs_symbol`; collision groups are flagged with
  whether members share one Ensembl ID (e.g. CD99/CD99:1 share one ID; MATR3/MATR3:1 carry
  different IDs — these situations are recorded as different).
- Regression anchors (pinned HGNC resource, sha256 recorded in the manifest):
  MUM1/ENSG00000160953 → PWWP3A (symbol evidence IRF4 recorded as conflict, stable ID wins);
  AC000061.1/ENSG00000083622 → CFTR-AS2 via stable ID (not "inherently unmappable").
- Manifest reports separately: input feature rows; unique source stable IDs; mapped rows;
  unique target IDs; unresolved rows; ambiguous rows; stable-ID/symbol conflicts; collision
  groups (with and without shared Ensembl); mutually exclusive mapping-method counts.
  v1 numbers are audit evidence, not targets.

## 7. Missingness representation

- Numeric effect arrays use NaN **exactly** where a contrast is unavailable; every NaN cell
  must be justified by the availability mask (QA verifies the correspondence in both
  directions). Baseline self-contrasts (vehicle vs itself) are defined zeros, marked
  `baseline_self`, and are distinct from unavailable contrasts. Unknown-identity groups do
  not exist in the arrays.
- Sample-sheet reconciliation is a real key-level join: expected keys from the sheets,
  observed keys from identifiable h5ad cells, matched / expected-not-observed (status
  `not_represented_in_processed_source` — absence from a processed derivative is not a
  failed experiment) / observed-not-in-sheet, with counts at each step.

## 8. Evidence and contract statuses

- No output row is `qualified` merely because its group contains cells. Availability
  (`available_in_processed_source`) is separated from experimental quality; no row receives
  `qualified_experimental_evidence`; no outcome labels are constructed; no mechanistic
  conditioning labels are invented; `label_kind` stays `none`; `biological_replicate_id`
  stays unavailable; `sampling_frame` stays limited/unspecified (no attempted-experiment
  denominator). A useful response dataset may remain ineligible for the
  hypothesis-conditional forecaster.

## 9. Deliverables bound to this protocol

- `data/processed/sciplex_pilot_v2/`: pilot_manifest.json, observation_provenance.csv,
  condition_classification.csv, well_summaries.csv, response_arrays.npz, response_genes.txt,
  response_index.csv, gene_mapping.csv, quarantine_ledger.csv, unavailable_contrasts.csv,
  sample_sheet_reconciliation.csv, typed_evidence.csv.
- `outputs/sciplex_pilot_v2/`: QA_REPORT.md, qa_report.json, figures.
- Documentation: `CONTRACT_MAPPING_V2.md`, `PILOT_HANDOFF_V2.md`; PILOT_HANDOFF_V1 carries a
  superseded addendum.
- Tools: `tools/case_memory/sciplex_v2_lib.py`, `build_sciplex_pilot_v2.py`,
  `qa_sciplex_pilot_v2.py`; regression tests `tests/test_sciplex_pilot_v2.py`.
- v1 data/QA artifacts, the frozen historical evaluation and original downloads remain
  immutable; v1 builder/QA implementations are hash-archived under
  `tools/case_memory/archive_v1/`.
