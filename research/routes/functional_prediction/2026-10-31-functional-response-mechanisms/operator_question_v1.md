# I002.v1: can static functional responses identify an intervention update?

2026-10-31. **Frozen scientific question for independent qualification, not an admitted model or numerical protocol.** Parent: the continuing Virtual Cell-first objective and the newly audited legal pooled-response design. A shared state update was developed after independent source scouting. No numerical response values were inspected. No novelty or biological benefit is claimed for the mathematical constructions below.

## Important unknown and possible practical use

A useful functional virtual cell would predict how an intervention changes a cell's susceptibility to a later intervention in an unmeasured background. A drug-discovery team could then choose a follow-up schedule or combination using existing processed functional/state measurements. The practical question is whether a compact measured state and a shared intervention update predict such held-out consequences with less justified calibration than ordinary direct conditional prediction. Assay costs and source/target feedback must be equal across rivals. Actual benefit is untested.

Proposed restriction: `z_after_A = U_A(z_before_A)` and `effect_of_B_after_A = h_B(z_after_A)`, with the relevant A/history/background effects exhausted by this state and the declared schedule controls. This closure and transport assumption is the scientific hypothesis; an embedding or fast refit does not establish it. Generic controlled state-space learning, causal representation learning and dynamical pharmacology already exist. No exact new algorithm difference has been established.

The qualification question is whether the currently legal observations distinguish this restriction from alternatives that match those observations but disagree on the requested future action. A negative identification result is distinct from a poor prediction score and from proving that no useful inductive bias exists.

## Actual observation contract

The existing Rhaister/Emerald Bay summary has SHA256 `3b4b9e451eab1106b7e47aac1b68d5181f0e684c021c88fc63f0dca01d7cc5c9`. It physically contains a response column, but only cell-line and condition identities were semantically read. Under the qualified observation assumptions, `S[c,p] = log2(g[c,p]) - k[p]`, with an unknown condition-specific pool factor. Stable line-specific recovery permits cross-line contrasts; treatment-dependent differential recovery can invalidate them.

The root metadata-only audit in maestro establishes 52 cell lines and 93 conditions: 44 noncontrol single-drug conditions from 19 names; 41 two-drug, three three-drug and three four-drug conditions, covering 16 combination families. Only **17 two-drug conditions** have both exact-dose constituent single conditions. No higher-order condition has all exact single doses. These are condition counts, not independent culture repeats or qualified response surfaces. There are no sequence/order/preparation fields in this summary. Tuple order is not a dosing schedule; a combination label alone does not authenticate simultaneous or sequential administration.

For declared backgrounds c,d, `D[c,d,p] = S[c,p]-S[d,p]` is relative selectivity under the observation model. When exact single doses exist, `J[c,d,A,B] = D[c,d,A+B]-D[c,d,A]-D[c,d,B]` is differential departure from a multiplicative fold reference. It is not absolute synergy, viable burden, death, normal-cell safety or clinical efficacy. No D or J values have been computed.

Rhaister already predicts responses using measured query panels, ridge and additive fallback. Gaussian feedback conditioning, factor completion, controlled state-space models, flexible conditional models and the appropriate ordinary response-surface model are necessary rivals. An unrestricted direct predictor can reproduce any finite update algorithm's input/output function; absolute non-representability by direct prediction is not the selection standard.

## Claim A: limited scalar offset boundary

Consider a **common differentiable pointwise** function F of only two uncalibrated single-drug log folds. On a connected open domain, require for every pair of points and every locally admissible independent common shift a,b:

`F(x+a,y+b)-F(u+a,v+b) = F(x,y)-F(u,v)`.

Differentiating in a and b at zero makes the two partial derivatives constant across inputs, hence `F(x,y)=alpha*x+beta*y+gamma`. If additional zero-exposure consistency identities are justified on a domain including the relevant axes, their additive-log null is the ordinary no-interaction reference. A zero observed effect is not automatically zero exposure.

This is a translation-invariance deduction, not new theory. It does not exclude nonlinear maps of whole contrast vectors, measured states, known dose/identity structure, external anchors or scientifically restricted offset families. It does not require all valid predictors to be pointwise or prove that absolute cell action is unknowable with other measurements. A qualified absolute anchor for each constituent condition removes this particular input-offset ambiguity; it does not identify a dynamic update or validate a response surface.

## Claim B: a standard control witness for missing order information

For one background, start state (x,y,z) at zero and use nonnegative constant or staged drug controls u,v:

