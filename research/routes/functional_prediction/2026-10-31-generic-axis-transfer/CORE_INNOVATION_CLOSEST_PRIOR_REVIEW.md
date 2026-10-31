# Adversarial closest-prior review: task-sufficient transfer representation

Date: 2026-10-31 (Asia/Shanghai)
Scope: independent prior-art and falsification review of the proposed `task-sufficient transfer representation` / `intervention-sufficient minimal functional state` as a possible Virtual Cell drug-discovery core.
Boundary: this pass did not run, modify, or inspect new numerical results from the current MVP. The GAT finding is treated as a reported premise: removing shared transcriptional directions improved selective transfer correlation but did not establish a gain in choosing the most sensitive cell lines.

## Executive judgement

The broad proposal is **not yet a defensible new method**. State-conditioned perturbation representations, transfer to unseen cell types or compounds, mechanism-aware knowledge conditioning, and pathway-grounded reasoning already appear in recent work. The phrase `intervention-sufficient state` also has a close structural analogue in predictive-state representations from robotics and reinforcement learning: a state is useful when it is sufficient for predicting future observations under actions.

A narrower proposition remains potentially substantive but is **distinct and unvalidated**:

> Under a fixed measurement budget, a compact state derived from baseline and early perturbation observations is predictively sufficient for later dose/time-resolved viability and cell-selectivity decisions for intervention classes held out by mechanism or chemotype, while a full signature or GAT baseline is not.

The word `predictively` is essential. The proposed test would not establish a biological causal state. It would establish a conditional predictive capability under intervention holdouts. A causal or mechanistic claim would require additional evidence that this state is necessary for the biological process, which the available public data do not identify.

The candidate should therefore be narrowed to **decision-sufficient state with intervention/cold-start holdouts**. `Generic-axis removal`, a dual generic/specific head, a graph encoder, an LLM, and an agent are baselines or later implementation options, not the scientific claim.

## Evidence reviewed

