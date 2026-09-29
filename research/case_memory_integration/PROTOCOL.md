# Pre-analysis protocol: untouched-source evaluation of the evidence-grounded case memory

> **File summary**
> - **Path**: `research/case_memory_integration/PROTOCOL.md`
> - **Purpose**: the frozen pre-analysis protocol for evaluating the case-memory, directional-feature
>   and conditional-forecast pipeline on a source no MAESTRO session had opened before this task
>   (LINCS 2020 Level 5). Written and hashed before any signature value was read.
> - **Core points**:
>   - Split: held-out test units are InChIKey connectivity blocks absent from GSE92742 and GSE70138;
>     references are the remaining blocks of the same build. The independent unit is the block.
>   - The validator, feature arms, thresholds and gates are copied unchanged from the development
>     registrations (`research/protocol_v2/protocol.json`, `research/maestro_vc_v1/protocol.json`);
>     nothing is tuned on the external source.
>   - The unseen stratum is exploratory: the confirmatory population minimums of protocol v2 cannot
>     be met, so no confirmatory claim is permitted whatever the result.
> - **Interfaces / data**: freeze record `freeze_protocol.json`; data pack `data/processed/case_memory_integration/`;
>   results in `outputs/case_memory_integration/`.
> - **Depends on**: `research/protocol_v2/protocol.json` (thresholds), `data/external/lincs2020/provenance.json`.

- **Version**: external-case-memory-1
- **Written at**: 2026-09-29T14:35:00+08:00
- **Status**: registered before any LINCS 2020 signature value was read. Metadata exposure before this
  registration is exactly the column set declared in `data/external/lincs2020/provenance.json`
  (`columns_the_census_may_read`) plus the metadata-only counts recorded in
  `outputs/case_memory_integration/lincs2020_unseen_metadata.csv`; no signature value and no
  signature-quality column (`cc_q75`, `tas`, `is_hiq`, `qc_pass`, `median_recall_*`,
  `is_exemplar_sig`, `is_ncs_sig`, `is_null_sig`) has been read by any session.

## 1. Evaluation source

| Field | Value |
|---|---|
| Study | CMap LINCS 2020 beta build (clue.io build `LINCS2020`), compound treatment Level 5 |
| Source URL | `https://s3.amazonaws.com/macchiato.clue.io/builds/LINCS2020/level5/level5_beta_trt_cp_n720216x12328.gctx` |
| Metadata URLs | `https://s3.amazonaws.com/macchiato.clue.io/builds/LINCS2020/{siginfo,compoundinfo,geneinfo,cellinfo}_beta.txt` |
| Publication | Subramanian et al., Cell 2017 (platform); CMap 2020 expansion described in the LINCS symposium summary (NIH Common Fund) |
| Version | beta build, `Last-Modified: Wed, 16 Dec 2020 23:54:09 GMT` (HTTP header); siginfo `Tue, 07 Dec 2021` |
| License | not stated in the files; clue.io terms of use apply. Publicly released for research use; not redistributed by this repository (manifests and checksums only) |
| Metadata download date | 2026-09-27 (recorded in `data/external/lincs2020/provenance.json`) |
| Signature download date | 2026-09-29 (this task, after the metadata-only census) |
| Checksums | metadata SHA-256 in `data/external/lincs2020/provenance.json`; Level 5 SHA-256 recorded after download in `outputs/case_memory_integration/external_source_manifest.json` |
| Independent unit | InChIKey connectivity block (first 14 characters) |
| Study-level split | LINCS 2020 beta build against GSE92742 + GSE70138: a test unit is a block absent from both phase-I and phase-II `trt_cp` compound lists |
| Known limitations | beta build; MoA labels are curated annotations (proxy truth, not ground truth); inferred genes included; no replicate structure at Level 5; condition coverage sparse outside the core scope |

## 2. Population and split

- **Scope (frozen)**: `trt_cp` Level 5 signatures in cell lines A549, MCF7, PC3, VCAP at 24 h and
  10 µM — the same condition family as the development L1000 scope.
- **Pool rule (frozen)**: a mechanism class enters the pool when it has at least 12 reference blocks
  and at least 3 unseen blocks with a core-scope signature. Classes are the `moa` strings of
  `compoundinfo_beta.txt`, unedited. Metadata-only count at registration: 5 classes
  (Opioid receptor agonist, Opioid receptor antagonist, Angiotensin converting enzyme inhibitor,
  PARP inhibitor, JAK inhibitor), 26 unseen blocks, 67 reference blocks.
- **Split (frozen)**: test = unseen blocks (absent from GSE92742 and GSE70138 `trt_cp` block lists);
  reference = all other blocks in pool classes. Episodes are forced-choice contrasts: the test
  unit's annotated class against every other pool class, order seeded by `20260929`.
