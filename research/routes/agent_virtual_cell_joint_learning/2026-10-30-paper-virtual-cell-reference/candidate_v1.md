# Candidate I304.v1 — error-source-gated functional reuse

**Status: conditional research candidate; not a validated innovation.**

## Core question

When a virtual cell predicts a drug response but the external functional readout disagrees, can an Agent decide whether the response model is wrong or the proxy-to-function mapping is wrong, obtain the smallest legal observation that separates those explanations, and update only the supported layer before ranking unseen drug/background conditions?

## Proposed mechanism

For condition (x=(cell/background, drug, dose, time)), let (z) be a cheap proxy state (for example a fixed RPPA or L1000/module panel) and (y) an independently measured function. Maintain:

- (M_r: x\rightarrow p(z)), a virtual-cell intervention-response model;
- (M_f: (z, assay context)\rightarrow p(y)), a proxy-to-function map;
- an explicit error state (H_r) (response model misspecification), (H_f) (mapping misspecification), (H_b) (batch/readout shift), and an unresolved (H_{both}) state.

After a disagreement, enumerate only legal candidate observations already available in the assay contract: a matched proxy repeat, one orthogonal functional endpoint, or a predeclared target/genetic reference. For each observation, calculate the predicted outcome under each error state and its cost. Select the observation that most reduces **decision-relevant** equivalence classes per cost. If the observation cannot separate the states, retain the equivalence class and abstain from a layer-specific update. If it does separate them, revise only the supported layer and quarantine the affected drug family/background when appropriate.

The shared learning object is therefore the applicability of a functional proxy and its local response model, rather than an LLM score explanation. A later ranking action is allowed to use the proxy only when the current evidence class supports it.

## Exact closest-prior difference

The target paper's Analyzer–Planner–Auditor loop uses PBMC feedback to revise an external score from an equal-weight mean to a balance-constrained minimum; DrugReflector revises a transcriptomic signature after phenotype feedback. MDA combines probabilistic model checking with value-of-information selection. Ordinary Bayesian model comparison, hierarchical partial pooling and standard VOI can encode much of I304. The unresolved difference is the explicit **layer-localized diagnostic and reuse/quarantine decision**: feedback determines which part of a virtual-cell/function system may be reused and which must be re-fit or measured directly. This difference is a hypothesis, not a novelty finding.

## Necessary conditions

1. The same drug, background, dose and exposure time identify the proxy and independent function rows, with vehicle, preparation and independent-repeat identities.
2. At least two competing error states make different predictions for one legal candidate observation.
3. The functional endpoint is external to the proxy training/readout and has a fixed decision threshold or utility.
4. The candidate observation costs less than measuring the full set of downstream functions, after all controls and repeats.
5. Splits hold out complete drugs, backgrounds or batches; target/genetic references are used only when their identity and timing are qualified.

If any condition fails, the result is an information/identifiability audit, not a mechanism test.

## Strong ordinary rivals

Compare under the same rows, prior information, tuning budget and total assay cost:

1. direct functional measurement for every candidate;
2. ordinary hierarchical Bayesian model with a shared and drug-specific mapping term;
3. standard Bayesian model comparison/VOI without layer-localized quarantine;
4. direct response-to-function prediction with complete refitting;
5. random, fixed-panel and uncertainty/active-learning selection;
6. source-paper mechanistic active-learning baseline when the resource provides one.

## Smallest decisive test

Use a public matrix that passes the data gate. Freeze a proxy panel, an independent functional endpoint, dose/time and repeat units. Leave out whole drugs and one background or preparation. Give every policy the same initial data and a fixed number of functional observations. Measure the main outcome as functional decision utility or fixed-threshold simple regret on held-out conditions. A positive result requires that I304 improves this endpoint over the strongest ordinary partial-pooling/VOI rival and that the selected observations correctly localize at least one predeclared error state. If ordinary hierarchical/VOI or direct measurement matches it, withdraw the algorithmic claim. If the endpoint is not independent or the states remain observationally equivalent, stop without attribution.

## Current data status

The supplied paper is a design reference: OMIX017117 is controlled-access in the dated official snapshot, and exact pairing/dose/repeat fields for the 13-compound T-cell validation are unavailable. Rhaister Emerald Bay provides cheap drug×cell identity support but no inspected independent functional endpoint. The eLife RPPA/phenotype resource offers a retrospective proxy/function entry point, but it is one cell background, has 24-hour RPPA versus 72-hour resazurin, incomplete row-level pairing/scale details and no qualified cross-background transfer. No current resource therefore admits the decisive test. No code or scientific result is promoted.
