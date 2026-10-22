# Failures and scope limits

- First DeepSeek call exhausted 12,000 completion tokens with no visible content; retained, no usable proposal, no retry in reasoning mode. A single direct-mode recovery yielded classical/defective proposals. Total usage retained; monetary cost unavailable, not zero.
- First source rg used a PowerShell-unexpanded wildcard path and returned an invalid-path error; corrected using rg -g DECISION.md. No source was changed.
- One inline Python command containing a complex regex failed with exit 1 and empty output; replaced by inspect_sources.py. No response data were involved.
- Initial broad arXiv biological query included unrelated generic perturbation papers; the targeted second query and all original results are retained.
- A broad SCHEMATIC/Fong search returned mostly unrelated authors; exact-title follow-up identified the source and 2025 correction. Full-text XML then returned HTTP500, retained as 151 bytes. No data schema inferred.
- TDAL analyzed version is v1 despite v2 metadata; CDGS analyzed version is v1 despite v3 search metadata. Dates are first submission/publication, not inferred from arXiv identifiers or journal issue year. CDGS v1 has an unresolved J sign/direction inconsistency noted in the initial position; no later-version claim is made.
- Full BATCHIE CSVs were not downloaded or checksummed. Streaming first-line reads retained only headers; underlying transport buffer byte counts were not measured. Advertised full MD5s remain registry claims.
- Actual raw API response file hashes differ from logical content hashes because Windows text output translated newlines. Preserve both and verify separately; do not overwrite the recorded receipt.
- No biological response rows/scalars, stopped numerical datasets or protected reserves were opened. No new fit, author contact, or provider-generated code execution occurred.
