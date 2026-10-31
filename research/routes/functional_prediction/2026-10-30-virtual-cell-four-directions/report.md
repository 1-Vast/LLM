# Virtual-cell-first feasibility and learning-mechanism test

**No direction established an independently validated new virtual-cell learning mechanism this round.** The executable B candidate lost to ordinary full-rank regression under source-grouped evaluation. C contains technically consistent dose-dependent rank reversals, but their out-of-background predictability was not tested. A and D stopped at resource/qualification gates. These outcomes do not support introducing an Agent or promoting a model into `src/` or `tools/`.

This bounded episode follows the supplied four-direction brief and the user's extended virtual-cell-first goal. Experiments used the canonical `D:/anaconda/envs/maestro/python.exe`; all research code and reviews remain here. The broader research objective remains **ACTIVE / NOT_ACHIEVED**.

## What was actually tested

| Direction | Observed result | Current decision |
|---|---|---|
| A: cell-line to ex-vivo functional transport | PPC preprint/abstract authenticated; no numerical response table, schema, or system×study×assay overlap obtained | Resource stop; transport hypothesis untested |
| B: context-conditioned genetic target prioritization | 15 methods/controls, five grouped holdouts; candidate rare-hit P@50 **10.09%**, full-rank ridge **11.58%** | Park this residual construction under tested conditions |
| C: dose-window rank switching | **51/336** eligible background×drug-pairs meet the frozen technical-consistency rule | Descriptive feasibility; prediction and biological replication unestablished |
| D: knowledge-constrained unseen-drug function | No qualified new independent scaffold/background functional panel in this acquisition | Conditional branch; no old pathway-label rerun |

The directions were not merged into a large model. A/B/D passed through actual source gates; only B received the full predictive-model comparison. C's small descriptive census tested whether the proposed phenomenon was observable before committing to another model.

## B: conditional information exists, but the proposed structure adds no demonstrated value

The practical task is to rank genetic interventions from a known assay gene library using phenotype, treatment and cell-context metadata. The candidate removes general per-gene hit propensity, scales residuals and learns 16/32/64 shared residual modes from task text. This is ordinary residual/multitask learning. A shared factorization by itself is neither a new biological rule nor a causal mechanism.

The [data audit](audit_b/report.md) verified **1,901 historical entries**, with official temporal splits **1,349 train / 218 validation / 334 test**. LaTest's separate 19 entries were not requested. Projection of only genes, binary hits and metadata avoided the complete 1.09 GB Parquet. Official validation/test rows physically co-occurred in downloaded column chunks but were masked from the extracted training arrays and never scored. The final experiment consumed only the official historical training cache.

Directionally ambiguous merged/recovered rows were excluded. The primary roster contains **1,231 tasks / 115 canonical source groups**. Two small-library directional tasks fail the fit-defined 50-gene eligibility rule, leaving **1,229 tasks / 114 groups** for every actual method and both scoring subsets. Eleven eligible tasks have zero rare hits and remain at zero precision. Eligibility never uses held-out hit counts.

An independent reviewer found that publication IDs alone did not close known dependence: CERES reanalysis and gold-standard label calibration link five papers. Their rows were conservatively joined into one source group. This guards documented label-construction dependence; it does not prove that the remaining groups are biologically independent. Folds are fixed hashes of canonical groups. Hyperparameters are selected on an inner group-held-out set, then all transforms and propensities are refit on four outer training folds. All model variants use the same allowed assay-context fields, which are retrospectively curated and not validated as prospectively available. Outcome-bearing notes, significance/ranking fields, author and source IDs are excluded.

Primary P@50 is **true hits among 50 selected genes / 50**, averaged within sources and then across sources equally. Rare eligibility means fit-partition hit frequency ≤0.10 and measurement in at least 3 canonical fit groups. It is not proof of selective vulnerability or nonessentiality.

| Method | Rare-gene P@50 |
|---|---:|
| Full-rank ridge | **11.575%** |
| Source-balanced rationale frequency | 11.190% |
| Nonlinear tree | 11.074% |
| Official-style text-neighbor frequency | 10.286% |
| Candidate conditional residual | **10.086%** |
| Source-balanced general gene prior | 10.033% |
| Screen-weighted general gene prior | 8.264% |
| Candidate with permuted training context | 8.083% |
| Uniform-ranking expectation | 4.768% |

Candidate minus the strongest primary rival is **−1.489 percentage points**, or **−12.86% relative**. The frozen source-resampling 95% interval is **[−2.752, −0.357] percentage points**; all five outer-fold differences are negative. Excluding the two largest source components leaves a **−1.516 point** difference. These are conditional summaries of retrospective predictions with shared training, not fresh biological confirmation or a universal model-performance theorem.

For drug/chemical/environment-response screens, candidate P@50 is **8.643%**, versus **10.764%** for the strongest subset rival, coarse-phenotype frequency (209 tasks / 49 groups). For non-fitness screens it is **7.352% versus 9.093%** (321 tasks / 90 groups). All-library P@50 is 20.480% for the candidate, 20.782% for full-rank ridge, and 22.060% for the strongest all-library rival, source-balanced screen-type frequency. The [full frozen decision](b_decision.json) fails the continuation gate.

![Source-grouped B comparison](figures/b_model_comparison.png)

The context control is informative: real context beats its permutation by 2.004 points. That supports a bounded association between task context and hits. It does not show that the low-rank restriction is necessary: ordinary regression wins, and a source-balanced gene prior nearly matches the candidate. The current comparison cannot isolate whether rank compression, variance scaling or another implementation choice explains the deficit; no component-specific mechanism is claimed. The panel is stronger than a global-frequency-only comparison, but does not reproduce every published AssayBench/AssayFormer model. A candidate already losing to ordinary models does not merit expensive foundation-model training here.

