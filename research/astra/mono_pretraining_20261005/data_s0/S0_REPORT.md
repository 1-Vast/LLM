# S0 report: GDSC2 mono -> Jaaks anchored combination transfer (stage before labels)

Agent B, 2026-10-05. Built by `build_s0.py` (run once; refuses to overwrite). Every access is in `access_log.jsonl`. Machine-readable facts: `s0_facts.json`. Sources with URL/bytes/SHA256/licence: `source_manifest.json`.

Hard rule status: no GDSC2 `LN_IC50`, `AUC`, `RMSE`, `Z_SCORE` value and no figshare Jaaks outcome column value was read by the build. One disclosed deviation during exploration is in section 9.

## 1. Headline numbers

| Item | Value |
|---|---|
| GDSC2 file | 242,036 records, 969 cell models (SANGER_MODEL_ID), 295 DRUG_IDs (286 names), one DATASET (`GDSC2`), one `NLME_RESULT_ID` (343), `WEBRELEASE` = Y; SHA256 equals the receipt (`f950a702...7560`) |
| Jaaks drug IDs | 65 distinct (anchor and library): 63 mapped, 1 unmapped (2265 Galunisertib), 1 composite (`1032|1372`, not split) |
| Jaaks lines | 125 original + 1 validation-only (HPAF-II, SIDM00669) = 126 SIDMs, all present in GDSC2; Supplementary Table 2 lists 128 names (adds PL18, CL-34, CL-40, none in GDSC2; omits HPAF-II) |
| Cells excluded from mono | 126 of 969 (rule in section 3); no alias/derivative of a Jaaks line exists in GDSC2 |
| Eligible mono cells | 843 after exclusion; 837 also have a PROGENy context column (primary set); 6 have none |
| Eligible mono records (primary) | **48,618 records, 63 drugs, 837 cells**; per drug 211 to 837 (median 829) |
| Same, no context requirement | 48,972 records, 843 cells |
| If sibling DRUG_IDs are pooled | 50,402 records (+1,784 from IDs 1819, 1806, 2106) |
| Records in the excluded Jaaks lines (ceiling diagnostic only, NOT eligible) | 7,448 records, all 126 lines, 12 to 63 of the 63 drugs per line (median 59) |
| Tissue overlap with Jaaks tissues after exclusion | essentially none: TCGA_DESC BRCA/COREAD/PAAD primary cells = 1 (SNU-61, 56 records); by Cell Model Passports tissue 4 cells (SNU-61, SNU-283, SW626 large intestine; QGP-1 pancreas) |
| Proposed grouped mono validation | 665 train / 172 val cells (38,715 / 9,903 records) |
| Jaaks menu coverage by mapped drugs | 2,475 of 2,575 (tissue, anchor, library) pairs have both drugs mapped: breast 1,275/1,275, colon 600/650, pancreas 600/650 (the 50+50 unmapped are the 2265 and composite pairs) |

Consistency with the earlier metadata census (`PRETRAINING_PROTOCOL.json`): 48,670 candidate rows over 838 cells there equals 48,618 over 837 here plus HPAF-II (52 records, 1 cell). The earlier census excluded only the 125 partition SIDMs; HPAF-II is in the Jaaks validation screen and is excluded here.

## 2. Drug identity (`drug_identity_map.csv`)

- Mapping basis: Sanger `DRUG_ID` equality plus casefold/stripped name equality; both studies use the same Sanger drug registry. Names agree exactly in all 63 (after stripping edge whitespace: 739 GDSC2 `DRUG_NAME` values and 717 `PUTATIVE_TARGET` values carry trailing/leading spaces). Pathway annotation agrees in all 63; target token sets agree in all 63.
- Supporting evidence: the release-8.5 compound table (screening site, synonyms, target, pathway), and PubChem name -> CID with synonym cross-queries. PubChem support is *consistent* for 58, *unverified* for 5, none *unresolved*:
  - Cisplatin and Oxaliplatin resolve to salt/mixture-style PubChem entries (platinum complexes), synonym queries disagree; OSI-027 title is a code name; Wee1 Inhibitor is a generic descriptor (1046; distinct compound from MK-1775/1179 by ID); Nutlin-3a (-) resolves only after stripping the stereo tag (PubChem entry "Nutlin 3": stereo/active-enantiomer identity not authenticated).
