# Independent metadata qualification review

The independent result was saved and SHA256-frozen before reading the primary output. Its SHA256 is `83d4428db565b354833dceae64ec04a4eef6ad46d3b07e3f17b512da1e91ef35`. Executed independent source: `D:\CodexData\tmp\independent_metadata_20261029_905d\independent_scan.py`, SHA256 `4ec8b978ad5ad7881e1353ab93d2943caaf6a4bdc46d6cd0b75d05c826544ce3`. The primary script was never read or executed. After freezing, only `dictionary_overlap_result.json` was read for comparison (SHA256 `aa1ec18846fd6f6d4318764a09afba8ba2cde38be5c5dbbbd8a82c190c0bb110`).

## Independent findings

The fixed 20,355,833-byte source has expected SHA256 `0883b3ef6e440603094c43c74044e1d333fce61e92e3efa374ea3a54f0b50302` before and after the scan. One metadata pass processed 135,242 data rows. All eight whitelisted metadata columns exist; complete CSV lines were tokenized but only those eight indices were accessed. No response field values were accessed, interpreted, fitted, scored, or output. No network/API, installation, GPU, author code, sealed/confirmation material, or environment files were used.

Raw matched cell name: Jurkat (179 rows); HEK293 has no match under fixed normalization. Raw matched drug names: Dasatinib (760 rows), Crizotinib (737 rows), Dinaciclib (727 rows). There are three joint source rows and three unique joint metadata rows, each occurring once:

| Cell | Sanger ID | COSMIC ID | Drug | Drug ID | MIN_CONC raw | MAX_CONC raw |
|---|---|---|---|---|---|---|
| Jurkat | SIDM01016 | 998184 | Dasatinib | 1079 | 0.001001 | 2 |
| Jurkat | SIDM01016 | 998184 | Crizotinib | 1083 | 0.001001 | 10 |
| Jurkat | SIDM01016 | 998184 | Dinaciclib | 1180 | 0.001001 | 1 |

All rows report DATASET GDSC2. Names are casefolded and only ASCII spaces, hyphens and underscores removed for matching; raw metadata strings are preserved. No HEK293T or clone aliases were merged. The full fixed 2-cell by 3-drug cross-product was checked; Jurkat/Crizotinib is therefore included even though it is not one of the named literature pairings.

## Comparison after freeze

- source SHA256: AGREES
- source bytes: AGREES
- total data rows: AGREES
- accessed metadata columns: AGREES
- individual matched cell names: AGREES
- individual matched drug names: AGREES
- raw candidate metadata tuples: AGREES

No scientifically relevant mismatch was found among shared fields. The primary output does not provide per-name source counts or joint multiplicities, so those independently counted fields cannot be directly compared. Unit labels differ in wording only: independent `unknown` agrees with primary `not certified by this CSV; requires original contract`. Neither output establishes culture/clone/time/endpoint/intervention-error equivalence.

## Qualification and resource limits

This is a resource-overlap candidate at the name/metadata level only. Concentration units remain unknown because no formal original contract was inspected; raw numeric strings do not establish a physical same-dose intersection. These matches do not establish cultured biological equivalence, same-dose function/engagement pairing, molecular H, intervention bounds, a novel algorithm, agent benefit, or scientific PASS. HEK293 absence here does not imply absence in all public resources.

The completed scan measured CPU 0.390625 s, wall 0.413649 s, historical peak working set 21,876,736 bytes and peak pagefile usage 13,152,256 bytes over 74 samples. These measurements end immediately before final JSON serialization/write and exclude interpreter startup and this comparison/review. CPU60s, wall90s and sampled historical peak memory256MiB were checked cooperatively every 4096 rows and hash chunk; launcher additionally provided a 90 s external kill. There was no OS-hard CPU or memory cap, so a threshold overshoot could be detected rather than prevented. The independent JSON is 4,347 bytes; exclusive write and prewrite size check enforce its 2 MiB bound. The review plus JSON are also below 2 MiB.

One initial launch failed during the first source-hash chunk due to an omitted ctypes handle signature, before the CSV was opened or parsed and before any receipt existed. The signature was fixed; there was exactly one actual metadata scan. This initialization failure is not hidden as a successful first launch. No output receipt was overwritten or scan rerun after freeze.

Requested model/effort: Sol / medium. Effective settings and actual model usage are unknown absent telemetry; this review does not certify routing.
