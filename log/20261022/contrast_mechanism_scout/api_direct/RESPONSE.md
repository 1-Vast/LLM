## Two candidate operations (at most two; one is a strong lead, one is conditional)

I keep both because they are materially different operations, not renaming. Candidate A is the stronger lead. Candidate B is only worth pursuing if A’s source qualification fails; otherwise it collapses into a standard context-conditioned model and should be dropped.

---

# Candidate A: **Interventional support–response consistency gate with a virtual-cell counterfactual nuisance direction**

## A1. Concrete drug-discovery decision and functional endpoint

**Decision:** for a given cell line/context \(c\) and candidate perturbation \(d\) (or combination \(d_1+d_2\)), decide whether the virtual-cell model’s predicted functional response is *intervention-supported* enough to advance to a higher-cost functional assay, versus defer/reject.

**Functional endpoint:** the measured functional readout after perturbation in that cell line — e.g. viability, apoptosis, or a specified pathway reporter — at a fixed dose/time regime. The operation is not trained to improve RNA prediction loss; it produces a triage label:

\[
\text{advance}(c,d)=1 \iff \big(\hat y_{\text{func}}(c,d)\ \text{favours the program}\big)\ \wedge\ \big(\text{support gate}=1\big)
\]

where the gate is computed from intervention overlap in the virtual-cell model, not from prediction confidence alone.

**Why this is a useful decision:** the agent must choose which predicted interventions are worth functional testing. A model can predict expression well and still have no defensible functional extrapolation for an unseen drug/context pair. The gate explicitly asks whether the predicted functional effect is anchored by observed interventions of the same type in comparable contexts.

## A2. Exact minimal update/inference equation (1–3 operations)

Let the virtual-cell model produce, for context \(c\) and perturbation \(d\), a predicted functional scalar \(\hat y(c,d)\) and an embedding \(z(c,d)\). Define a **support kernel** over observed intervention units \(\{(c_i,d_i,y_i)\}_{i\in S}\):

\[
w_i(c,d)=\exp\!\left(-\frac{\|z(c,d)-z(c_i,d_i)\|^2}{2h^2}\right)
\cdot \mathbf 1\!\left[\text{perturbation class}(d_i)=\text{perturbation class}(d)\right].
\]

Normalize \( \tilde w_i = w_i/\sum_j w_j\). The **counterfactual nuisance direction** is the residual of the predicted functional effect after removing the support-weighted local mean:

\[
r(c,d)=\hat y(c,d)-\sum_i \tilde w_i\, y_i .
\]

Gate:

\[
g(c,d)=\mathbf 1\!\left[\ \sum_i \tilde w_i \ge \tau_s\ \ \wedge\ \ |r(c,d)|\le \tau_r\ \right].
\]

Decision: advance only if the program-favourable sign of \(\hat y(c,d)\) holds and \(g=1\). Optionally, the model is refit only on the support neighbourhood when \(g=1\) is borderline; this is a **local support refit**, not a global retraining.

This is 3 operations: (i) support weights over intervention units, (ii) support-weighted functional correction, (iii) gate/decision.

## A3. Nearest recent primary mechanism and classical counterpart

**Recent mechanism (unverified exact identifiers):** 2025–2026 work on **retrieval-augmented or support-conditioned scientific prediction** and **conformal/selective prediction under distribution shift**. I cannot cite a specific paper/DOI from memory with confidence. The closest verifiable family I know is retrieval-augmented prediction and selective classification/conformal prediction; specific 2025–2026 primary CV/NLP/robotics papers should be authenticated by the root researcher. **Do not treat any identifier as verified here.**

**Classical counterpart:** kernel regression / Nadaraya–Watson local averaging with a selective-prediction gate; conformal risk control as the calibration layer if used.

**What is new relative to ordinary strong methods:** the gate is not a generic confidence score. It is a **support–response consistency residual** computed in the virtual-cell intervention embedding, with the perturbation class constrained in the kernel. The operation rejects a prediction when the predicted functional effect is not locally anchored by observed intervention responses, even if the expression model is confident.

## A4. Biological information constraint making the step matter

