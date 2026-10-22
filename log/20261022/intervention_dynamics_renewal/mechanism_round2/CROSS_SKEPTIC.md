# Actual cross-examination: selection-bound skeptic and mechanism advocate

Date: 2026-10-22. Participants: `selection_bound_skeptic` and `mechanism_advocate`. This is an actual two-way agent exchange, not a simulated debate. No network, measured response data, model fit, or biological validation occurred. The independent skeptical draft `SKEPTIC.md` was written before this reviewer read `ADVOCATE.md`. Messages were exchanged directly through collaboration tools after both drafts existed.

## 1. Advocate's questions and skeptical answers

**A1. Are scalar interval intersections sufficient as well as necessary under arbitrary fixed-type selection?**

Yes, for common-population aggregate marginals only. Choose `p` in the intersection, retain `Z_h` out of the initial type-one mass `p`, and retain `L_h-Z_h` out of type-zero mass `1-p`. These operations are feasible exactly when `Z_h <= p <= Z_h+delta_h`. This does not establish compatibility with measured paired founder IDs, nested histories, or full trees. The advocate explicitly accepted changing its draft from “necessary, not sufficient” to “necessary and sufficient for marginal null feasibility; passing does not prove the actual world has no memory.”

**A2. Which missing mass belongs in the challenge-response interval?**

Let `z_h` be known final live mass, `u_h` challenge-censored/unknown fate mass, and `delta_h` mass missing before challenge. Then the population response bound is `[z_h,z_h+u_h+delta_h]`, equivalently `[known B-live mass,1-known B-dead mass]` when a disjoint, complete mass frontier is accounted for. Known B deaths are response zero and do not widen the upper bound. Cells known dead during conditioning remain unknown for their counterfactual later B response and do widen it. Never count both a parent and its children. The advocate accepted each distinction.

**A3. What does rejection mean biologically?**

It rejects a strict fixed endpoint-response type plus selection explanation. It does not uniquely imply epigenetic memory, a new hidden state, or treatment-induced changes in transition rates. Residual drug, inherited damage, cell-cycle/age effects, mutation, and ordinary dynamic phenotypes can alter endpoint response. The advocate accepted the narrower statement.

**A4. Can state and response marginals locate a mediator?**

No. If `P(S=1)=P(Y=1)=1/2`, both `Y=S` and `Y=1-S` have the same observed marginals and opposite state-response relations. Same-lineage pairing would identify an association, not by itself a causal mediator. The advocate accepted not stacking separate marginal tests into a claim of state-mediated memory.

## 2. Skeptic's objections and advocate's explicit answers

**Q1. Randomization does not make finite treatment arms empirically identical.**

Counterexample: four founders contain two fixed responders and two fixed nonresponders; assign two to each arm. With no conditioning loss, two of the six assignments give empirical `Z=1` versus `Z=0`. A pointwise interval rule rejects under a true selection-only null with probability `1/3`. The advocate explicitly agreed that the constraint concerns a common population expectation, and an actual test requires the real treatment randomization/biological clustering and simultaneous uncertainty, not empirical nonintersection alone. Founder/cell numbers cannot silently replace independent biological runs.

**Q2. An unchanged response probability is not an unchanged realized fate.**

Two cells with identical fixed response probability `r=1/2`, zero loss, and independent challenge draws can produce `Z_1=1,Z_2=0`. The interval constraint applies to expected response mass after integrating challenge randomness. The advocate accepted explicitly separating deterministic latent fate from response probability and requiring statistical calibration for the latter.

**Q3. Half-split mass removes proliferation, including clinically relevant proliferation.**

Weights `2^-depth` describe a chronological random-daughter path, rather than uniformly sampled extant cells or total tumor burden. If one resistant founder expands to eight cells while a sensitive founder stays one cell, unweighted resistant fraction becomes `8/9` from `1/2`, while the founder-weighted response remains `1/2`. Drug utility can worsen while this identification statistic stays constant. The advocate accepted reporting cell number/absolute functional outcome separately and using `Z` only for the stated null. The statistic cannot be the sole application utility.

