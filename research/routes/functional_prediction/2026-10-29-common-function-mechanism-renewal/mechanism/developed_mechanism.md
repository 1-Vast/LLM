# How much hidden selection would be needed to explain a sensitizing pretreatment?

First developed candidate, 2026-10-29. This is a **conditional analytical opening, not an admitted experiment or a recommended new Agent algorithm**. Overall goal remains NOT_ACHIEVED. The concrete object is the minimum hidden lineage amplification needed for an unchanged-susceptibility population to reproduce a measured pretreatment-induced response shift. The current public resources do not yet qualify the bounds required to interpret that object biologically.

The initial reasoning is preserved in `initial_mechanisms.md`, saved before reading parallel source originals. This version incorporates the actual new bacterial and sarcoma papers, but no neutral-scout draft, raw response file or experimental run. No independent challenge of this developed version has occurred; there have been no post-challenge revisions.

## Scientific question, need and usable output

A screening team sees that A pretreatment makes B more effective. That observation can reflect a changed response state, enrichment of a pre-existing B-sensitive subpopulation, residual A, altered inoculum, or a changed assay signal. Predicting the sequence outcome alone does not distinguish those explanations. Conversely, insisting on molecular labels for every subtype would forfeit the ordinary functional-data constraint.

The proposed question is narrower and answerable in a qualified experiment: **could any static mixture of pre-existing susceptibilities explain this shift without exceeding a defensible amount of population amplification?** Its usable output is a required amplification frontier and, only when an independently justified cap is smaller, exclusion of that specified static-selection explanation. It does not identify a target, a memory substrate, a durable therapeutic benefit or an optimal treatment.

The potential practical use is triaging a small set of short, weakly depleting priming conditions for subsequent mechanism work. A large, reproducible change under a small certified selection budget is more informative about a changed response than the same change after many generations of uncontrolled outgrowth. This is a proposed workflow benefit, not a measured saving. The new Pseudomonas paper already establishes a Cpx-associated sensitization mechanism with genetic and uptake evidence; rediscovering that mechanism is not this contribution.

## Inputs and the strongest static-selection null

Let `pi_z` be the distribution of arbitrary stable latent types in a common initial population. There may be any number of types; neither the learner nor the rival is given molecular labels. Fix the physical B challenge, inoculum/density, medium, timing, assay and endpoint.

- `w_z >= 0` is the expected number of viable descendant assay units left by pretreatment A per initial type-z unit, before B starts. It includes the **entire** handling and recovery window. It may reflect both division and death. A separately justified upper bound is `w_z <= U` for every admissible type.
- `b_z in [0,V]` is the type-z outcome per viable challenge-input unit under B, and is unchanged by A under the null. A reproductive-survival probability or one-colony-per-founder endpoint has `V=1` by its observation definition. A bulk CFU or live-count fold after hours of growth does **not** automatically have `V=1`; it needs a qualified upper bound V.
- `m = E_pi[w]` is pretreatment viable-unit fold relative to the common initial population, `q = E_pi[b]` is the unpretreated B outcome, and `r = E_pi[w*b]/m` is the B outcome per viable unit after A. Require `m>0`.

This null permits arbitrary correlation between A survival/growth and B susceptibility. It is stronger than a two-subtype model or a Bliss product. It permits latent subtypes that favor the selection explanation as much as possible. It excludes type conversion, any A-induced change in b, altered density/challenge context and drug carryover; a failure of the null alone cannot identify which of those exclusions failed.

The reference population matters. q must refer to the same initial-type distribution pi used to define m. A later vehicle culture that has itself selected or differentially expanded types is not automatically that distribution. In a matched A-versus-vehicle design, an alternative formulation uses pi as the vehicle challenge distribution and w as the **relative** A/vehicle lineage fold; then U must bound that relative fold, not merely the absolute number of divisions under A. Missing common support or uncontrolled differential growth makes that version unqualified. Matching aggregate vehicle counts does not prove matching hidden composition.

## Operative rule: a sharp frontier with a constructive rival witness

Since `0<=w/U<=1` and `0<=b/V<=1`, every such mixture obeys

`L(U,V) = max(0, V - U*(V-q)/m) <= r <= min(V, U*q/m) = H(U,V)`.

This follows from `w*b >= V*w + U*b - U*V`, `w*b >=0`, `w*b <= V*w` and `w*b <= U*b`, then averaging. It is standard bounded-moment/Fréchet reasoning. No new probability theorem, inference engine or general experiment-design algorithm is claimed.

For `0<q<V` and `0<=r<=V`, invert both inequalities:

`U_required(V) = m * max(r/q, (V-r)/(V-q))`.

This is the **smallest possible maximal pretreatment amplification** that can explain m,q,r under an arbitrary static mixture. It is not an estimate of actual amplification. The formula is sharp: construct two immutable types, one with `b=V` and fraction `q/V`, the other with `b=0` and fraction `1-q/V`. Assign

`w_(b=V) = m*r/q`, and `w_(b=0) = m*(V-r)/(V-q)`.

These nonnegative weights exactly reproduce m,q,r and attain the stated maximum. This explicit selection-only witness is the strongest simple rival explanation whenever the permitted U is at least the frontier. A two-variable construction or tiny linear program implements the same result, with no Agent.

At q=0 or q=V, the exact bounded null requires respectively r=0 or r=V. Real uncertainty near these boundaries must be propagated; finite precision cannot be treated as proof that a pre-existing response type has zero mass.

For sensitization (`r<q`), `U_required = m*(V-r)/(V-q)`. If V is unbounded, this requirement approaches m as V grows: an arbitrarily rare, rapidly expanding challenge type can explain the shift. Thus a cap on **pretreatment amplification alone is insufficient for an unbounded bulk-growth endpoint**. This second boundary prevents substituting six-hour CFU fold or normalized OD into the survival formula.

## Constructive region and an exact failure case

The following numbers are a mathematical thought experiment, chosen without raw outcome access. They are not empirical results, simulations or fitted values.

Use a founder-survival endpoint (`V=1`), `m=0.95`, B-alone survival `q=0.80`, and post-A B survival `r=0.20`. Then

`U_required = 0.95 * 0.80 / 0.20 = 3.8`.

If a separately qualified short preparation allows at most one binary division of any founder during the entire window, `U<=2`; selection alone predicts `r >= 1 - 2*0.20/0.95 = 11/19`, about 0.579. The observed thought-value 0.20 would exclude that null. The enabling condition is the externally supported lineage expansion cap, together with a bounded challenge outcome and matching reference preparation. Net count retention of 95% is not that condition.

If the window permits `U=4`, the same observations are exactly compatible with static selection: the initially 20% B-sensitive type expands by 3.8; the initially 80% B-resistant type retains 0.2375 descendants per founder. Their average fold is 0.95 and their subsequent average B survival is 0.20. Large hidden birth and death flows can therefore make an almost unchanged population look newly sensitive. No amount of additional precise measurement of only these three means distinguishes that constructed rival from induction.

A preparation lasting less than a **qualified minimum interdivision time**, including processing and recovery, can in principle impose U<=2 even if some founders were already about to divide. The word “short” or a population-average doubling time does not establish that cap. If two generations per lineage remain possible, the illustrative exclusion disappears. These are conditional deductions, not claims about the actual Pseudomonas protocol.

## Consequence for a functional learning loop

The virtual-cell object would be a feasible set of unchanged-susceptibility mixtures plus response-changing alternatives, constrained by measured counts and externally qualified U,V. The shared learned item is the functional response law and its remaining selection-compatible envelope, not a molecular subtype annotation.

A proposed Agent can choose a short A pulse and a B challenge where the reference outcome q is close enough to V for selection to have limited leverage, while an independently motivated priming effect could still change r. Feedback updates m,q,r and removes the static-selection explanations only when the entire valid uncertainty region violates their bound. It can then choose a discriminating wash/recovery/independent-endpoint follow-up; it must not label the remaining explanation “Cpx” or “induction” from the inequality alone.

This changes which experiments are scientifically informative: measuring the strongest killing condition is not necessarily informative about induction, because q near zero leaves broad scope for selection. However, a high-q challenge gives no benefit if the priming effect there is too small to measure. No guaranteed sample saving follows.

The exact same operative rule is available to a fixed short-pulse panel plus a bound calculator, an ordinary robust mixture model, or a standard sequential design policy. They are mandatory same-information, same-cost rivals. A new architecture or agent-specific advantage is not claimed. A substantive contribution would require showing that this measurement principle enables a useful explanation exclusion or transfer task with ordinary inputs in a regime where existing practice cannot do so at comparable cost. That empirical and closest-prior case is presently missing.

## Actual new source evidence and what it admits

**Upterworth et al., Nature Communications 2026, DOI `10.1038/s41467-026-71178-5`.** Original local JATS: `../evidence/p5_negative_hysteresis.xml`. Actual reading is selected primary-text reading (P), not the full article/SI. Sec3, Sec6–8 and Sec13–16 were read completely as selected sections; Sec4 was received as part of a longer initial extraction, and no complete-parent-section reading is claimed because that extraction was truncated.

