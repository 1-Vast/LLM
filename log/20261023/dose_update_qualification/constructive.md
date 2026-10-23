# Independent dose-update qualification: a shared potency shift is testable, not yet a distinct updater

2026-10-23. **NONE / NO_CORE_GO for the proposed shared-module potency-shift updater.** This is a local method assessment, not proof that potency transfer is useless. No network, API, new numerical biological label, or fit was used. No peer report from this dose_update_qualification phase was read. Root supplied only the candidate question and, later, the instruction not to execute redundant profile/MAP or single-point toy checks. Native model identity, tokens and cost are unattested. Previously exposed functional outcomes remain exposed, not a fresh validation reserve.

## Historical constraints inspected

- `log/20261022/early_update_mechanism/DECISION.md`: the molecular dose-tangent nuisance-profile shift was actually compared to ordinary joint WLS/MAP in ten fixed cases and agreed to 2.22e-16. A regularized noiseless estimate need not recover the true shift; a second dose can discriminate models only with a prespecified gap relative to noise. That literal estimator+OED construction was not promoted. I do not rerun it here.
- `log/20261023/action_rule_search/constructive/INDEPENDENT.md` and `CROSS.md`: action-only calibration freezes cell response while fitting target action coordinates. A Hill/occupancy parameter is not automatically measured target engagement. The later reciprocal correction explicitly withdrew a full occupancy->state->function triple as a universal prerequisite for predictive utility. Retain that correction: physical occupancy claims require stronger anchoring than conditional predictive claims.
- `log/20261022/decrypte_feedback_pilot/DECISION.md`: ordinary high-dose functional feedback provided a real strong conditional-prediction baseline. `decrypte_molecular_increment/key_correction/DECISION.md` subsequently stopped the fixed high-dose protein increment after the actual corrected fit. Do not open other doses, endpoints, subgroups or the 96 protected drugs as a rescue.
- `log/20261022/cdk_functional_increment/DECISION.md`: fixed Middle-composition function ranking failed for Abema; Palbo evaluation was not estimable under its protocol. This is not an unrun potency-transfer opportunity. `cdk_middle_feedback/DECISION.md` was consulted for its composition task; it was not read as a new independent function experiment.
- `log/20261022/cipa_calibration_probe/DECISION.md` and `cipa_control_information/DECISION.md`: primary calibration/control-map stops retain small ordinary mixture/control-information positives. Protected sites are not available for rescue. Context transport at those sites does not establish a drug-specific potency mechanism.
- `research/kinobeads_substitution_20261019/REPORT.md`, opening result/method sections: actual measured-binding substitution test was NOT_SUPPORTED, not pending. Functional B5 includes target Jaccard, and lysate affinity does not equal same-cell engagement. Do not relaunch Jaaks/Kinobeads under shared-module dose terminology.
- `log/20261023/cxcl9_source_feasibility/DECISION.md`: its fixed 9-to-15 adaptive update was actually stopped while retaining ordinary control calibration. Single fixed-dose inhibitor feedback cannot separate target action repair from pathway gain. AL1/AL2 are not new authorized numerical probes for this candidate.

These are scoped decisions. None refutes all dose models, all target-sharing restrictions or finite-budget structured inference. Initial broad `rg` and combined reads produced truncated console output; the decisive early-shift, action-specific, decryptE, CDK-functional, CiPA-calibration and kinobead sections were then read in bounded form. No truncated output was treated as a newly audited complete raw-data asset.

## Exact operation under assessment

Let x=log(dose). Freeze a drug-specific source functional curve f_d(x), including its control baseline, maximal effect and slope, learned lawfully from source tasks. Let w_d be a frozen known or source-trained vector of drug-to-module loadings. In a new cell context, restrict every drug curve to

    F_d,new(x;delta) = f_d(x - w_d^T delta).

For a single common module, w_d=1 for its prespecified drugs. Functional support S consists of actual (drug,dose,time,context,assay) packages and their observed outcomes; queries are disjoint unrevealed packages. The support update often proposed is

    delta_hat = argmin_delta sum_{s in S} (y_s - f_ds(x_s-w_ds^T delta))^2 / sigma_s^2
                             + (delta-m_H)^T Lambda_H (delta-m_H).

Its inheritable objects are the frozen curve family, module mapping, prior (m_H,Lambda_H), support-noise model and perhaps a selection rule. This is precise and differs from fitting an arbitrary vertical output offset/amplitude. Horizontal shifts can produce dose-dependent corrections and preserved source saturation rather than a uniform scalar correction. Do not dismiss that operational difference.

But with the same f,w,H,S and Gaussian noise/prior, this exact objective is ordinary nonlinear random-effects MAP. An ordinary same-forward solver can be the identical low-dimensional optimization, so no iteration-count or dimensionality advantage has been supplied over that comparator. If the candidate instead integrates delta and predicts E[f_d(x-w_d^T delta)|H,S], the ordinary same-model posterior predictive estimator is exactly the same operation. MAP and posterior mean are not generally equal; do not claim the broader equality. Whole-world refit can differ, but defeating that less-restricted estimator alone would not distinguish the updater from same-forward MAP or structured nonlinear EB.

