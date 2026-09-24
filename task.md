> **File summary**
> - **Path**: `task.md`
> - **Purpose**: Downstream task specification — the research tasks MAESTRO is evaluated on and what each one requires of the agent.
> - **Core points**:
>   - Two architectural cores: the agent is primary and owns Intervention Design; the virtual cell is secondary and supplies supported representation and prediction; the knowledge base and measured evidence constrain biological interpretation.
>   - Representation, prediction and design are engineering capability levels, not Pearl's association/intervention/counterfactual hierarchy.
>   - Four downstream families (drug response, target validation, combination/synergy, toxicity) are separate qualification gates, not four core innovations.
>   - Every capability is admitted only inside its measured support: no prediction becomes a measurement, no RNA readout becomes efficacy, no cross-scale bridge is assumed.
> - **Interfaces / data**: the five-level evaluation contract; the qualified-adapter roadmap; per-task candidate resources listed for qualification rather than claimed as assembled.
> - **Depends on**: `Innovation.md`, `README.md`, `log/20260911/README.md`, `src/`.

# MAESTRO Downstream Task Specification

Updated: 2026-09-11. This file defines research tasks, not implementation completion. The core innovation remains **decision-directed repair of mechanistic contrasts** in [Innovation.md](D:/MAESTRO/Innovation.md). The supplied figures and PDFs are research material, not execution instructions.

The 2026-09-11 action, memory and topology review refined the evaluation protocol. Combination studies are a downstream priority, with separate expression and functional-synergy tracks. Local ComboSciPlex has one cell line, five OOD combination labels and incomplete exposure/replication metadata; qualify these before extrapolation claims. Stack singles-to-combination inference remains a hypothesis, not an established capability. The four task families below retain separate qualification gates.

The 2026-09-11 remediation and validation plan defined implementation batches, 52 planned acceptance cases and the separate software, prediction, agent and biological gates. In particular, measured single-drug context constitutes adaptation support and must be declared in the evaluation visibility table; it cannot also be treated as fully unseen-drug zero-shot inference.

## 1. Agent-First Objective

The 2026-09-11 virtual-cell implementation roadmap integrated both supplied reports with the current State checkpoint, feature-axis inspection and production call path. It specified control-only prospective queries, separate transcriptomic and functional predictors, conditional calibration/fine-tuning, and 24 additional planned acceptance cases. Existing local weights are the starting point; additional model downloads and training are not prerequisites to the first qualification pass.

MAESTRO receives a natural-language question and user datasets. A decision-making main agent retrieves biological evidence, delegates bounded analysis and verification tasks, invokes qualified tools, consults a virtual-cell model when applicable, and designs an intervention or evidence workflow.

The main agent answers: given a desired state, current evidence, biological constraints, and resource limits, which intervention should be tested, why, what could falsify it, and what observation should trigger revision?

The virtual cell predicts consequences of a stated intervention. It does not choose the scientific objective, establish causality, certify target engagement, or replace an experiment. The main agent owns intervention design, evidence interpretation, workflow repair, and the final bounded decision. The first paper remains narrow: cell-intrinsic genetic–pharmacological discordance. The four scenarios below are downstream tests, not four separate innovations.

## 2. Structural Complementarity

The agent is the primary architectural core and the virtual cell is the secondary architectural core. This division is compatible with one methodological core innovation: decision-directed repair of mechanistic contrasts. The table describes responsibility, not equal decision authority. The virtual cell's importance does not remove its applicability checks or the agent's ability to continue when prediction is unavailable.

| Capability | Main agent | Virtual cell | Required interface |
|---|---|---|---|
| Representation | Selects biologically relevant variables and claim level | Encodes a supported state | Context, features, assay and lineage |
| Prediction | Interprets candidate outcomes and alternatives | Predicts state changes for a stated intervention | Candidate-specific query, support and calibration |
| Intervention design | Searches, composes, repairs and prioritizes interventions | Supplies response estimates when qualified | Mode, target set, dose/time and desired state |
| Evidence | Retrieves and verifies multi-source evidence | Consumes compatible inputs | Provenance, conditions, units and parent artifacts |
| Uncertainty | Chooses act, measure, ask, defer or abstain | Reports model uncertainty and limits | Calibrated interval or explicit descriptive spread |
| Feedback | Updates case state and repair policy from real results | Scores predictions against later measurements | Frozen request/result IDs and reliability ledger |

