# Prospective baseline calibration — draft, not permission to fit yet

Purpose: establish a reproducible functional evaluation asset and strong conventional learning curves before selecting any new update mechanism. Ordinary retraining/Maxide capability is already published; this stage cannot establish algorithmic novelty, a virtual-cell world model, inheritance or RSI.

## Data and information

Conditional on author-selected K562 CRISPRa growth-hit targets, use only measured single-target RNA and independent bulk single growth priors to predict double-target growth. Gene-average processed_fitnesses is the proposed primary endpoint; gene-level GI is secondary. Do not confuse chosen-guide processed_perturbseq fitness with gene-average primary. Do not use double-RNA outputs, GI-derived clusters, guide-selection labels outside explicit single priors, whole-map embeddings or held-out function values as features.

Primary source author uses raw cells, UMI>=2000 and single_cell filtering. Reconstruct exact cell/guide assignment semantics from source before values. Record state/QC bias; this is a retrospective conditional seen-gene pair task, not new-gene or unselected genome-wide screening. All arms share supplied single RNA and single growth availability; arms omitting RNA are information ablations, not same-information superiority controls. RNA acquisition cost is disclosed, not zero-cost prospective discovery.

## Splits and access

After string-only aliases and gene membership fixed, canonicalize an unordered nonself pair as sorted gene symbols joined with `|`. Hash SHA256 of `MAESTRO_NORMAN_FUNCTION_V1|` plus canonical pair, take first eight bytes big-endian integer modulo100: 0..59 source,60..79 development,80..99 protected audit. Keep mirrors, replicates and guide measurements of the same unordered pair together. Seen genes are explicit; no split by single cells. Do not convert protected numerical values merely to count missingness. Report source/development missingness independently; membership does not prove labels complete.

Source pair sample ordering uses separate SHA256 salt `MAESTRO_NORMAN_BUDGET_V1|`. Nested measured-pair budgets128,512,2048 when enough source examples exist; report actual N otherwise. Common sampled feedback and initialization across arms. Development labels are for a small declared hyperparameter menu only and their exposure counts as cost. No model/candidate sees protected outcomes until final frozen implementation. Repeated budgets are computational replays, not new biological tasks.

## Necessary conventional references

1. Constant and single-growth additive/quadratic response, fit coefficients on observed source pairs only.
2. Gene identity pair ridge / conventional low-rank completion using the same feedback.
3. Regularized direct symmetric RNA-pair predictor and simple fusion with single-growth response.
4. Original RNA-side-information Maxide plus fitted quadratic-growth residual procedure, with explicit observation mask preserving real zeros; document any implementation corrections and compare original-compatible setting. Do not silently label a different estimator as faithful reproduction.

Use train-only feature scaling/DR where learned with feedback; if RNA-only transforms use all available single profiles, disclose transductive seen-gene design and give every same-information arm that access. No future pair-RNA means or all-label-selected feature dimensions. Avoid tuning a large hidden search for the proposed arm.

Primary report is development MSE versus measured-pair budget and total fit/selection cost. Also report GI ranking/decision utility with the selection target fixed before labels; no drug response claim. Pair residuals share genes: naive independent-pair intervals are insufficient for broad generalization; use gene-aware resampling/sensitivity and state within-one-map limits. Do not count random seeds as independent tasks.

## Gates

Before execution: source/QC semantics, actual matrix-identity alignment, primary endpoint lineage and zero/missing handling must pass review. Then run baseline calibration rather than an unreviewed new mechanism. A stable residual error pattern under strong same-information conventional models is evidence for formulating a candidate, not itself a new method. Only a separately specified mechanism with independent novelty/necessity review can enter a method comparison. If conventional methods explain all proposed incremental value, stop that innovation claim. No repeated runs of historical stopped configurations and no RSI progression inferred from one K562 map.