- Sec3/13: actual CAR→GEN switching, early exponential cultures, pretreatment up to 30 min, removal/resuspension, CFU at 0/2/4/6 hours of main treatment. One-minute CAR exposure at 4 MIC reportedly suffices; effects wane after approximately 45–80 min of drug-free growth. This changes the old absence of joint interventions, but does not certify a maximum lineage fold or V=1 for subsequent CFU.
- Sec14: two 5 mL PBS washes, 10 min centrifugation at 4000g and 4°C, biological replicate wording, and explicit failure to remove covalently bound CAR. This addresses free-drug carryover for the tested condition; it does not prove all memory is drug-free or all hidden types share the same B response.
- Sec15 and Sec3: chloramphenicol suppression of active growth prevents the sensitization. Therefore no-growth U=1 is especially inappropriate as an unqualified assumption here. Full handling time matters; a “one-minute drug pulse” is not automatically a one-minute selection window.
- Sec16: the broad screen is OD every 15 min for 12 h, with two pretreatment MIC fractions and four main-treatment fractions. Its analysis chooses a non-growth-inhibitory pretreatment and a main concentration based on observed growth. This is the authors' analysis; a new experiment must freeze its own selection/validation rule before new outcome access. OD is not the bound's viable-founder endpoint. The paper's monotonic CFU/OD association does not establish an absolute response cap or a conversion for each condition.
- Sec6/7: actual Cpx deletions/overexpression and gain-of-function mutants, membrane probes, and GEN ELISA provide mechanism evidence in specified PA14 experiments. Those are already this paper's scientific discovery. A count-only bound would at most screen conditions where such explanatory work is justified; it cannot take credit for the Cpx mechanism or generalize the controls across all strains/drugs.
- Sec8: static MIC can differ little while tolerance/hysteresis changes, and the authors discuss growth-related dilution, residual covalent binding, alternative memory forms and resistant-strain exceptions. Generic primability or sequence-aware learning is not a novel contribution against this source.

**Exploiting collateral sensitivity in the evolution of resistance to tyrosine kinase inhibitors in soft tissue sarcomas, Communications Biology 2025, DOI `10.1038/s42003-025-08652-1`.** Original local JATS: `../evidence/p4_collateral_sarcoma.xml`; P-level selected reading of Sec3/4/6/12/16–19.

- Sec6/16: a real 58-inhibitor panel after four mTKI pretreatments; temporal conditions, colony experiments and genetic FGFR1 perturbations appear in the source. This is substantive prior work on exploiting acquired/temporal collateral sensitivity, not a missing concept to rename.
- Sec12/16/18: the screening endpoint is 72-hour CellTiter-Glo; pretreatment lasts days, with culture maintenance and reseeding. It does not supply V=1 or a tight absolute lineage amplification cap. Fig4 text uses 0.5 micromolar pretreatment whereas Sec16 says 1 micromolar; that source-level condition must be resolved before a matched numerical contract. No raw values were read to resolve it.
- Sec17 gives direct-cell-count growth assays but ends a sequence when confluency is reached; this alone is not a universal cap on every hidden lineage. Source-level replicate statements are not automatically independent identities for each exported row.

**HTS001 and the immediately preceding local pilot.** `../../2026-10-29-functional-observation-pilot/report.md` was read as an internal report, not new source-data access. Its control mean comparison does not estimate births/deaths, certify constant rates or identify maximal lineage fold. The HTS001 metadata has no switching contract and no verified experiment identity. Neither its drug counts nor its controls should be opened for this candidate.

## Closest rivals and present novelty limit

| Rival or prior | Same inputs and operative rule | What remains different, if anything |
|---|---|---|
| Arbitrary static mixture with bounded weights | Optimize E[w*b] with fixed m,q and bounds U,V; exact two-type construction above | It is the main scientific rival, and supplies the same frontier. The proposal is a way to test its limits, not a better optimizer. |
| Classical Fréchet/bounded-contamination or selection sensitivity analysis | Bound joint moments from marginals and support, or invert the bound | The mathematics is inherited. Exact prior use for the proposed short-pulse pharmacology workflow remains unverified. |
| Fixed low-dose/short-pulse grid plus direct challenge and bound calculation | Purchase the same m,q,r and controls, apply the same inequality | Implements the claimed discrimination. There is no established Agent advantage. |
| The 2026 Cpx negative-hysteresis study | Real switching, wash/recovery tests, genetic intervention and independent uptake measurement | Already provides stronger mechanism evidence for its tested system. The present lead could only be a cheaper qualified triage principle elsewhere; that capability is not demonstrated. |
| Earlier MAESTRO joint-susceptibility graph and history/PSR packets | Learn cross-drug susceptibility alignment or predict future functional outcomes | Those objects differ from a resource-limited exclusion of selection. No graph/factor/PSR novelty is implied by this distinction. |

