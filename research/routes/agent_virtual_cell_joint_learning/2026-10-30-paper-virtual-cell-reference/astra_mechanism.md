# Exception-aware conditional-interaction co-learning for cheap functional screens

**Status: design only (2026-10-30).** No response values were consumed for this proposal, no model was trained, and no code was promoted. The proposal is deliberately narrower than a generic “Agent plus virtual cell” system. It starts from the failed CXCL9 shared-gain restriction and asks whether a small, explicitly testable **interaction-support rule** can be learned and withdrawn when a drug is an exception.

## Frozen hypothesis, assumptions, rivals, and falsifier

### Hypothesis

For a fixed cell background, dose, exposure time, and functional endpoint, the dual-condition interaction residual

```text
i(c,d) = y(c,d,11) - y(c,d,10) - y(c,d,01) + y(c,d,00)
```

is not a common multiplicative gain. It may nevertheless be sufficiently stable within a small **single-condition response signature** `r(c,d) = (u,v)`, where `u = y10 - y00` and `v = y01 - y00`, to support decisions for several unmeasured drugs. The virtual cell stores these signature-indexed residual intervals and an exception mask. The Agent buys a dual-condition measurement that can certify or reject a whole signature bin, then uses the revised mask and intervals for the next drug decisions.

The central prediction is conditional and falsifiable: with the same pre-measured single-condition anchors and a fixed number of dual-condition observations, a signature-conditioned interaction rule should certify more held-out drug decisions than a global gain, a constant-interaction model, and a strong hierarchical interaction model **only when** the residual is stable within a bin and the bin contains enough target drugs to amortize a calibration observation. When the residual is heterogeneous, the rule must abstain or fall back to direct measurement.

This is an interaction-support question, not a claim that drugs in one bin share a molecular target or mechanism. The CXCL9 result is a boundary: its common gain was lower than the constant-interaction comparator in three of four preparations, and 11 of 20 gain envelopes missed the observed technical-well ranges. That result does not show that every conditional interaction rule fails, but it rules out silently reusing the failed global gain.

### Assumptions that must be frozen before any outcome is read

1. `00`, `10`, `01`, and `11` are the same biological background, dose, time, endpoint, and normalization contract. A different exposure schedule is a different action.
2. The development data can estimate technical and preparation variation. Technical wells are not counted as independent biological preparations.
3. A signature bin is defined from `00`, `10`, and `01` only. Its thresholds and number of bins are frozen on development data; the held-out `11` response cannot create a favorable bin.
4. Within a qualified bin, `i(c,d)` has a bounded spread that can be checked on held-out drugs. The bound is an empirical restriction, not a molecular completeness assumption.
5. Query missingness is recorded. A screen with selective missing `11` outcomes cannot be treated as a random matrix without a sensitivity analysis.
6. The endpoint is interpreted on its documented scale. A pooled cell-count proportion or a fluorescence signal is not silently converted into an absolute viable-cell number, secretion concentration, death probability, or clinical benefit.
7. The decision target (for example, retain if `y11 <= tau`, or rank the lowest `y11`) and its practical margin are fixed before adaptive queries. The scoring objective is not changed after feedback.

### Strong ordinary rivals

Every rival receives the same anchor observations, control wells, query menu, repeat policy, and total well cost.

- Directly measure the final `11` target for every queried drug; this is always legal. For a small target list it should dominate.
- `B_add` and `B_const`, the additive and fixed-untreated-interaction rules used in the CXCL9 audit.
- A drug-specific hierarchical interaction model with partial pooling, random slopes, and the same two adaptive query slots. This is the strongest ordinary statistical rival for the proposed relation.
- Ridge reconstruction from observed perturbations (the Rhaister-style economical predictor), an ordinary matrix/interaction completion model, and a fixed calibration panel followed by joint refitting.
- Standard uncertainty/variance-reduction or Bayesian batch active design, including a BATCHIE-like design where its ordinary model can choose the same direct target actions.
- A **non-adaptive signature-panel baseline** using the same bins and the same two calibration slots, and a **same query policy with a fixed model**. These isolate any effect of changing the virtual-cell state from an effect of choosing a better action.