```text
User question and datasets
 -> main-agent task contract
 -> retrieval, multi-omics and QC subagents
 -> state/context construction
 -> candidate intervention generation
 -> virtual-cell applicability check and prediction
 -> dependency-aware selection and scheduling
 -> execution and biological QC
 -> validated observation
 -> main-agent decision or targeted repair
```

The agent must continue to work when the virtual cell abstains. A prediction must never become measured evidence by entering context or memory.

## 3. Multi-Scale Virtual-Cell Representation

The proposed world-model layer is a collection of conditional models across scales, rather than a requirement to train one universal embedding. Different scales may use different models, connected by explicit, validated bridges. Multi-omics describes measurement modalities; multi-scale describes levels of organization. RNA plus ATAC does not by itself create a multicellular model.

| Scale | State variables | Intervention examples | Candidate methods | Limit |
|---|---|---|---|---|
| Molecular | Sequence, structure, binding, occupancy, activity, protein, phospho and metabolite state | Mutation, inhibitor, degrader, rescue allele | Structure/compound encoders, biochemical models | Binding/expression does not prove cellular efficacy |
| Intracellular network | Regulatory edges, signaling, pathway flux, feedback | Knockdown, activation, acute inhibition | CellOracle/SCENIC+-style GRN and pathway models | Inferred edges are hypotheses |
| Single cell | Transcriptome, chromatin, protein, cycle, realization and heterogeneity | Dose/time, genetic, cytokine or environment | State, CPA, GEARS, Scanpy/Pertpy | OOD and endpoint calibration are task-specific |
| Population | State distribution, resistant subpopulations, growth/death and interactions | Combination and sequential dosing | Dose-response and adaptive screening models | Means can hide rare states |
| Multicellular/tissue | Cell communication, spatial organization, immune/stromal context | Combination, co-culture and spatial intervention | Spatial and population models | Less standardized; later scope |
| Organism/exposure | PK/PD, organ distribution and systemic response | Exposure schedule and therapeutic window | Qualified PK/PD and organ models | Outside first paper |

Representation rules:

1. Keep scales distinguishable; latent proximity is not biological equivalence.
2. Attach every variable to measurement type, units, context, time, uncertainty and source.
3. Represent an intervention by mode, target set, dose, duration, exposure, residual function, spectrum and intended state change, not only its name.
4. Expose the assumptions connecting molecular, cellular and population predictions.
5. Preserve heterogeneity and resistant subpopulations instead of relying only on means.

## 4. Knowledge Base for Biological Credibility

The knowledge base should provide structured biological constraints, not just more text.

The 2026-09-11 graph-support and compositional-prediction specification added query-specific graph coverage, source/context checks, contradiction handling, and verified retrieval. Coverage is an input to empirically validated reliability, not a probability or a universal extrapolation ceiling. Keep the evolving reasoning graph separate from the graph used by a trained predictor. F08 evidence admission and F03 scientific contrast validation are prerequisites for decision claims. Downstream combination tests must separately assess expression change, interaction residuals and functional synergy; a high overall expression score does not satisfy those gates.

| Layer | Content | Use in Intervention Design |
|---|---|---|
| Entity identity | Genes, proteins, compounds, pathways, cells, tissues and assays | Resolve synonyms and prevent mismatches |
| Mechanism | Binding, inhibition, degradation, activation, localization and feedback | Determine functional comparability |
| Multi-omics | Transcriptomics, proteomics, phosphoproteomics, epigenomics, metabolomics, imaging | Bridge intervention to mechanism and phenotype |
| Intervention evidence | Dose, exposure, occupancy, residual function, selectivity, off-targets and rescue | Check intended state realization |
| Context | Genotype, lineage, culture, batch and microenvironment | Restrict transfer |
| Assay quality | Controls, replicates, QC, detection limits and missingness | Decide whether evidence is usable |
| Conflicting evidence | Failed, contradictory and non-replicated results | Avoid one positive source dominating |

