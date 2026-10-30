# CDI fresh-context challenge (2026-10-30)

## Scope and evidence boundary

This is an independent conceptual challenge of the supplied CDI summary only. I did not inspect prior MAESTRO discussions, project reports, `src/tools`, or literature, and I ran no scientific-effect experiment. The judgments below are therefore mechanism and identifiability judgments, not a verified novelty or efficacy claim.

I interpret (A,B) as two compounds intended to act on one target, (C) as a cell background, (y) as a pre-specified functional endpoint, and Δa as a relative affinity feature measured or predicted under a stated assay condition. Unless a design explicitly supplies otherwise, dose, exposure, time, assay scale, and batch are assumed to be comparable.

## Verdict

As written, CDI is mostly a composition of standard pieces:

| CDI component | Ordinary formulation | What could remain distinctive |
|---|---|---|
| (D=[y(A,C_1)-y(B,C_1)]-[y(A,C_2)-y(B,C_2)]) | A two-by-two factorial interaction contrast. It is called difference-in-differences only if (C_1,C_2) are valid control/time dimensions with the needed common-trend assumptions; two cell backgrounds alone do not make a causal DiD. | A pre-registered measurement and intervention contract that makes the interaction diagnostically interpretable. |
| Virtual cell learns when Δa predicts Δy | Hierarchical/mixed-effects or conditional response regression, possibly with measurement error and nonlinear occupancy. | A model whose output is a falsifiable attribution of the failure mode, rather than a better response score. |
| Agent chooses drug-pair/cell-pair experiments | Active learning, Bayesian optimal design, value of information, or model-discrimination design. | The action objective is expected separation of named failure models under equal cost, with an explicit stop rule. |
| AdaMBind-style new-target adaptation | Few-shot/meta-learning/domain adaptation. | It is a later transfer test, not the central mechanism. |
| PBCNet2.0 or measured Δa | A covariate or noisy prior in a hierarchical model. | Only a calibrated uncertainty-bearing prior tied to absolute affinity/exposure can support a mechanistic claim. |

Therefore the full stack should not be presented as a new architecture or as an already-established scientific capability. The smallest potentially defensible contribution is a **matched structural-to-functional diagnostic design**: paired compounds and cell contexts are selected, together with target, exposure, and assay controls, to distinguish pre-registered explanations for a structure-to-cell-response failure. The novelty would be in the estimand, controls, attribution, and stopping rule. Without those contracts, CDI reduces to hierarchical regression plus active learning/VOI plus few-shot transfer.

## Conditions required for identification

The contrast is only interpretable if the following conditions are explicit and checked.

1. **The estimand and scale are fixed.** Raw viability, log viability, logit viability, growth rate, and an Emax parameter give different interaction contrasts. Choose the scale before seeing results and retain a replicate-level error model. A bounded or saturating endpoint can create a nonzero (D) by scale choice alone.

2. **The pair is comparable for the intended question.** A and B need matched target identity, concentration/exposure and assay timing. Their selectivity, efficacy, residence time, chemical stability, and obvious off-targets must be recorded. A structural difference that changes many properties cannot be attributed to affinity alone.

3. **Δa is calibrated and sufficient for the proposed link.** Record whether Δa is measured or predicted, its assay temperature/construct/ligand state, uncertainty, and model version. Relative affinity alone is generally insufficient when absolute affinity, target abundance, occupancy, efficacy, or kinetics affect (y); the model must retain (a_A,a_B), concentration, or a justified occupancy transform when needed.

4. **Exposure is observed or controlled.** Intracellular free concentration, uptake, efflux, protein binding, and degradation can vary by cell background. A relation between Δa and (y) is not identified if the observed difference is actually a relation between exposure and (y).

5. **Cell backgrounds are measured and have support.** (x_C) should include at least target abundance/alteration and relevant transport, pathway, growth, and media variables, with passage/lot and cell-state metadata. Two backgrounds identify one contrast; they do not identify a moderator function. Learning a virtual-cell rule needs multiple backgrounds and held-out backgrounds with overlap in Δa and exposure.

6. **The factorial assignment is randomized and blocked.** A and B must be measured in the same plate/block, with both backgrounds represented on each relevant day and independent replicate days. Plate, operator, reagent lot, and position cannot be confounded with compound or cell background.

7. **Target dependence has a counterfactual.** A target knockdown/knockout, rescue, orthogonal target-engagement assay, or another justified intervention is required if the claim is that Δa explains a target-mediated component. An untreated parental line is not a target counterfactual.

