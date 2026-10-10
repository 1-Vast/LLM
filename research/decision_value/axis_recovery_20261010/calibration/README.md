# Finite informative axis calibration, stage 1

The frozen index screen found insufficient support for the registered
two-discovery/one-holdout information requirement, **before any new CSR values or
X_hvg vectors were requested**. This is a physical-support failure in the fixed
panel, not a failure of the greedy allocator and not a global impossibility claim.

Seven public-summary-guided, metadata-qualified conditions provided 1,042
full-QC cells. Every actual cell/sample/plate/condition join was checked against
the pinned filtered source and official sample metadata. Sentinel labels and
their pooled sample IDs were excluded across all line partitions, and the old
250 noise rows remained protected.

| File | Eligible cells | Genes with fewer than three CSR-index occurrences |
|---|---:|---|
| c44.h5ad | 427 | CD38 (2), IL1A (2), PLCB2 (1), IFNB1 (1), TNF (1) |
| c45.h5ad | 615 | CD38 (1), DCN (1), HGF (2), PLCB2 (1), LUM (2), ERBB2 (1), IFNB1 (1), F2 (2), BGN (1), TNF (1) |

Index presence does not prove a nonzero value. It is an upper bound on the number
of available nonzero observations. With fewer than three occurrences in the
entire eligible panel, the registered 2/1 discovery/holdout requirement cannot
be met by any selection from that panel. No paired freeze, paired row manifest,
paired results or coordinate certificate was created. The source genes, all
2,000 HVG coordinates, checkpoint decoder and P0.6 sentinel gate were not released.

The first freeze preceded all new index reads. It contains the complete source
inputs, metadata evidence, QC rows, exact physical spans and stage code.
`METADATA_NETWORK.jsonl` and `METADATA_CACHE_REUSE.jsonl` are immutable prefixes;
active ledgers retain every subsequent request. `INDEX_RESULTS.json` preserves
the first-stage failure. The separate design verifier independently reconstructed
all metadata joins and CSR indices without importing producer logic, yielding
`PASS_INDEPENDENT_OFFLINE_RECONSTRUCTION`.

Known application-received bodies total **12,397,900 bytes**: 7,829,936 metadata
and 4,567,964 indices. There were no new CSR-value or HVG-body requests. The
metadata process was restarted to load a persistent HTTP session before the
scientific index freeze. `METADATA_READ_AMENDMENT.json` explicitly records that
its termination boundary was unknown and any in-flight partial transport bytes
were unmeasured; the byte claim is application-retained known bodies, not total
wire traffic. No retained source or old freeze was deleted.

Reproduction of the independent result is offline:

```text
python path/to/axis_recovery_20261010/design/calibration_verify.py
```

The verifier's existing receipt is write-once; use a fresh extracted copy without
that generated receipt to rerun it. All producer `--execute` paths require the
registered freezes and refuse overwriting results. This stage is calibration
development, not a biological decision experiment. A supplementary panel, if
used, must be recorded separately with its adaptive selection, additional byte
budget and new immutable freezes.