Functional responses are often driven by a small number of pathway states that may not be linearly recoverable from expression alone, and drug/context combinations can be functionally distinct despite similar transcriptomic embeddings. The support kernel uses **observed functional responses** from prior intervention units, so the gate carries information the expression model alone does not have: whether the functional effect is locally supported. This is not universal impossibility; it is a finite-budget inductive bias favouring deferral where functional support is absent.

The constraint is: the virtual-cell model may predict expression for many pairs, but the functional endpoint is only defensibly advanced where the intervention class and context neighbourhood contain observed functional responses. This is a testable information constraint, not an architectural claim.

## A5. Difference from strong ordinary method / equivalence

**Strong ordinary baseline:** a multivariate model (e.g. gradient-boosted or regularized regression) mapping expression/context/perturbation features to functional endpoint, with ordinary cross-validation. The proposed gate differs by adding an **explicit intervention-support residual** and a **selective decision rule** that can abstain. If the strong baseline is already trained with the same support features and a calibrated abstention rule, the operation may be equivalent; the falsifier below is designed to detect that.

**Honest equivalence risk:** if the support kernel is just a nearest-neighbour confidence score and the baseline includes the same neighbour features, this collapses to a standard selective predictor. The distinguishing step is the **perturbation-class-constrained support residual on the functional response**, not on expression. If that does not add decision value, drop it.

## A6. Public dataset/repository and expected key fields/independent units

**Candidate public resources (unverified expectations; root researcher must verify access and schema):**

- **LINCS L1000 / CLUE Connectivity Map**: perturbation–expression profiles across cell lines. Expected fields: cell line, perturbagen, dose, time, gene expression. Independent unit: **cell line × perturbagen × dose × time run**, not technical wells.
- **DepMap / Achilles**: cell-line functional dependencies and viability screens. Expected fields: cell line, gene dependency, viability. Independent unit: **cell line × perturbation run**.
- **GDSC / CTRP**: drug sensitivity across cell lines. Expected fields: cell line, drug, dose, viability/AUC. Independent unit: **cell line × drug × dose run**.
- **Tahoe / scPerturb-style perturbation atlases**: single-cell perturbation responses. Independent unit: **perturbation × cell line × donor/replicate**, not individual cells.

**Required key fields:** context identifier (cell line, tissue, perhaps donor), perturbation identifier and class (drug, gene, cytokine, combination), dose, time, functional endpoint, and a run/replicate identifier. **Task unit** = cell line × perturbation × dose × time; **technical wells/cells/timepoints** are not independent units. This distinction is critical for the falsifier.

I cannot verify current 2025–2026 dataset versions, exact access conditions, or schema from memory. Mark all of the above as **unverified until authenticated**.

## A7. Cheapest data-blind source qualification and algebraic falsifier

**Data-blind qualification:** read the source code of the virtual-cell model and the candidate dataset metadata. Check whether the model already exposes a support/neighbourhood feature or an abstention score computed from the same intervention embedding. If yes, the operation is likely equivalent to an existing selective predictor; stop unless the perturbation-class-constrained functional residual is absent.

**Algebraic falsifier (no fitting):** on a held-out set of intervention units, compute the support weights and the residual \(r(c,d)\) using only metadata and precomputed embeddings. Test whether the gate’s abstention set is identical to a simple threshold on the model’s predictive variance or on nearest-neighbour distance. If the gate’s decisions are algebraically equivalent to a standard confidence threshold, the operation adds no new information. A stronger falsifier: check whether

\[
\mathrm{sign}\big(r(c,d)\big)
\]

is predictable from the model’s own uncertainty alone with no functional observations. If so, the functional support information is redundant.

## A8. True useful decision success/stop with controls

**Success criterion:** on held-out intervention units, the gated decision improves **functional decision utility** — e.g. precision of advanced candidates at a fixed budget, or area under the decision-utility curve — relative to strong baselines, with independent units as defined above.

**Stop criterion:** if the gate’s advanced set is not better than the baseline’s advanced set at equal budget, or if the algebraic falsifier shows equivalence to a standard confidence threshold, stop.

**Controls required:**

