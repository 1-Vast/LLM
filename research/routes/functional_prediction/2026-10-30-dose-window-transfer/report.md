# Two-dose calibration does not establish a new virtual-cell learning mechanism

The proposed anchor-scaled curve-shape rule did not improve the primary drug-choice outcome over ordinary covariance conditioning. Its pairwise choice regret was **0.025324**, versus **0.022345** for full joint covariance updating: **13.33% higher loss**. The fixed continuation gate did not pass. HTS031 treatment counts remain unread, and no Agent or core-code promotion is supported. The overall research goal remains **ACTIVE / NOT_ACHIEVED**.

This result advances the earlier four-direction study's C question from observed dose switches to an actual prediction test. It does not refute all conditional dose prediction: ordinary calibration models retain useful internal signals, including better whole-menu choices. The current source and evaluation do not establish independent biology, exceptional drug-discovery benefit or an algorithmic innovation.

## What was predicted

For a new background in an existing drug library, measure two concentrations per compound and predict its six intermediate concentrations using historical full curves from other backgrounds. The candidate assumes the intermediate curve shape is approximately preserved after scaling by the target background's two endpoint responses. In [candidate.md](candidate.md), the prediction is `A + D*(u+q_drug)`, where A,D come only from the two measured target conditions and q comes only from source backgrounds. This is ordinary anchored shape-invariant regression, not a newly identified cellular mechanism.

The input is the already exposed HTS001 source: six related PC9 backgrounds, fourteen drugs, ten doses and two technical wells per condition. The endpoint is vehicle-adjusted log2 growth between 24 and 60 h, with interpolation brackets strictly before 72 h drug replacement. It is an interval-specific growth contrast, not a verified post-stabilization DIP rate, cell-death measurement or clinical exposure model. The final bracketing image can occur after 60 h.

Zero-based dose indices 1 and 8 were fixed calibration conditions; indices 2–7 were queries. Those 2 calibration conditions are 20% of the ten-dose grid and one third of the six queried conditions. That is a condition count, not a total-cost saving certificate. Controls, imaging, plates and historical data also cost resources; measuring one desired dose directly can be cheaper. All methods could use the complete 28-condition target anchor vector and the same historical full curves.

Every outer fold holds out one whole background; hyperparameters are selected globally per model using inner background holds. All means, covariance, scales, priors and tree features are fit-only. A target-background ID is used for optimizer logging only. The test concerns unmeasured drug-dose/background combinations of historically measured compounds; it does not test unseen chemical identities or scaffolds. One plate per background and shared ancestry prevent treating the six folds as independent preparations.

The common query roster contains **56 drug pairs and336 pair-dose choices per background**:2,016 pair-dose choices in total, repeatedly using the same 504 query-condition means. Pair comparisons use exact physical molar concentration, never matching normalized indices between different dose grids. Twelve multi-drug dose menus per background supply a separate best-compound metric. Temsirolimus-only menus are excluded because there is no choice.

## Full frozen comparison

Primary regret is the growth penalty for choosing the worse member of a two-drug shortlist, averaged over query doses within pair, pairs within background, and backgrounds equally. Zero is the oracle floor. Whole-menu regret instead chooses one compound from every eligible exact-dose menu. Both are measured in log2 interval-growth units and are better when lower.

| Model | Pairwise regret | Whole-menu regret |
|---|---:|---:|
| Full joint covariance update | **0.022345** |0.022455|
| Additive anchored source shape |0.022617|**0.013266**|
| Full anchored ridge |0.022731|0.016663|
| Response-profile neighbor |0.022980|0.016865|
| Same-information tree |0.023350|0.018429|
| Source mean, no target anchors |0.023618|0.031607|
| Smooth GP |0.025072|0.017252|
| Candidate anchor-scaled shape |**0.025324**|0.015309|
| Regularized Hill |0.034760|0.059054|
| Pooled normalized shape |0.049139|0.109293|
| Target log-dose interpolation |0.050628|0.075671|
| Wrong-drug shape diagnostic |0.075964|0.328410|

![Fixed C2 selection comparison](figures/selection_regret.png)

Candidate improvement against the fixed strongest primary rival is **−0.002978**; the conditional paired-background 95% interval is **[−0.009389,+0.002162]**. Only 2/6 backgrounds improve. Both technical-well sensitivity comparisons also favor the rival. The interval includes zero, so this is a failure to establish the requested gain, not a population-level proof that the restriction is always harmful. Background bootstrap summaries share training and do not certify independent cultures.

There is also a planning limitation: the strongest rival has only **0.022345** oracle headroom, less than the predeclared **0.05** absolute improvement threshold. That part of the gate is unattainable here even for an oracle. The threshold was retained. Its failure cannot be used as evidence against a biological relationship. Separately, the candidate's observed primary loss is higher than ordinary rivals and even the uncalibrated source mean. Future threshold/power planning must use source-only decision-loss headroom before committing to a supposed exceptional-gain test.

Useful signals remain. Candidate shape beats interpolation, pooled shape and the wrong-drug diagnostic by 0.025305, 0.023816 and 0.050640 respectively. Drug-specific historical shapes therefore contain information under this calibration setting, but those controls do not establish the necessity of scaling by D. The ordinary additive shape and covariance rivals do better on the primary objective. This comparison cannot attribute the deficit uniquely to shape invariance, regularization or another single component.

