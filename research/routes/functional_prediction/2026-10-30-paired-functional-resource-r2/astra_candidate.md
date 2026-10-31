# Conditional candidate R2: a conservative recovery gate for cheap drug screens

**Status: conditional research candidate; no response values were read, no model was trained, and no code was changed.** This candidate changes the scientific object after the I304 challenge and the failed CXCL9 shared-gain test. It does not claim a new Bayesian or active-learning algorithm. Its possible contribution is an experimentally testable functional restriction: a cheap short-term response may be sufficient for a *durable-loss decision* in a bounded cell/drug domain, while the same response may be unsafe for another domain and must trigger an independent assay.

## Central question and changed premise

For a fixed cell background, drug, dose and exposure, can a cheap public screen response identify when treatment has caused **irreversible loss of recoverable function**, rather than transient cytostasis or a reversible metabolic change? Can a small, independently measured bridge panel define where that cheap response is safe to use for advancing or rejecting drugs, with explicit abstention elsewhere?

The cheap response `z` can be the documented growth/viability endpoint in GDSC, CTRP, PRISM or a comparable one-source matrix. The independent function `q` is fixed before access to outcomes: the recommended primary version is the fraction of cells that recover clonogenic growth after drug washout and a predeclared recovery interval. An acute apoptosis/dead-cell endpoint is a different candidate and must not be pooled with recovery.

The changed object is the **durability of function**, not the source of a proxy/function disagreement. I304 asks which layer is wrong and uses ordinary latent-source model comparison plus VOI to choose a measurement. R2 asks whether a cheap endpoint can carry a conservative, decision-level certificate for an independent downstream function. It does not revise score weights, impose a shared gain, or transfer a drug-specific residual globally. A positive result would be a bounded functional domain and a useful triage rule; it would still need to beat ordinary selective prediction and direct measurement before any algorithmic claim.

This premise is plausible but unverified. Cytostasis/cytotoxicity distinctions, growth-rate inhibition and assay-interference controls are established concerns. The novelty of the R2 question is therefore conditional on a new, qualified paired matrix and an out-of-domain test, not on the name “Agent” or “virtual cell.”

## Virtual-cell state

For each context `c`, drug `d`, dose `k`, and fixed exposure contract, retain the cheap response `z(c,d,k)` with its replicate and preparation uncertainty. Define durable loss as `r(c,d,k) = 1 - q(c,d,k)`, where `q` is the post-washout recovery fraction. The treatment decision is fixed in advance: advance a candidate only when `r >= τ`, or reject it when `r < τ`; the threshold `τ` and practical margin come from development data and are frozen before final test outcomes are unsealed.

The virtual cell is a small auditable state table, not an unobserved mechanistic simulator:

```text
S_t(c) = {
    cheap response curve z(c, d, dose),
    development-frozen response bins B,
    calibrated interval I_t(c, B) = [L_t, U_t] for durable loss r,
    independent-preparation counts and uncertainty scale,
    proxy-safe / unsafe / unresolved flags,
    queried conditions and remaining assay budget
}
```

Bins or monotone dose intervals are created from development data only. For a new drug, the cheap curve places its dose in a bin; the state supplies an interval for `r` only while that bin has passed its calibration and transfer checks. A conservative output is:

* **advance** if `L_t(c,B) >= τ`;
* **reject** if `U_t(c,B) < τ`;
* **measure directly or abstain** when the interval crosses τ or the bin is unsafe.

An independent endpoint observation updates only the interval and the safety flag for the predeclared cell/bin scope. A violation shrinks or withdraws that scope. It does not create a favorable bin, fit a drug-specific rescue, or silently turn a failed transfer into a new global model. This is the minimal two-way coupling: the Agent's measured endpoint changes the virtual cell's admissible certificate, and that certificate changes which candidate receives the next independent assay.

## Agent action and cost contract

The action menu contains one legal expensive measurement: a matched `q` assay for a whole `(cell, drug, dose)` condition, including its vehicle/control and the source's fixed independent-replicate requirement. All methods receive the same cheap `z` anchors, QC information and total `q`-assay budget. Directly measuring `q` for a target is always allowed.

At each round the Agent scores unresolved candidates by the expected number of decisions that could cross τ after one `q` result, divided by the full condition cost. It chooses the highest score, ties by frozen identifiers, reveals that `q`, updates the relevant interval and safety flag, and repeats until the fixed budget is spent. No multi-step look-ahead, score reweighting or language-model explanation is needed for the first test. A fixed bridge panel and random/uncertainty selection receive the same menu and cost.

