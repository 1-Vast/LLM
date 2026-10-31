# B1: conditional functional hit prediction across source groups

Status: proposed v1, before any grouped model score. This is an exploratory capability test of ordinary conditional models, not a novel algorithm claim. Resource census and whole-training label prevalence were inspected during eligibility; this is not untouched confirmation.

## Scientific question and mechanism

Can phenotype/background-dependent gene-hit patterns guide target prioritization across publications beyond general gene importance, phenotype-conditioned frequency and text-neighbor baselines? The practical output is a ranked list for a functional screen's known gene library. This is gene-perturbation hit prioritization, not small-molecule efficacy or a causal drug-induced dependency.

Candidate: subtract the training-only per-gene general hit propensity, scale residuals by sqrt(p_g(1-p_g)+0.01), and fit a small shared low-rank residual relation from allowed task text. The restriction is a common conditional relation across publications; free per-test-study or intervention fits are forbidden. Weighted truncated SVD supplies 16/32/64 residual modes; kernel ridge from TF-IDF context predicts mode coefficients. Restore the gene propensity and scale at readout. Missing gene-task measurements have zero residual (mean imputation), not negative labels. All factual gene/library masks remain visible to all comparators. This is a known residual/multitask learning construction; its relevance and portability are the hypotheses.

Rivals: universal essentiality, phenotype-stratified hit rates, ordinary text neighbors, full-rank regression and nonlinear trees on the same task information. No learned mode is interpreted as a biological pathway without separate evidence. Cross-field sources motivate falsifiable common relations and grouped compositional tests; they do not validate the biology.

## Data and grouping

Use only the 1,349 official yearfold0=train tasks from pinned Genentech/assaybench revision fa2ed4195d2eea1e5ed570d1a67c21e47650962d. Official historical validation/test outcomes and LaTest remain unscored. Public Parquet chunks physically include historical rows, but extraction masks nontraining rows and only the training CSR is consumed.

Primary endpoint set: keep the 1,062 unidirectional base rows and 169 explicitly directional dec/inc variants; exclude 74 merged any-direction variants and 44 recovered-bidirectional rows. Expected 1,231 rows before library/score eligibility. Binary hit is defined by the benchmark's source-specific criteria, not a common effect magnitude. Directional dec/inc hit sets were verified disjoint with merged equal to their union; this validates representation consistency, not experimental replication.

Group by source_id (publication) after joining PMID27260156 and PMID29083409 because the GeCKOv2 original/reanalysis lineage is shared. All original-screen variants therefore stay together. Other cross-publication donor/culture/processing overlap is not certified, so describe results as source-grouped internal evaluation, not fully independent biology. Report equal-source averages and largest-source sensitivity.

Outer fold = int(SHA256('maestro-vc-b1:'+group)[:8],16) % 5. For outer fold k, test k, validation (k+1)%5, fit the remaining three folds. Select hyperparameters on source-macro rare-gene P@50, deterministic simpler/smaller first on ties; then refit on all four non-test folds. Do not select models or thresholds on outer scores. Persist fold/group roster before fitting. No target-label anchors or test-study calibration are allowed.

Allowed text: phenotype, condition_clause, screen_rationale, cell_line, cell_type, screen_type, library_type. Exclude author/source IDs/dataset IDs, notes, significance_criteria, ranking_rationale, answer fields, raw numeric outcomes and post-screen hit lists. Reporter, target and known background names present in safe fields are prospective assay context, not causal evidence; document this scope. Fit TF-IDF only on each fit partition: max_features=5000, English stop words, word 1–2 grams, min_df=2. Official-neighbor reproduction uses phenotype+condition_clause+screen_rationale only; same-information neighbor and all learned models use the full allowed text. Blank/Not specified fields contribute no text.

## Comparators and controls

- Uniform ranking expectation from each measured eligible library; deterministic lexicographic tie breaking for all actual ranks.
- Screen-weighted global per-gene hit frequency and source-balanced global frequency.
- Screen-type, coarse phenotype and screen-rationale conditional frequency, with 10 pseudo-observations of global propensity for measured support; missing strata fall back to global.
- Official-style TF-IDF k=10 neighbor frequency, unweighted observed hit/count ratio, unseen gene=0. Same-information neighbors tune k in [5,10,30], retaining the same observed-mask ratio.
- Full-rank kernel ridge predicting training-centered binary hit residuals, alpha in [0.1,1,10]. Same-information nonlinear ExtraTrees predicts 64 ordinary residual modes from a train-fitted 64-component TF-IDF representation; 128 trees, max_depth in [4,8], min_samples_leaf=2, n_jobs=4, random_state=1030. Report that this is a bounded strong-baseline panel, not every published AssayBench/AssayFormer baseline.
- Candidate scaled residual modes: rank in [16,32,64], alpha in [0.1,1,10]. Use identical source-balanced fitting weights for learned models; normalize weights to mean1. Truncated decompositions use random_state1030. All fitting transformations and gene propensities use the fit partition only.
- Ablation: general gene propensity (no conditional residual). Negative control: same selected candidate with training task-context rows permuted with seed1030, leaving label arrays, masks and source weights fixed. This is a shortcut diagnostic, not a permutation p-value. Use its own training-only text fit. No control gets test labels.

## Evaluation, opportunity, and stopping

Rank genes within the screen's measured library. Primary rare-gene eligibility: training screen-weighted hit frequency <=0.10 and measured in at least three distinct fit publications; recompute after final outer refit. Require at least 50 eligible measured genes; do not exclude a screen because it has no rare hits. Save all input/eligible denominators and numbers of available true hits. Rare means uncommon training hit, not demonstrated selective/nonessential biology.

Primary metric: P@50 on rare eligible genes, average tasks within source then sources equally. Secondary: all-library P@50, rare recall@50, random-adjusted P@50=(P@50-library prevalence)/(1-library prevalence), and non-fitness/drug subset metrics. Treat zero-hit eligible libraries as P@50=0; recall undefined with denominator reported; prevalence=1 makes adjusted metric undefined. Report task-weighted scores separately. Target hit counts are used only for scoring, never for filtering or fitting.

Save top-50 gene IDs and hit counts per task/model/subset, selected hyperparameters, input/source/code/protocol hashes and execution time. Source-level paired candidate-minus-best-baseline differences and a fixed 2,000-draw source bootstrap summarize these frozen predictions; this is conditional resampling of observed publication groups, not biological-culture uncertainty or prospective validation. Report all five outer-fold differences and exclude the two largest sources as a preset sensitivity.

Continue to an independently sourced/frozen capability test only if candidate rare P@50 exceeds every comparator by >=0.05 absolute and >=20% relative, paired source-bootstrap lower bound >0, >=3/5 outer folds improve, all-library P@50 falls by no more than0.02, and both real context and non-fitness/drug tests show benefit. These are pragmatic development margins for this round, not universal biological standards. Otherwise preserve the scoped negative and diagnose which simple rival wins. Even a pass is not sufficient for core promotion or an Agent: those require separate independent data and decision/cost evidence.

Run using D:/MAESTRO/.venv/Scripts/python.exe, CPU only, no dependency installs/network/model bridge. Initial ceiling: 15 minutes wall for this one five-fold job matrix, 4 compute threads, observed resource use logged; ceilings are cooperative rather than OS-enforced. Do not expand the hyperparameter grid after scores. Correct implementation failures with preserved logs and unchanged scientific criteria. Independent protocol challenge and arithmetic/leakage review are required before scientific interpretation.