On whole-menu choices the candidate improves on the primary covariance rival, so a statement that it loses every outcome would be false. However, the simple additive anchored shape has still lower whole-menu regret: **0.013266 versus 0.015309**. Ordinary calibration reduces this secondary loss from the no-anchor source mean's 0.031607. These are useful internal associations, not independent validation or measured assay-cost savings; they do not rescue the candidate's frozen gate.

## What happened to dose switches

Within the six queried interior concentrations, **35/336** background/drug-pairs have technically concordant observed flips. C1 found 51 using all ten concentrations; the witness support differs, so 35 is not a correction to 51. Candidate predictions recover 19/35 (sensitivity 54.29%) with 19/27 precision 70.37%. The uncalibrated source mean recovers 20/35; ordinary additive shape recovers 27/35, and response-profile neighbors 28/35. Historical shared structure and ordinary calibration explain substantial predictive signal without establishing a special scaled-shape mechanism. These counts reuse drugs/backgrounds and are technical observations, not 336 independent experiments.

## Source and principle reading changed the design

The [source/design investigation](source_design/findings.md) authenticated the BESTDR 2025 original and current Zenodo description. BESTDR already uses hierarchical curve sharing; Thunor and Harris already define ordinary logistic/DIP methods. The original 2026 response-profile paper's Methods already uses measured drug responses as a functional background descriptor and ordinary trees, with source-only panel construction. MOGP already shares dose outputs and reports cross-study variation and negative transfer conditions. Their methods constrain novelty and supply strong rivals; titles or deposit dates were not treated as new scientific evidence.

The [early principle scout](principle_scout/findings.md) partially read seven original works, reusing local sources. Poke and Strike's task-informed probing supports evaluating final choices, but its physical simulator/property interventions are unavailable here. L2M's time-invariant-feature and sampling assumptions do not turn treatment responses into passive covariates. SPI-Active's excitation requirement does not identify biological parameters from cell counts. GVALID's strong-concavity/interior-dose optimum does not apply to a fixed-window compound shortlist. These sources confirmed input, utility and identifiability limits; none established a new biological learning rule. Root used fixed metadata anchors, so it did not implement or validate adaptive probe selection. This is targeted partial method reading, not an exhaustive 2025–2026 top-journal survey or universal novelty clearance.

HTS031 metadata has six distinct SCLC backgrounds and 126 common drugs with seven common physical concentrations. Forty-one plates partition drug panels; they are not 41 independent screens. Extra ranges for some drugs do not supply replicate occasions. HTS003 remains byte-identical to HTS031. Its downloaded treatment counts were not decoded, used for fitting or scored. The failed development gate leaves them untouched; a later hypothesis would require its own justified frozen protocol. Any future within-release panel test must distinguish transferring the learned fourteen-drug q values from retraining a generic procedure on 126 drugs, and neither implies independent external biology.

## Execution, verification and retained decision

The [initial challenge](review/protocol_initial.md) preceded root responses/code/results. The [code/amendment check](review/code_amendment_check.md) passed after prefit fixes to terminal failure preservation and deadline checks. Scientific settings were unchanged. Canonical direct maestro completed the one twelve-method matrix in **53.703 seconds**, 72.4375 CPU-seconds, with four threads. No environment install, paid model API, external model bridge or model rerun occurred; peak memory and agent token/cost are unmeasured.

Hill optimization reached the frozen 200-evaluation limit in 45/1,260 source-curve calls and 4/1,764 target-MAP calls. These are calls across nested fits, not distinct biological curves. Their predetermined fallback vectors/priors remained in the panel and every status was saved. No difficult task was dropped. Hill's reported score belongs to that finite-budget procedure; the candidate already loses to ordinary models without relying on Hill as the strongest rival.

The [independently authored verifier](review/verify_predictions_independent.py), frozen before outputs and without main implementation access, validated all **10,080 prediction rows**, equal task/dose menus, truth/well mapping and finite values. It independently recomputed losses, flips and gates, comparing **176 schema field groups** with root outputs. See [independent result](review/independent_metrics/summary_independent.json) and [decision](review/independent_metrics/decision_independent.json). This is same-observation arithmetic plus a separate static fitting review, not an independent biological experiment or refit audit.

The source/design work used 2 new GETs and 77,376 completed bytes; donor/prior checks reused local originals. The cumulative search allowance retains the earlier six passes; this continuation used one additional scoped pass and left the reserved final pass unused. [Usage](usage.json), [record](record.md) and [library verification](library_verify.json) retain actual scope; the library now has 181 unique papers / 151 files with zero errors/warnings. Inherited agent configurations were retained, and effective model/effort/cost metadata is unavailable.

The [independent outcome interpretation](review/outcome_initial.md) was saved before root synthesis and reached the same scoped decision. It preserves positive ablations and secondary menu utility while separating the point deficit, uncertain population inference and unattainable absolute margin.

The final [content review](review/content_review.md) passed without material corrections. The earlier challenger/outcome reviewer checked this handoff; this is not another fresh-context or outcome-blind assessment. Root's final checks confirmed the frozen hashes, unchanged comparison inputs, current registry paths and local links. This bounded stage is closed; the overall research objective remains active.

**Retained decision:** park this C2 anchor-scaled shape construction under the tested setting. Preserve ordinary calibration's useful internal secondary signal and C1's observed phenomenon. Do not revise the gate, decode HTS031 counts, claim a new learning mechanism, introduce an Agent or promote core code from this result. A different future hypothesis must change a failed premise or supply genuinely new decisive evidence rather than rename this residual model.
