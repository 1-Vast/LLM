# A shared intervention-update law is not identified by this endpoint table

2026-10-31. Developer analysis for the coordinator; this is not independent challenge or a frozen numerical protocol.

**Central proposition.** Learning a reusable action of a drug on a cell state would have scientific content if that state were observable or independently testable, its update were shared across backgrounds, and the updated state predicted a subsequent intervention. The present pooled endpoint table does not observe such an update. It supports differential combination selectivity, but a representation fitted to its static response matrix does not become an intervention mechanism by being updated after feedback. The strongest concrete version examined below either reduces to an ordinary predictor, needs missing scale information, or requires a new observation of the proposed state transition. I do not recommend an experiment on this table under a claim of a new learning mechanism.

This does not imply that combinations are unpredictable, that existing ordinary prediction has no value, or that all Virtual Cell mechanisms are impossible. The conclusion concerns this candidate and these observations.

## Scientific object and information available at use time

Write the released endpoint as `S[c,p] = log2(g[c,p]) - k[p]`, where `g[c,p]` is the matched-vehicle fold of cell-line burden under the observation assumptions in the readout contract. The unknown common term `k[p]` includes the pool normalization. Stable line-specific recovery still permits the following contrast; treatment-dependent differential recovery may not.

For a prespecified pair of cancer backgrounds `c,d`, define:

`D[c,d,p] = S[c,p] - S[d,p] = log2(g[c,p]/g[d,p])`.

For an exact-dose two-drug condition `A+B`, a useful scientific output is its relative selectivity `D[c,d,A+B]`. A second identifiable output is its departure from the sum of the constituent selectivities:

`J[c,d,A,B] = D[c,d,A+B] - D[c,d,A] - D[c,d,B]`.

This is differential departure from multiplicative vehicle-fold response. It does not identify absolute synergy, cancer killing, healthy-tissue safety, or a molecular cause. Choosing another reference line or centering is not an innovation. The reference and requested comparison must be chosen before looking at outcomes. A panel of cancer lines is not a cancer-versus-normal safety panel.

The intended use case is a research team with historical intervention responses across source backgrounds and a prespecified, already available response panel in a query background. Query inputs may include treatment identities/doses, the permitted panel, and any independently qualified baseline measurements. The query combination response remains unavailable. Any diagnostic combination feedback used at query time must be charged to every rival and excluded from evaluation. Predicting a response from zero query interventions is a different information setting.

Actual design support is narrow. The root's metadata-only audit establishes 52 lines, 93 conditions, 44 noncontrol single-drug conditions from 19 drug names, and 47 combination conditions. The latter are 41 two-drug, three three-drug, and three four-drug conditions, covering 16 drug-name families. Only 17 of the 47 combination conditions have every exact constituent single-drug dose present; this is not a count of 17 qualified two-drug surfaces. Unordered tuple order does not encode administration order. No sequence, preparation, batch, or biological-repeat fields have been established. Four endpoint DMSO rows per line do not replicate ordinary drug rows. Pairwise line contrasts do not turn 52 lines into 1,326 independent experiments; for each condition they have at most 51 independent contrast coordinates. The shared pool and controls also matter for uncertainty.

I read the metadata and source text only. I did not inspect the response column, calculate these contrasts, or identify a numerical effect.

## One candidate: learn how an intervention changes a functional state

The candidate is a restricted update, not a named architecture. A cell has a compact functional state `z[c]`. A drug at a declared dose and duration changes it by a shared operation `U[A]`. A second intervention's effect is read from the changed state:

`z_after_A = U[A](z_before_A)`;

`response_to_B_after_A = h[B](z_after_A)`.

Historical feedback would estimate the shared operations and readouts. Legal query probes would estimate the query state. The proposed gain would come from reusing an observed change in state to predict an unmeasured combination across backgrounds, rather than estimating a separate response for every background and pair.

The load-bearing biological restriction is closure: once `z_after_A` is given, the relevant effect of the first intervention on the second is exhausted. Other consequences of A, cellular background, exposure history, and pool interactions must not change B's response beyond the stated state/readout model. The update itself must also transport across the specified backgrounds and doses. This is a hypothesis about biology and the observation process. It does not follow from calling an embedding a cell state, using a sparse update, or minimizing adaptation loss.

