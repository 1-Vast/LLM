# MAESTRO v2: repository-grounded audit and gated research plan

You are working on MAESTRO: Mechanism-Aware Evidence-driven Scientific Agent for Therapeutic Reasoning and Optimization.

Repository: https://github.com/1-Vast/LLM.git. Use the supplied local checkout as the working source of truth and record its commit and worktree state.

## 1. Objective and execution scope

Determine which missing measurement can distinguish the remaining mechanistic explanations, when a world-model prediction helps select that measurement, and when the system should repair its assumptions or defer.

The primary biological use case is cell-intrinsic genetic–pharmacological discordance. Start with one qualified task and a one- or two-measurement horizon. Combination screening, toxicity, large-scale pretraining, and additional agent roles are outside the initial scope.

RUN_MODE = AUDIT_AND_PLAN by default. Deliver a repository-grounded audit, a minimal implementation specification, and a preregistration-ready experiment plan. Do not interpret this prompt as authorization to rebuild the whole system, train large models, download entire datasets, or consume a sealed evaluation cohort.

If the user explicitly selects MINIMAL_IMPLEMENTATION, also implement the smallest justified slice after the audit and verify it. Continue independently within the authorized scope; request clarification only when a consequential ambiguity prevents progress. Report unmet prerequisites instead of inventing data or completing later stages nominally.

Success means an auditable, executable, falsifiable plan or implementation. It does not require a positive model result. Distinguish engineering completion, scientific evidence, and eligibility for default deployment.

## 2. Establish the current state before proposing changes

Read applicable AGENTS.md instructions, README.md, task.md, Innovation.md, and relevant research protocols. Inspect the actual call paths, tests, and result artifacts; documentation alone does not establish runtime behavior.

Start with these existing components:

- `research/protocol_v2/`: measurement states, public policy view, truth-free episodes, scoring, registration, headroom, calibration, and attribution.
- `src/maestro/models.py`, `outcome.py`, `provenance.py`: evidence kinds, scoped updates, interpretation rules, and source clustering.
- `src/maestro/planning.py`, `acquisition.py`, `contrast.py`: planning, action selection, mechanism contrast, and repair.
- `src/virtual_cell/interface.py` and `research/belief_planning/world.py`: prediction contracts, competence fields, and outcome forecasting.
- `research/experiments/`, `research/protocol_v2/DIAGNOSIS.md`, and dated logs: historical evidence and known limitations.

For each requirement classify the current state as SATISFIED, PARTIAL, MISSING, CONTRADICTED, or UNVERIFIED. Cite file, symbol, relevant line, test, and artifact where available. Separate production, research-only, legacy, and proposed paths.

Reuse existing contracts and implementations. Do not create a second evidence store, planner, registry, or calibration framework merely to match the names in this prompt. New module boundaries are justified only by a demonstrated responsibility or access-control gap. A provenance graph can be represented by typed records and edges; no graph database is required.

Treat supplied historical findings as claims to verify and qualify:

- Fixed expert order captured approximately 63–99.6% of the reported oracle's correct decisions across the historical tasks.
- Approximately 76–82% of historical L1000 episodes were unidentifiable under the registered menu and interpretation rules.
- Historical power estimates for a +0.02 correct-decision difference were roughly 345–813 independent units in selected settings; development tiers had 42–256 units.
- GSE70138 yielded 38 label-compatible compounds out of 673 metadata-eligible new compounds.
- Raw wrong-elimination forecasts underestimated observed rates by roughly 2–5 times in the reported settings.
- World-model and feedback components did not meet the reported decision-level promotion criteria.

These numbers are not universal properties or mandatory new sample sizes. Record their population, protocol, denominator, uncertainty, and exposure status. Distinguish no demonstrated benefit, evidence excluding a practical benefit, and underpowered uncertainty. Historical GSE70138 is consumed; the audit also reports within-study reference fitting, which limits claims of unseen-study model generalization.

## 3. Data construction and access boundaries

Audit the complete path:

raw source → manifest → identity/condition normalization → independent-unit construction → metadata eligibility → split/seal → fold-specific fitting → task compilation → policy-visible view → selected measurement reveal → scoring.

