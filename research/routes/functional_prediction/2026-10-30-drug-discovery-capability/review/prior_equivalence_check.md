# Independent mathematical check of selected prior equivalences

2026-10-30. Bounded follow-up to `prior/evidence.md`; this does not replace the initial source assessment or evaluate numerical target outcomes.

## Findings and corrections

1. **The full residual-surface equivalence is exact.** On the same domain and response coordinates, subtracting one common function `N(u,v)` gives `H_R-H_P = (H_R-N)-(H_P-N)` pointwise. Justification of N is needed to interpret the residual as a particular pharmacological interaction, not for this subtraction identity itself. A full residual function is essential; scalar synergy summaries or same-dose comparisons do not establish it.
2. **The stated MuSyC product-state subfamily is exact.** Both directional alpha parameters and both gamma parameters must equal one. Shared `E0,E1,E2,E3`, nondegenerate/invertible axes, and the equilibrium four-state model yield the same H after state-specific Hill potency/slope recalibration. This follows directly from the owning transition equations, not merely the prose description of parameter names.
3. **Common E0–E3 is sufficient, not necessary.** The resulting H has a simpler bilinear form given below. Generic sharing of MuSyC interaction labels is not a proof of common H, particularly when marginal endpoint ranges change. The prior note already qualifies this correctly; no reversal of its central conclusions is needed.
4. **Arbitrary Loewe recalibration would overclaim.** Multiplicative dose scaling preserves the inverse-dose ratios in the standard Loewe equation; general nonlinear monotone axis registration does not. This is independent of whether the source archive can currently be obtained.

## Owning primary source actually inspected

`prior/request03-musyc-primary.body`: Wooten et al., *MuSyC is a consensus framework that unifies multi-drug synergy metrics for combinatorial drug discovery*, Nature Communications 12 (2021), DOI `10.1038/s41467-021-24789-z`, PMCID `PMC8322415`.

Decision-relevant XML locators: **Par6 and Table 1 (`Tab1`)** define baseline/asymptotes, C/h, beta and directional alpha/gamma. **Par8** states multiplicative survival and the conditional reduction to Bliss. **Par9** describes dose equivalence and its conditional MuSyC reduction. **Box 1 (`boxed-text1`), Eqs. 10–16 (`Equ10`–`Equ16`), especially Equ11–15**, own the Hill marginals, four-state transitions, equilibrium system, normalization and endpoint-weighted response. I read the selected prose and equations, including a second concise extraction of the owning formulas after an initial verbose extraction was truncated. I did not inspect supplements, images, author software or any target outcome data.

## 1. Full matched-effect interaction residuals

Let D be the qualified common component-effect domain. Assume both H functions are expressed in the same declared response coordinate, and let one fixed `N:D→R` apply in both states. Define

`S_b(u,v)=H_b(u,v)-N(u,v)`.

Then, at every point of D,

`S_R(u,v)-S_P(u,v)=H_R(u,v)-H_P(u,v)`.

Thus `H_R=H_P` on D if and only if `S_R=S_P` on D. The same absolute pointwise tolerance, and any common norm of this difference, is retained exactly. There is no separate independent empirical fact in verifying both statements. This is algebraic restatement of the scientific restriction, not a new transport theorem or evidence that portability holds.

If instead each state uses a different reference `N_b`, residual equality means `H_R-H_P=N_R-N_P` and is not the proposed restriction. Equal averages, volumes or fitted synergy parameters need not imply equal full residual functions. Different endpoint normalizations must be resolved or explicitly made part of the estimand before attaching a shared biological interpretation to raw u/v coordinates.

For a decreasing, normalized surviving-fraction response with untreated reference one, Bliss uses `N(u,v)=u*v` under its multiplicative-survival interpretation. **Par8** explicitly discusses independent survival probabilities; its MuSyC reduction requires `E0=1`, `E3=E1*E2`, alpha parameters one and gamma parameters one. A percent label does not supply the survival interpretation. On a percent scale from 0 to 100 rather than fractions, the corresponding product is `u*v/100`. On an inhibition scale the formula changes again. The HPAC CTG endpoint is unresolved, so Bliss remains conditional. A common arbitrary N still cancels algebraically even if its Bliss interpretation is invalid; those two facts must not be conflated.

## 2. Product-state MuSyC derivation

In the source's Equ11–13, write the isolated forward and reverse rates for drug i as

`a_i=r_i*d_i^(h_i)`, `b_i=r_-i`, and `x_i=a_i/b_i=(d_i/C_i)^(h_i)`.

Set **both** `alpha12=alpha21=1` and **both** `gamma12=gamma21=1`. The transition rates for adding/removing drug 1 then agree whether drug 2 has acted, and vice versa. Directly in the equilibrium equations Equ12/13, the following normalized state vector balances each pair of transitions:

`(U,A1,A2,A12) = (1,x1,x2,x1*x2) / ((1+x1)*(1+x2))`.

For example `a1*U=b1*A1` and `a1*A2=b1*A12`; the analogous two drug-2 balances also hold. Their weights sum to one. Positive reverse rates and finite admissible doses give the ordinary unique equilibrium; zero-dose boundary weights follow by continuity. This construction therefore solves the owning system used in Equ14/15 rather than assuming the desired surface.

Let `q_i=x_i/(1+x_i)`. Equ15's endpoint-weighted mean becomes

`Y=E0*(1-q1)*(1-q2)+E1*q1*(1-q2)+E2*(1-q1)*q2+E3*q1*q2`.

The axes from Equ10 or by setting the other q to zero are

