# Independent task review: dynamic collateral sensitivity in E. faecalis

2026-10-22. Role: scientific skeptic. **Decision: pursue one small, conditional phenotypic prediction gate; do not allocate to a new world-model/agent architecture or RSI on the current evidence.** This is a methods and source review, not an experiment result. No response matrices, network requests, numerical fitting, or assay values were used in this review.

## Evidence and exposure

Reviewed the locally acquired primary-source projections:

- `log/20261022/dynamic_source_followup/ncbi_scout/REPORT.md`
- `log/20261022/dynamic_source_followup/ncbi_scout/PRIMARY_METHODS_AVAILABILITY.json`
- `log/20261022/dynamic_source_followup/ncbi_scout/SWITCH_DESIGN_LITERATURE.json`

Primary paper: Maltas, Huynh and Wood, *Dynamic collateral sensitivity profiles highlight opportunities and challenges for optimizing antibiotic treatments*, PLoS Biology (2025), DOI `10.1371/journal.pbio.3002970`, PMC11709278. S1Data is `pbio.3002970.s001.xlsx`; the public archive DOI is `10.5281/zenodo.14064963`. Source acquisition, public file availability and actual row-level pairing are different claims. Another auditor is inspecting schema; this review does not duplicate that work.

The Methods, Results and Fig 4 caption have already exposed the paper's design and reported average sensitivity window. They cannot become a blind validation set merely by downloading the workbook later. Individual population trajectories and a frozen residual prediction question may still supply a legitimate retrospective held-out evaluation, with this exposure declared.

## What the original model already does

The original dMDP has a finite, discretized resistance vector as state; antibiotic as action; action-conditioned Markov transitions; negative resistance to the current antibiotic as reward; discounted cumulative reward; and value iteration. Its dynamic version uses collateral profiles from days 2, 4, 6 and 8. It propagates future-state values backward across time periods, because independently optimized local policies can enter states that become unfavorable under later profiles. The authors explicitly note that this requires knowledge of future reward/collateral profiles.

Consequently, a proposal whose new operation is “time-dependent phenotypic world model + antibiotic planning + feedback refit” has no established novelty here. A state-space model, Bayesian posterior update, refitting after assays, dynamic programming, or model-predictive control would each need a separate, non-equivalent technical contribution. A different name, LLM wrapper, added memory, or more elaborate architecture is insufficient.

The paper's empirical collateral measurements parameterize a simulated treatment model. They do not authenticate a measured transition table for every starting resistance state and every next antibiotic. Its simulated multi-drug control performance cannot serve as ground truth for an independently proposed controller unless that model dependence is the explicit question.

## Keep the two biological experiments separate

| Item | Main dynamic collateral-profile experiment | Separate timed challenge experiment |
|---|---|---|
| Biological scope | One V583 ancestor, 5 selection antibiotics, 4 evolution lineages per antibiotic | One V583 ancestor, 20 CRO-selected populations |
| Duration | 8 daily passages | 14 daily passages |
| Assayed times | Days 2, 4, 6, 8 | Daily samples |
| Readout | IC50 against the five test antibiotics; 3 or 4 technical repeats per dose-response | Daily sample challenged with DOX for 24 h; dose-response, IC50 and AUC sensitivity |
| Sampling identity | Methods specify plating and a single colony for IC50 determination | Results/Fig 4 describe a diluted sample from the continuing CRO parent population; exact workbook assay identity still requires confirmation |
| Legitimate unit | A selection-lineage trajectory | A CRO population trajectory |
| Unsupported extrapolation | Every sampled clone is a complete representation of its evolving population | The challenged branch continues evolving, returns to CRO, or undergoes repeated treatment switches |

The design product 5 × 4 × 4 × 5 agrees with the abstract's 400 strain-drug combinations; actual complete rows and identifiers remain unverified here. Twenty populations × fourteen days is not 280 independent research tasks. Technical repeats, concentrations, adjacent days and challenge drugs from the same lineage are dependent measurements.

Daily selection doses depend on prior visible growth: the highest growing concentration seeds the next day's doses. Dose is therefore an observed, history-dependent selection variable, not a randomized intervention. Include it only if recorded and genuinely available at the prediction cut. Do not infer an unmeasured causal dose effect from its association with later resistance.

The authenticated state is phenotypic resistance. A fully sequenced ancestor does not establish evolved longitudinal genomic or transcriptomic measurements. Lack of molecular state does not prohibit a useful phenotype task; it limits a molecular virtual-cell claim.

## Legitimate narrow task and the resource-changing gate

**Priority: the 20-population CRO→DOX experiment, conditional on persistent population/day identifiers and individual responses.** Its daily paired measurements are more useful for a first temporal feasibility test than splitting the four main-study lineages into many nominal tasks.

**Resource decision:** authorize only a small baseline pilot after identity qualification. The pilot asks whether an early measured DOX phenotype prefix predicts later population-specific DOX response beyond known calendar-time behavior and the most recent phenotype. A failure ends this source as a core adaptive world-model/agent benchmark; retain it only as a descriptive or external robustness source. Do not download new molecular data, build an LLM agent, or run broad architecture search before the gate passes.