8. **The four proposed failure classes have separable predictions.** Structural misspecification, insufficient target dependence, cell pharmacology, and assay mismatch must differ under at least one allowed intervention. If every class predicts the same distribution for the available actions, no agent can identify the cause.

9. **Information and splits are clean.** Candidate selection cannot inspect held-out (y). New-target adaptation needs target-level support/query splits with no compound, scaffold, assay-day, or target leakage. The equal-budget unit must include controls and failed assays, not just successful measurements.

10. **Non-target terms are either invariant, measured, or intervened on.** For example, write a decomposition such as

   [
   y_{d,c,b} = \mu_c + \tau_{d,c} + e_{d,c} + o_{d,c} + q_{d,b,c} + \epsilon,
   ]

   where τ is target-mediated response, (e) exposure/cell pharmacology, (o) off-target response, and (q) assay/batch. The pair contrast and (D) remove a term only when its A/B difference is zero or stable across contexts. Cell-dependent exposure, off-target expression, or unbalanced batch therefore remains in (D) unless measured or controlled.

## Counterexamples that break the proposed inference

| Counterexample | What CDI could observe | Incorrect inference | Required discriminator |
|---|---|---|---|
| A is more lipophilic and C1 has higher uptake/efflux than C2 | (D\neq0) and even an apparent Δa slope | The target-affinity prior transfers through cell state | Intracellular exposure or matched-exposure assay; transport controls |
| A and B have similar affinity but different efficacy, residence time, or allostery | Δa ≈ 0 but Δy is large | Affinity model is misspecified in a way a virtual cell can repair | Absolute affinity plus efficacy/kinetic and target-engagement measurements |
| Both compounds saturate the target at the chosen dose | Large Δa but Δy ≈ 0 | Target dependence is absent | Dose/occupancy series at a non-saturating regime |
| One compound has an off-target pathway active only in C1 | Context-specific (D) | Cell variables explain target-mediated affinity transfer | Off-target panel, target perturbation, and pathway controls |
| A is always on one plate or cell background is always on one assay day | Stable-looking (D) | A cell-background mechanism exists | Randomized blocked replication across days and plates |
| Raw viability is analyzed on an additive scale | (D) changes sign or size after logit/Emax transformation | The biological interaction is real | Pre-registered endpoint scale and replicate-level measurement model |
| Only C1 and C2 are available | Any two observed points can be fit by many virtual-cell functions | The background rule is learned | More contexts, overlap, and a held-out context |
| PBCNet predictions share chemotypes or target data with the test set | Strong apparent new-target adaptation | AdaMBind transferred mechanistically | Target-level, scaffold-aware, time-split leakage audit |

These are not rare edge cases; each is compatible with the supplied summary. A nonzero (D) is therefore evidence of a compound-by-context interaction, not evidence by itself of target-mediated structure-to-function transfer.

## Minimal mechanism worth retaining

Retain only a **pre-registered paired-interaction diagnosis**:

1. Use replicate-level outcomes for a matched A/B pair and model both absolute affinities (or an explicitly justified occupancy transform), dose/exposure, cell covariates, and batch. Use (r_{AB,C}=y(A,C)-y(B,C)) and report (D=r_{AB,C_1}-r_{AB,C_2}) as an interaction estimand, not as an automatic causal DiD.
2. Freeze four model classes before selection:
   - **M1, structural/target-mediated:** the A/B response difference follows calibrated affinity/occupancy and is attenuated by target perturbation.
   - **M2, target-insufficient/null:** the response difference does not change as predicted under target perturbation.
   - **M3, cell pharmacology/exposure:** adjusting or matching exposure/transport removes most of the apparent affinity relation.
   - **M4, assay mismatch:** the relation disappears under plate/day-balanced replication or an orthogonal endpoint.
3. Let the agent choose the next pair-by-context-by-control for expected posterior separation among M1–M4 at equal cost. This is model-discrimination VOI, so the comparator must be ordinary hierarchical regression plus random or standard VOI selection with the same candidate pool and budget.
4. Stop when the models are observationally equivalent under the available interventions. Do not add a larger virtual cell, meta-learning, or an architecture change to rescue an unidentifiable design.

AdaMBind-style adaptation and a broad virtual-cell representation can be tested later, only after this core diagnostic contrast survives strict held-out contexts and target perturbation. They are extensions, not required components of the mechanism.

## Data contract