The Agent therefore learns **where the cheap endpoint is decision-safe**, rather than learning a global response map. A direct assay wins whenever its cost or expected decision value is better. If no candidate can be certified, the correct output is abstention, not a forced ranking.

## Independent functional endpoint requirement

The `q` endpoint must be biologically and operationally independent of `z`:

1. For the primary version, remove or dilute the drug after the fixed exposure, allow the fixed recovery interval, and count clonogenic recovery or an equivalent independently calibrated reproductive-function readout. A later value of the same luminescence signal without a washout/recovery contract is not an independent durability endpoint.
2. Every pair must match cell identity, drug identity/structure, physical dose, exposure time, vehicle, treatment history, and treatment preparation. The recovery assay may use a separate matched preparation, but its biological replicate and plate identifiers must be explicit.
3. Technical wells are nested within one preparation and never counted as independent biological units. The source must expose QC, failed wells and control costs.
4. If an accessible source supplies Annexin V/PI, caspase or another acute-death endpoint instead, freeze a separate acute-death question and threshold. Do not merge it with post-washout recovery or call either endpoint “viability” by default.
5. A target or genetic reference is optional for the bounded durability question, but required for a molecular-mechanism or intervention-equivalence claim. R2 makes no such mechanism claim.

The current archive does not yet qualify this contract. The DrugComb audit recorded no usable apoptosis/caspase/PARP numeric values in the inspected export, and the paper-inspired OMIX matrix is controlled. GDSC/CTRP/PRISM provide plausible cheap anchors, but a nominal cross-database join is not a matched (z,q) pair. Until a public row-level bridge passes the contract, R2 remains conditional and no effect run is admitted.

## Whole-drug and whole-cell split

The test must make both forms of transfer visible:

| Split | Development | Calibration/bridge | Final test |
|---|---|---|---|
| Cell backgrounds | (C_{dev}) | disjoint (C_{cal}) | disjoint (C_{test}) |
| Drugs (and scaffold clusters when available) | (D_{dev}) | disjoint (D_{cal}) | disjoint (D_{test}) |
| Rows | all doses and preparations for a unit stay together | same rule | all doses and preparations stay sealed until evaluation |

The final test contains cells and drugs absent from development. A drug seen in calibration cannot be called unseen in test, and a technical replicate cannot be used to manufacture a new cell or drug. If the source cannot expose these identities, report a within-matrix exploratory replay only; do not claim transfer or screening savings.

## Strong ordinary baselines

Every arm gets the same cheap anchors, bridge outcomes, controls and `q`-assay budget.

1. **Direct endpoint baseline:** buy `q` for each selected target and make the threshold decision directly. This is the practical upper bound when the target list is small.
2. **Cheap-only baseline:** a predeclared growth-rate/viability rule with no independent endpoint. It measures how much of the apparent benefit is simply the cheap assay.
3. **Hierarchical two-endpoint model:** fit `q ~ f(z,c,d)` with cell and drug random effects, replicate/batch effects and posterior intervals; refit on all feedback. This is the strongest ordinary statistical rival and can represent local pooling and exceptions.
4. **Ordinary selective prediction:** quantile regression or conformal calibration on the same bridge set, with abstention at the same risk target. This directly tests whether the certificate adds anything beyond standard coverage control.
5. **Fixed/random/uncertainty bridge panels:** non-adaptive panels and standard variance-reduction or Bayesian VOI selection, each allowed to buy direct `q` targets. Include a fixed panel with the same response bins to isolate the Agent action from the state representation.

If the hierarchical model, conformal predictor or standard VOI policy matches R2 at equal information and cost, retain the durability relation as an empirical assay-calibration result only. Do not call ordinary interval calibration an Agent advantage.

## Minimal computation experiment

This is a planned, inexpensive replay; it is not an executed result.

1. Admit one public source only after the row contract passes. Use its cheap cell×drug×dose response as `z`, and a genuinely paired, independent recovery endpoint as `q`. Do not combine unrelated datasets to fill missing fields.
2. Freeze `τ`, the practical margin, bin/interval construction, replicate weighting, and a total expensive budget `B` before reading final test `q`. A pilot minimum is at least six cell backgrounds, twelve drugs, three doses, and two independent preparations per bridge condition; fewer units are exploratory only.
3. Fit development intervals, calibrate the safety/abstention rule on disjoint cells and drugs, then expose only cheap `z` for the final held-out cells and drugs. Run each policy for the same small budget (for example `B=2` matched `q` conditions per held-out cell, with controls counted); all unselected test `q` values remain sealed until the final evaluation.
4. Primary endpoint: durable-hit recall at a fixed false-advance rate, or equivalently threshold decision utility with the predeclared cost of a missed durable hit and a false advance. Secondary endpoints: interval coverage, abstention fraction, number of independent assays needed to reach a fixed recall, and frequency of correctly flagged unsafe bins. Raw `z` or `q` MSE is not the primary claim.
5. Compare R2 with every ordinary baseline above on the same held-out whole-drug/whole-cell units. Report the fraction of decisions that remain unresolved; do not discard difficult bins or use unselected test outcomes to change τ or the bins.

