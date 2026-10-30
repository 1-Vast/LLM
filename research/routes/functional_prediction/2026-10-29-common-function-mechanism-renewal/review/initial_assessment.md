# Independent initial assessment of candidate v1

Recorded before coordinator discussion or access to any other agent's analysis. Date: 2026-10-29. Requested settings recorded by the assignment: gpt-6.1-sol / high. The effective runtime model, accepted reasoning setting, native token use and monetary cost are not exposed here; those requested settings must not be represented as verified runtime settings.

## Scope and independence

I read `mechanism/candidate_v1.md`, verified SHA256 `a0f1edfc587ef130660896b6dfb56ff10ce09577981f3068069a8a41741b01dd`, and parsed these original local XML passages with Python ElementTree:

- `evidence/p5_negative_hysteresis.xml`, DOI 10.1038/s41467-026-71178-5: Sec3, Sec4, Sec5, Sec6, Sec7, Sec8, Sec13, Sec14, Sec15, Sec16, including embedded figure captions in those sections.
- `evidence/p6_hysteresis_prior.xml`, DOI 10.1073/pnas.1810004115: s2 title and first two direct paragraphs only; s9, s15 and s16 in full.
- `evidence/p4_collateral_sarcoma.xml`, DOI 10.1038/s42003-025-08652-1: Sec6, Sec12, Sec16, Sec17, Sec18 and Sec19, including embedded figure captions.

One combined extraction was truncated in the middle; I separately extracted p5 Sec6-8 and Sec13-16 and p6 s2 to ensure the listed scope was actually visible. I have not read whole papers, supplementary methods, supplementary datasets, the Source Data workbook, raw outcomes, other project reports or other agents' notes. I did not make network requests, run author code, conduct experiments, access .env or sealed resources, or install software. The only executed work was bounded local XML text extraction, candidate hashing, and writing this assessment.

## Initial judgment

The proposed inequality and inverse are correct sharp consequences of the stated bounded reweighting model, after making its parameter domain explicit. They provide a useful conditional audit statistic: how much hidden relative amplification a static response mixture would need. The packet does not yet establish that cheap public functional resources qualify the needed lineage and output bounds, that a selection-only explanation is excluded in any actual condition, or that an Agent and a virtual-cell model learn something beyond ordinary robust sequential experimental design. The currently supportable positive claim is an analytical diagnostic and a prospective assay-design rationale. A practical sensitization mechanism, useful co-learning capability and an empirical cost advantage remain unestablished.

## Mathematics checked independently

Assume finite U > 0, V > 0, 0 < m <= U, and 0 <= q <= V, with nonnegative w <= U and b <= V on one common probability space. Writing t = E[wb] = mr gives four bounds:

- t >= 0 and t <= Vm;
- t <= Uq, because wb <= Ub;
- t >= Vm - U(V-q), because (U-w)(V-b) >= 0.

Dividing by m gives precisely the candidate's interval. This proof accommodates arbitrary latent-type heterogeneity and arbitrary w-b association. It does not require a normal distribution, small type count or a dynamical simulator.

For 0 < q < V, put probability q/V at b=V and the remainder at b=0. Set the corresponding weights to mr/q and m(V-r)/(V-q). These weights have mean m and cross-moment mr. They are in [0,U] exactly when r belongs to the stated feasible interval. Thus every point in the interval, and both extrema, is attained; the proposed region is sharp over the stated class. The inverse is therefore exact, not merely a necessary threshold:

`U_required(V) = m max(r/q, (V-r)/(V-q))`.

Its maximum factor is at least one, so U_required >= m. No separate smaller U can satisfy the observed mean. For r=q, U_required=m, with the constant-weight construction w=m. For r=0 with q interior, U_required=mV/(V-q); for r=V, U_required=mV/q. These are legitimate endpoint mixtures with one zero weight.

Necessary qualifications that should remain explicit:

1. If m>U, q outside [0,V], or r outside [0,V], the observation contract already fails; those values are not valid inputs to the ordinary inverse formula.
2. At q=0, nonnegative b forces b=0 almost surely, so only r=0 is feasible; at q=V, only r=V is feasible. In either feasible endpoint case, the minimum U is m. In the other endpoint cases, no finite U suffices. The displayed ratios must not be evaluated through 0/0.
3. V=0 forces q=r=0, again requiring U>=m; m=0 leaves r undefined and is excluded. A protocol with no viable challenge-entry cells cannot provide this normalized response.
4. For sensitization r<q and fixed finite m,q,r, the second inverse factor dominates, and U_required decreases to m as V grows without bound. The amplification threshold becomes uninformative unless V is genuinely bounded. For r>q, the limit is mr/q, rather than m. The candidate limits its stated asymptotic claim to sensitization, correctly.
5. The example m=.95, q=.8, r=.2, V=1 gives .95 max(.25,4)=3.8. It is an algebraic illustration only.

The theorem is elementary bounded-moment/reweighting geometry. This is useful, but neither this derivation nor the supplied sources establish priority for the formula or justify presenting it as a new probability theorem.

## The observation contract is the major scientific bottleneck

The theorem applies to additive, linear outputs per comparable challenge-entry unit. Both arms need a common reference distribution, an interpretable lineage weight through the complete pretreatment/handling/recovery window, and an unchanged type-specific challenge output under the selection null. All descendants assigned the same stable type must retain that type's response. State conversion, context effects and assay nonlinearities violate the null; the bound does not distinguish among them.

A vehicle reference is valid if its lineage weights define the reference population and the A/vehicle relative weights are bounded on common support. Equal total counts do not imply equal composition. In particular, lineages absent from the vehicle challenge population but present after A cannot be handled by a finite relative-weight bound. Differential plating loss, recovery, dilution, passage or outgrowth must enter the weight definition. Counting an equal number of cells for the challenge can preserve a composition comparison, but it does not retrospectively reveal the original per-type relative weights. The m, U and response denominators must refer to the same units and sampling operations.

Density matching is also necessary: if the challenge response changes with inoculum, medium, growth phase or readout timing, b is not invariant. Shared competition or secreted factors can make the output of a mixture differ from the weighted sum of isolated type outputs. The candidate's simple null is then scientifically narrower than all possible nonconversion explanations. Excluding it establishes failure of that full contract, not proof of induction or a molecular memory mechanism.

A subtle endpoint issue deserves an explicit protocol diagram. An isolated *challenge-entry cell* can have a binary reproductive-success outcome and hence V=1. An isolated *original pretreatment founder* that produces several descendants and is scored by whether any descendant later forms a colony generally has output `1-(1-b)^w`, not wb. That binary founder-family endpoint cannot automatically be inserted into this linear model. Counting CFU produced by a growing original founder, by contrast, is additive in some settings but can exceed one. One must define where founder isolation occurs and how pretreatment descendants are sampled, not just call the endpoint founder-isolated survival. Filamentation or clumping can additionally sever the assumed one-cell/one-lineage/counting correspondence.

A short pulse limits elapsed time, not by itself the largest lineage weight: some cells can already be near division at pulse entry, rare fast lineages can be concealed by average growth, and washing/recovery adds time. A qualified ceiling could come from an explicit physically defensible division bound plus the complete handling window, or direct lineage-resolved qualification. A maximum observed among finitely sampled cells is not a universal maximum over all admissible latent types. If qualification is probabilistic or permits rare outliers, that uncertainty or tail mass must enter a revised bound; it cannot silently be treated as a hard U.

## What the cited original sections support

PNAS 2018 s2 already reports order-specific hysteresis after short CAR pretreatment, including 15 minutes and low sub-MIC dosing, with increased GEN killing. Its s9 measures bulk CFU over six hours after medium exchange. Its s15 already combines genotype-specific growth, selection, mutations and experimentally inferred hysteresis multipliers in a population model. These passages make short functional priming, history-dependent killing and a model incorporating selection plus physiological effects prior art. They do not qualify a universal lineage ceiling or a per-challenge-cell V for the proposed new statistic.

Nature Communications 2026 Sec3 reports effects even after one minute of CAR exposure, disappearance during a drug-free growth gap, and washing controls. Sec13-16 describe bulk CFU, AUC, centrifugation/resuspension, special pretreatments and an OD screen. Sec5 explicitly notes filamentation/lysis-related OD confounding. Sec6-8 report genetic and uptake/membrane evidence supporting Cpx-dependent physiological remodeling; these are stronger biological controls than an aggregate reweighting bound alone. Sec14 specifically says washing does not remove covalently bound CAR. Therefore free-drug removal must not be relabelled exclusion of all persistent drug action or damage. The viewed passages contain no qualified universal U and no binary per-challenge-cell V. The one-minute condition is a promising place to assess feasibility, not an already certified U<=2 experiment.

