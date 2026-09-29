# Acquisition plan: ranked shortlist and executable construction

> **File summary**
> - **Path**: `research/dataset_discovery/ACQUISITION_PLAN.md`
> - **Purpose**: the corrected, executable acquisition and construction plan (revised per
>   `REVIEW.md`, 2026-09-29): which files first, the separate dataset tasks, the four linked data
>   products, preprocessing and split rules, and the exact claims each subset can and cannot test.
> - **Depends on**: `DATASET_SEARCH_REPORT.md`, `dataset_inventory.json`, `source_checks.json`,
>   `REVIEW.md`, `research/case_memory_integration/SCIENTIFIC_REPAIR_V3.md`.

## 1. Revised priority (per REVIEW)

1. **sciPlex2 + sciPlex4 as small, inexpensive contract pilots**: dose response and
   chemical/metabolic rescue. Count distinct compounds, doses, cells, plates, controls and
   replication from metadata first (sample sheets verified in REVIEW).
2. **Replogle pseudobulk metadata screening for a separately specified genetic task**; no
   small-molecule calibration eligibility until a domain bridge is defined. Actual file
   capitalization on the scPerturb mirror: `ReplogleWeissman2022_K562_gwps.h5ad` etc.
3. **Tahoe metadata -> observed coverage table + per-component exposure ledger**; a subset only
   for a stated development/calibration task with overlap declared.
4. **LINCS as a QC-denominator candidate until the processing-stage and completeness audit
   succeeds.** Discovery metadata does not itself qualify a prospective failure model; a new
   documented protocol is required before reading quality data excluded from the frozen analysis
   (writing that protocol is authorized; the frozen protocol is preserved).
5. **MIX-Seq / JUMP retained as orthogonal readout candidates** with source-level linkage audits
   (MIX-Seq `sens` is externally linked PRISM/GDSC, not same-experiment follow-up).

There is currently **no approved untouched confirmatory dataset** in this register.

## 2. Separate dataset tasks (no universal training table)

| Task | Estimand | Sources | Status |
|---|---|---|---|
| A. Population response prediction | P(response \| context, action, matched control) | sciPlex2, sciPlex3 (local) | pilot authorized (development-only) |
| B. Chemical/metabolic rescue cases | rescue contrast outcomes under the actual sciPlex4 combinations | sciPlex4 | pilot authorized (development-only) |
| C. Genetic perturbation response | separately specified genetic task | Replogle (pseudobulk first) | metadata screening only |
| D. Measurement validity | P(QC pass \| reached deposited assay stage), NOT P(valid \| attempted) | LINCS instance/QC tables (unidentified) | pending: sampling_frame=unspecified |
| E. Restricted measured-action replay | decision value over a measured menu with registered endpoint/utility/abstention | sciPlex2 dose menu (candidate) | blocked until endpoint, utility, eligible-action and abstention rules are registered; no claim about unmeasured alternatives |

Task A data alone does not establish mechanism discovery, action-selection benefit, or a
prospective closed loop.

## 3. First downloads (in order, with verification)

1. **sciPlex2 + sciPlex4 official hash sample sheets** (GEO FTP, KB-class) - done in REVIEW;
   re-downloaded and checksummed by the acquisition agent into `data/external/sciplex_family/`.
2. **scPerturb harmonized h5ad for sciPlex2 (145,178,504 bytes) and sciPlex4 (253,335,945 bytes)**
   from Zenodo record 13350497 (CC BY 4.0). The harmonized file's size does not prove it
   preserves raw counts, replicate identity, controls or every treatment combination: inspect its
   schema and processing provenance before deciding whether GEO raw files are required.
3. **Replogle pseudobulk manifest** (figshare API 20029387) - manifest only; acquire one small
   pilot file only after the genetic task is specified; verify whether aggregation removed
   replicate information.
4. **Tahoe remaining metadata** (`cell_line_metadata`, `sample_metadata` via streaming) for the
   coverage table and exposure ledger; no expression pull before the census.
5. **LINCS QC table identification** from local phase I/II archives and the LINCS2020 build
   documentation; `instinfo_beta.txt` (675 MB) only after the new protocol exists.

No FASTQ, no full atlases, no image collections.

## 4. Metadata census and exposure ledger (before any expression analysis)

Census per source: distinct perturbation identities; canonical compound blocks or target genes;
unidentified/ambiguous identities; observed cell contexts; doses and units; exposure times;
plates/wells/batches/donors/guides/replicate identifiers where available; control types and
matching coverage; observed action combinations (counted, not presumed Cartesian products);
missing metadata and excluded records.

