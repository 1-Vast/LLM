# Independent attenuation identifiability review

2026-10-23. Read reusable_error_mechanism/DECISION and original research/mixed_feedback_estimator_20261023/extract.py (not executed). No peer current-stage opinions, saved biological arrays, protected values, raw matrices, new fits or HTTP. One exact analytic witness script executed and saved. Native exact model/token/currency unknown. **GO for algebraic source diagnostic only; NO_CAUSAL_EXPLANATION_GO, no new predictive law nominated.** Old overlap/product STOP remains.

## Extraction actually defines these quantities

extract.py:32–39 computes per-cell CP10K from raw feature counts and per-cell total UMI, then separately accumulates CP and log1p(CP). Lines164–172 divide both sums by cell counts. Thus for each fixed group/gem/readout,

    m = mean_cells(10000*C_gene/T_cell),
    ell = mean_cells(log1p(10000*C_gene/T_cell)),
    J = log1p(m) - ell >= 0.

m is a mean of relative per-cell expression, **not absolute transcript count**, even before log transformation. Per-cell denominators are accumulated across genes; the saved103readouts do not recover absolute total RNA per cell. Sparse zero entries contribute0 to both sums, consistently with division by all retained cells. J captures the log Jensen gap for this normalized distribution, not a uniquely biological heterogeneity component.

## Exact identity and its permissible interpretation

Let D f = f_ab-f_a-f_b+f_0 within one target gem. Then

    D ell = D log1p(m) - D J.

Average over the same predefined gems only after constructing these terms; the identity survives linear averaging. D J can have either sign although each J>=0. It is invalid to log1p(mean_gem m) and call that the same term, or replace meanlog by logmean and infer biology. This diagnostic is algebraically exact and can expose a coordinate/dispersion contribution to the observed contrast. It cannot identify whether any term is caused by regulation, technical noise, cell-state mixture, selection or normalization; all are properties of the observed post-selection distributions.

If all four CP means are nonnegative and m_cf=m_a+m_b-m_0>=0, an **additive-in-CP-means** counterfactual can be passed through log1p:

    C_log = log1p(m_cf)-log1p(m_a)-log1p(m_b)+log1p(m_0).

Where m_cf<0 it is not a valid expression counterfactual, even when1+m_cf happens to remain positive. Report validity mask/counts; do not clip, discard invalid points from global scores, or tune a subgroup. Crucially, additive CP means are neither additive absolute transcripts nor an identified counterfactual cell distribution. Plugging this value into log1p(m) supplies no J_cf; assuming J_cf=0 is an additional homogeneity assumption. Do not call the resulting synthetic contrast a reconstructed real double state or subtract it and relaunch prediction.

## Executed exact counterexamples

EXACT_WITNESS.json and exact_witness.py preserve four mechanisms as logical witnesses, not our biological data:

1. **Log curvature without any absolute interaction.** Homogeneous absolute values x0=1,xa=xb=2,xab=3 satisfy xab-xa-xb+x0=0. Yet their log1p mixed contrast is log(8/9)<0. In general with baseline x and positive additive increments a,b, the log ratio is1−ab/((1+x+a)(1+x+b))<1. A same-sign deficit after logging therefore need not be antagonism or attenuation of absolute action.
2. **Compositional normalization without any absolute interaction.** Two-gene absolute vectors (1,1),(2,1),(2,1),(3,1) are exactly additive coordinatewise, but the first gene's normalized mixed contrast is3/4−2/3−2/3+1/2=−1/12 (CP10K:−2500/3). This persists before log and with homogeneous cells/J0. Consequently even an additive-CP diagnostic cannot identify absolute biology.
3. **Jensen heterogeneity without an absolute mean interaction.** Every condition has absolute mean1; control and singles are deterministic1, double is an equally weighted0/2mixture. Mixed means are0, but D ell=0.5log3−log2<0 and D J=log2−0.5log3>0. This is explicitly a no-mean-interaction example; it does not assert individual-cell action additivity or that altered distributions are biologically meaningless.
4. **Persistent control bias across different gems.** True single/double/control values all1; observed control is1+c in every technical stratum while singles/double are unbiased. Then centered input parents are−c, global-shrink feature g=2c, target contrast r=c and fitted beta1/2, despite zero true effect. This assumes shared *systematic group bias* across separate input/target gems. It is not the same random measurement reused. If all group errors are independent, symmetric and centered across strata, the corresponding cross-product expectation can be0; no artifact is guaranteed.

Witnesses demonstrate non-identifiability of a biological interpretation, not that any listed cause explains the observed0.67/0.99% overlap positive or stronger ordinary attenuation. The source data could contain real interactions plus these effects.

## Useful next mechanism boundary, without a new fit menu

The more testable restriction is **observation pushforward consistency**: any claimed biological additive/attenuation mechanism should specify its physical state and observation map, then predict how its contrast changes when that observation map changes. A rule defined only in logCP space is a coordinate-specific predictive rule until an independently calibrated scale/observation model is provided. Ordinary generative/measurement models already implement this restriction; no new optimizer or core is claimed.

The immediate lawful diagnostic can use only already exposed per-gem m/ell to reconstruct the exact Dlogmean/DJ decomposition, tabulate CP-counterfactual validity, and report the exact identity residual plus signed contributions. It must not regress new features, tune a corrected law, swap the stopped predictor to CP, select readouts/genes, or rank explanations by a favorable new MSE. These quantities do not require importing original extraction or reopening raw matrices. Freeze selector/weights/outputs first. Equality to machine precision checks implementation, not explanatory attribution.

A true functional follow-up would require prospective scale information such as independently calibrated per-cell RNA/absolute counts and matched function, or a controlled measurement perturbation that changes normalization/capture without changing the prior living state. Same baseline and treatment units plus independent viable count/decision outcome are needed. No such package is newly authenticated, so this pass does not launch another source hunt or claim a functional mechanism. Technical gem partitioning prevents one literal shared random observation leak; it does not establish absolute scale, eliminate stable group bias or create later research tasks.

## Decision

Support root's exact decomposition as an identifiability diagnostic, with explicit CP-relative/absolute distinction and unavailable J_cf. It may narrow the interpretation of the observed attenuation but cannot decide its cause from a mathematical identity. Keep ordinary predictive positives intact and STOP both failed specific laws. No causal attribution, functional head, new feature fit, world-model, inheritance or RSI claim follows.