| ID | Source | Reading scope | What it establishes for this challenge |
|---|---|---|---|
| P1 | Viñas Torné et al., *Nature Biotechnology* 2025, Systema, DOI [10.1038/s41587-025-02777-8](https://doi.org/10.1038/s41587-025-02777-8) | Official Nature HTML; abstract, Discussion, evaluation and limitations sections | Full-text evidence that systematic variation inflates perturbation metrics; Pearson/cosine-like reference-sensitive scores are strength-invariant and reference-sensitive; recommends downstream biological utility. |
| P2 | Alsulami et al., *Nature Machine Intelligence* 2026, PrePR-CT, DOI [10.1038/s42256-026-01202-2](https://doi.org/10.1038/s42256-026-01202-2) | Official Nature HTML; abstract, unseen-cell-type and unseen-perturbation results, Discussion, Evaluation and Datasets | Full-text evidence for cell-type-specific co-expression graph representations, transfer to unseen cell types and compounds, expression mean/variance prediction, R² evaluation and known batch/HVG limitations. |
| P3 | Feng et al., *Nature Machine Intelligence* 2026, MAP, DOI [10.1038/s42256-026-01286-w](https://doi.org/10.1038/s42256-026-01286-w) | Official Nature HTML; abstract, evaluation settings, zero-shot sections, knowledge-ablation section, dataset descriptions | Full-text evidence for mechanism-aware knowledge conditioning and zero-shot unprofiled-drug prediction. Held-out drugs and their knowledge-graph relations are removed to limit leakage. Endpoint remains transcriptomic, not viability decision utility. |
| P4 | Wang et al., *Nature Computational Science* 2025, CRISP, DOI [10.1038/s43588-025-00887-6](https://doi.org/10.1038/s43588-025-00887-6) | Official Nature HTML metadata/abstract only | Abstract-level evidence for foundation-model transfer to unseen cell types and cross-platform drug-response prediction. Method-level comparisons remain unresolved in this pass. |
| P5 | Adduri et al., *Cell* 2026, State, DOI [10.1016/j.cell.2026.07.052](https://doi.org/10.1016/j.cell.2026.07.052) | OpenAlex/PubMed-level abstract only; Cell full text was blocked by Cloudflare in this pass | Abstract-level evidence for perturbation prediction across cellular contexts using observational cell embeddings from 167 million cells and the Cell-Eval framework. Exact state definition, leakage controls and viability utility require full-text review. |
| P6 | Li et al., *Cell* 2026, UniPert-G2CP, DOI [10.1016/j.cell.2026.06.005](https://doi.org/10.1016/j.cell.2026.06.005) | OpenAlex/PubMed-level abstract only; publisher full text not acquired in this pass | Abstract-level evidence for bridging genetic and chemical perturbations through multimodal cause representations and phenotype transfer. It is a direct prior threat to a broad “causal intervention transfer” claim. |
| P7 | Li et al., *Science Advances* 2026, systematic comparison, DOI [10.1126/sciadv.aed3414](https://doi.org/10.1126/sciadv.aed3414) | OpenAlex abstract | Abstract-level evidence that metric choice, perturbation effect size, variance compression and cell-type transfer strongly alter conclusions; no method consistently generalizes across cell types. |
| P8 | PertReason, arXiv:2607.18777 (2026 preprint) | Full arXiv HTML, sections 3.1–3.4, 5.1, 5.4 and A.2.2; no formal peer-reviewed version verified | Preprint evidence for cell-state-conditioned graph gating, OOD perturbation/context splits and separate outcome/mechanism metrics. The authors explicitly state that curated paths are mechanistic proxies rather than exhaustive causal ground truth. |
| P9 | Bai & Su, *Bioactive Materials* 2025, AIVOs review, DOI [10.1016/j.bioactmat.2025.12.030](https://doi.org/10.1016/j.bioactmat.2025.12.030) | OpenAlex abstract | Review-level architecture claim: virtual cells are minimal executable units inside organoid-scale digital twins; multimodal longitudinal observations, virtual instruments and cell-cell/cell-matrix/transport modules are required. This is a design reference, not evidence that any candidate works. |

The search was targeted rather than exhaustive. It used OpenAlex and official publisher pages on 2026-10-31, with exact-title/DOI recovery for the listed papers. A no-hit search for the exact phrases `sufficient state`, `predictive state` and `sufficient representation` combined with single-cell/perturbation/drug response did not identify a direct high-relevance 2025–2026 paper. This is only a `Not found in the searched scope` result, not a novelty proof.

## Exact comparison with PrePR-CT

PrePR-CT is the strongest recent same-field nearest neighbour inspected in full. It uses cell-type-specific gene co-expression graphs as an inductive bias and a graph-attention model to predict post-perturbation expression mean and variance. Its tests include leave-one-cell-type-out and leave-one-compound-out settings, across five single-cell datasets, one bulk dataset and a LINCS subset. It reports R² and explicitly argues that Pearson correlation misses magnitude.

The proposed state is therefore not new merely because it is a state representation, is graph-based, is cell-type-conditioned, or transfers to an unseen compound/cell type.

| Dimension | PrePR-CT | Proposed decision-sufficient state |
|---|---|---|
| Research object | Cell-type-specific transcriptomic response distribution (mean/variance) | A compact state that is sufficient for a later drug-discovery decision |
| Input | Cell-type co-expression graph and perturbation information | Baseline plus early perturbation observations, with the measurement budget declared |
| Holdout | Unseen cell types and compounds, mostly within the reported data regimes | Entire mechanism/target family or chemotype held out, plus assay/platform transport |
| Target | Expression mean/variance and DEG-oriented prediction | Viability magnitude, selective profile and top-k cell-line/compound choice |
| Minimality | Not the central claim; graph representation has many genes/edges | Explicit state-dimension or measurement-budget curve and removal test |
| Uncertainty/refusal | Not the central validated output | Required support score, calibrated interval and refusal when transport is unsupported |
| Mechanistic claim | Interpretable attention, not causal identification | Only predictive sufficiency may be claimed; biological causality remains untested |
| Practical value | Better transcriptomic response prediction | Fewer or better-chosen viability assays under a fixed budget |

The difference is substantive only if the final four rows are tested and hold. Reusing a GAT, graph attention network, PCA, contrastive encoder or foundation model without those task-level tests would be a domain adaptation, not a core innovation.

## Closest-prior threats and what survives

### Systema: evaluation correction is necessary but not sufficient

Systema shows that perturbation-response metrics can be dominated by systematic variation and that reference-sensitive metrics do not measure perturbation strength. This directly weakens any claim based only on GAT's selective Pearson correlation. A candidate state must report both direction and magnitude and must be judged by the downstream selection decision. Systema does not itself provide a viability-oriented minimal state, so it is a necessary evaluation prior rather than a complete replacement.

### PrePR-CT and State: state-conditioned transfer is already a recognized capability

PrePR-CT gives a concrete graph-based state-conditioned transfer method and tests unseen cells and compounds. State (abstract-level in this pass) extends the same problem to broad cellular contexts and a large observational embedding corpus, with a dedicated evaluation framework. A proposed state therefore cannot claim novelty from better embeddings or unseen-cell transfer alone. The remaining possible difference is the object of sufficiency: a compact state that preserves a prospective viability decision under mechanism-cold-start and assay transport.

### MAP and UniPert-G2CP: mechanism-aware zero-shot transfer is already occupied

MAP's full methods page defines two zero-shot settings and removes held-out drugs and their relevant knowledge-graph relations during pretraining. It integrates molecular structure, protein sequence, text and a single-cell foundation model. UniPert-G2CP's abstract describes genetic-to-chemical phenotype transfer through multimodal intervention representations. A broad claim that “knowledge graphs or target information enable causal zero-shot virtual-cell prediction” overlaps these works. The candidate must either use an exact new estimand (selective viability decision) and stricter target-family/chemotype cold-start, or be dropped as prior-owned.

### PertReason: state-conditioned mechanism reasoning is a preprint prior

PertReason is not peer-reviewed evidence in this review, but it is a material novelty threat. It gates a global regulatory graph by basal cell state and evaluates both perturbation outcomes and pathway connectivity under OOD context/mechanism splits. Its authors caution that curated paths are proxies, not true causal ground truth. The proposed state can remain distinct only by being a small, experimentally measurable predictive state for future viability decisions, rather than a graph-gated reasoning or language output. It must cite PertReason as a close preprint and must not claim that cell-state-conditioned mechanistic reasoning is unexplored.

### Predictive-state representations: the structural idea is not new

Predictive-state representations in robotics/RL define state by statistics of future observations conditioned on action histories. That is the same abstract pattern as “a state sufficient for future cell response under an intervention.” The biological contribution cannot be a new general state theory. The defensible difference is an operational biological estimand, realistic intervention holdouts, minimal measurement budget and a drug-discovery decision endpoint.

### CV/NLP transfers: residualization and dominant-axis removal are prior methods

GAT's all-but-the-top/PCA-like projection has direct precedents in NLP embeddings, image retrieval and genomic unwanted-factor correction. A task-sufficient state cannot be rescued by renaming this projection, adding a contrastive loss, or using a larger encoder. Those are implementation choices and should be ordinary baselines.

## Candidate revision and deletion decisions

1. **Keep, but narrow:** `decision-sufficient state with intervention/cold-start holdouts`.
2. **Demote to baseline:** generic-axis removal, generic-plus-specific dual heads, graph attention, contrastive learning, kernel ridge, foundation-model embeddings and target-knowledge graph conditioning.
3. **Remove from the core claim:** “causal state”, “mechanistic state”, “virtual cell understands mechanism”, and any claim that a correlation gain proves a cell-death mechanism.
4. **Defer:** organoid, agent, autonomous experiment selection and any `AIVO` claim until the state interface passes an independent external decision test.
5. **Do not rescue a failed state candidate by stacking the demoted components.** A failure under mechanism holdout is evidence against the proposed capability, not a request for a larger architecture.

## Minimal falsifiable experiment

This is a planned test, not an executed result.

### Frozen question

Can a compact state, computed from baseline and early perturbation observations, predict later viability and selective cell-line choice for compounds from a mechanism or chemotype family absent from training?

### Information boundary

Fit every transformation using reference compounds only. Do not use the held-out compound's outcome, target label or response profile. If a target/MOA annotation is used for a split, freeze the mapping before reading the held-out outcome. Keep an external assay/platform untouched until the final gate.

### Minimum arms

- `R0`: current raw transfer rule.
- `R1`: promoted GAT configuration.
- `R2`: full-signature ordinary supervised baseline (ridge/PLS with honest fold refits).
- `R3`: sparse or low-rank state model with the state dimension selected only on development data.
- `R4`: generic-plus-specific two-channel baseline, if needed to test whether the “state” is only variance partitioning.
- `R5`: chemical/target or knowledge-conditioned baseline where the needed annotations are available.

A foundation model is optional and should not replace these ordinary baselines.

### Splits

Use nested development/confirmation splits with, in priority order:

1. entire target/MOA families or intervention mechanisms held out;
2. scaffold or chemotype families held out;
3. an independent assay/platform or dose/time regime;
4. cell-line or context holdout where the data support it.

Random compound splits can be reported as diagnostics but cannot support the core claim.

### Endpoints

- Later viability magnitude: MSE/MAE or a pre-specified calibration metric.
- Selective profile direction and magnitude: a Systema-style residual metric plus a magnitude-sensitive metric.
- Drug-discovery decision: top-​k sensitive cell-line recall, regret of the best untested line, hit enrichment and performance under a fixed assay budget.
- State minimality: performance versus number of state dimensions or measured features, stability across outer folds, and a removal test. If the state needs almost all genes/features, call it a representation, not a minimal state.
- Transport support: coverage-risk or conformal coverage, with a refusal option. A high score obtained by silently extrapolating outside support fails the practical test.

### Strongest competing explanations

- The gain is ordinary low-rank regularization or shrinkage.
- The gain comes from more neighbours, reference density or a hidden tuning difference.
- The held-out mechanism is represented by near-duplicate chemistry or target labels.
- The residual endpoint or generic profile was constructed using held-out information.
- The state merely predicts transcriptomic magnitude and has no value for viability selection.
- The state is unstable across assays, doses or cell types and therefore cannot be transported.

### Pass condition

A candidate may be called a Virtual Cell core only if all of the following are pre-registered and met:

- it improves a decision endpoint against the strongest ordinary rival, not just a correlation metric;
- the improvement is reproduced on at least two independent domains or one domain plus a strict mechanism/chemotype cold-start set, with uncertainty excluding no benefit;
- it does not materially degrade viability magnitude or calibration;
- the compact state is stable and substantially smaller than the full input, or the contribution is explicitly relabelled as a non-minimal representation;
- it has an explicit support/refusal behavior, and an independent verifier reproduces the result without the run code.

### Stop conditions

Stop and park the candidate if any of these holds:

- only Pearson/selective-r improves while top-k assay decisions do not;
- improvement disappears under mechanism-family or chemotype holdout;
- ordinary ridge/PLS or a fixed GAT residual baseline reaches the same decision utility;
- the state is not compact or changes substantially across folds;
- confidence/refusal is uncalibrated on shifted data;
- a required external domain lacks the data needed to test the claim.

## Scientific judgement

The current closest-prior review does not justify a “new state representation” claim. It does justify a narrower research question: whether drug-discovery decisions can be supported by a compact, transportable, intervention-conditioned functional state, tested under mechanism-cold-start and magnitude-sensitive endpoints. This is a high-risk, potentially high-value candidate. Its value would come from making a previously unreliable decision testable under a declared measurement budget, not from a new neural architecture.

If the minimal test fails, the correct conclusion is still useful: static transcriptional state is insufficient for the proposed viability decision under the chosen information boundary, and future Virtual Cell work must add temporal, multimodal or spatial information. That negative result should close the line rather than trigger architecture stacking.

## Coverage limits

- The review is targeted to nearest-prior threats, not an exhaustive survey of all 2025–2026 virtual-cell literature.
- CRISP, State, UniPert-G2CP and Science Advances benchmark evidence is abstract-level in this pass, so exact split and implementation claims remain unresolved.
- PertReason is a 2026 arXiv preprint; its full HTML sections were read, but peer-review status and biological ground truth remain unverified.
- No author code was executed, no weights were downloaded, and no current MVP response cells or new numerical fits were read.

## Critical clarification from coordination review

The current GAT pilot receives an L1000 signature for each query compound. It predicts an unmeasured viability profile; it does **not** perform truly unprofiled-drug zero-shot prediction. Therefore, the proposed state candidate must not claim zero-shot prediction from molecular structure alone, and must not inherit MAP's unprofiled-drug terminology unless a separate structure-only experiment is run.

Likewise, projecting 978 genes or observed condition slots into a PCA/low-rank state is representation or storage compression, not a reduction in experimental measurement cost. A claim of a smaller measurement budget requires a pre-declared subset of genes, time points, conditions or assays that are actually omitted at inference and whose missingness is realistic. The minimal first claim is consequently:

> Given an early perturbation readout that is already measured, is a compact state sufficient for a later functional decision on intervention classes absent from training?

The decisive test must include action-conditioned equivalence or challenge cases. It cannot be a single-endpoint compression exercise. A state that produces the same predicted viability profile from different early interventions is only useful if those interventions also agree under the future action/query relevant to the decision; otherwise the representation has merged distinguishable futures. This is a planned next experiment, not evidence supplied by the current GAT pilot.

## Cross-field falsification: state abstraction already has an action-conditioned criterion

A 2026 arXiv theory paper, *Compositional Behavioral Semantics for State Abstraction in Reinforcement Learning* (arXiv:2606.25357; full HTML sections 2–4 and F.4 inspected), makes the relevant warning explicit. A model-irrelevance abstraction requires states mapped to the same representation to have the same observation and transition distributions for **all actions**. MDP homomorphism further separates the state map from the action-interface map. This is a stronger and more precise prior than an ordinary embedding similarity test.

For a cell model, the analogous challenge is not simply whether two compounds have similar early signatures or similar predicted viability. It is whether two observations assigned to the same state remain equivalent under the future interventions used in the decision: dose changes, follow-up perturbations, combinations, washout or time extension. If they diverge under an allowed action, the state has merged distinguishable futures and is not intervention-sufficient for that task.

This cross-field prior changes the minimum experiment. Add an action-conditioned equivalence challenge with paired or compositional interventions, where the same early-state bin is followed by different future actions and the model must predict the different outcomes. A one-endpoint held-out viability test cannot establish sufficiency. The proposed biological state is therefore an operational task abstraction, not a new state-abstraction theory.

## Candidate disposition after the prior check

| Candidate | Closest-prior status | Keep or discard | Reason |
|---|---|---|---|
| Generic-plus-specific dual response heads | Close/incremental | Keep only as a baseline | It tests whether GAT discarded useful overall killing magnitude, but factorizing a response is ordinary multi-task/low-rank modelling. It becomes scientific only if the decision endpoint changes under mechanism cold-start. |
| Mechanism/knowledge-conditioned zero-shot transfer | Overlaps strong prior | Do not use as the default core | MAP and UniPert-G2CP already occupy mechanism-aware compound/intervention transfer. A viability/selectivity endpoint and stricter target-family holdout could reopen it, but the prior check must come first. |
| Dynamic early-state to later fate/commitment | Close, high prior risk | Keep as a second route | CellFlow, ARTEMIS and RegVelo already cover temporal or regulatory dynamics. The only defensible difference is a decision-relevant commitment prediction with a measured viability endpoint, not trajectory interpolation. |
| Support-aware transport and refusal | Useful capability, weak standalone novelty | Keep as a reliability gate | CRISP, State and cross-dataset benchmarks establish context-transfer difficulty. Calibrated refusal can make the tool safer, but ordinary confidence scoring is not a core innovation. |
| Intervention/decision-sufficient minimal functional state | Distinct but unvalidated | Main candidate for one MVP | The exact object combines compactness, action-conditioned future equivalence, mechanism/chemotype cold-start and viability decision utility. It has strong prior threats and may fail; that is why it is worth a bounded falsification test. |

The table is a research disposition, not a novelty score or a claim that the surviving candidate is new. The final status remains conditional on the planned experiment and a fresh closest-prior review after any material implementation change.
