# Downstream tasks and evaluation contract

This file defines what MAESTRO is evaluated on and what each task requires of the agent. It
defines research tasks, not completed implementation. The core contribution is in
[`Innovation.md`](Innovation.md); the runnable surface is in [`README.md`](README.md).

---

## 1. Objective

Given a desired biological state, current evidence, constraints and a resource limit, the agent
must answer: **which intervention should be tested, why, what would falsify it, and what
observation should trigger revision?**

The agent owns intervention design, evidence interpretation, workflow repair and the final
bounded decision. The virtual cell predicts the consequences of a *stated* intervention within
its applicability domain; it does not choose the objective, establish causality, certify target
engagement, or replace an experiment. **The agent must keep working when the virtual cell
abstains.**

The first paper stays narrow: cell-intrinsic genetic–pharmacological discordance. The four
families below are downstream tests with separate qualification gates, not four contributions.

## 2. Capability levels

Representation, prediction and intervention design are engineering capability levels. They are
**not** Pearl's association / intervention / counterfactual hierarchy: a conditional predictor
does not thereby identify `p(Y | do(u))`, and designing a population intervention does not
require individual counterfactual inference.

| Capability | Agent | Virtual cell | Required interface |
|---|---|---|---|
| Representation | Selects relevant variables and claim level | Encodes a supported state | Context, features, assay, lineage |
| Prediction | Interprets candidate outcomes and alternatives | Predicts state change for a stated intervention | Candidate-specific query, support, calibration |
| Intervention design | Searches, composes, repairs, prioritizes | Supplies response estimates when qualified | Mode, target set, dose, time, desired state |
| Evidence | Retrieves and verifies multi-source evidence | Consumes compatible inputs | Provenance, conditions, units, parents |
| Uncertainty | Chooses act, measure, ask, defer, abstain | Reports model uncertainty and limits | Calibrated interval, or explicit descriptive spread |
| Feedback | Updates case state and repair policy from real results | Scores predictions against later measurements | Frozen request and result identifiers |

## 3. Task families and their gates

Each family is admitted only when its gate passes. An unadmitted family stays pending and is
reported as such.

### Task 1 — Drug response

Predict state and phenotype responses across supported context, dose and time.
**Agent:** choose readouts, matched controls, candidate doses, follow-up assays.
**Metrics:** readout error, differential-expression recovery, calibration, abstention risk,
fixed-budget decision loss.
**Stress tests:** unseen context, unsupported dose or time, missing control, transcriptomic
prediction presented without phenotype validity.

### Task 2 — Target identification and validation

Which target or necessary target set can move a defined context toward a desired phenotype?
**Agent:** integrate dependency, chemical response, pathway evidence and contradictions; design
a functional-strength ladder and a validation sequence.
**Metrics:** held-out target ranking, wrong advancement and wrong abandonment, evidence cost,
calibration, independent confirmation.
**Stress tests:** genetic–pharmacological discordance, pan-lethal knockout, partial suppression,
off-target phenocopy, context-specific dependency, necessary multi-target activity.

### Task 3 — Combination and synergy

Which combination and schedule produces a desired response while limiting escape or toxicity?
**Requires measured combination response matrices with matched single-agent controls.** Prespecify
a reference model according to its assumptions and report sensitivity to alternatives.
**Transcriptomic interaction is not viability synergy**, and efficacy and toxicity are reported
separately: a synergistic combination need not be useful.
**Stress tests:** absent true combination labels, out-of-distribution pairs, schedule dependence,
shared off-targets, growth-rate confounding.

### Task 4 — Toxicity and safety liability

Which intervention preserves activity while limiting toxicity across relevant contexts? This is
an **in-vitro hazard prioritization task**. It cannot establish clinical safety or an in-vivo
therapeutic window from isolated cell assays.
**Stress tests:** a single-cell model used for organ toxicity, missing exposure data, rare
sensitive subpopulation, delayed toxicity, pathway activation mistaken for injury.

## 4. Evaluation contract

Five levels, scored separately and never averaged into one number: representation quality,
prediction quality, intervention-design quality, biological credibility, decision quality.

**Freeze before any outcome is revealed:** objective, weights, acceptable actions, visible
evidence, tool pool, model versions, prompts, budgets. Record digests.

