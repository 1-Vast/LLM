# Independent challenge: action-conditioned cell state to AIVO and Agent

Date: 2026-10-31 (Asia/Shanghai)

Reviewer role: separate challenge pass over the frozen task-sufficient-transfer record. This is a scientific and design review only. No numerical run, source-code edit, sealed-data read, or AIVO implementation was performed.

## Review scope

Reviewed:

- `NEXT_ROUND_DESIGN.md` in this study;
- the study `REPORT.md` and `VERIFY_61_REPORT.md`;
- the GAT report and its conditional AIVO boundary note;
- the stated promotion, AIVO and Agent gates.

The review treats the saved pilot as an exploratory result. The independent numerical verifier's `PASS` certifies internal pipeline consistency under the allowed-input boundary; its `scientific_gate` remains `INCONCLUSIVE` because the pilot has no independent external test.

## Overall decision

**Retain the action-conditioned decision-sufficient cell state as a conditional research question. Do not admit it as a Virtual Cell core, do not start the AIVO stage, and do not promote an Agent.**

The design is substantially better framed than GAT as a scientific question. It replaces the vague claim of a biologically complete latent cell state with a bounded predictive claim:

```text
P(Y_{t+delta} | H_t, a, context)
    approximately equals
P(Y_{t+delta} | z_t, a, context),  z_t = f(H_t)
```

The design also adds the missing practical test: whether the state improves a declared drug-discovery decision under a fixed assay budget, while preserving an overall-effect channel and refusing unsupported actions. Those are appropriate gates. They remain untested because the current data contain neither a matched baseline/early state nor multiple future actions.

## What should be retained

### 1. The scientific object is correctly narrowed

The proposed state is a predictive object for a declared action menu. It is not called a universal cell state, a causal mechanism, or a sufficient statistic for all biology. This distinction is necessary because the GAT pilot only showed a small transfer-correlation effect on an exposed pool and did not establish decision utility.

### 2. The data admission contract is strong

The next resource must retain the complete join between early state, intervention identity, physical dose, exposure duration, sequence or washout, later functional outcome, preparation/plate/replicate keys, and chemical or mechanism-family labels. This protects the next test against the exact failure modes visible in the current record: endpoint substitution, incompatible assays, and random compound splits that overstate transfer.

### 3. The comparison set is appropriate

The frozen design should retain direct full-history prediction, raw transfer, GAT, ordinary ridge/PLS or an explicitly declared nonlinear conditional model, a compact-state measurement curve, chemistry-only and shuffled-target controls, plus a fixed-coverage refusal baseline. A new encoder or Agent should not be added merely because a candidate is weak.

### 4. The organoid boundary is correctly conditional

The design does not treat the AIVO review as validation. It requires a single organ-specific task, measured initial composition or spatial context, a functional organoid readout, donor/batch holdout, a persistent state and a virtual assay. The additive mixture of independent virtual cells is the right first comparator. An interaction claim needs an intervention such as omission/add-back, ligand blockade, matrix manipulation or a controlled exposure contrast.

### 5. The Agent boundary is appropriately narrow

The proposed first Agent task—selecting a discriminating measurement among intrinsic resistance, poor local exposure and intercellular protection—is scientifically testable. It keeps the biological transition model frozen and limits the Agent to a declared action menu, QC, provenance, uncertainty propagation, versioned updates and refusal.

## Material objections and required corrections

### Objection 1: the action-conditioned challenge is currently underspecified

The design proposes pairs with similar early observations but different future actions. If the future action is supplied as `a`, two histories may legitimately share the same `z_t`; the action itself can explain the different later outcomes. Therefore divergence after different actions is not, by itself, evidence that the state is insufficient.

The decisive challenge must be stated as one of the following before freezing:

1. **Same action, matched early histories:** two histories have similar `H_t` and receive the same allowed action, but have different later outcomes. A compact `z_t` that merges them is insufficient at that action.
2. **Multiple actions, conditional prediction:** for the same history or matched histories, evaluate every action in the declared menu and test the full conditional outcome vector. Sufficiency is judged by the joint predictive distribution over actions, not by whether the state separates actions that were explicitly supplied as inputs.
3. **Counterfactual action contrast with measured support:** if the resource contains repeated units assigned to different actions, fit on one set of action contrasts and test on held-out contrasts without using later outcomes to construct `z_t`.