- **Direct control:** strong ordinary multivariate model on the same features, no gate.
- **Refit control:** same model refit on the support neighbourhood only.
- **CL control:** contrastive/self-supervised representation baseline with the same functional head.
- **AL control:** active-learning acquisition using the same support kernel but no functional residual gate.
- **Mixture control:** mixture-of-experts or ensemble with the same intervention features.
- **Equal-budget-search control:** random or grid search over the same candidate set with the same number of functional evaluations.

All controls must use the same independent-unit split and the same budget. No numerical fitting in this scout; the above is a protocol, not an experiment.

## A9. What world/agent/inherited improver would separately contribute

- **World model:** supplies the intervention embedding \(z(c,d)\) and the functional prediction \(\hat y(c,d)\). It does not supply the support gate.
- **Agent:** chooses which candidates to advance, using the gate plus program objectives. The agent can also decide when to collect more functional observations to expand support.
- **Inherited improver:** would need to improve the **support representation** or the **gate calibration** across tasks, not just the predictor. If an inherited improver only improves expression prediction, it does not address this operation. The transfer/improvement of the update rule is optional and only relevant if the gate’s support kernel is shared across tasks.

**Honest gap:** I have not verified a specific 2025–2026 primary paper that supplies this exact operation. The mechanism is classical kernel regression + selective prediction; the biological novelty is the perturbation-class-constrained functional support residual. If the root researcher finds a paper that already does this, the lead is not new.

---

# Candidate B (conditional, likely to be dropped): **Counterfactual dose–time monotonicity projection for functional triage**

This is included only because it is a genuinely different operation. It should be dropped if Candidate A qualifies, or if the monotonicity assumption is not supported by the dataset metadata.

## B1. Decision and endpoint

**Decision:** for a drug \(d\) at dose \(x\) and time \(t\), decide whether the predicted functional response is **monotone-consistent** with observed lower-dose/lower-time responses in the same cell line, and advance only if the projected response is consistent. Functional endpoint: viability or pathway reporter at \((d,x,t)\).

## B2. Minimal operation

Given observed functional responses \(y(d,x_j,t_k)\) for the same drug and cell line at lower doses/times, fit a monotone envelope (e.g. isotonic projection) and require

\[
\hat y(d,x,t)\ \text{lies within the monotone envelope expanded by a tolerance}.
\]

If not, project \(\hat y\) onto the envelope and use the projected value for triage. This is one projection operation plus one gate.

## B3. Nearest mechanism and classical counterpart

**Recent mechanism:** monotonicity-constrained or shape-constrained prediction; **unverified** specific 2025–2026 primary paper. Classical counterpart: isotonic regression / monotone splines.

## B4. Biological constraint

Many functional responses are monotone in dose and time over a restricted range, but not universally; this is a testable assumption. If the dataset metadata shows non-monotone responses, the operation is invalid.

## B5. Difference from strong ordinary method

A strong ordinary model can predict non-monotone responses. The projection enforces a shape constraint that may improve triage under sparse data. **Equivalence risk:** if the baseline is already shape-constrained, this is not new.

## B6. Public data

Same as A6; dose and time fields are required. **Unverified** whether the chosen dataset supports monotonicity over the relevant range.

## B7. Data-blind qualification and falsifier

Check metadata for dose–response monotonicity. Algebraic falsifier: test whether the projection changes the sign of the predicted effect; if it never does, the operation is inert.

## B8. Success/stop and controls

Same control family as A8. Stop if the projection does not improve decision utility at equal budget, or if the monotonicity assumption is violated in metadata.

## B9. World/agent/inherited improver

World model supplies predictions; agent uses the projection; inherited improver would need to learn shape constraints across tasks. **Honest assessment:** this is weaker and more assumption-laden than A. I would not pursue it unless A fails source qualification.

---

## Summary recommendation

**Pursue Candidate A only.** It is a concrete, falsifiable operation: perturbation-class-constrained support–response consistency gate with a functional residual, applied to a triage decision. The main honest gaps are: (i) no verified 2025–2026 primary paper identifier from memory; (ii) dataset access/schema unverified; (iii) equivalence risk to standard selective prediction if the baseline already includes support features. The algebraic falsifier and equal-budget controls are designed to detect that. Candidate B is a fallback only if A’s source qualification fails, and it should be dropped if the monotonicity assumption is not supported by metadata.