Every claim should link to a source, condition and evidence type. Use relations such as `supports`, `contradicts`, `measures`, `derived_from`, `uses_context`, `targets` and `requires`. Multiple reports of one experiment form one source cluster.

The validator distinguishes file validity, biological QC, condition matching, statistical support and authorization for a development action. A retrieved claim cannot satisfy a measured prerequisite merely because it appears in the knowledge base. An underlying historical measurement can qualify after its original data, conditions, QC and lineage are checked. Multi-omics should create explicit bridges such as molecular activity -> pathway state -> transcriptional response -> phenotype. Each bridge is tested on matched conditions or marked as an assumption; the arrows are proposed explanatory relations, not an automatic causal chain.

### 4.1 Integration without creating false evidence

Distinguish same-cell measurements, different cells from the same sample, matched samples, and unrelated studies. Preserve donor, sample, time, batch and experimental-unit identifiers. Do not fabricate a paired proteome for an RNA-only sample. Imputed modalities remain predictions with uncertainty and cannot count as independent confirmation of their input modality.

Use late integration of evidence and structured biological summaries first. Add joint representations when pairing, overlap and the task justify them. Prevent batch correction from removing the intervention effect being studied. Missingness and assay detection limits are part of the interpretation, not automatically zero expression or absence of activity.

An evidence item should include species and reference build where relevant, cell/sample identity, intervention and control identity, timing and units, assay, effect and uncertainty, replicate structure, source accession/version, derivation parents, relation direction/sign when supported, and evidence/claim type. Context-specific contradictory relations must coexist rather than be merged into a single universally true edge.

Measure biological credibility through independently adjudicated claim support, condition-match accuracy, invalid-update rate, reproducibility on held-out studies, calibration, and orthogonal experimental confirmation. Do not use citation count, graph connectivity, attention weight, enrichment significance or agent agreement as a universal credibility score. A literature-derived graph used to constrain a prediction cannot also serve as independent ground truth for that prediction.

## 5. Main Agent and Specialist Subagents

The main agent maintains the global case state and owns task interpretation, relevant biological scale, competing mechanisms, missing prerequisites, candidate intervention workflows, delegation, resource allocation, result review, repair and final answer.

| Subagent | Bounded responsibility | Output |
|---|---|---|
| Evidence researcher | Search PubMed, Open Targets, ChEMBL, UniProt, Reactome, KEGG and primary papers | Conditioned evidence cards and contradictions |
| Dataset/QC analyst | Inspect AnnData/matrices, identities, controls, batches and replicate units | QC report, artifacts and admissible analyses |
| Multi-omics analyst | Run differential, pathway, regulatory, protein/phospho and metabolite workflows | Effects, uncertainty, links and limitations |
| Intervention designer | Enumerate modes, doses, times, target sets, combinations and rescue designs | Typed candidate interventions and expected outcomes |
| Virtual-cell specialist | Check applicability and run qualified predictors | Candidate-specific predictions and calibration limits |
| Verification specialist | Audit sources, transformations, assumptions and alternatives | Structured objections and repair counterexamples |
| Optimization specialist | Select and schedule feasible bundles | Plan, cost, solver status and conflicts |

These rows describe responsibilities, not seven mandatory persistent agents. Preserve the four-role initial pool in the agent-first design: Evidence Researcher; Bioinformatics Analyst covering dataset/QC and multi-omics; Simulation Specialist; Verification Specialist. The main agent retains intervention-design authority and may request bounded design alternatives from specialists. Selection and scheduling are numerical tools; a separate optimization LLM is unnecessary by default.

Subagents propose outputs; only the main agent and deterministic evidence validator update global state. Delegation is on demand and budgeted. Compare the hierarchy with a single-agent control under a common resource ceiling, reporting actual calls, evidence, compute and latency; do not force wasteful calls just to equalize counts. Agreement between subagents is not independent biological evidence.

## 6. Intervention Design Is the Primary Agent Task

Given current state `s`, desired state `s*`, candidate intervention `u` and constraints `C`, the agent searches over mode, target set, dose, time, order, combination, controls and readouts. Candidate designs must satisfy feasibility, biological identity, applicability, functional realization, assay, resource and interpretation constraints.

