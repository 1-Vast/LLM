# External observed-dose resource admission

Date: 2026-10-30. Direction 3 only. Overall episode: ACTIVE / NOT_ACHIEVED.

**Disposition: CONDITIONAL for an external observed-dose phenomenon check; NOT READY for outcome access or a new dominance model.** Simplicity authenticates the existence of harmonized raw screening archives, but no raw-table header or exact shared observed dose grid was admitted in this pass. Its calculated viability exports, fitted summaries, and DrEval's standard prediction targets cannot establish a reversal in independently observed dose measurements. This pass found neither a positive nor a negative external flip result.

The strongest practical next branch is a metadata-first admission of one original 72-hour screen, preserving well/experiment identities and control measurements. It remains conditional on an identity-only projection proving sufficient actual-dose support and interpretable experimental replication. PRISM requires an additional processing-stage audit because its published preprocessing uses fitted curves in corrections to the measurements.

## What was authenticated

| Artifact | Owning source and status | Admissible use now |
|---|---|---|
| Simplicity v1.0 landing page | Official app, HTTP 200; identifies OSF project `a9w5r` and separate raw, summary, calculated-viability and full-fit artifacts | Source and artifact contract |
| Simplicity primary article | Ling, *Simplicity: web-based visualization and analysis of high-throughput cancer cell line screens*, DOI `10.26502/jcsct.5079217`, PMID 38435702, PMC10906814; official full JATS and publisher supplement saved | Methods and lineage |
| Initially linked app paper | Xia et al., DOI `10.26502/jcsct.5079218`, PMID 38344217, PMC10852200; reference 24 leads to the actual Simplicity article | Table 1 supplies study-level assay/time metadata; this paper alone is insufficient methods evidence |
| DrEval article | Existing official JATS, DOI `10.1038/s41467-026-72903-w`, PMC13168506, Methods Sec16 / Par38–41 | Separates raw measurements, normalization, curve fitting and summary targets |
| DrEval code | Existing `daisybio/drevalpy` snapshot `c5a7274e9c843dc4f24797986446d39d22124195`; upstream `preprocess_drp_data` tree `e494b3b38d08b6325f062e06fd72062fdeafc578` and two exact notebook blobs saved | Source-code contract; no code was executed on drug-response data |

Exact quoted passages and stable paragraph/cell locators are saved in `primary_passages.txt`, `simplicity_supplement_methods.txt`, and the two `*_source_only.txt` files beside this report. Public originals and manifests are under `D:/MAESTRO/data/external/conditional_interventions_20261030/dose/`.

## Raw measurements versus fitted outputs

The official app says custom viability calculations use **“the fitted dose-response curves in Simplicity”** (`simplicity_index.html`, line 363). Pre-calculated viability files contain estimates at 11 generated concentrations, plus an optional second 11-point range to Csustained; these are **not measured dose grids** (lines 472–477). The `*_Results_v1.0.tsv` summaries contain curve parameters, tested concentration metadata, AUC and IC50 (lines 466–469). Full `drc` objects are fitted models (line 488). These artifacts can support a fitted-curve comparison, not an observed-only C1 check.

The app's raw-download link labels mistakenly say `*_Results_v1.0.tsv.7z` (lines 481–484). The OSF API resolves them to the following actual raw filenames. These are metadata records only; none of these four archives was downloaded.

| Actual OSF filename | Archive bytes | OSF download | OSF-reported SHA256 |
|---|---:|---|---|
| `CTRPv2_Raw_v1.0.tsv.7z` | 127,217,800 | `https://osf.io/download/6ezmg/` | `5280a2273de88a3ddb842ba065a2af893bdf5f079ca2f555f2967e746ba3efd7` |
| `GDSC1_Raw_v1.0.tsv.7z` | 38,766,678 | `https://osf.io/download/qmp7y/` | `5d9a03de96203406ec02710a03743ef6e459b22d2ed67249012e9e70f8da0874` |
| `GDSC2_Raw_v1.0.tsv.7z` | 24,144,226 | `https://osf.io/download/we7ry/` | `20efa6121e1c13803a717cf0efad43e868e4d6b3cb1a3dc5b8ebedc9ce894090` |
| `PRISM_Repurposing_Raw_v1.0.tsv.7z` | 239,866,619 | `https://osf.io/download/nbjdu/` | `dfe04e82a125edf26a67625b5fbc7dfbbdd52fefb1b51faf61968eb20f4d6ba6` |

