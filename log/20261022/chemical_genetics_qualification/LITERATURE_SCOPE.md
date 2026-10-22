# Narrative literature scope

2026-10-22. Before the offline projection below, root authorizes reading the
already acquired primary article's abstract, narrative Results/Discussion and
figure captions. This is necessary to assess what the original authors already
contributed and which source tables represent longitudinal experiments. It is
literature/design exposure, including any published numbers and qualitative
outcomes in those paragraphs. It is not a sealed evaluation and does not count
as our experimental evidence. No response-table arrays, supplementary workbook
measurements, FASTQ or external services are opened by this step.

`research/chemical_genetics_qualification_20261022/narrative_literature.py`
projects these fields from the retained `sources/PAPER.xml`, recording its
SHA256. All top-level body section headings are inventoried; only sections
explicitly titled Results or Discussion are projected. Nested paragraph text
is included once. Figure captions are deliberate source-design exposure, not
tabular response parsing. Success means the retained projection identifies the
author's existing mechanism and the relevant source-data figure; failure means
retain the exception and correct the local parser without any network request.
