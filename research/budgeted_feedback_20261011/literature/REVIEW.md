# Literature evidence for sparse, reliable, budgeted feedback

Reviewed on 2026-10-11, Asia/Shanghai. This targeted supplement addresses gaps in the [existing review](../../dual_core_scientific_20261011/literature/REVIEW.md): CV batch acquisition, NLP label scarcity, robotics feedback and transfer, and inference after candidate selection. It contains 13 verified primary-paper records, including four CV, two NLP and three robotics papers; this is the supplement's record count, not a claim of 13 new unique papers across all repository reviews. [sources.json](sources.json) records exact abstracts, authors, URLs, retrieval status, hashes, inspected scope, supported claims and limitations. The retrieval logs preserve failed and blocked requests as well as successes. Most papers were inspected at abstract level; MAP publisher HTML and relevant KnowNo HTML sections received closer inspection. This is not a systematic review or a certification of novelty.

The practical conclusion is to test a small number of feedback batches on top of the strongest existing cell-context transfer model. Ordinary active learning, EVSI, graph priors, calibration, and LLM tool use already have substantial prior art. The contribution must be a demonstrated improvement in the final biological decision after paying observation and turnaround costs, together with explicit conditions under which the policy refuses further feedback.

## Evidence from the requested fields

| Primary paper | What its evidence supports | Consequence for MAESTRO |
| --- | --- | --- |
| Yoo and Kweon, [Learning Loss for Active Learning, CVPR 2019](https://openaccess.thecvf.com/content_CVPR_2019/html/Yoo_Learning_Loss_for_Active_Learning_CVPR_2019_paper.html) | A small loss-prediction module can guide annotation across classification, detection and pose tasks. | Include a cheap predicted-error acquisition baseline. Predicted error alone is not endpoint decision value. |
| Kirsch et al., [BatchBALD, 2019](https://arxiv.org/abs/1906.08158) | Joint batch information accounts for redundancy that independent acquisition scores can miss. | Use a strong jointly selected batch comparator; compare batch sizes under explicit turnaround cost. The present source verifies the author preprint. |
| Ash et al., [BADGE, 2019](https://arxiv.org/abs/1906.03671) | Gradient embeddings combine uncertainty and diversity in batch selection. | Diversity plus uncertainty is established. Label any feature-space adaptation honestly; do not call a generic diversity heuristic an exact BADGE implementation. |
| Oquab et al., [DINOv2, 2023](https://arxiv.org/abs/2304.07193) | Curated unlabeled images and self-supervision can produce reusable frozen representations. | Reusing a frozen representation can reduce target-label demand. Training a new large vision model is not automatically cheap, and cell-image transfer requires plate/site validation. |
| Ein-Dor et al., [Active Learning for BERT, EMNLP 2020](https://aclanthology.org/2020.emnlp-main.638/) | Small-budget, imbalanced classification can benefit from active learning; initialization bias matters. | Report conditions where feedback helps: prior bias, active prevalence, uncertainty quality and effective correlation. Random and uncertainty baselines remain necessary. |
| Liu et al., [WANLI, Findings of EMNLP 2022](https://aclanthology.org/2022.findings-emnlp.508/) | LLM-generated proposals are filtered, then revised and labeled by humans; this creates useful NLP training examples. | Generation can cheaply propose hypotheses, graph assertions and assay conditions. It cannot supply missing viability outcomes. Verification remains a costed operation. |
| Ren et al., [KnowNo, CoRL 2023](https://proceedings.mlr.press/v229/ren23a.html) | Calibrated language-planner uncertainty triggers help; a sequence-level construction addresses multi-step planning. | Reliability-triggered assistance is existing work. Calibrate a fixed complete policy on matching episodes, and test decision-value-based purchases against uncertainty-triggered purchases. |
| Open X-Embodiment Collaboration, [Open X-Embodiment, 2023](https://arxiv.org/abs/2310.08864) | Standardized heterogeneous robot datasets support positive transfer across platforms. | Preserve cell, dose, time, assay and source identifiers when pooling data. Compare pooled and context-conditioned transfer, including negative-transfer cases. |
| Chebotar et al., [Closing the Sim-to-Real Loop, 2018](https://arxiv.org/abs/1810.05687) | A few real rollouts update simulation randomization and improve transfer in two robot tasks. | Sparse measured feedback can update a low-dimensional context/assay residual. The biological analogue must demonstrate actual endpoint benefit rather than simulated agreement. |

Two additional optimization references sharpen the baseline. [BOCA, ICML 2017](https://proceedings.mlr.press/v70/kandasamy17a.html) already optimizes with costly objectives and cheaper approximations. [BoTorch](https://arxiv.org/abs/1910.06403) supplies efficient Monte Carlo acquisition, variance reduction, and one-shot Knowledge Gradient. Therefore, neither mixed-cost observations nor faster EVSI estimation alone constitutes a new method.

## The requested MAP paper is verified

The normalized DOI is [10.1038/s42256-026-01286-w](https://doi.org/10.1038/s42256-026-01286-w): Feng et al., *A knowledge-driven framework for predicting single-cell responses for unprofiled drugs*, Nature Machine Intelligence. Crossref gives online publication on **2026-08-26**; the publisher citation metadata places it in the September issue. Both Crossref and the publisher returned the matching paper.

MAP-KG integrates 14 public resources, 187,089 drugs, 22,924 genes and 694,246 mechanistic relations. MAP aligns molecular structures, protein sequences and mechanistic text, then couples the learned features to a single-cell foundation model. Its two main evaluations have different meanings:

1. **Unseen cell-drug combinations:** a held-out drug remains profiled in other cellular contexts. This is directly relevant to the currently successful context-transfer direction.
2. **Unprofiled drugs:** all response profiles for held-out compounds are removed. The paper also removes held-out drug entities, aliases and incident graph relations during knowledge pretraining. This is stricter than leaving the test compound in a graph and hiding only its phenotype label.

The abstract reports improvements in top-50 DEG Pearson delta correlation and an in silico A-549 screen. These are not independent measurements of killing, selectivity, apoptosis or causal target engagement. The article's own discussion identifies computational and memory cost from gene-token interactions as a limitation.

The original [code repository](https://github.com/MAGIC-AI4Med/MAP) and [MAP-KG dataset](https://huggingface.co/datasets/RainGate/MAP-KG) were also retrieved. The dataset API lists four CSV files and roughly 97.8 MB of total stored content, with an Apache-2.0 license tag and no gating. Its card text still says the graph will be released soon, so the file listing is the more useful availability evidence. The repository recommends at least **4 TB** for its full three-dataset preparation. This review downloaded metadata and README material, not the graph payloads or those expression atlases.

The efficient first experiment is to add frozen graph descriptors to the existing context-transfer baseline, with fixed data access and budget. Compare context transfer alone, structure-only features, graph features alone, graph plus context transfer, and a degree-preserving shuffled graph. Freeze the graph snapshot and retain edge source, relation, timestamp and entity mapping. Remove endpoint-derived edges when evaluating prediction of that endpoint. Distinguish an inductive unprofiled-compound claim from a transductive experiment that permits test-compound graph information. A graph prior must never be appended to the measured-response ledger as an experimental observation.

## Reliability must follow the actual selection process

[Bao et al., Biometrika 2024](https://doi.org/10.1093/biomet/asae010), *Selective conformal inference with false coverage-statement rate control*, is closer prior art than ordinary marginal conformal prediction. Its publisher-deposited abstract describes selecting both calibration and test samples and using the selected calibration distribution. Exact FCR control is stated for exchangeable selection; nonexchangeable procedures require additional assumptions and bounds. The publisher full-text request was blocked, so this review does not claim to have inspected its proof.

These quantities must remain separate:

- Marginal coverage averages over the evaluation population.
- Selected-set coverage and active-subgroup coverage are diagnostics on important subsets, with sample counts and uncertainty intervals.
- FCR controls the expected fraction of noncovering reported intervals under a specified construction; it is not per-compound conditional coverage or simultaneous coverage of every candidate.
- Whole-policy reliability concerns the complete sequence of purchases, updates, stopping and terminal selection. Marginal one-step intervals do not automatically cover this trajectory.

KnowNo's sequence-level calibration is a useful design precedent, but its scenario distribution, assistance model and planning construction are part of its result. A biological policy cannot inherit that theorem by adding a confidence field. For MAESTRO, freeze the policy, prior, candidate menu and stopping rule before calibration; replay the same complete procedure on disjoint evaluation units. Top-k residual calibration can be an empirical safeguard, but must not be advertised as a distribution-free selected-policy guarantee without a valid matching construction.

The active-drug coverage problem also implies an operational distinction. Reliability failures in the selected region should prevent claims of certified superiority and may justify fallback to the frozen batch policy. They do not prove that every possible observation is worthless. Risk gating and value estimation answer different questions.

## A testable design and the boundary of novelty

Let the terminal utility be specified for a fixed cell background, dose, time, endpoint assay and eligible action set. For a prospective batch A, compare

`net_value(A) = E[best terminal utility after observing A] - best current terminal utility - observation_cost(A) - turnaround_cost(A) - planner_cost(A)`.

The expectation is model-based EVSI, not an observed improvement or a formal lower bound. Retain the no-purchase action. Batches share a turnaround cost, so summing independent per-point scores is not generally the right objective. For equal budget comparisons, a policy that spends on additional rounds must have correspondingly less assay capacity or explicitly pay a utility penalty; it cannot receive free extra information.

The user's reported raw adaptive gain of 0.00217 with 16 versus 1 turnarounds would imply a point-estimate break-even tariff of `0.00217 / 15 = 0.0001447` normalized utility per extra turnaround, before other incremental costs. This is an arithmetic sensitivity calculation from the user's numbers, not a reproduced result. Because the reported gain is not statistically significant, it does not establish any positive turnaround tariff that is reliably affordable. Monetary conversion requires a declared utility-to-cost scale.

The following are proposed experiments, not new established results:

| Proposed change | Established ingredients | Decisive test / failure condition |
| --- | --- | --- |
| One or two feedback batches update a context-transfer residual | Sim-to-real adaptation, transfer, Bayesian acquisition | Positive paired net utility versus the strongest tuned fixed batch on a frozen evaluation split; report the entire cost-benefit curve and the break-even tariff. |
| Reliability checks determine whether a policy can claim benefit | Selective conformal inference, risk control, KnowNo | Selected and active-stratum coverage with uncertainty; complete-policy calibration diagnostics. Failure to meet a criterion remains a failure, not a post-hoc threshold change. |
| Joint choice of observation modality, batch size and stopping | EVSI, BatchBALD/BADGE, multi-fidelity optimization | Same prior and budget, with fixed batch, one update, two updates and many updates; compare real/permuted feedback and no-feedback controls. |
| Graph prior complements cell-context transfer | MAP and cross-domain transfer | Holdout by compound/context/source; structure/no-graph/shuffled-graph controls and measured endpoint utility. No new graph benefit means the simpler transfer model stays preferred. |
| Agent proposes useful admissible experiments | BioDiscoveryAgent and LLM tool workflows in the existing review | Agent, deterministic planner and ordinary LLM tool loop receive the same tools, information, action menu, random seeds and budget. Log runtime/token cost and the distinct accepted actions. |

A defensible methods claim would be a reproducible policy that estimates which sparse feedback batches remain useful after reliability and turnaround constraints, and identifies when the fixed batch is preferable. It requires improvement over strong acquisition comparators and an explanation of the conditions driving that improvement. The ingredients listed above are established; this targeted search cannot certify that their combination is unprecedented. A statistically null result should keep the experimental method in `research/`.

## Using existing and inexpensive data

Use available data according to what they actually measure:

| Data resource/type | Useful role | Required boundary |
| --- | --- | --- |
| Existing context-matched perturbation measurements | Train and evaluate context transfer; simulate lawful budgeted purchases during replay | Previously exposed compounds remain retrospective evidence. Splitting them again does not create independent biological confirmation. |
| Public control-cell RNA or unlabeled images | Learn or reuse a representation; estimate background similarity | These provide no drug-response endpoint labels. Split by source, donor/line, plate and assay as appropriate. |
| MAP-KG and public molecular/target annotations | Frozen mechanistic prior and candidate grouping | Keep relation provenance and endpoint leakage audits; inferred or text-extracted edges are not measured phenotype. |
| Cheap morphology or a smaller targeted assay | Candidate low-cost observation modality | First demonstrate a held-out, paired bridge to the target endpoint at matching dose/time/context. A cheap assay can disagree systematically with viability. |
| A small number of true endpoint measurements | Correct context-specific bias and test feedback value | Pay their assay and turnaround costs; prevent their use before purchase during replay. |
| Synthetic cells, simulated outcomes or LLM proposals | Stress tests, policy training under labeled assumptions, experimental proposal generation | Never use them as independent measured truth or count synthetic sample size as biological replication. |

The immediate priority is a small matched panel: a few selected candidates, diverse/negative controls, and independent endpoint measurements under the intended conditions. Use existing broad resources to form priors, and spend scarce new measurements where they can distinguish competing decisions or validate the assay bridge. Independent secondary measurement must remain a separate endpoint test; transcriptomic agreement or pathway plausibility cannot repair a negative secondary result.

For efficiency, cache frozen encodings and covariance terms, fit a low-dimensional residual model first, vectorize candidate scoring, and evaluate a finite preregistered set of batch sizes. Retain compute time, memory and acquisition calls in the result ledger. Escalate model size only after evidence shows that the additional capacity improves the cost-adjusted decision.

## Retrieval audit

The initial [retrieval_log.json](retrieval_log.json) contains primary URL lookups and Crossref title/topic searches. [followup_log.json](followup_log.json) resolves WANLI, selective conformal inference, the robot transfer paper, MAP resources and DINOv2. [second_followup_log.json](second_followup_log.json) adds BoTorch and KnowNo HTML. Crossref returned 429 for two broad searches; two candidate proceedings URLs returned 404; the selective-conformal publisher request returned 403. BADGE's OpenReview URL returned HTTP 200 but served a browser-verification page, so its content is not used. A retrieved paper about choosing the conformal miscoverage level is logged but is not substituted for selected-candidate FCR inference.

Run `python research/budgeted_feedback_20261011/literature/compile_sources.py` to regenerate the inspected citation catalog from the preserved raw responses and logs. Raw source hashes identify the material actually consulted. Downloaded HTML being present does not imply that every section, supplement, experiment or proof was read or reproduced.
