# Development plan: does structured knowledge add real information? (written before any response value was analysed)

This plan fixes the exploratory stage before `develop.py` reads a response value. PRISM 19Q4 is
already exposed to MAESTRO (blocks N and P, and the selective hit triage), so nothing here can be
claimed as independent confirmation. The stage is a gate. It decides whether a confirmatory test on
sealed data is worth its cost, and whether an LLM decision layer may be built at all.

## Task (T0, strict cold start)

* **Unit.** A PRISM 19Q4 primary-screen compound (Broad core; aliases merged by InChIKey
  connectivity).
* **Outcome.** The compound's 2.5 µM log2 fold change over 561 lines with CCLE 19Q4 expression.
* **Target.** The selective residual. The compound's own intercept and slope on the generic
  profile G are removed, where G is the per-line median over training compounds of the fold.
  Predictions are residualised the same way.
* **Inputs a T0 prediction may read.**
  * Structure.
  * T0 knowledge edges: curated Hub, curated MAP-KG mechanism, aggregate binding, biochemical assays.
  * The lines' basal expression and mutations.
  * Training compounds' outcomes.
  * Never the query's own screen values, its L1000 profile, or any cell-based assay edge.
    Cell engagement edges are T1, and growth or viability edges are removed outright.
* **Splits.** Five folds by MoA family (`CENSUS.json`). Shared targets and MoA strings join 91% of
  compounds into one component, so that component is split by first MoA string.
  * Test compounds may therefore share a target gene with training.
  * `strict_new_target` marks the ones that do not (about 107 annotated compounds).
* **Evaluation population.** Active compounds: at least 5 lines with a residual robust z ≤ −3
  and LFC ≤ −1. The rule reads only the compound's own outcome and applies identically to every
  arm. All compounds are reported too.

## Arms

* **zero.** Generic profile only, so the selective score is 0 by construction.
* **Chemistry.** `chem_knn` (Tanimoto kNN) and `chem_ridge` (Tanimoto kernel ridge, penalty by
  inner CV).
* **Annotation and RKT.**
  * `annot`: Hub targets and MoA, Jaccard kNN.
  * `rkt_know`: block Q's knowledge route, re-implemented with its parameters.
* **New.**
  * `kn_typed`: provenance-weighted, relation-typed Jaccard kNN.
  * `tc`: the target-context ridge, with typed and provenance-grouped features of the targets'
    basal expression and mutation in each line.
* **Stacks.** Non-negative weights fitted on inner grouped CV:
  * `chem_full` = chem_knn + chem_ridge (the best non-knowledge T0 baseline);
  * `annot_full` = chem + annot;
  * `rkt_full` = chem + rkt_know;
  * `know_full` = chem + kn_typed + tc (the candidate);
  * `know_only` = kn_typed + tc.
* **Ablations.**
  * `tc_untyped`: one pooled group;
  * `tc_curated`: curated edges only;
  * `know_full_t1`: adds cell-engagement edges; labelled T1, so never a T0 claim.

## Knowledge controls

Twenty seeds each. Each control is applied to the whole graph, training and test, within fold.

* **Degree-preserving.** A curveball swap of drug-gene edges within each (relation, provenance
  group) layer and each fold, and of drug-MoA edges. Every drug's and every gene's degree is
  kept per layer.
* **Stratified set permutation.** Whole knowledge bundles (targets and MoA) are permuted among
  compounds of the same fold and stratum. A stratum is the target-count bucket and whether
  measured edges are present.
* **Coverage-matched gene relabelling.** A permutation of genes within strata. A stratum is the
  degree bin, expression-SD tertile and hotspot frequency. The graph stays isomorphic; only the
  genes' biology changes.
* **Annotation density.** `density_full` = chem + a ridge from annotation counts per provenance
  and mean target degree to the profile.
* **Time-matched.** Not possible. No edge in either source carries a date, and the Hub file
  (2020-03-24) postdates the PRISM release (2019-12). Recorded as `TIME_STAMPS_UNAVAILABLE`.

## Metrics

* **Drug-specific accuracy.** Per active compound, the Pearson r between the predicted and
  observed residual across lines. The unit is the compound.
* **Biological specificity.** r with the compound's own profile, minus the mean r with the other
  active test compounds' profiles.
* **Calibration** of the selective-hit event: residual robust z ≤ −3 and LFC ≤ −1. Brier score
  and expected calibration error of a logistic calibrator fitted on inner predictions.
* **Decision utility.**
  * Per fold, nominate 200 (compound, line) pairs with at most 3 per compound, and count observed
    selective hits.
  * Where a PRISM secondary curve exists, also count secondary-confirmed hits: secondary AUC
    residual robust z ≤ −2.
* **T1 incremental value.**
  * 25% of lines are visible per compound; the remaining 75% are predicted.
  * T1 baseline: chem plus `ctx`, the 25 most expression-similar visible lines, plus `pheno`,
    training compounds that match on the visible lines.
  * T1 + knowledge adds kn_typed and tc.

## Gate (decided before running)

Knowledge earns a confirmatory test only if all three hold on active compounds:

* **G1.** `know_full` − `chem_full` mean Δr > 0, with a one-sided family-cluster sign-flip
  p < 0.05.
* **G2.** The true graph's `know_full` r, and its gain over `chem_full`, each exceed the 95th
  percentile of the same quantity under every control: degree-preserving, set permutation and
  coverage-matched.
* **G3.** The specificity of `know_full` exceeds that of `chem_full`: Δ > 0, sign-flip
  p < 0.05.

The outcomes:

* **G1 passes but G2 fails.** The gain is attributed to annotation structure, not biological
  relationships.
* **G3 fails.** The gain is generic.
* **No LLM decision layer** is built in this study under any outcome. One may be introduced only
  after knowledge passes the gate **and** an independent confirmation.
