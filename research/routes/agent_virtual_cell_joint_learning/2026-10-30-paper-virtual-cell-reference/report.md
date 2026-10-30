# How to use the immune-rejuvenation virtual-cell paper in cheap drug discovery

**Episode status: conditional lead only; no validated new mechanism, Agent advantage or code promotion.**

The user-supplied paper is *Virtual-cell verification enables self-auditing AI discovery for immune rejuvenation* (You et al., bioRxiv v1, posted 2026-08-11, DOI `10.64898/2026.08.04.742916`). The local audit reads selected indexed original-text passages, the official metadata records and the dated OMIX access page. It is a preprint; a complete authenticated paper, supplement, code, weights, prompts, logs and raw condition-level matrix were not verified. The paper is therefore a strong design reference, not a ready public reproduction dataset.

## What is useful to borrow

The paper has three separable operations.

1. **A directional phenotype contract.** PACE keeps cell-type-resolved axes and their directions instead of collapsing immune aging to one opaque score. This is useful when a drug can improve one biological axis while worsening another: every axis should remain visible, and the aggregate rule should be fixed before functional validation.
2. **A compact response representation.** CellQ compresses each single-cell transcriptome to eight discrete residual-vector-quantized tokens aligned with a language-model vocabulary. The transferable idea is a compact, auditable state representation that predicts module-level perturbation responses. The token count, an LLM, or the reported benchmark score is not itself a drug-discovery contribution.
3. **An externally anchored update loop.** The Analyzer–Planner–Auditor reads a response matrix, proposes a change to the ranking objective, checks it against an external assay, and applies it to the next ranking round. In the selected text, an equal-weight mean of aged-down and aged-up restoration was changed to a balance-constrained minimum after a 110-compound PBMC screen; a separate 13-compound T-cell assay used flow phenotypes, senescence staining and matched-supernatant cytokine ELISAs.

The important transfer is the separation between an internal proxy and an external function. A model score is not allowed to certify itself. The scoring rule, triggering observations, external endpoint, accepted revision and failed alternatives should be versioned in a ledger.

## What the paper already covers

The broad claim “an Agent uses functional feedback to revise a virtual-cell or drug-ranking objective” is occupied. DrugReflector (Science 2025) uses paired transcriptomic and phenotypic measurements to revise a screening signature and reports a later phenotypic hit-rate result. MDA (2026 preprint) combines candidate model structures, predictive failure, posterior updating and value-of-information experiment choice. BATCHIE (Nature Communications 2025) is a biological Bayesian adaptive-selection comparator for combination screens. A new role name, a mean-to-min change, or a CellQ-style tokenizer cannot be presented as the main innovation here.

The 2026 preprint also does not establish equal-budget hit-rate gain from the 110-compound screen. The selected evidence supports a reported score–readout association and an independent assay, while exact drug lists, doses, donor/well pairing, raw values and replication structure remain unverified. The local official OMIX017117 snapshot records controlled access and says the data were not currently downloadable; this status can change, but it blocks a current reproduction claim.

## The remaining conditional research lead

The frozen candidate I304 asks whether a disagreement can be assigned to the right layer:

- (M_r): the intervention-to-proxy response model is wrong;
- (M_f): the proxy-to-function map is wrong;
- (M_b): batch/readout or time-shift error is responsible;
- (M_{both}): the observations do not identify a single layer.

When a virtual cell predicts a function (y) from a cheap proxy state (z) and an external assay disagrees, the Agent would enumerate only legal candidate observations: a matched proxy repeat, one orthogonal function endpoint, or a qualified target/genetic reference. It would choose the observation that separates decision-relevant error states per cost, update only the layer supported by the result, and quarantine a drug family/background when the evidence is local. If the states remain observationally equivalent, it would keep the equivalence class and abstain.

This is a conditional **identifiability and reuse policy**, not an accepted new algorithm. A standard model can encode the same behavior as

```text
p(y,z | x, state) = p(z | x, response_model)
                     p(y | z, mapping, batch)
```