Required capabilities, implemented through the smallest extensions to existing code:

1. Source manifests with study/accession, release, file checksum, acquisition date, licence, transformations, and exposure history.
2. Canonical compound/structure, gene/target, cell, intervention, dose/unit, duration, assay, endpoint, control, batch, and replicate identities. Uncertain matches remain unresolved; display-name joins alone are insufficient.
3. Distinct identifiers for biological units, repeated observations, split groups, statistical clusters, and original evidence sources. These identifiers are not interchangeable.
4. Field lineage, outcome derivation, and stage-specific access permissions propagated through derived tables, caches, manifests, and logs.
5. Separate development, calibration, and sealed evaluation partitions, grouped according to the declared generalization claim. Audit identity, scaffold, batch, study, and model-pretraining overlap; do not require every possible holdout dimension simultaneously.
6. Allow-listed task and policy views. Enforce evaluator-only outcome access using process/filesystem separation where feasible. Describe the actual threat model: a Python wrapper or read-only flag is not a security boundary against unrestricted code.

Before splitting, eligibility may use only approved metadata and documented fixed transformations. Outcome-dependent QC, feature selection, normalization fitting, batch correction, PCA, reference-pool selection, and threshold fitting must respect training/calibration boundaries. Study-provided processed matrices need an upstream preprocessing audit. If transductive processing is unavoidable, declare it and restrict the claim.

Do not infer pre-experiment availability from a table that contains only successful measurements. Preserve study-design availability separately from measurement success, QC, and readout interpretation. The proposed states NOT_PLANNED, PLANNED_NOT_MEASURED, MEASURED_VALID, MEASURED_QC_FAILED, and MISSING_OR_UNKNOWN are lifecycle concepts, not replacements for the existing undetected/ambiguous/eliminating readout categories. Specify a lossless mapping or separate fields before migration.

Changing held-out outcomes while keeping permitted metadata and training data fixed must not change cohort membership, split assignment, hypothesis generation, or the initial legal menu. Outcome changes after a legitimate reveal may change subsequent actions.

## 4. Evidence, claims, and mechanism state

Maintain the hard distinction between real measurements, measurement-derived statistics, model predictions, retrieved sources, curated assertions, hypotheses, and assumptions. Never strengthen origin through retrieval, aggregation, memory, or repeated citation.

Retain evidence IDs, parent links, source clusters, biological conditions, quantity/unit, QC, interpretation scope, visibility, dataset/code/rule versions, and timestamps. Deduplicate derivative citations to the original experiment. Unknown source dependence is not demonstrated independence.

Public experimental data may enter as real measurements through a validated data-ingestion contract with raw-data provenance and QC. A retrieved paragraph or database assertion does not become a measurement merely because it describes an experiment. Measurement-derived statistics retain their derivation and can support a registered rule only through qualified measurement ancestors.

Validate claims deterministically:

- Binding/engagement requires an appropriate binding or engagement assay and its stated scope.
- Functional inhibition requires a proximal functional readout.
- Pathway and phenotype claims require their corresponding matched measurements.
- Lysate binding does not establish intact-cell engagement or functional inhibition.
- Transcriptomic or morphological similarity alone does not establish on-target mechanism.

Deterministic validation means reproducible rule execution, not error-free biology. Rules must state controls, condition tolerances, effect/detection thresholds, noise assumptions, and false-elimination risk. Non-detection is not automatically evidence against a mechanism without sufficient assay power and demonstrated intervention realization.

Separate the admitted compatible mechanism set from advisory model-based scores or probabilities. Predictions may rank measurements but cannot satisfy measured premises or directly eliminate mechanisms. Existing Bayesian advisory branches may remain comparison arms; calibration of a marginal score alone does not validate an entire likelihood model.

Handle incomplete and overlapping mechanism spaces explicitly. A singleton remaining set is not automatically proof; an empty set is a contradiction, not a successful decision. Support UNKNOWN/OTHER or an equivalent open-set state, multi-target explanations where appropriate, named repairs, and DEFER. Preserve the full update history when qualified contradictory evidence triggers revision.

## 5. Qualify the task before optimizing the planner

