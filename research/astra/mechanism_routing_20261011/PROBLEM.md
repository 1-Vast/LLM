# Block N: where does an LLM add value to a virtual cell? Predicting which cancer lines a drug kills

Started 2026-10-11 under the requirements added that day:
* use the LLM for work that needs knowledge integration and reasoning;
* use few, cheap, local datasets;
* demonstrate every contribution by ablation against strong non-LLM methods.

This file states the question and the design intent. The development trail that led here is in
`feasibility/README.md`. The registered protocol and freeze come later (`PROTOCOL.md`,
`FREEZE.json`). No confirmation value has been read: confirmation PRISM profiles sit in a sealed
tier (`TIERS_RECEIPT.json`).

## 1. Scientific question

A compound's pattern of *which* cancer lines it kills is the starting point for biomarker
discovery, indication finding and repurposing. Measuring it takes a pooled screen over hundreds of
lines. The question is whether the dual core can predict that pattern, before or after a partial
screen:

* **Virtual cell.** Predict the selective killing pattern from the compound's transcriptional
  response in nine lines (L1000), by transfer from screened reference drugs with similar responses.
* **Agent, three roles that need knowledge rather than arithmetic:**
  1. *Forecaster*: from literature, name the screened mechanisms whose killing pattern the
     compound should share, including off-target and physicochemical modes, and the genomic
     features expected to change sensitivity.
  2. *Critic*: judge which of the virtual cell's transcriptional neighbours share the compound's
     cytotoxic mechanism and which only look alike.
  3. *Explainer*: after seeing the most and least affected lines of a partial screen, propose the
     genomic features that explain the pattern and predict unseen lines.
* **Capability.** Do reasoning mode or model size change any of these answers?

## 2. Why this task

* **The LLM's knowledge matters only here.** Mechanism of cytotoxicity, polypharmacology,
  biomarker biology and cell-line genetics have to be integrated. Curated targets (Repurposing
  Hub) and chemical similarity are the strong non-LLM knowledge baselines.
* **Few, cheap data.** Every input is local and public:
  * GSE92742 L1000 (already extracted by block M);
  * PRISM Repurposing 19Q4, primary and secondary screens;
  * CCLE 19Q4 expression and mutations.

  The secondary screen is an independent re-screen of the same compounds (different plates and
  run), used for the ceiling and for validation.
* **Earlier negative evidence is respected.** Block M and this block's feasibility probes found
  that agent claims written before data (lines, times, genes) carry little information. Asking the
  agent to forecast numbers is a weak use of it. The critic and explainer roles test reasoning
  over evidence instead.

## 3. Units, endpoint, splits

* **Units.** 1,403 drugs with a block M L1000 profile and a PRISM primary profile, split within
  mechanism class (seed 20261011): 701 reference, 281 development, 421 confirmation.
  Confirmation drugs' PRISM values are sealed.
* **Endpoint.** Selective r: the Pearson r over 578 lines between predicted and observed log fold
  change at 2.5 uM. Both are first residualised against the generic killing profile, so
  "kills everything" is not credited.
* **Population.** Drugs killing at least 5% of lines (log fold change < -1). The other drugs have
  no selective pattern to predict.
* **Regimes.**
  * *Known class*: the drug's class has screened reference members.
  * *Novel class*: same-class members are removed from every pool and from the agent's
    vocabulary. This regime is the one where knowledge should matter most.
* **Line split for the explainer.** Lines with complete CCLE features are halved (seed 20261011).
  The agent sees at most the top and bottom 20 of 40-160 discovery lines. Scoring uses the 281
  test lines it never saw.

## 4. Controls and baselines

* Generic profile.
* Annotated class mean (known class only).
* Target kNN (Hub Jaccard).
* Chemical kNN (Morgan).
* Non-LLM ensemble.
* Target-expression rule.
* Unrestricted statistical mining (top-1, top-5, ridge).
* Target-restricted and random-restricted mining.

Agent ablations: no literature, name masked, no virtual-cell evidence, no discovery data (prior
only), and model profile (flash without thinking, flash with thinking, pro).

## 5. Cost accounting

* **Lab units.** None purchased. The analogy is a PRISM screen (one compound x ~578 lines) against
  nine L1000 profiles.
* **Provider spend.** Recorded per call in `tmp/mechanism_routing_spend.json` against a $10
  ceiling. Pro calls are booked at the provider's published rate for the hour they finish.
