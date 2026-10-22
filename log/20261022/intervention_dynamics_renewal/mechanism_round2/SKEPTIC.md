# Independent skeptical review: conserved lineage mass and selection bounds

Date: 2026-10-22. Reviewer: selection_bound_skeptic. This draft was written without reading `mechanism_round2/ADVOCATE.md`. Scope: mathematical audit only; no network, response data, fitted model, or biological experiment. The task supplied the two proposed inequalities. A mathematical possibility result is not evidence for cell memory, a world model, an agent, inheritance, or RSI.

## Judgment before cross-examination

Both inequalities are correct as **sharp marginal feasibility bounds under a particularly strict, deterministic, fixed-response-type null and a common initial population**. The proposed scalar interval is exactly the binary missing-outcome worst-case bound. The multistate bound is the existence condition for a probability measure that dominates every observed subprobability measure. These are useful selection audits, but the formulas and mass accounting alone do not establish a new core algorithm or a broad biological memory claim.

There remains a falsifiable empirical use: show that real, carefully tracked, randomized conditioning histories violate an attrition-robust fixed-response null on a clinically useful later drug endpoint. That can be scientifically informative even with a known inequality. It needs an authenticated lineage/state/function dataset, a calibrated sampling test, and a biological question not already answered by the original study. It is currently a conditional candidate, not an established contribution.

## 1. Precise scalar theorem

Normalize initial founder mass to one over a common population. Let `T` be a founder's fixed binary challenge response, inherited by every descendant: `T=1` means that all retained mass survives the standardized challenge and `T=0` that none survives. Let `S_h in [0,1]` be the fraction of initial lineage mass remaining immediately before challenge after history `h`. Splitting mass equally between two daughters preserves mass; death removes mass. At the population or exact common-cohort counterfactual level,

```
L_h = E[S_h] = 1 - delta_h
Z_h = E[S_h T]
p   = E[T]
```

Then `p-Z_h = E[(1-S_h)T]` lies in `[0,delta_h]`, so

```
p in [Z_h, Z_h + delta_h] for every h.
```

Thus `max_h Z_h <= min_h (Z_h + delta_h)` is necessary. It is also sufficient for existence of *some aggregate population-level null model* when these are the only constraints and `0 <= Z_h <= L_h <= 1`. Pick any common `p` in the intersection. For each history retain type-one mass `Z_h` out of `p`, and retain type-zero mass `L_h-Z_h` out of `1-p`. The two feasibility requirements are precisely `Z_h <= p` and `L_h-Z_h <= 1-p`. Arbitrary selection can realize these histories, with an arbitrary coupling between histories conditional on `T`. Boundary `p=0` or `p=1` follows by setting the absent type's mass to zero.

**The sufficiency statement is limited.** It does not say that the observed full lineage records, founder identities, temporal transitions, nested histories, integer finite cohorts, or common early branches admit that null. It says the supplied aggregate marginal summaries do. Additional measured links can refute a null that passes these summaries.

## 2. Multistate theorem and relation to the scalar theorem

Suppose `K` is a prespecified exhaustive finite set of labels and every descendant retains its founder's same label throughout all conditioning histories. Let `q_h(k)` be retained initial mass of label `k`. The common initial label distribution `p(k)` must obey `p(k) >= q_h(k)` for all `h,k`, with `sum p(k)=1`. Therefore

```
sum_k max_h q_h(k) <= 1.
```

This is necessary and sufficient for aggregate marginal feasibility under unrestricted selection: set `p(k)=max_h q_h(k)` and place the remaining mass arbitrarily among allowed labels. If an initial `p` is measured or biologically constrained, this maximization condition is too weak; each `q_h(k) <= p(k)` must hold with uncertainty propagated from that initial measurement.

For binary deterministic response, use `q_h(1)=Z_h`, `q_h(0)=L_h-Z_h`. The multistate bound becomes

```
max_h Z_h + max_h (L_h-Z_h) <= 1,
```

which is algebraically identical to the interval-intersection bound. These are two presentations of the same binary constraint, not separate independent modules or pieces of confirming evidence.