- Caveat flags (counts): sibling DRUG_ID with the same name 3 (Docetaxel 1007/1819, Oxaliplatin 1089/1806, Uprosertib 1553/2106); salt named in synonyms 2 (Irinotecan, Ruxolitinib); stereo designator 1 (Nutlin-3a (-)); PubChem title differs from the name 10 (mostly hyphen/case or alternate codes).
- Status: `mapped` is an identity statement inside the Sanger registry. It does not authenticate the physical stock, lot, salt form or stereochemistry (Jaaks used commercial vendors; GDSC2 uses `COMPANY_ID` codes, undocumented). `ambiguous`: 0 (the rule would flag an ID match with name or target conflict, or a same-name match under another ID).
- Unmapped: 2265 Galunisertib is not a DRUG_ID in GDSC2 and is absent from the release-8.5 compound table (name and code LY2157299 searched). Composite `1032|1372` is Afatinib+Trametinib as one intervention; it carries no GDSC2 mapping and no mono pseudo-observation; the plain `1032` (Afatinib) and `1372` (Trametinib) are separate single drugs and are mapped.
- Sibling IDs: same name, different `DRUG_ID`, different company code and dose-range (e.g. Docetaxel 1007: 0.0125 uM max; 1819: 3 uM max). Default rule: primary records are ID-equal only; siblings are tagged and counted separately (`eligible_if_siblings_pooled`). They are the only repeated measurements of the same drug in the same cell (see section 5).

## 3. Cell identity and exclusion (`cell_identity_map.csv`)

Exact exclusion rule (applied to mono training and mono validation alike). A GDSC2 cell entity is excluded if any of:

1. T1: its SIDM is in J = original Jaaks screen (125) union validation screen (97, adds SIDM00669) union Jaaks Supplementary Table 2 (adds 3 lines not in GDSC2).
2. T2: a normalised name/synonym (upper-case alphanumerics) or a COSMIC/BROAD/CCLE/RRID value equals that of a member of J under a different SIDM.
3. T3 to T6: it lies in the same connected component as a member of J in the Cell Model Passports relation graph. Edges: `parent_id`, same `sample_id` (T3: derivative), same `patient_id` (T4), relation-comment mention of a name or synonym with at least 4 alphanumeric characters (T5), and transitive closure (T6). Graph built on `model_list_latest.csv` (2026-09-21) and `model_list_20240110.csv`, edges unioned.

Observed: only T1 fires. 126 of 969 GDSC2 cells excluded, 843 retained.
- Jaaks lines: COSMIC IDs and cell-line names agree exactly between the Jaaks CSV, GDSC2 and Cell Model Passports for all 126 (0 disagreements). GDSC2 COSMIC_ID and SANGER_MODEL_ID are one-to-one.
- 40 Cell Model Passports relatives of Jaaks lines exist (e.g. COLO-201/COLO-206F, KP-1N derivative KP-1NL, LS-174T, RKO-E6, KCI-MOH1, EFM-192 series, SW480, HCC-BL lymphoblastoid lines): **none is in GDSC2**, so no derivative has to be dropped. 0 name/ID alias collisions. Relation edges overall: parent_child 120, same_sample 202, same_patient 471, comment_mention 438.
- Ambiguous but conservatively excluded: none needed. If the 2024 or a later model list adds relations, rerun the script.
- No two GDSC2 cells share a `patient_id` or `sample_id` in Cell Model Passports (the GDSC2 panel is one model per patient), and none of the 23 GDSC2 cells that have a `parent_id` has its parent in GDSC2: every eligible entity is a singleton group. `entity_group_id` is kept as a safeguard for later model-list versions. (`s0_facts.json` key `gdsc2_cells_sharing_relation_component` = 38 counts Jaaks cells that share a component with context-only models; it is not a statement about eligible cells.) Four homonym pairs inside GDSC2 (`T-T`/`TT`, `KMH-2`/`KM-H2`) are different models (different SIDM and COSMIC) and are not merged; flagged `gdsc2_name_homonym_other_sidm`.
- Context: 1,431 public-context SIDMs (PROGENy 14 pathways); 963 are in GDSC2 (837 non-excluded); 468 have no GDSC2 mono; 6 GDSC2 cells have no context (not in the primary set: SIDM00205, 00361, 01021, 01201, 01219, 01261).
- Not verified: Cell Model Passports is the only alias source; cross-contamination not recorded there is invisible to this rule. The GDSC2 file has no STR/SNP evidence.

## 4. Coverage and the target-line ceiling arm

