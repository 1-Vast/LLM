# FSD-01 v1: timed re-observation and future drug response

2026-10-31. A conditional scientific hypothesis, not a numerical protocol or a new architecture. Parent: study52's common probe-specific prechallenge response restriction. This version changes the declared observation calendar and decision deadline; it does not reopen the parent without new biological support. No empirical benefit, novelty, information-sufficiency certificate or drug-selection advantage is claimed.

## Important question and core claim

For controlled cancer-treatment histories and one specified subsequent drug, can an affordable second cellular observation obtained before the actual challenge make future functional response predictable across histories without history-specific response calibration? A transiently uninformative early snapshot could become informative later, before the decision. The capability sought is a tested biological response restriction at a usable deadline, rather than reconstruction of all cellular states.

LetHbe a documented treatment/recovery history,S0an earlier cellular observation,Sda second observation obtained at deadline d,Athe specified next drug/schedule andYits later functional endpoint at a fixed horizon. The hypothesis is a common conditional mean

`E[Y | H,S0,Sd,A] = m_A(S0,Sd,d)`

over a declared population, history/observation support and endpoint definition. A distributional equality is a stronger, separately testable claim and is not implied. The observation input includes every permitted covariate; measurement time, dose, handling and reseeding cannot be hidden. If only one next challenge is covered, this is a response task, not treatment choice. A fixed intervention plus an adaptive schedule with later observations are different targets.

## Necessary mechanism and useful contrast

The operative principle is re-observation before a decision: additional measured information can reveal a functional distinction that an earlier snapshot misses. Fit the same simple conditional response family withS0,with(S0,Sd),and with(H,S0,Sd),using equally available training labels and fixed calendars. The common map excludesHfrom deployment; the richer-history rival tests that restriction. An invariance penalty or a neural encoder is optional and has no established necessity. This is ordinary conditional predictive sufficiency/state abstraction; no new mathematical operation is asserted.

Constructive thought case, not a simulation: two histories have the same early markerS0but cause different later challenge responses. Before the challenge, a later markerSdaccurately distinguishes the response classes in both histories. A common map fromSdis then possible without retaining the history label. Boundary case: ifSdbecomes informative only after the challenge, it is leakage; if the two histories remain observationally identical but have different responses, the common restriction fails; if they have no shared support, the comparison is inconclusive. A fitted model failing does not prove information is absent from its inputs.

## Evidence and closest priors

- P1, Daglish2026 DOI10.1038/s41419-026-09061-w: original withdrawal, recovery, mitochondrial assays and concurrent venetoclax findings motivate distinct recovery/next-challenge endpoints. Source Methods and Fig5/6 do not by themselves provide the joined two-observation/deferred-challenge table.
- P2, Wang2025 DOI10.1371/journal.pcbi.1012815: existing coupled epigenetic/population and holiday optimization prior. Its separate data-source roles are not a new joined response matrix.
- P3, existing BESTDR DOI10.1158/0008-5472.CAN-25-1181: phase/branching/kinetic ordinary alternative.
- P4, existing BCL11B2026 DOI10.1126/sciadv.aec5436: actual pretreatment sorting and subsequent challenge are already source-owned. Fig5Cstate uses6dayTNF; Fig5Echallenge begins after2daysTNF. Public GEO identity metadata authenticates14bulk samples but not a2dayTNFstate/functional join.
- P5/P6, original arXiv2610.27446v1 and2609.25757v1: support declaring complete information, observation calendars and decision deadlines. Their finite decision-interface/imitation objectives are not transferred into drug-response learning. These general principles were already partly in the initial scout note; the donors refine the proposed test rather than invent it.
- Study52's Peyre/PSM and Roux/shared-threshold findings, and the older Lee2012 sequential-rewiring DOI10.1016/j.cell.2012.03.031, remain close target priors. The exact two-observation/held-history difference needs target prior checking; no universal novelty finding follows.

## Practical use and strongest rivals

Proposed user: a cancer pharmacology team deciding whether a fixed next challenge is worth measuring after a controlled pretreatment. Usable output would be its functional response at an explicitly available deadline, with uncertainty. Current alternatives are treatment-label regression, initial viable abundance/recovery, simple phase/compartment or survival models, and a richer history-aware predictor. Laboratory cost must include the second observation and any sibling wells, not treat them as free. No assay saving, therapeutic benefit, exceptional VirtualCell gain or Agent benefit has been observed.

## Planned decisive test and failure conditions

First authenticate exact history/dose/washout, prospectiveS0/Sdtime, challenge/horizon, preparation/sample identities, assay encoding, denominator and later endpoint. Destructive measurements may use exchangeable sibling cultures if the population estimand and preparation design support it; same-cell trajectories are not universally required. Do not merge endpoints across unrelated cultures or fit latent states using future responses.

Then predeclare the finite biological frame, held histories and independently prepared repeats, exposure status, measurement cost, common support, response family/likelihood, strongest equal-information rivals, effect precision and useful-error criteria. A new hidden test is needed because published effects are already exposed. Improvement from the second observation on held preparations plus no practically consequential residual history dependence would support only the declared response restriction, not full cellular state sufficiency. Reproducible residual history dependence would defeat the chosen measured-state law. Lack of overlap/precision or uncertain joins is inconclusive. Treatment rankings require additional intervention coverage and are outside a one-challenge test.

Current unresolved prerequisites: no inspected source authenticates the required joint observation/calendar/functional-response frame with held-history preparation support; new public P1 proteomics alone cannot fill it. No data matrix, code, numerical thresholds or execution freeze is defined. The next informative action is to resolve such a source contract or retain this as an untested hypothesis. At most two substantive revisions are allowed; this isv1,zero used.