The virtual cell estimates `p(y | u, context, representation)` only when supported. If mechanism variables are not model inputs, the agent must not claim `p(y | u, mechanism)`. Mechanism-dependent validation designs should pair a relevant proximal realization readout with a distal phenotype, or cite already-qualified matching measurements. Descriptive analysis does not require these assays. A distal-only negative result generally leaves intervention failure and mechanism failure unresolved.

### 6.1 Separate intervention optimization from evidence acquisition

Intervention design chooses an action expected to improve a predeclared biological objective; evidence acquisition chooses what to learn before committing to an action. They interact but are not the same optimization problem. Mechanism-contrast repair is the specific operator used when missing or incomparable conditions block a defensible design choice.

For a validated outcome model, a candidate-design objective may be:

\[
u^*\in\arg\max_{u\in\mathcal U_{\mathrm{feasible}}}
\mathbb E[U(Y_u,c)\mid E]-\lambda C(u),
\]

where `U` measures the prespecified desired phenotype, `C` records intervention burden, and `E` is current evidence. Include explicit normal-cell or other toxicity constraints when relevant; use a validated risk bound only if its uncertainty model is justified. Otherwise report trade-offs as a Pareto set and list unresolved constraints. LLMs propose variables and candidates, but do not invent numerical outcome probabilities or utility weights.

Represent the desired state by interpretable endpoints, acceptable ranges, time horizon and protected functions. Moving an embedding closer to a healthy reference is not sufficient: apparent disease-signature removal can be caused by cell death, changed cell composition or technical effects. A concrete design must map latent changes back to feasible target/mode/dose/time operations and independently measurable endpoints.

Use a two-loop design: an inner loop generates and compares feasible interventions with fixed evidence; an outer loop obtains real evidence, diagnoses failures and repairs the design. Optimize evidence acquisition using the decision-risk objective in Section 7. The model can suggest which missing modality or biological scale would change the decision, but new measurement acquisition must be compared with cheaper existing-evidence paths.

### 6.2 Corrections to the supplied conceptual figures

