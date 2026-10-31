# Source-derived final serialization audit

Continue the original identity-only scope. Preserve v1 and v2 outputs. Do not use counts, PSI, exon/intron counts, scores or historical responses.

The separately identified official upstream implementation now supplies the actual serialization rule: `ce.detect_splicesites.py` lines194-198 sorts all present corrected coordinate values and joins positive values after `str(chr)+'_'`. Missing columns are absent at per-variant construction time and may become NaN on concatenation. Empty products retain the underscore. Apply precisely this source rule, including sorting; do not infer a rule by optimizing agreement. Compare only literal keys and coordinate identities. The observed ordering example22992 is not a different set of boundaries under this rule.

The same source lines216-218 and231-235 aggregate counts after correction and drop duplicate keys. Thus a successful exported-key check cannot establish that every contributing raw junction shared the representative `_o` tuple. Source code is statically inspected, not executed or repaired. Source version remains an official current implementation rather than an authenticated execution trace for the2025data run.
