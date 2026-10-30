# Developed result — endpoint relations can reverse action, but these sources do not qualify a new co-learning claim

2026-10-29. Independent alternate development branch in pass15. Initial alternatives were saved in [initial.md](initial.md) before reading any parallel candidate or agent verdict. No parallel candidate/verdict was read for this development. No new HTTP, response-file values, scientific run, external model call, author code, installation or protected access. This branch used only published paper text/captions/protocols, the official source-file listing, and relevant original archived reports. Native model/settings/cost remain unexposed beyond the requested gpt-6.1-sol/high.

**Finding.** A learned relation between ATP, surviving-cell abundance and reproductive survival can logically reverse a real drug/schedule decision. The meaningful biological distinction is metabolically active survivors versus survivors capable of repopulating after withdrawal. The inspected P3/P4 material does not establish matched observations needed to identify that relation. Moreover, short-term viability versus long-term growth, and history-dependent functional states, already have direct source/archive ownership. This branch therefore supplies an exact conditional question and a resource boundary, not a new mechanism/algorithm recommendation or an empirical negative.

## Exact question and relation

For a human tumor-cell background c and a physical treatment history h ending at time t, let:

- A(c,h,t) be blank-corrected total ATP luminescence, before lysis;
- N(c,h,t) be the number of live cells entering a defined recovery assay;
- p(c,h;t,T) be the probability that a randomly sampled live entry cell produces a colony by a fixed recovery deadline T after an explicitly defined washout and replating protocol;
- C(c,h;t,T)=N(c,h,t)p(c,h;t,T) be expected reproductive survivor burden at the entry time.

The final equality is an expectation identity under additive colony-founder output, not a new biological law. It requires an assay in which colony assignment to an entry cell is meaningful, specified plating efficiency, handling and density, and no uncontrolled merging. It does not require mutual independence for the expectation, but preparation/family dependence matters for uncertainty. If one instead measures total descendants at T, the multiplier is expected descendants per entry cell and can exceed one; it must not be silently called a colony probability.

Write A=mN only as the definition of population-average luminescence per live cell m when N>0. ATP contains signal from non-live material unless blank/background handling excludes it; this needs qualification rather than assertion. The scientifically testable question is whether the **relationship between m and p changes with drug action/history**, such that A and N fail to order C, and whether a constrained relationship learned in paid, matched assays transfers to a drug/background not used to establish it. Learning an arbitrary C=f(A,N,h) is ordinary outcome prediction. A general joint model can implement any useful restricted relation; that fact does not refute biological value, but no distinct relation or innovation is established merely by writing this decomposition.

The practical decision is which drug or finite schedule to advance when the laboratory wants durable suppression after treatment removal. At an actual immediate decision time, C is a future target and cannot be treated as already observed. Delayed C measurements can update a virtual-cell relation used on later cultures; the agent chooses which matched assay to pay for and later changes an unmeasured action decision. This supplies a real feedback path, while leaving its necessity, cost and advantage unproven. It cannot promise clinical benefit.

## Constructive enabling case and failure cases

A hand-constructed example, not an experiment or simulation: two regimens at their common stopping time have (A,N,p) equal to (20,20,0.90) and (30,60,0.10). Ranking by lowest ATP prefers regimen1. Their reproductive survivor burdens are 18 and 6, so ranking by expected colony founders prefers regimen2. The first has fewer metabolically active cells but most retain reproductive capacity; the second has more live cells whose reproductive capacity is poor. This is a real change in the action objective, not an RMSE claim. A matched historical relation strong enough to predict p could enable the second choice before C is available. The numbers demonstrate possibility only, not a plausible numerical effect size or a transferable law.

Important failure cases:

1. If p/m is a common positive constant across both candidate actions under the qualified protocol, C=(p/m)A and ATP already gives the same ranking. A calibration that only rescales A cannot improve that choice.
2. If p varies arbitrarily after conditioning on A,N and observed history, learning m does not identify p. Two populations can have identical (A,N) but p=.1 versus .9; another ATP/count observation at the same endpoint need not resolve them. One needs a genuinely informative functional observation or a validated restrictive relation. Calling the missing variable a virtual-cell state adds no information.
3. If matched post-washout C is equally cheap and available before the action must be chosen, direct C measurement is the strong alternative. An indirect relation has no automatic saving. If it is delayed, both arms must receive the same calendar-time constraints and historical information; compare total training, control, replicate, failed-well and decision-delay costs.
4. Crystal-violet occupied area is neither N nor C without an identified observation relation. A paper calling an image a clonogenicity experiment does not make early fixed area a per-founder colony probability.

## What distinguishes the proposal from a strong ordinary rival

A one-dimensional ATP-only model is too weak. The relevant rival uses the same complete continuous A/count/history data, flexible joint outcome inference, delayed C labels, and the same acquisition menu/budget. It can learn action-specific observation maps, time dependence and survivor composition. No mathematical exclusion or incremental learning operation over this rival was found here.