**Q4. Existing formulas plus an unauthenticated asset are not a core mechanism innovation.**

The scalar rule is a standard unknown-missing-outcome bound; the multistate rule is common domination of subprobability measures. The advocate explicitly agreed that the current status is a **source/design qualification candidate**, not a new core mechanism, world model, agent contribution, inheritance result, or RSI result. It accepted one bounded asset/closest-theory check before any architecture work.

**Q5. Treatment-independent spontaneous switching is an alternative to induced memory.**

If every division has the same treatment-independent probability `a` of switching `0 -> 1`, conditioning that changes the generation count `d` changes random-lineage response probability to `1-(1-a)^d`, even with no loss and no treatment-specific transition rule. The strict fixed-type bound may be violated without an induced memory mechanism. The advocate accepted this counterexample and agreed that an ordinary generation-aware switching/birth-death model is a required explanation/baseline before inventing memory. It said it would replace “world model must allow lineage-internal functional state change” with the narrower “must go beyond fixed-type selection; ordinary pre-existing dynamics plus changed generations may suffice.”

## 3. Additional precision from the two-way exchange

The advocate asked whether a common history-invariant measurement kernel `K(observed | fixed latent type)` preserves the state constraint. The skeptical answer was: if retained latent measures `a_h <= p` and `q_h=K a_h` with the *same* nonnegative kernel, then `q_h <= Kp` and a common dominating observed-state distribution exists. This is a population/expectation claim. A kernel merely specified for unselected cells need not be the relevant conditional kernel after selection on unmodeled assay variables. History-dependent `K_h` can manufacture observed-state rejection through assay artifacts or readout dynamics, with no drug-response conversion. Finite measurement draws still need inference.

The advocate also asked whether passing separate state and response bounds guarantees a joint fixed-state/fixed-response selection model. It does not. This reviewer supplied a stronger explicit example in the actual exchange:

| History | Retained mass L | State A mass | State B mass | Challenge-live mass Z |
|---|---:|---:|---:|---:|
| h0 | 1 | 1/2 | 1/2 | 1/2 |
| h1 | 1/2 | 1/2 | 0 | 1/2 |
| h2 | 1/2 | 1/2 | 0 | 0 |

The state bound passes with sum of maxima 1. Response intervals intersect at `p=1/2`. But h1 forces initial `P(A,Y=1) >= 1/2`, h2 forces `P(A,Y=0) >= 1/2`, whereas h0, which retains all mass, forces `P(A)=1/2`. No common joint fixed-type distribution exists. This illustrates information lost by separate summaries. It is a standard joint partial-identification/coupling problem, not itself an established new theorem or mechanism.

The table assumes that each row's state and functional masses are authentically tied to the same history, population/initial cohort, denominator, and relevant run/design interpretation. It does not permit pairing a reporter figure with a different colony experiment merely because a condition has the same name. Cell-level state-to-fate pairing is not needed for this particular extremal marginal contradiction; trustworthy condition/run-level linkage is needed. The common fixed joint type and a deterministic response target (or correctly integrated expected response with its observation model) remain substantive null assumptions.

This also limits the opposite overstatement: missing within-history pairing prevents identifying the state-response association in general, but it does **not** imply that all joint-null restrictions become untestable. Some extreme marginal combinations already exclude a common joint model. A practical joint feasibility analysis would need its own precise null, measured common cohort/run interpretation, and uncertainty; this exchange does not authorize adding a new module.

