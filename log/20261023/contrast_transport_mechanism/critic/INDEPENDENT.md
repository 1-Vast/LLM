# Independent contrast-transport critic: four-cycle isolation is standard, transport remains unproved

2026-10-23. Uses sealed replicated_contrast measurement evidence only;no current peer report,new raw/count/array value,fit,toy or literature retrieval. Verdict NO_CORE:the positive does not select a specific cross-action restriction;four-cycle contrasts can isolate a well-defined ordinary interaction coordinate but do not themselves learn its transport.

## Strongest simple explanation of the existing positive

Let m_c(a,b)be the frozen terminalmeanlog(count+1)endpoint. Define context difference C_ab=m_A(a,b)-m_B(a,b),so the measured pair-of-pair statistic isDelta=C_ab-C_cd. A simple context-dependent gene/role model is

    C_ab = kappa + u_a + v_b + Q_ab.

The roles matter for an anchor/array assay. A symmetric unordered alternative usesu_a+u_b. Choosing symmetry does not follow from canonicalizing IDs;both processing roles must be mapped and their weighting understood. Qis the residual beyond that model,not automatically a molecular interaction.

Under the role model,

    Delta = u_a-u_c + v_b-v_d + Q_ab-Q_cd.

Thus a fully reproducible gene-context main effect withQ=0can produce the existing nonzero repeatableDelta. Merely pairing actions with the same number of targeted genes does not cancel these terms. Sharing one endpoint only cancels that endpoint: C_ab-C_ad=v_b-v_d+Q_ab-Q_ad. There is no general elimination of both gene effects by one ordinary pair-of-pair comparison of distinct actions.

This is a concrete exact alternative,not a claim that the observed result has been fitted/explained by it. No source-supported evidence currently establishesQnonzero,lowrank,sparse or portable. The old published-GI endpoint fit's failure cannot decide this new terminal-count model either.

## What a matched four-cycle actually does

For a rectangle of four distinct ordered actions(ab),(ad),(cb),(cd),fix the same roles and aggregation and form

    T = C_ab-C_ad-C_cb+C_cd
      = Q_ab-Q_ad-Q_cb+Q_cd.

The equality follows by cancellingkappa,u_a,u_c,v_b,v_dterm by term. For an unordered symmetric node-additive model the alternating four-edge cycle also cancels every gene coefficient. Distinct roles/genes and all four eligible edges must actually exist. If an estimator changes guide weights or role aggregation across edges,the corresponding nuisance law may no longer have this separable form.

ThisTis the standard two-way interaction contrast ofC,or context-by-row-by-column contrast ofm. It is not a new estimator,novel world update or proof of gene epistasis. A generic context-dependent guide/representation effect that is not gene-additive can remain inT. Passing a repeatability gate forTwould show that this residual coordinate repeats under the screen contract,not that sparse feedback predicts unseen rectangles.

In matrix notation,letZbe the fixed gene/role incidence design andwthe four-edge alternating vector. ThenZ^T w=0andT=w^T C. Any direct model with the sameZcan use this exact contrast without fitting nuisance coefficients. Weighted least-squares nuisance projectionP=I-Z(Z^T WZ)^+Z^T Wprovides the ordinary global counterpart;its domain/weights must be declared and singular graph components handled,not given an oracle. A model receiving the same observed four edges can computeTwith the same four-term sum. Renaming it a feedback-preserving cycle cannot supply operational distinctness.

For a complete bipartite anchor-by-array matrix,the row/column additive design has rankn_row+n_col-1;the interaction space has dimension(n_row-1)(n_col-1),and ordinary four-cycle contrasts span it. On a sparse assayed graph,available cycles determine which nuisance-free contrasts are observable;do not invent missing edge outcomes. In an unsigned symmetric gene-incidence graph,even cycles cancel by alternating weights;an arbitrary odd cycle does not. A tree can fit every observed edge with additive node terms,so lack of an observable cycle is a design-identification limit,not absence of biological interactions.

## Restricted interaction transport reduces to a concrete familiar model

One possible restriction isQ_ab=p_a^T q_bwith rankr. Then

    T = (p_a-p_c)^T(q_b-q_d).

This is precisely a low-rank interaction/matrix-factor model after additive nuisance removal. In symmetric biology one might imposeq=pand a context-dependent coefficient,but that is an additional testable assumption. More generallyQ_c,ab=sum_t eta_ct p_at q_btis ordinary multi-context tensor factorization;source-trained geometry and target-support coefficient updates are explicit conventional operations. A fixedr,sourcecovariance or featureprior cannot be chosen from target query performance for free.

Four-cycle observations could make additive nuisance cancellation exact under the assumed law and can improve finite-sample conditioning when nuisance dominates. That is a potentially useful measurement/design property even within ordinary mathematics. It must be compared with direct models given the same cycle measurement/contrast and incidence resources. It does not justify a claim that direct conditional inference cannot exploit the cancellation. Conversely generic expressive equivalence does not prove identical optimization/sample efficiency for all nonlinear models.

Compute:oneTrequires four observed action endpoints per context;observations can be reused across overlapping rectangles,but the endpoints and screen bundle remain charged. O(4)contrast arithmetic is cheap for both cycle and direct controls. Covariance isw^T Sigma w,not the sum of four independent variances when genes,guides,baselines/cultures are shared. No inverse count of cycles gives biologicalN. Low-rank coefficient fitting can use anr-dimensional solve/O(nr)prediction when legal features are available;do not compare it with an intentionally dense naive direct solver. Learning those features and selectingrconsume source labels/search/compute.

## Exactly what the current evidence permits

The repeated readDelta positive supports existence of a stable measured contrast on the fixed library,but imposes no nontrivial algebraic restriction on how unseen actions vary. It can be entirely node-additive,can include repeated pair-specific nuisance,or can include biological mixed effects. This phase has not discriminated these possibilities. Therefore I cannot honestly nominate a rank-one/shared-module/sparse-edit rule as uniquely worth testing from this evidence. NO_COREratherthan an arbitrary new parameterization.

A bounded ordinary diagnostic could ask whether a predeclared nuisance-free interaction coordinate such asTexists/repeats or whether legal sparse feedback forecasts unseen-action contrasts beyond a fitted gene-additive baseline. Those are distinct questions,not an automatic next experiment or a new core. The direct updater question remains held-action prediction from few support outcomes with a fixed endpoint/common starts and strong same-information ordinary controls. Anynewsplitofalreadyexposedarraysisdevelopment;no repeat,cycle,guide split or seedcreatesindependentconfirmation.

Do not require a new mathematical primitive or unique latent identification before such diagnostic,but do not promote it merely because the nuisance cancellation is exact. Keep the previous endpoint predictor stopped,no countre-read/lung opening/refit is authorized here,and world/agent/inheritedU/joint/improved-improverremainunestablished.

Record: reasoning and report only;zero new numerical access,HTTP/API,fitorcodeexecution. Independent seal before current peer cross. All evidencehere;no researchcode needed. Fullgoalactive/notachieved.