A useful distinguishing scientific observation would be a reproducible crossed-action pattern: under matched culture preparation and fixed t,T, equal (or predeclared narrow-range) A and N but different C, followed by a held-out action/background on which a **previously fixed, biologically constrained relation** predicts the direction and reverses a prospectively specified action choice. Such a pattern rejects sufficiency of the snapshot, not the ordinary full-history rival. Merely fitting history-specific constants after seeing C is calibration. To contribute beyond existing history models, the relation must restrict unseen-action predictions in a source-supported way that the unrestricted rival does not obtain for free. This branch did not discover that restriction.

## Exact source contract and overlap

P3 is Molecular Systems Biology2025, DOI10.1038/s44320-025-00150-0. Read original [paper XML](../../2026-10-29-common-function-mechanism-renewal/evidence/p3_transition.xml), particularly Sec3/Fig1, Sec4/Fig2, Sec7/Fig5, Sec12, Sec14–16; original text is distinct from our interpretation.

- Sec14: CTG uses 5,000 cells per96-well, treatment24h after seeding, read24h after treatment, with cell lysis.
- Sec15: density imaging uses 50,000 cells per six-well; fixation/crystal-violet staining; Fiji quantifies occupied area. Fig5B explicitly uses an independent dish at each time point. These are not longitudinal ATP and live-cell count measurements on one well, and their distinct densities/platforms need bridging even for matched-condition means.
- Sec3 already states the substantive drug-holiday decision: regained sensitivity is offset by population growth, and actual density changes the preferred interpretation. Sec4 already models sensitive/tolerant compartments, proliferation, drug memory, asymmetric switching and alternative topologies. Sec7 already demonstrates direction-specific alternating death modes and lower long-term population. None of these are new claims of this branch.
- The [official BioStudies listing](../sources/human_source_index.json) exposes Figure1 density data/image filenames, Figure3 FRET/survival files, Figure4 files and Figure5 density/survival files and sizes. It supplies no response values, culture pairing, live-cell ATP calibration or post-washout founder-colony contract. Absence of a qualifying contract in this inspected listing is not proof no qualifying material exists elsewhere.

P4 original [sarcoma paper XML](../../2026-10-29-common-function-mechanism-renewal/evidence/p4_collateral_sarcoma.xml), Sec6/Fig4, Sec7/Fig7, Sec12, Sec16–19:

- CTG uses2,000 cells per96-well and72h exposure. Temporal CTG reseeds cells sampled after different pretreatment days from T75 cultures maintained at70–90% confluency.
- Long-term growth/sequential treatment uses500 cells per well, serial fixed-cell Hoechst/Celigo counting, drug/media replenishment every72h, stopping each sequence at confluency. That differs from the reseeded short-term CTG history, density and horizon.
- The source already connects a13-day screen to sitravatinib→infigratinib long-term count validation and reports sensitivity appearing byday3. Temporal collateral sensitivity, switching the drug, and independent long-term confirmation belong to the source. Genetic/RTK controls do not supply a missing ATP/count/reproductive-survival pairing.

Thus P3/P4 contain useful inexpensive human functional measurements, but these inspected protocols do not support identifying p, m and their transferable relationship jointly. Comparing their published graph means would confound endpoint biology with timing, density, handling and measurement process.

## Relevant archive conditions retained

- [Assay relation identification](../../2026-10-29-assay-relation-identification/report.md) already distinguishes shared-relation updating from current-object conditioning and gives a paid multigoal indexing construction. Ordinary joint learning can implement it; certification costs remain. This branch does not rename its mapping g.
- [Functional-index pilot](../../2026-10-29-functional-index-pilot/report.md) failed the specified training advantage gate against direct complete continuous target values. That limited result is retained; it neither proves endpoint relations impossible nor licenses a rescue on another endpoint without a new contract.
- [History/state-equivalence round](../../2026-10-28-joint-mechanism-round/report.md) already treats histories with identical present survival but different future functional response and retains controlled-state/PSR rivals. Snapshot failure alone is not new.
- [Control-mean pilot](../../2026-10-29-functional-observation-pilot/report.md) found a relative mean-prediction prerequisite and explicitly did not identify turnover, metabolism or viable reproductive output. No covariance/rate route is reopened here.

## Smallest accessible next check and disposition

The next check should be a narrow **protocol/pairing check before any response values**: locate a source-defined same-culture or experimentally matched sister-well key that joins ATP and live count at the same physical dose/time to a separately qualified washout/reproductive endpoint; verify actual washout, reseeding, density, controls, biological replicate identities and recovery horizon. This can be checked in deposited assay documentation, figure-source sheet headers or author-supplied pairing records if separately authorized. Values are not needed for this first decision. P3's current file listing alone cannot answer it. A positive key would permit a frozen feasibility/test design; an absent or incompatible key parks this dataset; unknown remains unknown.

**Disposition:** do not spend the one remaining scientific test on this branch using the current P3/P4 contract. There is a constructive action-reversal possibility and a useful distinction between live and reproductive survival, but no identified new transferable biological relation, no unowned source-level principle, and no qualified dataset here. Preserve this as a conditional endpoint question. Do not promote an algorithm, claim empirical drug benefit, or infer that all human functional co-learning laws are impossible.
