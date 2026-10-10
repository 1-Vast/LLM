# Official pseudobulk method review

The receipt in `FETCH_RECEIPTS.json` records **33,289 successful response-body bytes** for six source files from the pinned official repository commit `4f4123d9e1ac6a02e2447935ba47b04fc2f061f8`. All requested files are source code or documentation. No RNA, model weights or independent outcomes were requested.

`pseudobulk_correlation.py` performs the following operations:

1. Read original plate6 and plate14 H5AD files separately for a cell line; retain `pass_filter == full`.
2. Run Scanpy `normalize_total`, then `log1p`, separately on each cell-line/plate subset. Intersect named genes between plates. Select 2,000 Seurat HVGs on plate6 and apply those names to both plates.
3. Require at least 50 DMSO cells on each plate and compute each plate's reference mean over **all** its DMSO cells. Hold these vectors fixed for the cell-depth sweep.
4. For every shared exact drug-dose label, sample N treated cells without replacement on each plate for N = 25, 50, 100, 200, 400, 800 and 1,600 when supported by both sources. Repeat sampling ten times.
5. Calculate `mean(log-normalized drug cells) - mean(log-normalized DMSO cells)` and Pearson correlation of the two signature vectors across genes. Record Monte Carlo mean/standard deviation and treated/control counts.

The script calls the mean difference an LFC, but it is a difference of mean log-normalized expression, not automatically a log ratio of mean raw counts. Scanpy's default `normalize_total` target is determined by the input subset when a target is not specified; separate plate subsets can therefore imply different scaling unless the version/default behavior is recorded. This preprocessing must not be silently imposed on the existing filtered X, whose transformation is already specified.

The comment “control-arm noise removed by fixing DMSO” describes a conditional computational experiment: control sampling variation is not resampled during the sweep. The control mean still has uncertainty and its shared error affects every condition using it. Reference noise is not proven zero and cannot be counted as independently sampled for each candidate.

The code comments that raw pseudobulk correlation is dominated by cell-line baseline expression. Its remedy—compare perturbation-minus-control signatures—is directly relevant as a strong P0.6 baseline. The quoted numerical correlation in source comments is an upstream statement, not a MAESTRO measurement.

A bounded adaptation for the proposed 32-cell sentinels can use fixed matched source references and N = 8/16/32, with the same declared gene panel and transformation in both sources. It must be called an adaptation, not a full reproduction of the original N/HVG protocol. Ten resamples estimate Monte Carlo cell-subset behavior within two source observations, not ten independent cultures. Inference units must retain pooled sample and plate identity across cell lines.

`docs/METHODS_metrics.md` additionally documents compositional cell shares, cell-cycle redistribution and other RNA-derived metrics. Source prose sometimes labels a loss of compositional share as killing, but captured cell-line proportions also reflect preparation, sampling, composition and growth. MAESTRO should retain the actual compositional/derived measurement definition and cannot relabel these as an independently measured viability or apoptosis assay.

Reusable code is the explicit sample count grid, exact condition intersection, fixed reference, complete-vector sampling, deterministic seed and output counts. The entire script requires original full plate files and a heavyweight Scanpy pipeline; copying it unchanged would violate the cheap bounded pilot objective. Reuse the method with declared adaptations and retain the source receipt.
