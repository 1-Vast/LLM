# Research direction exploration after the feedback-validation result

Date: 2026-10-03, Asia/Shanghai. Status: exploration and design only.

## Recommendation

Prioritize one linked research question: can predictions of independent confirmation outcomes improve the allocation of a fixed resource budget between screening, verification, and stopping beyond strong simple policies?

First establish whether the feedback contains a reproducible signal under matched experimental conditions. Do not immediately build a more complicated world model. Retain the registered Jaaks negative result and distinguish it from the new exploratory questions.

Three subagents independently explored verification allocation, measurement-aware prediction, and agent/certification contributions. The parent reviewed their evidence and retrieved primary-paper metadata and full-text design/methods through Europe PMC. No production files were changed, model APIs called, new confirmatory outcomes opened, or physical experiments performed. Core and research suites were not rerun.

## Newly identified constraints

### 1. The exploratory verification advantage is not an equal-consumption comparison

Source: `../feedback_validation_20261003/results/followup_verification.json` and `followup_verification.py`.

| Policy | Measurements consumed | Confirmed discoveries |
|---|---:|---:|
| Static verify-hits | 3,958 | 238.5 |
| Static paired | 3,762 | 205.0 |

The reported 16.34% difference is 238.5 / 205 - 1. The paired policy consumed 196 fewer measurements, or 4.95% less than verify-hits. Its per-round `budget // 2` does not fully carry unused pairing capacity across rounds. Some leftover capacity is unavoidable under an odd total budget and pair-only actions; the new design must distinguish this from avoidable per-round underuse.

Normalizing discoveries by consumed measurements gives approximately 10.58%, but this is only an arithmetic diagnostic. It is not a repaired estimate or confidence interval: spending the remaining budget would buy different experiments.

The follow-up also counts each orientation access as one measurement rather than charging the corresponding `14 * plates` combination wells. In the primary report, 3,958 static purchases correspond to 80,738 combination wells, not 55,412. Verification-direction costs, shared controls, baseline wells, and plate setup must be treated explicitly.

Keep the original receipt unchanged. Before interpreting a verification-allocation effect, produce a separately labelled exposed-data analysis with budget conservation, feasible pairing, branch-specific costs, and terminal verification capacity. A screen-only policy's zero *observed confirmed* discoveries follows from the reporting rule; it does not mean zero biological hits.

### 2. Role-swapped validation cannot isolate measurement noise

The Jaaks Methods specify two drug/tissue-specific fixed anchor concentrations and a seven-point, 1,000-fold library titration. Emax is defined at the highest library concentration. Reversing anchor/library roles changes the dose domain and endpoint conditions.

Consequently, poor transfer across orientations supports limited robustness to that second protocol. It does not by itself establish that all learned effects are noise. The strongest unresolved alternatives are condition-specific biology, plate/reference error, and unstable target-context effects.

The original paper reports biological repeats for 14 cell lines, with 2-18 repeats and typically three technical repeats per biological repeat. Design-only inspection of the exported fitted tables found same-condition measurements on multiple plates, but their 46 fields do not provide an explicit culture, biological-repeat, technical-repeat, date, or passage identity. A barcode identifies a plate, not an independent culture. Do not authenticate biological replication from barcode counts.

The first data task should be recovering or documenting the repeat hierarchy using the glossary, supplementary design tables, raw-source documentation, and existing metadata. If unavailable, retain a plate-level diagnostic and label biological independence unknown.

The model subagent's attempts to retrieve supplementary design tables encountered TLS, HTTP 403, and connection failures. No barcode-to-culture map was authenticated. Its code review also found that the post-hoc R-squared is a variance-ratio diagnostic, not the usual squared-error R-squared, and the coefficient correlations compare shrunken estimates rather than independent physical effects. Do not infer a noise fraction from these statistics.

### 3. The new baseline is already adaptive

Static prediction plus verify-hits uses newly measured results to allocate verification. It is a dynamic scheduler with a fixed predictive ranking. Separate three contributions: predictor updating, measurement allocation, and LLM decision-making.

The proposed next protocol's 10% practical threshold cites fourfold latency versus a static policy. Its proposed static verify-hits comparator is itself multiround. Preserve the historical threshold and verdict, but justify any new threshold using the actual incremental resource and delay differences before freezing another study.

