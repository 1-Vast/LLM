# Independent critic: decision-relevant probing needs a new operator, not full model identification

2026-10-23. NONE_NEW_CORE at this checkpoint. Two new2026original algorithms provide concrete and nontrivial comparators for decision-focused probing; neither should be dismissed merely as an argmin or because a direct policy can represent it. No current-phase peer report was opened before sealing. A source-agent summary/question arrived after both originals were read and the exact witness executed; it is disclosed, not used to choose those sources/witness, and will be answered after sealing. No communication-blind claim is made.

No new biological observations, full-info cost vector, old panel fit, inherited updater search or drug efficacy experiment occurred. One exact finite-model probe-target witness ran. This is not the old conformal-set-to-drug shortcut, full-information DFL transfer or ordinary Bayes-equivalence witness.

## Historical boundaries actually reviewed

Read functional_mechanism_frontier/critic/INDEPENDENT.md and CROSS.md, and feedback_shift_mechanism/DECISION.md. Prior stops remain: full cost feedback cannot be silently imputed for an OnlineDFL theorem; accepted-population/set coverage is not a nominated drug's efficacy or free assay cap; nuisance projection/profiled ridge equality is limited to its explicit quadratic model; measurement and biology are not identified by one untreated control; old FAC/OLA selectors cannot become prospective tests. These do not require identifying a complete virtual cell before a useful drug decision.

## Source1: Action-BED, actual operator and computational price

Original https://arxiv.org/html/2606.23662v1, *Action-BED: Task-Driven Bayesian Experimental Design with Singly Intractable Objectives*, manuscript22June2026. Retained original HTML/projection/receipt, SHA2564bfa9bf991b3c7e6a371c18aaff7b7d5d61c97e6e05987474b7d3f8478022680. Read Sections2–4, Algorithm1, related work and AppendixA assumptions plus relevant gradient limitations; selected experimental protocol/ablation paragraphs, not full proof or benchmark reproduction.

Concrete operation: learn a design policy pi_d(h) that selects each next probe and a terminal action policy pi_a(h_T), jointly minimizing

    E_(theta,epsilon) loss(pi_a(h_T(theta,epsilon;pi_d)), theta).

This lifts the nested Bayes action minimization into a shared stochastic optimization over both policies. It removes explicit posterior-density/marginal-likelihood estimation and the nested expectation/optimization cost of conventional BED implementations. The unrestricted equivalence uses measurable selectors, compact action space, lower-semicontinuous conditional losses and integrability. A finite neural policy class need not attain the unrestricted Bayes optimum; this is not a theorem that SGD discovers the optimal drug policy.

Algorithm1 samples latent theta and rollout noise from a joint generative model and differentiates the terminal loss through design/outcome trajectories. Pathwise training requires a reparameterizable simulator and appropriate differentiability. If that is unavailable, the stated alternative requires a score function for a REINFORCE estimator. An opaque real assay provides neither gradient contract automatically. The method is likelihood-free in the density-estimation sense, not simulator-free, and still knows theta for evaluating loss in synthetic training rollouts.

At deployment the action/design policies only need acquired history, so partial observed feedback is lawful. Training nevertheless has simulated full latent truth and many counterfactual rollouts; replacing those with a learned cell model transfers model bias into design optimization. Without known simulator, a real fully measured patient/drug pool could support a carefully defined replay objective, but not arbitrary generated assays or unseen-schedule values. No genuine cell simulator/score or new finite-pool asset is authenticated by this paper. Charge all pretraining rollouts and optimizer steps, not only deployment probes.

This is already a strong direct design-policy+terminal-policy comparator for “resolve only ambiguity that affects the decision.” It can leave most theta unestimated. The paper itself cross-evaluates design/action networks and common posterior-based terminal decisions to distinguish policy coupling from query quality. These are substantive controls worth inheriting as evaluation practice. Calling our action policy a scientific agent and adding world states would not by itself supply a different operator or RSI. A real advantage in simulation efficiency, misspecification robustness or transferable restriction could still be novel; no candidate supplies it here.

## Source2: RAED, nuisance-robust resolution is not automatically drug regret

Original https://arxiv.org/html/2609.03686v1, *Resolution-Aware Experimental Design under Partial Identifiability*, manuscript3September2026. Original SHA256fe5ee676c9f9d9d4e7dc1b54d2bb6e13cfd2df94e5f0d4c76d3684d96788e7de. Read Sections1–5, exact cross-nuisance aliasing statements and calibration/rare-tail assumptions; did not reproduce subsurface/methane experiments or independently prove its theorems.

Concrete operation: for each experiment e, optimize the expected cardinality of a nonempty structural candidate set Gamma_e(Y), subject to false-exclusion constraints across persistent nuisance states. The constraints range from average nuisance risk to upper-tail CVaR-style risk or pointwise validity. A single observation-to-set rule must work across protected nuisance states; nuisance-specific decoders are not free. This can rank experiments differently from average information gain, and the source proves a specific aliasing separation while preserving genuine composite Blackwell order.

Practical pipeline trains family scores, chooses experiment using an independent selection sample, fixes a nested conservative threshold path and then calibrates the selected rule on independent data. It does not assume learned scores attain the oracle frontier. Tail calibration needs independently drawn nuisance states, possibly with repeated observation-noise simulation within each. Repeating one nuisance state does not increase independent-nuisance sample size. Positive-tail finite-sample claims do not automatically cover pointwise validity at delta0. Its rare-tail requirement scales as log(1/beta)/(alpha*delta) in the stated construction.

