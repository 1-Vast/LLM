# Evidence-conditioned histone response transfer

MAESTRO's next useful scientific role is to investigate a prediction disagreement and obtain evidence that changes a measurable decision. This study tests a small version of that claim: can source-qualified pharmacology help an agent select measured response donors for a frozen cross-cell predictor, and thereby select a more reliable cell/feature/sign follow-up? The agent cannot write numerical response vectors or replace the deterministic action decoder.

**Completed exploratory result: the scientific superiority gate failed.** The development-selected deterministic model found 14/20 directional histone-response hits; integrated and conventional agents each found 12/20, and agent-only found 10/20. No biological selector is promoted. Source provenance and campaign persistence are engineering capabilities, not evidence of successful scientific synergy.

## Why another experiment was justified

The preceding [context-discrimination study](../context_discrimination_20261013/README.md) found useful RKT model information but no demonstrated gain from more elaborate LLM reasoning. In its 84-compound pilot, the strongest fixed pair found 16 opposite-activity cases, deterministic RKT found 15, conventional LLM plus RKT found 12, and the integrated hypothesis/revision agent found 10. These were historical RNA-profile retrievals, not new cultures. Earlier apparent agent gains also mixed improved experimental choices with better filling of unmeasured values. Scientific prose sometimes drifted from the registered opposite-activity endpoint toward high activity or lineage diversity.

This study moves the agent's responsibility from overriding a small numerical menu to selecting and qualifying additional evidence. It supplies genuinely measured histone-peptide responses in a new assay modality, independent of the preceding L1000 response matrices. It remains an offline retrospective experiment using public data; publication and pretraining exposure prevent treating it as a prospective unseen biological discovery.

## The scientific architecture

The two cores contribute different objects. The response model produces numerical forecasts from measured donor responses and an observed query anchor. The agent produces requested evidence identifiers, source-bound donor qualifications and competing explanations. A deterministic decision layer controls admission, numerical transfer and the terminal action.

| Layer | Input and responsibility | Observable output |
|---|---|---|
| Measured-response model | Reference profiles plus an acquired A375 query profile; frozen ridge maps and residual transfer | Three target-cell response vectors and model/donor disagreement |
| Evidence agent | Query identity, permitted descriptions, donor menu and permitted diagnostics | Up to five requested donor descriptions, then qualified donor IDs or abstention |
| Decision contract | Valid donor IDs, admitted citations and fixed decoder | One target cell, measured feature and predicted direction |
| Evaluation | Withheld target profiles and retained replicate values | Assay-level directional hit and predictive metrics |

This is a response-transfer model within GCP, not a validated general virtual cell and not an extension of the L1000 RKT certificate. Reusing the existing ridge-transfer implementation avoids introducing an unsupported RNA-to-histone bridge. The contribution under test is the **incremental value of qualified evidence for a fixed model-mediated decision**, rather than the mere existence of an agent/model loop.

## Data, normalization and independence