The source history must train the same curve/module/prior for both sides. Giving the candidate a target module, spare-capacity state or source curve known from future query data would be a free-information advantage. Learning the prior across tasks can be useful inheritance; without a new tested property it is ordinary inherited model adaptation rather than an independent algorithm or RSI.

## The minimal missing biological sharing constraint

To be more than an unconstrained shared shift, state a falsifiable cross-drug law. A particularly small candidate law would be:

For prespecified selective reversible drugs A and B acting through the same target module, after matching exposure and readout time, each context change modifies the *same effective target-activity threshold*, while the target-activity-to-function curve remains invariant. Consequently, corrected concentration at equal measured target activity produces equal functional effect within the specified tolerance, and the residual log-potency changes satisfy a frozen cross-drug relation rather than independent fitted drug shifts.

One explicit stronger constraint is

    a_d,c(C) = C / (C + K_d * rho_c),
    y_d,c(C) = g_m(a_d,c(C)),

where K_d is source-anchored, rho_c is the only new-context module factor, and g_m is shared and frozen. This predicts equal log-potency shift log(rho_c) across those drugs, unchanged maximal function, and unchanged shape after activity alignment. It also predicts held-out doses and drug B after feedback from drug A. Measured target activity is needed to interpret a_d physically; alternatively this can be tested as a purely predictive curve-alignment law, with the weaker interpretation stated honestly.

Required observations for a physical version are matched actual drug exposure/time, drug-specific target engagement or specific proximal activity over a useful dose range, and independently measured function with controls. General phosphosite or RNA similarity is not automatically the needed target-activity measurement. For the predictive version, actual matched functional dose curves across independently grouped contexts and prespecified drugs can test horizontal sharing without complete occupancy identification. At least one query must vary drug identity, rather than only interpolate A's already measured curve. Practical discovery value additionally needs disjoint future contexts/drugs and fair acquisition accounting.

The law fails for reasons that must be part of the intended domain: different intracellular exposure/efflux, off-target functions, target expression ceilings, reversible versus covalent/time-dependent inhibition, distinct target conformations or changing downstream compensation. “Same module annotation” by itself rules out none of these. Do not exclude failures by selecting drug pairs from their observed response similarity. This is the missing extra measurable sharing constraint; no such relation is currently verified in the stopped assets.

Even if the law holds empirically, fitting rho is still ordinary nonlinear MAP/posterior adaptation. A novel scientific contribution could be a newly established transferable biological law with useful decisions, but a new *updater mechanism* would still need a distinguishable finite-data/robustness/compute property against the same law fitted conventionally. No such property is provided here. Adding an editor or calling rho an inherited action coordinate does not add it.

## Hand-derived falsifiers; no new execution

One dose cannot generally identify horizontal potency versus efficacy change. Define inhibition h(C;K,A)=A*C/(K+C), with a source K=A=1. At C=1 the outcome 1/3 is consistent with either potency shift K=2,A=1, or unchanged potency K=1 with amplitude A=2/3. At C=2 their predictions are 1/2 and 4/9, gap 1/18. An absolute noise bound at least 1/36 allows overlapping outcome intervals, so a second point is not guaranteed to discriminate. This is an analytic design witness, not a performed synthetic or biological result; it repeats no profile/MAP test. With multiple unknown slopes, ceilings and off-targets, fitting a few supports can remain underidentified.

For cross-drug falsification, hold A's support response fixed and consider two worlds in which B has the common context potency factor or a B-specific intracellular exposure factor. The support information is identical. Unless a legal measurement or a validated domain restriction excludes the latter, the update cannot guarantee B's response. This does not show that cross-drug transfer is statistically useless; it identifies the assumption that must earn empirical support and the posterior alternatives that ordinary nonlinear EB should receive.

Positive criterion: freeze the domain, module relation, support packages and query range; then show held-out B curves follow the prespecified A-derived shift with useful accuracy and stable nomination/regret beyond gene/target priors, strong direct curves and same-forward nonlinear MAP/EB at equal total cost. Negative criterion: disjoint drug/context curves require drug-specific shifts, changing ceilings/slopes, or same-forward conventional conditioning accounts for all gains. In those cases stop this fixed common-factor rule, without declaring every potency model invalid. A numerical usefulness margin must come from the new assay/decision protocol before outcomes; neither the old 5% RNA gate nor a new convenient percentage is adopted here.

## New entry-point disposition

I do not nominate another biological asset or compound family merely to keep the route alive. A genuinely useful new source would need matched drug-specific proximal activity and function across selective same-module drugs plus independent contexts; alternatively a function-only source could support the explicitly weaker predictive alignment claim. This is an information contract for root's independent primary-source search, not evidence that such a source has been found or that an occupancy database must be collected.

No evidence presently establishes world-model necessity: a direct conditional curve predictor gets all purchased curves, modules, states and target-activity observations. No agent gain is shown: ordinary model-discrimination/OED can choose a separating dose. No updater-inheritance or improved-improver gain is shown: a changed research strategy must improve later descendant updates from common starts, history and total cost. Current action: do not launch a biological fit or reopen protected/stopped outcomes for the shared-shift formula alone. Seek the specific measurable sharing law or a different structural problem before promotion.