The primary article describes these as **“Raw viability values from each screen following compound and CCL name harmonization”** (PMC10906814, body paragraph 18). That supports the existence of observed-source values, but does not by itself identify the processing stage or preserved fields in each archive.

For PRISM this distinction is consequential. Supplemental Methods P43 states that a four-parameter log-logistic fit is used to calculate per-well multiplication factors that align measured and fitted viabilities, with a correction shared across pooled cell lines. P45 then shifts median viabilities at concentrations below 1 nM to 100% per analyte/plate under a null-effect assumption. It is **unresolved whether the OSF raw archive contains pre-correction or post-correction values**. A predeclared control-based analysis of original MFI/control fields is a possible route; fitted corrections cannot silently enter an observed-only replication.

DrEval Methods Par40 says raw measurements are normalized per replicate and CurveCurator fits one model across replicates. Par41 describes within-dosage-group fitting and out-of-range EC50/IC50 invalidation. The saved loader defaults to `LN_IC50_curvecurator`; its allowed measures are summary endpoints. Existing `curvecurator.py` lines 31–64 also shows optional `replicate` support, aggregation of duplicate keys, and constructed zero-dose controls of 1.0. Such constructed controls are not fresh observations.

## Source ancestry, assay contract and grid support

| Resource | Exact Simplicity input lineage from Supplemental Methods | Assay/time in PMC10852200 Table 1 | What is still missing |
|---|---|---|---|
| CTRPv2 | P5–8: CTD2 `CTRPv2.0_2015_ctd2_ExpandedDataset.zip`, `CTRPv2.0._COLUMNS.xlsx`, `CTRPv2.0._INFORMER_SET.xlsx`, downloaded 2020-05-29 | Broad; CellTiter-Glo; 1536-well; 72 h | Original per-well header, exact concentration identities across comparisons, control semantics, run/culture independence |
| GDSC1 | P9–17: release 8.2 `GDSC1_public_raw_data_25Feb20.csv`, raw-data description; screened-compound and cell-line annotations; fitted files are separately identified | MGH/Sanger; Resazurin or Syto60; 96/384-well; 72 h | Which assay/site applies per experiment, actual `CONC` grid, raw control/run keys and independent-culture evidence |
| GDSC2 | P9–17: release 8.2 `GDSC2_public_raw_data_25Feb20.csv`, corresponding metadata and separate fitted response file | Sanger; CellTiter-Glo; 1536-well; 72 h | Exact observed-grid projection, row-level timing/replicate schema, original release description |
| PRISM Repurposing | P18–26: secondary-screen logfold change `20237730`, MFI `20237742`, cell info `20237769`, replicate-treatment info `20237760`, pooling info `20237766`; downloaded 2020-04-06. Separate fitted curve-parameter file `20237739` | Broad; HTS-PRISM or MTS-PRISM; 384-well; 120 h | Processing stage, pooling/control/replicate-treatment joins, observed dose grid, independent experimental units; 120 h cannot be equated with 72 h |

These are source-reported study conditions, not a verified row-level table contract. Assays measure different signals; matched numerical viability scales do not establish matched biological endpoints.

The DrEval CTRPv2 source notebook is informative without reading its outputs. Cells 4–10 load `v20.data.per_cpd_well.txt` and join `v20.meta.per_experiment.txt`, `v20.meta.per_cell_line.txt`, and `v20.meta.per_compound.txt` by `experiment_id`, `master_ccl_id`, and `master_cpd_id`. Cell 11 transforms `bsub_value_log2` with `2**x`. Cell 13 constructs replicate labels from within-experiment/concentration row occurrences plus experiment identity. Cell 58 maps `cpd_conc_umol → dose`, transformed `bsub_value → response`, CVCL → `sample`, CID → `drug`. These are code-inferred available fields, not a raw-header verification. A replicate label constructed this way does not prove an independently cultured replicate.