Define the scientific decision, candidate mechanisms, actions, prerequisites, interpretation rules, budgets, and scoring truth. Specify how a mechanism conclusion maps to a development action. A retrospective MoA annotation is a reference label with limitations, not direct causal truth or evidence of therapeutic efficacy.

Separate two environments:

- Retrospective replay: policies buy access to already observed, hidden experimental results. Missing outcomes are unavailable and cannot be filled with predictions for decision scoring.
- Prospective proposal: policies may propose registered feasible assays without existing outcomes. Report the proposal and execution requirements; do not claim the experiment happened.

A second measurement is an adaptive information acquisition step unless genuine longitudinal intervention data justify a state-transition interpretation. Independent perturbation snapshots are not offline-RL trajectories.

On development data, quantify fixed-baseline performance, absolute oracle-minus-fixed headroom, unidentifiable/conflicting cases, second-step headroom, and the number of independent units. Define the oracle's information advantage: realized-outcome hindsight is an upper bound, not an attainable policy benchmark or a population identifiability proof.

Register task eligibility before final evaluation. Do not inspect sealed outcomes to choose tasks, modalities, thresholds, or cohorts. If final headroom is low, report it post hoc without replacing the cohort. Low-headroom tasks can remain safety/regression tests but should not be the primary superiority benchmark.

## 6. Qualify data by the uncertainty it can resolve

Separate data for action-menu expansion, model development/calibration, and sealed confirmation. Begin with metadata and small processed-feature pilots. For each source report actual availability, independent-unit count, pairing keys, condition overlap, labels, licences, cost, exposure history, and the uncertainty it could resolve.

Candidate priorities are conditional, not a requirement to ingest every source:

- JUMP/CPJUMP1: test whether morphology adds discriminative information.
- Target-engagement and proximal-function datasets: test intervention prerequisites and polypharmacology, retaining assay-specific scope.
- LINCS 2020: perform a metadata-only cohort census and overlap audit before considering a new-compound evaluation.
- Tahoe-100M: consider bounded response-model development if simpler/local data are inadequate; audit pretrained-model overlap and never use cell count as independent N.
- DepMap/PRISM: construct development discordance cases only with validated entity/context matching and label-use boundaries.

RNA + morphology or genetic + pharmacological comparisons require measured pairing or an explicitly justified transport design. Shared compound names do not establish matched dose, time, cell, control, or batch. Unpaired modalities can support separate analyses or training, but cannot be concatenated into fictitious measured episodes. Imputation stays a prediction.

For menu expansion compare baseline and expanded menus on the same eligible development units, with the same budget and an updated strongest simple baseline. Report attrition and overlap. Qualify a modality by prespecified gains in discrimination, risk, cost, or time; a useful cheaper assay need not increase the absolute oracle ceiling.

## 7. World model: minimal, removable, and available at decision time

Use a replaceable interface for:

`p(y | H, D_real, candidate_action, context, intervention_mode, dose, time)`.

Define what H means, what training observations support conditioning on it, and what assumptions permit transfer. Do not present this conditional distribution as an identified causal intervention distribution merely because H or intervention mode is an input.

Return a joint or coherent outcome distribution with QC/no-result behavior, uncertainty, reference support, domain assessment, model/training/calibration versions, and abstention reason. Prefer observable readouts or registered outcome categories. Correct/wrong/ambiguous are downstream rule-relative quantities and must not require hidden test truth at inference time. Do not collapse conflicting eliminations or empty-set outcomes into success.

Intervention realization, outcome prediction, and competence are conceptual responsibilities, not a requirement for three neural heads. Start with empirical, ridge, or other simple supported models.

For time and intervention realization `r(t)`:

- Use only actual supported time points; 6/24/72 h are examples, not required invented coverage.
- Label realization as measured, estimated, or unknown. Use target-specific quantities where one scalar is biologically inadequate.
- A new-candidate engagement/function assay is an action with cost and latency, not a free model input.
- Estimate r(t) using information available before the candidate action; propagate uncertainty. Never derive it from that action's hidden outcome and feed it back as a predictor.
- Measured r(t) unavailable at deployment may be evaluated as an explicitly privileged upper-bound arm, not as a deployable result.