`x'=u`, `y'=v`, `z'=a*u*y+b*v*x`.

Any constant coadministration u,v over time t gives `(x,y,z)=(ut,vt,(a+b)*uv*t^2/2)`. Singles have z=0. Separate stages with integrated exposures U,V give `z_A_then_B=b*U*V` and `z_B_then_A=a*U*V`. Holding a+b fixed while changing a-b preserves all constant coadministration dose/time trajectories from this initial state but changes ordered responses. The fixed-initial-state restriction matters: knowing the vector field at arbitrary intermediate initial states could identify the coefficients.

For a concrete two-background pair of worlds, set `(a_c,b_c)=(0,2)` and `(a_d,b_d)=(1,1)` in world 1, and `(a_c,b_c)=(2,0)`, `(a_d,b_d)=(1,1)` in world 2. Let `log2(g)=-z`. All constant coadministration absolute and corresponding pooled responses agree between worlds. With U=V=1, the A-then-B log-fold contrast between c,d is -1 in world 1 and +1 in world 2. The folds are positive and at most one. Equal schedule duration and component exposures can be used in both worlds. Arbitrary identical monotherapy contributions can be appended without removing the between-world ambiguity.

This is a mathematical counterexample, not simulated or observed biology. It rules out a general data-only identification guarantee over this model family from the specified static/concurrent design, even with noiseless dense data. It does not establish that the actual cultures have these dynamics or order effects, that unordered tables never contain useful predictive information, or that all simultaneous measurements are uninformative. The actual summary does not even authenticate these richer simultaneous state observations.

The classical source is LaValle, *Planning Algorithms* (2006), chapter 15, §15.4.2: ordered flows/Lie bracket, Eqs15.75–15.81; its Example15.10/Eq15.83 is the special case a=-1,b=1, the nonholonomic integrator. The fixed-sum pair-of-worlds argument above is root's explicit derivation using this standard structure, not an attributed book theorem or new control invention. Biological inverse controls, driftless dynamics and observable smooth state are not supplied by a pooled assay.

## Constructive conditional opening and how it can fail

A symbolic measurable-state example: observe a defense fraction q in (0,1), with `U_A(q)=q+theta_A*q*(1-q)`, theta_A in [-1,1], and conditional B log-fold `ell_B(q)=-beta_B*(1-q)`. With matched A-only schedule control and no remaining A-to-B path outside q, an interior pre/post-A observation identifies the toy theta, and B contrasts across two known distinct q values identify beta. The resulting shared update predicts a held-out background's A-then-B contrast. Equal differences q_c-q_d can yield different conditioned contrasts when q_c+q_d differs. This is a constructive possible restriction, not an identified biological state, new algorithm or real sample-size claim.

An unobserved state r that leaves every legal input and measured q transition unchanged but adds `rho_AB*(r_c-r_d)` to the later B contrast defeats identification. State reconstruction or early adaptation fit does not certify closure. A same-measured-state/different-history B challenge is a direct falsification attempt. Ordinary nonlinear conditional prediction can represent the toy law when given the same q/transitions; a fitted interaction beta*theta is not by itself a new mechanism.

The minimum useful observation depends on the claim. Qualified single-condition scale anchors address Claim A. Matched A→B/B→A schedules with doses, equal elapsed/exposure conditions, washout/carryover and independent preparations can test order sensitivity. A measured transition plus a subsequent challenge and schedule controls is needed to test the proposed state/update closure; order endpoints alone do not prove mediation or state sufficiency. One ordered measurement identifies a coefficient only inside the stipulated two-parameter toy family, not arbitrary biological dynamics.

## Source and review boundary

Original source passages available to the independent reviewer: Bengio arXiv1901.10912v2 Proposition1/§2; Perry arXiv2206.02013v2 §5–6 including Sachs biological application; Choi arXiv2610.34204v1 §2.4 identification counterexample (2026 preprint); LaValle original author chapter §15.4; Rhaister original model/Emerald Bay source; ordinary MuSyC original Methods. These require compatible conditions and do not collectively establish a new biological mechanism. The independent reviewer should assess the mathematics, its limits, the actual observation match, the constructive opening and strongest ordinary alternatives without a requested verdict.

No model, response-value inspection or synthetic benefit test is admitted by this record. A genuine real-data operator test would need a new complete numerical protocol, source/target/feedback costs, frozen code and actual independent review before responses. In particular, do not substitute routine combination prediction on this table for a state-update mechanism test merely to produce numbers.