L1 representation, L2 prediction and L3 intervention design are useful engineering capability labels. They are not equivalent to Pearl's association/intervention/counterfactual hierarchy. A conditional predictor does not automatically identify `p(Y | do(u))`; designing a population intervention need not require individual counterfactual inference. Counterfactual claims require additional causal assumptions and identification, not merely forward simulation. See [Pearl and collaborators' causal-inference collection](https://ftp.cs.ucla.edu/pub/stat_ser/ACMBook-published-2022.pdf).

Likewise, a repeatable deterministic simulator can be biologically wrong, and a valid probabilistic model can produce stochastic samples. Reliability comes from validated inputs, held-out performance, interpretation limits and control of accumulated error. The product of a constant per-step success probability is only a simplifying model; use measured workflow failure rates and dependency-aware recovery instead of claiming a universal geometric law.

Do not claim Intervention Design is an empty field. Experimental design and active screening already address parts of it, including [BATCHIE](https://www.nature.com/articles/s41467-024-55287-7). MAESTRO's proposed contribution must be demonstrated by intervention-condition repair under matched resources.

## 7. Operations Research for Selection and Scheduling

The candidate space is combinatorial. Use OR after the main agent creates a biologically meaningful pool:

| Decision | Formulation | Purpose |
|---|---|---|
| Evidence/tool selection | Budgeted coverage, set cover, knapsack with dependencies | Transparent baseline |
| Workflow composition | AND/OR planning with precedence | Represent prerequisites and alternatives |
| Assignment/scheduling | Resource-constrained project scheduling or CP-SAT | Respect agent, GPU, API and deadline limits |
| Adaptive replanning | Scenario trees and receding horizon | Replan after real observations |

Represent each operation with cost, duration, required artifacts, biological guards, resources and covered decision requirements. Count shared controls once and duplicate evidence once. Use MILP or CP-SAT for bounded pools and exhaustive enumeration for small verification cases. Report candidate-pool hash, objective, feasibility, timeout and optimality gap. A solver optimum is only optimal for the declared finite problem.

Complementary evidence may have zero individual value but high bundle value. Therefore do not assume submodularity or use greedy information/cost ranking without checking its conditions. When calibrated distributions exist, optimize expected stage-decision loss minus resource cost; otherwise use reviewed robust scenarios or requirement coverage and explicit abstention. Do not use LLM self-reported probabilities.

## 8. Four Downstream Model Tests

### Task 1: Drug Response Prediction

**Question:** Predict state and phenotype responses for a drug across supported context, dose and time.

**Agent:** Select readouts, matched controls, candidate drugs/doses, follow-up assays and intervention designs.

**Virtual cell:** Predict supported transcriptomic, protein, pathway or phenotype changes and abstain outside support.

**Inputs:** Baseline/perturbation transcriptome, protein/phospho, genomic alterations, cell state and assay metadata.

**Outputs and metrics:** Dose/time design, proximal activity assay, phenotype endpoint, alternative intervention; readout error, differential-expression recovery, calibration, abstention risk and fixed-budget decision loss.

**Stress tests:** Unseen context, unsupported dose/time, missing control, and transcriptomic prediction without phenotype validity.

### Task 2: Target Identification and Validation

**Question:** Which target or necessary target set can move a defined context toward a desired phenotype?

**Agent:** Integrate dependency, chemical response, multi-omics, pathway/regulatory evidence and contradictions; design a functional-strength ladder and validation sequence.

**Virtual cell:** Simulate supported genetic or chemical perturbations without certifying engagement or causality.

**Outputs and metrics:** Perturbation mode, matched comparator, proximal function assay, phenotype, orthogonal tool and rescue; held-out target ranking, wrong advancement/abandonment, evidence cost, calibration and independent validation.

**Stress tests:** Genetic–pharmacological discordance, pan-lethal knockout, partial suppression, off-target phenocopy, context-specific dependency and necessary multi-target activity.

### Task 3: Drug Combination and Synergy Prediction

**Question:** Which combination and schedule produces a desired response while limiting escape or toxicity?

**Agent:** Define endpoint and synergy criterion, select sparse members and sequence, and design confirmation experiments.

**Virtual cell:** Predict supported joint state changes and interaction effects, distinguishing single-agent data from true combination evidence.

**Inputs:** Multi-omics response, pathway topology, selectivity, state composition and time-resolved phenotype.

**Outputs and metrics:** Combination/schedule, single-agent controls, synergy model, resistant-state readout and toxicity guard; held-out synergy ranking, sparse cost, confirmation rate and resistant-state coverage.

**Stress tests:** No true combination labels, OOD combinations, schedule dependence, shared off-targets and growth-rate confounding.

Use measured combination response matrices and matched single-agent controls for synergy evaluation. Prespecify a reference such as Bliss or Loewe according to its assumptions and report sensitivity to alternatives; [SynergyFinder](https://academic.oup.com/bioinformatics/article/33/15/2413/3100330) implements several distinct reference models. Transcriptomic interaction is not equivalent to viability synergy. Report combination efficacy and toxicity separately: a synergistic combination need not be therapeutically useful.

### Task 4: Toxicity and Safety-Liability Prediction

**Question:** Which intervention preserves desired activity while minimizing toxicity across relevant normal and disease contexts?

**Agent:** Define therapeutic window, select contexts, design exposure and recovery arms, and require orthogonal toxicity readouts.

**Virtual cell:** Predict supported cell-state or population changes and abstain from unsupported organ/systemic claims.

**Inputs:** Tissue/cell-type expression, proteomics, stress/apoptosis, mitochondrial/metabolic state, genetic susceptibility, imaging and exposure metadata.

**Outputs and metrics:** Exposure schedule, selectivity constraint, disease/normal comparison, early toxicity marker and confirmatory assay; toxicity ranking, therapeutic-window error, false-negative rate, calibration and confirmation cost.

**Stress tests:** Single-cell model used for organ toxicity, missing PK/exposure, rare sensitive subpopulation, delayed toxicity and pathway activation mistaken for injury.

This is initially an in-vitro hazard/response prioritization task. Use a prespecified sensitivity operating point and relevant held-out injury endpoints. It cannot establish human clinical safety or an in-vivo therapeutic window from isolated cell assays. Translation to systemic toxicity requires exposure and organ-level validation.

### 8.1 Candidate data and baseline map

The following resources are candidates for qualification, not a claim that matched multi-omics or complete intervention menus have been assembled.

| Task | Candidate evidence source | Required comparator and qualification |
|---|---|---|
| Drug response | [DepMap/PRISM](https://depmap.org/portal/data_page/?tab=currentRelease) and supported perturbation transcriptomic datasets | Mean/linear and qualified dose-response baselines; verify units, cell identity, time, controls and independent response labels |
| Target validation | DepMap genetic dependency plus source-traced chemical and functional studies | Dependency-only, literature-only, fixed expert workflow and ordinary-agent controls; verify mode/realization instead of equating KO with drug inhibition |
| Combination | [DrugComb](https://pmc.ncbi.nlm.nih.gov/articles/PMC6602441/) and original combination screens | Single-agent/additivity, random batch and suitable active-design baselines; deduplicate dose matrices and source studies, hold out pairs/series |
| Toxicity | [EPA ToxCast](https://www.epa.gov/comptox-tools/toxicity-forecasting-toxcast) and source-matched normal-cell/organ-specific studies | Assay-specific statistical/QSAR baselines where applicable; qualify exposure, endpoint meaning and assay interference rather than treating every assay hit as tissue injury |

Use [PRIDE](https://www.ebi.ac.uk/training/online/course/pride-quick-tour/what-pride-1) and original studies to locate protein/PTM evidence. Discovery of a relevant accession does not make its specimens matched to another omics dataset. Admit a case only if the available outcomes can actually score its chosen design; do not fill missing historical outcomes with predictions.

## 9. Evaluation Contract

Evaluate five separate levels: representation quality, prediction quality, intervention-design quality, biological credibility and final decision quality. Freeze objective, acceptable actions, visible evidence, tool pool, model versions and resources. Split by target, chemical series, context, study and source cluster. Hide real outcomes until action selection.

Report error, calibrated coverage only for calibrated intervals, OOD detection, abstention, action loss, wrong advancement/abandonment, justified deferral, evidence/tool/compute cost and latency. Cells are not independent biological replicates. Compare no model, simple model, qualified model, always-trusted, applicability-scoped and valid prediction-shuffle controls. A lower prediction error does not necessarily improve Intervention Design.

Use within-task endpoints and case-level uncertainty; do not average transcriptome error, synergy scores and toxicity rates into an arbitrary overall score. The main shared measure is improvement in a task's prespecified biological objective or stage-decision loss under resource constraints, with failure/coverage reported alongside it. For prospective design quality, freeze recommendations before acquiring outcomes.

To isolate biological credibility, compare RNA-only with additional **measured** modalities on the same eligible cases; separate their benefit from the benefit of adding more cases or spending more money. Test condition-aware versus condition-agnostic retrieval, provenance-aware versus duplicated-source retrieval, and valid versus permuted cross-scale links. Hide held-out outcomes from the knowledge base, retrieved summaries and model adaptation. Evaluate the incremental value of a new modality or scale at its additional acquisition/compute cost.

## 10. Tool Roadmap

Current tools provide basic profiling and filtering. Next qualified adapters should be `anndata_qc`, `condition_alignment`, `entity_normalization`, `pseudobulk_differential`, `pathway_and_regulatory_analysis`, `perturbation_realization_qc`, `primary_evidence_retrieval`, `virtual_cell_state`, `virtual_cell_linear`, `intervention_bundle_select` and `workflow_schedule`. CPA/GEARS or other paper-derived models should be added only after task-matched reproduction.

Every adapter needs a manifest, typed input/output schema, source and version, environment, applicability, validation example, cost and explicit failure output. Dynamically retrieved code must not be imported directly into production. Tool qualification states should be `discovered`, `packaged`, `reproduced`, `task_validated` and `active`; active does not mean universally valid.

### 10.1 Mature representation and prediction components to reuse

| Component | Supported use to investigate | What it does not establish |
|---|---|---|
| [MOFA+](https://link.springer.com/article/10.1186/s13059-020-02015-1) | Interpretable factors across appropriate multi-modal data | Causal mechanisms or arbitrary modality alignment |
| [totalVI](https://www.nature.com/articles/s41592-020-01050-x) | Joint modeling of single-cell RNA and antibody-derived protein measurements | General phosphoproteomics or direct catalytic activity; proteins outside the measured panel remain unmeasured |
| [MultiVI](https://www.nature.com/articles/s41592-023-01909-9) | RNA/accessibility integration with suitable paired/unpaired data structure | A validated perturbation simulator just from a good integrated representation |
| [CellOracle](https://www.nature.com/articles/s41586-022-05688-9) | GRN-based candidate TF perturbation analysis | Proof that inferred regulatory edges or every simulated effect is causal |
| [State](https://github.com/ArcInstitute/state), [CPA](https://github.com/theislab/cpa), [GEARS](https://www.nature.com/articles/s41587-023-01905-6) | Checkpoint- and task-matched perturbation prediction | Universal drug/target/context transfer or automatic efficacy prediction |
| [LIANA+](https://www.nature.com/articles/s41556-024-01469-w) | Contextual cell–cell communication analysis and multi-view integration | Verified secretion, receptor activation, transport or causal communication from expression alone |
| [PhysiCell](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005991) | Parameterized multicellular dynamics and spatial interaction simulations | Automatic conversion of RNA embeddings to growth, death, motility or diffusion parameters |

The [AIVC perspective](https://arxiv.org/abs/2409.11654) motivates representations and virtual instruments across scales; it is a research vision, not evidence that a universal multi-scale representation has already been validated. Prefer modular interfaces and task-specific adapters over retraining a universal foundation model for this project.

### 10.2 A concrete multi-scale bridge to validate

For a future co-culture design, connect measured compound exposure and target activity to a cell-state predictor, then connect separately validated cell-state/functional features to growth, death or secretion parameters. Feed those calibrated parameters into a multicellular simulator with measured composition, geometry and boundary conditions. Predict population composition or a spatial phenotype, and validate it with held-out imaging/co-culture measurements.

Do not feed raw State latent coordinates directly into simulator parameters with matching-looking names. Every bridge needs units, parameter identity, calibration data, uncertainty and a scope. Preserve shared-source correlation when propagating uncertainty; repeated use of one RNA dataset does not create independent confirmations at three scales. If a bridge is unvalidated, present the result as exploratory and design a measurement that can test it.

A useful optional innovation hypothesis is **decision-directed modality and scale acquisition**: the main agent chooses the cheapest additional assay or scale-specific observation that can resolve the current design ambiguity. Compare it with fixed RNA-first, fixed multi-omics and generic information-gain policies. This extends the existing repair policy; it is not a fourth independent core innovation or a proven novel algorithm.

## 11. Research Sequence

| Phase | Focus | Gate |
|---|---|---|
| A | Recheck evidence, identity, state and termination contracts | Adversarial cases pass with unified semantics |
| B | Implement persistent shared state and bounded delegation | Restart, failure and provenance are reproducible |
| C | Add multi-omics credibility and first bioinformatics tools | Real supplied data yield traceable replicate-aware artifacts |
| D | Add dependency-aware selection and scheduling | Solver agrees with small enumeration and handles complementary bundles |
| E | Qualify simple and virtual-cell predictors | Held-out accuracy, calibration and abstention scope documented |
| F | Qualify and run downstream tasks in stages: target/response first, combination/toxicity when evidence supports them | Each admitted task reports representation, prediction, intervention and credibility metrics; unavailable tasks remain pending |
| G | Evaluate and optionally learn repair policy | Equal-resource independent cases test transfer |

Do not build a large multi-agent ecosystem before one complete evidence-bounded Intervention Design works. Do not add a scale merely to fill a diagram; add it when it answers a defined intervention question and has a measurable bridge to another scale.

## 12. Positioning

MAESTRO is a decision agent that designs and repairs biologically grounded intervention workflows. It coordinates evidence retrieval, multi-omics analysis, qualified multi-scale virtual-cell prediction and constrained optimization while preserving biological uncertainty and abstaining when evidence or models are not credible.

The virtual cell is useful when it helps compare intervention designs or identify which design needs real validation. Multi-omics is useful when it supplies a measured bridge between intervention, mechanism and phenotype. Operations research is useful when it handles dependencies, complementarity and scarce resources. The core contribution remains the main agent's decision-directed repair of the evidence workflow.