The existing 312-valid-call LLM test used deterministic-policy histories rather than histories generated by the LLM's own choices. Its MODIFY verdict is inconclusive under the registered rule, not evidence of benefit and not a universal rejection of LLMs.

### 4. Certificates need separate proceed and futility decisions

A valid lower bound above a threshold can support proceeding. A lower bound below that threshold only means sufficient yield has not been established. Futility requires an appropriate upper bound below the threshold, or explicit unresolved status.

A bound on `P(buy and yield < threshold)` is not a bound on `P(yield < threshold | buy)`. State which risk is controlled. Fixed-time guarantees cannot be reused under repeated inspection, optional stopping, adaptive shortlist replacement, or simultaneous claims without the corresponding justification.

Begin with a fixed-time decision. Sequential certificates are a later option, justified from the sampling-without-replacement literature. Certificates control a declared measured label, not biological reproducibility.

## Two experiments worth preparing

### A. Is independently reproducible target-context information learnable?

Use genuinely same-condition repeats where their provenance can be recovered. Separate culture, plate, reference, dose, and orientation structure. Start with a simple historical confirmation model or hierarchical shrinkage, not a deep network.

The smallest proposed model is a scalar correction: `validation prediction = static validation prior + lambda * purchased-screen feedback correction`, allowing `lambda = 0`. Fit lambda only on independent development history. A zero correction is a legitimate selected model. Match the prior's endpoint and protocol to the second measurement rather than assuming first-screen scores transfer unchanged.

For the existing S-by-V bipartite menu, adding a constant to every S drug effect and subtracting it from every V effect leaves pair predictions unchanged. Priors can yield unique numerical coefficients without identifying physical drug effects. Evaluate observable prediction contrasts, not a causal interpretation of the latent coefficients.

Compare a static prior, the current screen-only feedback update, simple repeat-calibrated shrinkage, and a minimally identifiable repeat-aware model. Estimate shared and measurement-specific effects only when the data support separating them. History-derived parameters must be fitted in development; target-context updates may use only measurements already purchased.

Evaluate held-out repeat predictions and action contrasts. Partition by authenticated culture or, for the weaker diagnostic, plate clusters. Keep a third untouched measurement for final evaluation when verification observations are used to adapt the model; otherwise evaluate subsequent purchased confirmations prequentially using predictions frozen before each reveal. Do not adapt on a hidden validation label and then call performance on that same label independent evaluation.

Continue if shared information improves repeat-level prediction or useful action comparisons over simple shrinkage. Modify or stop if shared signal is weak, unidentifiable, or does not transfer. Failure to distinguish effect blocks is a data/identification result, not justification for adding more blocks.

### B. Do the model and scheduler contribute separately?

After correcting allocation accounting on exposed data, freeze a 2-by-2 comparison:

| | Optimized simple scheduler | Proposed adaptive scheduler |
|---|---|---|
| Static predictor | Strong baseline | Scheduler contribution |
| Repeat-aware predictor | Model contribution | Combined contribution |

Actions are screening a new candidate, paying for an independent verification, and stopping. Add other interventions only with measured outcomes for their full conditions.

Strong baselines include full-feasible-budget paired measurement, a development-selected fixed screening/verification split, verify-hits with reserved terminal verification, and a simple historical confirmation-probability-per-cost rule. Charge both directions, unsuccessful attempts, and known fixed/shared resources. Unknown prices remain unknown; show measured-resource and delay trade-offs instead of invented net utility.

The primary endpoint is independently confirmed discoveries actually obtained through paid observations. Report first-screen yield, confirmation rate, missed discoveries, failures, cost, and rounds separately. Compare time-matched and resource-matched settings where feasible; do not force a static comparator to wait solely to create equal elapsed time.

Introduce an LLM arm only after a specific action requires more than reproducing displayed scores. It must run on its own purchased history and beat the strongest deterministic scheduler with equivalent information. A successful deterministic scheduler is a valid outcome even if no LLM contribution emerges.

Continue only if a proposed contribution achieves a predeclared practical benefit on new qualified evidence. If optimized verify-hits accounts for the entire gain, retain that policy and pause complex feedback/LLM selectors. Do not require an LLM win.

## Data candidates and appropriate scope

