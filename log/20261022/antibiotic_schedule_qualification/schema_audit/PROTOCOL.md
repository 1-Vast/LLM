# LIST tabular schema qualification, before payload access

2026-10-22. Root follow-up to the public, nontruncated GitHub tree. This is source
qualification, not a new mechanism or a performance experiment.

Fetch exactly two Git blobs already named in the authenticated tree:

- `4. Colony Tracking, Combination Index/Syngergy Calculation/growth_data.csv`,
  17,137 bytes, git SHA `4197e4588383cd2a2441704f758f2533a3abe6bf`.
- `3. Operational File for GUI/Supplementary File (Multiplexing control).xlsx`,
  2,029,932 bytes, git SHA `0dc02c1c85a7d10d6783a361d2ae41f91d9bb685`.

At most two requests, 3,000,000 retained decoded HTTP body bytes total; no retries
or redirects. Retain failed bodies and transport failures, verify decoded blob
length and git SHA before parsing. Do not open image or growth payloads in root
tool output. A worker may decode them to export **only** shape, sheet names,
first-row header strings and counts of blank/numeric/formula cells. Numeric
strings in headers are redacted; no data rows, response summaries, fitted values,
plots or growth/cost utility are exported. Unknown header strings are redacted.
Workbook headers after blank introductory rows are not guessed or promoted.

Success: identify whether the accessible table exposes an explicit time/treatment
schema, and whether the supplementary operational workbook is a treatment/GUI
map. Neither a GUI map nor example curves alone authenticates experiment/run
lineage, a complete schedule menu, or independent tasks. Keep any unqualified
dimensions unresolved. A source mismatch/access failure stops that request; the
other independent fixed blob may still be processed.

Meaningful verification: the export function must redact numeric strings and
unrecognised labels, preserve duplicate header positions, and never include a
data row. Save executable checks and result receipts in their required folders.
