# Could GDSC2 single-agent records be the same physical data as Jaaks single-agent / library fits or controls?

Stage S0 (before labels). Evidence is documentation, headers, design/identity columns and the Jaaks paper text only. No GDSC2 outcome value and no Jaaks outcome column was read. Numbers below come from `s0_facts.json` / `drug_identity_map.csv` / `coverage_*.csv`.

## Short answer

Cannot be excluded at the raw-data level, and is unlikely at the fitted-record level. Neither is authenticated.

- What is verified: the two studies are different screening campaigns that share institution, platform, protocol, cell-line panel and drug-ID registry. The Jaaks authors themselves describe GDSC single-agent IC50s as *independent screens* and used them as an external comparison (Extended Data Fig. 2e, n = 4,338 drug-cell pairs, natural-log IC50).
- What is not known: whether any plate, control well, compound stock/lot or cell passage is shared, and whether Jaaks plate data fed the GDSC2 release-8.5 NLME fit. The GDSC2 fitted file has no barcode, plate, date or lot column.

Consequence for the design: all 126 Jaaks lines are excluded from mono training and validation, which removes the only route by which a Jaaks library-versus-GDSC2 duplicate could enter through the cell axis. A drug-axis duplicate (same compound, other lines) is not leakage of Jaaks labels. The residual risk is a GDSC2 curve for a *non-Jaaks* line that was fitted jointly with Jaaks-line data (shared NLME parameters). That cannot be removed and must be disclosed as a provenance limitation: `NLME_RESULT_ID` is a single value (343) for all 242,036 records, so every fitted record is a joint-model output.

## What is known (each item with its source)

| Topic | Jaaks 2022 | GDSC2 (release 8.5) | Same? |
|---|---|---|---|
| Site | Wellcome Sanger Institute, GDSC platform (Jaaks, Methods) | Wellcome Sanger Institute (DepMap docs) | same institution |
| Plate / dispensing | 1,536-well, XRD384 seeding, Echo555 drugging (Jaaks Methods; Screening_documentation.pdf) | 1,536-well, Echo555 (DepMap docs, GDSC2 section) | same platform |
| Readout / duration | CellTiter-Glo 2.0, 72 h, 24 h pre-plating | CellTiter-Glo, 72 h, 24 h pre-plating | same protocol |
| Normalisation | per plate (treated - blank)/(NC - blank), NC = DMSO | per plate, negative = DMSO/medium, positive = blank | same form |
| Controls | DMSO n=126, untreated n=6, blanks n=28, staurosporine n=20, MG-132 n=20 per plate | not stated for GDSC2 files | unknown |
| Single-agent fit | per-plate 2-parameter sigmoid [Vis et al. 2016]; LIBRARY_XMID in log2 units, 9 = top dose | NLME 2-parameter model of Vis et al. 2016 (gdscIC50), one joint fit (NLME_RESULT_ID 343) | same method family, different fit runs |
| Library dose design | 7 doses, 1,000-fold, non-equidistant; max conc drug- and tissue-specific from a pilot in 9-13 lines per tissue | 7 doses, 1,000- or 1,024-fold; MAX_CONC per DRUG_ID and dose-range group (458 groups over 295 DRUG_IDs) | design overlap |
| Drug registry | Sanger DRUG_ID (65 distinct, incl. composite `1032|1372`) | Sanger DRUG_ID (295); 63 of the 64 single Jaaks IDs present, names equal in all 63 | same ID space |
| Compound sourcing | commercial vendors (Supplementary Table 1 not retrievable here as a vendor/lot list); stored in Roylan storage pods | industry/academic/commercial; Roylan storage pods | stock identity unknown |
| Cell lines | 125 (original) + 1 (validation-only, HPAF-II) lines; Supplementary Table 2 lists 128 names | 969 SIDMs; all 126 Jaaks SIDMs present, COSMIC IDs and names agree exactly | same lines, same SIDM |
| Release date | paper Feb 2022; figshare files 2022 | file dated 27 Oct 2023 | GDSC2 file is later than the paper |

Further design-level facts:

- Library maximum concentration (Jaaks `LIBRARY_CONC`, design column) equals a GDSC2 `MAX_CONC` value for the same drug in 59 of 63 mapped drugs. The four that do not: Dactolisib (Jaaks 0.1 vs GDSC2 0.25), MK-1775 (4 and 10 vs 10), Gemcitabine (0.2 and 10 vs 1 and 10), Luminespib (0.1 vs 0.25 and 1). Equal dose-range designs are not evidence of equal data, because the Jaaks pilot concentrations were chosen with GDSC-style ranges.
- GDSC2 contains 7,448 records for the 63 mapped drugs in the 126 Jaaks lines (12 to 63 drugs per line, median 59). The GDSC2 breast, colon and pancreas panels are almost entirely the Jaaks lines (Cell Model Passports tissue, GDSC2 cells: breast 52 of which 51 are Jaaks; large intestine 48 of which 45 are Jaaks; pancreas 31 of which 30 are Jaaks incl. HPAF-II), so the Jaaks lines were drawn from the GDSC panel.
- Jaaks Extended Data Fig. 2e compares Jaaks library IC50 with "corresponding drug responses from the GDSC" on 4,338 drug-cell pairs. That is far fewer than the 7,448 records now available, so the comparison used an earlier GDSC release or a subset (not stated).

## What is unknown (and cannot be settled from metadata)

1. Plate barcodes, screening dates and compound lots of GDSC2 records (not in the file). Jaaks has 3,106 plate barcodes; the two ID spaces cannot be matched.
2. Whether the Jaaks pilot screen (9-13 lines per tissue) or Jaaks library plates were also deposited into GDSC2.
3. Whether the GDSC2 release-8.5 NLME fit included any Jaaks plate data (the fit is joint; `drug` is DRUG_ID plus max concentration).
4. Whether the compound stocks are the same: `COMPANY_ID` in GDSC2 is an undocumented company/source code (17 values; 1046 for 166,344 records; exactly one value per DRUG_ID) with no lot; Jaaks Supplementary Table 1 names vendors, which cannot be joined to COMPANY_ID.
5. Whether Jaaks anchor single-agent viability and library fits could be recomputed from GDSC2 curves: they cannot, because the Jaaks anchors are measured at two fixed concentrations (single points), not curves.

## Handling rules adopted for S1

- Exclude every Jaaks SIDM (126 design + 3 listed only in Supplementary Table 2, which are not in GDSC2) and every Cell Model Passports relative (none found in GDSC2; see cell map) from mono training and from mono validation.
- Treat the GDSC2 mono labels as fitted-parameter transfer with a joint-fit provenance limitation; do not describe them as independent observations.
- Keep the "target-line own mono" arm (the Jaaks line's own GDSC2 record) as a separately flagged ceiling diagnostic, counts in `ceiling_diagnostic_target_line_counts.csv`; it is NOT eligible for the primary pretraining set and any use of it must be reported as a different, leakier question (the Jaaks authors report library IC50 highly correlated with the GDSC response in the same lines).
- Any claim of "independent external supervision" must carry: same institution, same protocol, same cell lines, possible shared fit, unknown lot overlap.