There is no evidence in the inspected release identifying such a state, its transition, or closure. A five-day scalar abundance contrast is an outcome of treatment; it is not a measurement of the state that mediates a later intervention. A simultaneous A+B endpoint cannot be silently rewritten as an A-then-B transition. Whether a useful state exists remains a worthwhile biological question, but the current data do not answer it.

### Why a static nonlinear shortcut has an additional measurement problem

A tempting substitute is a common per-cell law `ell_AB = F(ell_A, ell_B)`, where `ell = log2(g)`, followed by subtraction between cell lines. Suppose it is intended to predict this difference from the uncalibrated single-drug readouts alone, independently of the two unknown pool offsets. Then it must satisfy, over its stated domain,

`F(x+a,y+b) - F(u+a,v+b) = F(x,y) - F(u,v)`

for all admissible common offsets `a,b` and all two-cell inputs `(x,y),(u,v)`. If F is differentiable on a connected open domain, differentiate in a and b at zero. Its two partial derivatives must be the same at every input. Therefore

`F(x,y) = alpha*x + beta*y + gamma`.

Thus a local, offset-invariant law of only the two uncalibrated scalar inputs is affine. Adding the ordinary null-dose identities gives the familiar additive log-response rule. This is a basic translation-equivariance deduction, not a claimed novel theorem.

The scope of this statement is important. It does not exclude nonlinear prediction from an entire vector of relative probes, known dose structure, external calibration, or a separately measured state. It does not require every useful predictor to be pointwise. It says that an arbitrary nonlinear local map of the reported per-cell single-drug values cannot simultaneously be interpreted as an intrinsic law of absolute cellular response and be invariant to their missing independent offsets. A nonlinear map defined directly on one fixed pool's relative readouts may be a legitimate empirical predictor, but it has not thereby identified an intrinsic cell-level action law.

One qualified absolute anchor for each constituent single-drug condition would remove this particular two-offset ambiguity. Under stable recovery, an independently known reference-line fold suffices; a physical total alone does not suffice under unknown unequal recovery, as the owning readout contract explains. These anchors would identify the inputs to F, not its biological validity. They do not have to include the query combination outcome.

After calibration, a shared nonlinear response surface is still not a new mechanism. The inspected ordinary MuSyC subfamily already gives

`H(u,v) = u + v - E0 + lambda*(u-E0)*(v-E0)`

in component-effect coordinates under its stated constraints. A learned common lambda or a hierarchical update of it is ordinary response-surface estimation. It can be informative without being an original intervention-update principle. The source does not establish that the current pooled endpoint satisfies MuSyC's endpoint or sampling assumptions.

### A constructive case in which a measured update would be informative

The following is a symbolic thought experiment, not a biological finding, simulation, or recommended model for the table. It shows exactly what information could make the proposed restriction useful.

Assume an independently measured scalar state `q[c]` in `(0,1)` is a functional defense fraction relevant to B. During a fixed preconditioning interval, A changes it by

`U[A](q) = q + theta[A]*q*(1-q)`, with `-1 <= theta[A] <= 1`.

Suppose B's conditional log-fold contribution after that interval is

`ell_B(q) = -beta[B]*(1-q)`.

Assume that the contribution of A over the complete matched schedule is accounted for by an A-only schedule control; after conditioning on q, A has no remaining influence on B. This is an explicit exclusion restriction. It would fail under unmeasured A toxicity, pharmacokinetic carryover, or another A-induced state that changes B's action.

For a fixed A,B and two query backgrounds, the proposed law predicts the difference between the combination selectivity and the matched A-only selectivity:

`D[c,d,A_then_B] - D[c,d,A_only]`

`= beta[B] * {q[c]-q[d] + theta[A]*[q[c]*(1-q[c])-q[d]*(1-q[d])]}`.

The pool offsets cancel from each D. A measured pre/post-A state at an interior q identifies theta algebraically as `(q_after_A-q_before_A)/(q_before_A*(1-q_before_A))` in the noiseless one-parameter example. B-only relative responses across two different known q values identify beta from their contrast. The shared update then predicts the scheduled combination in another background without using that background's combination outcome.

