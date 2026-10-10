# Literature for block M (verified sources; reading depth stated)

"Metadata" means a Crossref or arXiv record and abstract; "abstract" means a search-engine or
publisher summary; "full text" means the article was read. No claim below rests on a passage this
study could not read. Nature article pages redirected to an authentication wall from this machine,
so the two reference papers were verified through Crossref and, for MAP, through MAESTRO's earlier
full-text source audit (`research/knowledge_layer_validation_20261009/SOURCE_AUDIT.json`).

## The two reference papers

| Source | Depth | What it does | What transfers to MAESTRO | What it does not do |
|---|---|---|---|---|
| Gottweis et al., "Accelerating scientific discovery with Co-Scientist", *Nature* 655:487-496 (2026), doi:10.1038/s41586-026-10644-y | Crossref metadata and abstract | Multi-agent Gemini system: agents generate, critique and refine natural-language hypotheses; a tournament evolution ranks them; quality improves with test-time compute; in vitro validation of AML repurposing candidates, plus target discovery and an antimicrobial-resistance mechanism. | Generation-critique-refinement as a source of a hypothesis *space*; external experimental validation as the arbiter. | Hypotheses are prose ranked by model-based debate; there is no quantitative world model that computes each hypothesis's predicted observations, no calibrated rejection rule, and no design over a measurement menu. |
| Feng et al., "A knowledge-driven framework for predicting single-cell responses for unprofiled drugs" (MAP), *Nat Mach Intell* 8:1478-1491 (2026), doi:10.1038/s42256-026-01286-w | Crossref metadata; MAESTRO's 2026-10-08/09 full-text and code audit | A multimodal knowledge graph (drug, protein, text) is aligned contrastively into one embedding space; the knowledge-informed drug embedding conditions a STATE-based response model; evaluated on pseudobulk RNA for held-out drugs (24 h, single time). | Knowledge as a prior for drugs without profiles. | Knowledge is an embedding, not a testable claim; edges are not signed cell-context effects; no time; no hypothesis about *why* a response occurs. MAESTRO found MAP retrieval no better than Morgan fingerprints for known targets (EVIDENCE.md). |

## Closest competing work

| Source | Depth | Relation to block M |
|---|---|---|
| Huang et al., POPPER, "Automated hypothesis validation with agentic sequential falsifications", ICML 2025 (PMLR 267:25372-25437), arXiv:2502.09858 | abstract | LLM agents design falsification tests for free-form hypotheses on existing data; e-values give sequential Type-I control. Closest in spirit. Differences: no world model computing each hypothesis's predicted observations, no choice among a measurement menu, no identifiability or exhaustion output. |
| "Towards Autonomous Mechanistic Reasoning in Virtual Cells" (VCR-Agent / VCReasoner), arXiv:2604.11661, ICML 2026 | abstract and lab blog | Mechanistic explanations as DAGs of typed action primitives, verified against evidence, used as supervision for Tahoe DE prediction. Explanations of observed responses, not hypotheses tested by new observations. |
| Yuan et al., "Plausibility Is Not Prediction", arXiv:2606.01042 (2026) | abstract | LLM perturbation reasoning over-predicts differential expression and can lose to a gene-frequency baseline; contrastive evidence helps. Motivates treating the agent's hypotheses as claims to calibrate, not predictions. |
| LLM-Guided Retrieval (LGR), arXiv:2608.01734, ICLR 2026 | abstract | LLM ranks neighbour drugs for Tahoe-100M response prediction; cell-mean baseline strong for unseen drugs. Prediction, not falsification. Block M's analogy compiler is the class-level counterpart (agent-chosen analog classes' reference means); in development it carried class information (own-class rank 0.572 vs 0.503 shuffled) but enlarged falsification sets. |
| Miao et al., VCLMU, arXiv:2610.04475 (Oct 2026) | abstract | "Mechanism" as learned latent units in a world model for genetic perturbations; no LLM, no time, no hypothesis testing. |
| Li et al., CellScientist, arXiv:2605.07335 | abstract | LLM-driven revision of perturbation *models* from execution feedback; not biological hypothesis testing. |
| Roohani et al., BioDiscoveryAgent, ICLR 2025 | abstract | LLM chooses genes for perturbation screens; beats Bayesian-optimisation baselines on hit discovery. Design for hits, not mechanism discrimination. |
| Robin (arXiv:2505.13400); Biomni (bioRxiv 10.1101/2025.05.30.656746); CRISPR-GPT (Nat Biomed Eng 2025) | abstract | Closed-loop or general agents; no calibrated mechanism falsification. |
| BED-LLM, arXiv:2508.21184 (authors not verified here) | abstract | Expected-information-gain question selection with the LLM as the model; an LLM's in-context updates need not be calibrated posteriors. |
| MEDA (arXiv:2607.13608) and AgentODE (arXiv:2607.00733), 2026 | abstract | LLM-guided ODE discovery; report that numerical fit can retain biologically incorrect equations. Supports separating fit from mechanistic validity. |
| Box & Hill 1967; Busetto et al. ICML 2009; Vanlier et al. *BMC Syst Biol* 8:20 (2014); Silk et al. *PLoS Comput Biol* 2014 | abstract / known references | Optimal design for model discrimination (time points, inputs). Silk et al.: when every candidate model is wrong, discrimination design can favour the least-wrong model; this is why block M reports exhaustion explicitly. |
| Fannjiang et al., *PNAS* 2022, conformal prediction under feedback covariate shift | abstract | Conformal validity when the design depends on earlier data. In development, per-option-set calibration under the adaptive design lost coverage for responsive drugs; block M therefore calibrates the whole adaptive procedure (calibration drugs run the same design; "episode calibration"), which restores exchangeability at the price of pooling over option sets. |
| Vovk, Gammerman & Shafer, *Algorithmic Learning in a Random World* (Springer 2005); Sadinle, Lei & Wasserman, *JASA* 114:223 (2019); Romano, Sesia & Candes, NeurIPS 2020 | known references | Mondrian (category-conditional) conformal prediction; least-ambiguous and adaptive set-valued classifiers. Block M's sets are class-level conformal sets with Mondrian categories by support and observed energy; marginal coverage alone hid a failure on responsive drugs (development), hence the energy taxonomy. |
| Subramanian et al., *Cell* 171:1437 (2017) (L1000, CMap) | known reference | The platform; MoA discovery by connectivity to reference signatures. |
| Corsello et al., *Nat Med* 23:405 (2017) (Drug Repurposing Hub) | file header | Mechanism and target annotations used as ground truth. |
| McFarland et al., *Nat Commun* 11:4296 (2020) (MIX-Seq), doi:10.1038/s41467-020-17440-w | full text (Europe PMC XML) | Responses decompose into a viability-independent component (target engagement, e.g. EGR1/DUSP6 down at 3 h for trametinib) and a viability-related component (cell-cycle genes, 12-24 h, only in sensitive lines). Different response components carry mechanism and fate information at different times. |

## Positioning

Established and not claimed: conformal p-values, expected-information design, hierarchical
prototype models, LLM hypothesis generation, connectivity-based MoA inference.

Not found in the searched literature (a search result, not proof of absence): a loop in which
an LLM writes *executable* mechanism hypotheses that a world model compiles into predicted
observations over a menu of contexts and times; hypotheses are rejected by a rule calibrated on
reference perturbations, including hypotheses with no reference data; the next observation is
chosen to falsify; and the output includes which mechanisms are indistinguishable within the menu
and when the hypothesis set itself is exhausted.
