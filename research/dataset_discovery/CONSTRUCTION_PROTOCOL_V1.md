# Construction protocol v1: sci-Plex contract pilots (development-only)

> **File summary**
> - **Path**: `research/dataset_discovery/CONSTRUCTION_PROTOCOL_V1.md`
> - **Purpose**: the registered construction choices for the sciPlex2/sciPlex4 pilot data
>   products, written before any response outcome was inspected, per the corrected
>   `ACQUISITION_PLAN.md` section 5 and the current contracts in
>   `research/case_memory_integration/SCIENTIFIC_REPAIR_V3.md`.
> - **Status**: registered 2026-09-29 before expression-matrix inspection; development-only.

- **Version**: sciplex-pilot-construction-1
- **Registered at**: 2026-09-29, before opening the downloaded h5ad matrices beyond schema
  inspection (obs/var column names and shape only) and before computing any response value.

## 1. Tasks and estimands

| Task | Estimand | Sources |
|---|---|---|
| A. Population response (dose) | signed population effect of compound x dose vs matched vehicle wells, per cell context | sciPlex2 (4 compounds x 8 dose tokens incl. 0) |
| B. Chemical/metabolic rescue cases | signed population effects of first treatment x second treatment combinations vs matched DMSO/DMSO wells, per cell line; rescue contrast = combination minus single-treatment references | sciPlex4 (8 first-treatment identities x 3 second-treatment identities, A549/MCF7) |

No mechanism discovery, action-selection benefit, engagement, calibration-transfer or
confirmatory claim is an estimand of this pilot.

## 2. Inclusion and exclusion

- Include: every sample-sheet treatment row resolvable to an identity, including zero-dose and
  DMSO tokens; every cell context present; no response-based selection.
- Exclude: rows whose treatment token cannot be resolved (reported as excluded with reason);
  genes failing the deterministic mapping to stable identifiers (reported, not silently dropped).
- The scPerturb harmonized h5ad is the source of record for expression; the official GEO hash
  sample sheets are the source of record for treatment identity. If the h5ad drops rows,
  controls or combinations present in the sample sheet, the discrepancy is reported and the
  affected combinations are marked missing, never zero-filled.

## 3. Units, grouping and replication

- **Independent grouping unit**: the (compound-or-combination, cell context) condition for
  census; for any later grouped split, the compound identity block. No split is forced in this
  pilot (development-only).
- **Biological replicate definition**: a distinct, independently randomized plate/well series
  demonstrating independent treatment preparation. sciPlex2's six hash rows per agent-dose and
  sciPlex4's repeated rows are **hash/indexing rows**; the sciPlex4 census shows 0 of 206
  combinations observed on more than one plate, so independent biological replication of a
  combination is **not verified** in this pilot. `biological_replicate_id` is recorded as
  unavailable unless processing metadata proves otherwise; hash rows are never counted as
  biological replicates; cells within a well are never independent experiments.
- **Control matching**: vehicle/zero-dose wells matched by cell context and plate where the
  design provides them; sciPlex2 zero-dose tokens of the same agent family are population
  vehicle controls; sciPlex4 DMSO/DMSO wells per cell line per plate are the combination
  controls. Controls are population-level, not personalized pre-action states.

## 4. Allowed preprocessing

- Deterministic per-sample processing only: library-size normalization and log1p at the
  single-cell level, then aggregation to the well/condition level (pseudobulk mean log
  expression and cell counts). If the h5ad already carries processed matrices, their layers are
  documented and the raw count layer is used for aggregation when present.
- Signed effect = treated condition pseudobulk minus the matched vehicle pseudobulk, on the
  log-expression scale, per gene. This is a population effect estimate; uncertainty is reported
  only where a defensible replicate structure exists (otherwise marked not estimable).
- Feature identifiers: gene symbols as provided by the h5ad var, mapped to HGNC (local
  `data/external/hgnc/hgnc_complete_set.txt`) with the mapping version recorded; unmapped genes
  reported.
- **Fitted transformations**: none in this pilot. No gene filter, threshold, centroid or label is
  fitted; every transformation is deterministic and documented. Any later fitted artifact must
  be fitted inside a registered training partition.

## 5. Endpoints and value kinds

- `population_log_effect` (signed, per gene per condition): deterministically derived.
- `cells_in_condition`, `wells_in_condition`: directly observed.
- `control_kind`: population_vehicle (sciPlex2), population_dmso_dmso (sciPlex4).
- No outcome labels, no mechanism labels, no decision utilities. MoA/target annotations, if
  joined later, are curated-annotation proxy labels in a separate column.

## 6. Splits and intended use

- Development-only. No train/calibration/test split is constructed or implied.
- The pilot may be used to test contract conformance (observation/response/evidence tables),
  preprocessing plumbing and schema compatibility. It must not be used for performance claims,
  estimator comparison, or as a fresh evaluation population.

## 7. Failure and missingness handling

- Conditions present in the sample sheet but absent from the h5ad are listed as missing
  (status `planned_missing`), never zero-filled.
- Conditions with zero detected cells are `undetected`, not zero effect.
- Unresolvable treatment tokens are `ambiguous` and excluded with a named reason.

## 8. Prohibited claims

- Any biological efficacy, mechanism, target-engagement, calibration, model-performance or
  decision-utility claim.
- Treating hash rows, wells or cells as independent biological replicates.
- Treating the sciPlex4 factorial design as a sequential decision history or a genetic rescue.
- Treating this development pilot as an untouched evaluation set.

## 9. Deliverables bound to this protocol

- `data/processed/sciplex_pilot_v1/`: observation_provenance.csv, response_contrast.csv,
  typed_evidence.csv, pilot_manifest.json.
- `outputs/sciplex_pilot_v1/`: qa_report.json and QA figures.
- Contract mapping: `research/dataset_discovery/CONTRACT_MAPPING_V1.md`.
