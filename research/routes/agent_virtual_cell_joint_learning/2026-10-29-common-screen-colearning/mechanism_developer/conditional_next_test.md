# A conditional joint-susceptibility boundary and its smallest useful test

Frozen developer packet, 2026-10-29; version 1. Status: **constructive mathematical boundary, not a recommended new co-learning algorithm**. Independent challenge has not occurred. This follows `initial_alternatives.md`; it is the only developed line. No experimental outcomes, response counts or protected data were accessed. No experiment or author code was run.

## Finding and practical decision

Even complete monotherapy live-count trajectories can leave a combination decision unresolved because they do not necessarily say whether different drugs remove the same cells. The missing object is the **joint distribution of drug susceptibilities within a population**. It is different from the marginal birth/death rates of each drug. A count measurement after exposing the same surviving population to both drugs can reveal one part of that joint distribution.

This is not a claim that single-agent information is always uninformative about combinations. The construction below proves a boundary for a precise admissible preparation/action menu. It explicitly matches the **joint law of the entire permitted adaptive observation history**, rather than inferring joint indistinguishability from individually equal measurements.

The proposed user is a screening team deciding whether to retain a specified pair/dose/schedule for a population-depletion follow-up. The usable output is retain, reject or unresolved for a prespecified live-count threshold. Counts alone do not establish a molecular target, extinction of every resistant lineage, durable regrowth suppression, clinical benefit or drug-interaction mechanism.

## Exact model, inputs and action menu

The proof uses a deliberately small admissible model, not a biological description of HTS001.

1. Each well starts with an even, known total `n`, with exactly `n/2` cells of each of two stable latent types `z = -1,+1`. No phenotype conversion, density dependence or proliferation occurs during the analyzed window. Cell deaths are conditionally independent. A common known proliferation factor could be included for mean comparisons, but is unnecessary for the proof.
2. Drug `i` has a nonnegative physical-dose-dependent killing rate `k_i(d)` for one type and zero for the other. Its orientation `x_i in {-1,+1}` records which type resists it. The orientation stays fixed over the dose/time window. Rates may differ across drugs.
3. In the starting menu, every well receives vehicle or one drug. The learner can choose any concentration, any observation times, more repeats, and future monotherapy conditions adaptively. It may observe the complete path of each well. Fresh wells have independent cell-event randomness. There is no matched, randomly fluctuating mixture composition shared across different drugs, no lineage or susceptibility label, no biomarker anchor, and no second drug on an already treated well.
4. Observation noise, including any shared technical noise, has the same conditional joint law in the compared worlds and does not reveal the latent labels. No assumption that an observation is binary is made: the full count path is available.
5. The expanded menu adds a specified two-pulse schedule on the same well. Drug `i` is applied for its fixed pulse, then removed and drug `j` applied for its fixed pulse. Switching has no carryover or independent perturbation in this construction. A matched `i`-then-`i` schedule and vehicle exchanges control duration and handling in a real experiment. Simultaneous co-exposure would provide the same expectation under these constant additive-hazard assumptions, but real simultaneous interactions need not obey them.

The preparation and action assumptions matter. Matched clonal preparations, measured mixture fractions that vary jointly across drug arms, susceptibility biomarkers, switching interventions, or a trusted shared target-action law can break the symmetry. The proof does not deny information from such inputs.

## Proposition 1: equality of the full adaptive monotherapy history

Consider two drugs A and B. World S has `x_A = x_B`; world C has `x_A = -x_B`. Keep every `k_i(d)`, starting count, observation schedule, technical-noise law and all other parameters equal.

Under a single drug `i`, the complete latent count process is

`N_i(t) = n/2 + sum_(l=1)^(n/2) 1{T_il > t}`, with `T_il ~ Exponential(k_i(d))`.

This representation has exactly the same path distribution for either value of `x_i`. Concentration/time changes for that same drug can replace exponential survival by the corresponding cumulative hazard without revealing which latent label is sensitive. Vehicle observations are also identical. Repeated wells remain jointly identical by the stipulated preparation/noise law.

