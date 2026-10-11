# Block P literature review: what to adopt, adapt or reject

Searched 2026-10-11 (web search, abstracts and author pages; full texts only where open). Each
entry records:
* the claimed contribution;
* what transfers to MAESTRO;
* the assumptions that may not hold;
* overlap with this block;
* the decision.

Only primary sources are cited for numbers. Where only a secondary summary was reachable, the
entry says so.

## 1. The task and its closest prior art

**Corsello et al. 2020, Nature Cancer 1:235** (PRISM Repurposing; 4,518 drugs x 578 lines).
* Many non-oncology drugs selectively kill subsets of lines, predictably from molecular features.
  Examples: PDE3A-SLFN12 complex stabilisers, vanadium via SLC26A2, disulfiram with low
  metallothionein, tepoxalin via ABCB1.
* *Use:* defines the endpoint and shows that selective killing is a real, mechanistically
  diverse phenotype, not only an oncology-drug property.
* *Limit:* the 2.5 uM primary screen is single-dose; we check hits against the independent
  secondary dose-response screen.

**DeMeo et al. 2025, Science (10.1126/science.adi8577), "Active learning framework leveraging
transcriptomics identifies modulators of disease phenotypes"** (DrugReflector).
* A model trained on Connectivity Map signatures ranks compounds for a phenotypic screen.
* A lab-in-the-loop step refines the target signature from the hits and non-hits of a round.
* Reported: a 13-17x hit-rate gain over random across two haematological campaigns, and a further
  2x from refinement (abstract and lab summary only).
* *Overlap: high.* Transcriptomic profiles plus active learning for phenotypic hit-finding is
  their contribution, not ours.
* *Difference:*
  * They target one phenotype in one cell system. Our phenotype is context-selective killing
    across hundreds of lines, inferred from L1000 in only 5-7 lines, so the virtual cell must
    transfer across contexts.
  * They compare against their own baselines. We compare whole-system arms (fixed workflow,
    deterministic planner, agent with and without the virtual cell, conventional LLM+world model)
    on untouched compounds, with a feedback-permutation control.
* *Decision:* cite as the closest prior art; do not claim the active-learning loop as novel.

**Moshkov et al. 2023, Nature Communications** (16,170 compounds, 270 assays).
* Chemical structure, Cell Painting and L1000 profiles each predict 6-10% of assays well, and
  21% in combination.
* *Use:* modalities are complementary. Hence our stacked world model over transcriptional,
  chemical, target and annotation evidence, rather than a single predictor.

**Hafner et al. 2017, Nature Communications** (L1000 + growth across ~600 drug-line pairs).
* Chaperone and cell-cycle inhibitors induce similar transcriptional changes across lines.
* Signalling-kinase inhibitors induce line-specific changes, and transcription can change
  without growth effects.
* *Implication:* transcriptional similarity is not killing similarity. The virtual cell's
  transfer must be validated on killing, which block N did, and its failures detected per
  campaign.

## 2. Virtual cells and their critiques

**Ahlmann-Eltze, Huber & Anders 2025, Nature Methods 22:1657.**
* Five foundation models and two other deep models do not beat no-change or additive baselines
  for transcriptome responses to genetic perturbation.
* *Use:* every virtual-cell arm here is benchmarked against non-transcriptional transfer
  (chemistry, targets, class mean) and a zero arm.
* MAESTRO's own history agrees: STATE lost to basal-similarity transfer (phenotype anchor) and to
  a CCLE prior (block K).

**PRESAGE (bioRxiv 10.1101/2025.06.03.657653).**
* Gene embeddings from about 40 knowledge sources (GO, Reactome, STRING via node2vec; ESM and
  BioGPT via PCA), trained on Perturb-seq for genetic perturbations.
* Evaluated by functional virtual screens, not only expression error.
* *Transferable idea:* evaluate a virtual cell by the decisions it supports (functional
  evaluation), which this block does with hit yield.
* *Not adopted:* the model covers genetic perturbations, while our perturbations are compounds.

**VCWorld (Wei et al., ICLR 2026, arXiv 2512.00306).**
* An LLM-driven "white-box" simulator reasons stepwise over structured knowledge to predict drug
  perturbation responses, and claims state-of-the-art results on drug benchmarks.
* *Assumption that fails here:* that LLM mechanistic reasoning carries the response signal. In
  block N, mechanism-based LLM judgement discarded the cross-mechanism neighbours that carry
  the signal (critic -0.052).
* *Decision:* not adopted as a world model. An LLM prior is tested only as a gated expert.

**MultiVCDiff.**
* Not found under that name. The closest are StateXDiff (2026; RNA plus inferred protein,
  conditional diffusion), PerturbDiff (2026; distribution-level diffusion) and AROMA (2026;
  text+graph+sequence, genetic perturbations).
* *Decision:* not adopted. Distribution-level single-cell generation is not needed for a bulk
  viability endpoint, and the training cost is outside this block's constraints.

**STATE (Arc 2025) and the Virtual Cell Challenge 2025.**
* Per secondary coverage, MAE could be gamed by mean prediction, which prompted a separate
  generalist prize.
* *Use:* report decision metrics and include a no-change/generic arm, never MAE alone.

## 3. Agents for experimental design

**BioDiscoveryAgent (Roohani et al., ICLR 2025).**
* An LLM agent proposes genes per round of a CRISPR screen, with literature, code and critique.
* It claims +21% hits over Bayesian-optimisation baselines across six datasets.
* *Assumption:* the LLM's prior over gene relevance is informative, which holds for well-studied
  phenotypes.
