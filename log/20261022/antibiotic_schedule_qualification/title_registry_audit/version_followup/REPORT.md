# Exact Zenodo version and availability follow-up

2026-10-22. **The LIST README's exact old DOI is authenticated, but the public image records do not claim to release the complete raw/analysed study data.** One separately preregistered GET to [Zenodo 18362221 metadata](https://zenodo.org/api/records/18362221) returned HTTP200, **6,692 bytes**, without truncation. No image, archive, presentation, thumbnail or IIIF payload was fetched; no retry occurred.

The official local copy of [Uchicago-TAY/LIST README](https://github.com/Uchicago-TAY/LIST/blob/Code/README.md), line 111, states: `Additional image data are available at DOI:10.5281/zenodo.18362221.` The exact API record has this DOI, Yoon Jeong as creator, title *Multiplex Microfluidics(TAY LAB)_All 512 Chamber Images*, and a description directly citing target paper `10.1101/2025.10.30.684665v1`. Its parent/concept is 18362220, the same concept as the independently discovered newer record 22118144. Thus README→old exact DOI→common concept→newer linked-paper record is cross-authenticated. This is source lineage, not equality of experimental data.

## Versions are different payload assets

| Metadata | Exact README record 18362221 | Observed newer record 22118144 |
|---|---|---|
| DOI | 10.5281/zenodo.18362221 | 10.5281/zenodo.22118144 |
| publication_date | 2026-01-24 | 2026-08-26 |
| created | 2026-01-30T00:45:23.561660+00:00 | 2026-08-26T23:22:35.521683+00:00 |
| updated | 2026-01-30T00:45:24.308929+00:00 | 2026-08-26T23:22:36.041910+00:00 |
| metadata.version | v1 | not supplied |
| listed files | 7 | 6 |
| listed total bytes | 8,282,569,524 | 7,496,048,562 |

Publication date is not silently equated with created/upload time. Both have record revision 4, which is registry metadata revision, not a certified experiment version. Newer metadata was projected offline from the already saved author-query response; no second follow-up request was needed.

The **old exact README record** lists:

| File | Listed bytes |
|---|---:|
| 512Chamber(A1 to P32)_3hours.tif | 322,913,137 |
| 512Chamber(A1 to P32).tif | 1,609,960,248 |
| 512Chamber(A1 to P32)_3hours(BeforeCROP) (512).zip | 1,653,685,221 |
| 512Chamber(A1 to P32) (512).zip | 564,947,489 |
| 128 Chamber (4x4 binning).pptx | 786,607,590 |
| 512Chamber(A1 to P32)_3hours (2).tif | 1,609,966,290 |
| 512 Chambers (2x2 binning).pptx | 1,734,489,549 |

The newer record instead lists six `1024Ch...` PNG/ZIP files recorded in the preceding report. **No filenames overlap across the two manifests.** Common concept and unchanged descriptive title therefore do not license substituting the newer record for the README's referenced 512-chamber asset. Old filenames suggest positions A1–P32 and a `3hours` label, but those are filename strings, not authenticated acquisition timestamps, timelapse indices, drug schedules or actual treatment-condition joins. Neither record's file manifest reveals internal ZIP/PPTX contents; no such contents were opened.

## Exact source-description availability evidence

After a separately saved offline semantic-scope amendment, a separate worker examined only both saved `metadata.description` strings. Their source explanation is identical (numeric tokens would be masked; none of the following availability prose contains measured values):

> The main data supporting the results in this study are available within the paper and its Supplementary Information. The raw and analysed datasets from the study are too large to be publicly shared, but they are available for research purposes from the corresponding author on reasonable request.

The paragraph also identifies the target preprint via its bioRxiv URL. **This is now an authenticated author availability statement that the full raw and analysed datasets are supplied on reasonable request.** It does not nullify the public additional image files or establish that every relevant processed table is absent from the paper/supplement. No author was contacted.

Neither description specifies an acquisition time, time-lapse sequence, strain, named antibiotic/dose/order/lag or a run→chamber→colony→time→response schema. The only URL in each description is the target paper; there is no further data/code URL in these particular paragraphs. Lack of a time-lapse literal is not proof that the underlying images are not time-lapse. Source descriptions do not explain the `3hours` filenames or resolve the new title 512 versus file label 1024 discrepancy.

**Finite decision:** authentic public source lineage and distinct version manifests are now established; actual schedule/state/function replay eligibility remains NOT_QUALIFIED. Do not download multi-GB image assets or interpret README A+B/A-B/B-A platform capabilities as measured complete branches. Root independently audits the small repository table/schema evidence; this subtask did not duplicate those reads. Any numerical opening or further exact file/schema qualification needs its own task-specific contract.

## Verification and accounting

The exact follow-up adds **one request / 6,692 bytes** beyond the completed four-request / 41,111-byte stage, for **five title/author/version metadata requests and 47,803 bytes total** across those two explicitly separate blocks. Raw response, receipt/status/headers/hash/UTC are preserved locally. Imported registry/citation helpers had five meaningful synthetic tests from the first block; two additional description-projection tests passed, including numeric-response sentinel masking and no false schedule certification.

`VERIFICATION.json` passed **19 checks**, including all six exact-follow-up pre-request hashes unchanged, raw response size/hash, README DOI, common concept, direct target DOI, old v1 label, file sums and disjoint manifests. `TIMESTAMP_COMPARISON.json` and `DESCRIPTION_SOURCE_EVIDENCE.json` separately pin their existing raw metadata hashes. Later semantic/verifier code is not described as frozen before the request. Verification proves provenance and metadata consistency, not measured biological responses, model performance or RSI.
