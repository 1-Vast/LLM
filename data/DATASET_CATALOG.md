# Dataset catalog by scientific use

This catalog is a navigation layer over [`INVENTORY.md`](INVENTORY.md). It does not change source identity or exposure status. Empty directories remain placeholders and are not data.

| Route | Canonical locations | Endpoint/use | Status and boundary |
|---|---|---|---|
| Cheap viability and response | `external/prism_19q4`, `external/depmap_19q4`, `external/beataml2_20261017`, `external/gdsc_combinations`, `external/gcp2020` | cell × compound × dose or fitted response | usable for bounded prediction/replay; exposure, release, and biological independence are task-specific |
| Perturbational state / virtual cell | `external/lincs_l1000_gse92742`, `external/lincs_l1000_phase2`, `external/mixseq_scperturb`, `external/tahoe_phenotype_20261010`, `external/kinetic_horizon_20261010` | transcriptional or population-state signatures | state proxies; not interchangeable with viability or proximal engagement |
| Target and mechanism context | `external/klaeger2017_chembl`, `external/ptv1_proteintalks_20261021`, `external/hgnc`, `external/msigdb`, `external/ontology` | binding/annotation/pathway support | contextual only; no same-row engagement-to-function proof |
| Combination discovery | `raw/oneil2026_qualification`, `processed/certified_discovery`, `external/gdsc_combinations`, `processed/research_packages` | pair × cell × dose, synergy or discovery labels | mostly exposed development or historical replay; preserve vault/restriction boundaries |
| Single-cell / multi-scale state | `external/mixseq_scperturb`, `external/sciplex_family`, `external/sciplex3`, `processed/sciplex_pilot_v1`, `processed/sciplex_pilot_v2` | perturbation × cell state | pilot/derived outputs; missing time/function/randomization gates remain explicit |
| Agent and evaluation artifacts | `processed/maestro_vc_v1`, `processed/model_experiment_v1`, `processed/case_memory_integration`, `processed/research_results`, `evaluation` | synthetic or derived scores, contracts, and cases | engineering/evidence artifacts; not biological validation |
| Historical source packages | `processed/research_packages`, `processed/research_records`, `external/research_sources`, `external/literature_surveys` | exact source and replay recovery | preserve hashes and original identities; do not treat package membership as completion |
| Historical state-controller evidence | `external/state_evidence_20261001` | MATLAB control formulas and protocol sources | seven small source/protocol files retained; four unneeded MAT payloads were structurally audited and removed with external recovery hashes |

Raw and external sources are immutable evidence. Processed directories contain derived data, model artifacts, or reports and must carry a source/recipe pointer before cleanup. The full data inventory remains the authority for file-level hashes and exposure notes.