For two histories, `sum max(q_1,q_2) = (L_1+L_2+||q_1-q_2||_1)/2`. For equal retention `L=1-delta`, if `r_h=q_h/L` are normalized live-state distributions, feasibility requires `TV(r_1,r_2) <= delta/(1-delta)`. At `delta >= 1/2` this two-history bound cannot reject any pair of live-state distributions. This is an explicit loss-of-power condition, not a reason to hide missing or dead lineages.

**Critical logical distinction:** fixed drug-response type does not imply that an arbitrary measured live-state label (cell cycle, AP-1 activity, morphology, RNA bin) is fixed. The multistate test can reject a fixed-*state*-label null while every cell's drug response remains unchanged. It cannot be advertised as a drug-response conversion test unless the labels themselves are authenticated stable response types, or the joint null explicitly fixes both.

## 3. Strict counterexamples to overbroad interpretations

1. **Stochastic challenge invalidates a pathwise fixed-probability test.** Two histories have no loss, `delta_1=delta_2=0`. All cells have the same unchanged drug survival probability `1/2`. One observed challenge survives and the other dies, giving singleton intervals `[1,1]` and `[0,0]`. This occurs with positive probability under unchanged susceptibility. The inequalities remain valid for expected survival probability `E[S_h r]`, `r in [0,1]`, but independent Bernoulli observations require sampling uncertainty. A type that means a fixed response *probability* is not a type that forces identical realized fate.

2. **Independent founder samples do not share an empirical baseline.** One founder per arm is drawn independently from a population with half fixed-resistant founders and no conditioning loss. One resistant founder and one sensitive founder produce the same nonintersecting intervals even with a deterministic challenge. With these sample sizes it happens with probability `1/2`. Randomized arms share a population distribution, not an exactly equal realized type composition. Testing needs a founder/run randomization or sampling model; treating all descendant cells as independent falsely narrows uncertainty.

3. **State change need not be response conversion.** All initial cells are B-resistant and all survive B under either history; no mass is lost. History 1 puts every live cell in an AP-1-high measured state, history 2 puts every live cell in AP-1-low state. `q_1=(1,0), q_2=(0,1)` gives sum of maxima 2, rejecting fixed state labels. Yet fixed B-response type is true. The scalar response bound passes. State labels cannot silently replace response types.

4. **Aggregate feasibility need not imply the observed paired records are null-compatible.** Two matched founders a,b survive conditioning under both histories. Under h1 their deterministic challenge responses are `(1,0)`; under h2 they are `(0,1)`. Both aggregate `Z` equal 1/2 with zero loss and the interval test passes. In the paired data each founder has changed response, which the strict inherited-type null forbids. Thus 'sufficient' applies to unlinked marginal summaries, not all obtainable lineage evidence.

5. **Unlogged censoring can manufacture a violation.** Suppose the initial population is half resistant and half sensitive. History 1 loses observation of sensitive cells, history 2 loses observation of resistant cells; no biological conversion occurs. If exit from field/segmentation failure is omitted from missing mass, retained denominators can be reset to one and observed response becomes 1 versus 0 with reported loss zero. The false rejection disappears when all unobserved initial mass is conservatively included in `delta`. Tracking incompleteness is part of the target's identification, not a nuisance to impute away.

6. **Fixed intrinsic response parameters need not imply fixed endpoint survival.** Identical inherited per-division drug damage or kill probability can produce different time-horizon survival if conditioning changes division timing. A bound violation would refute a fixed endpoint-response null, while a broader no-mutation/no-stable-conversion model with reversible physiology remains possible. The biological null must be stated in endpoint terms; it cannot expand after rejection to all forms of selection-only physiology.

## 4. Division, challenge, measurement, and inference requirements