- **Leakage boundary**: pool definition, reference centroids, feature definitions, the validator and
  all thresholds use reference blocks and metadata only. Test-unit signatures are read once, at
  scoring time, by the frozen code. No test-unit signature, label-derived eligibility list or
  quality column may influence any fitting step.

## 3. Validator (frozen)

For test unit `u` of class `c` at condition `k` against decoy class `d`:

- `s(u, k)` is the Level 5 moderated z-score vector (12,328 genes).
- Class centroid `m(c, k)` is the mean signature over reference blocks of class `c` at `k`.
- Detection: `u` is `undetected` at `k` when `||s(u, k)||_2` is below the 5th percentile of
  reference-block signature norms at `k` (reference-side rule, no test quantity).
- Reading code: `unresolved` when `|cos(s, m(c)) - cos(s, m(d))| < 0.02`; otherwise `0` when
  `cos(s, m(c)) > cos(s, m(d))` (matches own class) and `1` when it does not (matches the decoy).
- A condition with no signature for `u` is `not_planned`; it is never offered, never charged and
  never scored.

## 4. Feature arms (frozen)

The directional-feature comparison required by the investigation, each arm a case memory built from
reference blocks only:

1. `scalar`: magnitude features only (signature norm), the development status quo.
2. `signed_direction`: signed gene-level changes (ranked up/down features), no pathway projection.
3. `pathway_direction`: Hallmark v2024.1 gene-set projection (signed standardised scores,
   landmark-gene subspace), no gene-level features.
4. `combined`: signed gene-level + pathway-direction features with context (cell line, time, dose).
5. `mechanism_prior_only`: retrieved-neighbourhood class prior, no state features.
6. `case_memory_only`: class-frequency memory (no structure, no state features).
7. `full`: combined features + mechanism prior + adaptation-aware reranking, the integrated system.
8. `oracle`: the clairvoyant upper bound (always reads the truth); reported for headroom only.

Similarity for retrieval arms 2-4 and 7 is cosine on the arm's feature vector; a floor of 0.0 is
applied so only positively similar references weigh in (frozen; no tuning).

## 5. Endpoints

- **Primary endpoint**: paired difference in forecast NLL of the validator reading, `full` minus
  `scalar`, over all (test unit, condition, contrast) items; 95% unit-cluster bootstrap interval,
  2,000 draws, seed 20260929 (the procedure of `research/external_validation/statistics.py`).
- **Secondary endpoints**:
  - Calibration: NLL, Brier score and ECE of the wrong-elimination forecast per arm; directional
    accuracy (fraction of detected readings matching the own class) per arm.
  - Discrimination: mean log probability ratio between hypothesis-conditional branches (nats).
  - Decision: correct / wrong / deferred terminal decisions of the belief planner per arm, and the
    paired correct-decision difference against the fixed expert order.
  - Cost: measurements per episode at price 0.02 (protocol v2 utility).
  - Abstention: licensed-delay precision and recall (a delay is licensed when the oracle could not
    decide correctly either).
  - Failure/negative ablation: NLL change when misleading and undetected readings are removed from
    the memory (re-run of the development ablation on the external source).

## 6. Gates and thresholds (reused unchanged from protocol v2)

| Quantity | Value |
|---|---|
| `mpie_correct` (practically meaningful correct-decision gain) | 0.02 |
| correct non-inferiority margin | 0.01 |
| wrong non-inferiority margin / wrong-risk cap | 0.005 / 0.05 |
| measurement non-inferiority margin | 0.10 per episode |
| headroom gate | oracle-minus-fixed correct >= 2 x mpie and lower 95% bound >= mpie |
| utility | correct +1, wrong -2, exhausted -2, deferred/undetermined 0, measurement price 0.02 |
| minimum forecast support (`min_reference_units`) | 6 (flag below, never fabricate) |
| stratum size for inference | 50 units |
| exploratory population minimum | 200 units (not met by the unseen stratum at core scope: 93 units; all statements are therefore stratum-level or descriptive) |

## 7. Missingness policy (frozen)

The six measurement states (`not_planned`, `planned_missing`, `qc_failed`, `undetected`,
`ambiguous`, `qualified`) are kept typed end to end. A missing or failed condition is never encoded
as a zero vector; a zero-filled state marks the feature arm invalid and fails the quality audit.

## 8. Claim boundaries (frozen)

- The unseen stratum supports stratum-level inference (93 >= 50 units) and exploratory statements
  only; no confirmatory claim and no default activation of the planner follows from any result here.
- Mechanism classes are curated MoA annotations: the proxy task is labelled as a proxy throughout.
- A negative or null result is reported with the same precision as a positive one.
- Production integration is limited to what passes the registered gates: data contracts, safe case
  storage, provenance, abstention, monitoring and research-mode retrieval stay behind
  `case_memory_enabled = false` unless the decision gate is met.