For an adaptive policy, suppose the acquired history up to step m has the same law in both worlds. The policy therefore chooses its next legal action with the same conditional distribution, including any independent randomization. Given that action and history, the new path/count observation has the same law because its drug's orientation is unobserved and the well is a fresh, balanced preparation; further observations of an already tracked monotherapy well also have the same full-path conditional law. The extended history thus has the same law. Induction establishes equality for every finite budget and every stopping rule based on that history.

Consequently, no policy restricted to that menu can uniformly choose different correct answers in S and C, even with unlimited exact monotherapy trajectories. If the correct decision differs between the two worlds and they have equal prior probability, any randomized decision based only on that history has average error at least 1/2. This is a conditional identification result, not a lower bound for all possible biological experiments.

The proof also extends to D drugs: all `2^(D-1)` orientation patterns modulo a global label swap have the same complete monotherapy history law. It does not rely on discarding continuous observations or on giving a weak baseline less history.

## Proposition 2: one permitted joint exposure can separate the worlds

For equal rates and pulse durations, let `s = exp(-k tau)`, with `0 < s < 1`.

| Quantity | World S: same susceptible type | World C: complementary susceptible types |
|---|---:|---:|
| Single A or single B after tau, expected count / n | `(1+s)/2` | `(1+s)/2` |
| A followed by A after 2 tau | `(1+s^2)/2` | `(1+s^2)/2` |
| A followed by B after 2 tau | `(1+s^2)/2` | `s` |

The last-row difference is `(1-s)^2/2`. It arises because in S the initially resistant half survives both pulses, whereas in C each half encounters one effective pulse. These two-pulse schedules are order symmetric in this model: AB and BA agree. Thus a search restricted to **order asymmetry** could miss the relevant static complementarity.

An exact decision example uses `s = 1/4`. Both worlds have monotherapy surviving fraction `5/8`. AB leaves `17/32 = 0.53125` in S and `1/4 = 0.25` in C. A target of at most `0.30` of the initial live count therefore retains AB only in C. AA leaves `17/32` in both. These are exact expectations in a thought experiment, not observed biological results or completed simulations. Finite-count and measurement variability require replication to make a statistical decision.

The smallest observation that can separate these two specific worlds is a full continuous live-count observation under AB at the specified endpoint, with a qualified matched baseline/control. Additional monotherapy doses, timestamps or technical repeats do not do so under Proposition 1. A single noisy physical well does not guarantee separation.

## Shared learned object, exact update and quantitative resource comparison

For D drugs, allow different within-sensitive-type surviving fractions `s_i`. Define

`a_i = (1+s_i)/2`, `b_i = (1-s_i)/2`.

At the fixed dose/pulse, a type-z cell survives drug i with probability

`q_i(z) = a_i + b_i x_i z`.

The normalized expected surviving count after the two pulses is

`C_ij = E_z[q_i(z) q_j(z)] = a_i a_j + b_i b_j x_i x_j`.

The potentially shared learned object is therefore the orientation vector `(x_1,...,x_D)` modulo a global sign, or equivalently the rank-one susceptibility matrix `U_ij = x_i x_j`. It is not a representation of molecular cell identity. All monotherapy histories can estimate the marginal rates/survival fractions but leave U unchanged.

For `b_i b_j > 0`, a noiseless exact pair expectation gives

`U_ij = (C_ij - a_i a_j)/(b_i b_j)`.

The resulting update is an ordinary signed-graph constraint. For the following theorem, D counts only active drugs with `b_i > 0`, D is at least 2, and the marginal parameters are treated as already known. Observing edge `(i,j)` links the relative orientations of the two nodes. A spanning tree of D-1 such edges identifies every orientation relative to an arbitrary root and hence every unmeasured pair expectation. Fewer edges leave at least two disconnected components; flipping all signs in one component preserves every acquired edge and monotherapy observation but changes cross-component pair expectations. Thus D-1 edges are necessary and sufficient **for recovering all pair means in this restricted, noiseless, pair-only query model**. Exhaustively measuring D(D-1)/2 pairs is unnecessary under its assumptions. A drug with `b_i = 0` has no relevant orientation, so it must not be counted in this lower bound.

