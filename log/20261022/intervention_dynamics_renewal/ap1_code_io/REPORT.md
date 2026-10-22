# AP1 memory static code-I/O audit

Date: 2026-10-22 local. Reviewer: `/root/functional_auditor`.

**Decision: three exact code blobs authenticated; a state→function join is not authenticated by these files.** The code identifies a useful colony-count endpoint and its source objects, but does not establish independent-run identity, drug/time dictionaries for the CSV labels, or a connection to the FISH-state tables. A matched-condition population-mean task remains possible after those keys are authenticated; same-cell identity is not required for that narrower task.

Only three GET requests were made, all HTTP200, total18,671 decoded HTTP-body bytes. The retrieved R/Rmd files were read as text and never executed. No CSV, spreadsheet, rendered HTML notebook or plot was fetched or opened. The primary article was reused offline from `skeptic/AP1_MEMORY_PRIMARY.body`. The separate source workbook obtained by root was not inspected in this task.

## Exact source identity

Repository: `arjunrajlaboratory/cellularmemory`; complete tree `ed565d810bd1aa0b067c761c13bfb98989240417`, `truncated=false`. The local manifest SHA256 is`5d8b74c62eeecc65511714318d426f6449c6a0f7ffd25a81cec4b18ded88554f`. Each file's SHA1 was independently recomputed as `SHA1("blob " + decimal_length + NUL + file_bytes)` and matched both the manifest and GitHub blob response.

| Exact code path | Decoded bytes | Verified Git blob SHA1 |
| --- | ---: | --- |
| `code/incucyte/tram.Rmd` | 4,328 | `9eac05b111e0d5aae3f4fbbafd527a4aa023b789` |
| `code/incucyte/ap1i/jnk_stat.Rmd` | 3,338 | `1b5064e60674e3935f8bc5290a0395aa2f966e70` |
| `code/dexmemFISH/dexmemfish_function.R` | 5,228 | `5ea491ea51baf35d21d3169e22a91bb5a655a0ee` |

`REQUEST_01.json`–`REQUEST_03.json` preserve exact blob URLs, UTC start/end, status, response bytes/SHA256, decoded bytes/SHA256 and blob verification. Published code is preserved under `research/intervention_dynamics_renewal_20261022/ap1_published_code/`. Fetch/extraction helpers are in that research directory. `STATIC_EVIDENCE.json` contains all receipts, static schemas, exact input manifest entries and relevant primary methods.

## Colony endpoint and repeats actually used

Both Incucyte scripts read CSVs with `header=TRUE`, group by the single consumed column`Name`, and compute `colony=n()`. Their functional observation is therefore **one row count per(Name,input file)**, with an`exp` identifier supplied by the script. Neither script consumes a time, well, annotation ID, image field, lineage ID, area or initial-cell-count column; neither performs unique-colony deduplication or normalizes by the number of cells plated. The code assumes CSV rows are countable colony annotations. Whether each row is one final colony, a repeated annotation/time point, or another exported object must be established from headers and design metadata before adopting that endpoint.

The primary Image analysis methods describe manually segmented cells, SegmentAnything-segmented colonies, tracking to distinguish single-cell-derived and merged colonies, and NimbusImage CSV/JSON export. This supports the intended colony phenotype but does not identify the exact row unit of these unopened CSVs. It also does not turn individual colonies or image fields into independent experimental runs.

`tram.Rmd` lines24–62 uses these seven files:

| Source branch | Exact CSV basename(s) | Derived exp label(s) |
| --- | --- | --- |
| `extractedData/incucyte/t5224/` | `VID2180.csv`, `VID2181.csv` | `exp2180`, `exp2181` |
| `extractedData/incucyte/jnkin8/` | `VID1516.csv`, `VID2536.csv`, `VID2112.csv` | `exp1516`, `exp2536`, `exp2112` |
| `extractedData/incucyte/tram/1541/` | `VID1541_repA.csv`, `VID1541_repB.csv` | `exp1541A`, `exp1541B` |

All seven are present with exact size/SHA in the existing manifest. After binding, the code retains only **`hi1`, `lo1`, `lohi1`** and discards otherName categories. Thus this script pools common selected conditions from several assay branches; it is not evidence for seven independent tram-only experimental runs. Such control pooling could be legitimate if conditions match, but drug history, dose, duration and background must be checked. The two1541 files especially require a definition of repA/B: different names and script-assigned exp labels do not prove different biological starts.

