# Measured signature retrieval

Compares a measured transcriptional signature with a digest-bound library of measured SciPlex3
responses (A549, K562 and MCF7, 24 h) and reports which vendor-annotated compound classes it
resembles. The query is centered on the library's mean response at the same line and dose, so
the stress response most compounds share cannot decide the ranking. The best similarity is
compared with a gene-permutation null, and the procedure's recorded held-out agreement travels
with every answer.

Why it exists: in the 2026-09-26 agent probe (`log/20260926/README.md`), neither DeepSeek nor
Jev could name a compound's class from an anonymised signature (0.100 and 0.075 against a
frequency prior of 0.150), while this retrieval reached 0.500 on the same 40 held-out compounds.
Given its output as an evidence card, both models improved by 0.3 to 0.4 but did not exceed it.

The output is a `derived_analysis` of measurements. Resembling a class is not having its
mechanism, and the analysis can neither satisfy a measured premise nor eliminate a hypothesis.
The library is built by `research/biological_depth/build_library.py` into
`data/virtual_cell/sciplex3_signature_library/`; without it the tool refuses with
`signature_library_missing`.
