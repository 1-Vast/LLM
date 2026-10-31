# Dataset catalog by scientific use

This catalog is a navigation layer over [`INVENTORY.md`](INVENTORY.md). It does not change source identity or exposure status. Empty directories remain placeholders and are not data.

| Route | Canonical locations | Endpoint/use | Status and boundary |
|---|---|---|---|
| Cheap viability and response | `external/prism_19q4`, `external/prism_24q2_20261031`, `external/depmap_19q4`, `external/beataml2_20261017`, `external/gdsc_combinations`, `external/gcp2020`, `external/nci60_cellminer_20261031` | cell × compound × dose or fitted response | usable for bounded prediction/replay; exposure, release, and biological independence are task-specific |
| Perturbational state / virtual cell | `external/lincs_l1000_gse92742`, `external/lincs_l1000_phase2`, `external/mixseq_scperturb`, `external/tahoe_phenotype_20261010`, `external/kinetic_horizon_20261010` | transcriptional or population-state signatures | state proxies; not interchangeable with viability or proximal engagement |
| Target and mechanism context | `external/klaeger2017_chembl`, `external/ptv1_proteintalks_20261021`, `external/hgnc`, `external/msigdb`, `external/ontology` | binding/annotation/pathway support | contextual only; no same-row engagement-to-function proof |
| Combination discovery | `raw/oneil2026_qualification`, `processed/certified_discovery`, `external/gdsc_combinations`, `processed/research_packages` | pair × cell × dose, synergy or discovery labels | mostly exposed development or historical replay; preserve vault/restriction boundaries |
| Single-cell / multi-scale state | `external/mixseq_scperturb`, `external/sciplex_family`, `external/sciplex3`, `processed/sciplex_pilot_v1`, `processed/sciplex_pilot_v2` | perturbation × cell state | pilot/derived outputs; missing time/function/randomization gates remain explicit |
| Agent and evaluation artifacts | `processed/maestro_vc_v1`, `processed/model_experiment_v1`, `processed/case_memory_integration`, `processed/research_results`, `evaluation` | synthetic or derived scores, contracts, and cases | engineering/evidence artifacts; not biological validation |
| Historical source packages | `processed/research_packages`, `processed/research_records`, `external/research_sources`, `external/literature_surveys` | exact source and replay recovery | preserve hashes and original identities; do not treat package membership as completion |
| Historical state-controller evidence | `external/state_evidence_20261001` | MATLAB control formulas and protocol sources | seven small source/protocol files retained; four unneeded MAT payloads were structurally audited and removed with external recovery hashes |

Raw and external sources are immutable evidence. Processed directories contain derived data, model artifacts, or reports and must carry a source/recipe pointer before cleanup. The historical data inventory records file-level hashes and exposure notes at its stated observation cutoff; it is not a current full-content verification.


## Later acquisitions and current storage boundary

The 2026-10-31 metadata-only census observes 42 immediate dataset/source directories under `external/`. It does not read protected outcomes, authenticate current payload contents, infer assay eligibility or update historical exposure labels. The full census and exclusion boundaries are external at `D:/MAESTRO-organization-20261031/before.json`; the older `INVENTORY.md` and `ASSETS.json` retain their dated source observations rather than being silently regenerated.

| Scientific use | Additional actual locations | Interpretation boundary |
|---|---|---|
| Conditional functional screens | `external/conditional_interventions_20261030`, `external/functional_anchor_binding_20261030`, `external/virtual_cell_four_directions_20261030` | Resource qualification and exposed development inputs; follow the corresponding functional-prediction episode protocol for held-out restrictions |
| Combination and patient-context qualification | `external/vis2024_pancancer_combinations`, `external/fpmtb_zenodo_7370747`, `external/nci_almanac_2017` | Dataset presence does not establish compatible endpoints, independent units or transfer |
| Proximal/protein-state context | `external/pisa_living_cells`, `external/p100_program_pilot_20261028` | State or engagement context is not matched independent cellular function |
| Primary-source checks | `external/research_sources/methodological_screen_checks` | Twenty retained text captures; source excerpts are not newly verified biological observations |
| Curated literature and author-code snapshots | `../reference/papers.tsv`, `../reference/repositories.tsv`, `../reference/papers`, `../reference/code` | Keep this existing reference-library layout and hash-bound source versions; downloaded or catalogued does not mean fully read, executed or licensed for every reuse |

