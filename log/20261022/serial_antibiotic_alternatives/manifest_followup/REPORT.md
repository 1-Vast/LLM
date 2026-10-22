# Tripartite official manifest-entry audit

2026-10-22. **One exact supplementary-media identity is confirmed from the retained primary article, but this finite follow-up did not authenticate an OA package manifest or a valid exact-project BioSample count.** It provides no evidence that BioSamples are absent, that the paper is unavailable, or that functional replay is qualified.

After registering `PROTOCOL.md`, exactly two sequential official GETs consumed **1,953 response-body bytes**; no truncation, retry, alternate query or package/PDF/genome download occurred. Unmodified bodies, status/headers/URL/hash/UTC and failures are preserved in this directory.

| Request | Actual result | Permitted conclusion |
|---|---|---|
| [Specified NCBI PMC OA endpoint](https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC12164588) | HTTP404, 1,588 bytes, HTML content type; no successful OA XML projection | This exact endpoint request failed. No package href/format/license/update was authenticated. It does not revoke the retained article's CC BY4.0 or show that a modern OA endpoint/package is absent. |
| [BioSample esearch](https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=biosample&term=PRJNA1254677%5BBioProject%5D&retmax=0&retmode=json) | HTTP200, 365 bytes; count=0, retmax=0 | Only this literal request returned zero. Its query semantics do not establish a valid exact project-link census. |

The BioSample response actually translated the requested `PRJNA1254677[BioProject]` to **`(PRJNA1254677[All Fields])`** and returned `errorlist.phrasesnotfound=["PRJNA1254677[All Fields]"]`, plus “No items found.” `fieldsnotfound=[]` does not repair that semantic fallback. Thus count zero is **not** an authenticated count of BioSamples linked to the project and cannot imply zero strains, genomes, clinical backgrounds, lineages or future tasks. This block did not fetch any BioSample ID, SRA Run or genomic/MIC values.

## Retained primary article supplementary-media identity

An offline whitelist projection of the existing `TRIPARTITE.xml` re-authenticated PMC12164588, PMID40478208 and DOI10.1093/molbev/msaf115, without reading/exporting figure/results or measurements. It found exactly one `supplementary-material` element:

- id `sup1`; content-type `local-data`; label `msaf115_Supplementary_Data`.
- nested media href **`msaf115_supplementary_data.pdf`**.
- explicit media mimetype/mime-subtype/title absent in this XML; `.pdf` is a filename extension, not a fetched document verification.

This is a concrete primary supplementary filename entry. It does not certify its public download URL/availability, page/table contents, machine-readable phenotype schema, or genome↔lineage↔schedule↔MIC join keys. The failed OA API supplied no package manifest to resolve those paths. Existing primary Data Availability still names PRJNA1254677 for genomic data; no new source result invalidates that author statement, and none proves a complete action/state/function replay table.

**Finite decision:** stop this two-request block. Preserve the exact supplement href and BioProject as source identifiers for a separately justified, separately registered metadata/schema qualification if root chooses one. Do not fetch the whole package or supplementary PDF, contact authors, start an architecture, infer clinical background counts or open functional/genomic values on this evidence.

Three synthetic projection tests passed: OA link/error retention, BioSample count/warning without ID export, and supplement href without article-result sentinel leakage. `VERIFICATION.json` records **21 PASS checks**, including the three pre-request frozen artifacts unchanged, two source lengths/hashes/status and body totals, exact query translation caveat, faithful whitelist projection and exact supplementary filename. Verification establishes source/absence-of-claim discipline, not biological signal or research-agent/RSI contribution. All new scripts are under research; all outputs and failures are in this log directory.
