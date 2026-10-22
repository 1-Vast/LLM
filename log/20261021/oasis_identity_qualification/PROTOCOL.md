# OASIS identity and CellPainting pairing qualification

Frozen before this block's reads/retrieval, 2026-10-21 15:02:50 UTC. New block only; the prior source qualification and its frozen files remain unchanged. Limit: **20 minutes / 20,000,000 new HTTP response-body bytes**, one network writer, no fitting/API/GPU. All new code is in `research/oasis_identity_qualification_20261021/`; all records, downloads and outputs are in this log package.

## Scope and permitted data flow

Existing exposure: published aggregate claims and the prior blind schema/identifier/coverage/null-count outputs. Functional values and CellPainting feature values remain unavailable to optimisation. Chemical groups and independent reserve have not yet been constructed.

1. An independent Python process may read only explicitly white-listed identity/chemical columns from the 68 existing sealed biochemical files: source/plate/well/well_id, compound name/code/OASIS_ID, concentration, chemical structure/formula/salt fields, library/plate_type. No functional column is loaded. Source hashes must match the prior manifest.
2. Explain 160 duplicate source/plate/well records and 72 actions with more than two records by identity fields, physical well keys and file lineage. Do not compare or select on functional values, and do not assume distinct records are independent measurements.
3. Public metadata/index files may be downloaded to this block's `sealed_source/`. They are potentially contaminated with outcomes/features, so only a separate process with a column whitelist may read them. Schema output is permitted. Exact chemical identifiers and image URLs are allowed metadata, not selected candidates.
4. CellPainting feature/image payloads may not be downloaded or decoded. Prefer a small official index and metadata file, with publisher code/schema and version lineage. A profile CSV may be streamed only if its complete compressed payload fits the remaining budget, and its parser may retain only explicit header-approved ID columns. Directory-level existence is not exact well pairing.

## Qualification rules

GO to a chemical-group split protocol only if chemical identities can be traced without functional filtering, duplicate records receive a deterministic identity-only disposition, and the retained functional actions have authenticated matching CellPainting well/compound/dose keys. Report exclusions/unknowns without guessing, including source/version mismatches and missing plates. Any restricted subset is defined solely by identity and availability before numerical optimisation; no completeness inference from 1085 labels or 67 directory matches.

BLOCKED means this data qualification has a concrete missing identity/linkage prerequisite; it does not update any thread/goal status. If the complete intended unit cannot be authenticated within this block, stop with a partial census and exact missing requirements. No target outcomes, data split or benchmark score may be changed to make qualification pass.

## Sources and preservation

Raw S3 cpg0037-oasis data: CC0 1.0 (prior official Gallery receipt). Prepared Zenodo record 17067683: 2025-09-06, website v1/API version null, CC BY4.0. Preparation repository pinned to commit `ca4872de0f1f0a4f203bee41271a6512b314a076`. Every new object retains URL/version/ETag/hash/size and receipt. Source snapshots are preserved; no old file is overwritten, moved or deleted.

Isolation is an independent process plus whitelisted data flow, **not** an OS sandbox or encrypted vault. Newly downloaded mixed-content sources remain sealed by access convention. One acquisition process serialises all requests and commits the ledger after every request; no parallel network ledger writes. Seeds are inapplicable because there is no stochastic experiment.
