# Deliverable A: literature map and novelty audit

## How deeply each work was read

This is a 2026-10-13 desk review, and the depth of reading varies by source:

* **Abstracts, search summaries and project pages, read this session:** PRESAGE, TxPert, Systema,
  Ahlmann-Eltze et al., DrEval, the Specification Game, TransCDR, scPertEval, PertEval-scFM,
  LLM-AutoSciLab, BioDiscoveryAgent, Robin, DeepTarget, Pabon et al., Caranzano et al., Bonner et al.,
  the Model-X papers, PRCD-MAP, Gene-GeoFlow, Mechanisms Matter, Perturbation Response
  Decomposition, VCWorld and FORGE.
* **Records from earlier MAESTRO blocks** (`research/context_discrimination_20261013/literature_sources.json`
  and the knowledge-reality README): MAP / MAP-KG (we hold its release and KG locally), PIE and
  GeneAgent.
* **From background knowledge, not re-read this session:** Co-Scientist, the CMap/L1000 paper,
  decision-focused learning, OOD calibration and Bayesian experimental design.

No full text was read end to end. "Not reported" below means not reported in what was read. A
claim of novelty against a work is only as strong as this reading.

## 1. Knowledge-conditioned perturbation prediction

| Work | What it does | Knowledge it uses | What it implies for us |
|---|---|---|---|
| GEARS (Roohani et al., Nat Biotech 2023) | GNN over GO and co-expression graphs; predicts unseen genetic (incl. double) perturbations | GO and co-expression graphs | The reference knowledge-graph prior. Later benchmarks show that linear baselines match it. |
| PRESAGE ([bioRxiv 2025.06.03.657653](https://www.biorxiv.org/content/10.1101/2025.06.03.657653.full.pdf)) | Gene embeddings from many knowledge sources, attention aggregation, functional metrics | Many; the strongest is cross-system Perturb-seq | Measured perturbation data dominates curated knowledge. Not reported: source ablations against relabelled sources. |
| TxPert ([arXiv 2505.14919](https://arxiv.org/pdf/2505.14919v1.pdf)) | Basal encoder plus GNN perturbation encoder over several graphs (STRING, GO, PxMap, TxMap); OOD singles, doubles and lines | Curated graphs plus graphs built from perturbation screens | Graphs from screens help most. Introduces stricter baselines and ceilings. Not reported: identity relabelling. |
| MAP / MAP-KG (Feng et al., Nat Mach Intell 2026) | KG of 694k drug-gene relations aligned with structure, protein and text; conditions a single-cell foundation model for unprofiled drugs | Curated DBs plus ChEMBL assay text | The drug-side knowledge source we hold locally. Not reported: relabelling controls. |
| PIE (Verma, Adduri, ..., Roohani, bioRxiv 2026-10) | Population-level genetic effects from external knowledge, baseline expression and observed responses | External knowledge plus observed responses | Same family. Recorded in earlier blocks, not re-read. |
| VCWorld (arXiv 2512.00306, ICLR 2026) | White-box simulator: KG plus stepwise LLM reasoning; gene-centric benchmark | KG plus LLM | Agent-style. Its interpretability rests on KG identity, which is exactly what relabelling tests. |
| LPM, X-Pert, PertOmni (2025) | Shared embedding spaces for chemical and genetic perturbations | Perturbation data, LLM text embeddings | Closest to genetic-to-pharmacological transport. LPM clusters drugs with knockdowns of their targets. |
| FORGE (bioRxiv 10.1101/2025.09.04.674143) | Joint matrix factorisation of DepMap dependency, expression and drug response; a "Benefit Score" | CRISPR dependency | Brief 5's question: does dependency inform drug response? Our dependency data are absent (needs authorisation). |
| DeepTarget (Sinha, Sinha, Ruppin; bioRxiv 2022, npj Precis Oncol 2025 per a newsletter) | Drug–knockout similarity (Pearson, across lines) to infer primary and secondary targets | DepMap CRISPR and drug screens | Identity-based genetic-to-pharmacological linkage, used for target inference rather than prediction. |
| Pabon et al. (PLoS Comput Biol 2018) | Ranks targets by matching compound L1000 signatures to knockdown signatures; top-100 accuracy 41% on 152 drugs | L1000 KD/OE | On L1000, KD-to-compound similarity carries target identity at the retrieval level. Our task asks whether it carries it at the signature-prediction level. |
| CMap / L1000 (Subramanian et al., Cell 2017) | The resource; shRNA consensus gene signatures (CGS) | — | Same-gene shRNA pairs were only slightly more similar than random, while shared-seed pairs were much more similar. So CGS signatures carry strong off-target, generic structure. |

## 2. Transport, decomposition and evaluation of perturbation models

| Work | Finding relevant to identity |
|---|---|
| Systema ([Nat Biotech 2025](https://doi.org/10.1038/s41587-025-02777-8)) | Methods rarely generalise beyond systematic variation (the perturbed-vs-control shift). Common metrics overstate performance. Systema evaluates perturbation-specific effects only. **Our analogue removes generic structure from the knowledge contribution rather than from the outcome.** |
| Ahlmann-Eltze, Huber, Anders ([Nat Methods 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12328236/)) | No deep model beat additive or linear baselines on unseen single and double perturbations. |
| PertEval-scFM ([ICML 2025](https://proceedings.mlr.press/v267/wenteler25a.html)) | Foundation-model embeddings add little over simple baselines, especially under distribution shift. |
| scPertEval (Schäfer et al., bioRxiv 2026; [PyPI](https://pypi.org/project/scperteval)) | Evaluation taxonomy: representation, metric, score transformation and reporting. |
| Mechanisms Matter (ICML 2026) | Causal transportability: no model generalises across contexts whose mechanisms differ. Semi-synthetic Perturb-seq simulator; a Vendi diversity diagnostic. |
| Perturbation Response Decomposition (bioRxiv 2026, 10.64898/2026.07.24.740459) | Responses split into global, perturbation, cell-line and interaction parts. Coessentiality priors align with response geometry. Simple linear or MLP models win. |
| Gene-GeoFlow ([arXiv 2608.06824](https://arxiv.org/pdf/2608.06824)) | Shuffled gene geometry matched learned gene IDs (Pearson delta 0.44 vs 0.40); aligned geometry 0.82. One dataset, used as an ablation only. |

## 3. Drug response evaluation

| Work | Finding |
|---|---|
| DrEval (Bernett et al., [Nat Commun 2026](https://doi.org/10.1038/s41467-026-72903-w)) | Deep models barely beat a naive mean drug-plus-cell-line effect model. None beats tuned tree ensembles in relevant settings. Calls out leakage, pseudoreplication, biased metrics and missing ablations; provides application-aware splits. |
| Specification Game (Codicè et al., [J Cheminf 2025](https://doi.org/10.1186/s13321-025-00972-y)) | Standard evaluation is gamed by dataset bias. Proposes Global, Fixed-Drug and Fixed-Cell aggregation, and AUDRC over IC50. |
| TransCDR ([BMC Biol 2024](https://doi.org/10.1186/s12915-024-02023-8)) | Cold-scaffold and cold-drug splits. Gains come from chemical pretraining; ECFP and mutation features matter most. |

## 4. Controls for knowledge priors

| Work | Finding |
|---|---|
| Caranzano et al., "Sparsity is all you need" ([arXiv 2505.04300](https://arxiv.org/pdf/2505.04300), Brief Bioinform) | 29 pathway-informed networks against structure-matched random counterparts: randomised versions performed as well, and in 3 of 15 models better. The benefit is attributed to sparsity, not biology. |
| Esser-Skala and Fortelny (npj Syst Biol Appl 2023) | Node-level interpretations of biology-inspired networks are unstable and biased by the knowledge used. |
| Bonner et al. ([arXiv 2112.06567](https://arxiv.org/abs/2112.06567v1)); Sosa et al. 2024 | Degree imbalance drives drug-discovery KG predictions, so hub nodes win. |
| MAESTRO knowledge reality (2026-10-13) | On PRISM viability, a knowledge gain of +0.0056 r survived gene relabelling within strata (p 0.95). The gain was mechanism-class membership, not target biology. |

Common pattern: every control in this literature is a **diagnostic run after the fact**. Model
behaviour does not change when the control fails.

## 5. Statistical falsification machinery

* **Model-X knockoffs and the CRT.** Candès et al. ([arXiv 1610.02351](https://arxiv.org/pdf/1610.02351)).
  * Null copies of a feature drawn from its conditional distribution give exact tests of
    conditional importance.
  * The tests are global (per feature), not per query, and do not decide how a predictor uses a
    feature.
  * Robustness: Berrett et al. 2020 (conditional permutation test). Power: Wang and Janson 2020.
* **Permutation "proof by contradiction"** ([arXiv 2601.06704](https://arxiv.org/html/2601.06704v1)).
  A model should fail on permuted labels. This is a diagnostic.
* **PRCD-MAP** ([arXiv 2605.01669](https://arxiv.org/pdf/2605.01669)). Learns one global trust
  level for an imperfect prior in causal discovery. The trust is not per query and not supervised
  by falsification.

## 6. Agents and closed-loop discovery

| Work | Finding relevant here |
|---|---|
| Robin ([arXiv 2505.13400](https://arxiv.org/pdf/2505.13400)) | Multi-agent loop; ripasudil raised RPE phagocytosis in vitro. The agent's analysis said 7.5-fold, the human analysis 1.75-fold, a gap that shows why verification must be separate from generation. |
| Co-Scientist (Gottweis et al., 2025) | Generate–debate–evolve; AML repurposing and fibrosis targets with wet-lab follow-up. |
| BioDiscoveryAgent (ICLR 2025) | +21% over BO baselines on gene-hit discovery. The gain is concentrated in early rounds, where LLM prior knowledge substitutes for data. |
| LLM-AutoSciLab ([arXiv 2605.24043](https://arxiv.org/pdf/2605.24043)) | Hypothesis-conditioned experiment selection on ActiveSciBench; 2–5× sample efficiency, self-reported. |
| GeneAgent (Nat Methods 2025) | Self-verification against domain databases. |

MAESTRO's own record: blocks P, Q and the triage studies found agent loops null or harmful
relative to fixed workflows. Brief 6 forbids paid LLM work until a method shows independent value.

## 7. Decision theory

* **Decision-focused learning** (Elmachtoub and Grigas, "Smart predict-then-optimize"). Trains
  predictors for the downstream decision loss.
* **Bayesian experimental design** (Rainforth et al., Stat Sci 2024). The value of information
  decides which experiment to run next.
* **OOD calibration and selective prediction** (Ovadia et al. 2019; Geifman and El-Yaniv 2017;
  conformal prediction). A per-query trust score must be calibrated under shift. Our block Q
  certificate is of this kind: it predicts per-route accuracy.

## 8. Novelty audit for the selected idea

The selected idea is in [CANDIDATES.md](CANDIDATES.md): orbit-contrast evidence admission (OCEA).
It has two parts:

1. **Orbit decomposition.** Split a knowledge-conditioned prediction into:
   * its mean over a stratum-preserving relabelling orbit of the knowledge (the generic part);
   * the residual (the identity part).
2. **Falsification-calibrated admission.** Admit the identity part per query, weighted by a model
   trained to predict the identity contrast. The identity contrast is the route's accuracy with
   real knowledge minus its mean accuracy over the orbit.

| Closest prior | Overlap | Difference |
|---|---|---|
| Randomised-graph and relabel controls (Caranzano; Gene-GeoFlow; knowledge reality) | Same null family | They are diagnostics. OCEA makes the null part of the estimator: the orbit mean enters the prediction as a credited generic term, and the null contrast is the training target. |
| Model-X CRT and knockoffs | Null copies from a conditional distribution | Their unit is a global test per feature. OCEA's unit is a per-query decomposition plus admission, with no finite-sample guarantee claimed. |
| Systema; Perturbation Response Decomposition | Remove systematic or generic structure | They decompose the outcome or the evaluation. OCEA decomposes the contribution of knowledge to a prediction. |
| Block Q certificate; selective prediction | Per-query trust | The block Q certificate predicts route accuracy. OCEA predicts identity contrast, which can be zero for an accurate route whose accuracy is generic. |
| Mixture of experts, gating, PRCD-MAP | Learned trust weights | Their supervision is accuracy, or one global trust level. |
| Group averaging (Reynolds operator) in invariant learning | The same operator | It is used there to build invariant models. OCEA uses it to isolate the non-invariant part and to price it. |

**Honest novelty claim.** Every component exists: permutation nulls, group averaging, learned
gating. The new part is the inference rule: "credit and use knowledge only through its orbit
residual, admitted per query by a model trained on falsification contrasts".

* Nothing found implements this rule.
* The search was keyword-based (see the depth note above). A work outside these queries could
  overlap.
* If the rule does not beat its own ablations (unconditional residual, accuracy-supervised gate),
  it is not a methodological contribution. At most it would be an evaluation device.