The nonlinear term has content: two background pairs with equal `q[c]-q[d]` but different `q[c]+q[d]` have the same B-only contrast but different A-conditioned contrast when theta is nonzero. A predictor restricted to B-only selectivity cannot express this difference. One source transition at an interior state can determine the toy parameter, whereas a transition at q=0 or q=1 is uninformative. No real-world sample-size claim follows from this noiseless construction.

This construction demonstrates possibility under explicit observations and restrictions, not novelty. A direct predictor supplied the same q, pre/post observations, and source responses can implement the equation exactly. The product beta times theta is an ordinary restricted interaction. Standard controlled state-space learning is also an immediate methodological rival. A new scientific contribution would have to establish a specific economical state and a useful portable action restriction in real biology, or another demonstrated capability beyond what those ordinary alternatives achieve. This report has not identified such a state or cleared that target-specific prior art.

### Boundary and counterexample

Introduce an unmeasured state `r[c]` that has no effect on the legal baseline/panel readouts but changes B's action after A. Replace the conditional B effect by

`ell_B_after_A = -beta[B]*(1-U[A](q[c])) + rho[A,B]*r[c]`.

All source observations and all legal query inputs can be identical in two worlds, including q and its measured A transition, while the query combination differs by `rho*(r[c]-r[d])`. Choose small effects if needed to remain within any stipulated positive burden range. Good state reconstruction, fast adaptation, or low source prediction error cannot select the correct world. Closure is the assumption that rules out this alternative; it is not established by a baseline fit.

For the present table the boundary is even earlier: neither q nor its transition is observed. Without any proposed state, one can simply let the held-out combination log folds differ by a background-dependent term while leaving every permitted monotherapy and source combination response unchanged. This counterexample establishes non-identification under an unrestricted interaction class. It is not evidence that biological interactions are arbitrary or that useful restricted prediction is impossible.

A stronger symbolic witness shows why even collecting more concurrent endpoints would not necessarily recover a sequence update. The coordinator supplied the following standard control-system construction during development; I checked the algebra without running it. For one background, start `(x,y,z)` at zero and let drug inputs be u and v:

`x' = u`, `y' = v`, `z' = a*u*y + b*v*x`.

Under any constant coadministration u,v for time t, `x=u*t`, `y=v*t`, and `z=(a+b)*u*v*t^2/2`. Either monotherapy has z=0. For separate stages with integrated exposures U and V, A then B gives `z=b*U*V`; B then A gives `z=a*U*V`. Here U and V are the time integrals of the corresponding drug inputs, not an omitted assumption that every stage lasts one time unit. Both schedules can have the same total duration and component exposures.

Holding a+b fixed therefore preserves the entire concurrent constant-dose/time response surface while changing the ordered responses. Taking nonnegative a,b and `log2(g)=-z` gives positive burden folds no greater than one. In multiple backgrounds, preserve each background's sum `a[c]+b[c]` while varying its difference: the two worlds agree on every concurrent absolute response and thus every pooled response, but can disagree on sequential cross-background selectivity. Identical monotherapy contributions depending only on the component exposure totals can be appended in both worlds without changing the argument. The construction is a non-identification witness, not a fitted biological model.

This is ordinary noncommuting control structure, not new theory. It establishes that simultaneous data alone cannot choose the proposed sequence law even in an ideal noiseless, densely sampled version of this example. It does not refute prediction of the simultaneous surface that was actually observed, establish that these cultures have order effects, or invalidate a sequence law fixed by independent biological evidence. One nonzero ordered response would identify one of a,b within this stipulated toy family if their sum were known; it would not identify an arbitrary biological transition law. Reversed-order responses give the direct contrast `(b-a)*U*V` and a check of the stipulated restriction.

## Exact ordinary rivals and prior-source boundaries

The main practical rival is an information-matched response-panel predictor, with the additive selectivity rule and shrinkage estimated from source responses. Rhaister already learns ridge weights expressing an unmeasured intervention response as a linear combination of measured query-panel responses, using fully observed source contexts and an additive fallback. Its inspected Emerald Bay sensitivity evaluation filters to single-drug conditions. Applying the same ordinary principle to combination targets would change the evaluated target, not establish a new learning mechanism.

