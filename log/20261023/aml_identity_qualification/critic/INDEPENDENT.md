# Independent chemistry and namespace audit

Scope: metadata and official text only. No matrices, lineage records, new labels, fitting, foreign-code execution, or peer reports inspected. Two new HTTP requests acquired the cited SingleCellLineage tree and README. Parent subsequently reported a 31-character field; this report does not inspect that record or infer its actual contents.

## Positive evidence

GEO SOFT source SHA256 verified against the old receipt: 8545602f3dd82e41836e7a8e34d7a8cbb82e6a5c715d3321eb68b4f15174e9c3. SAMPLE_METADATA.json retains only sample metadata with original line numbers (481 metadata lines). GSM8791699/1700 identify multiplexed HL60/TF1/OCI-AML3 baseline sample3; GSM8791701/1702 identify multiplexed HL60/TF1 post-treatment sample4. GSM8791698 explicitly associates FLARE with sample2 AND sample3 despite mouse-oriented source fields; it cannot be excluded solely by those source fields.

Pinned AML preprocessing line43 merges cellBC onto FB_bc and line48 retains both GEX_bc and FB_bc. Utilities extract cellBC from R1[0:16], UMI from R1[16:28]. These operations are exact source evidence of an expected external mapping, not evidence that a particular mapping table is available or nonidentity.

New official SingleCellLineage tree is pinned at 0efc48dd02994029ec5fd6f56d6197fab9aea704; full nontruncated tree and README bodies/HTTP receipts retained. README line166 distinguishes combined barcode/UMI read from sequence read and requires correct FASTQ slot orientation. Lines184-187 give a readName whose second underscore field ends in FWD, explicitly interpreting its FIRST16 bases as 10X barcode and NEXT12 as UMI. Thus a rule requiring that entire field be DNA or exactly28 characters is scientifically unsupported. A technical suffix is compatible with the cited pipeline; it does not itself imply chemistry mismatch. This is a simulated example and does not authenticate the AML pipeline version, full grammar, or actual data.

## Three distinct identity questions

1. Chemistry representation: does an extracted FB16 barcode map to the same or a different GEX16? Need the experimentally applicable kit/chemistry, whitelist and explicit FB_bc→GEX_bc table or exact authenticated rule. A generic translation table and maximal overlap after trying alternatives are insufficient provenance. GEO metadata says only 10X 3-prime and CellRanger count or multi; exact kit/version and table are not authenticated here.
2. Suffix: a GEX identifier may contain a suffix/GEM-group token. Removing a verified representation suffix is different from translating FB16 to GEX16. The readName FWD suffix is also a different suffix, attached to combined barcode/UMI. Neither is a biological sample label.
3. Namespace: physical identity must retain the library/GEM context plus barcode. Sample2/sample3 sharing a FLARE accession is not proof of one GEM partition. Barcode16 alone is not a globally unique cell key. Human line and flask/time/treatment need a declared MULTIseq feature-to-culture manifest and demultiplex calls; human species cannot separate three human lines.

## Minimal falsifiable next check (proposal, not executed)

Freeze source-backed barcode/UMI extraction grammar, orientation and allowed suffixes before looking at records; initially use a bounded tiny grammar-only probe with no lineage tags or expression. Separately pin a same-library identity manifest and justified chemistry mapping. Then audit barcode cardinalities, duplicate/many-to-one mappings, namespace collisions, GEX-set membership and unmatched identities for each declared library independently. Require deterministic identities; ambiguous/unmapped cases remain unresolved, never silently forced by nearest sequence, endpoint prevalence, or assumed identity translation. Membership alone cannot distinguish a coincidental collision from a correct assignment.

The exact permissible mismatch/coverage criterion must be declared from assay requirements before endpoint inspection; do not tune thresholds to observed lineage survival. Record-level grammar validation cannot establish translation or culture identity. No endpoint clustering, abundance, functional labels or post-treatment expression may define baseline groups or choose a translation rule.

## Verdict and stop conditions

Continue source qualification, not model training. Concrete useful progress is a source-backed parser convention and explicit sample associations. Still missing: authenticated FB/GEX mapping or identity rule, experimental pipeline/chemistry version, FLARE library/GEM routing, and MULTIseq feature-to-line/flask/time manifest. If these cannot be authenticated or unique baseline eligibility cannot be established, stop this particular baseline-to-fate task rather than call absence extinction. This is a scoped dataset-qualification stop, not a global impossibility claim or algorithm novelty judgment. No world-model, inheritance or RSI benefit is demonstrated by this audit.
