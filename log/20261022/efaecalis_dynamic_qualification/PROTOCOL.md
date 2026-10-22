# E. faecalis temporal collateral-sensitivity source qualification

Preregistered 2026-10-22 before the S1Data request or workbook inspection. Exact source: Maltas, Huynh and Wood, *Dynamic collateral sensitivity profiles highlight opportunities and challenges for optimizing antibiotic treatments*, PLoS Biology (2025), DOI 10.1371/journal.pbio.3002970, PMC11709278. This is a new source-qualification task, not a reopening of the chemical-genetics mechanism or a method experiment.

## Scope and acquisition

Root explicitly authorizes **one GET**, no redirect following/retry, to `https://journals.plos.org/plosbiology/article/file?id=10.1371/journal.pbio.3002970.s001&type=supplementary`, maximum **30,000,000 body bytes**. Official S1Data identity `pbio.3002970.s001.xlsx` is authenticated by the retained primary XML and METHODS/availability projection. Save raw body, URL, timestamps, status, content type/disposition, Location, received bytes and SHA256, including partial/error bodies. A 302 is retained with Location and not followed. Failed requests or insufficient identity do not mean the data do not exist. No alternate/second download is automatically made in this block.

Use maestro Python `-B`. Code/tests only in `research/efaecalis_dynamic_qualification_20261022/`; all protocol/data/log/failure/test artifacts only here under `log/20261022/efaecalis_dynamic_qualification/`. No DeepSeek/model calls, author messages, models, predictor baselines or novelty experiments. Preserve prior source reports.

## Prior design exposure and biological distinction

The already retained `dynamic_source_followup/ncbi_scout/REPORT.md` and `PRIMARY_METHODS_AVAILABILITY.json` are literature/design-exposed. Main experiment: 5 selection antibiotics ×4 lineages, 8 daily passages, dynamic collateral profiles at day2/4/6/8. Frozen stocks were plated and a single colony selected for IC50. Challenge dose curves have 3–4 technical replicates. Selecting concentrations adapt to earlier visible growth; dose histories are not randomized.

A separate experiment selects **20 independent CRO populations for 14days** and samples each day for a DOX dose challenge. It is not an authenticated serial multi-switch continuation experiment. Root's existing original d-MDP baseline uses phenotypic resistance-vector states, antibiotics as actions and time-varying transition models; those mechanisms are already published. Source qualification cannot constitute novelty or RSI evidence.

## Read-only projection

1. Freeze this protocol, downloader/projector, tests and prior reports before acquisition. Run synthetic guard tests before any source workbook is opened.
2. On a successful XLSX response, retain a complete internal ZIP manifest. Do not rewrite, recalculate, render or export the workbook. Parse OOXML using stdlib in read mode; identify workbook/sheets, dimensions, merged ranges, cell-type/formula counts and string coordinates. Do not interpret or emit any numeric, boolean, error or date cell contents, formulas/cached results, IC50/OD/AUC response arrays, statistics or plots.
3. Project schema/headers and drug/gene/day/lineage/control/replicate identity strings wherever they occur. Exact drug names/abbreviations are permitted; avoid the prior mistake of masking all unknown entities. Generic identity/assay headers and known control labels are permitted. Numeric strings, numeric dose/measurement text and pure/binary outcome strings such as Yes/No, XR/CR/CS/neutral, validated/bidirectional/monochromatic, resistant/sensitive, high/low and success/failure are withheld. Unknown nonnumeric strings not suspected to encode outcomes may pass **with an explicit unclassified-design-exposure annotation**. Suspected phenotype/class/future-outcome text is withheld rather than presumed to be identity. This guard is not a proof that all possible string-encoded endpoints were removed; any unforeseen qualitative outcome exposure is recorded and excluded from later sealed claims.
4. Do not expose concentration values at this stage, even if numeric strings. Once exact identity/design columns are identified, any day/lineage/concentration values require a separate preregistered targeted census. Concentrations, if later opened, are design plus prior-feedback-exposed; they cannot be treated as random interventions or free future knowledge.
5. Optionally inspect only nonnumeric identity/design text in the retained primary Table1 (drug names/abbreviations/mode labels) to authenticate naming. No primary results tables or response arrays are projected. Keep main-clone and independent-population identities separate.
6. Report exact candidate columns/rows and legitimate query/state/function units, including missing keys/controls/replicate/branch provenance and dependence. Do not infer completeness of 400 combinations from design alone or count days/doses/technical replicates as independent tasks. Rehash original workbook, frozen code/protocol and prior reports after inspection.

## Success and stops

Success: retained official response plus authenticated usable sheet/identity schema, or a precise retained failure/redirect with the next lawful object. If lineage/day/clone-versus-population/branch identity cannot be established, stop the corresponding temporal/continuation claim while retaining whatever functional source is actually qualified. A 302, binary download failure or finite source budget is not evidence of absent data and does not complete the overall research goal.

Spreadsheets skill and read-only/scientific guides apply; no authoring marker/import/export/recalculation. User maestro and log/research placement override generic artifact-authoring defaults.