with a latent source indicator, shared and drug-specific effects, posterior predictive checks, partial pooling and cost-aware VOI. The independent challenge therefore parked the algorithmic novelty and assay-saving claims. A contribution would require a formal separation rule and a held-out decision benefit over this ordinary model under equal information and cost.

The cross-field audit supports the structure but not novelty. DeepXplore supplies model-disagreement tests, CheckList supplies explicit behavioral/invariance tests, robotics fault diagnosis supplies residual signatures for competing fault sources, and GIES supplies the idea that interventions can break equivalence classes. None of these sources establishes a virtual-cell drug-screening algorithm with minimum-cost error-source identification.

## Data gate before any experiment

The candidate needs a row-level condition contract. Every proxy and function row must carry drug, cell/background, dose, exposure time, vehicle, preparation or plate, independent replicate, readout identity, and QC. A target or genetic reference is needed if the claim uses mechanistic equivalence. Technical wells cannot be counted as biological replicates. Whole drugs, backgrounds or batches must be held out.

The current resources do not pass this gate:

- **OMIX017117:** the paper's 110-compound PBMC perturbation data are controlled in the dated official snapshot; exact pairing and raw values are unavailable.
- **Emerald Bay/Rhaister:** cheap drug×cell identity support is verified, but the inspected summary has no independent functional endpoint or preparation key; it is a relative-response and ordinary-prediction resource.
- **eLife RPPA/phenotype:** one SkMel-133 background, 12 drugs and 89 nominal conditions, 24-hour RPPA and 72-hour resazurin. Source text reports three biological RPPA replicates and triplicate cell-cycle assays, but the row-level pairing, scale and cross-background transfer are incomplete. Four shared downstream readouts are a retrospective clue, not proof of chemical equivalence.
- **LINCS/L1000 joined to PRISM/GDSC:** nominal drug/cell joins are not automatically matched dose, time, preparation or endpoint observations.

Consequently, the current round stops at an information audit. The previous CXCL9 minimum experiment remains a useful negative boundary: the global shared-gain rule was worse than the constant-interaction comparator in three of four preparation records, and 11 of 20 prediction envelopes missed the observed technical-well ranges. That result rules out silently reusing a global gain; it does not validate I304 or the narrower exception-aware branch.

## Decisive test when a qualified matrix appears

Freeze the proxy, external function endpoint, exposure contract, threshold or ranking utility, repeat unit and total budget before unsealing the target outcomes. Allocate development, calibration and test by independent preparation/background and whole drug. Give all policies the same anchors and two or another predeclared number of expensive function slots.

Compare direct function measurement, complete refitting, hierarchical latent-source/partial-pooling, ordinary Bayesian model comparison plus VOI, random/fixed panels, uncertainty active learning and the source-paper baseline. The main endpoint is held-out functional decision utility or fixed-threshold simple regret; secondary endpoints are calibrated source localization, correct quarantine and abstention rate. Report the fraction of failures that remain unidentifiable.

Stop the line if the ordinary model matches I304, if direct measurement is cheaper at the same decision loss, if source states cannot be separated, or if the observed gain is only a proxy loss reduction without a changed drug decision. Do not convert a PASS from a file, test, or auxiliary Agent into biological validity.

## Current scientific judgment

Use the paper as a template for directional phenotype contracts, compact state representations and externally audited objective updates. Do not copy its architecture or claim that a self-auditing role stack is new. The most defensible new question is whether an Agent can learn **where a functional proxy is safe to reuse and where it must abstain**, under a qualified cheap matrix and a strict ordinary-model challenge. That question is currently unresolved because the needed paired public resource is missing. No core implementation is authorized by the evidence in this episode.

Evidence and challenge records: [brief](brief.md), [paper evidence audit](evidence_audit.md), [cross-domain map](cross_domain_map.md), [data gate](data_gate.md), [candidate](candidate_v1.md), [independent challenge](challenge_initial.md), [decision](decision.md), and the Astra MAX alternative [astra_mechanism.md](astra_mechanism.md).