If the hierarchical model, ordinary active design, or the non-adaptive panel reproduces the result, this is a useful assay-specific relation at most; it is not a new Agent algorithm.

### Falsifier and stop rule

The candidate is rejected for the declared source and endpoint if any of the following is frozen and observed on the untouched test set:

- the residual spread in a signature bin exceeds its development bound on more than a predeclared fraction of test drugs, or a bin requires a separate exception for nearly every drug;
- decision coverage or calibrated interval coverage is no better than the strongest ordinary rival at the same cost (a practical margin must be set from replicate precision before testing; an illustrative gate is a 10 percentage-point coverage gain);
- direct target measurement gives lower decision loss at the same two query slots, especially when fewer than eight targets share a bin;
- the result disappears after holding out independent preparation/background groups, drug IDs or chemical scaffolds, or after shuffling the signature while preserving batch structure;
- the only improvement is lower average prediction loss while the fixed threshold/ranking decision does not change, or the Agent uses a test `11` outcome to change bin thresholds;
- controls, normalization, exposure identity, or replicate nesting are not qualified. An unqualified source is an admission failure, not a positive or negative biological result.

On rejection, stop the interaction-sharing claim. Do not fit drug-specific rescues and rename them a shared law; report direct measurement or abstention as the model output.

## Observable data contract

The minimum row is one condition-level functional observation with the following fields:

| Field | Required use | Cheap-screen interpretation |
|---|---|---|
| `context_id` | cell line, sample, or preparation identity | Keep independent preparations together; never split technical wells across folds. |
| `drug_id` and optional `dose` | intervention identity | A dose or salt change is a new action unless the source contract proves equivalence. |
| `time` and treatment history | exposure semantics | Fixed time is the minimum version. Sequential or washout treatment is out of scope here. |
| `endpoint_id` and `response` | `y(c,d,s)` on one declared scale | Use a relative response or raw assay signal only as documented. |
| `condition_code` | `00/10/01/11` or the source-specific two-factor crossing | The four cells must share background, dose, time, and endpoint semantics. |
| `vehicle/control_id` | denominator and matched control | Controls and their failures are part of cost and uncertainty. |
| `replicate_id`, `batch/plate_id`, QC flags | error model and leakage control | Distinguish technical wells from independent cultures. |
| optional `context descriptors` | diagnostics only | Do not use omics or an LLM-generated embedding as a substitute for missing functional fields. |

The compact Rhaister/Emerald Bay summary has verified identity fields (`cell_line`, `condition`, `growth_rate`) and a documented cell-count-proportion readout, but its released summary has no preparation/plate key and its numerical response values were not consumed in this episode. It can support a relative-response baseline or a schema check; it does not by itself qualify the crossed `00/10/01/11` interaction test.

The CXCL9 repository supplies the required crossed cytokine/inhibitor conditions and four preparation files, but its exported PE signal is a capture-bead sandwich assay readout for secreted CXCL9, not a calibrated secretion concentration or cell count. Its five-inhibitor panel is too small to demonstrate amortized savings; it is the negative boundary and a possible development diagnostic, not a positive validation set.

## Model state and functional endpoint

For each fixed background `c`, compute from the common anchor packet

```text
u(c,d) = y(c,d,10) - y(c,d,00)
v(c,d) = y(c,d,01) - y(c,d,00)
i(c,d) = y(c,d,11) - y(c,d,10) - y(c,d,01) + y(c,d,00).
```

The failed CXCL9 law is `V = kappa U`, where `U = u`, `V = y11 - y01`; equivalently it imposes `i = (kappa - 1)u`. The proposed model does not impose this proportionality. It uses a development-frozen partition of the observed signature plane `r=(u,v)` into bins `J`, and stores

```text
M_t(c) = {signature bins J, residual intervals H_{c,J}, assay error scale Sigma_c,
          exception mask E_{c,d}, unresolved target decisions}.
```

