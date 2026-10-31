# Bounded independent review of the frozen identity-only scan

2026-10-31. This follow-up preserves `challenge/initial_review.md` unchanged. Reviewed only the new scope, four-record identity syntax projection, exact scan source, scan freeze, and the previously inspected header audit. No coordinator scientific rebuttal or response outcome was supplied. The scan had not run when checked: `root/junction_identity_geometry.json` did not exist.

**Decision: allow the exact frozen metadata scan, with the narrow interpretation below. This does not admit numerical model analysis or revise v1.**

## Exact access and output

All five freeze entries matched their SHA-256 values on independent local verification: scope, syntax projection, script, header audit, and the 29,713,285-byte compressed source. Source verification read compressed bytes for hashing only; it did not decompress or expose response rows. The script itself was read, not executed.

The script's gzip line reader necessarily receives whole lines. Its `line.split("\t", 2)` returns the gene label, junction identifier and one opaque remainder containing the sample fields. Only the first two fields are stripped or parsed. The opaque third string is neither split further, converted, printed, selected on, summarized nor stored in the result. Checking that a third field exists tests row shape, not a numerical response. This is compatible with the frozen scope's explicit allowance that count bytes may pass through a line reader while remaining unprojected.

Header equality authenticates the column ordering used by that extraction. The header audit includes sample names but no response values. Numeric conversion is restricted to the two coordinates parsed from `Junction_id`. The counters describe records, identity parsing, gene-label multiplicity, strand/coordinate ordering and geometry. They are metadata counts, not sequencing read-count statistics. Elapsed time and the compressed-file hash do not deliberately expose any response values. No effect, PSI, coverage, baseline support or treatment-specific grouping is calculated.

The output contains no raw data lines, count tokens, response extrema or per-sample summaries. It writes one new root output JSON and prints that same metadata summary. The script refuses an existing output and checks the source hash and header. Execute the reviewed file normally with Python assertions enabled; the source/header/output checks are `assert` statements and are disabled by Python optimization. A run with `python -O` or `PYTHONOPTIMIZE` is outside this reviewed execution condition. This is an invocation condition, not a request to modify the script.

## Geometry validity and interpretation limits

The coordinate regular expression is a declared, conservative parser. For each unique parseable identifier it collects all exported gene labels. It excludes identifiers with multiple labels, missing labels or labels outside its simple-label syntax. It groups by gene, chromosome, strand and one coordinate, counting distinct alternatives at the other coordinate. Deduplicating the alternative coordinate with sets prevents duplicate rows alone from creating extra geometric alternatives. Reporting both first-coordinate and second-coordinate grouping, while separately reporting strand/order, avoids assuming which coordinate is the donor or acceptor. The four syntax examples are plus-strand examples; they establish the observed string shape only, not strand orientation or export-coordinate conventions.

Three caveats affect interpretation, not count access:

1. `unambiguous_junction_ids` means a parseable identifier having one simple exported gene label. It does not authenticate genomic uniqueness, gene annotation correctness, or a unique biological transcript. A simple gene label can still be wrong or incomplete. Likewise `unique_parsed_junction_ids` counts identifier strings, rather than proving a unique biological junction universe. These labels must be explained as export-level categories.
2. The positive-coordinate/distinct-endpoint check defines the admitted geometry. Until the coordinate convention is authenticated, the counter named `invalid_coordinate_identity` means rejected by this parser. In particular, zero is not universally invalid under every possible genomic coordinate convention. A nonzero rejection count would be an uncertainty to report, not proof of malformed biology. The aggregate tally is consequently restricted to this parser and its positive-coordinate domain.
3. Common-anchor groups can overlap, contain splicing paths with different unobserved contexts, or reflect alternative transcript mixtures. Their number is not the number of independent biological events, samples, usable targets, or eligible experimental units. Unparsed and label-excluded identities can also make an observed group appear more complete than it is. No closure claim follows.

The script itself retains the main limitations: overlapping groups, unauthenticated donor/acceptor order, pooled treatment-informed discovery, and no claim about closure, support, read quality, missing branches or drug invariance. The scope also prohibits using this tally to choose the eligibility rule or training/holdout split. Those boundaries are sufficient for this exact narrow scan. The wording “possible common-acceptor or common-donor geometry” in the scope must remain a biological interpretation to authenticate later; the exact script correctly reports common first/second coordinates.

## Relation to initial objection T2

This is a defensible narrow follow-up. It can establish whether the acquired export contains observed multibranch shared-coordinate geometry under a fully specified identity parser. A positive result would remove one possible structural obstacle to constructing a local conditional junction-use estimand. An absent result could reflect the export/parser/filtering and would not refute the biological hypothesis.

It cannot qualify baseline support, source positivity, observation uncertainty, branch closure, the independent event universe, the eligibility intervention class, or the transport law. It therefore resolves only a graph-level subquestion of T2. It does not turn pooled sample-discovered junctions into an outcome-independent prospective event universe. No count-based support scan, numerical endpoint, model fit, learner comparison, treatment response classification or holdout selection is authorized by this decision.

## Measured use and remaining availability

This follow-up used local file reading and SHA-256 verification only: 0 HTTP attempts, 0 acquired bytes, 0 decompressed response rows accessed by the reviewer, 0 fits/simulations, and no execution or modification of the reviewed script. Only this review file was written. The initial review was preserved. Available for a bounded final report/source check; no new exploration was begun.