Without this correction, a positive result could be an ordinary action-conditioned predictor with no evidence that the compact state preserves intervention-relevant information.

### Objection 2: “compact” can become a score-only claim

The state-dimension curve must include measurement cost and coverage. A lower-dimensional vector is not useful if it requires nearly the same assays, if it is unstable across folds, or if its advantage disappears when direct `H_t` receives the same preprocessing. The design should predeclare:

- maximum state dimension and maximum early measurements;
- the direct-history comparator at each measurement budget;
- a minimum coverage for refusal;
- a utility curve over coverage, not only the best selective subset;
- stability of state dimensions and action predictions across outer folds.

If the compact state only matches full history without reducing measurements or improving decisions, label it representation compression and stop the core-innovation claim.

### Objection 3: support-aware refusal can hide poor performance

A model can improve selective metrics by refusing difficult queries. The refusal rule must therefore be compared with an abstaining baseline using the same coverage grid, and reported with coverage-weighted utility, calibration, and worst-group risk. A high-risk low-coverage result cannot be used to trigger AIVO or Agent work.

The threshold must be fitted only on reference data and frozen before external outcomes. The external test must report how many compounds, cell contexts and action types are refused, including whole mechanism families that fall outside support.

### Objection 4: the action menu is a finite contract, not a universal intervention claim

Dose, continuation time, combinations, washout and follow-up perturbations have different information requirements. The candidate can be sufficient for one declared menu and fail for another. The first round should select one menu—preferably dose/time or one follow-up perturbation—and hold it fixed. Combination and washout actions should be separate rounds unless the data contain adequate repeated contrasts.

Any result must state the action support, observed action coverage, and interpolation versus extrapolation regime. No universal “intervention-sufficient cell state” language is justified.

### Objection 5: the GAT overall-effect channel is necessary but not fully specified

GAT was evaluated after removing a generic profile, so its advantage is confined to selective transfer. The next state must jointly model overall effect and selective effect, but “retain an overall channel” needs an estimand and calibration test. A model could preserve a mean response while misranking high-toxicity versus selective responses.

Require a two-endpoint decision table:

- overall viability or kill magnitude, with calibration and error;
- selective cell-line profile, with top-k regret and hit enrichment.

A candidate that improves selective correlation while degrading overall-effect calibration is not eligible for AIVO.

### Objection 6: mechanism-family holdout may be unavailable or ambiguous

Whole-family holdouts require authenticated target/mechanism labels. Chemical scaffold, InChIKey connectivity and target-family labels are not interchangeable. The data gate should explicitly record which labels are source-authenticated, which are inferred, and which are unavailable. If no auditable mechanism-family key exists, the candidate may use scaffold/context holdout but must narrow its claim and cannot call the result mechanism-general.

### Objection 7: the AIVO upgrade needs an identifiability test before adding physics

A virtual organoid requires more than an additive collection of cell predictions. The initial state must include only variables that are measured or have an explicit observation model: composition, spatial/neighbor context, matrix/culture condition, drug exposure, donor/batch, and baseline function. The transition must expose time and a measurable virtual assay.

Cell-cell, matrix or transport modules should be added only if a corresponding intervention can change that component and a held-out endpoint detects the change. Otherwise the module is an unidentifiable story. A model that is sensitive to arbitrary boundary conditions or spatial assumptions must fail the AIVO gate even if its aggregate endpoint correlation is high.

The first organoid gate should compare:

1. an additive mixture of independently predicted virtual cells;
2. an interaction model with the smallest declared cell-cell or matrix term;
3. a null/persistence model;
4. a mechanistic or exposure baseline when available.

The interaction model must improve a held-out organoid function or decision, and the improvement must survive donor, batch and drug-family holdouts. A better fit without a component intervention is not evidence for interaction biology.

