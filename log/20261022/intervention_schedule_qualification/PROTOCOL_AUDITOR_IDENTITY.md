# Preregistered GSE30516 metadata identity audit

2026-10-22, Asia/Shanghai. Registered after reading `ADVOCATE_SOURCE_REPORT.md` and its authenticated official GEO accession, before either new request. This is a dependent exact-accession qualification, not a repeat of earlier failed article requests.

At most two new public HTTP requests; <=2,000,000 combined response-body bytes; no retries or third fallback. Runtime maestro. All code in `research/intervention_schedule_qualification_20261022/` with `auditor_` prefix; all raw response bytes, receipts, tests and metadata outputs in `log/20261022/intervention_schedule_qualification/auditor_sources/`.

1. Official GEO family MINiML metadata: `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE30516&targ=all&view=full&form=xml`.
2. Official GEO series-only SOFT metadata: `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE30516&targ=self&view=full&form=text`.

A separate worker owns acquisition and projection. Raw bodies remain in `sealed_source/` and are not opened by the researcher. For MINiML, discard any Data-Table XML block from byte data before XML text decoding, then whitelist sample accessions/title/type/platform references, source/organism/characteristics and explicit growth/treatment/extraction/label/hybridization/scan/data-processing protocol text. Export supplementary file names/URLs only, without fetching linked data. Reject malformed/non-MINiML payloads with stage/error type, never print source rows. For SOFT text, stop before `!sample_table_begin`; only series identity/title/type/pubmed/platform/sample IDs, summary/design and supplementary filenames leave worker. No expression values, phenotype values, processed matrix, raw CEL, data-table rows or full source body printing.

Synthetic checks before acquisition cover Data-Table removal/no numeric sentinel leakage, whitelist exclusion and stopping before SOFT table rows. Identity/protocol doses/times are permitted metadata; they are never treated as measured responses. Freeze code/protocol/scout source hashes before worker.

Questions: Are all 25 authenticated sample accessions recovered? What exact cell-line labels, drug, dose and treatment-duration metadata are released? Are molecular arrays only first-drug priming, or do they cover the actual order/simultaneous/reverse branches? Are linked supplements expression-only, or is there an authenticated raw apoptosis/phenotype manifest and join key? Sample metadata cannot prove actual culture independence, matched functional observations, complete alternative action menus or inheritance/RSI task eligibility.

Stop after two requests regardless of response success. Report actual coverage and source gaps. No architecture, numerical response opening or performance experiment is authorized by positive metadata availability.