`H_{c,J}` is an interval or a small robust distribution for `i` estimated from calibration drugs in bin `J`. A target drug may borrow that interval only while its anchor signature lies in the bin and no exception has been recorded. This is a predictive equivalence on the declared endpoint, not a latent cell state and not an assignment of molecular mechanism.

The functional prediction is `yhat11 = y10 + y01 - y00 + ihat`, with an interval propagated from `H_{c,J}`, anchor uncertainty, and assay error. A decision is emitted only if the whole interval lies on one side of the fixed threshold or gives a stable rank; otherwise the model says **measure directly or abstain**.

## Minimal Agent–virtual-cell loop

1. **Anchor.** Reveal the predeclared `00`, `10`, and `01` conditions for each target drug. Fit the frozen signature bins and the ordinary baseline models using training/development data only.
2. **Find unresolved mass.** For each bin, count target decisions whose propagated interval crosses the threshold or can change the top-k list. Do not sum generic predictive entropy for targets that cannot change the action.
3. **Choose a legal query.** Select one drug in the bin with the largest unresolved decision mass per condition-pair cost. A direct target `11` query is in the same menu and wins whenever it is cheaper or more decision-relevant. The first version has no multi-step lookahead and no LLM role.
4. **Update the virtual cell.** Add the returned `11` response, update `H_{c,J}` and `Sigma_c`, and mark `E_{c,d}` if the predeclared interval is violated. An exception withdraws sharing for that drug or bin; it does not trigger an unconstrained refit until the target fits.
5. **Choose the next query or stop.** Recompute unresolved decisions and stop at the fixed budget. Return decisions, intervals, exceptions, and unresolved actions. The Agent has changed its action because the measured functional relation changed; it has not changed the definition or weights of the score.

The only co-learning claim is this two-way dependency: a query changes the interaction support carried by the virtual cell, and that support changes which next measurement is worth buying. The same procedure can be implemented by an ordinary sequential design program. Its algorithmic novelty must therefore be demonstrated against the strong rivals above, rather than inferred from the word “Agent.”

## Fixed observation budget and fair replay

Use one fixed budget for all methods:

- The common anchor packet contains the matched controls and the `00/10/01` response for the candidate target set. Its real well cost is recorded once and paid by every method.
- The adaptive budget is **`B=2` condition-pair slots per background**. A slot is one `11` treatment condition plus its matched vehicle/control and the source's fixed technical replicate count. No method may buy a third slot after seeing a surprising result.
- The minimum amortization case is eight target drugs in a signature bin. If a source has fewer targets, report direct-measurement dominance rather than extrapolating savings.
- A retrospective replay reveals only values in the anchor packet and the two selected slots. All held-out `11` outcomes remain sealed until the final evaluation. Failed wells, controls, and repeat costs are included in the same budget accounting.

This budget is intentionally small enough for ordinary public screens. It does not assert that two wells are biologically sufficient; the source's own repeat structure and precision decide whether the candidate is admitted.

## Train, calibration, and test split

Use a three-way split before any adaptive trajectory is generated:

1. **Development:** independent preparation/background groups and drug IDs used to estimate signature bins, interval widths, assay error, and the practical decision margin.
2. **Calibration:** disjoint groups used once to freeze the query tie-break, bin thresholds, and exception rule. No final test `11` outcomes enter this step.
3. **Test:** held-out preparation/background groups and held-out drug IDs (and scaffold clusters when structures are available). Reveal only the anchor packet and the two chosen query slots, then unseal all remaining `11` outcomes once.

All technical wells and repeated rows from one preparation remain in one split. If independent preparation IDs, batch identity, or action history are absent, the result is an exploratory matrix replay and cannot support external transfer or a biological population claim. The four CXCL9 files provide a preparation-holdout diagnostic, not enough independent backgrounds for a general claim. The compact Rhaister summary lacks the crossed interaction and preparation fields required for this test.

## One computable toy counterexample (not data)

