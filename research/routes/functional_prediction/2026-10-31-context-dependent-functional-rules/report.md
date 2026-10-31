# Common-coordinate transport of functional pair responses

2026-10-31. **The selected common-coordinate restriction did not demonstrate added predictive capability on the observable internal panel.** It modestly improved a zero-interaction predictor, missed the prospective 10% margin, and lost substantially to an equally informed ordinary nonlinear predictor. The admitted numerical pipeline failed during final JSON export. The comparisons below are independently checked, **post-failure descriptive arithmetic on saved predictions, labels and losses**, not a claim that the original pipeline passed. The useful Virtual Cell objective remains **ACTIVE / NOT_ACHIEVED**.

## Question, lineage and scientific restriction

The user's D-SPIN/MAMMAL/RiNALMo discussion motivated testing a useful intervention relation before enlarging a model or adding an Agent. Earlier [study53](../2026-10-31-splicing-pharmacology-learning/report.md) qualified an economical RNA sample/identity entrance but left intervention eligibility and numerical count support unresolved. This episode compared that limitation with the existing environmental-genetic-interaction entrance and the newly recovered original D-SPIN Methods. It selected one falsifiable functional-response experiment, rather than treating data qualification as useful learning.

I054.v1 asks whether a nonlinear coordinate learned from untreated-to-etoposide responses transfers to glucose deprivation after observing target singles, without using target double outcomes for training. A screening team with an existing pair screen could use predicted conditional pair effects to prioritize follow-up combinations. Target single/control measurements and untreated double measurements are paid inputs; this is not prediction of a wholly unperformed intervention or demonstrated screening savings.

For each guide construct and culture, let `L = log2((C_condition+p)/(C_T0+p))` and let `Y` subtract the mean non-targeting-control L. Apply an anchored increasing Yeo–Johnson transform T to individual Y values **before** averaging controls. The proposed restriction keeps

```text
K_ab,e = T(Y_ab,e) - mean_n T(Y_an,e) - mean_n T(Y_nb,e)
         + mean_nm T(Y_nm,e)
K_ab,e = K_ab,UT
```

across environments. Observed single effects may change arbitrarily. Invert T to predict the target double, then evaluate the direct contrast

```text
D = log2((C_target+p)/(C_UT+p))
Q_ab = D_ab - mean_n D_an - mean_n D_nb + mean_nm D_nm.
```

The label Q algebraically cancels T0, while nonlinear model inputs still depend on T0 measurement. Q is not the paper's subtraction of separately standardized native GI scores. The exact equations, constructive example and indistinguishable-input counterexample are in the [frozen candidate](development/common_coordinate_candidate_v1.md), SHA-256 `ee1d15621b33b1e1b4fd2c8a2e101e0452cf9b5242fec024b753c0998e82fc33`.

This is an ordinary monotone-link model with fixed pair effects and changing measured single terms, not a new fitting algorithm. Identity lambda=1 gives Q=0 exactly. Its scientific claim is useful transfer of this restriction in the stated assay, not molecular rewiring, physical interaction discovery or a general cell simulator.

## Data, information and prospective comparison

The exact [protocol_v5](protocol_v5.md), [experiment_v5](experiment_v5.py) and [numeric freeze](numeric_freeze_v5.json) were independently admitted before execution. Freeze SHA-256 is `2b86e5d5d1b10a244fd84b202ee839ae7440810cfc0add0fc7c39faff26dac52`. The [earlier EGI access contract](../2026-10-30-conditional-intervention-admission/egi_source/admission_contract.md) was read completely before extending response access.

