# Luna archive acquisition implementation plan

Status: implementation and synthetic checks only. No real archive GET or CEL extraction is authorized by this plan.

## Inputs independently checked

- `RNA_IDENTITY_MANIFEST.json`: 172 unique exact CEL basenames across 31 compounds; 144 source identities (48 each Middle, High, Control) and 28 development identities (14 Middle, 14 Control); one HG-U133_Plus_2 platform.
- `RNA_ARCHIVE_HEADS.json`: 31 official HTTPS archive URLs, all status 200 with `Content-Length`; lengths sum to 3,658,321,111 bytes. HEAD responses downloaded zero body bytes.
- Each manifest compound maps to one HEAD URL by exact archive basename and its allowlist equals the manifest's `expected_allowed_barcodes`. The archive is expected to include excluded members; full archive bytes are therefore an exposure/contact cost even though extraction is exact-whitelist only.

## Planned implementation

1. Add `rna_archive_acquire.py` under this phase's research directory. At startup it rechecks manifest and HEAD consistency and refuses acquisition unless an explicit freeze JSON authorizes it and pins the manifest SHA256. Serial archive GETs stream to write-once `.part` files, with bounded connect/read timeouts and no automatic retry. Per-attempt receipts record timestamps, HTTP status/headers, expected and actual body bytes, final URL, outcome, and SHA256 when complete. Existing completed archives are reused only after receipt length and SHA256 verification; ambiguous files are never overwritten. Failures and extra/short bytes remain recorded.
2. Extraction reads ZIP central directories, matches only the 172 exact `<BARCODE>.CEL` basenames, rejects unsafe paths and non-unique/missing matches, and extracts selected members flat with CRC/uncompressed-size checks. It never parses CEL headers or expression values. Low, development High, other times/doses, later compounds, and all non-whitelisted members are not extracted.
3. Add 3 synthetic tests using temporary ZIP/HTTP fixtures written only under this phase log directory: successful exact extraction with unrelated members left untouched; duplicate/missing/unsafe member rejection; download length mismatch retaining a failure receipt and partial bytes. No live URLs in tests.

## Run gate

Real GET/extraction remains disabled until the root supplies a freeze JSON. The implementation will require status `RNA_ACQUISITION_FROZEN_AND_AUTHORIZED` and matching `manifest_sha256`, plus an explicit CLI action. Suggested freeze fields: `status`, `manifest_sha256`, `authorized_archive_count` (31), and `expected_archive_bytes` (3658321111). The root's single-threaded ledger remains outside this script to avoid concurrent writes.

## Success criteria

- Manifest-to-HEAD mapping verifies exactly 172 identities and 31 archives with the recorded byte sum.
- Synthetic tests cover successful extraction, unsafe/ambiguous whitelist handling, and incomplete download accounting.
- No CEL payload is parsed, and no real archive GET occurs before the root freeze.

## Independent implementation hashes

- `research/tggates_rna_feedback_pilot_20261022/rna_archive_acquire.py`: `5c5adcf6f014925627429563f3ba993bcd67bb2cc6037e0d824bd93955124693`
- `research/tggates_rna_feedback_pilot_20261022/test_rna_archive_acquire.py`: `bc5509b8033f2d8e363c1670ea04635c6f92aa379413421cd63ced4c0b8b5b6d`
- This plan's SHA256 is recorded in `LUNA_ACQUISITION_PLAN.sha256` to avoid a self-referential hash.