Exposure ledger components: local development history (GSE92742, GSE70138, sciPlex3, PRISM
19Q4, DepMap 24Q2); case-memory fitting (LINCS 2020 pool, 65 reference blocks); calibration
(v3 development fit, 44/10/11 split); inspected evaluation sets (frozen external 26-block
population - not reusable as a fresh confirmatory test); the active virtual-cell checkpoint
(State; Tahoe training overlap verified); any embeddings, predictions or derived features used
downstream (each inherits its source's exposure). Unresolved structures stay unknown;
connectivity-block identity and scaffold novelty are different tests; for genetic perturbations,
target/guide overlap is reported where relevant.

## 5. Construction protocol registration

A new versioned construction protocol
(`research/dataset_discovery/CONSTRUCTION_PROTOCOL_V1.md`) is registered **before inspecting
response outcomes**, recording: task and estimand; inclusion/exclusion rules; independent
grouping unit; biological replicate definition; control-matching rules; allowed preprocessing;
endpoint construction; fitting vs deterministic transformations; split assignment; intended use
of each partition; failure and missingness handling; prohibited claims. For tiny pilots,
development-only use is registered explicitly; no underpowered train/calibration/test split is
forced. The previously inspected 11-compound holdout and the frozen external evaluation are not
reused as a new untouched test.

## 6. Data products (linked, versioned)

1. **Observation and provenance table**: source_record_id, study/release, sample/well/plate/
   batch, cell context, perturbation identity and type, dose/units/exposure time, control
   identity, biological_replicate_id only if verified, original measurement/status, processing
   stage, source file and checksum.
2. **Response/contrast table**: treatment and matched-control references, feature identifiers and
   mapping version, value and value_kind, contrast definition, effect scale, biological replicate
   support, uncertainty when estimable, measurement/QC status, preprocessing version and
   fitted-artifact provenance. Population responses are marked `population_response`; no
   artificial cell-level treatment-control pairing; no replicate-based standard errors when only
   one aggregate exists.
3. **Typed evidence table**: direct molecular measurement / derived population response /
   chemical/metabolic rescue / genetic perturbation response / morphology / external viability
   linkage / curated annotation / model prediction - never upgraded across layers.
4. **Decision episode (optional)**: only if a source genuinely supports information-at-decision-
   time, >= 2 eligible measured actions, interpretation rules, and sourced or explicitly assumed
   costs. Otherwise the qualified response table is delivered and the blocker recorded.

## 7. Source-to-contract mapping (required before construction)

Every field classified as directly observed / deterministically derived / fitted-estimated /
unavailable for: `value_kind`, `biological_replicate_id`, `availability`, `sampling_frame`,
laboratory, assay/readout/cell/time/dose, `conditioning_hypothesis`, `contrast`, `label_kind`,
outcome label and status, `independent_unit`. Boundaries: raw counts and normalized expression
are not signed effects; centered expression z-scores are not automatically differential
z-scores; unknown values are not zeros; thousands of cells from one sample are not thousands of
experiments; a future response is `outcome_only`, never pre-action; contemporaneous untreated
cells support a population control contrast but are not automatically a personalized pre-action
state; treatment assignment does not establish mechanism truth; an explicit all_attempts flag
requires a verified denominator; curated MoA and expression similarity remain proxy labels;
missing conditioning truth stays missing even if that prevents insertion into the current
conditional case-memory estimator. A useful response dataset does not have to be forced into a
hypothesis-conditional episode schema.

## 8. The first subset, concretely (corrected)

**sciPlex2 (dose response) + sciPlex4 (chemical/metabolic rescue), scPerturb harmonized files.**

- Exact files: `SrivatsanTrapnell2020_sciplex2.h5ad` (145,178,504 bytes) and
  `SrivatsanTrapnell2020_sciplex4.h5ad` (253,335,945 bytes), Zenodo record 13350497, CC BY 4.0,
  plus the official GEO hash sample sheets.
- Expected units (metadata-verified): sciPlex2: 4 compounds x 8 dose tokens incl. zero, 32
  agent-dose groups (replication unverified); sciPlex4: ~8 distinct small-molecule/metabolite
  identities in combination across A549/MCF7, 206 raw token combinations before collapsing
  equivalent zero-dose conditions (NOT independent compounds).
- Scientific claims it can test (development-only): whether the current observation/response/
  evidence contracts can represent a real dose-response and a real chemical/metabolic rescue
  dataset without contract violations, and whether signed population effects can be constructed
  with verified control matching. It cannot test: mechanism discovery, action-selection benefit,
  engagement, any confirmatory or untouched-evaluation claim.
- Remaining blockers: replicate identity in the hash sheets; scPerturb processing provenance
  (whether raw counts, controls and all combinations survive); license line for GEO raw files
  if raw data become necessary.

## 9. What this plan does not provide (scoped)

Among the candidates reviewed for the current checkpoints and claims, this search did not
verify: a single-cell attempted-experiment denominator; atlas-scale matched target engagement;
or an untouched evaluation source for the Tahoe-trained checkpoint. These are statements about
this review's scope, not universal impossibility claims. Prospective logging (planned vs
attempted vs succeeded per well) and engagement assays remain prospective measurements.

## 10. Execution status (supersedes "planned" above where noted)

Minimal procurement executed under CONSTRUCTION_PROTOCOL_V1: sciPlex2 + sciPlex4
h5ad (Zenodo 13350497, MD5 verified) + hash sample sheets downloaded to
`data/external/sciplex_family/`; pilot package built at
`data/processed/sciplex_pilot_v1/` (240 conditions: 33 sciPlex2 + 207 sciPlex4).
QA: 10/10 checks passed (`outputs/sciplex_pilot_v1/QA_REPORT.md`).
Full details, gene-mapping accounting, limitations and reproduction commands:
`PILOT_HANDOFF.md`. Remaining blockers above that required only metadata are
resolved in the manifest; replicate identity remains unavailable (structural).