If realization data or identifiability are insufficient, deliver the prerequisite audit and a time-only baseline; mark the realization experiment NOT_READY. Do not train an uninterpretable latent proxy and call it functional inhibition.

## 8. Planning, calibration, and knowledge

Retain a legal fixed/expert fallback where appropriate. World-model abstention does not imply that no useful real measurement exists. Select an admissible measurement, named repair, or explicit deferral based on evidence and constraints.

A conservative separation-minus-cost/risk score may be an experimental ranking heuristic. Specify its pair aggregation, units, normalization, weights, support thresholds, and sensitivity analysis. Replacing an uncalibrated posterior with an uncalibrated risk penalty does not establish safety. Hard admissibility and budget constraints remain deterministic.

Condition second-action forecasts on the revealed first result and audit dependencies between repeated measurements. Compare feedback arms with identical first actions when isolating the value of execution-time feedback.

Audit and extend the existing calibration code before adding methods. Start with raw predictions and the simplest suitable calibrator; add isotonic, beta, hierarchical, or conformal methods only when sample support and assumptions justify them. Separate calibration data from fitting and final evaluation, including nested choices where needed.

Assess calibration on actions actually selected by the frozen policy, not just pooled actions. Report conditional wrong-elimination rate, uncertainty bounds, coverage, deferral, and cumulative episode-level false-elimination risk. Sparse accepted sets or zero observed errors do not prove safety. State assumptions behind conformal/risk guarantees; arbitrary study shift does not preserve them. Few development studies support exploratory transfer evidence, not a universal cross-study guarantee.

Use a small provenance-preserving KB only if it addresses a demonstrated hypothesis-generation, measurement-generation, or plausibility gap. Prefer existing integrations; ChEMBL, OmniPath, Reactome, and MSigDB are candidates. Audit answer-bearing compound–target/MoA entries and reference-label provenance so retrieval does not become a hidden answer key. Freeze the allowed knowledge snapshot and access rules; distinguish metadata-only closed-book evaluation from a declared knowledge-assisted track.

Separate KB attribution experiments: hold the menu fixed to test ranking; allow generated menus to vary under equal acquisition budgets to test generation. Report both stages. Do not require an identical menu while claiming to measure the benefit of generating new actions. Shuffled KB controls should preserve relevant degree/type structure and cannot corrupt the authoritative measurement ledger.

## 9. Evaluation and promotion

Report representation, prediction, experiment selection, biological validity, and final decisions separately. Prediction improvement, action changes, and decision gains are different claims.

Choose one primary estimand before evaluation. Prefer paired correct-decision difference against the strongest fixed/expert baseline under matched resources, with prespecified wrong-decision, wrong-elimination, and cost constraints. A cost/time superiority claim is an alternative registered estimand requiring decision-quality noninferiority, not a post-hoc substitute for failed correctness superiority.

Define denominators, unresolved/deferred/exhausted outcomes, coverage, risk among decided cases, acquisition cost, and scoring eligibility. Report all metadata-eligible units for operational endpoints and explicitly report the labelled scoring subset. Weight units as registered so compounds with more episodes do not silently dominate. Use paired cluster-aware uncertainty and power calculations matching the actual dependency structure; account for multiple primary comparisons and repeated looks.

Minimum relevant baselines:

- Prediction: training mean, linear/ridge, nearest reference; add zero-effect/PCA where appropriate.
- Decisions: fixed expert order, budget-matched random legal action, a simple model-based acquisition rule, and no-world-model MAESTRO.
- Add EIG/VOI, committee, retrieval, or named published methods only when their task and input contracts match. Identify exact papers/implementations and adaptation limits; a vague “MDA-like” label is insufficient. BATCHIE/ScreenShot are deferred unless combination screening is actually in scope.

Minimum attribution: remove/shuffle world-model predictions, fix planner while replacing the model, and fix the first action while withholding planning feedback but preserving authoritative evidence updates. Add time, realization, KB, competence, risk, and cost ablations only for components actually changed. Budget all acquisition inputs and report compute separately.

Use namespaced gates to avoid collision with historical G1–G4 definitions:

- WM-G0: appropriate simple baselines are reproduced on leakage-controlled splits.
- WM-G1: the chosen model demonstrates the registered prediction and competence benefit.
- WM-G2: it improves a defined action-ranking/regret endpoint on qualified development tasks.
- WM-G3: it meets the registered decision benefit and safety/resource constraints with paired uncertainty.
- WM-G4: the frozen benefit reproduces on an eligible unopened cohort with a precisely stated generalization claim.

Specify numeric thresholds, uncertainty rules, and sample-size assumptions in the experiment registry before running. Use PASS, FAIL, INCONCLUSIVE, and NOT_READY distinctly. If WM-G2 or WM-G3 fails, retain the simpler default and the negative result; the experimental model may remain an isolated research or retrieval component.

## 10. Work sequence and stopping rules

1. Audit existing paths and reproduce relevant evidence where locally feasible. Output the gap matrix and evidence limitations.
2. Specify or implement the minimum data/evidence/evaluation boundary fixes. Verify leakage, provenance, and scoring invariants before relying on new results.
3. Run or plan E-DATA1 first: matched-cohort action-menu and second-step headroom qualification. Stop planner-superiority work on tasks with insufficient headroom; retain their regression value.
4. Run or plan E-CAL1 early using existing forecasts: cross-study and selected-action calibration. Conservative unvalidated heuristics may be explored, but cannot be promoted as risk-controlled planning.
5. Run or plan E-WM1 only after its data gate: dose-only vs dose+time vs deployable dose+time+realization, with identical eligible evaluation units and charged inputs. Separate privileged-input diagnostics.
6. Evaluate one minimal second-measurement planner with the qualified menu/model and relevant attribution controls.
7. Prepare external confirmation only after the previous gates justify it. Freeze cohort criteria, code, model, preprocessing, KB, menu, calibrator, rules, thresholds, seeds, environment, and analysis before reveal.

For external work audit prior exposure by analysts, agents, pretrained models, validators, calibrators, and KB sources. Distinguish unseen compounds, scaffolds, cell contexts, and studies. Target-study reference fitting is adaptation and must be disclosed. Reusing consumed GSE70138 is development or retrospective analysis, not new confirmation.

Use an evaluator-only, logged reveal. No adaptive retuning, cohort replacement, or repeated model selection after results. A deterministic rerun for a technical failure is permitted only under the registered failure policy, identical frozen artifacts, and a disclosed access trail. Any changed analysis is explicitly post hoc.

If data, resources, reliable truth, or statistical power are missing, report the exact blocker, the smallest next requirement, and what can still be concluded. Do not download full image universes or launch large training jobs without an explicit resource envelope.

## 11. Required deliverables and acceptance checks

Produce a compact set of linked artifacts:

1. Audit matrix: current behavior; file/symbol and evidence; status; scientific consequence; minimal correction; dependencies; test; success/failure criterion. Include supported and unsupported claims.
2. Current and proposed data-flow diagrams with access boundaries, module reuse, reveal points, and authoritative update paths.
3. Minimal implementation plan with exact files/interfaces, migration compatibility, prioritized issues, resource estimates, and rollback/default behavior. Record skipped ideas with reasons.
4. Dataset qualification table plus an experiment registry for E-DATA1, E-CAL1, E-WM1, and conditional external confirmation. Each entry needs hypothesis, exposure status, units, splits, arms, estimand, thresholds, uncertainty/power method, budget, failure rule, and artifact locations.
5. Validation record: commands actually run, results, skipped checks, unresolved limits, and the next justified action. Do not describe planned experiments as completed.

For implementation mode, test at least the relevant changed boundaries: held-out outcome mutation cannot alter construction; forbidden fields fail closed; predictions and citations cannot satisfy measured premises; condition/QC failures cannot eliminate mechanisms; duplicate citations cannot increase independent evidence count; unknown truth cannot score as correct; missing measurements cannot become biological failure; empty/open mechanism sets produce named outcomes; and no-world-model fallback remains executable. Verify frozen artifacts cannot be silently overwritten through supported APIs.

Preserve historical protocols/results, existing user changes, and the production default unless a separately authorized, gate-supported change calls for promotion. Do not edit historical findings to match new results. Finish with a specific go/no-go decision for the next phase and the evidence supporting it.