The advocate's last supplemental question was whether agreement with existing theory and a result consistent with the broad null should stop promotion to a core mechanism. This reviewer answered yes: retain any honest scientific null-test use, but do not call it a new core or completion of the requested research framework. The advocate subsequently explicitly accepted all three supplemental answers, including the common-kernel qualification and the three-history joint-capacity witness, and stated that no core dispute remained. It preserved its independent original as `ADVOCATE_INDEPENDENT.md` and revised `ADVOCATE.md`; those revisions are responses to the debate rather than independent corroboration.

## 4. Independent review of root's exact logical audit

This reviewer read `research/intervention_dynamics_renewal_20261022/selection_null_audit.py`, `LOGIC_PROTOCOL.md`, and `LOGIC_RESULT.json` without executing `main`, overwriting outputs, or reading measured data. The inspected code snapshot had SHA256 `b4a7e9040f554d76c90b6bf6779d7a6cfc6fd7e824c119718da9d1925a646392`. Subsequent root supplements, if any, need a separate review statement; the following refers to the original audit.

Static review found the enumeration and witness constructions consistent with their stated scope:

- Binary: all type assignments over four founders and all independent history-specific retention masks for three histories yield exactly 1,443 feasible summaries out of 3,375 candidates; the interval test selects exactly the same set. Selecting `K=max Z` responsive founders supplies the explicit finite-integer witness.
- Three categories: all type assignments over three founders and all masks for three histories yield exactly 1,478 of 8,000 candidates; the sum-of-maxima test selects exactly that set.
- Binary interval and two-category sum-of-maxima tests are algebraically identical; code checks this for all binary candidate records.
- The `2/6` randomization false-point-gate example and `1/2 -> 8/9` unweighted proliferation example are exact rational constructions. Their interpretation is limited to mathematical cautions.
- The three-state witness in which each history retains mass `1/2` in a distinct category passes each category's isolated binary interval but has global sum of maxima `3/2`. This correctly illustrates why exhaustive labels require a simultaneous probability-mass constraint.

The exact audit is a useful implementation/proof check. It is not a measured biological result, a novelty audit, a calibrated statistical test, or evidence of world/agent/RSI benefit.

### Supplemental exact joint witness audit

After the root registered and ran a separate supplement, this reviewer statically read `selection_joint_audit.py`, `JOINT_LOGIC_PROTOCOL.md`, and `JOINT_LOGIC_RESULT.json` without rerunning `main` or modifying the result. Independent `Get-FileHash` reads confirmed code SHA256 `281629b3f4ff8379a3360ca5bdf9e0abbaf303f3572d211f209a90a1cf45b0ea` and protocol SHA256 `0a590d18318ae15034c4a46d957dcad25dbca5562aacf7e58369eec738fcd4d4`, matching the retained result.

The enumeration covers exactly `4^2 * 4^3 = 1024` joint-type/mask configurations for two equal-mass founders, binary state, binary deterministic response, and three histories. The reported 392 distinct observable marginal summaries are consistent with the projection implemented in the code; the independent review did not recompute that count. The negative record `q=((1,1),(1,0),(1,0)), Z=(1,1,0)` in half-mass units passes both separate tests but is absent from the joint feasible set. The positive record with the same q and `Z=(1,1,1)` is present: choose founders `(A,response1)` and `(B,response0)` and retain only A in both shortened histories. The assertions and proof interpretation are correct at this finite deterministic common-population scope. No stochastic challenge, biological observation, new identification theory, or predictive-performance claim follows.

## 5. Remaining uncertainty and decision

There is no remaining disagreement in the exchanged core mathematical or biological-scope objections. The source asset, closest primary-theory precedence, finite-run test/power, application utility, and added value beyond known identification tools remain unresolved. No qualified public dataset was established in this review.

Recommendation: retain only a bounded source/theory qualification candidate. Stop architecture expansion and promotion to a core innovation at this stage. If a suitable public design later exists, preregister one narrow selection-robust response claim and compare it with the ordinary dynamic alternatives above. A positive identification result would still leave the user-requested world-model, agent, inheritance, joint, and improver-improvement contributions untested.
