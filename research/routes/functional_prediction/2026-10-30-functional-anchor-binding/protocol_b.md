# B: chemical/ORF relation prediction in two known contexts

Version1, before any CPJUMP1 phenotype values. Overall objective ACTIVE / NOT_ACHIEVED. This is a small countertest of conditional non-equivalence, not a new shared-space architecture or a reproduction of CellCLIP/UniPert. Independent protocol review must precede numerical access.

## Identifiable question and available information

Can an ordinary conditional predictor choose the same versus opposing orientation of a nominal target's measured ORF morphology more accurately for a completely held-out compound than fixed or context-pooled relations? The users are profiling teams selecting probes to mimic or oppose a measured genetic phenotype. The output is a morphology relation, not drug efficacy, sensitization, target engagement or knockout equivalence. The design target is an input hypothesis; target discovery is not tested.

Source admission is cpjump_source/admission_contract.md. Use only the frozen8 raw well-median plates: compound48h and ORF48h, parental A549 and U2OS, two plates per modality/cell. Equal elapsed time does not equal biological phase or perturbation mechanism. Independent culture/batch identities remain unverified. Positive-control-role chemical/ORF treatments are excluded from scored queries/reference targets. No image model, CRISPR96h, reimaging, published processed feature selection or new condition is used.

Freeze b_compound_split.tsv before values:260 source noncontrol chemical IDs,256 names,255 transitive alias/connectivity groups;5 folds47/56/56/52/49. All cells, plates and reagent aliases stay together. The target may be shared with training compounds. This is whole-compound grouped prediction, not scaffold-disjoint, unseen-target or unseen-cell transfer. The original ID remains the observation; group closure does not equate stereochemistry or stocks. Primary averaging is equal over source compound IDs and the two contexts; duplicated names are grouped for uncertainty but remain distinct measured queries.

Prediction-time inputs: Morgan radius2/1024-bit/chiral source-SMILES fingerprints;130 nominal design-target one-hot columns; cell identity; measured ORF reference catalog in BOTH cells; negative controls in all eight plates; source-fold chemical profiles. Query chemical profiles are evaluation truth only. Broader target_list is unused. The ORF/control measurements are additional costly information, not free transfer. All references/controls may define normalization because this assay-assisted workflow explicitly measures them at prediction time.

## Frozen response construction

Project row identities before decoding any feature cells. Decode only selected chemical trt rows, selected ORF trt rows for the130 matched targets, and negative controls. Skip positive controls and empty wells without numeric conversion. Pin original complete-file hashes before access. Keep an access receipt with admitted row/value counts, skipped identities and any failure. Opening containers is not secure blinding.

Use the5792 identical feature headers. On each of8 plates, calculate per-feature negative-control median and population median absolute deviation; scale by1.4826*MAD. Keep the intersection of features whose control values are all finite and scale>1e-12 on EVERY plate. This is fixed using reference controls only, never query activity. Stop if fewer than100 features survive. For every admitted treatment/control feature, standardize with its own plate controls, clip to[-10,10]. Any nonfinite treatment value on retained columns causes a terminal DATA_NONFINITE stop; no response-based row exclusion or imputation. This avoids inventing uncertain activity-based eligibility.

Within each cell, sort two chemical plates and two ORF plates lexically, and pair their first/second positions. For each target gene and ORF plate, take the componentwise median of its two treatment wells after normalization. Each compound has one chemical well per plate. For each paired plate position, r is cosine(chemical effect, matched target ORF effect); zero vector norm yields r=0. The outcome is mean(r_first,r_second), with both replicate scores saved. Cosine is a feature-dependent geometric assay summary; it is not a causal relation or a calibrated three-class mechanism. No phenotype representation/PCA is learned from queries.

The primary action a=sign(predicted r), with exact0 permitting abstention. Utility=a*r; oracle utility=abs(r), regret=abs(r)-a*r. Weak measured relations automatically contribute less; no favorable activity subset replaces the primary population. Save MSE and replicate agreement descriptively. The two plate positions are not certified biological replicates or external validation.

## Fixed ordinary panel

All source-only fitted models use source groups and predict both contexts for query groups. Standardize inputs with source mean/population SD, zero SD=>1. Ridge includes intercept, alpha100. RBF kernel uses centered train/query kernels, intercept, alpha1 and gamma=1/(number of source-varying standardized columns), fallback1. Outputs clip to[-1,1].

1. fixed_same: prediction+1.
2. fixed_opposite: prediction-1.
3. global_mean: mean source relation across both cells.
4. gene_shrink10: source target-gene mean shrunk to global mean by10 pseudo-observations, pooling both cells.
5. pooled_ridge100: fingerprints+target one-hot; no cell, hence identical predictions in both cells.
6. pooled_rbf1: same pooled inputs and kernel rule.
7. conditional_ridge100: pooled inputs plus signed cell code(-1 A549,+1 U2OS) and its interaction with every pooled input. Ordinary conditional regression, not a claimed new method.
8. conditional_rbf1: same conditional inputs and kernel rule; ordinary equal-input nonlinear rival.

Primary conditional method is fixed index6. Primary comparator is the maximum full out-of-fold mean utility over ALL seven noncandidate methods, ties in listed order, including the conditional nonlinear rival. The fixed candidate must improve even over this ordinary rival before any stronger mechanism is proposed. Also report context-pooled versus conditional contrasts descriptively; no post-outcome candidate/rank/hyperparameter selection. Failure of one linear design is not biological impossibility or evidence against every conditional model.

## Decision, uncertainty and limits

One5-fold8-method matrix only. Every ID/cell contributes equally, including weak/zero profiles. Bootstrap255 complete identity groups,2000 draws, seed20261032, lexical groups, sum per-group utility differences and divide by sampled count of ID/cell queries; percentile95% interval uses NumPy linear interpolation. This interval conditions on saved predictions, this dataset and the selected comparator; it omits refitting/selection and shared-control/reference error. No randomization p-value is claimed without a defensible exchangeability model.

Exploratory information gate requires positive full gain, positive gain against the SAME selected comparator separately on both plate-position relation outcomes, and conditional interval lower bound>0. This gate neither certifies reproducible biology nor practical drug benefit. Report oracle headroom and magnitude. robust_benefit_established=false, core_promotion=false, Agent=false regardless. No secure-holdout or external validation claim. If ordinary baselines suffice, preserve the result and park this particular design; do not add an architecture to force improvement.

## Execution and output

One1800-second hard launcher under D:/anaconda/envs/maestro/python.exe,4 threads. The whole round has one implementation-failure-only spare matrix; an unfavorable result does not authorize reruns. Before execution freeze protocol/amendments, metadata/splits, chemical features, code, independent arithmetic checker and original profile hashes. Synthetic math checks and independent source-access/code review precede any values. Save labels/predictions/replicate relations/control feature mask, run/launcher/access receipts, per-query metrics, summary and decision under data/processed/functional_anchor_binding_20261030/b. Retain partial/failed outputs. Independent arithmetic and interpretation precede root synthesis.

Closest priors already cover chemical/genetic morphology matching, shared supervision and conditional distillation; CellCLIP's shared morphology supervision is direct prior overlap, UniPert remains abstract-only, and TIDE's linked code correspondence is uncertified. This cheap countertest cannot establish novelty or replace task-matched reproductions. Its value is deciding whether a larger virtual-cell representation experiment has enough evidence to justify that cost.