The script fits a random-intercept model by`exp` and also performs paired tests on condition vectors. The latter uses vector position, without an explicit exp-keyed join. Any missing condition could disrupt that implicit pairing. No published tests were rerun or adopted as validation of a new prediction task.

## Explicit zero and excluded repeat

`jnk_stat.Rmd` reads the three JNK files1516,2536,2112 and retains allName categories. A fourth label`exp2925` occurs only in a commented-out binding expression and is not read or included; the reason is not given by this code.

Lines43–51 insert a **published observed zero**: `(Name="hi2",colony=0,exp="exp2536")`. The author's comment says this condition had no resistant colonies and all cells died. This is not a measured CSV row inspected here; it is an explicit outcome correction embedded in the published analysis. Counting only existing annotation rows cannot recover zero-colony categories without a complete design roster. A future reconstruction must preserve this provenance, verify the condition dictionary, and distinguish an observed empty condition from an unmeasured/missing condition. Do not silently treat every absentName as zero.

This code exposure is now part of the record. The exp2536/hi2 outcome must not be described as a sealed test observation for the current team. No rendered model summaries, p-values or other output tables were read.

## FISH I/O, labels and processing

`dexmemfish_function.R` defines a generic function accepting`inputdirectory` and`outputdirectory`; it contains no active caller specifying an experimental replicate or condition set. It lists CSV files in the supplied directory, reads them, adds a filename-suffix label and binds rows. It does not recursively collect every replicate directory or establish that any particular rep directory is a biological repeat.

Its expected columns are:

- Required by downstream operations:`cy3`, `a594`, `cy5`, `cy7`, `cell.Blob.Blob.metrics...Area`.
- Also listed for numeric conversion when present:`cell.Blob.Blob.metrics...Perimeter`, `cell.Blob.Blob.metrics...Centroid...y`, `cell.Blob.Blob.metrics...Centroid...x`.
- Derived`file_identifier`: everything after the final hyphen and before`.csv`; for example a suffix resembling`2_3ddex` remains a string. No time, drug, dose or replicate dictionary is parsed.
- Derived`file_id`: bind-list position. It is dropped from downstream plotting selections and is not a biological identifier.

The code computes each of three channels divided by`cy7`; it also multiplies the exported area by calibration0.0467 and plots channel counts per resulting area. It does not state which gene each channel represents; the small manifested`probes.txt` objects were not read in this scope. Primary methods identify the fluorophores, fixed-cell RNA FISH and spot counting, but a fluorophore name is not a gene mapping.

Numeric coercion can introduceNA. The raw melted and area-normalized tables use`na.omit`; the ratio-normalized table has no equivalent explicit omission or denominator-finiteness check. `outlier.shape=NA` suppresses boxplot outlier symbols; it does not delete those observations from the data. These are static processing facts, not claims that the unopened data contain invalid values.

Manifest suffixes and folders provide candidate condition/repeat labels, including nominal3-day dex, washout and later tram conditions across several`rep*` directories. They are metadata leads only. Acquisition timestamps and CSV position cannot be converted into biological time or independent run IDs without the experimental dictionary. Some early and late files have different acquisition dates even within one folder; this does not itself prove or disprove a valid paired-condition design.

## Actual join and next boundary

There is **no join, merge, shared-cell-ID mapping, or condition/run mapping between FISH and colony data in the three audited files**. Colony code uses `(exp,Name)` assigned fromVID files. FISH plotting uses filename suffixes and an externally supplied input directory. No code connects these two label systems. Shared mention of trametinib is insufficient: dex-priming/washout histories and low/high tram dose-escalation histories must not be conflated.

To establish a lawful matched-condition prediction task, the next audit needs an authenticated dictionary tying line/clone, drug/dose, pretreatment duration, washout, challenge timing and independent run to both assays. Fixed-cell FISH requires a population/condition join, not an invented same-cell future. A complete functional condition roster is also necessary to represent zero-colony outcomes. The generic primary statement that most experiments have at least three biological replicates cannot authenticate the independence of each file or pair.

Root will choose the next exact header/source-workbook object. For convenience, `STATIC_EVIDENCE.json` records exact manifest entries for1541A/B, the zero-bearing2536 file, and small candidate early-state FISH files. No such object was fetched here. In particular, the manifest gives1541A11,843B/blob`087d74383adb80b1be16f88332a0e55b5a99b9be`,1541B11,908B/blob`41d5f73be50ab34bd6be8516dae2a4f7a1333476`, and2536 8,757B/blob`1eaa3ea6ff81b82e89e747766da9fd733c8422b6`. These provide exact next-step targets without opening outcomes in this audit.