For a Gaussian hierarchical response model, the familiar feedback update is

`E[y_target | y_panel] = mu_target + Sigma_target,panel * (Sigma_panel,panel + R)^(-1) * (y_panel-mu_panel)`.

An affine learned residual update of this form is covariance conditioning; learning the basis or covariance does not escape that explanation. Low-rank factors learned from the same static response matrix are also an ordinary matrix-completion explanation. These equations describe rival classes, not a claim that every nonlinear learner is Gaussian or low rank.

An unrestricted direct predictor of all legal inputs and permitted feedback can reproduce the input/output map of any finite update algorithm. Therefore literal non-reducibility to every equal-information direct predictor is not a coherent observational criterion. The defensible target is a falsifiable restriction, a new identified biological capability, and useful sample efficiency or transfer under matched information and cost. Beating only a linear rival would not establish those claims if the proposed law is simply a nonlinear feature expansion.

The inspected priors constrain the proposed update as follows:

| Original and inspected locator | What is already owned or required | Difference left for this candidate |
|---|---|---|
| Rhaister, *Back to basics: Observed statistics are sufficient to predict drug responses*, DOI [10.64898/2026.06.09.731197](https://doi.org/10.64898/2026.06.09.731197), original JATS sections “The Rhaister model” and “Emerald Bay”; local `../../2026-10-30-drug-discovery-capability/sources/root07_rhaister_explicit_redirect.body` | Ridge reconstruction from observed perturbations, additive fallback, optional molecular summaries; five-day pooled endpoint | A verified state transition and transport restriction would be different. New combination labels alone would not be. |
| Bengio et al., [arXiv:1901.10912v2](https://arxiv.org/abs/1901.10912), pp. 3–5, especially Proposition 1; local `../scout/sources/bengio_meta_transfer.txt`, lines 203–250 | Learning a representation/factorization through early adaptation is prior work. Zero expected transfer gradient requires correctly learned conditionals, correct causal parents, and a conditional that truly did not change. | No general meta-learning or sparse-update novelty remains. A specified biological state, compatible repeated episodes, and its transport evidence are missing here. |
| Perry, von Kügelgen and Schölkopf, [arXiv:2206.02013v2](https://arxiv.org/abs/2206.02013), pp. 3–4, Proposition 5.1/Theorem 5.3, pp. 9–10; local `../scout/sources/perry_sparse_mechanism.txt`, lines 171–179, 348–409, 591–634 | Pairwise mechanism-shift scoring already exists, including a protein-cytometry intervention application. Common graph, sufficient within-environment observations, and stringent confounding/sparsity assumptions matter. | A static line-by-condition endpoint matrix does not provide the claimed joint-variable environment samples by relabeling rows. No new biological transfer is established. |
| Choi, [arXiv:2610.34204v1](https://arxiv.org/abs/2610.34204), Lemma 1 p. 8 and section 2.4 pp. 10–11; local `../scout/sources/stable_measurement_conformal.txt`, lines 326–364 and 455–502 | Stable-mechanism identification additionally needs injectivity; identical target inputs can support distinct outcome shifts under different conditional restrictions. | A good baseline/state fit cannot certify the closure or stable conditional proposed here. This is a current preprint constraint, not evidence that its correction method applies to this task. |
| Wooten et al., *MuSyC*, [DOI 10.1038/s41467-021-24789-z](https://doi.org/10.1038/s41467-021-24789-z), Box 1/Eqs. 10–16 and Par38–43; local `../../2026-10-30-drug-discovery-capability/prior/request03-musyc-primary.body` | Ordinary state-transition pharmacology and shared nonlinear response surfaces already exist. Par43 explicitly assumes concurrent administration and distinguishes staggered treatment. | A measured sequential update would change the observed object, but is not novelty clearance against dynamical pharmacology. Tuple order in this release supplies no such evidence. |

Reading scope: I directly inspected the Rhaister model/Emerald Bay text, Bengio Proposition 1/parameter argument, selected Perry theorem/assumption/application passages, Choi's identification and counterexample passages, and MuSyC Par38–43. The MuSyC algebra above is reused from the coordinator-owned inspected source derivation in the prior episode, rather than claimed as my independent reading of every displayed equation. No full code, supplement, or complete target-field novelty audit was performed. No HTTP was allocated or used. Existing source locators do not imply comprehensive novelty coverage through 2026-10-31.

## Smallest observation that would change the boundary

There are two different boundaries, and one should not be substituted for the other.

For a static nonlinear law of single-drug absolute effects, the smallest measurement change at one A,B dose pair is a qualified scale anchor for each single-drug condition, together with a scientifically specified response family. This removes the two unknown input offsets. It neither identifies a dynamic update nor makes shared MuSyC or hierarchical surface estimation novel. Exact-dose constituent support and the released-column transformation must still be qualified before any analysis.

For the actual update candidate, the minimum informative new evidence is an existing processed, matched intervention-history observation: the same prespecified state measured before and after A, together with a B challenge and the appropriate A-only/vehicle schedule controls. Merely adding another simultaneous combination endpoint does not observe the update. A reversed-order pair under matched doses and exposure windows can refute an unordered endpoint model, but cannot by itself establish the proposed state or exclude pharmacokinetic carryover.

In the toy one-state case, one interior pre/post-A transition and a B contrast across two known states determine the parameters algebraically. A further combination contrast in a background not used for that fit is the smallest falsifying prediction. It is not sufficient empirical confirmation: real inference needs qualified independent preparations and uncertainty, more than one informative state to test the update shape, and states/backgrounds withheld from fitting. No universal numerical replicate count is derived here. Small processed measurements could meet this requirement; new raw sequencing or model weights are not inherently required. No such source is established in this analysis.

The most direct closure challenge is a same-state/different-history comparison: arrange or find two backgrounds or preconditioning histories with the same measured post-A state, then compare the subsequent B response under matched measurement conditions. A reproducible response difference rejects state sufficiency. A match supports only the tested range and does not prove mediation; a molecular mediation claim needs additional intervention/target-engagement evidence.

If that data contract becomes real, a minimal meaningful prediction test would fit the shared update using source transitions, freeze it, and predict a reserved A-then-B relative selectivity contrast in a new background or intervention-history block. Compare the same observations with an ordinary nonlinear conditional predictor, a controlled state-space model, response-panel ridge/covariance conditioning, and the additive rule. Charge the state assay and all feedback to every arm. Test the portability/closure prediction as well as decision accuracy; avoid treating pooled line contrasts as independent assay replicates. A wrong prediction rejects the specified restriction. Equal performance leaves it scientifically unproven. A reproducible advantage at equal total information and cost would support the restriction's utility, not automatically its causal interpretation or novelty.

No such test is defensible as an operator-mechanism experiment on the currently inspected table. A descriptive combination-prediction experiment could still be designed for a separately justified incremental question. It should not be admitted just to produce a numerical result for the present mechanism objective.

## Handoff and process record

Decision: **do not promote this candidate from the present source**. Retain the narrow constructive condition—an independently measured, sufficiently informative functional state with a shared intervention update—as a conditional research question. The missing evidence is a specific transition/closure observation, not a larger embedding, more meta-learning steps, or another name for covariance conditioning.

The root owns candidate selection and freeze. A different fresh challenger must review any substantial version of this proposed update, or this mathematical boundary if used as a decisive exclusion. This developer has not reviewed its own proposal independently and has not dispatched another agent.

Requested configuration, as supplied in the coordinator assignment: `gpt-6-astra`, reasoning `max`. Effective serving model/effort are not exposed to this agent and are not certified. Native token counts, model cost, and total tool cost are unknown. Actual activity: local source/metadata reads, symbolic reasoning, and one Markdown report; zero HTTP, zero response-value exposure, zero numerical experiment/fitting, zero installations, zero protected-data access, zero author-code execution, zero shared-file edits, and zero subdelegation. The only authored artifact is this file in `developer/`.

Owning measurement evidence: `../../2026-10-30-drug-discovery-capability/evidence/readout_contract.md`, `../../2026-10-30-drug-discovery-capability/data/summary_metadata.json`, and `../root/pooled_design.json`. The source hash is `3b4b9e451eab1106b7e47aac1b68d5181f0e684c021c88fc63f0dca01d7cc5c9`. Root metadata updates received during this analysis were incorporated without opening the numerical table.
