# Exact Day identity census

Preregistered 2026-10-22 before any numerical cell value access in this block. Root explicitly authorizes only **MOESM9, Fig.5a!E2:E61** as numeric Day metadata, plus the existing approved B/C/D string projection. This finite block is intended to seal the date/lineage identity join, not to run any response/model/baseline/novelty experiment.

Use `D:/anaconda/envs/maestro/python.exe -B`. Code and synthetic tests are stored only in `research/chemical_genetics_qualification_20261022/`; protocols, freezes, source hashes, test artifacts, failures and census are stored only in this `log/20261022/chemical_genetics_qualification/numeric_identity/` directory. No HTTP/model API calls, workbook edits, recalculation, rendering or exports.

## Allowed reads and strict boundary

- The original MOESM9 file is `identity_followup/workbooks/41564_2024_1857_MOESM9_ESM.xlsx`; verify its hash against `identity_followup/EXTRACTION.json`.
- Read workbook/relationship XML solely to locate exact sheet `Fig.5a`. Stream that sheet's OOXML. Access a cell's value text **only if its exact coordinate belongs to E2:E61**. Other cells are skipped without retrieving/interpreting their value/formula text. No other worksheet is read. Reading the enclosing XML bytes is necessary to locate authorized cells; it is not a numerical projection of the other cells.
- Each allowed E cell must occur once, be numeric type with no formula and represent an integer date. Formula/cached, missing, duplicate, nonnumeric or unexpected identity cells cause failure, retained without expanding scope.
- Obtain B/C/D only from the already approved `identity_followup/STRING_IDENTITIES.json`, never re-open those source values. Parse `Tetracycline {lineage}/Azithromycin/{day}` from B and verify its C/D consistency.
- Compare each E value to the B-string day for the same row. Check exactly 60 rows and exact lineage/day product `{1..12} × {2,3,5,7,10}`, without duplicate or missing keys. Days are authorized identity metadata. F/G and all other numerical cell values remain unread/unexported.

## Sequence and success / failure

1. Freeze protocol/code/tests and existing workbook/string/extraction provenance before the census. Run meaningful synthetic tests before opening source numerical values: exact scope excludes F/G/outside cells, integer-date and formula guards, missing/duplicate E detection, mismatch and duplicate/missing identity keys, source bytes unchanged.
2. Run a single offline census. Retain `CENSUS.json` with source hashes, exact access scope, allowed Day values, row/string comparisons, product checks and unchanged-source checks. No response values/statistics are included.
3. On failure preserve typed failure and its coordinate/reason where safe; do not inspect other numbers or silently repair. On success rehash frozen files and original workbook and mark this exact identity block sealed. Sealing confirms date/lineage identities only; it is not a performance holdout, genomic-state certification or a claim that earlier published qualitative outcomes were unseen.

Prior broad strings and author Yes/No groupings remain DESIGN/SCHEMA-EXPOSED as documented in `identity_followup/EXPOSURE_CORRECTION.md`. Exact Day metadata is now explicitly exposed. Genomic state extraction and F-column target semantics remain outside this block.
