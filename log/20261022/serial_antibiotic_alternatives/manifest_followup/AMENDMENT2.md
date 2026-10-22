# Explicit amendment 2: current PMC host and actual BioProject relation

2026-10-22, registered after the original two-request REPORT/STATUS were completed, before these new requests. Root explicitly authorizes continued source qualification. Original failure bodies/receipts/report are preserved unchanged: legacy www.ncbi.nlm.nih.gov PMC OA path returned404; the requested BioSample BioProject field silently became an All Fields phrase. Neither is a valid reason to close the scientific asset.

This separate amendment permits **at most three new official GET requests**, combined additional consumed body <=500,000 bytes, no retry/substitute, single writer, refuse overwrite:

1. Current PMC-host metadata `https://pmc.ncbi.nlm.nih.gov/utils/oa/oa.fcgi?id=PMC12164588`. This is an explicit host-migration qualification, not a publisher restriction bypass or a repeat of a 429 response.
2. Entrez `esearch.fcgi?db=bioproject&term=PRJNA1254677&retmax=5&retmode=json`, to obtain real project Entrez IDs and query translation.
3. **Only if request2 returns a real nonempty all-digit project ID**, one Entrez `elink.fcgi?dbfrom=bioproject&db=biosample&id=<returned IDs>&retmode=json`, using exactly the returned IDs (at most five). No guessed IDs or project-to-SRA fallback.

Export OA record/package href/format/license/update; BioProject count/IDs/QueryTranslation/errors; BioProject→BioSample link-name/IDs/count, with relation ambiguity preserved. A count of linked records is not a count of distinct strains, donors, clinical backgrounds, independent lineages or research tasks. No FASTQ, package, PDF, genome, MIC/fitness measurement, author contact, publisher fetch or architecture. Raw response/failure bytes and receipt/status/hash/headers/UTC under `amendment2_sources/`; scripts under research with auditor_manifest_amendment2 prefix. Stop after this dependent sequence even on failure.