The coordinator reports one broad EuropePMC prior query in `../root_sources/selection_prior_query.json` (discovery only; poorly focused first results). This developer did not independently read its response and makes no absence-of-prior claim from it. A primary closest-prior check remains required before recommending this as a new scientific contribution. Source access failures are not evidence that a needed dataset or method does not exist.

## Exact next evidence: admit, kill, or leave unresolved

The next step should be a **protocol/source qualification**, not a count-value pilot or another learner. It can use ordinary functional information; no omics is intrinsically necessary.

1. Qualify a bounded challenge readout. A one-colony-per-founder reproductive-survival endpoint supplies V=1 by design if founder isolation/colony counting and interference limits are verified. The inspected papers' bulk CFU and CTG endpoints do not automatically supply it. Alternatively provide a valid V for the actual fixed challenge and all admissible hidden types. An average control fold or monotonic OD–CFU relationship is insufficient.
2. Qualify the whole pretreatment/processing lineage cap U and the reference distribution. A defensible minimum interdivision time plus a fully documented short preparation can bound the number of binary divisions without molecular labels. Ordinary total-count trajectories alone cannot do this in the presence of compensating births and deaths. A trusted direct division study or another explicit independent bound may be needed; that is extra evidence, not something the current bulk screen supplies. Do not use growth arrest as a free control if it abolishes the priming phenomenon.
3. Require the common initial/reference population, absolute viable counts before and after pretreatment, known dilution/reseeding factors, identical B challenge conditions, wash/vehicle controls, and independent preparation identities. Current source descriptions provide some of these pieces but do not close their joint contract. Source-data acquisition must remain separately budgeted and must not consume outcomes until the protocol is frozen and reviewed.
4. Before any test, freeze the one endpoint, candidate pulse/challenge, U/V evidence, independent-unit analysis, uncertainty procedure, practical discrepancy margin and stop rule. A conservative decision excludes selection only if **every** m,q,r compatible with the prespecified uncertainty region has `U_required(V)>U_allowed` (including uncertainty in U,V/reference handling). Do not tune the bound, pulse length, dose, readout or margin after looking at the answer. Merely increasing technical wells cannot fix a missing cap or an unidentified endpoint.

**Admit to a narrow empirical test:** an inspected ordinary functional protocol actually supplies finite, informative U and V, a valid reference and independent units, and the preregistered feasible response region includes a practically detectable separation. One does not need to know the result beforehand. The conceptual prediction is that qualified short, weakly depleting pretreatment can sometimes produce a subsequent response outside every static-selection mixture; the matched static-selection rival predicts it cannot.

**Kill this version as the current main candidate:** the closest original prior already delivers the same useful pharmacological exclusion/transfer capability, or U/V can only be justified by assuming the desired mechanism, or the only available resource has an effectively unbounded growth endpoint/selection window. A valid response inside the envelope kills the exclusion claim for that condition, not the possibility of biological induction. A broad interval crossing the envelope is inconclusive. If violating conditions also change inoculum, carryover or readout, they do not establish induced susceptibility.

**Current decision:** keep the frontier as a concise, falsifiable analytical lead and an explicit reason not to spend the remaining scientific-test budget on the present OD/CFU/CTG resources for this claim. The new source does change sequential-intervention availability and biological plausibility, but it does not yet admit this bound. There is no observed effect, novelty verdict, measured cost saving, validated cross-background transfer or completed Agent–virtual-cell contribution.

## Accounting and exact reading limits

This worker performed local document searches/reads, JATS text extraction, reasoning and two Markdown writes only. Network/HTTP/API requests 0; raw outcome access 0; scientific tests/simulations 0; author-code execution 0; installations 0; subagents 0; shared-index, library or core-code edits 0. Published numerical statements were read as scholarly evidence; no public raw data workbook or count table was opened. No scout initial draft was read. Native effective model, tokens and paid cost are unknown.

The initial archive locators and reading levels remain in `initial_mechanisms.md`. New primary reading is limited to the section IDs listed above; original-source statements are separated from the proposed derivation. No external paper is claimed fully read, and the source's molecular evidence is not claimed reproduced. The mechanism is now concrete enough for a fresh independent challenge on its algebra, null/reference assumptions, practical input contract and closest-prior difference.
