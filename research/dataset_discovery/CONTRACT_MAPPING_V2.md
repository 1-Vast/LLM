# Contract mapping v2: sci-Plex source → MAESTRO contract fields

> **File summary**
> - **Path**: `research/dataset_discovery/CONTRACT_MAPPING_V2.md`
> - **Purpose**: the version-2 source-to-contract mapping required by
>   `CONSTRUCTION_PROTOCOL_V2.md` (v1 never delivered its promised CONTRACT_MAPPING_V1).
> - **Scope**: `data/processed/sciplex_pilot_v2/` products. Development-only.

Notation: **direct** = copied from source metadata; **derived** = deterministic
transformation declared in the protocol; **unavailable** = not constructible from this
source without invention.

## Per-field mapping

| Contract field | Source | Status | Transformation | Validation | Permitted use |
|---|---|---|---|---|---|
| `value_kind` | h5ad X (raw counts) + determinstic normalization | derived | per-cell CP10K + log1p; per-well mean; unweighted mean of per-well means per condition | integer/nonnegative checks on X; layers/raw enumerated in manifest (provenance only) | descriptive population log-expression summaries; NOT replicate-level inference |
| `population_log_effect` (response) | means block minus matched control means | derived | signed difference on log1p-CP10K scale; NaN where contrast unavailable (availability-masked) | QA verifies NaN ⟺ unavailable, both directions; baseline self-contrasts exactly zero | Task A descriptive effects only; no threshold biology claims |
| `biological_replicate_id` | none | unavailable | constant "unavailable (hash/index rows are not replicates)" | QA asserts the constant | none; no replicate uncertainty anywhere |
| `availability` | grouping over identifiable cells | derived | `available` flag per contrast; `contrast_kind` ∈ {treatment_vs_vehicle, baseline_self, unavailable} | counts reconcile: sciPlex4 60 available treatment contrasts + 2 baselines + 144 unavailable; sciPlex2 28 + 4 | downstream must respect masks; unavailable ≠ zero |
| `sampling_frame` | none | unavailable (limited) | constant "processed_source_only (no attempted-experiment denominator)" | QA asserts the constant | none; no failure-rate or denominator claims |
| `laboratory` | GSE139944 (SrivatsanTrapnell2020) | direct (study-level) | constant per study string in provenance | recorded in manifest sources | provenance only |
| assay / readout | sci-Plex scRNA-seq (hashing demultiplexed) | direct (study-level) | recorded as study design note | — | provenance only |
| `cell_line` | obs `cell_line` | direct (validated) | raw value validated by `is_missing` BEFORE string coercion; sciPlex2 observed {A549}, sciPlex4 {A549, MCF7} | 40 sciPlex4 + 529 sciPlex2 cells failing validation quarantined | conditioning context |
| `plate_id` | obs `plate_id` (sciPlex4 only) | direct (validated) | part of condition key and control-matching rule | same-plate rule enforced in QA | control matching; no batch correction applied |
| `well` / `well_id` | obs `well`/`well_id` | direct (validated) | per-well membership (`well_summaries.csv`, 816 wells) | wells positive cell counts (QA) | per-well summaries; NOT independent replicates |
| exposure `time` | none in sources | unavailable | — | — | unresolved; no time-matched claims |
| `dose_value` | obs `dose_value` | direct (token) | string token as stored | token format only | ordering/census; **units unresolved** (`dose_unit` = "unverified_token"; neither sheets nor h5ad carry a unit field) |
| treatment identity (1st/2nd) | obs `perturbation`, `perturbation_2` | direct (validated) | condition key `p1::d1\|p2::d2@cell@plate`; sheet token `DMSO` ≡ h5ad `control` (declared normalization, recorded) | complete two-intervention classification (QA gate; regression-tested) | identity-based analysis only |
| control identity & matching | derived grouping | derived | sciPlex2: same-agent zero-dose same cell (rule used recorded); sciPlex4: DMSO/DMSO same cell **and same plate** | QA verifies plate equality for every treatment contrast; unavailable rows carry reasons | — |
| rescue contrast | `rescue_contrast_ledger.csv` | derived (negative result) | six registered contrast kinds checked per combination; all 96 combinations lack same-plate references | QA gate: verdict matches ledger | Task B = **not constructible from the qualified subset**; design-type label `chemical_metabolic_rescue_design` ≠ demonstrated rescue |
| independent grouping unit | declared | declared | condition (treatment × context); per-well summaries retained; well-unweighted mean estimand named in manifest | QA asserts estimand name | descriptive aggregation only |
| `measurement_status` | processed-source availability | derived | `available_in_processed_source` semantics via `available`; **no** `qualified` status anywhere (nonempty groups are not quality) | QA: no qualified claims | — |
| `evidence_class` | classification + contrast kind | derived | `direct_molecular_measurement` (vehicle baselines) / `derived_population_response` (treatments); never `qualified_experimental_evidence` | QA gate | — |
| `label_kind` | none | constant | "none (no outcome labels constructed)" | QA gate | future measured responses must stay `outcome_only`; no contemporaneous-control-as-personalized-baseline reinterpretation |
| `conditioning_hypothesis` | none | unavailable | empty; no mechanistic labels invented | — | dataset may remain ineligible for the hypothesis-conditional forecaster |
| `ambiguity/conflict/collision` | `gene_mapping.csv` | derived | stable-ID-first mapping; conflicts resolved to stable ID and recorded; multi-target aliases stay ambiguous; suffix handling only `:\d+$` | QA gates incl. MUM1/AC000061.1/CD99/MATR3 anchors | feature identity lookups; no column merging |

## Gene mapping census (recomputed, not inherited from v1)

- input feature rows 58,347; unique source stable IDs 58,302
- mapped rows 42,483 → 41,869 unique targets; unresolved 15,743; ambiguous 121
- stable-ID vs symbol conflicts 71 (resolved to stable ID, recorded)
- collision groups 324 (38 share one Ensembl ID, 286 carry different IDs)
- mutually exclusive methods: stable_id 41,761 / stable_id_ambiguous 3 /
  symbol_approved 492 / symbol_prev_or_alias_unique 230 / symbol_alias_ambiguous 118 /
  unresolved 15,743

## Quarantine and reconciliation

- quarantine ledger: 569 cells (sciPlex2 529: dose+well missing; sciPlex4 40: all seven
  identity fields missing), each with source row id, missing-field list, reason.
- sample-sheet reconciliation: real key-level join; sciPlex2 192 sheet rows → 32/32
  conditions matched; sciPlex4 624 sheet rows → 206/206 matched (after the declared
  DMSO→control token normalization); absence from the processed source would be recorded
  as `expected_not_observed_in_processed_source`, never as a failed experiment.
