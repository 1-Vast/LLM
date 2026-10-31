# Independent local control-only audit

2026-10-31. All six selected archives pass cloud-MD5, size, member-identity and advertised input-origin crosswalk checks. This is preparation before scientific admission; it is neither fitting nor a benefit claim. No new network access occurred.

## Access contract

`audit_controls.py` reads only the six original local tarballs selected in `root/selected_archives.json`. It uses a positional `csv.reader` filter to retain coordinate/GeneID identifiers, native IDs, control `IJC_SAMPLE_2`, `SJC_SAMPLE_2`, `IncLevel2`, and effective-form lengths. It never converts, stores in a selected row dictionary, or prints KD count/PSI columns, PValue, FDR or IncLevelDifference. Underlying CSV lines necessarily pass through the tokenizer in memory; no forbidden values are inspected. Native IDs are local and not used for cross-file matching. No treatment-selection rule or new scientific test was defined.

## Identity and orientation

All six compressed MD5 values equal the official `cloud_metadata.md5sum_base64` in `root/sources/encode_splicing_files.json`; sizes also match. Each archive has exactly the advertised members from `root/archive_headers.json`, with the target/batch/cell prefix matching its official alias. There are five `JunctionCountOnly` event tables per archive: SE, MXE, A3SS, A5SS and RI. No extraction or archive code execution occurred.

Official metadata advertises hg19 for all six and explicitly states Sample_1 is KD/KO and Sample_2 is control. Each archive's four `derived_from` BAM identities map through `root/sources/selected_input_bams.json` to exactly two BAMs from the stated perturbation dataset and two from its exact `possible_controls` dataset. Across the slice there are 24 distinct BAM identities and 24 advertised origin biosamples. Each control pair advertises biological replicate numbers 1 and 2. All three control vectors in every table have length two. **Vector slots are called slot 1 and slot 2 only:** neither the metadata list order nor those counts independently proves which slot corresponds to named biological replicate 1 or 2. Metadata lineage supports distinct biosample origins; it is not direct inspection of culture provenance or raw BAM read assignments.

Full event keys contain GeneID, chromosome, strand and every event-defining coordinate column, as recorded separately per event type in JSON. The SE key is GeneID/chr/strand/exonStart_0base/exonEnd/upstreamES/upstreamEE/downstreamES/downstreamEE. Across all 30 tables there are 448,068 rows, all positive finite effective lengths and no duplicate full keys within a table. Event counts are dependent observations, not independent perturbation tasks.

## Control eligibility and baseline reconstruction

Eligibility here is a descriptive control-only audit: both control slots have IJC+SJC >=20 and finite reported PSI within [0,1], with valid positive inclusion/skipping effective lengths. Interior counts additionally require both PSI slots in [0.01,0.99]; they are descriptive and not an admitted scientific analysis filter.

| Target | Cell | Archive | SE keys | GeneIDs | Eligible SE keys | Interior eligible |
|---|---|---|---:|---:|---:|---:|
| HNRNPC | HepG2 | ENCFF244XJW | 42,916 | 9,914 | 27,440 | 7,378 |
| HNRNPC | K562 | ENCFF312MYV | 50,432 | 9,948 | 33,413 | 9,061 |
| HNRNPK | HepG2 | ENCFF146LKU | 43,658 | 9,839 | 30,108 | 8,618 |
| HNRNPK | K562 | ENCFF757KYW | 44,277 | 9,190 | 31,497 | 9,694 |
| RBFOX2 | HepG2 | ENCFF602CHO | 32,823 | 8,939 | 20,155 | 5,349 |
| RBFOX2 | K562 | ENCFF128FXL | 34,518 | 8,841 | 20,771 | 6,527 |

| Target | Cross-cell full SE-key intersection | Eligible in both cells | Interior eligible in both |
|---|---:|---:|---:|
| HNRNPC | 20,935 | 12,561 | 3,169 |
| HNRNPK | 19,474 | 12,611 | 3,373 |
| RBFOX2 | 14,972 | 7,726 | 1,963 |

For each comparable control slot the independent reconstruction is:

`PSI = (IJC / IncFormLen) / ((IJC / IncFormLen) + (SJC / SkipFormLen))`.

All 872,774 comparable control slots agree within 0.0005000001 absolute error (three-decimal rounding plus floating-point tolerance); no mismatches occur. The maximum observed absolute error is approximately 0.0005. There are 23,362 zero-denominator slots and 23,362 rows with a missing/nonfinite reported control PSI; these are explicitly counted, not interpreted as PSI zero. No control/length parsing errors occurred. Formula agreement verifies internal baseline consistency, not biological truth or treatment-effect validity. Full counts for all event classes, form-length pair diversity, control-vector validity and missingness are in `control_audit.json`.

## Boundaries

No reference GTF annotations were used in this audit. Overlapping events, shared flanking exons, gene families and same-control/sample relationships still create dependence; the event intersection counts do not establish independent held units. There are only three RBPs and two cell lines in this acquired slice. This audit cannot establish unseen-RBP performance, causal binding-to-splicing mechanism, a new learning principle or novelty. eCLIP and KD remain cross-experiment associations, not matched cultures.

Prior-task exposure is unchanged: published aggregate altered-exon counts, significance descriptions and KATMAP validation summaries were read during source review, as disclosed in `../evidence_notes.md`. No per-event treatment effects or episode performance were inspected in either audit. Baseline/control values have now been accessed under this preparation authorization and must not be described as unseen.
