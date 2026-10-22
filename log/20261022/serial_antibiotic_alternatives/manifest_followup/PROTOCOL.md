# Tripartite official manifest-entry follow-up

2026-10-22, registered before either new request. Existing paper identity is *Tripartite Loops Reverse Antibiotic Resistance*, PMID40478208 / PMC12164588 / DOI10.1093/molbev/msaf115. Existing Data Availability names SRA BioProject PRJNA1254677 for genomic data; this does not certify phenotype tables or every lineage-prefix genome.

At most two official sequential GET requests, combined consumed body <=500,000 bytes, no retry/substitute:

1. `https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC12164588`, for OA downloadable package links/format/license/update metadata only.
2. Entrez BioSample esearch with exact term `PRJNA1254677[BioProject]`, retmax=0, retmode=json. Return count/query translation/warnings only; no BioSample identities, genome, SRA run or MIC data fetch.

Save unmodified source/failure bytes and receipt status/URL/headers/hash/UTC, single writer, reject overwrites, freeze protocol/script/retained article bytes before requests. If the BioProject search field is invalid or returns zero, report its literal scope; do not equate with no BioSamples. Metadata count is not clinical background/lineage/task count.

Offline, only the already retained `../TRIPARTITE.xml` may be parsed for supplementary-material/media href/type/title metadata and article source identity/license. Do not open supplementary PDF/package, figures, results tables, numerical measurements or raw genomes; do not infer supplement content from PDF existence. Goal is a precise official manifest入口, not numerical evidence or architecture approval. No PDF skill, publisher retry or author contact.

All code in `research/serial_antibiotic_alternatives_20261022/` with `auditor_manifest` prefix; all new protocol, bytes, receipt, safe projection, verification and report in this `manifest_followup/` directory. Runtime maestro. Stop after these finite requests and report whether exact official source entries permit a separately registered identity/schema qualification.