Keep stable dataset identities in place: physical regrouping of immutable source roots would break frozen recipes without establishing scientific value. Classification is provided here by function; detailed study inputs stay under the original study contracts. Numeric artifacts retained inside episode workspaces are not automatically moved out of hash-bound runs.

## Current external-source footprints (metadata only)

These 2026-10-31 baseline counts describe eligible files, not qualified datasets or content verification. Protected and managed boundaries were not traversed; an excluded subtree count means the footprint is partial. Empty and placeholder-sized locations must not be treated as acquired assay data. The newly relocated methodological text/history collections are described above and were not present at this baseline.

| External directory | Eligible files | Logical bytes | Excluded subtrees | Footprint boundary |
|---|---:|---:|---:|---|
| `arc_state` | 154 | 1,084,377,965 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `batchie_zenodo_13871987` | 0 | 0 | 0 | EMPTY_ELIGIBLE_SCOPE |
| `beataml2_20261017` | 8 | 354,055,234 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `chemCPA` | 0 | 0 | 1 | EMPTY_ELIGIBLE_SCOPE |
| `conditional_interventions_20261030` | 39 | 204,727,848 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `core_completion_round_20261023` | 6 | 2,966,719 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `depmap_19q4` | 3 | 591,009,610 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `evidence_portfolio_optimization_20261023` | 13 | 4,125,417 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `fpmtb_zenodo_7370747` | 7 | 47,358,082 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `functional_anchor_binding_20261030` | 20 | 342,007,356 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `gcp2020` | 189 | 12,327,007 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `gdsc2_fitted` | 0 | 0 | 0 | EMPTY_ELIGIBLE_SCOPE |
| `gdsc_combinations` | 4 | 271,349,722 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `hgnc` | 0 | 0 | 0 | EMPTY_ELIGIBLE_SCOPE |
| `hill2017` | 0 | 0 | 0 | EMPTY_ELIGIBLE_SCOPE |
| `jaaks2022_provenance` | 0 | 0 | 0 | EMPTY_ELIGIBLE_SCOPE |
| `jump_target` | 0 | 0 | 0 | EMPTY_ELIGIBLE_SCOPE |
| `kinetic_horizon_20261010` | 19 | 78,120,238 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `klaeger2017_chembl` | 3 | 9,068,401 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `lincs_l1000_gse92742` | 17 | 45,083,201,219 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `lincs_l1000_phase1` | 0 | 0 | 0 | EMPTY_ELIGIBLE_SCOPE |
| `lincs_l1000_phase2` | 8 | 11,347,080,666 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `literature_surveys` | 101 | 14,809,621 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `MAP` | 0 | 0 | 1 | EMPTY_ELIGIBLE_SCOPE |
| `map_module_replacement_20261009` | 1,485 | 614,305,071 | 1 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `mapkg_20261009` | 4 | 67,785,015 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `mixseq_scperturb` | 1 | 1,459,410,830 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `msigdb` | 0 | 0 | 0 | EMPTY_ELIGIBLE_SCOPE |
| `nci60_cellminer_20261031` | 8 | 63,926,887 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `nci_almanac_2017` | 0 | 0 | 0 | EMPTY_ELIGIBLE_SCOPE |
| `nyman2020` | 0 | 0 | 0 | EMPTY_ELIGIBLE_SCOPE |
| `p100_program_pilot_20261028` | 20 | 2,002,162 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `pisa_living_cells` | 0 | 0 | 0 | EMPTY_ELIGIBLE_SCOPE |
| `prism_19q4` | 13 | 395,749,830 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `prism_24q2_20261031` | 6 | 74,867,050 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `ptv1_proteintalks_20261021` | 31 | 776,565,501 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `public_checks_20260929` | 0 | 0 | 0 | EMPTY_ELIGIBLE_SCOPE |
| `research_sources` | 2,263 | 6,881,293,031 | 4 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `retired_research_sources` | 17 | 51,091 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `sciplex_family` | 0 | 0 | 0 | EMPTY_ELIGIBLE_SCOPE |
| `state_evidence_20261001` | 8 | 80,068 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `tahoe_phenotype_20261010` | 1,001 | 4,941,501,014 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `virtual_cell_four_directions_20261030` | 91 | 325,071,271 | 0 | PRESENT; CONTENT_AND_ELIGIBILITY_NOT_REVERIFIED |
| `vis2024_pancancer_combinations` | 0 | 0 | 0 | EMPTY_ELIGIBLE_SCOPE |