Freeze the following before opening numerical response values:

1. Use the first six days as the available prefix, and days 8–13 as the future response interval. Day 7 is excluded to make the evaluation at least a two-day forecast. This interval is **design-exposed from the publication**, not a newly discovered sensitivity window. If these exact days are absent or individual trajectory identity is unavailable, reject this gate configuration rather than adapt it after inspecting outcomes.
2. Primary target: individual future DOX AUC sensitivity over the paper's documented 0.05–0.8 μg/mL interval. Compute it only if concentration curves, controls, units and normalization support the same quantity. Otherwise preregister a replacement IC50 target before examining its values; do not select the easier readout after seeing both. An already published AUC column is acceptable after its definition and identity are verified.
3. Split by whole population. A small, fixed development/test split can be committed by population identifier before response inspection; all days, technical repeats and controls derived from a population stay together. Use the development trajectories for any fitting and model choice. Never build the population-average day curve using a held-out trajectory's future values.
4. Compare a development-population mean day curve; that curve plus the held-out population's day-6 offset; and one deliberately small direct prefix predictor with fixed regularization chosen inside development data. The offset control captures ordinary persistence, which a proposed latent-state representation must surpass. The direct predictor receives exactly the same prefix; it tests usable information, without implying a world-model advantage. Any newly proposed method later receives the same assay access and fitting budget.
5. Score future AUC error per population, then compare paired population-level errors. **Pass only if the small prefix predictor improves over both the calendar curve and the last-response offset on the held-out populations, with the prespecified population-level uncertainty interval for its improvement excluding zero.** Freeze the uncertainty procedure and all tie/failure rules before fitting. This is a deliberately conservative allocation gate; with only 20 trajectories an inconclusive result is a stop for expansion, not evidence that biological state has no predictive information.

This gate has a specific practical purpose: determine whether there is demonstrated, exploitable variation beyond the paper's known mean timing pattern and ordinary persistence. It does not establish a new mechanism. It also makes no assumption that an early DOX assay is cheaper than directly measuring a later sample. The pilot conditions on an available early prefix; a later query policy must charge every assay it acquires.

If the gate passes, allocate the next block to a single frozen assay-allocation comparison: given a prefix and a fixed remaining assay budget, select which still-unqueried population/day DOX outcomes to confirm. Compare to day-only selection, persistence, random allocation, direct predictive uncertainty, ordinary active learning, and equal-budget small program search. Use only actual measured population/day outcomes as a retrospective oracle. Report confirmation utility under that menu; do not report multi-switch treatment efficacy. A useful query policy must improve an actual allocation decision, not merely reproduce the known days 8–13 group-average window.

## What could and could not be learned

- **World-model contribution:** a dynamical phenotype model must improve held-out temporal prediction or fixed-budget confirmation utility against the same-information direct predictor, simple Markov/history model and ordinary refit. A successful baseline information gate alone is not this evidence.
- **Research-agent contribution:** only data-supported experiment selection and update choices are currently credible. Revealing an archived response simulates information acquisition; it does not intervene on the original growing population. Compare fixed procedure versus adaptive procedure with identical acquired observations, computation and oracle costs where applicable.
- **Cross-experiment evaluation:** the main five-drug clone study could serve as a separate transport challenge or source of a predeclared prior. The biological material, selection duration and readout differ from the CRO population challenge. Any benefit is conditional cross-experiment phenotypic transfer, and must beat direct pooled training and simple mixtures. A common ancestor or shared drug is not a complete causal join.
- **Inheritance:** no evidence yet supports improvements that persist across independent later research tasks. Reusing weights or a response history within one CRO→DOX trajectory is ordinary state/model updating. Test inheritance only after locating genuinely subsequent tasks with frozen task boundaries and an equal-budget restart control.
- **RSI:** no editable improvement strategy or sequence of independent improvement opportunities has been established. Even positive model and query results would not demonstrate RSI. RSI would additionally require that a revised improvement procedure makes subsequent improvements more effective than the original improver under equal opportunities, with inherited artifacts and costs specified. These 20 replicate populations cannot automatically become an m0→m1→m2 research sequence.

## Objections, unresolved points, and decision

The strongest supporting point is a real daily intervention-associated functional readout on independently evolved populations; it avoids inventing unsupported molecular response labels. The strongest objection is that a single drug pair and ancestor, together with a published mean time window, may leave only a small persistence problem. The original dMDP further removes broad novelty from “dynamic resistance world model + planning.”

Unresolved at this review: whether individual population/day responses and persistent keys are public; whether daily selection concentration and CRO resistance are recorded; whether Fig 4 responses are population assays or colony-derived under the general IC50 Methods; assay-normalization details; and missingness. The schema auditor should resolve these identities without treating the Methods/Results wording conflict as settled by inference.

**Final recommendation:** keep this as a conditional, narrow phenotype forecasting and experimental-allocation lead. Run the small information/persistence gate once if schema permits. A negative or inconclusive gate stops framework expansion on this source. A positive gate buys one decision-utility experiment and a new independent novelty review; it does not buy claims of a virtual-cell mechanism, multi-switch control, inherited research capability, or RSI.