The original Herken resource, DOI [10.1016/j.molcel.2026.01.025](https://doi.org/10.1016/j.molcel.2026.01.025), supplies GI2 K562 construct counts: shared T0/untreated references, etoposide and glucose-deprivation day-9 endpoints, in two culture ancestries. The count gzip has SHA-256 `f9f5c85fc81e366709fd5d42f1c3c85388f00ab19624e14ebede53f72e09080b`; the source-derived guide table has SHA-256 `9adbe2671aa6d422f394016677b4f944c9347eacfb8bc6acb07a2b0ba184ea78`. These endpoints are not trajectories or five independent environments. The selected gene panel has screening ancestry; it is not a genome-wide or independent external validation set.

Eligibility uses T0>=30 in both cultures, complete untreated inputs, and a common availability mask for paid single/NTC controls across the three conditions and both cultures. Empty allowed fields remain missing, never biological zeros; nonempty tokens must be finite nonnegative integers. Target and held-etoposide double availability cannot select prediction eligibility. The saved masks retain 405,269 T0-supported constructs, remove 800 for untreated availability and 27 for paid-control availability, leaving 404,442 constructs. Guide/orientation support leaves 310 genes and 47,894 unordered pairs.

Whole-pair SHA-256 folds allocate 0–6 to source training, 7 to source validation, and 8–9 to test; all guides, orientations and both cultures of a pair share a fold. Complete source-development labels leave 33,398 training and 4,719 validation pairs; 145/20 source pairs are unobservable in those respective splits. The fixed prediction test universe is 9,612 pairs. Genes recur across folds. Both source cultures train the models, so culture 2 is not an independent training-culture holdout.

Only source etoposide development doubles choose lambda from 0:0.05:2 or tune ordinary rivals. The five-model matrix is the selected coordinate, Q=0, source mean, Ridge and histogram gradient boosting (HGB). Ordinary models receive all 41 coordinate-grid predictions plus the same paid raw summaries; the restriction has no hidden information advantage. Source validation selects lambda=0.70, Ridge alpha=1 and HGB 15 leaves, with the remaining hyperparameters frozen. Predictions for all pseudocounts were saved and hash-bound before held source/target double access.

Useful internal advantage required at least 10% lower pooled glucose MSE than **every** rival, lower error in each culture than its best rival, and a positive lower gene-weighted resampling bound against the best pooled rival. Source-held improvement over zero, >=80% input/label coverage, a source-profile diagnostic and target signal headroom were additional requirements. The primary pseudocount is 1; 0.5 and 2 are fixed sensitivity analyses, not choices after seeing results.

## Execution failure and what was actually checked

The first [launch receipt](launch_receipt.json) records failure after 5.594 seconds at an empty count field, before fitting or frozen predictions. The sole implementation repair added explicit missing-value handling and matched-label denominators; all failed code/freezes/logs remain intact. Its exact revised bytes received a fresh [independent admission](review/execution_admission.json).

The [repair receipt](launch_repair_receipt.json) records successful fitting at 213.453 seconds, followed by score-stage failure at 237.672 seconds total. Aggregate numerical subprocess time was 243.266 seconds of the 1,800-second ceiling, using four logical CPUs (affinity mask 15). No further matrix launch, scorer rerun or second implementation repair occurred.

Before failing, the process saved [predictions and their manifest](run_repaired/prediction_manifest.json), source-fit parameters, fitted-model bytes and `scored_labels.npz` containing labels, matched-observation masks and paired squared losses. Final `json.dumps(..., allow_nan=False)` rejected NaN. The independent [artifact review](challenge/post_failure_artifact_review.md) found a concrete cause: a constant source-mean prediction had exactly zero range but tiny positive floating-point standard deviation, passed the correlation guard and produced undefined Spearman correlation. This explains a reporting failure; the review does not certify that every unsaved summary was otherwise valid.

Root and reviewer separately verified prediction-manifest bindings, finite predictions, matched-label masks, and exact equality of saved losses to `(prediction-label)**2`. The reviewer hashed the pickle without loading it. The scored-label file is a later artifact, not a member of the prelabel manifest; its recorded SHA-256 is `c328fd64e64bb2bb68cf3a4e03f49e7ce425e946a9fab88618bfb7b1faa3dbac`. See [root arithmetic](review/post_failure_arithmetic.json) and [independent arithmetic](challenge/persisted_artifact_arithmetic.json).

The first root arithmetic extractor itself failed a mixed-indexing shape assertion before output. Its original bytes are preserved; [the correction record](review/extractor_correction.json) identifies the explicit-axis arithmetic-only version. This did not rerun a scientific model or score raw counts. Correlations, raw-count-floor and coordinate-residual summaries were not reconstructed by root and are not represented as completed original diagnostics.

## Saved-array results

All values in this section are **post-failure internal descriptive results**, pooled original-Q MSE on exactly the same observable pairs for every model. Source-held coverage is 9,564/9,612 (99.50%); glucose coverage is 9,444/9,612 (98.25%). Missingness need not be random.

| Model | Held etoposide MSE | Glucose MSE | Glucose culture 1 / 2 |
|---|---:|---:|---:|
| Common coordinate, lambda=0.70 | 0.100965 | 0.074499 | 0.074296 / 0.074702 |
| Q=0 | 0.112472 | 0.079345 | 0.078918 / 0.079772 |
| Source mean | 0.112470 | 0.079155 | 0.078754 / 0.079556 |
| Ordinary Ridge | 0.040480 | 0.145006 | 0.158361 / 0.131652 |
| Ordinary HGB | 0.041267 | **0.031484** | **0.030834 / 0.032134** |

The coordinate lowers glucose MSE by about 6.1% relative to zero, below the frozen 10% margin. Its source-held improvement is real in these arrays, but both ordinary fitted predictors have much lower source error. HGB has much lower glucose error in both cultures. Ridge's poor transfer cannot rescue the restriction by selecting a weak comparator.

The declared 500 Poisson(1) gene-weight resamples use seed 20261031, pair weight `w_a*w_b`, and common weights across cultures. For `MSE(rival)-MSE(coordinate)`, the 95% percentile interval is [0.000956, 0.010528] against zero and **[-0.057098, -0.032174] against HGB**. Thus modest zero-baseline gain coexists with failure against the strongest ordinary rival. These are internal resampling intervals, not population-level biological uncertainty from two cultures.

The descriptive 1%-validation-loss-compatible lambdas are {0.65, 0.70, 0.75}; both culture profiles minimize at 0.70. No test pair has mean-culture compatible prediction spread >0.5. This is not a confidence set or proof of biological identification. Primary input support covers 99.42% of the fixed glucose test universe; on 9,411 supported/observed target pairs, coordinate/HGB MSE is 0.072819/0.030795. Glucose centered pair variance 0.075305 exceeds half mean squared culture disagreement 0.024165. Profile, coverage and descriptive headroom therefore do not explain away or rescue the failed advantage.

At the original 100-pair absolute-Q ranking budget, with lexical ties and a signed strong hit requiring |Q|>=1 in both cultures with matching observed/predicted sign:

| Model | Confirmed hits | Assessed nonhits | Unassessable |
|---|---:|---:|---:|
| Coordinate | 21 | 59 | 20 |
| Q=0 | 0 | 94 | 6 |
| Source mean | 0 | 94 | 6 |
| Ridge | 23 | 51 | 26 |
| HGB | 33 | 44 | 23 |

The observed-label hit ceiling is 50; the full-universe ceiling is unknown. Tail missingness is substantial despite high overall coverage. These are confirmed assay-contrast yields with unresolved selections, not complete precision estimates, therapeutic hits or validated drug-prioritization benefits.

At pseudocount 0.5, saved coordinate/zero/HGB glucose MSE is 0.075163/0.079922/0.031817; at 2 it is 0.073312/0.078307/0.031165. The ordering persists without refitting. A separate source-code limitation leaves the local `lam` at 2 when constructing **alternate-pseudocount support and inverse-sensitivity diagnostics**. Alternate candidate predictions still use the selected 0.70 grid column, and primary diagnostics use 0.70. Alternate support/sensitivity diagnostics are excluded from validated selected-coordinate claims; no repair or rerun was made.

## What the source work changed

The [source findings](root/source_findings.md), [investigator handoff](investigator/evidence_handoff.md) and [donor handoff](scout/handoff.md) preserve locators and actual reading scope. The important changes are:

- **D-SPIN:** official Caltech data record `tbmca-wbj97` and authenticated 2023 preprint v3 originals were recovered. Main p5 specifies shared J with condition-specific h. Supplement section 1.16, pp17–18, fits combination samples on measured 5x6/5x5 grids and interpolates fitted h with thin plates. Small Figure5/7 workbooks were inspected only for metadata/header geometry; their fitted J/h summaries are derived model outputs, not independent functional labels. Fixed J with changing h can change marginal correlations, so correlation changes alone cannot justify coupling revision. This changed the executed selection: no D-SPIN learner was fitted from these summaries. Formal 2026 DOI [10.1016/j.cell.2026.04.028](https://doi.org/10.1016/j.cell.2026.04.028) and the 2025 guide remain abstract-level, not final-Methods verification.
- **Global epistasis and ordinary predictors:** Carlson2025 [10.1073/pnas.2509444122](https://doi.org/10.1073/pnas.2509444122), original sections2/4/11; PLoSCB2026 [10.1371/journal.pcbi.1014000](https://doi.org/10.1371/journal.pcbi.1014000), Methods4.1/4.2; and NARGAB2026 [10.1093/nargab/lqag084](https://doi.org/10.1093/nargab/lqag084), MethodsSEC2-2, sharpened the ordinary-equivalence and multidimensional/noise alternatives. They support a narrow empirical restriction test and strong ordinary rivals, not an algorithm-novelty claim. Otwinowski2018 [10.1073/pnas.1804015115](https://doi.org/10.1073/pnas.1804015115) remains metadata-only after failed original interfaces; exact closest-prior overlap is unresolved.
- **IMP donor:** original [arXiv2205.09162v2](https://arxiv.org/abs/2205.09162), pp1–4/Algorithm1, requires a stable measured response-descendant channel and observed target covariates. Neither entrance authenticates that matched downstream channel. It changed the information question and prevented an unsupported module attachment; no IMP model was implemented.

The current official D-SPIN tree `70028cf0069ba7284c819930e0a1c40695b22912` is not a verified commit. Selected README/LICENSE/preprocessing bytes match its Git blobs but are not a complete model reproduction. Original code for the PLoSCB/NARGAB works is stored as inert selected slices; none was installed or executed. The library's technical supplement-format slots explicitly distinguish JATS main text and the 2023 D-SPIN main preprint from scientific supplements and the unacquired formal main version.

## Decision, preservation and reusable boundary

Stop I054.v1 as a candidate for **added capability on this observable internal panel**. Preserve `PIPELINE_FAILED` separately from `POST_FAILURE_DESCRIPTIVE_NEGATIVE_CAPABILITY`. The negative comparison is supported by coherent saved artifacts; it is not merely an unexplained crash. It does not show that all common coordinates are impossible or that molecular couplings changed.

HGB receives the entire coordinate grid, so its success does not prove that coordinate preprocessing is dispensable. Its lower internal error also does not establish a new Virtual Cell mechanism, independent functional transfer, actual experiment savings, drug efficacy or Agent advantage. Shared references, source training in both cultures, recurrent genes, selected assay ancestry and missing tails remain material limits. GI2 is now numerically exposed through this experiment; native standardized GI matrices, original EGI Results/Discussion and protected CGI63/S2/HTS031/historical-confirmation responses remain unopened.

Reusing the declared paired-loss comparison, ordinary-equivalence analysis and source/control observation contract is supported under these exact conditions. A future restart needs a materially different, prospectively qualified scientific restriction or independent observation capable of resolving it; another lambda search or target-based calibration would be a new exploratory study. The already described independently grown sparse-library/new-environment test was conditional on useful internal superiority and is not justified by this result. No further experiment is initiated in this episode.

Actual acquisition was 37/50 HTTP attempts and 28,436,434/134,217,728 known decoded bytes, counting four redirects and two complete 500 error bodies. Six selected episodes total 248/350 attempts and 552,929,129/1,040,187,392 bytes, not program totals. Wire bytes, effective model settings, tokens and monetary cost are unconfirmed. Requested roles were Sol/medium investigator, Sol/high scout/challenger and Astra/MAX difficult proposer; the proposer was not the independent challenger.

Actual [owner-library verification](library_verify_final.json) reports 239 identities, 204 reading files, 26 snapshots and 19 sources with official stored code, with no errors/warnings/changed snapshots. Four new identities, five originals and three inert code slices were registered. Two local registration failures (`other_ids` and protected `archive_sha256` metadata) and their bounded supported-field resumes are preserved; they are not numerical reruns. The old D-SPIN metadata row is narrowed to formal-abstract versus preprint reading, and its empty repository placeholder becomes the authenticated selected-slice relationship; the original rows remain in the baseline snapshot.

Bounded integration adds study54 to the existing six project surfaces and preserves prior entries and text. No cleanup, commit, upload, installation, weights, author-code execution, Agent or core promotion is part of this result. The [scientific decision](root/scientific_decision.json), independent content review and final preservation receipt distinguish scientific interpretation, report integrity and execution status.