The minimum contract should be versioned and immutable before agent selection.

- **Drug table:** canonical structure/stereo/tautomer, drug and target IDs, pair ID, (a_A,a_B,Δa), source (measured/PBCNet), uncertainty, assay construct/temperature/ligand state, concentration/dose, exposure measurements, selectivity/off-target panel, lot and stability.
- **Cell table:** cell ID and background vector (x_C), target expression/copy-number/mutation state, pathway and transporter variables, growth/media state, passage/lot, perturbation/rescue status, and the date of these measurements.
- **Pair and intervention table:** matched-pair rationale, target engagement, parental versus knockdown/knockout/rescue, exposure/transport control, orthogonal assay, and which M1–M4 prediction each arm tests.
- **Assay table:** replicate-level raw (y), endpoint units and transform, dose/time, plate/day/operator/reagent lot/well position, randomization/block, censoring and QC flags. Preserve raw data; do not make a normalized value the only record.
- **Selection ledger:** candidate pool, frozen model versions and priors, expected information for each action, selected action, cost, budget remaining, and whether any outcome was available when the action was chosen.
- **Split/provenance table:** target-level support/query/holdout labels, scaffold and compound-overlap checks, affinity-model version, training-data provenance, and hashes or stable IDs for input snapshots.

At least three measured cell contexts are needed to estimate a context moderator; two contexts can supply a single planned contrast but cannot validate a virtual-cell rule. Every selected A/B pair needs both compounds in the same blocked assay, replicated across independent days. If exposure or target-engagement measurements are absent, the corresponding attribution claim is out of scope rather than imputed.

## Stopping and advancement rules

Stop the CDI line if any of these hold:

- (D) is not reproducible within the pre-specified assay variance, or its interpretation depends on an unregistered endpoint transform.
- Target perturbation does not selectively change the proposed target-mediated component, and exposure/off-target controls cannot separate the alternatives.
- A simple hierarchical model using the same inputs and budget explains the response and the agent adds no out-of-sample model separation.
- M1–M4 remain observationally equivalent for all affordable actions; expected information is below the assay-noise/cost floor defined before data collection.
- The relation fails on held-out contexts or strict held-out targets, or apparent AdaMBind gain is attributable to target/scaffold/assay leakage.
- An essential data-contract field is missing or post hoc; do not reinterpret the missing measurement as evidence for a mechanism.

Advance only when a target/exposure/assay intervention produces a reproducible pattern that distinguishes at least one model class, and the same diagnostic choice improves attribution per equal cost against hierarchical-regression and standard-VOI baselines. Numerical cutoffs should be set from replicate variance and a pre-registered minimum discriminating effect; none is justified by the summary alone.

## MAESTRO recommendation

**Conditional GO for one small falsification pilot; NO-GO for the full CDI stack.** The pilot should answer whether (D) contains target-dependent information beyond exposure and assay artifacts, not whether a large virtual cell or AdaMBind improves a benchmark.

A minimal planned pilot is one well-characterized target, two or three A/B pairs spanning a meaningful range of absolute/relative affinity (including a near-null pair where available), at least three measured cell contexts or two contexts plus a target-perturbed/rescue arm, randomized blocked replicates across independent days, intracellular exposure or a justified matched-exposure control, and an orthogonal target-engagement or endpoint readout. Freeze M1–M4 and the candidate pool first. Let the agent choose only the next diagnostic action after an initial balanced block, then compare equal-cost model separation with random selection and ordinary VOI. The success criterion is a reproducible attribution pattern on held-out context/day; a mere predictive score gain is insufficient. If the pattern is exposure-driven, assay-driven, or non-identifiable, stop and retain the negative result.

This pilot is worth doing only if the data contract and target-specific intervention are already feasible. If they are not, CDI should be parked as an ordinary regression/active-learning proposal rather than expanded with more modules.

## Decision summary

- **Ordinary methods?** Yes for the individual components and for the full stack as currently specified.
- **Potentially defensible core?** A matched factorial interaction plus orthogonal controls, model-discrimination acquisition, and a hard non-identifiability stop rule.
- **Main risk?** (D) conflates target effect, exposure, off-target pharmacology, and assay/batch variation; two contexts and relative affinity alone do not identify them.
- **Minimum next action?** A preregistered identifiability/falsification pilot, not model scaling or full transfer evaluation.
- **Novelty status?** Unverified. This fresh challenge did not perform a prior-art search; no first-ever or efficacy claim is warranted.
