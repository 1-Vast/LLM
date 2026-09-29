# Conditional population flow: development pilot

Written before this pilot's extraction, fits and scores. Existing SciPlex3 data
were exposed in earlier research; this is not external or preregistered confirmation.

Use actual single-cell RNA, not pseudobulk chunks or ensemble members. Restrict
to A549, 24 h, 1000 nM. Eligible drug/replicate/plate populations have >=64 cells
and >=64 vehicle cells on the same plate and replicate. Select 24 distinct
InChIKey connectivity groups by SHA256 ordering of `population-pilot|group`;
choose one compound per group lexicographically. First 16 groups train, next 4
validate, last 4 test. These are connectivity splits, not Murcko scaffolds.
Retain at most two lexicographically ordered replicate/plate populations per drug.
Sample 64 cells per population with seed 20260927; controls may be shared across
drug populations on the same plate. No independence claim for shared controls.

Use the previously audited +offset gene identity and frozen 2473-gene universe;
that historical universe used controls from all contexts, so this is a reused
feature universe, not a fully untouched preprocessing evaluation. Normalize
using total human counts per cell, log1p(CP10K). Rank 128 genes by variance in
unique training control cells only; PCA(16) fit on those controls only. No target
outcome enters coordinate learning. No latent-to-RNA biological claim is made.

Condition: Morgan-128 radius 2 plus log1p(dose)/log1p(10000). Control-set mean and
standard deviation condition the field. Equal-condition minibatch OT with 32
cells, MLP 64/64, AdamW 1e-3, 80 epochs, seed 0. Select epoch on validation MMD;
do not change hyperparameters after test scoring. Flow time 0..1 is not hours.
The vehicle boundary is exact; biological dose effects are not forced monotone.

Compare on identical controls/targets: unchanged vehicle, mean training shift,
chemical nearest-neighbour training shift, and conditional flow. Baseline shifts
preserve control population shape; nearest neighbour averages ties. Gaussian
MMD bandwidth is median nonzero pairwise distance among training controls.
Report per-condition and equal-drug MMD², mean error and variance error in frozen
PCA coordinates. Only four test groups: no significance or calibration claims.
Prediction-research screen passes only if flow mean MMD is below all baselines;
even then production promotion and agent decision utility remain untested.

Write row IDs, selected genes, PCA transform, chemical groups, checkpoint,
history, predictions, file hashes and metrics. RNA heterogeneity is not target
engagement, viability, lineage, cell-count dynamics or causal mechanism evidence.