Take a no-drug calibration with `(y00,y10,y01,y11)=(0,1,1,2.5)`. Then `u0=1`, `V0=1.5`, `kappa=1.5`, and the untreated interaction is `i0=0.5`. Suppose development has frozen two signature bins using `u<2` (A) and `u>=2` (B), and two calibration queries have established `i_A=+0.5` and `i_B=-0.5`. The held-out target drugs reveal their single-condition anchors but not `y11`:

| target | `u` | `y10` | `y01` | true `i` | true `y11` | shared gain | constant `i0` | signature rule |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A1 | 1 | 1 | 1 | +0.5 | 2.5 | 2.5 | 2.5 | 2.5 |
| A2 | 1 | 1 | 1 | +0.5 | 2.5 | 2.5 | 2.5 | 2.5 |
| B1 | 3 | 3 | 1 | -0.5 | 3.5 | 5.5 | 4.5 | 3.5 |
| B2 | 3 | 3 | 1 | -0.5 | 3.5 | 5.5 | 4.5 | 3.5 |

The computed mean absolute errors are 1.0 for the shared gain, 0.5 for the constant-interaction rule, and 0 for the signature rule. With `B=2` dual-condition slots, one calibration in each bin can support four target predictions in this toy. Direct measurement with two slots verifies two targets, so the example shows a possible amortization pattern, not a superiority theorem. A hierarchical interaction model with the same bin information can reproduce it; that is why the toy is a feasibility counterexample and not evidence of algorithmic novelty. If one B target has `i=+0.2`, the predeclared B interval rejects it and the model must measure or abstain rather than silently claim transfer.

## Distinction from the self-auditing score paper

The local abstract for *Virtual-cell verification enables self-auditing AI discovery for immune rejuvenation* describes three components: PACE gene-set phenotype modules, CellQ single-cell transcriptome tokenization with a multimodal LLM, and an Analyzer–Planner–Auditor that changed an equal-weight mean into a balance-constrained minimum after a 110-compound PBMC screen, with a separate 13-compound T-cell assay. That is the evidence level available here; the abstract is not a full method or data audit.

The present mechanism keeps a fixed functional endpoint, fixed threshold/ranking objective, fixed decision margin, and fixed cost. Feedback changes an assay-specific **interaction support/exception map**, not the score weights or definition. It uses ordinary pooled functional fields and does not require single-cell omics, residual vector quantization, an LLM, or a self-audit of the objective. A successful replay would show conditional functional transfer under a held-out action contract; it would not reproduce or extend the paper's objective self-correction claim.

## Claims that must not be made

- Do not call a signature bin a pathway, target class, mechanism, or cell state without independent perturbation or rescue evidence.
- Do not call a relative cell-count or fluorescence endpoint absolute viability, secretion, death, growth rate, durability, or clinical benefit.
- Do not claim broad cross-cell-line or cross-assay transfer from a preparation-holdout replay, and do not treat technical duplicates as biological replication.
- Do not claim screening savings unless all anchor, control, repeat, failed-well, calibration, and adaptive-selection costs are counted against direct measurement and ordinary active design.
- Do not claim Agent advantage if an ordinary hierarchical model, fixed panel, BATCHIE-like design, or direct target measurement matches it.
- Do not change the threshold, ranking loss, bin thresholds, or practical margin after seeing test outcomes. Objective revision would be the self-audit problem and is outside this mechanism.
- Do not promote an implementation to `src/` or `tools/` from this design note.

## Admission decision

This is a minimal candidate for a changed data contract: a sufficiently large, crossed, single-endpoint functional screen with matched two-factor conditions and independent preparation metadata. The current CXCL9 panel is a useful negative diagnostic but is too small and rejects the global gain. The currently verified Rhaister summary is cheap and public but lacks the crossed interaction and preparation fields. Therefore the mechanism is **not validated or admitted for an effect run**. The next admissible step is a source/schema check for a public screen meeting the row contract; if no such source exists, retain the CXCL9 negative boundary and stop rather than adding a loss, an LLM role, or a larger latent model.


