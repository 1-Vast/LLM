# Frozen conditional object: can extracellular redox protection preserve drug isoeffect relations?

Version 1, frozen for independent challenge, 2026-10-30 within the 2026-10-29 episode and shared passes 17–18. This is a **conditional biological relation**, not an established mechanism, new algorithm, empirical result or experiment admission. Initial alternatives are preserved in `initial_directions.md`; source passages and exact ownership are in `source_grounding.md`. Effective model/effort/tokens/cost remain unknown. The developer has not independently reviewed this object.

## The useful question and the narrow proposed change

A screening laboratory has measured multiple drug dose curves on a reference extracellular support. It now needs to decide which hits remain useful on a second controlled support, without immediately assaying every hit there. The question is whether extracellular support changes a **shared resistance margin** for a biologically specified family of drugs, so that a reference drug measured on the second support transfers the old dose-response scale to still-unmeasured drugs.

The new source makes this question concrete: engineered stiffness and washed, decellularized ECM can change PDAC gemcitabine sensitivity through a background-dependent redox program. The source already owns that mechanism and its BRG1/NRF2 gate. What it does **not establish in the inspected passages** is a drug-independent relation transporting functional drug effects between extracellular contexts. The proposed scientific object is that extra relation, including where it fails. This is not a claim that the relation is absent from all prior literature.

The central restriction is simple:

> In a fixed, qualified cellular background, two drugs/doses that produce the same true functional effect on the reference support should still produce the same effect on the changed support, if that support acts only by shifting a common redox protection margin and both drugs challenge the same margin without changing it themselves.

This makes an unmeasured target prediction. It is stronger than “stiff matrices cause resistance,” a BRG1 label, an arbitrary context-conditioned response model, or an unconstrained low-dimensional embedding. It is deliberately restricted to a family established independently of the target-context outcomes; gemcitabine's membership is not guaranteed merely because one part of its response involves ferroptosis.

## Biological inputs, relation and observable prediction

Available inputs at use time would be: fixed human cell background and independently established pathway competence; a reference support s0; a changed observable support s1; identical dose, exposure duration, medium, starting population and endpoint definitions; old functional dose curves y(d,c,s0); and a paid reference-drug curve y(r,c,s1). The target drug's outcome at s1 remains unmeasured.

An explicit enabling model is a population with a common susceptibility distribution F. Drug d at dose c contributes an effective oxidative injury q_d(c). Support s changes only a shared protective margin a_s. For a fixed endpoint and observation interval,

`y(d,c,s) = F(q_d(c) - a_s)`.

Here y increases with functional injury. F must be one common response function for this qualified cell population, not an independently chosen curve per drug or support. q_d must remain invariant when support changes; a_s must remain invariant when the drug changes. The model presumes that differences in oxidative timing, growth, cell-cycle engagement and other killing routes have been controlled or shown irrelevant over the proposed domain. These are testable, strong biological assumptions. P2 motivates a redox margin but does not establish this common-threshold model.

For a reference y value in a region where F is one-to-one,

`q_d(c_d) = q_r(c_r)` if `y(d,c_d,s0) = y(r,c_r,s0)`;

therefore

`y(d,c_d,s1) = y(r,c_r,s1)`.

Equivalently there is a single context map `T_s1<-s0` with

`y(d,c,s1) = T_s1<-s0(y(d,c,s0))`

for all independently qualified drugs and tested doses. A reference curve measured at both supports estimates this map over its observed, nonsaturated range. A target dose matched to a reference dose at s0 then inherits the reference's s1 prediction. No fitting of target-context values is allowed before this prediction.

Observable restrictions include preservation of drug ranking at matched old effects, one context map across the qualified drugs, and agreement on repeated old-response levels reached by different drugs. If three supports are actually qualified, maps should compose consistently over overlapping measured ranges. Composition alone is not decisive evidence: arbitrary invertible one-drug curves can be composed; the **cross-drug equality at matched old effects** does the scientific work.

Neither a general shift of IC50 nor common curve slopes is assumed. The map may be nonlinear because F is nonlinear. At plateaus, equal old output does not identify equal injury, so no transport inference is licensed. Finite-noise matching requires an interval propagated through the reference curve; exact equality is the ideal mathematical statement, not a practical precision claim.

## Constructive possibility and a biological failure boundary

The constructive case is analytic, not simulated or observed. Suppose two load-generating interventions have different dose-to-injury functions but challenge the same fixed population thresholds. Choose doses making q equal on s0. Changing only antioxidant protection a shifts both injury margins by the same amount. Their outputs stay equal on s1; one reference measurement then answers both unmeasured dose questions. If the common s1 response crosses a prespecified hit threshold, the rule changes the screening decision. Different cellular backgrounds require their own qualified margins/maps unless a further cross-background law is separately established.

A counterexample uses a biologically meaningful alternative, not representation equivalence. One drug supplies extra oxidative injury; a second instead blocks the defense that is upregulated by stiffness. At s0 their outcomes can be matched. On s1 the first can become less effective while the second becomes more effective, because its action scales with the changed defense. Thus old isoeffect does not force new isoeffect. **Erastin is a candidate challenge of this kind, not automatically a valid reference load probe**, because it perturbs cystine-dependent protection. P2's inclusion of Erastin makes this alternative relevant but does not provide an unexamined cross-context test result.