### Objection 8: an Agent may be equivalent to ordinary planning

The proposed Agent role is a partially observed measurement-selection problem. Deterministic Bayesian optimization, mutual-information design, value-of-information planning, change-point detection and a fixed rule can implement the same action selection. Natural-language reasoning or multiple agents do not establish extra scientific value.

The Agent experiment must therefore be frozen as a matched-budget policy comparison:

- random design;
- fixed panel or scheduled sampling;
- ordinary Bayesian optimization/active learning;
- deterministic value-of-information or POMDP planner;
- the constrained Agent.

All policies receive the same state, action menu, tool calls, wells, days, assay types and stopping rule. No policy may inspect held-out outcomes or use hidden literature/data retrieval. The primary endpoint is prospective or temporally held-out decision regret or assay count at matched coverage, with uncertainty calibration and refusal. If the deterministic planner matches the Agent, the Agent is an operational interface and should not be promoted as a research innovation.

### Objection 9: Agent model updates need a causal and provenance boundary

A model-fidelity Agent may request spatial or transport measurements, but it cannot decide from an unexplained output that a new biological interaction exists. State updates must be versioned and attributable to measured observations; transition parameters cannot be rewritten by an LLM. The Agent may select among frozen models or request a new experiment. It must abstain when the model posterior is out of support or when competing explanations remain unresolved.

### Objection 10: current evidence does not justify reopening the numerical goal

The task-sufficient pilot was non-confirmatory and exposed-only. The verifier's PASS is an internal artifact check; its scientific gate is INCONCLUSIVE. GAT's 139/139 result and the pilot's development-pool direction do not supply the missing external action-conditioned data. The next action is a data-contract audit, not a new model, AIVO build, Agent implementation or core promotion.

## Conditional acceptance criteria

### Cell-state gate

All are required:

- one complete early-state/later-function resource passes the row-level data contract;
- outer splits hold out scaffold or authenticated mechanism family, plus donor/context and dose/time where supported;
- action menu is fixed before outcome access;
- conditional sufficiency is tested using same-action matched histories or a joint action-outcome vector;
- overall and selective endpoints are both retained;
- decision margin and coverage floor are predeclared;
- refusal calibration improves risk at the declared coverage;
- state size and measurement cost are stable across folds;
- ordinary direct-history and GAT/ridge comparators are not equivalent under the same information;
- a fresh implementation reproduces the result.

Failure of any item parks the candidate as a bounded predictive representation and leaves the Virtual Cell core `NOT_ADMITTED`.

### Organoid gate

Only after the cell-state gate:

- one organ-specific task and functional endpoint are fixed;
- two or three cell types and one measured composition/spatial context are sufficient for the first MVP;
- donor/batch and drug-family holdouts are available;
- additive and interaction models are compared;
- any interaction/transport claim has a corresponding intervention and held-out response;
- longitudinal update and uncertainty are evaluated on future time points;
- the model improves a drug decision, not only a transcriptomic or morphology score.

Failure leaves AIVO `DEFERRED`; do not add more modules to rescue it.

### Agent gate

Only after the organoid gate:

- action set, costs, tools and stopping rules are frozen;
- deterministic planners and ordinary BO/active learning are matched at equal budget;
- the Agent has a measurable policy advantage on prospective or temporally held-out organoid outcomes;
- all state/model updates are provenance-linked and versioned;
- refusal and model-regime-change detection are calibrated;
- a second donor/batch or organoid context reproduces the advantage.

Failure leaves Agent `DEFERRED` and retains the best deterministic planner.

## Final recommendation

**RETAIN WITH CORRECTIONS.** The candidate is a credible, narrow research question and a useful gate structure, but not a demonstrated innovation. Correct the action-conditioned challenge, predeclare coverage and measurement-cost thresholds, and require the two-endpoint (overall plus selective) decision test. The AIVO and Agent stages remain conditional. The immediate next step is a row-level data audit; if no resource provides repeated action contrasts and later function, issue `INSUFFICIENT_ACTION_CONDITIONED_RESOURCE` and stop.
