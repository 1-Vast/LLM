# Outcome-blind workbook structure protocol

Preregistered 2026-10-22, before acquiring or opening the workbooks. This is a source-qualification subtask, not a numerical research experiment. Existing parent reports remain unchanged.

## Authorization and runtime

Parent explicitly authorizes exactly one GET to `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11726442/supplementaryFiles`, with at most 60,000,000 received body bytes, no retry, mirror, redirect following, or model API. Use `D:/anaconda/envs/maestro/python.exe -B`. Code/tests belong under `research/chemical_genetics_qualification_20261022/`; records, raw inputs and synthetic test artifacts belong only here under `log/`.

## Sequence and checks

1. Freeze this protocol, acquisition/projection code, synthetic tests and old report hash before the request. Verify the projection on synthetic adversarial cells before any source workbook is opened.
2. Save the request URL, UTC start/end, HTTP status, received-byte count, SHA256, content type and raw body, including failures/partial bodies. Disable redirects and retries. A cap, failed request, invalid ZIP, absent/ambiguous whitelist member or parse error is reported, not repaired through another request.
3. Export a complete ZIP central-directory manifest (path, compressed/uncompressed sizes, CRC and directory flag). Extract only unique exact basenames `41564_2024_1857_MOESM3_ESM.xlsx` and `41564_2024_1857_MOESM7_ESM.xlsx`. No FASTQ or any other ZIP member is extracted. Save workbook hashes; do not rewrite/recalculate/render workbooks.
4. Parse XLSX OOXML with Python stdlib `zipfile` and `ElementTree` in read mode. Export all sheet names, declared dimensions, merged ranges and cell-type/formula counts. Export only a conservative string-label projection for rows 1–30 inclusive. Do not export numeric/boolean/error/date values, formulas, cached formula results, cell matrices, statistics or any numeric response.
5. Each candidate string cell in rows 1–30 receives its coordinate and either an approved generic header/identity label or a withholding reason. Decode shared/inline/rich strings only inside the process. Numeric strings, dose-like strings, missing tokens and response-related terms (including XR/CS/neutral/phenotype, resistance/sensitivity, fitness/growth, IC90/MIC/AUC, synergy/antagonism) are withheld. Generic headers and explicitly labelled lineage/replicate/day/ancestor/control identifiers may pass. All other strings are withheld as unqualified entity/text, including exact drug names, abbreviations and doses; their value scope requires a later explicit protocol. This stricter allowlist avoids assuming that an unfamiliar string is safe.
6. Identify candidate exact header/identity coordinates from this projection for a separately preregistered targeted census. Do not infer unique pair counts, joins, trajectories, sample equality or task independence from sheet shape. Rehash old report, source workbooks and frozen files after inspection.

## Success and stop conditions

Success: a retained official response and complete ZIP manifest, the two unmodified whitelisted workbooks, structural metadata and a constrained first-30-row string projection, with candidate identity axes/columns or an explicit statement that masked labels prevent their determination. No research-performance or novelty claims follow.

Stop this acquisition block on any failed check. Preserve the failure and notify the parent with the next required source/authorization, rather than silently retrying or treating a finite source block as completion of the research goal.

## Exposure limits

The raw ZIP/XLSX files necessarily contain endpoint data; acquisition is not evidence that these endpoints were evaluated. Numeric cell text may be XML-parsed internally for structure but is never interpreted or emitted. String filtering cannot prove that no string encodes an endpoint or that all outcome-related terms are recognized. Approved generic labels themselves constitute schema/design exposure, not held-out evidence. No hidden worksheet contents, comments, formulas, drawings, charts, pivot caches or external links are separately projected. Unknown text is conservatively withheld. Exact drug/dose metadata is deferred even though generic drug/dose headers are allowed.

## Skill use

Applied Spreadsheets skill and its read-only Q&A/scientific-research guides. No authoring marker, artifact import, XLSX export, rendering or recalculation is performed. The user's maestro runtime and log/research placement take priority over generic authoring defaults.