The current DrEval GDSC2 notebook uses **`GDSC2_public_raw_data_27Oct23.csv` and `screened_compounds_rel_8.5.csv`** (cells 4, 6), while Simplicity uses 2020/release 8.2 inputs. Cell 7 uses `SCAN_ID`, `POSITION`, `TAG`, `DRUG_ID`, `INTENSITY`, `CONC`, and negative/positive controls; normalization is `(INTENSITY - PC) / (NC - PC)`. Cells 15–19 construct replicate labels and use `CONC.round(10)` as `dose`. Cells 60–61 retain the original library-dose label as `lib_dose` and save normalized responses. Cell 69 separately reads fitted summaries dated 24Jul22. These mixed vintages must be reconciled before treating a packaged table as a single immutable source version.

**No exact concentration sequence, count of shared measured concentrations, count of eligible compound pairs, replicate adequacy, or cross-study match count was established.** Overlap of dose *ranges* does not imply overlap of observed dose *points*. No standard nominal grid is substituted for missing measured metadata.

Simplicity and DrEval are data-processing resources, not new independent experiments. Their CTRPv2 ancestry directly overlaps at the 2015 expanded CTD2 release. Their GDSC source families overlap, with exact version/well overlap unresolved. Reprocessing the same screen in two resources is an analysis sensitivity check. Distinct underlying screens can be external experimental comparisons only after matching identities, actual doses, timing and endpoints.

## Identity matching and prepared metadata

Simplicity primary article body paragraph 9 states that its harmonization uses prior manually curated tables, Cellosaurus, the Broad Drug Repurposing Hub, and webChem. DrEval Par38 states Cellosaurus CVCL accessions and PubChem CIDs when available. The code contains manual mapping exceptions and unmatched identifiers; labels alone cannot ensure exact chemical identity.

The following small, outcome-free supplemental tables are saved as original XLSX and projected TSV:

| Prepared TSV path under `D:/MAESTRO/data/processed/conditional_interventions_20261030/dose/` | Schema | Limitation |
|---|---|---|
| `Simplicity_Table_S1_PGX_CellLine_Name_Harmonizer.tsv` | `PGX_CellLine_Name`, `simplicity_CellLine_Name`, `Note` | PharmacoGx↔Simplicity names only, not a complete original-screen identity table |
| `Simplicity_Table_S2_PGX_Compound_Name_Harmonizer.tsv` | `PGX_Compound_Name`, `simplicity_Compound_Name` | Name map; does not prove salts, stereochemistry, mixture composition or exact original-screen IDs |

Cell-line notes explicitly keep `COLO 320`/`COLO 320HSR` and `Lu-99`/`Lu-99A` separate because equivalence could not be verified. Supplemental Methods P61–62 likewise exclude these ambiguous cell lines and some cross-screen matches of blebbistatin, bleomycin A2 and nutlin-3 because different chemical forms were screened. These exclusions must carry into a future identity contract.

The full harmonization workbooks have authenticated OSF metadata but were not acquired: `Harmonized_CCL_Data_v1.0.xlsx`, 416,053 bytes, SHA256 `217e5fc9b8e4660e40b95f5a109817ad46a9445dcdeef69b9a06979075f3c0b7`, download `https://osf.io/download/9q4zs/`; and `Harmonized_Compound_Data_v1.0.xlsx`, 240,205 bytes, SHA256 `3e066adf30d5ea925b9bcc9ede1c5c623ee466739f47967641703536abbe9fea`, download `https://osf.io/download/w9h76/`.

## Contract required before a C1-type check

A local observed reversal in relative compound advantage needs the same identified cell and two identified compounds, two predeclared comparable dose conditions, observed responses for both compounds at both conditions, matched timing/endpoint, and interpretable noise information. Under a same-concentration contract, the four measured points must actually exist at the shared concentrations; interpolation, fitted values and extrapolation cannot fill missing corners. Another dose-equivalence contract would need explicit scientific justification before outcomes are read.

Admission must first preserve source release, source cell ID and CVCL, source drug ID and verified structure/form, concentration with units, endpoint, treatment time, screen/experiment/plate/well keys, vehicle/positive controls, and the most defensible biological versus technical replicate identifiers. No numerical threshold or uncertainty model is selected here. After an identity-only feasibility projection, freeze the development/held-out and practical reversal contracts, then use designated development measurements to assess noise and headroom. A phenomenon check remains separate from held-out prediction and biological mechanism claims.

