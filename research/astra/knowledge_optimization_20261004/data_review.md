# Independent data and retrieval review

Date: 2026-10-04. Scope: the imported, exposed `knowledge_transfer_20261004` package and `research/REPORT_ZH.md`. This review does not modify frozen inputs, run new biological comparisons, access Vis outcomes, call a provider API, or update production code. Commands ran in the existing `maestro` environment. Findings distinguish byte identity, engineering behavior, and biological applicability.

## Verified evidence

- All **82** entries in the imported `RUN_MANIFEST.json` match their local SHA-256 values.
- The three experiment freezes contain **20, 38, and 43** entries. Each has exactly one raw-byte mismatch: the external `research/astra/confirmation_campaign_20261004/protocol/partition.json`. Its current CRLF hash is `19b82c5a8059cc12e59448aaa129e575d4365ba5f873f0375f6792d523203e16`; the recorded LF hash is `576d3e767254d6834239ccd0bccb5ad91315bc3d86b6dc57a658ec0e6fbd62e6`. In-memory CRLF-to-LF normalization reproduces the recorded hash exactly. No original hash was rewritten. Raw-byte freeze checks therefore do not pass as written in this checkout; this is a line-ending transport difference, not evidence of changed partition membership.
- Both SQLite databases opened through `Path.resolve().as_uri() + '?mode=ro'` and returned `PRAGMA integrity_check = ok`. The assembled database's hash agrees with its manifest.
- Independently reconstructed **49,424** campaign records: graph 21,130; context 15,918; interaction 12,376. History membership, target exclusion, partition membership, measurement accounting, verification eligibility and every reported selected-arm total match. This was an in-memory reimplementation, because the original `verify_receipts.main()` writes an existing receipt and its byte-strict freeze check fails on the partition newline difference.
- The original **14 synthetic checks pass**, independently rerun with bytecode writes disabled. They establish the tested engineering invariants, not scientific value.
- Six pinned footprint-source hashes match. The two subsets contain exactly the partition's **125 unique SIDM IDs**, with **14 pathway** and **771 TF** coordinates; no duplicate coordinates, missing values, or nonfinite values. CSV subset versus upstream matrix differences are at most `8.88e-16`; database versus subset values match exactly.
- Assembled counts agree: 45,187 HGNC entries; 65 drugs; 124 target annotations; 150,705 network claims; 98,125 context scores; 18 ChEMBL identities; 21 mechanisms; 12 target entities. All 124 action signs are null; all 18 benchmark-structure-verification fields are null; all 21 mechanisms have `used_in_models = 0`. Network tissue/cell/dose/time fields are all null. The SQLite schema contains no benchmark outcome or monetary-cost table.

The 45,187 HGNC records are gene entries, not necessarily 45,187 protein-coding intervention targets. The 150,705 claims are source annotations, not independent experiments. The context values are ULM-derived RNA scores, not measured protein activity or authenticated contemporaneous cellular state.

## Successor corrections worth making

### 1. Preserve typed relations before deciding sign conflict

`query_knowledge.py` rejects any usable edge when another usable row for the same source and target has the opposite sign, without conditioning on dataset or relation type. There are **63** affected gene pairs, all across datasets; there are **zero** opposite-sign pairs within either dataset under that flag. Examples: AR -> CASP2 is OmniPath -1 and CollecTRI +1; AR -> ESR1 is OmniPath +1 and CollecTRI -1.

The experiment intentionally treats protein influence and transcription regulation as separate feature blocks. Opposite signs across these layers are not automatically contradictory measurements of the same quantity. A successor retrieval implementation should return both typed claims and their sources. Resolve or flag conflicts only within the same relation/measurement semantics and applicable conditions; unknown conditions remain unknown. Dataset can be an initial proxy for the existing two layers, but should not be advertised as a complete biological relation ontology. Do not change the frozen model or claim that revised retrieval retrospectively improved its results.

### 2. Make retrieval use the declared database

The original path query always opens `knowledge/knowledge.sqlite`, so it cannot retrieve the assembled context scores or post-evaluation ChEMBL annotations despite the delivered assembled database. A small successor CLI can accept an explicit database and expose paths, context and drug annotations. It needs no registry or second store. Open with a properly encoded absolute URI in read-only mode, enable query-only behavior, validate identifiers/hops/limits, and deterministically bound result counts. Return whether a record exists separately from whether its applicability is authenticated.