**Split by independent experimental unit.** Molecular identity, plus scaffold for a chemistry
claim; study and source cluster for a literature claim. A context with no adequate training
support is an explicit extrapolation test, not an interchangeable coordinate system. Cells are
not biological replicates; the analysis unit is the compound or study cluster, and intervals
are cluster bootstraps on paired differences.

**Report:** error; calibrated coverage only where an interval claims coverage; out-of-domain
detection; abstention; action loss; wrong advancement and abandonment; justified deferral;
evidence, tool and compute cost; latency. Laboratory cost is wells and turnaround days with
shared controls charged once; provider spend is reported separately.

**Mandatory controls:** no model; simple model; qualified model; always-trusted; applicability-
scoped; valid prediction-shuffle. A lower prediction error does not by itself improve
intervention design, and must not be reported as though it did.

**Biological credibility** is isolated by comparing RNA-only against additional **measured**
modalities on the same eligible cases, separating that benefit from the benefit of more cases
or more spend. Test condition-aware against condition-agnostic retrieval, provenance-aware
against duplicated-source retrieval, and valid against permuted cross-scale links. Held-out
outcomes stay hidden from the knowledge base, retrieved summaries and model adaptation.

**Credibility is not measured by** citation count, graph connectivity, attention weight,
enrichment significance or agent agreement.

## 5. Data policy

Preference order: already public, condition-level, inexpensive to process, and deployable from
inputs available **before** the candidate is measured — structure, dose, time, cell background,
a matched control, and where applicable one existing measurement of the current action.

Three costs are stated separately for every asset: access and preprocessing; training and
running; and the inputs a genuinely new candidate requires at deployment. A published processed
feature table is not intrinsically cheap, and not intrinsically clean: check whether its
normalization or feature selection was fitted across all plates, including the test compounds.

Do not fabricate a paired modality for a single-modality sample. An imputed modality remains a
prediction with uncertainty and is never independent confirmation of its own input. Missingness
and detection limits are part of the interpretation, not silent zeros.

Asset-by-asset costs and licences: [`research/asrg/02_data_and_costs.md`](research/asrg/02_data_and_costs.md).

## 6. Tool qualification

Every adapter needs a manifest, typed input and output schemas, source and version, environment,
applicability, a validation example, cost, **explicit failure output**, and both `use_when` and
`do_not_use_when` conditions. Qualification states are `discovered`, `packaged`, `reproduced`,
`task_validated`, `active`; active does not mean universally valid. Dynamically retrieved code
is never imported directly into production.

Next qualified adapters, in order: `anndata_qc`, `condition_alignment`, `entity_normalization`,
`pseudobulk_differential`, `pathway_and_regulatory_analysis`, `perturbation_realization_qc`,
`primary_evidence_retrieval`, `virtual_cell_state`, `intervention_bundle_select`,
`workflow_schedule`.

## 7. Research sequence

| Phase | Focus | Gate |
|---|---|---|
| A | Evidence, identity, state and termination contracts | Adversarial cases pass with unified semantics |
| B | Persistent shared state and bounded delegation | Restart, failure and provenance reproduce |
| C | Multi-omics credibility and first bioinformatics tools | Supplied data yields traceable replicate-aware artifacts |
| D | Dependency-aware selection and scheduling | Solver agrees with small enumeration; handles complementary bundles |
| E | Qualify simple and virtual-cell predictors | Held-out accuracy, calibration and abstention scope documented |
| F | Downstream tasks, target and response first | Admitted tasks report all five levels; others stay pending |
| G | Evaluate, and optionally learn, the repair policy | Equal-resource independent cases test transfer |

Do not build a large multi-agent ecosystem before one complete evidence-bounded intervention
design works. Do not add a scale to fill a diagram; add it when it answers a defined question
and has a measurable bridge to another scale.

## 8. What no result here licenses

A passing result licenses one sentence: under a frozen protocol, at equal candidate sets and
equal budget, the agent's decisions were better supported than the named controls' on the tested
cases. It does not license a claim about target occupancy, mechanism, efficacy, clinical safety,
or transfer to an untested context, assay, time point or modality. Mechanism claims require
orthogonal functional, genetic or rescue evidence in matched conditions.