* *Our finding so far:* LLM knowledge roles were null or harmful in blocks M and N.

**Gupta, Hartford & Liu 2025, Findings of EMNLP (arXiv 2509.21403).**
* LLM design agents were insensitive to experimental feedback: permuted outcomes did not change
  their performance.
* Linear bandits and GPs outperformed them.
* A hybrid (LLM prior + nearest-neighbour sampling, "LLMNN") was competitive.
* *Adopted as controls:* every agent arm gets a feedback-permutation twin. The LLM is used, if at
  all, as a prior inside a statistical acquisition loop, not as the selector.

**CALIPER (arXiv 2606.01730, 2026).**
* Evidence-gated LLM priors: expert weights are updated online from observed objectives and
  discounted over time.
* LLM self-reported confidence was not reliably beneficial.
* *Overlap:* our arbitration of evidence sources by in-campaign feedback is the same principle.
  We do not claim it as new; we test whether it matters biologically.

**AI co-scientist (Gottweis et al. 2025, arXiv 2502.18864).**
* AML repurposing from 2,300 approved drugs; 3 of 5 initial candidates and KIRA6 inhibited AML
  line viability in vitro.
* *Limit:* a handful of candidates, no fixed-workflow comparison at equal budget.

**Robin (FutureHouse 2025, arXiv 2505.13400).**
* Multi-agent hypothesis generation plus data analysis; ripasudil increased RPE phagocytosis
  7.5x in vitro.
* *Limit:* no matched-budget comparison with a deterministic workflow.

**Biomni (Huang et al. 2025, bioRxiv 2025.05.30.656746).**
* A general tool-using agent: 150 tools, 105 packages, 59 databases.
* Independent BixBench accuracy is about 50% (secondary source).
* *Use:* tool breadth is not the bottleneck here; the decision loop is.

**GeneAgent (Wang et al. 2025, Nature Methods 10.1038/s41592-025-02748-6).**
* Self-verification of LLM claims against curated databases reduced hallucination in gene-set
  naming.
* *Adopted principle:* agent claims are verified against an independent source. Here, every
  reported hit is checked against the secondary screen, and only evidence-supported sources keep
  weight.

**CellWhisperer (Schaefer et al. 2025, Nature Biotechnology 10.1038/s41587-025-02857-9).**
* Contrastive transcriptome-text embedding for chat-based exploration.
* *Not adopted:* it is single-cell annotation, not perturbation-response prediction.

## 4. Robotics and sequential decision-making

**Active search (Garnett et al. 2012; Jiang et al. ICML 2017; NeurIPS 2018 batch).**
* Maximise the number of positives found under a labelling budget.
* Greedy one-step search is the baseline. Efficient nonmyopic search (ENS) adapts exploration to
  the remaining budget.
* Drug discovery is the canonical application.
* *Adopted:* the campaign objective (hits found) and greedy/batch acquisition. ENS is a candidate
  planner refinement if F2 shows exploration matters.

**POMCP (Silver & Veness 2010).**
* Monte-Carlo tree search over beliefs in POMDPs.
* *Not adopted at this stage:* with a known reveal model (screening reveals the profile),
  nonmyopic active search covers the relevant planning. Belief-space MCTS was tried in MAESTRO
  before (belief planning, 2026-09-27) without a gain over fixed policies.

**DreamerV3 (Hafner et al. 2023/2025).**
* Learn a world model and plan in imagination.
* *Analogy only:* our world model is learned in-context per campaign; no policy is trained in
  imagination, because campaigns are few and the reveal model is exact.

**SayCan (Ahn et al. 2022).**
* Language proposes; a learned value grounds it in what is feasible.
* *Adapted:* the LLM may propose (a prior over compounds), but the virtual cell and the
  in-campaign evidence decide (gated weight). Block N showed the reverse arrangement, the LLM
  filtering the world model, is harmful.

**Imaging (JUMP Cell Painting, CellCLIP 2025, JUMP-lite 2026).**
* Morphological profiles are the other cheap, scalable modality for perturbation similarity.
* *Not used:* no Cell Painting profile is local for these PRISM compounds. JUMP-CP is about 115 TB,
  and the brief excludes large downloads.
* It is the natural third modality for a later block.

## 5. What the literature leaves open, and this block's defensible contribution

1. **Matched-budget comparison** of an autonomous discovery system against:
   * fixed workflows;
   * deterministic adaptive planners;
   * the same agent without the virtual cell;
   * the virtual cell without the agent;
   * a conventional LLM+world-model loop.

   It is run on untouched compounds, with feedback-permutation controls. The agent papers above
   do not report this set.
2. **Where agent-virtual-cell synergy comes from.**
   * Hypothesis: screening outcomes enlarge the virtual cell's same-platform reference library
     exactly where the new library lies. The agent's choice of what to screen therefore decides
     how much the virtual cell can transfer to the remaining compounds.
   * This is falsifiable as a factorial interaction (feedback x virtual cell).
3. **A context-selective phenotype.** Lineage-selective killing across 578 lines, validated on an
   independent dose-response screen, rather than one phenotype in one cell system.

Rejected directions, with reasons:
* LLM-as-world-model (VCWorld style): blocks M and N found that mechanism-level LLM judgement
  removes the virtual cell's cross-mechanism signal.
* Diffusion or single-cell generative virtual cells: the endpoint is bulk viability, and the
  training cost is out of scope.
* Belief-space MCTS: no gain in MAESTRO's 2026-09-27 belief-planning block, and the reveal model
  here is exact.
* Cell Painting: no local data, and the download would be about 115 TB.