| Candidate | Useful role | Remaining boundary |
|---|---|---|
| Existing Jaaks same-condition repeated plates | Exposed-data variance and identifiability diagnostics | Need culture/technical hierarchy; barcode alone is insufficient |
| Jaaks role-swapped complete panels | Exposed-data development and budget-accounting correction | Different conditions; already opened; not new confirmation |
| Nair et al. 2023 | Cross-protocol/second-laboratory robustness on the shared validation subset | Primary technical duplicates; cross-lab validation selected 27 shared combinations in 15 lines, changed assay and treatment conditions; cannot evaluate arbitrary full-menu policies |
| BATCHIE prospective release | Prior-art reference and potentially bounded prediction validation | Adaptively measured fraction of the full library; not complete alternative-policy support. Existing repository work already noted this limitation |

Do not impose an arbitrary 60-line gate on a small identifiability pilot. Confirmation sample size must follow a declared estimand, realistic variance/dependence, and a practical effect size. Selective validation can support a narrowly declared common menu, not outcomes for unvalidated combinations.

The original cheap predecision-state question remains separate. Cell identity, single-drug functional probes, current untreated state, and combination feedback are distinct inputs. No new state or STATE checkpoint result is established by this exploration.

## Literature checked and novelty boundary

Primary-source metadata/abstracts and relevant methods/design paragraphs were retrieved through Europe PMC. Detailed theorem proofs were not independently rederived.

- Jaaks et al. (2022), *Effective drug combinations in breast, colon and pancreatic cancer cells*. DOI: https://doi.org/10.1038/s41586-022-04437-2 ; full text: https://europepmc.org/articles/PMC8891012 . Supports the anchor design, repeat hierarchy, and selective rescreen boundary.
- Nair et al. (2023), *A landscape of response to drug combinations in non-small cell lung cancer*. DOI: https://doi.org/10.1038/s41467-023-39528-9 ; full text: https://europepmc.org/articles/PMC10307832 . Supports technical duplicate primary plates and selected cross-laboratory validation with independently sourced stocks, a different viability assay, and dose matrices.
- Tosh et al. (2025), *A Bayesian active learning platform for scalable combination drug screens*. DOI: https://doi.org/10.1038/s41467-024-55287-7 ; full text: https://europepmc.org/articles/PMC11696745 . Adaptive combination screening and follow-up validation already exist. The prospective release is linked as https://doi.org/10.5281/zenodo.13871987 ; its raw outcome files were not downloaded in this exploration.
- Woo et al. (2023), *Optimal decision-making in high-throughput virtual screening pipelines*. DOI: https://doi.org/10.1016/j.patter.2023.100875 ; full text: https://europepmc.org/articles/PMC10682755 . Multistage budget allocation is prior art; its computational setting differs from noisy wet-lab confirmation.
- The model subagent also read the original full text of *bayesynergy*, https://doi.org/10.1093/bib/bbab251 , and *Dose-response prediction: a probabilistic approach*, https://doi.org/10.1186/s12859-023-05256-6 . These support accounting for repeat/control uncertainty and condition-specific probabilistic prediction; they do not establish effectiveness of the proposed correction. The parent did not separately audit their implementations.
- Waudby-Smith and Ramdas, *Confidence sequences for sampling without replacement*: https://arxiv.org/abs/2006.04347 . The subagent checked the original abstract; theorem-level applicability remains to be checked before implementation.
- Jin and Candes, *Selection by Prediction with Conformal p-values*: https://jmlr.org/papers/v24/22-1176.html ; ACS: https://arxiv.org/abs/2507.15825 . The subagent checked original abstracts. Do not describe ACS as allowing no adaptation at all; its permitted adaptation depends on information-control assumptions.

Potential contribution: reproducibility-aware prediction plus evidence allocation that improves independent confirmation yield beyond strong verification policies. Novelty is a hypothesis to check against the literature, not an established result.

## Concrete next step and execution boundary

First reconcile the exposed verification replay's feasible budget and branch-specific wells, and qualify the available repeat metadata. Then run a small, explicitly exploratory identifiability diagnostic if that design is supportable. Only after a useful signal and qualified external evaluation are established should the 2-by-2 protocol be frozen and executed.

The ready-to-copy English continuation prompt is `NEXT_PROMPT.md`. All existing freezes, result files, thresholds, and verdicts remain unchanged. This exploration did not establish new discovery gains or biological efficacy. No Git commit or push was performed.