Communications Biology 2025 Sec6 already reports temporal collateral sensitivity after pretreatment and targeted functional follow-up. Sec12 and Sec16 use 72-hour CTG; Sec16 includes 13 days of pretreatment, and Sec17-18 include longer growth, confluency management and temporal resampling. CTG normalized to DMSO is not a hard per-type reproductive-output bound. Long pretreatment, repeated replenishment and population growth make a tight worst-case relative amplification ceiling particularly difficult. Direct counts in Sec17 do not themselves supply lineage-specific ceilings. I did not inspect its supplementary methods, raw data or any library beyond the stated original sections.

These papers provide accessible functional assay designs and already established instances of sensitization. Their viewed results cannot be treated as retrospective validation of this candidate's inequality in a biologically qualified setting. Data availability statements or a downloadable workbook would not alone repair an observation contract missing lineage bounds.

## Static-mixture and ordinary-design rivals

The direct two-type construction is a complete aggregate-data rival whenever U >= U_required. Consequently, adding a flexible virtual-cell simulator cannot identify induction from m,q,r alone. More expressive simulation may merely conceal the same nonidentifiability. Conversely, when the qualified bound is violated, a small calculator already detects that fact; a large agent is not necessary.

A fixed short-pulse grid, matched controls and this calculator is a serious baseline. Ordinary robust sequential design can retain the same feasible model set and choose actions that maximize expected information or reduce uncertainty per unit cost. The proposed retain-and-select loop is currently an instance of that familiar approach. No explicit additional state, model update, rule-revision operation, objective or information pathway establishes a distinct Agent×virtual-cell co-learning mechanism in this frozen packet. Language-model planning, execution convenience and proposing conditions might be useful engineering capabilities, but those must be demonstrated rather than counted as a scientific mechanism.

Moving q near V is a mathematically motivated design heuristic for sensitization because a bounded selection explanation then needs large amplification. However, this may mean a weak baseline challenge, can leave little dynamic range or unstable normalization, and only helps if an effect remains measurable and U,V remain credible. It should be evaluated against an ordinary design policy under equal measurements and assay cost, including the cost of lineage qualification and controls.

## Minimal decisive evidence and contribution threshold

The immediate gate is a concrete, fully specified cheap protocol with a valid mapping from observed counts to m,q,r and independently justified simultaneous bounds on U and V. It must cover both arms' handling and recovery, challenge-entry sampling, relative support, and the endpoint's additivity. A matched lineage-resolved check of pretreatment descendants plus a binary assay of individually isolated challenge-entry cells is one possible route, but its feasibility, cost and universal-versus-probabilistic bound must first be justified. The current papers' aggregate endpoints are insufficient for this gate.

After that qualification, the smallest scientific demonstration is one preregistered condition with a joint uncertainty region for all relevant parameters that is disjoint from the feasible static-mixture region. For a genuine sensitization example, every admissible point must satisfy `r < V - U*(V-q)/m`; a point estimate or separately chosen favorable bounds is insufficient. The same experiment needs matched density/medium/readout and controls for free-drug carryover and handling to interpret the violated contract. Residual target-bound drug action remains an explicit biological alternative. Such a result would exclude the qualified unchanged-response selection model, not by itself identify a molecular mechanism.

For the co-learning claim, separately freeze a state representation, update rule, action policy and outcome criterion. Then compare the Agent policy to the fixed grid plus calculator and an ordinary robust sequential policy using identical starting information, access, budget and qualification costs. Evaluate prospective held-out conditions or independent environments; lower cost to a valid exclusion or reliable calibrated predictions would be a relevant endpoint. A retrospective choice of the strongest published priming condition cannot establish the claimed advantage. No such prospective demonstration or evaluation is present here.

The narrow potentially valuable contribution is a transparent falsifiability and resource-qualification framework: a minimum-amplification certificate tied to a precise assay contract, and a decision about when cheap functional data cannot discriminate selection. Its actual novelty relative to bounded reweighting/selection inference and experimental-design literature is still unverified. A practical biological discovery or substantive co-learning contribution is not currently supported. This is an initial assessment of the frozen proposal, not a claim that the missing experiment must fail.
