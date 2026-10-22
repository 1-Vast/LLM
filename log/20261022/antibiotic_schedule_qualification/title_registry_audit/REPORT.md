# Antibiotic schedule title/author registry result

2026-10-22. **A public data-paper link is authenticated:** [Zenodo 22118144](https://zenodo.org/records/22118144), DOI `10.5281/zenodo.22118144`, by Yoon Jeong, cites the target bioRxiv DOI `10.1101/2025.10.30.684665v1` directly in its registry description. The record is titled *Multiplex Microfluidics(TAY LAB)_All 512 Chamber Images*, dated 2026-08-26, with concept/parent record 18362220. The earlier exact-DOI relatedIdentifier search missed this record because its structured `related_identifiers` is null and its title differs from the paper. This replaces any temporary “not yet linked” inference from the initial title-only results.

The four preregistered sequential public metadata requests all returned HTTP200, no truncation, consuming **41,111 bytes**. Zenodo title phrase returned zero; DataCite title-field phrase returned zero; Figshare search returned ten broad, unrelated titles/other paper DOIs, so it cannot be described as an exhaustive zero result. Zenodo author/context query returned four records: the linked Jeong chamber-image record, an unrelated E. coli susceptibility study, a distinct Tay-lab macrophage immune-pulse dataset/software record, and an unrelated bubble-streaming paper. Same-lab authorship is not a reason to merge those datasets into this antibiotic task.

An independently registered offline worker projected only DOI/URL citations and exact target-title/DOI presence flags from already saved description metadata. It did not export prose, response values or images. The exact target DOI match and matched Yoon Jeong creator authenticate the direct link despite the absent structured relation. The original citation strings include HTML `&nbsp`/bibliographic punctuation; `LINKED_RECORD_MANIFEST.json` records explicitly normalized identifiers while retaining the unaltered original citation projection. No fifth HTTP request occurred in this four-request block.

## Actual public file manifest, not archive contents

| File | Listed bytes |
|---|---:|
| 1024Chamber_whole_view_x60.png | 31,972,215 |
| 1024Chamber_whole_view_x40.png | 30,960,299 |
| 1024Ch_x40.zip | 2,188,028,156 |
| 1024Ch_x60.zip | 2,188,028,168 |
| 1024Ch_x60_labeled.zip | 1,569,160,952 |
| 1024Ch_x40_labeled.zip | 1,487,898,772 |

Total advertised payload is **7,496,048,562 bytes**; none was downloaded. The record title says 512 chambers while filenames say 1024Ch; this identity discrepancy is preserved rather than reconciled by assumption. The manifest authenticates these named files, not their internal directory tree, microscopy content, labeled annotations, timelapse coverage or condition keys. In particular, no strain/drug/dose/order/lag/run/chamber/colony/time identity table, matched functional response schema or complete actual schedule menu is established from this manifest. ZIPs may contain additional objects; this block has not opened them and does not claim they contain only images.

**Finite decision:** title/author discovery succeeded at locating a directly paper-linked public file record, so “no public source was found” is no longer accurate. Actual intervention-state-function menu remains **NOT_QUALIFIED**. These filenames and authors do not justify model/agent/RSI implementation, image downloading, or treating platform chamber counts as independent tasks. Stop this four-request block here; a separate explicitly registered source-key/version qualification can use the new exact accession if independently justified.

All raw metadata and receipts are under `sealed_metadata/` and `NETWORK.json`; no publisher retry, fulltext bypass, code/GitHub request, image, numerical table or raw experimental payload was fetched. Three registry-projection synthetic tests and two offline-citation synthetic tests passed. `VERIFICATION.json` records 29 actual source/freeze/link checks, including three unchanged original frozen inputs, the four source hashes/byte totals, direct citation normalization, author and six-file manifest. This checks provenance and source identity, not scientific signal or performance. Later citation/verifier scripts are not described as pre-request frozen code.
