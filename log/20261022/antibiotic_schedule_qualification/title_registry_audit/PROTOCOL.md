# Preregistered antibiotic-schedule title/author registry audit

2026-10-22, Asia/Shanghai; registered before the new requests. Read the existing antibiotic qualification and exact-DOI registry reports. Their finite zero results do not establish that public data are absent. This block uses the authenticated title and primary authors to search public metadata registries only; the separate advocate owns code/GitHub discovery.

At most four new requests, sequential single writer, no retries; <=2,000,000 combined consumed HTTP response-body bytes and initial <=15 minutes. Exact ordered objects:

1. Zenodo records search for title phrase `"Massively multiplexed microfluidics"`, size 10.
2. DataCite DOI metadata search `titles.title:"Massively multiplexed microfluidics"`, page size 10.
3. Figshare public articles search POST `search_for="Massively multiplexed microfluidics"`, page size 10.
4. Zenodo author/context search `(creators.name:"Jeong" OR creators.name:"Tay") AND (antibiotic OR microfluidics)`, size 10.

Official API endpoints only: `https://zenodo.org/api/records/`, `https://api.datacite.org/dois`, `https://api.figshare.com/v2/articles/search`. No publisher/fulltext retries, mirror/bypass, GitHub/code duplication, numerical table/image/raw data fetch or article author messaging. Metadata search bodies are saved unmodified with receipt/status/hash/UTC/byte counts before projection; refuse overwrites and preserve failures. A separate script exports only registry IDs, titles, author names, DOI/URL/related identifiers, published/version metadata, and public file name/size/type/link manifest metadata. It does not print descriptions, embedded numerical responses or full raw JSON. Source units/experimental observations are not inferred from filenames.

A candidate must demonstrate a direct paper DOI/explicit relatedIdentifier link or exact title plus authenticated author agreement with the supplied paper record; title similarity alone is not a verified data-paper link. Even an authenticated data record/file manifest does not certify drug/strain/order/dose/run/chamber/colony/time keys or a complete measured schedule menu. If no direct linked manifest is authenticated after these four requests, conclude only that these exact title/author metadata searches did not establish the source, then stop this source block. No architecture or numerical opening follows automatically.

All new scripts use `auditor_title` prefix under `research/antibiotic_schedule_qualification_20261022/`. All this block's protocol, raw metadata, receipt, tests, hashes, finite decision and failures remain under this `title_registry_audit/` log directory. Runtime `D:/anaconda/envs/maestro/python.exe`.
