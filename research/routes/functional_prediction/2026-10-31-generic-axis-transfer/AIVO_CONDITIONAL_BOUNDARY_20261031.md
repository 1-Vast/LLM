# Conditional AIVO boundary note (2026-10-31)

This note is a **preparatory literature boundary**, not part of the GAT numerical verdict,
not a promotion receipt, and not an AIVO implementation. It records what would have to be
demonstrated after a virtual-cell core passes independent functional and decision-utility gates.

## Reading scope and source links

The user-supplied AIVO review was checked at DOI metadata/abstract level and its Crossref
reference list; the publisher full body was not recovered in this pass.

| Source | Link | Reading scope | Evidence status |
|---|---|---|---|
| Bai & Su, *Artificial Intelligence Virtual Organoids (AIVOs)*, Bioactive Materials, DOI '10.1016/j.bioactmat.2025.12.030' | https://doi.org/10.1016/j.bioactmat.2025.12.030 | DOI metadata, OpenAlex/Crossref abstract and cited-paper map | Abstract-level review facts; architecture claims are not empirical validation |
| Qian et al., *Grow AI virtual cells: three data pillars and closed-loop learning*, Cell Research (2025), DOI '10.1038/s41422-025-01101-y' | https://pmc.ncbi.nlm.nih.gov/articles/PMC12012092/ | Full open PMC HTML; sections 'Three data pillars', 'Evolution of AIVC', 'Low-hanging fruits' | Full-text review/editorial facts |
| Yakavets et al., *Machine learning-assisted exploration of multidrug-drug administration regimens for organoid arrays*, Science Advances (2025), DOI '10.1126/sciadv.adt1851' | https://pmc.ncbi.nlm.nih.gov/articles/PMC12309667/ | Full open Europe PMC JATS: abstract, closed-loop platform, objective, methods, results and limitations | Full-text original-study facts |
| Malka-Markovitz et al., *Multiscale modeling of drug-induced liver injury from organ to lobule*, npj Digital Medicine (2025), DOI '10.1038/s41746-025-01736-6' | https://www.nature.com/articles/s41746-025-01736-6 | Official full HTML: multiscale integration, validation and limitations | Full-text original-study facts |
| Yuan et al., *Targeted cellular depletion in an immune-liver-on-a-chip platform...*, Communications Biology (2025), DOI '10.1038/s42003-025-08928-6' | https://www.nature.com/articles/s42003-025-08928-6 | Official full HTML: six-cell chip, depletion contrast, drug results, discussion/limitations | Full-text original-study facts |
| Systema, Nature Biotechnology (2025), DOI '10.1038/s41587-025-02777-8' | https://doi.org/10.1038/s41587-025-02777-8 | Official abstract | Abstract-level fact: systematic variation can inflate ordinary metrics |
| Virtual Cell Challenge, Cell (2025), DOI '10.1016/j.cell.2025.06.008' | https://doi.org/10.1016/j.cell.2025.06.008 | Official abstract | Abstract-level benchmark proposal |
| CRISP, Nature Computational Science (2025), DOI '10.1038/s43588-025-00887-6' | https://www.nature.com/articles/s43588-025-00887-6 | Official HTML metadata/description | Method and result details remain partial |
| MAP, Nature Machine Intelligence (2026), DOI '10.1038/s42256-026-01286-w' | https://www.nature.com/articles/s42256-026-01286-w | Official full HTML metadata, abstract, model/data sections and dataset splits | Partial/full method passages; not independently reproduced |
| UniPert-G2CP, Cell (2026), DOI '10.1016/j.cell.2026.06.005' | https://doi.org/10.1016/j.cell.2026.06.005 | Official abstract | Abstract-level method/claim |
| CellFlow, bioRxiv (2025), DOI '10.1101/2025.04.11.648220' | https://doi.org/10.1101/2025.04.11.648220 | Preprint abstract | Abstract-level and not peer-reviewed here |
| ODFormer, bioRxiv (2025), DOI '10.1101/2025.07.08.663664' | https://www.biorxiv.org/content/10.1101/2025.07.08.663664.full.pdf | Preprint abstract/metadata | Abstract-level and not peer-reviewed here |

## Facts versus design inferences

### Facts from the literature

1. The AIVO review defines organoid-scale digital twins around multimodal/longitudinal data,
   virtual instruments, biophysical priors and hybrid modules for cell-cell, cell-matrix and
   transport dynamics. This is a proposed architecture, not a demonstrated universal model.
2. The Cell Research editorial separates prior knowledge, static architecture and dynamic
   perturbation states, and identifies targeted perturbation omics and closed-loop experiments
   as missing resources. It does not show that a language model can infer these missing states.
3. The Science Advances study used automated microfluidics plus Gryffin Bayesian optimization
   to select drug dose/order/duration for spheroids and PDOs. It set synergy and viability
   objectives, tested only a defined breast-cancer setting, and included human intervention.