Files: `coverage_by_drug_cell.csv` (63 mapped drugs plus the 3 sibling IDs, every cell, with flags), `coverage_all_gdsc2_records.csv.gz` (all 242,036 records with flags), `coverage_count_by_drug.csv`, `coverage_tissue_by_drug.csv`, `ceiling_diagnostic_target_line_counts.csv`, `jaaks_pair_coverage.csv`.

- All coverage figures are pre-QC and pre-label: a record counts as eligible if it is in the file. Missing/non-finite `LN_IC50` cannot be known at S0 (it needs values); the documented release rule (RMSE <= 0.3) means every row already passed author QC.
- Five drugs (1096 Tozasertib, 1129 PF-4708671, 1192 GSK269962A, 1194 SB505124, 2169 AZD6482) were screened in only ~265-268 cells (211 eligible each); AZD8055 (1059) has 620, Cisplatin (1005) 635, all others 773 to 837.
- Tissue distribution of eligible cells (TCGA_DESC, primary set): LUAD 61, SCLC 59, SKCM 54, HNSC 39, ESCA 35, OV 34, DLBC 34, GBM 33, ..., 176 UNCLASSIFIED; full table in `s0_facts.json` (`eligible_cells_by_tcga`, `cells.cmp_tissue_total_jaaks_eligible`). Breast, colon and pancreas Jaaks tissues are almost entirely consumed by the Jaaks lines (GDSC2 breast 52 cells of which 51 Jaaks; large intestine 48/45; pancreas 31/30).
- Consequence: the primary pretraining set can only support pan-cancer, cross-tissue transfer. The "target-line own mono" arm (the Jaaks line's own GDSC2 record, 7,448 records over 126 lines) is the only mono information on the three Jaaks tissues. It is **NOT eligible for the primary pretraining set**; counts only are reported in `ceiling_diagnostic_target_line_counts.csv` (per drug: lines with a record, by tissue).

## 5. Fit and duplicate groups (`fit_duplicate_groups.csv`)

- One joint fit: `NLME_RESULT_ID` is 343 for every record (DepMap docs: the complete set of cell x compound series is fitted simultaneously; scale parameter varies by cell model, position by cell model and compound). Fitted records are therefore not independent observations.
- `NLME_CURVE_ID` is unique per record. (cell, DRUG_ID) pairs are never repeated (0). Technical replicate wells are pooled inside the fit and are not separate rows: **the file contains no technical replicates**.
- Repeated measurements exist only as the same drug name under 2 DRUG_IDs (9 names: Acetalax, Dactinomycin, Docetaxel, Fulvestrant, GSK343, Oxaliplatin, Selumetinib, Ulixertinib, Uprosertib): 6,288 (cell, drug) pairs, 12,576 records. DepMap docs attribute them to "internal tracking". These are different registered stocks; in 6 of 9 names the dose range also differs (Acetalax, Selumetinib and Uprosertib share the same range).
- Multiple concentration ranges: `MIN_CONC`/`MAX_CONC` are stored per record. 76 of 295 DRUG_IDs have more than one dose-range group (458 groups in total; 39 DRUG_IDs have more than one `MAX_CONC`; 74 more than one `MIN_CONC`; e.g. Cisplatin max 4/6/8 uM). Realised range ratio is mostly 1,000 (half-log 7-point) and 1,024 or 256; extremes 256 to 1e6. The gdscIC50 vignette defines `drug` as DRUG_ID plus `maxc`, so the dose-range group is a drug-level model unit. Ranges are a design-level proxy for screening campaign; barcodes and dates are not in the file.

## 6. Observation contract (`observation_contract.json`, summary)

- `LN_IC50` = natural log of the fitted IC50 in micromolar: `log(maxc * 2^(xmid - 9))` (gdscIC50 `calcIC50`, `getConcFromX`; plot axis label log_e uM). `MIN_CONC`/`MAX_CONC` micromolar (DepMap docs). Verified from documentation and code, not from values.
- Assay: CellTiter-Glo, 72 h, 1,536-well, Echo555, drugging 24 h after seeding; DMSO negative control, blank positive control. GDSC1 (Resazurin/Syto60) is a different file.
- Fit: NLME two-parameter logistic of Vis et al. 2016 (R `gdscIC50`, GPL-3, master commit recorded).
- Out-of-range IC50: `xmid` is not clipped; an IC50 above `MAX_CONC` is an extrapolation of the fitted sigmoid, not an observed threshold; the file has no censoring flag. Rule: keep the value, carry `out_of_range_high/low` computed from design columns at S1, report in-range and extrapolated errors separately, no silent clipping or dropping; clipping to [ln MIN, ln MAX] is a recorded sensitivity arm.
- QC: documented rule is "curves with RMSE > 0.3 are excluded prior to release"; `Z_SCORE` is a descriptive z over the panel, not a filter. Plate-level thresholds for the GDSC2 file are not documented here (the Jaaks documentation lists CV <= 0.18 and Z-factor >= 0.3 for the combination screen).
- Comparability across drugs: raw `LN_IC50` is not comparable. Primary target recommendation (decision only): `y_rel = (LN_IC50 - ln MAX_CONC) / ln 2` (= xmid - 9, log2 steps below the top dose; uses only the design column `MAX_CONC`), standardised per drug on training cells only; AUC (bounded, never extrapolated) as secondary. Rationale: it is the quantity the NLME fit estimates, removes the arbitrary top-dose offset between drugs and between ranges of one drug, and matches the Jaaks log2 scale (9 = top dose). This choice used no values.
- Licence: Sanger DepMap Data Usage Policy (non-exclusive, non-transferable, internal proprietary research and educational use; no resale alone or combined; as-is; commercial use needs consent). The GDSC2 workbook has no embedded licence text; the Jaaks figshare record says CC BY 4.0 but repeats the stricter Sanger wording in its description. Treat the stricter as binding.

## 7. Split rules recommended for S1 (to be frozen)

- Entity of splitting: `entity_group_id` (connected component of the relation graph; every eligible cell is currently its own group, see section 3). All records of all drugs for one entity stay on one side. Because every fit group (same drug name under multiple IDs, dose-range groups of one cell) lives inside one cell, grouping by entity also keeps duplicate/fit groups together.
- Proposed assignment (metadata only): validation iff `int(sha256("mono_val_v1|20261005|" + entity_group_id)[:8], 16) % 5 == 0`. Primary set: 665 train / 172 val cells. No combination labels and no Jaaks line in mono selection. The proposal is in `cell_identity_map.csv:proposed_mono_split`; the lead may re-freeze with a different seed before any outcome read.
- Mono selection must use training-fold statistics only (per-drug standardisation, PROGENy standardisation parameters).
- Dose-range groups: carry the group id as a covariate, or standardise per group when a group has at least 30 training cells.
- Optional sensitivity: leave-drug-out within mono (drug-ID permutation arms need the same mapping table).

## 8. Verified, unknown, deviations

Verified (documentation or metadata): single joint NLME fit; unique curve IDs; no repeated (cell, drug) pairs; ln(uM) convention; assay and duration; documented RMSE <= 0.3 release rule; SIDM/COSMIC/name agreement of all 126 Jaaks lines; exact Sanger-ID name agreement of 63 drugs; no Jaaks relative in GDSC2; Jaaks figshare md5 equals the local file; GDSC2 SHA256 equals the receipt.

Unknown or not authenticated: physical stock/lot/salt/stereo identity of any drug across the two studies; plate barcodes/dates of GDSC2; whether Jaaks plates or pilot data entered the GDSC2 NLME fit; whether any `LN_IC50` is missing or non-finite; value-level confirmation of the unit and of the fraction of extrapolated IC50 (needs values, deferred to S1 after freeze); GDSC2 plate-level QC thresholds; completeness of Cell Model Passports relations; why Jaaks Supplementary Table 2 lists 128 lines and omits HPAF-II (the figshare CSVs are used as the authority for the exclusion list and the union of all three sources is excluded).

Deviations from the brief:
- Jaaks Supplementary Table 2 and the paper full text were downloaded (open access, CC BY 4.0) to obtain the line list and authors' statement on GDSC comparison; the 10 MB supplement bundle itself is not stored (only table 2, hash in the manifest).
- `coverage_by_drug_cell.csv` covers the 63 mapped drugs and sibling IDs (9.8 MB); the other 232 DRUG_IDs are only in the compressed `coverage_all_gdsc2_records.csv.gz`.
- One PubChem call failed at network level (all other calls and 503 retries are receipted).

## 9. Disclosure of an outcome-adjacent exposure (hard-rule deviation)

While locating the Jaaks cell-line table in the supplement bundle, I printed the sheet names, header row and first one or two data rows of seven supplementary workbooks. For Supplementary Tables 1, 3, 4 and 5 this displayed published *aggregate* Jaaks statistics for two or three breast combinations (combination-level synergy counts and percentages, one biomarker p-value and mean response). No per-line synergy labels, no figshare outcome columns, and no GDSC2 outcome values were seen. Nothing was used in any deliverable. The exposure is logged in `access_log.jsonl` (`outcome_values_read: true`) so the lead can decide whether it matters; it concerns breast pairs aggregated over all 51 lines (both E and HD).

## 10. Items that block or condition pretraining

1. No blocker for freezing the observation contract. The target (`y_rel`) and the exclusion list are fully specified from metadata.
2. Condition: only cross-tissue transfer is testable (Jaaks tissues have 1 to 4 non-Jaaks cells with mono data); claims must say so. The mono signal for the Jaaks tissues exists only in the excluded Jaaks lines (ceiling diagnostic arm, separate).
3. Condition: fitted-parameter transfer with a joint-fit provenance limitation; any independence claim must say same institution, protocol, lines and possibly shared fit.
4. Condition: 2265 and the composite remain without mono labels (100 of 2,575 tissue-pair rows); they stay in the menu with scratch-initialised embeddings and a coverage flag.
5. Resolve before reading values: pooled vs ID-equal sibling policy (default ID-equal only), grouped validation seed, and whether the 6 cells without context are dropped (default dropped).

## 11. Columns opened (exact)

- `GDSC2_fitted_dose_response_27Oct23.xlsx`: header row names for all 19 columns; cell values only for DATASET, NLME_RESULT_ID, NLME_CURVE_ID, COSMIC_ID, CELL_LINE_NAME, SANGER_MODEL_ID, TCGA_DESC, DRUG_ID, DRUG_NAME, PUTATIVE_TARGET, PATHWAY_NAME, COMPANY_ID, WEBRELEASE, MIN_CONC, MAX_CONC. LN_IC50, AUC, RMSE, Z_SCORE cells were skipped before their value element was read (the XML parser still tokenises those bytes; no value is extracted or stored).
- `original_screen_all_tissues_fitted.csv` and `validation_screen_all_tissues_fitted.csv` (design whitelist via `usecols`): BARCODE, COMBI_ID, Tissue, CELL_LINE_NAME, SIDM, COSMIC_ID, ANCHOR_ID, ANCHOR_NAME, ANCHOR_TARGET, ANCHOR_PATHWAY, ANCHOR_DRUG_TYPE, ANCHOR_Clin_Rel, ANCHOR_CONC, LIBRARY_ID, LIBRARY_NAME, LIBRARY_TARGET, LIBRARY_PATHWAY, LIBRARY_DRUG_TYPE, LIBRARY_Clin_Rel, LIBRARY_CONC. Not read: ANCHOR_VIABILITY, LIBRARY_RMSE/EMAX/XMID/XMID_uM/AUC/fAUC, all SYNERGY_*, Synergy, DAY1_NORM_MEAN/SD, GROWTH_RATE, DOUBLING_TIME. (Header lines were read to confirm names.)
- `partition.json`: `split` (SIDM lists), `counts`.
- PROGENy files: header row only (SIDM list); no scores.
- Jaaks Supplementary Table 2: Tissue, Cell line, SIDM, COSMIC ID, Replicate cell line, In validation screen, Supplier:Cat.No., Screen Media (other columns, e.g. PAM50, genotype, density, exist but are not used).
- Cell Model Passports model lists: model_id, sample_id, patient_id, parent_id, model_name, synonyms, tissue, cancer_type, model_type, model_relations_comment, COSMIC_ID, BROAD_ID, CCLE_ID, RRID.
- Documentation read as text: four Jaaks/GDSC combination PDFs, DepMap pages (drug sensitivity, data usage policy, model relationships), gdscIC50 sources, Jaaks article full text.

## 12. Files in `data_s0/`

`build_s0.py`, `access_log.jsonl`, `source_manifest.json`, `s0_facts.json`, `drug_identity_map.csv`, `cell_identity_map.csv`, `coverage_by_drug_cell.csv`, `coverage_all_gdsc2_records.csv.gz`, `coverage_count_by_drug.csv`, `coverage_tissue_by_drug.csv`, `ceiling_diagnostic_target_line_counts.csv`, `jaaks_pair_coverage.csv`, `fit_duplicate_groups.csv`, `observation_contract.json`, `overlap_with_jaaks.md`, `S0_REPORT.md`, `sources/` (downloaded metadata and documentation), `provenance/pubchem_receipts.jsonl` (per-call receipts).