`u=E0+(E1-E0)*q1`, `v=E0+(E2-E0)*q2`.

For `E1≠E0` and `E2≠E0`, substitute

`q1=(u-E0)/(E1-E0)`, `q2=(v-E0)/(E2-E0)`.

Expansion gives the explicit function

`H(u,v)=u+v-E0+lambda*(u-E0)*(v-E0)`,

where

`lambda=(E3-E1-E2+E0)/((E1-E0)*(E2-E0))`.

No C or h remains. Hence common E0–E3 makes H identical even when the two states have different positive C and positive finite h values. Recalibration must be confined to common, one-to-one, supported axis ranges; formal invertibility does not ensure useful inverse precision near plateaus. This deduction concerns equilibrium MuSyC and its Hill marginals. It does not establish that a finite-time assay follows that equilibrium model, or that empirical non-Hill monotone curves fit MuSyC exactly.

The bilinear expression also shows why shared E0–E3 is not necessary: shared E0 and the same lambda suffice within this subfamily, even if some individual endpoint parameters differ. The derivation establishes an exact included subfamily, not an equivalence between all portable empirical surfaces and MuSyC.

### Relation to Bliss and nontrivial efficacy interaction

With `E0=1`, the formula is

`H=u+v-1+lambda*(1-u)*(1-v)`.

Because `u*v=u+v-1+(1-u)*(1-v)`, Bliss is obtained exactly when `lambda=1`, equivalently `E3=E1*E2` for nondegenerate axes. Any other shared admissible E3 produces a different shared surface, so the exact overlap includes non-Bliss efficacy interaction. A parentally measured E3 can then contain joint-response information not determined by the single-agent axes. This is a model fact, not evidence that the HPAC data occupy that subfamily or that such historical information improves decisions.

### Why generic shared interaction parameters are insufficient

Table 1 defines

`beta=(min(E1,E2)-E3)/(E0-min(E1,E2))`.

A symbolic counterexample already exists inside the product-state subfamily. Take common `E0=1`, `E1=E2=e`, and common beta, so `E3=e-beta*(1-e)`. Then

`lambda=(1-beta)/(1-e)`.

If e differs between states, lambda generally differs even though both alpha parameters, both gamma parameters and beta are all shared. On an interior common effect range, H then differs. This argument is symbolic and uses no target outcome or numerical fit. Special cases such as beta one do not rescue the general claim. Baseline/asymptote constraints and the actual coordinate function must be checked; parameter-label sharing is insufficient.

Nor is the reverse containment established: an arbitrary shared empirical H can be non-bilinear or have non-Hill marginals, so it need not belong to this finite-parameter subfamily. “MuSyC overlap” is accurate; “the frozen restriction is exactly generic shared MuSyC interaction” is not supported.

## 3. Loewe calibration qualification

Using the conventional dose-equivalence equation on an admissible common response range, let `g_b=m_b^{-1}` and `k_b=n_b^{-1}`. A Loewe-additive combination response w solves

`d/g_b(w)+a/k_b(w)=1`.

After component-effect registration, `d=g_b(u)` and `a=k_b(v)`, so the equation is

`g_b(u)/g_b(w)+k_b(v)/k_b(w)=1`.

If `g_R=s1*g_P` and `k_R=s2*k_P` for positive constants s1/s2, each scale cancels. With common qualified response ranges and a unique relevant root w, the same Loewe surface in u/v follows. If instead `g_R=T1(g_P)` and `k_R=T2(k_P)` for general increasing nonlinear maps, the ratios need not agree. For example replacing positive doses by their k-th powers changes ratios t into `t^k`; preservation of `t1+t2=1` does not generally preserve `t1^k+t2^k=1`. Equal Loewe-additive status in both states therefore does not generally imply equal H after arbitrary monotone calibration.

Source precision: the XML inline equation `IEq4` in **Par9** prints `f_i(d_i)` in its numerator while the following prose calls f_i a monotherapy response. That is not the literal conventional dose-over-equivalent-dose equation written above. I use the standard Loewe definition explicitly for this derivation rather than silently treating the XML notation as a verified transcription of it. The prior note says “in standard Loewe notation,” so this does not require changing its mathematical conclusion.

## Scientific implication and limits

The new evidence supplies an exact algebraic alias and an exact ordinary parametric overlap. This tightens the boundary on claims of mathematical/model novelty. It does not decide the empirical state-transfer restriction, identify molecular mechanism, validate a new therapy or demonstrate Agent benefit. A local transport result could still be useful if it predicts resistant decisions beyond compatible ordinary comparators and at a justified information/cost budget. The exact protocol's publication history remains unresolved by this single-primary inspection.

Current source-access failures neither prove nor refute the biological restriction. They affect the feasibility of the next data-admission step. No reviewer vote or additional hypothesis is supplied here.

## Exposure and resource accounting

Read this follow-up's `prior/evidence.md` and only the selected owning MuSyC XML material described above; retained the existing frozen-question and original HPAC-source exposure from the initial assessment. The initial assessment had already been saved before these new readings. No proposer development, other reviewer report or shared coordinator report was inspected for this check.

This follow-up used **0 HTTP/API calls, 0 numerical target outcomes, 0 ZIP/source-archive accesses, 0 experiments/scientific tests, 0 author-code runs, 0 model bridges and 0 subagents**. Python was used only for selected source-text/MathML extraction; derivations were performed by reasoning, with no symbolic/numerical solver. Only this review file was written; shared reports and existing files were not edited. Requested configuration was inherited Sol/high; effective runtime/model settings, token count and cost were not exposed, so they are unknown here.