4. The npj Digital Medicine study coupled patient-specific portal anatomy, CFD, capillary
   surrogates and lobule injury across spatial/temporal scales. Its discussion explicitly
   reports unresolved small-vessel validation, static-boundary, two-dimensional surrogate,
   missing active transport and incomplete vascular/lymphatic components.
5. The Communications Biology study compared intact and cell-type-depleted immunocompetent
   liver chips across mechanistically diverse drugs. It identified cell-population-specific
   toxicity contributions but acknowledged cell-line, throughput and bile-transport limits.
6. Systema, the Virtual Cell Challenge and the 2026 perturbation benchmark literature all
   reinforce that ordinary expression-level agreement is not sufficient evidence of meaningful
   perturbation prediction. MAP, UniPert-G2CP, CRISP, CellFlow and ODFormer show that mechanism
   knowledge, unseen-context transfer and virtual-organoid prediction are active prior art.

### Design inferences for MAESTRO

These are proposed gates, not observed results:

- A single organ-specific use must be fixed before choosing an organoid architecture. A
  universal AIVO claim is not justified by a validated cell-line transfer module.
- The virtual organoid must receive an identifiable measured initial state: cell-type/state
  composition, architecture or spatial context, matrix/culture condition, baseline function,
  and batch/donor provenance. The resolution should be tied to the claimed decision.
- The intervention must include dose, timing/sequence and local exposure when these can alter
  the endpoint. Transport is a required module only when the decision is sensitive to it.
- The model must execute a state-to-state transition with explicit time and a measurable
  virtual assay. Static embeddings, post-hoc curve alignment or text explanations do not meet
  this condition.
- A claimed cell-cell or matrix mechanism requires an intervention that changes that component
  (omission/add-back, ligand blockade, matrix/flow manipulation), with an additive cell-mixture
  comparator. Correlation or an agent explanation is insufficient.
- The downstream test must use fixed wells/days/measurements and separate donors, batches,
  chemical families and new contexts. Report both prediction and decision utility, uncertainty
  and abstention.

## Agent boundary

The review uses 'agent-based' modules in the sense of executable cell interaction models. This
must not be conflated with an LLM/research agent. The following uses are excluded from the
scientific core: literature/report/code orchestration, generic explanation, multi-agent voting,
post-hoc optimization or an LLM proposer replacing uncertainty sampling/Bayesian optimization.

Conditional agent uses that might carry scientific value after the core passes are:

1. **Discriminating experiment selection:** choose the smallest intervention/measurement that
   separates intrinsic resistance, exposure failure and intercellular protection. Compare with
   fixed panels, mutual-information design and a conventional planner at equal budget.
2. **Adaptive model fidelity:** decide whether a cell model is sufficient or whether spatial
   transport/cell interactions/additional sensing changes the drug decision. Compare with a
   fixed-fidelity and error-triggered rule.
3. **Regime-change detection:** detect when repeated dosing makes the model stale, then abstain,
   recalibrate or request new measurements. Compare with change-point detection and fixed
   resampling schedules using a future held-out outcome.
4. **Protocol compilation with causal safeguards:** convert a proposed experiment into an
   executable protocol while preserving controls, dose/time contrasts and assay timing. A
   deterministic compiler is the first comparator; fewer invalid experiments must be shown.

None of these agent uses is validated or claimed novel in this note. A planner is admissible
only after the virtual-cell core independently demonstrates out-of-distribution functional
prediction and a reproducible drug-discovery decision gain.

## Conditional minimum upgrade sequence

1. **Core gate:** external, independent virtual-cell validation on at least two contexts or
   platforms, with scaffold/MOA/cell-context holdouts; improve a pre-registered decision metric,
   not only selective correlation; preserve a global efficacy/safety channel.
2. **Composition gate:** show that a spatial/state composition of virtual cells predicts an
   organoid functional endpoint better than an additive mixture, and that the added interaction
   is identifiable by an omission/add-back or analogous intervention.
3. **Transport/time gate:** add local exposure, boundary conditions and longitudinal state
   updates only if they improve held-out intervention outcomes; retain failure modes and
   calibration limits.
4. **Closed-loop gate:** compare a deterministic virtual-cell/virtual-organoid planner with
   random, fixed-design, standard BO/active learning and a human protocol under equal wells,
   time and assay budget. Require prospective or temporally held-out verification.
5. **Agent gate:** only then allow an agent as a constrained controller with provenance checks,
   uncertainty/abstention, fixed tool permissions and a hard stop; the agent is an experimental
   policy layer, not the source of the biological state model.

Current status: GAT has passed numerical independent verification but has not passed the core
decision-utility or organoid gates. This note does not reopen the paused numerical goal, read
sealed response cells, run a model, implement an agent, or modify src/tools.