The [GCP/P100 data descriptor](https://doi.org/10.1038/s41597-021-01008-4) describes targeted mass-spectrometry measurements across seven cellular backgrounds. The [GCP deposit](https://doi.org/10.6069/qmga-f590) supplies processed GCT matrices through Panorama. This experiment uses A375, MCF7, PC3 and YAPC at 24 hours, requiring the same compound-specific dose in all four lines and at least two retained samples per context. DMSO, vorinostat and staurosporine are excluded from model fitting and evaluation; vehicle wells remain permitted normalization controls. Published semagacestat/BMS906024 examples are excluded from the test population.

Compound connectivity blocks, computed from metadata structures, are assigned by a frozen hash to reference/development/test. Eligible counts are **66/27/20**. Structural identities cannot cross these partitions. This is a held-out compound split, not an entire unseen mechanism-family, laboratory or culture split. Compound doses can differ between compounds; identity matching does not establish equal exposure or target occupancy.

Normalization required a material correction before evaluating targets. The descriptor explicitly states that Level 2 is the log₂ ratio of light/heavy peptide signals, Level 3 includes invariant histone-peptide normalization, and Level 4 subtracts a whole-plate feature median. Whole-plate medians can depend on held-out treated wells. Consequently this study uses **Level 3 minus the same-plate DMSO feature median**, without treated query wells in centering. Preparation amendments document the switch and vehicle metadata handling; these are not silently erased.

The relevant plates have 40 common measured feature identifiers; finite complete reference support retains **34 modeled features**. That support filter uses reference measurements only. Missing visible A375 anchor values have a declared reference-A375-mean imputation; the final 20-compound choices record zero missing modeled anchor features. Target values are never imputed: unsupported query target measurements cannot become zeros. Released upstream sample/probe QC still depends on the source cohort and is a limitation, even after replacing the Level 4 normalization.

Source metadata contains plates, wells and internal replicate numbers, but not authenticated independent culture identifiers. A replicate-consistent sign is therefore a robustness criterion within these records, not independent biological replication. Shared DMSO controls induce correlated centering errors among compounds on the same plate; common plates, analysis tranches and source laboratories introduce further dependencies. Bootstrap intervals resample compounds and do not remove these dependencies. Exact within-compound dose matching across lines also does not establish comparability between different-dose donor compounds.

## Evidence acquisition and fair information access

PubChem descriptions were acquired live through its public compound-description API before agent decisions. The common cache holds **119 CID receipts: 99 with descriptive text, 19 empty and one failed request**. The failed source was metadata CID `0` for Verteporfin. Eligibility and source coverage have different denominators: the receipt counts cover the complete metadata collection, not just the 20 test compounds.

Each receipt stores the retrieval URL/time, exact JSON payload and SHA256, attributed description text, source name and source URL. Missing evidence remains missing. Descriptive pharmacology can suggest donor relevance; it is not measured target engagement or a causal mechanism label.

The distinction between retrieval and disclosure is essential. A common live PubChem cache is acquired by deterministic code. Each agent then chooses which five donor descriptions to disclose from its candidate menu. **This is agent-directed source disclosure and qualification, not autonomous corpus search, free-form web browsing or discovery of an unknown database.** The sources are newly retrieved in this session, but the scientific statements may have been known to the base model. The GCP outcomes and connectivity service are not evidence sources supplied to the agents.

The candidate menu is the union of the eight nearest chemical and eight nearest anchor-phenotype reference donors. All three arms receive the same query description and evidence budget. Integrated and conventional agents receive identical numerical diagnostics; their instructions differ. Agent-only omits learned forecasts while retaining the observed anchor and empirical donor similarities. Source receipts, messages, selections and responses preserve the exact information boundary.

## Frozen models, controls and endpoint

Reference data alone fit cross-cell multi-output ridge maps, with leave-one-out selection of regularization from 1, 10, 100 and 1000. Per-feature standardization uses the pooled reference standard deviation with a 0.1 log₂ floor. Baselines include target means, shifted anchors, ridge, phenotype-neighbor residual transfer, chemical-neighbor transfer, lexical pharmacology transfer and the equal ridge/phenotype blend.

For selected reference donors, residual transfer adds their target-minus-A375 response to the query A375 anchor. Valid selected donors are averaged; abstention or invalid output falls back to phenotype weights. Integrated and conventional predictions are the frozen 0.5 ridge plus 0.5 donor blend. Agent-only uses the donor prediction without ridge. No LLM confidence is a numeric weight, and no prose can override the transfer equation.

Controls include initial choices before donor-description disclosure and shuffled-query donor choices. The latter breaks query/donor correspondence; it is **not** a controlled rerun with randomized source text and does not alone establish causal use of pharmacology. Likewise a final citation proves attribution, not that reading the source changed the action. Those distinctions constrain any feedback/evidence-use interpretation.

One action is selected by the maximum absolute standardized prediction over three target lines and retained features, together with its predicted sign. A hit requires the observed signed vehicle-centered mean to exceed 0.5 log₂ and all available retained replicates to agree with that direction, with at least two finite replicates. This endpoint measures a directional histone-peptide response. It cannot establish killing, therapeutic selectivity, target-specific causation or clinical benefit. Selecting a large generic response can satisfy it; mechanism specificity is not an additional result.

The predeclared success gate requires a positive paired compound-bootstrap 95% interval against both the development-selected strongest deterministic policy and the conventional agent with matched information/budgets. Secondary metrics include centered cosine, signed magnitude, endpoint oracle, coverage, abstentions and resources. All registered comparisons must be reported, with paired discordance tests and the operational factorial interaction. Small test size limits power and generalization; a positive secondary metric cannot replace the primary decision gate.

## Development and final results

![Held-out decision results and paired uncertainty intervals](results.png)

Development selected the **no-agent ridge/phenotype blend** as strongest deterministic comparator: **14/27 directional hits**, mean centered cosine approximately **0.659**. This is model selection on development, not evidence that the integrated agent improves a held-out decision. Hyperparameters, blend, prompts and model identity are frozen before final target scoring.

| Test policy | Directional hits / 20 | Mean centered cosine |
|---|---:|---:|
| Reference target mean | 5 | 0.3450 |
| Shifted observed anchor | 2 | 0.3114 |
| Ridge transfer | 11 | 0.5934 |
| Phenotype-neighbor transfer | 12 | 0.5398 |
| Chemical-neighbor transfer | 5 | 0.3284 |
| Lexical pharmacology transfer | 3 | 0.3330 |
| **No-agent ridge/phenotype blend (development-selected)** | **14** | **0.6144** |
| Integrated evidence agent + model | 12 | 0.5958 |
| Conventional agent + model | 12 | 0.5826 |
| Agent-only donor transfer | 10 | 0.5152 |
| Initial choices before donor-source disclosure | 13 | 0.5978 |
| Shuffled-query donor control | 5 | 0.4357 |

All policies retain the same 20-compound denominator. The outcome-aware endpoint oracle finds a qualifying cell/feature/sign in all 20 compounds; it is not an executable comparator. The following paired contrasts are integrated minus the named policy, in percentage points:

| Comparator | Difference | Compound-bootstrap 95% interval | Wins / losses | Exact paired two-sided p |
|---|---:|---:|---:|---:|
| Development-selected no-agent model | -10 | [-30, 10] | 1 / 3 | 0.625 |
| Conventional agent | 0 | [-15, 15] | 1 / 1 | 1.000 |
| Agent-only | +10 | [-15, 35] | 4 / 2 | 0.688 |
| Initial choices before donor-source disclosure | -5 | [-20, 10] | 1 / 2 | 1.000 |
| Shuffled-query donor control | +35 | [10, 60] | 8 / 1 | 0.039 |

The primary gate fails against both required comparators. The intervals are compatible with uncertain differences, rather than a universal claim that agents harm biology. The shuffled-query comparison supports the importance of query-specific donor correspondence in this decoder; it does not attribute the benefit to retrieved pharmacology. In particular, final source-qualified choices do not improve the initial choices made before donor-description disclosure. The label `source_free_initial` still includes the supplied query description and numerical diagnostics; only donor-source disclosure is absent.

The operational interaction `(integrated - no-agent model) - (agent-only - shifted anchor)` is **-50 percentage points**, with bootstrap interval **[-85, -20]**. These arms have asymmetric decoders: model-equipped arms blend ridge and donor transfer, while agent-only uses donor transfer and its comparator shifts the anchor. This is an operational difference of improvements, not a clean causal factorial estimate of agent/VC complementarity. It does not establish a generally negative biological interaction.

The agent audit records 100 donor-description requests per arm. Nonempty descriptions were available for 81/100 integrated requests, 83/100 conventional requests and 86/100 agent-only requests. The fixed numerical fallback was used on 6/20, 4/20 and 4/20 queries respectively; these include empty/unsupported final qualifications and invalid calls, not solely explicit abstention. Valid admitted donor counts were 52, 62 and 61. Donor sets changed after source disclosure on 14/20, 13/20 and 14/20 queries. Changed rationales or sets show a process transition; they do not prove an improved decision, and the measured primary result does not demonstrate that improvement. Exact receipts and per-query traces are preserved in the source cache and [AGENT_AUDIT.json](AGENT_AUDIT.json).

## What is new, and what already exists

The prior art materially narrows the claim. [Robin](https://doi.org/10.1038/s41586-026-10652-y) already combines literature agents, iterative hypothesis revision, experimental assays and RNA-seq follow-up. [Co-Scientist](https://doi.org/10.1038/s41586-026-10644-y) already uses specialist agents, external search, persistent context and wet-lab validation. [Kosmos](https://arxiv.org/abs/2511.02824) links literature/data agents through a structured information world model and reports selected independent-data checks. [EvoScientist](https://arxiv.org/abs/2603.08127) already accumulates successful and failed research directions and execution strategies.

[PertReason](https://arxiv.org/abs/2607.18777) explicitly separates perturbation prediction from context-conditioned mechanistic reasoning. Its reference paths come from curated graphs paired with measured differential expression; these are not independent causal experiments. Here measured GCP responses score the action directly, and descriptive sources do not supply gold mechanism labels. [PerturbTrace](https://doi.org/10.64898/2026.08.18.745260) shows why final discovery recall is insufficient evidence of useful feedback. [Systema](https://doi.org/10.1038/s41587-025-02777-8) motivates separating specific biology from systematic response, while [simple-model benchmarking](https://doi.org/10.1186/s12864-025-11600-2) motivates strong numerical baselines. The [initial proteomic library](https://doi.org/10.1016/j.cels.2018.03.012) already studied cross-cell and cross-assay connectivity.

Accordingly this study makes no first-agent, first-memory, first-multimodal-transfer or mechanism-discovery claim. Its candidate methodological contribution is an auditable evidence-admission boundary tied to a frozen measured-response decoder and held-out terminal decision. Whether that boundary provides scientific benefit depends on the test, not architectural complexity. Review depths and the fuller 20-source record are in [literature_sources.json](literature_sources.json); selected full-text inspection is distinguished from abstract review.

## Framework implications and next justified work

Keep deterministic optimization responsible for the registered endpoint. Let the agent investigate source applicability and evidence gaps where numerical transfer lacks context, then admit its contribution only through validated source/donor objects. Preserve model disagreements rather than translating them directly into causal stories. Compare scientific yield and predictive filling separately, and retain negative results rather than tuning exposed targets.

CaseStore persistence is an independent engineering track: scope-bound source receipts, completed-campaign resume, pending-receipt reconciliation and avoidance of duplicate retrieval. Passing those checks proves operational continuity, not biological synergy. Persistent records are also not demonstrated cross-case learning. This experiment does not train a reusable memory on past cases and then evaluate it on new source studies. A future memory claim needs a frozen development-only episode bank and matched no-memory/shuffled-memory controls on new tasks.

The resulting optimized architecture keeps the numerical predictor and endpoint decoder as the operational decision authority. Source-qualified agents can propose evidence investigations, but their donor changes remain a research option until an incremental decision gate passes. The opt-in campaign persistence implementation can retain qualified receipts and recover completed work without duplicate retrieval; it must refuse unresolved partial campaigns until pending receipts are reconciled. This operational boundary is useful even when scientific yield does not improve.

For this study, retain provenance and persistence, and **reject promotion of the integrated donor selector**. Further scientific work should focus on a genuinely additional, context-matched observation that distinguishes explicit alternatives, with an independent laboratory or mechanism-family holdout and a discriminating measured functional endpoint. The current GCP outcome cannot be reused as fresh confirmation after another prompt. More tokens, hypotheses or memory would not establish the missing benefit on this exposed set.

## Cost, integrity and reproduction

This study authorizes at most USD 2.50 additional conservative API reservations, within the existing session ceiling. DeepSeek Flash is the only permitted provider model. Calls record exact prompts, returned objects, raw provider usage and failures; reservations are not invoices. Source retrieval is public and unmetered by MAESTRO. Actual laboratory wells and new culture experiments are zero; recorded-profile access and numerical forecasts must not be described as wet-lab execution.

The completed run contains **120 provider-call records: 117 valid successes and three failures**, with **USD 1.80 conservative reservations** under the USD 2.50 study ceiling. Actual token usage and any provider-price calculation are recorded separately in the cost report; the reservation is not an estimate of an invoice. Failed/invalid outputs remain in the traces and use the declared fallback. Only one stochastic agent realization was run per query/arm, so these results do not estimate stability across agent seeds.

[COSTS.json](COSTS.json) records 260,286 input and 52,512 output tokens. The same-day official Flash price snapshot gives an estimated USD **0.11103** at the applicable peak window; this is usage-based accounting, not a provider invoice. Lost transport responses or provider-side retries could leave unreported charges. Three bounded concurrent arms completed in **197.45 seconds**. Reused source receipts and deterministic reference fitting avoid repeated downloads and repeated model fitting per API turn.

The repository core suite passed **815 tests**; the preceding two study verifiers passed. The study verifier audits split/freeze boundaries, source identity, saved actions, replicate endpoint semantics and numerical result replay. Preparation/model amendments and [DEVIATIONS.json](DEVIATIONS.json) disclose the shared source-cache implementation, visible-anchor imputation, budget-reservation change and single-realization inference limits. See the preserved verification outputs and cost accounting for execution details.

The requested **maestro** environment (Python 3.11.16, NumPy 2.4.6) also passes all **815 tests** and the scientific result verifier. All 12 numerical policy predictions were independently rebuilt there from reference data, authorized anchors and cached donor IDs: maximum absolute difference was **0.0**, and every selected action was identical. Initial execution used Python 3.14; this environment replay required no additional API calls. [ENVIRONMENT.json](ENVIRONMENT.json) and `maestro_regression.log` preserve the checks. Total Python file count remains **189**: one research driver added and related transfer-metric tests consolidated into the existing knowledge-transfer suite.

The protocol and preparation/model freeze receipts establish when rules were fixed. Preparation amendments remain visible. All test choices must be saved before the evaluator reads target responses; the separately available A375 anchor is authorized input. Model/prompt freezes, exact data hashes, source receipts and cached outputs support auditing. A freeze's existence alone is insufficient: its hashes and the saved-choice timing must be checked.

From repository root, the existing `study.py` supplies metadata, preparation, development, decision/evaluation and verification commands. Use `python research/evidence_transfer_20261013/study.py verify` to audit preserved results. Consult the other command choices and freeze requirements before invoking them: preparation opens numerical matrices, and uncached agent decisions can incur paid calls. The decision command refuses to regenerate choices after final evaluation. Reproduction requires local ignored source caches or public reacquisition; checks of delivered artifacts should preserve caches. This report creates no additional Python file and does not supersede frozen preceding studies.