The corresponding acquisition rule is elementary: choose a pair that connects two presently disconnected components whose relative orientation could alter a pending decision. With noisy measurements, expected decision loss or uncertainty may guide repeats, but that is standard experimental design and does not inherit a new guarantee from the noiseless result. A noisy likelihood update can sum over binary orientations using the observed continuous pair counts; it must not discretize counts to create an artificial information advantage.

This quantitative saving does **not** support an agent-specific claim. A signed-graph solver, a rank-one factor model, ordinary combination-response matrix completion or a Bayesian experiment-design policy over the same latent object achieves it. For a single target pair, measuring that pair directly is one condition and can be cheaper than learning a transferable structure. D-1 counts experimental **conditions with exact expectations**, not physical wells or costs. Baseline wells, single-agent calibration, switches, controls, biological preparations, repeats, failures and model audits all require payment. No physical-well saving has been demonstrated.

## Exact closest-prior comparison and unresolved novelty

- **BESTDR:** already estimates drug-specific kinetic rates from common count observations and shares them across backgrounds. Our proof supplies marginal kinetics equally in both worlds. What differs is an across-drug susceptibility alignment not fixed by those marginals. This is a task/information distinction, not evidence that BESTDR claims to solve the constructed pairing problem or cannot be extended to it.
- **Wu et al. 2025:** already posits multiple phenotypes, estimates plasticity and uses full trajectory covariance. A model with shared, biologically anchored phenotype identities across drugs or appropriate joint interventions can represent and infer U. The construction shows that count-only monotherapies in the specified preparation do not supply those anchors. It does not claim that a more general model must fail when the requisite information exists. The Sec30 LLN implementation nuance is unrelated to this symmetry proof.
- **Independent drug action / Bliss / resistance overlap / Palmer–Sorger:** classical strong prior families, not claimed newly discovered here. Algebraically, multiplication of marginal surviving fractions gives `a_i a_j`; both S and C have these same marginals, but true pair means differ by `+b_i b_j` and `-b_i b_j` respectively. Thus marginal multiplication asserts a cross-drug susceptibility relationship rather than learning it from these monotherapies. Patient-level independent action and within-population susceptibility alignment are different units and must not be conflated. Original Bliss and Palmer–Sorger texts were not inspected in this zero-network developer allocation; a targeted primary-source check is required before any historical novelty claim.
- **Combination Bayesian optimization, BATCHIE and latent-factor response learning:** these are mandatory operational comparators. The concrete signed-graph result above already supplies a simpler rival that realizes the proposed sharing/observation saving. No distinct update, acquisition capability or biological structural law has been established beyond those priors. Root's archive notes also prohibit treating old internal BATCHIE replay as external evidence.
- **Predictive states, value equivalence and optimal design:** the pair susceptibility object is a useful decision-relevant state in the toy system, but naming it so or wrapping its acquisition in an agent does not create a separate contribution. The same-price full continuous target assay remains admissible.

Within the inspected source scope, the useful retained result is the explicit **joint-menu counterexample plus separating ordinary intervention and exact simple rival**. Its historical novelty is unestablished, and the developer does not recommend it as a main innovation. The two-subtype law is an unvalidated biological hypothesis, not a discovered property of a screen.

## Minimal executable falsifier, subject to the missing data contract

The target is the **shared two-subtype susceptibility law**, not the pure mathematical proof. No existing response resource was opened to choose drugs or thresholds. A future minimal, prespecified assay must contain one population preparation, three distinct drugs A/B/C at fixed physical doses and durations, baseline/vehicle, each single-agent pulse, AB and AC learning schedules, and an untouched BC audit schedule, all with matched handling and counted independent preparation/technical-repeat nesting. AA, BB and CC duration controls are needed to check the pulse model against ordinary longer exposure; these controls are accessible monotherapies but still cost resources.

The three-drug triangle is the smallest overidentifying relation **after** two pair edges have been used to infer signs. A single pair expectation inconsistent with both allowed levels already falsifies the exact two-subtype law; no triangle is needed in that case.

Freeze these operations before seeing the audit outcome:

1. Estimate single-pulse `a_i` and uncertainty from paid calibration measurements. Under this exact resistant-half/sensitive-half model, `a_i` must lie in `[1/2,1]`; otherwise the model is already incompatible with the survival-scale observations. Qualify equal composition, absence of changing growth, and reproducible dose/time/handling. If these are not supportable, do not reinterpret a fit as evidence of the model.
2. Use AB and AC only to update the two observed signed edges. If either edge requires `|U_ij|` materially different from 1, stop at a failed structural assumption. If uncertainty cannot distinguish the two edge signs, the test is inconclusive at that budget.
3. Freeze the full predictive distribution for the continuous BC audit count. Its expected value must obey

   `C_BC = a_B a_C + b_B b_C U_AB U_AC`.

   Equivalently, when `b_A > 0`, the mean discrepancy is

   `R = C_BC - a_B a_C - [(C_AB-a_A a_B)(C_AC-a_A a_C)] / b_A^2`.

   Propagate all calibration and pair-estimation uncertainty. Near `b_A = 0`, the experiment loses sensitivity; an almost inactive anchor cannot be called informative. Audit BC is not used for refitting before the primary discrepancy is evaluated.
4. Primary structural falsifier: the predeclared uncertainty interval for R excludes zero by a prespecified practical margin. Choose the margin and required independent-preparation replication from assay precision and the live-count decision threshold before execution. Those quantities are not supplied by current metadata, so this document does not invent a numerical power claim.
5. A decision-enabling result additionally requires the predicted BC count interval to lie on one side of the prespecified depletion threshold and the untouched direct BC measurement to agree. Merely fitting AB/AC, or an interval spanning both decisions, is not a useful gain. Passing one triangle does not prove a universal two-subtype structure, molecular complementarity or higher-order combination response.
6. Compare with (i) one direct BC measurement strategy at equal total purchased wells and delay, (ii) the elementary signed-graph/rank-one model with the same data, (iii) whole-history combination Bayesian/factor learning, (iv) Bliss/marginal product and (v) best-single/AA follow-up. The graph and proposed learner make identical ideal predictions; any claimed additional agent benefit needs a separate specified mechanism and evidence.

This is an executable protocol once the assay precision, independent preparation scheme and paired-schedule data exist. Under this worker's allocation it was not implemented or run. A deterministic algebra check can independently verify Propositions 1–2 and the graph theorem without biological responses; such a check cannot validate their biological premises or a co-learning advantage.

## Present-resource stop and restart condition

HTS001 has only single-drug trajectories in the qualified metadata. Its 72-hour replacement is the same-drug replenishment, not AB/AC/BC switching or a controlled matched-history probe. Two technical wells and more timestamps cannot turn that into joint exposure. **Do not open its counts for this proposed falsifier.** Its metadata already fails the essential intervention contract; no response-value experiment is required to establish that failure.

Restart only when an authorized resource has matched same-population pair/schedule observations, physical doses/times and a defensible replication/handling contract, or when a different ordinary observation provably breaks the demonstrated symmetry. Before promoting a co-learning candidate, establish a biological shared law that is both useful and distinguishable from ordinary pair-response factors under the full cost comparison. Otherwise retain the boundary as a concise reason not to spend a monotherapy-only acquisition budget on an unidentified pair decision.

## Provenance and accounting

Original relevant source: Wu et al., DOI 10.1038/s41540-025-00560-8, published JATS SHA256 `002ff6e2add18dfecc65faf95316a623a753ca6b712dd4d9f02d8b7d77beb889`, inspected Sec3 and Sec27–31. BESTDR source identity and limits are in `../../2026-10-29-functional-joint-discovery/target_evidence.md`; its main JATS/older-code distinction is preserved. Metadata contract: that episode's `metadata_result.json`. Current evidence report and scout map: `../evidence_worker/evidence.md`, `../scout/source_map.md`. Independent root state-space derivation: `../root_derivation.md` (ordinary diagnostic, not this proposal's mechanism).

The developer performed local reading, algebra and two report writes only. Network requests 0; received network bytes 0; paid API calls 0; experiments 0; count-value accesses 0; installs 0; author-code runs 0; subagents 0. No shared index/library, src or tools changes. Native token/cost use and effective model settings are not exposed. A fresh challenger should inspect the proof, assumptions, resource theorem and prior comparison; this developer has not supplied its own independent review.