Other concrete failures are drug-dependent NRF2 induction, environment-dependent uptake or metabolism, a changed distribution of cell states rather than a uniform margin shift, adhesion/cell-cycle effects, distinct oxidative time profiles, and support-dependent assay metabolism. Any of these can produce target-specific context effects with the same old functional curve. A one-drug calibration cannot identify which case holds for an unseen target. A functional fingerprint at s0 alone therefore cannot certify family membership.

This limitation is substantive: the present evidence does **not** yet identify a family of multiple human oncology compounds for which support changes only a shared margin. There is no valid “all cytotoxic drugs,” “all ROS-associated drugs,” or “all BRG1-positive cells” extension. A single trained transfer map would otherwise just conceal this unverified assumption.

## Agent decision and strongest ordinary rivals

If the family were qualified, an Agent could purchase a reference curve on the new support, match old target doses to reference effects, and predict which target hits remain above a predeclared functional-injury threshold on that support. The functional virtual cell would encode the common-margin relation and its admissible background/drug/support domain. A targeted violation would remove or revise that domain before further transfers. This is the intended scientific interaction; no particular model architecture or Agent novelty is claimed.

The strongest ordinary rivals get the same old curves, paid reference measurements, support information and assay budget: direct target-context screening; an ordinary joint drug/dose/support response model with pathway/chemical features available at the same time; monotone calibration using the same common-map hypothesis; dose-response matrix factorization; and a model with separate oxidative load and defense dependence. The proposed map can be expressed by ordinary inference. That fact does not refute the biology; it means there is no demonstrated algorithmic contribution and no reason to add an Agent merely to rename calibration.

For one new drug at one chosen dose, direct testing is at least as natural as buying a reference curve and costs must decide. Possible amortization exists only when multiple target decisions reuse an already qualified family/context map. Family qualification, baseline dose curves, reference probes, biological/technical controls, orthogonal endpoint checks and failed cases all count. There is no established assay saving or decision gain. The same functional endpoint and total measurement/timing costs must apply to all rivals.

## Exact closest-prior difference and what is still missing

Against **PNAS 10.1073/pnas.2423894122**, the object is not CAF induction, contact support, autophagy, dormancy, inhibitor sensitization or prevention versus maintenance. That prior also gives a reason not to choose division opportunity as the universal mediator. Its selected main-text 1:1 cocultures do not supply this proposed cross-drug isoeffect relation.

Against **Nat Commun 10.1038/s41467-026-75772-5**, the object is not the stiffness→Piezo1→NRF2/BRG1 mechanism, gemcitabine response gate, or senolytic/ferroptosis combination. The candidate asks whether a separately specified family has a **drug-independent transport map of functional effect** between controlled extracellular supports, sufficient to decide an unmeasured drug/context entry. The inspected source does not establish that common map or family. P2's CCK-8 output also cannot silently stand for reproductive survival. Its cited **Nat Mater 10.1038/s41563-024-01908-x** is an uninspected close biological prior whose original could materially reduce this difference.

The mathematics is ordinary shared latent susceptibility and monotone response calibration; it is not proposed as a new theorem or algorithm. Broader prior coverage for equieffective response transport has not been completed. The scientific contribution would have to be evidence for a restrictive, useful biological domain plus its failures, or a rigorous negative result showing that even that domain does not support transport. Neither has been achieved.

## Smallest condition that would change the decision

No scientific test is proposed for immediate execution from current evidence. First establish an actual public observation contract with (i) at least two candidate load-type drugs plus a reference drug, or two drugs with one held out and enough dose overlap to make matching informative; (ii) two explicitly controlled extracellular supports within the same background and time window; (iii) an independently justified family assignment and observable pathway gate; (iv) independent preparations with matched exposures, medium/volume and initial population; (v) functionally interpretable matched readouts, preferably live counts and/or a relevant reproductive endpoint, rather than assuming CCK-8 equivalence; and (vi) source identity, raw-data access and prior exposure status. A small design can falsify the relation; it cannot establish broad family/generalization coverage.

The first decisive source/data question is **whether multiple matched drug dose curves across the same controlled support change exist, with a true common functional endpoint and enough information to assign load versus defense action without observing target-context effects**. The current P2 narrative establishes useful support interventions and background gates but does not establish that contract. Its source-data file and SI have not been inspected here. A full across-drug/source test or a cheap public resource is therefore unknown, not nonexistent.

If the contract exists, freeze one reference curve and target drug before opening target-context outcomes, match only in the nonsaturated common-effect interval, and compare predicted target-context effects/decisions with direct and ordinary joint-model rivals at the same total budget. A target-specific reversal at matched old effects would reject this common-margin version for that domain. Agreement without independent drug or material variation would support only the tested local domain. A missing overlap, unclear readout, or insufficient independent preparations would be inconclusive/data-unqualified.

**Current disposition:** retain this as a concrete conditional object for challenge, with the load-bearing biological family restriction and public-data contract missing. Do not recommend a main algorithm or revive old scalar-cycle/ATP-founder objects. The initial finite-dose sink, support-capacity and competition branches remain ungrounded in qualifying local human sources; no evidence was found here that warrants substituting them for the frozen object. Zero new source acquisition by this worker; zero outcome-value consumption or scientific runs.
