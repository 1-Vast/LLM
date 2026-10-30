# Candidate v1: a selection-only amplification frontier

Frozen question, 2026-10-29. This packet states a conditional proposal for independent assessment. It contains no empirical result or scientific verdict. No raw response workbook has been accessed for this candidate.

Can inexpensive functional drug-switch experiments distinguish a change in response from selection of pre-existing response types, and can that distinction usefully guide subsequent measurements? The proposed usable output is the minimum hidden lineage amplification needed to explain a measured sensitization under an unchanged-response mixture. A proposed learning loop would retain feasible explanations and choose informative pulse/challenge conditions. The practical use sought is cheaper triage of priming conditions for mechanism follow-up.

## Mathematical claim and observation contract

Let pi be the stable-type distribution in a common reference population. An arbitrary latent type z has pretreatment descendant weight w_z in [0,U] and unchanged subsequent challenge output b_z in [0,V]. Define m=E[w]>0, q=E[b], and r=E[w*b]/m. The complete handling/recovery window is part of w. All challenge contexts, density, medium, readout and timing must match. U and V must be independently qualified over all admissible types, not fitted to explain the result. The null allows arbitrary correlation of w and b; it excludes conversion, carryover and context-dependent response changes.

The proposed sharp feasible region is

`max(0, V-U*(V-q)/m) <= r <= min(V, U*q/m)`.

For 0<q<V and 0<=r<=V, its inverse is

`U_required(V) = m*max(r/q, (V-r)/(V-q))`.

A proposed attaining construction has mass q/V at b=V with w=m*r/q and mass 1-q/V at b=0 with w=m*(V-r)/(V-q). At q=0 or V, bounded nonnegative b respectively forces r=0 or V. Assess the formula, necessary conditions and edge cases independently.

Illustration only: m=.95, q=.8, r=.2, V=1 would require U>=3.8. A qualified U<=2 would exclude this static-mixture model; U=4 would admit it. These numbers are not data, a simulation or an executed test.

For a matched vehicle reference, pi may instead be the vehicle challenge distribution and w the relative A/vehicle lineage weight; U must then bound that relative weight on common support. Aggregate vehicle-count matching alone is not a composition guarantee. For sensitization, the proposed U_required tends to m as V tends to infinity. Bulk CFU after proliferation, CTG and OD do not supply V=1 by their names. A founder-isolated reproductive-survival endpoint might supply V=1 only under a qualified observation protocol. A short pulse or average doubling time does not itself establish U.

## Proposed learning role and simple comparators

Retain the set of static-mixture explanations consistent with m,q,r,U,V and uncertainty. Prefer short/weakly depleting pulses and challenge outcomes q near V only where an effect remains measurable. Eliminate static selection only if every admissible point in the frozen joint uncertainty region is outside its feasible region. The surviving alternatives still include carryover, handling/density changes and altered readout; exclusion alone does not identify induction or a molecular mechanism.

Compare an Agent implementation to a fixed pulse grid plus this bound calculator, a direct two-type construction, and ordinary robust sequential design using the same data and assay cost. No Agent-specific superiority or new probability theorem is assumed. Assess whether a substantive co-learning contribution or practical capability remains beyond those comparators, and what evidence would establish it.

## Original-source inputs, not investigator verdicts

Read only original passages relevant to the judgment; do not read the developer's other notes, coordinator report or prior agent discussion before recording the initial assessment.

- `../evidence/p5_negative_hysteresis.xml`: DOI 10.1038/s41467-026-71178-5, Nature Communications 2026. Relevant original sections Sec3-8 and Sec13-16; availability includes MOESM18 Source Data, not acquired. Actual drug switching, recovery, CFU/OD, genetic and uptake controls.
- `../evidence/p6_hysteresis_prior.xml`: DOI 10.1073/pnas.1810004115, PNAS 2018. Relevant original sections s2 first two paragraphs, s9, s15 and s16. Short priming, CFU and population-model prior.
- `../evidence/p4_collateral_sarcoma.xml`: DOI 10.1038/s42003-025-08652-1. Relevant original Sec6, Sec12 and Sec16-19; temporal collateral response and CTG/direct-count protocol.

Review mathematical sharpness, scientific identifiability, common-reference validity, whether current ordinary functional resources supply informative U/V, closest-prior overlap, practical value and the exact minimal discriminating check. Distinguish proved deduction, source-reported finding, unexecuted test, data unavailability and novelty uncertainty. No outcome or positive verdict is required.
