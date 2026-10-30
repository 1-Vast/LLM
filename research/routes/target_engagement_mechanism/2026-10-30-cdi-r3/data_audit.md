# CDI data-contract audit

Date: 2026-10-30. Scope is the readable public/local assets and lightweight metadata in the current workspace. Sealed or confirmation responses were not opened, and `src/` and `tools/` were not modified.

## Definition and decision

The CDI candidate has four layers: (1) molecular relative binding/affinity difference, (2) drug-by-cell functional response, here viability or drug sensitivity, (3) target/subtype and genetic/background context, and (4) an agent selecting the next drug-by-cell measurement, optionally with dose.

Cross-assay predictive association does not require affinity and viability to be collected in the same culture, dose, or time. It supports prediction or ranking only. Cellular target engagement or mediation requires matched engagement or controlled genetic intervention.

| Layer | Feasibility | Decision |
|---|---|---|
| Relative molecular affinity | Limited feasible | Klaeger 2017/ChEMBL provides traceable lysate kinobead apparent Kd. Many values are right-censored `>` and are not precise Kd or live-cell binding. |
| Drug-by-cell functional response | Feasible by endpoint | PRISM 19Q4, GDSC Jaaks, and BeatAML2 provide viability or sensitivity data, but their endpoints and background units must remain separate. |
| Target/genetic context | Feasible as annotation/background | PRISM MoA/target and DepMap lineage/expression/mutation are conditional features, not engagement measurements. |
| Agent selection | Retrospective masked design feasible | Public matrices can simulate sequential reveal and selection; no prospective cost, purchasing/culture record, or independent prospective agent result is available. |
| Affinity-to-cell-response causal mediation | Not identifiable now | Requires cellular engagement, target isoform/subtype resolution, and controlled genetic comparison. |

## Resource findings

### Klaeger 2017 / ChEMBL CHEMBL3991601

Local files are `data/external/klaeger2017_chembl/klaeger2017_CHEMBL3991601_kd.csv`, `MANIFEST.json`, and `molecules.json`. The manifest records ChEMBL REST and Klaeger et al. 2017 (Science), with CC BY-SA 3.0, retrieval date 2026-10-19, and hashes. There are 70,505 activities, 243 ChEMBL molecules, and 325 assays. All records are Kd in nM; 65,576 have relation `>` and 4,929 `=`. Use censored relative-affinity/ranking features grouped by molecule, target, and assay. The data have no cell background, intracellular dose, exposure time, vehicle, culture preparation, or biological replicate, so they are not cellular engagement.

### Broad PRISM Repurposing 19Q4

Local primary and secondary files are under `data/external/prism_19q4/raw/`. Primary covers 4,518 compounds and about 578/562 cell lines; secondary covers 1,448 compounds and 489 cell lines with eight-step four-fold dilution starting at 10 uM. Metadata include `broad_id`, name, SMILES, MoA, target, phase, dose, screen, `depmap_id`, and plate/well fields. MTS010 is explicitly a technical redo. Endpoints are DMSO-relative log-fold viability and fitted dose-response summaries; exposure time is not provided. Use standardized drug identity by structure and exact `depmap_id`, with grouped holdouts. Do not treat target annotations as engagement.

### DepMap 19Q4

`data/external/depmap_19q4/` provides cell identity, lineage/subtype, culture metadata, baseline expression, and mutations. It has no drug, dose, time, vehicle, or functional endpoint. Use it only as background/genetic context. Exact `depmap_id` alignment proves identity alignment, not identical culture, timing, or batch.

### GDSC Jaaks 2022

`data/external/gdsc_combinations/jaaks2022_figshare/` includes fitted combination tables and raw wells. Fitted fields include cell identity, anchor/library drug, concentration, single-agent viability, synergy, and target/pathway annotations. Raw records retain barcode, scan, date, duration, position, drug, concentration, and intensity. Use for dose-aware viability/combination prediction; original and validation screens are not automatically independent biology and annotations are not engagement.

### BeatAML 2.0

`data/external/beataml2_20261017/` contains 63,395 single-agent curve-fit rows for 569 patient samples and 166 inhibitors, plus raw fields for plate, replicate, concentration, normalized viability, read time, and QC. It can provide an external patient-background evaluation. Patient samples must not be joined to PRISM cell-line labels as one experimental unit.

### LINCS L1000 and MIX-seq/scPerturb

L1000 signatures under `data/external/lincs_l1000_gse92742/` and `data/external/lincs_l1000_phase2/` include perturbagen, cell, dose, time, vehicle, and replicate-like identifiers but no PRISM/GDSC viability or independent functional endpoint. MIX-seq/scPerturb under `data/external/mixseq_scperturb/mcfarland_2020.h5ad` includes cell, perturbation, dose, time, hash, channel, ChEMBL ID, and QC fields but no viability, regrowth, or independent function. Both are state proxies only.

## Intersection limits

The nominal intersection is standardized drug identity (ChEMBL to Broad to GDSC) by exact PRISM/DepMap cell identity and Kd target annotation. It is not a shared experiment. Preserve each source's assay, dose, time, vehicle, plate/preparation, replicate, and endpoint. Same target names do not prove isoform identity, intracellular occupancy, or downstream causality. Mediation requires cellular engagement or identifiable genetic perturbation/rescue.

## Minimum retrospective CDI holdout

1. Freeze a structure/InChIKey whitelist linking ChEMBL molecule, PRISM `broad_id`, and GDSC drug; retain salt and batch ambiguity as unmapped.
2. Hold out complete drug groups/scaffolds and cell lineages, with at least three non-overlapping drug groups and three lineages in a pilot. Never split dose rows from the same drug-by-cell block.
3. Expose the agent only to training-block affinity summaries, structure, annotations, DepMap context, and revealed functional responses. Mask missing dose/time rather than imputing defaults.
4. Select one unrevealed drug-by-cell candidate or fixed batch per round. Compare random, structure-similarity, uncertainty, and oracle upper-bound strategies.
5. Report drug-held-out, lineage-held-out, and double-cold-start results on complete frozen PRISM blocks. Use drug or cell clusters for bootstrap; dose rows are not independent samples.
6. Limit conclusions to predictive selection unless matched engagement or controlled genetic intervention is added.

## Final ruling

Feasible now: censored relative-affinity features plus PRISM/GDSC viability and DepMap context for strict cross-assay prediction and retrospective agent selection. Conditional: BeatAML as a separate patient-background external evaluation. Not feasible now: cellular engagement, affinity-to-viability causal mediation, actual cost savings, or prospective agent advantage. Reopen the data gate after structure-level drug mapping, PRISM exposure/vehicle and biological-replicate documentation, and cellular engagement or controlled genetic perturbation are available.