The next decisive reads are concrete and narrow: the original CTRPv2 column dictionary; `GDSC_Raw_Data_Description.pdf`; header/identity/control projections for one selected source; the full harmonization workbooks; and, for PRISM, the replicate-treatment/pooling metadata plus proof of which preprocessing stage its raw archive represents. The GDSC2 archive has a documented bounded size, but large-archive acquisition is unnecessary until the metadata contract is fixed. The request allocation is exhausted, so no further requests were made.

## Structural scout decision and actual exposure

`initial_structural_mapping.md` was saved before primary-source reading. Its premise was: **“A raw measured grid can support a local comparison while leaving continuous-dose or cross-context claims unidentified.”** The source work adds a necessary condition: a raw-labelled measurement can already be model-corrected, and apparent cross-study identity overlap can be false. The executed decision is to keep direction 3 conditional and to exclude calculated viability exports from an observed-only check. This is added measurement precision, not a developed candidate, donor-method transfer, novelty claim, or demonstrated benefit.

Reading scope: episode brief; innovation-research skill and source-scout guidance; saved DrEval Methods Par38–44 (Par42–44 concern feature provenance); saved loader/utilities and CurveCurator preprocessing/configuration passages; selected docs/README matches; official Simplicity landing prose/download descriptions/metadata help; OSF manifests; PMC10852200 section list, section 8, software section, Table 1 and reference 24; PMC10906814 body prose; all plain body paragraphs of its supplemental DOCX, including references and figure captions; identity headers and ambiguity notes in the two small XLSX tables; full CTRPv2 and GDSC2 notebook source cells (the GDSC2 mapping block omitted by initial display truncation was recovered in a bounded read). Supplemental figure images, raw response tables, and notebook output cells were not inspected. Primary-article qualitative quality-comparison prose and supplement captions were incidentally visible; no numerical drug-response outcome values were exposed or used.

Downloaded notebook originals contain historical stored outputs as bytes. The helper selected only cell `source`, never `outputs`; no notebook, fit, outcome summary, or new test was run. No developing candidate/model, HTS031, protected outcome, or confirmation/sealed asset was accessed by this worker. No core/index/library edits, installation, subagent, or external message occurred. No donor-directed search was attempted within this resource-admission allocation; donor works with operative methods inspected: zero.

## Access receipts and limits

Actual pass-3 traffic: **12 HTTP requests including 1 redirect; 16,851,011 completed response-body bytes; 0 HTTP errors; 0 known partial/unknown traffic.** No Content-Encoding was returned. Calls were sequential with a measured minimum 1.051871-second gap after the prior response completed. The receipt log records each request URL, status, headers, bytes, completion flag, timestamp, SHA256, and saved path in `http_receipts.jsonl`; `access_summary.json` records the arithmetic. `public_files.sha256.tsv` also hashes decoded notebook originals and supplement members; these derived local bytes are not counted again as network traffic.

| Request | Status | Body bytes | Artifact |
|---:|---:|---:|---|
| 1 | 200 | 45,396 | Simplicity landing page |
| 2 | 200 | 10,760 | OSF root manifest |
| 3 | 200 | 1,123 | Europe PMC metadata for linked app article |
| 4 | 200 | 8,682 | OSF raw manifest |
| 5 | 200 | 48,400 | PMC10852200 JATS |
| 6 | 200 | 303,163 | DrEval preprocessing tree |
| 7 | 200 | 4,455 | OSF harmonization manifest |
| 8 | 200 | 35,297 | PMC10906814 JATS |
| 9 | 200 | 841,914 | Exact CTRPv2 notebook GitHub blob |
| 10 | 301 | 300 | Publisher supplement redirect body |
| 11 | 200 | 14,727,811 | Publisher supplement ZIP |
| 12 | 200 | 823,710 | Exact GDSC2 notebook GitHub blob |

Only source retrieval, metadata projection, receipt arithmetic, and method-source extraction were executed. Initial local extraction attempts failed because BeautifulSoup was unavailable and inline shell quoting was unsuitable; both were replaced with standard-library file scripts, with no installation or extra HTTP calls. Requested model/effort was inherited; effective effort, token/cost telemetry and model-family independence were not exposed.
