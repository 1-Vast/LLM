# Corrected coordinate-key identity check

This addendum retains the original identity-only scope and source. No read-count, PSI, response, exon/intron-count, score, or historical-response field may be used. Preserve the first script and output.

The first literal-key comparisons omitted the library-ID prefix and the absent-intron convention. Their zero matches therefore do not show an identity conflict. Test the explicit convention suggested by the displayed identifiers: library ID followed by each ordered junction pair, omitting a pair exactly equal to (0, 0). Do not infer offsets or tune conventions from responses. Record comparisons against both exported `_o` coordinates and corrected MaxEnt coordinates, including any unresolved examples. The corrected test neither authenticates `_o` as raw junctions nor proves preservation of counts before aggregation.

This is a correction to a source-identity check, not the conditional scientific comparison matrix or its implementation repair. All first-pass outputs remain available.