### One boundary construction (reasoning only)

Two drugs can have the same cheap response but opposite durability:

| drug | cheap response `z` | durable loss `r` |
|---|---:|---:|
| A (irreversible loss) | 0.80 inhibition | 0.90 |
| B (reversible arrest) | 0.80 inhibition | 0.20 |

With no independent `q` observation, these worlds are observationally equivalent to the cheap screen; a global `z → r` map must make a false choice. R2 can only certify a bin after the observed spread is below the frozen margin; otherwise it must measure or abstain. This construction is not data or evidence of an effect. It states the information boundary that the experiment must test.

## Falsification and stop conditions

Stop the R2 line, without adding a new loss or renaming the failed result, if any of the following occurs:

- no public source exposes a matched `z,q` row-level contract, or `q` is derived from the same signal as `z`;
- an independent bridge endpoint, dose, exposure, vehicle, preparation or replicate identity is missing;
- the `z`-bin interval violates its frozen tolerance on more than the predeclared test fraction, or nearly every drug becomes an exception;
- durable-hit recall at the fixed false-advance rate is no better than the best hierarchical/conformal/VOI baseline, or direct `q` measurement gives lower loss at the same total cost;
- the apparent gain vanishes under whole-drug and whole-cell holdouts, scaffold holdout, or a response-label permutation that preserves plate structure;
- the method improves `z` loss but does not change the fixed durability decision, or any threshold/bin is tuned after final outcomes are exposed;
- the abstention rate is so high that the method cannot support a predeclared fraction of decisions (set this fraction from calibration, not from the test result).

When a stop condition is met, report the result as an endpoint-sufficiency boundary or a negative resource audit. Do not infer molecular mechanism, therapeutic window, clinical durability or broad cross-assay transfer.

## Why this is a changed direction, and what remains unproven

R2 is not I304 with a new name. It changes the scientific output from **error-source localization and proxy reuse** to **a conservative certificate about an independent downstream function**. It is not the CXCL9 shared-gain law: it assumes no common response gain and explicitly permits arbitrary drug/cell exceptions. It does not claim that a virtual cell is necessary; an ordinary table plus conformal intervals may be sufficient.

The closest ordinary explanations are strong and likely: growth-rate normalization may explain some apparent cytostasis, a hierarchical multi-endpoint model may reproduce the state, and selective prediction may provide the same coverage. The contribution is worth pursuing only if a qualified public bridge demonstrates a reproducible, decision-level durability domain that survives whole-drug/whole-cell transfer and yields a net assay or decision benefit. Without that bridge, the correct status is **conditional candidate, not validated mechanism**.

## Evidence boundary inherited from the current archive

This design was based on the local records, without new network retrieval or response access:

- [`2026-10-30-paper-virtual-cell-reference/report.md`](../2026-10-30-paper-virtual-cell-reference/report.md), [`data_gate.md`](../2026-10-30-paper-virtual-cell-reference/data_gate.md), and [`challenge_initial.md`](../2026-10-30-paper-virtual-cell-reference/challenge_initial.md) establish that the paper's feedback loop is a design reference, I304 is reproducible by ordinary latent-source/VOI modeling, and the required paired proxy/function matrix is not currently qualified.
- [`2026-10-30-cheap-screen-joint-learning-r1/report.md`](../2026-10-30-cheap-screen-joint-learning-r1/report.md) records that the CXCL9 shared-gain relation lost to a constant-interaction comparator in three of four preparation records; no global gain is reused here.
- [`2026-10-29-local-relation-pilot/report.md`](../2026-10-29-local-relation-pilot/report.md), [`2026-10-29-common-screen-colearning/report.md`](../2026-10-29-common-screen-colearning/report.md), and the endpoint/support audits document the limits of dose-local sharing, generic feedback, and metadata-only joins. They do not provide a paired durable-recovery endpoint.
- The DrugComb qualification correction records a missing apoptosis/caspase/PARP numeric field in the inspected export. That is a data-gate limitation, not evidence that no public recovery or death resource exists.

These records support the changed question and its stop rules. They do not support a positive durability relation, a source-wide endpoint equivalence, a biological mechanism, or a novelty claim. No implementation, public download, model run or sealed/confirmation response was used for this candidate.