For a biological transfer, structural labels and protected nuisance sampling laws must be justified; technical wells, imaging sites or adaptive generations are not automatically iid latent biological states. Full true latent/structural labels in calibration simulations are a training/certification resource, not inferred from a few purchased drug endpoints. There is no requirement to assay every action during one deployment, but simulation/calibration resource is real. Independent scoring/selection/calibration must not be collapsed when using a tiny historical panel.

RAED explicitly acknowledges its fixed-experiment nuisance-average special case equals classical minimum-ambiguity set-valued classification. Its concrete outer experiment objective and persistent-nuisance constraints are the substantive contribution, not a renamed ordinary regression. Our previous conformal budget-interface objection must not be repeated as though it invalidates this different experiment-selection operation.

## New exact probe-target counterexample

Four equiprobable mechanistic models m1,m2,m3,m4. Under m1,m2,m3, drug A utility1 and B0; under m4, A0 and B1. Both available probes cost one and are noiseless:

- Structure probe outcomes partition models into {m1,m4}, {m2}, {m3}.
- Drug probe outcomes partition them into {m1,m2,m3}, {m4}.

At zero structural false exclusion, the minimal reported structural set must retain the whole deterministic observation fiber. Expected structural cardinality is3/2 for the structure probe and5/2 for the drug probe, so structural-resolution optimization strictly selects the former. The optimal subsequent drug decision has expected regret1/4 after the structure probe and0 after the drug probe. Both obey exactly the same observed-probe budget. This is a probe-ranking disagreement, not the old error of selecting an unsafe member of a covered drug set.

Fixed Fraction code research/decision_probe_mechanism_20261023/critic/probe_target_witness.py verified these four values and the best-drug candidate-set cardinalities3/2 versus1. No randomness, model fitting, free extra assays or biological values. This is an analytic interface counterexample, not an empirical drug advantage or new algorithm.

Crucial opposing interpretation: RAED can choose the structural target to be decision-equivalence classes rather than all mechanism IDs. In this example that changes the target to {A-best,B-best} and favors the drug probe. Therefore the witness does NOT refute RAED. It specifies a necessary target choice for this application. Defining the target as the best drug is already decision-targeted experimental design, not our new core. For unequal cost/margin losses, best-drug class alone also discards regret magnitudes; Action-BED already permits the full terminal decision loss. This is exactly why simply renaming mechanism elimination as decision-relevant model elimination is insufficient.

## What an admissible new mechanism must add

A useful virtual cell need not identify every state or pathway. It must provide a decision-relevant observation/response restriction that yields better legal probes or transfer at a declared assay/compute budget. A separate full-state-identification hurdle is unnecessary. Conversely a direct policy's ability to represent the resulting mapping does not negate a genuine sample/computation/transfer advantage.

The currently missing difference is precise: beyond joint action/design training already in Action-BED, nuisance-valid structural targeting already in RAED, and competent decision-focused AL/VOI, what additional biological sharing, simulator-learning operation, counterfactual restriction or finite-budget estimator makes an improved probe available? “World model predicts outcomes, then choose lowest expected regret” is not yet that difference. A new operator could use familiar parts and still qualify through a distinct falsifiable restricted advantage; no such surviving restriction is supplied in this pass.

For any future candidate freeze: finite drug decision/utility, known feasible probes, acquired feedback/noise/control costs, computational rollout budget, permitted history, and whether evaluation is new physical outcomes or finite-pool replay. Compare same-information full-history direct terminal policy, Action-BED-style joint policy, ordinary conditional refit/CL, decision-focused AL/VOI, structural/information-gain acquisition, simple mixtures and equal-budget policy/program search. Every arm receives the same useful cell features/simulator training data and paid observations. A world/no-world contrast must preserve information and distinguish inductive/compute value; do not deliberately deny the direct model molecular inputs to create a win.

Success requires a prespecified practical decision-regret/utility advantage at matched total assay+compute cost on independent later tasks, plus ablations identifying the proposed operation. Stop if probe gains vanish against the matched decision-aware comparator, hinge on wrong simulator support, or only reduce structural ambiguity irrelevant to drugs. Mere retained policy parameters are predictor/policy inheritance; U transfer requires common initial model/history and a retained learned updating capability, and improved-improver needs G1 versus unchanged G0 on later updater discovery at equal search budget. No result here establishes these contributions.

## Disposition and records

NONE_NEW_CORE / NO_NEW_BIO_NUMERICAL_GO in this review. This is not a ban on a small lawful finite-pool or calibration diagnostic, and it does not reopen earlier BeatAML/probe/scorer/FAC/OLA stops. Two recent actual methods show that decision-relevant partial identification is a live concrete research route, but copying their operation into a virtual-cell agent is insufficient novelty.

Four public GETs, all200: two official arXiv metadata searches and exactly two original algorithm manuscripts. Initial broad search had many irrelevant keyword hits; refined title/category search and bounded local ID/title duplicate search preceded fetching. No matching IDs/titles appeared in that bounded local search; no exhaustive novelty claim. Some broad projected-text reads were truncated; the actual bounded Methods3–4 and Sections5 reads above supplied the decisive assumptions. No author code/model run or bio fit. One exact witness returned0 under maestro, stored with code SHA. Native agent model/tokens/currency not exposed. All new code research/decision_probe_mechanism_20261023/critic/; all originals/projections/receipts/decisions/witness evidence log/20261023/decision_probe_mechanism/critic/.