### 3. Preserve exact identities and unresolved knowledge

SIDM joins are exact and validated. ChEMBL joins are unique normalized preferred-name/synonym matches only: they do not authenticate salt, structure, stereochemistry, experimental vial or lot. Preserve `benchmark_structure_verified = null`; do not infer identity certainty from one name hit. Three identities have no retrieved mechanism; this means missing annotation, not no biological mechanism. Two nucleic-acid entities, one protein complex, two complex groups and seven single proteins remain distinct. `direct_interaction_curated` describes the provider assertion, not target engagement in the benchmark cell.

### 4. Upgrade reproducibility without replacing history

All six assets named by `download_manifest.json` are absent from the imported package's `assets/` directory: Jaaks CSV/metadata, HGNC, OmniPath, CollecTRI and resource metadata. Therefore the retained SQLite/kernel and existing replay receipts are verifiable, but rebuilding the original network from raw inputs is currently blocked. Mutable URLs with unspecified expected hashes in `acquire.py` are not an exact recovery contract. A successor restoration command should use the recorded hash, refuse mismatching content, preserve failed receipts, and distinguish a fresh source snapshot from restoration. The frozen experiment must continue to reference its original snapshot.

ChEMBL request receipts preserve URL, byte count and raw-response hash, but do not preserve each original response as raw bytes, per-request retrieval time or an explicit ChEMBL release/version. The nested JSON and bundle hash authenticate the retained assertions, not independently reconstructible exact HTTP response bytes. Future retrieval should save a small response receipt with release, timestamp, response digest and local raw-response path. Footprint generation also depends on upstream RNA, coding-gene selection, regulons/PROGENy networks and decoupleR version, which are not all included in the six pinned files. Current guarantees concern the pinned score snapshot, not independent recomputation of ULM.

The assembled database records untreated RNA context but lacks sample-collection/readability timestamps and experimental batch linkage. It is legitimate retrospective background information. It is not certified decision-before-treatment state in the Jaaks physical campaign. Source age or a public release timestamp cannot establish that historical availability.

### 5. Avoid destructive reruns during cleanup

Original `build_knowledge.main()` deletes an existing database; `assemble_knowledge.main()` copies over its target; acquisition and receipt verification overwrite output manifests. Preserve these as frozen historical scripts. Successor commands should require a new output directory or refuse existing destinations. A read-only validation command must not overwrite `receipt_verification.json`. Unknown assay prices, elapsed acquisition effort, original QC failures and physical plate feasibility must remain unknown; free public retrieval does not make state measurement or deployment free.

## Minimal retrieval contract

Return a compact structured record with: typed entity/relation and original IDs; source dataset and release/hash; evidence kind; original citation/source-record pointer; direction/sign or null; requested and recorded conditions; applicability status (`matched`, `mismatched`, `unknown`); derived-versus-measured flag; identity-verification level; conflict annotations; and permitted use (`context` or `planning_prior`). Public annotation does not gain mechanism-elimination permission merely by retrieval.

For activity retrieval, return SIDM, feature, value, ULM method, feature snapshot/hash and unknown physical sampling chronology. For drug retrieval, return the original target annotation and typed ChEMBL mechanism/entity separately. For paths, retain constituent claims and their layer sequence; a composed sign is topology, not a measured drug response. Do not inflate confidence by counting databases that cite the same publication. Independent experiment support remains unknown until source-level measurements have been extracted.

## Validation commands and limits

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = 'src;.'
& D:/anaconda/envs/maestro/python.exe -m unittest `
  research.astra.knowledge_transfer_20261004.check_invariants `
  research.astra.knowledge_transfer_20261004.context.check_context `
  research.astra.knowledge_transfer_20261004.interaction.check_interaction -v
```

Result: **14 passed, 0 failed**. The read-only SHA, database and receipt checks above were run as inline Python, with no output-file writes. New hypothesis training, HTTP restoration, ULM recomputation, original network rebuild, full repository tests, and new wet experiments were not run in this review. Existing scientific results remain exploratory and unchanged.