## C: a real descriptive signal with a restricted evidence level

The [official Zenodo record](https://zenodo.org/records/18292967) advertises three files. Actual downloads show **HTS003.csv and HTS031.csv are byte-identical**, SHA256 `2a5b5a9b…`, and both contain HTS031/SCLC plate labels. They cannot be two independent datasets, and HTS003 cannot be treated as the advertised separate PC-9 experiment.

HTS001 is an already-contacted development source. Its seven backgrounds each have one plate, 14 drugs, 10 doses and two technical wells per drug-dose. The frozen 24–60 h relative-log-growth endpoint uses only bracketing frames before 72 h. MGH lacks such a 60 h bracket, so its 308 wells are excluded without extrapolation. The remaining six backgrounds supply 1,848 wells and 336 exact-dose background×drug-pairs.

There are 75 mean dose flips; **51** also meet the predeclared ±0.25 log2 margin in both deterministic technical pseudo-replicates, with all cross-well signs agreeing. At one deterministic witnessing dose pair per stable source unit, other backgrounds reproduce the mean sign 184/255 times (**72.16%**), but reproduce both margins only 110/255 times (**43.14%**). Drug pairs reuse drugs and backgrounds; those 255 opportunities are not independent experiments. These fractions are observed portability, not held-out prediction accuracy.

![Observed dose-switch example](figures/c_observed_dose_switch.png)

The example is selected for illustration. Relative log growth measures interval-specific growth suppression; it does not calibrate cell death or clinical exposure. No independent preparation/culture certificate was obtained. The [independently authored parser](review/verify_c_independent.py) reproduced every endpoint and flip count; maximum discrepancy across 1,848 endpoints is 4.44e-16. That is arithmetic corroboration on the same observations.

C therefore remains useful for a later narrowly defined prediction question: can a fixed, supported cross-background relation beat ordinary dose curves on held-out decisions? This round did not fit Hill/GP/curve models, so it makes no claim that traditional curves cannot explain the reversals. Qualified independent preparations remain necessary for biological replication.

## What primary-method reading changed

[DrEval 2026](https://doi.org/10.1038/s41467-026-72903-w) supplies direct warnings about drug/cell mean effects, application-aware splits, normalized evaluation and tuned ordinary models. Original [AssayBench 2026](https://arxiv.org/abs/2605.10876) methods/code already include phenotype-conditioned frequency and text-neighbor predictors. Consequently, B was tested against those capabilities rather than presented as a new task merely because it conditions on phenotype.

The [early cross-field scout](transfer/scout_notes.md) partially read seven primary works and one complete abstract. COGS/CompSub require meaningful constituent roles before claiming compositional transfer. LOGICZSL does not supply a verified biological primitive hierarchy. CLIP generalization warns that partial target-context exposure can introduce shortcuts. LAWM needs trajectories, which static endpoint screens do not provide. TraCA's constant-kernel construction shows why separate per-intervention mappings cannot establish a common transport relation. These sources sharpened the experimental restrictions; none supplied a validated new biological learning rule. Exact reading sections, adverse evidence and access limits are preserved in the scout and assay audit. This is targeted method reading, not an exhaustive 2025–2026 top-journal survey or universal novelty search.

PPC's [authenticated preprint](https://doi.org/10.64898/2026.02.14.705918) remained abstract-level after full-text access failures. Its atlas size claims were not independently counted. Actual model-system/assay confounding is unobservable without numerical and metadata release. [A's report](audit_a/README.md) and [D's gate](audit_d.md) preserve the exact resource limits and restart requirements.

## Verification, budget and handoff

The [independent B verifier](review/verify_b_independent.py) checked all 36,870 actual prediction records, exact source/fold mappings, fit-only rarity, identical evaluation populations and every 50-gene pick. Independently recomputed precision, recall, prevalence and adjusted precision match exactly; delta/interval discrepancies are below 2e-18. See [B comparison](review/b_comparison.json) and [C comparison](review/c_comparison.json). Static fitting-code review and output arithmetic are separate checks; neither authenticates new biological experiments.

Canonical maestro completed in 436.672 seconds, 503.406 CPU-seconds, with 4 compute threads. The initial isolated environment (derived from maestro) is preserved as a diagnostic; all aggregate metrics agree exactly. Canonical choice preceded score interpretation. Peak memory was not measured by the fitting script. [Execution notes](execution_notes.md) retain import-only, registration and comparison-helper corrections rather than recasting them as scientific failures.

The six-pass search/review ceiling is exhausted; no post-score grid expansion occurred. Known completed/capped source bodies total approximately **277.91 MB**, below the declared 300 MB budget. Failed partial traffic is unmeasured, so this subtotal does not certify total network transport below the cap. No paid model API or external model bridge was called; agent token/cost metrics are unavailable. [Usage](usage.json), [research record](record.md), frozen protocols, source receipts and [library verification](library_verify.json) preserve scope and actual limits. Figures were rendered and visually inspected; editable SVGs accompany the PNGs.

The [final content review](review/content_review.md) passed after correcting the retrospective-field availability boundary. The [final local checks](review/final_checks.json) record JSON validity, this episode's registry mappings and links, and frozen source/code hashes. This bounded stage is closed on 2026-10-30; the broader functional virtual-cell research objective remains **ACTIVE / NOT_ACHIEVED**.

**Retained decision:** park B1 as tested; retain C's phenomenon without a prediction claim; reopen A/D only when their qualified data conditions change. There is no independently validated flagship mechanism, Agent gain or core-code promotion. Preserve these negative results and boundaries in the existing project synthesis/index so the next round starts from evidence rather than another renamed residual model.
