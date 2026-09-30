# Round 2 publication artifacts

These files publish the verified 2026-09-30 audit. Frozen originals remain under
`outputs/identifiability_round2_20260930/`; the dated narrative is in
`log/20260930/README.md`.

Both full episode-level path attribution tables are losslessly gzip-compressed
and split into ordered 20 MiB parts. Concatenate each table's `.part000`,
`.part001`, etc., then decompress the resulting gzip file.
`publication_manifest.json` records each part's hash, the complete gzip hash,
and the original CSV hash checked after decompression. Other published artifacts
are byte-exact copies. The local `.gitattributes` disables newline conversion
so frozen hashes survive checkout. The unsplit staging gzip files are ignored.

The package includes task summaries, source discrepancies, freeze declarations,
reading-quality tables, STATE vectors and inference receipts, test receipts,
and provenance ledgers. Large per-query forecast banks, duplicate episode CSVs,
observation caches and H5AD predictions remain in the original output directory,
with their full hashes recorded. Those files are required for rechecking every
original forecast query; this subset does not host them in Git.

WorldV2 swaps were not run, no model was trained, and no production source was
changed. These exposed-data results remain descriptive. Reproduction entry
points are listed in `research/identifiability_audit/README.md`.