- **Mass and estimand:** weight `2^-depth` is conserved on a complete binary tree frontier (the usual Kraft/tree accounting). It represents following a random daughter at each split. It deliberately removes proliferation multiplicity, and therefore estimates a random-lineage functional outcome rather than cell-number tumor burden, biomass, or drug benefit. A treatment that greatly increases resistant cell count without death can have the same weighted response. Report an application-relevant functional measure separately. Calling this merely 'retrospective lineage weighting' risks a terminology error: uniformly sampling extant cells is a different, growth-biased retrospective measure.
- **Track completeness:** initial entrants, births, deaths, field exits, fusion, division arity, and unresolved branches must be logged. Never both retain a parent and its observed children on the same endpoint frontier. Binary halving is an explicitly chosen estimand; asymmetric division does not conserve physical biomass under halving. Unknown events need conservative mass bounds rather than fake exact `delta`.
- **Same challenge:** B dose, washout, residual conditioning drug, time origin, endpoint horizon, and medium should be controlled. A common drug name does not authenticate a common challenge. Delayed residual toxicity and state-dependent exposure must be distinguished from a persistent transferable response change when making a mechanistic claim.
- **Challenge branching:** weights must be defined at a prespecified frontier and carried consistently through challenge divisions and deaths. If `Z` is final living mass after challenge, the null must imply the expected/deterministic final mass response used in the theorem. 'Resistant type' without an endpoint response model is insufficient.
- **Labels:** choose state bins without outcome-dependent tuning; define whether they are fixed baseline identities or dynamic states; propagate misclassification. Searching state partitions or histories until `sum max q>1` needs the same search budget/multiplicity control as a comparison method. For high-dimensional noisy states, an apparent disjoint empirical support is nearly automatic and is not a valid population-measure rejection.
- **Independent units:** actual biological run and treatment assignment are the relevant clustering levels. Sisters and repeated frames share ancestors and exposures. Use the exact randomized treatment assignment when available; otherwise interval/likelihood estimation must respect founder and run dependence. A claim across future experiments cannot be justified by one run with many tracked cells.
- **Uncertainty:** a conservative implementation can use simultaneous lower confidence bounds on the `q_h(k)` and reject only when the sum of history-wise lower maxima exceeds one; scalar intervals similarly require simultaneous bounds on both `Z_h` and `Z_h+delta_h`. Simple plug-in violation magnitudes are not calibrated p-values. Joint covariance can improve power but must be modeled or obtained by a valid randomization/resampling design.

## 5. Closest theory and novelty boundary

Without fresh source retrieval, the relevant theory families are already recognizable: worst-case missing binary outcome/partial identification bounds (commonly associated with Manski), selection/attrition bounds (Lee-style trimming adds assumptions not present here), domination/coupling of subprobability measures, total-variation bounds, and conserved lineage-tree/path sampling. These names are a literature checklist, not a claim that specific theorem numbers or newest primary precedents were verified in this review.

The scalar interval is exactly `observed positive mass + unknown missing positive mass`. The multistate version is the corresponding common-baseline domination condition. Halving does an important accounting job but does not change this identification mathematics. Renaming them as a world model, a memory certificate, a lineage-conservation operator, or an RSI update would not supply a technical contribution.

Potential empirical novelty remains possible if, after primary-literature comparison, the work demonstrates a previously untested, useful selection-robust response conversion phenomenon on a uniquely appropriate perturbation/rechallenge system, or derives an additional sharp constraint from authentic temporal/paired branch links that the marginal bounds ignore. The latter needs a concrete observed design and a proof that the new constraint is neither a restatement nor dependent on unobtainable counterfactual lineages.

## 6. Recommended gate and stopping conditions

Proceed only to a small source/design gate: authenticate initial founder identifiers and independent run IDs; conditioning births/deaths/censoring; a later common challenge and its lineage-level endpoint; randomized/matched histories; and any state/function linkage. No dataset has been authenticated by this mathematical review.

Before response access, freeze the strict null, estimand, missing-mass treatment, independent unit, uncertainty test, minimum power/effect, and one biological claim. Compare conventional cell counts, unweighted survivor fractions, and the known partial-identification calculation to establish what lineage accounting adds. A direct predictor comparison is relevant for forecasting utility, but does not replace identification or by itself refute empirical novelty.

Stop promotion to a new core mechanism if only the existing marginal bounds and standard weighting remain; if the proposed dynamic state labels are not fixed under the tested null; if authentic challenge/lineage/censoring units are unavailable; if loss makes the bound vacuous; or if finite-run uncertainty explains apparent violations. Even a sound positive biological result would leave world-model benefit, agent benefit, inherited capability, and improver-improvement untested, requiring separate later gates.

This independent draft does not recommend architecture expansion or performance experiments yet.
