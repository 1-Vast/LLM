# MAESTRO: when does feedback improve biological decisions?

English research report, 13 October 2026. Base revision: `ac99532a21ff23bd2221784ddf87debe196b195d`.

**Verdict: useful virtual-cell prediction and a modest exploratory acquisition benefit;
no demonstrated autonomous-agent advantage or positive dual-core synergy.** The new
integrated reasoning pilot performed worse in point estimate than both its simpler
agent comparators and the strongest fixed workflow. No scientific component is promoted.

This study completed a Block Q audit, targeted literature investigation, task selection,
an executable deterministic replay over 702 compounds, and a matched DeepSeek pilot
over 84 compounds. It does not provide fresh biological confirmation. The agent
prototype tests a bounded scientific-reasoning workflow; it does not establish a
general autonomous researcher capable of independently selecting and completing
arbitrary biological investigations.

## 1. Why Block Q did not establish synergy

The local worktree was clean; GitHub HEAD matched the local revision. No active Python
experiments were found. Block Q's frozen input/code checks and statistical reconstruction
both passed. Its files were used read-only. Existing agent, CaseStore, evidence,
budget, RKT and evaluation interfaces were inspected before implementation.

**The virtual cell contributes substantially without an LLM planner.** At one well per
compound, the fixed sparse-hub campaign scores 0.623 with RKT filling versus 0.457
with its empirical fill on the same acquired cells. This +0.165 difference supports
the response model, not autonomous scientific reasoning. The fixed design also beats
the four-round planner by 0.044 while using one round. This does not prove the fixed
design is at an achievable ceiling: the outcome-aware reference is 0.910, but it uses
unavailable information. Oracle headroom is not actionable value of information.

**Block Q's utility is retrospective reconstruction conditional on activity.** It
rewards accurate direction on truly active cells and does not penalize declaring
activity on inactive candidates. The 702 compounds contain 4,808 measured contexts,
only 1,105 active. Activity must be inferred before a practical selection decision.

| Visibility | Actual activity | Mean predicted activity | Activity AUROC | Brier loss | Mean cosine, active contexts | Mean cosine, all contexts |
|---|---:|---:|---:|---:|---:|---:|
| No profile, B | 0.230 | 0.132 | 0.639 | 0.176 | 0.360 | -0.054 |
| One line, A1 | 0.230 | 0.224 | 0.855 | 0.104 | 0.528 | 0.117 |
| All other lines, A | 0.230 | 0.236 | 0.890 | 0.090 | 0.585 | 0.189 |

These are context-weighted descriptive means, so they need not equal Block Q's
compound-weighted primary contrasts. All-context cosine is a diagnostic, not a
replacement endpoint: directions of weak responses can be unstable. In regime B,
55.5% of all candidate contexts refuse a specific direction; the approximately 45%
reported previously concerns the active evaluation population. The denominators differ.

A simple illustrative prospective declaration rule, predicted activity >=0.5 and
expected active-response cosine >=0.5, makes only 80 declarations in regime B. Of
these, 49 are actually active with realized cosine >=0.5: precision 61.3%, recall
13.4% among contexts satisfying that joint truth criterion. With one measured line,
the corresponding values are 589 declarations, 70.3% precision and 61.9% recall.
These thresholds were used for diagnosis only, not tuned or independently validated.

**Coverage and distribution shift are credible explanations, not isolated causal
findings.** Development activity was approximately 7%, versus 23% in confirmation.
At the beginning of a campaign RKT underpredicts activity and ranks it weakly.
Concentrating acquisitions before obtaining first measurements therefore risks
missing useful compounds. At two wells per compound the historical planner's gain
is compatible with this explanation. A prevalence correction alone would require
stable class-conditional distributions; that assumption has not been established.
No new calibrator is promoted from these exposed outcomes.

**Previous LLM comparisons entangle decisions and filling.** Giving a conventional
agent the VC increased total utility by 0.038, but re-scoring the no-VC agent's chosen
cells with RKT gives 0.564, versus 0.555 for the VC-equipped conventional agent.
Better filling can explain a gain without better choices. The descriptive historical
interaction is -0.117, but policies are not factorially matched, so it is not a causal
interaction estimate. Invalid-output recovery also consumed 63 no-VC and 48
conventional-VC selections in Block Q.

**Biological specificity remains unresolved.** RKT's generic/specific decomposition
helps separate shared response from transferable direction. It does not identify
whether a residual is target biology, stress, dose sensitivity, plate variation or
measurement error. Existing measurements do not discriminate those causes.

## 2. Targeted literature and novelty assessment

Search records and retrieved abstracts are retained in `literature_sources.json`.
This was a targeted abstract/metadata review, not a systematic review or a claim
that every full paper was reread. MAP was checked by exact DOI after a keyword search
returned unrelated results. Intermittent network failures were retried and are
disclosed; inaccessible content was not treated as evidence of absence.

| Source | Relevant contribution | Consequence for MAESTRO |
|---|---|---|
| [PRESAGE](https://doi.org/10.1101/2025.06.03.657653), 2025 preprint | Modular gene embeddings; source choice and measured cross-system perturbations matter; functional evaluation beyond regression | Preserve typed measured-response transfer and test a decision endpoint. Sparse coverage itself is not new. |
| [MAP](https://doi.org/10.1038/s42256-026-01286-w), 2026 | Integrates 14 resources, 694,246 mechanistic edges and multimodal pretraining for unprofiled drugs | Knowledge-conditioned zero-shot prediction is prior art. Pathway-consistent predictions do not independently validate killing or mechanisms. |
| [TxPert](https://doi.org/10.1038/s41587-026-03113-4), 2026 | Transfers through multiple gene relationship graphs, including screen-derived information | Multi-source graph transfer is established; genetic perturbation results do not automatically transfer to drug dose/time effects. |
| [GeneAgent](https://doi.org/10.1038/s41592-025-02748-6), 2025 | Database self-verification improves gene-set descriptions | Use source-bound claims; descriptive accuracy is not evidence of better experimental selection. |
| [BioDiscoveryAgent](https://doi.org/10.48550/arxiv.2405.17631) | Iterative genetic experiment design using biological reasoning and tools | Compare against a conventional LLM workflow with the same information and calls. A reasoning loop is not novel. |
| [BATCHIE](https://doi.org/10.1038/s41467-024-55287-7), 2024 | Bayesian batched experimental design, including prospective combination-screen validation | A strong deterministic adaptive baseline is essential. Combination tasks offer meaningful outcomes but require endpoint and data audits. |
| [CellOT](https://doi.org/10.1038/s41592-023-01969-x), 2023 | Optimal transport between unpaired single-cell distributions | Useful for distributional transfer; inferred couplings are not measured cell trajectories. No dynamics claim is imported here. |
| [JUMP Cell Painting](https://doi.org/10.1101/2023.03.23.534023) | Large chemical/genetic morphological reference resource | Potential orthogonal evidence, but cell-line/dose/platform alignment and nuisance controls must precede use. |
| [Systema](https://doi.org/10.1038/s41587-025-02777-8) | Exposes systematic variation that inflates perturbation-prediction metrics | Keep generic controls and demand perturbation-specific, decision-relevant evidence. |
| [Cell Painting representation learning](https://doi.org/10.1038/s41467-024-45999-1), 2024 | Separates treatment information from confounding using diverse imaging studies | CV suggests invariance audits across plates/studies, not blindly concatenating morphology and RNA embeddings. |
| [Revisiting active perception](https://doi.org/10.1007/s10514-017-9615-3), 2018 | Sensing should be chosen for the task and current information state | Measure where competing decision outcomes differ. More rounds are a cost, not evidence of intelligence. |
| [Safe model-based RL](https://doi.org/10.48550/arxiv.1705.08551) | Model uncertainty and explicit assumptions constrain exploration | Borrow mismatch detection and refusal; do not claim Lyapunov guarantees or feedback control for sparse static cell profiles. |
| [Black-box label-shift estimation](https://doi.org/10.48550/arxiv.1802.03916), 2018 | Corrects prevalence changes under class-conditional invariance | A candidate calibration diagnostic, not a justified automatic repair when assay/context also changes. |
| [Optimal design for model discrimination](https://doi.org/10.1037/a0016104), 2009 | Selects experiments that separate explicit competing models | Mechanism claims require distinct predicted observations and a qualified observable. Different prose is insufficient. |
| [PerturbTrace](https://doi.org/10.64898/2026.08.18.745260), 2026 preprint | Reports strong final recall without consistent benefits from true versus random feedback | Directly relevant prior art: trace feedback-to-state, state-to-action and action-to-outcome separately. |

The defensible opportunity is **evidence acquisition for a specified biological
disagreement under model mismatch**, with typed source provenance, competing
observable predictions and verified incremental decision value. Neither source
routing, active learning, self-verification nor persistent memory alone is novel.
The present simple conditional selector is a diagnostic prototype, not a novel
algorithm or a publishable demonstration of autonomous synergy.

## 3. Task selection and data audit

| Candidate | Decision |
|---|---|
| More sophisticated one-well map completion | Reject for now: coverage already wins and LLM overrides repeatedly fail. |
| New knowledge graph for unprofiled activity | Defer: meaningful gap, but weak annotations and no demonstrated incremental source value justify large implementation. |
| Context-dependent transcriptional activity | Select for a cheap feasibility test: real observations, explicit opposite outcomes, matched budgets and preserved RKT scope. |
| PRISM selectivity or combinations | Scientifically attractive, but existing MAESTRO exposure and known replicate/plate dependencies prevent calling cached assays fresh confirmation. |
| RNA plus Cell Painting mechanism discrimination | Potential next acquisition task, conditional on matching contexts and an independently measured discriminating endpoint. |

The selected question is whether a second recorded cell-line profile can reveal
activity opposite to the first. Active means landmark response norm exceeds the
line's 95th-percentile vehicle norm. It is not a formal test that two cell lines
differ, and inactivity does not prove no biological effect.

Data: GSE70138 level-5 landmark consensus at 10 uM / 24 h, seven lines, 979 reference
compounds and the same 702 eligible Block Q query compounds. The original identity
audit excludes 28 connectivity duplicates and four compounds with too few lines;
the eligible query grid contains 4,808 responses. Reference means, maps, hub order,
fixed-pair ranking and empirical probabilities use reference outcomes only. The
frozen activity certifier is fitted on GSE92742. No query outcome enters model fitting.
Query arrays are set to NaN in the atlas before the first selected observation is
revealed. The LLM receives only that observation and candidate predictions.

The hub is A375 where available; the transfer order is A375, PC3, MCF7, YAPC, HELA,
HA1E, HT29. Fixed-pair ranking maximizes reference discordance, making it a stronger
task-specific comparator than sparse-hub alone. Availability is metadata-visible.
Original preprocessing, identity mapping and source dependencies remain traceable
through Block Q's unchanged freeze and the new `input_audit.json`.

Among all 734 cached query compounds, 4,899 contexts have one level-5 signature and
110 have two. These are already consensus signatures, not authenticated independent
cultures. The study does not estimate experimental error from those counts.
Model uncertainty (certificates), missing contexts, biological heterogeneity and
technical/culture error remain distinct. A certificate is not a biological replicate.

## 4. Full-library feasibility and virtual-cell contribution

Each policy receives two profile-retrieval slots per compound. All 702 compounds,
including inactive ones, remain in the denominator. No outcome is an LLM judgment.

| Policy | Discordant compounds / 702 | Rate | Strict-margin discordance | Simulated rounds |
|---|---:|---:|---:|---:|
| Fixed sparse hub | 108 | 15.38% | 23 | 1 |
| Best reference-derived fixed pair | 133 | 18.95% | 35 | 1 |
| Conditional empirical feedback | 127 | 18.09% | 29 | 2 |
| Norm-neighbour feedback | 143 | 20.37% | 27 | 2 |
| RKT feedback | 158 | 22.51% | 38 | 2 |
| RKT prediction packets shuffled across compounds | 131 | 18.66% | 32 | 2 |
| Outcome-aware two-line ceiling | 289 | 41.17% | 126 | Not executable |

Strict margin requires one norm >1.2 times its threshold and the other <0.8 times
its threshold. It tests boundary sensitivity; it does not authenticate replication.
The oracle can choose both lines and is consequently more permissive than a
hub-constrained adaptive policy.

Paired compound-bootstrap differences, percentage points, with descriptive 95% CIs:

- RKT minus fixed pair: **+3.56 [0.28, 6.84]**; strict margin **+0.43 [-1.57, 2.42]**.
- RKT minus norm-neighbour: **+2.14 [-0.57, 4.84]**.
- RKT minus empirical feedback: **+4.42 [1.71, 7.26]**.
- RKT minus shuffled packets: **+3.85 [1.00, 6.70]**.

These five comparisons are exploratory, not a multiplicity-controlled confirmation
family. Packet shuffling is a model-information control, not a causal test of LLM
feedback use. Different compounds' missing entries fall back to empirical estimates.

For unmeasured contexts after the hub observation, RKT activity Brier loss is 0.0959,
against 0.1177 for conditional empirical and 0.1070 for norm-neighbour prediction.
AUROCs are 0.868, 0.813 and 0.852. RKT active-response cosine is 0.540, against its
expected 0.555. This supports useful model information. It does not establish that
the extra simulated turnaround is worth 25 additional threshold-discordant findings,
especially when only three extra findings survive the strict margin.

## 5. Autonomous reasoning pilot and direct interaction test

The protocol selected 84 compounds by a fixed hash without activity filtering, grouped
into 12 batches of seven. Each LLM arm gets two calls per batch: hypotheses and
evidence gaps before feedback, followed by revised memory and second-line selection.
All arms see the same identities, annotations, tissue descriptions, source cards,
empirical probabilities and acquired hub results. C lacks RKT fields. D and E see
identical RKT probabilities, conditional accuracy and refusals. D uses conventional
scientific tool reasoning; E explicitly requests competing explanations, evidence
gaps and model-failure critique. Both have persistent context and identical call limits.

The pilot reuses `DeepSeekChatClient`, `SpendLedger`, `CaseStore`, `EvidenceAction`
and `MeasurementResult`. CaseStore holds 36 cases and 504 retrieved-source receipts,
with plan versions, two acquisitions per compound and final deferred status because
causal interpretation remains unsupported. Independent-unit counts stay unknown.
Requests, hypotheses, revised memory, choices and source citations are cached.
Successful outputs and imported observations support resumption without new spend.

| Matched pilot policy | Discordances / 84 | Strict-margin discordances |
|---|---:|---:|
| A: empirical feedback | 9 | 3 |
| Strong fixed pair | **16** | **5** |
| Norm-neighbour feedback | 12 | 2 |
| B: deterministic RKT | 15 | 2 |
| C: agent without RKT | 14 | 3 |
| D: conventional LLM with RKT | 12 | 1 |
| E: integrated hypothesis/revision agent with RKT | **10** | **1** |

No invalid selections required fallback. The integrated arm chose the deterministic
RKT second line on only 21/84 compounds; the conventional arm did so on 18/84.
A post-hoc trace audit found objective drift: for example, the integrated arm's
batch 1 rationale seeks high RKT activity for an already active R-428 observation,
although the registered objective needs an inactive second line. Other choices invoke
lineage diversity or expected cosine where opposite activity was the endpoint.
This is an illustration of failure, not an exhaustive hallucination classification.

Planned contrasts use 12 prompt-batch clusters, exact sign flips, and Holm correction
across four one-sided comparisons. Percentage-point differences with 98.75% bootstrap
intervals:

| Contrast | Difference | Interval | Holm-adjusted p |
|---|---:|---:|---:|
| E minus C | -4.76 | [-13.10, 5.95] | 1.00 |
| E minus D | -2.38 | [-8.33, 3.57] | 1.00 |
| E minus strongest pilot deterministic/fixed arm | -7.14 | [-15.48, 2.38] | 1.00 |
| (E-C) minus (B-A) | **-11.90** | **[-26.19, 0.00]** | **1.00** |

The interaction is an operational comparison, not proof of a general causal agent/VC
interaction: baseline policies and representations differ. Selection of the strongest
pilot comparator is descriptive. Small sample size and shared plate/source dependence
limit inference. The result supports **no demonstrated gain**, not a universal claim
that LLM reasoning harms biology.

This pilot still asks the LLM to connect scientific reasoning to a small numeric action
menu. It therefore cannot rule out value in tasks requiring new source discovery or
orthogonal mechanism adjudication. No live literature tool, knowledge-shuffle or
agent-memory ablation was run after the negative primary pilot; more calls were not
justified. Source cards are not evidence of autonomous literature search.

## 6. Cost, verification and integrity

There were 72 logical requests, **71 billable-request attempts**, and one exact cache
reuse. Provider usage records total 199,554 prompt tokens and 27,648 completion tokens.
Official Flash off-peak pricing gives an estimated **USD 0.03996**; applying peak
rates gives USD 0.07991. Neither is an invoice. The existing historical cost utility
does not price Flash, so it conservatively retains USD 0.71 in reservations under
the pilot's USD 1 cap and the user's USD 10 ceiling. No expensive model was called.

Deterministic preparation took 36.88 seconds; the three-arm pilot took 67.36 seconds
with three concurrent request workers, not subagents. Literature retrieval, auditing
and test time are additional. Each full-library arm used 1,404 replay slots; each
pilot arm used 168. Actual laboratory experiments, wells and turnaround were **zero**.
Hypothetical laboratory rounds are reported separately and have no authenticated
monetary or elapsed-time price.

`verify.py` checks frozen study code/protocol and input hashes, all 4,212 deterministic
choices, 252 agent choices, measured outcome scoring, 504 CaseStore receipts, prompt
information boundaries and API accounting. It passed. The default repository suite
passed **808 tests** in 46.85 seconds. Block Q's own verifier also passed.

The pre-existing repository shape test rejected even the committed Block Q folder.
It now requires explicit registration in `research/STUDIES.json`, protocol and
verification files, unique direct child paths, and a freeze for frozen studies.
This is the only existing test code changed; no production scientific code changed.

The first deterministic attempt encountered an empty-batch prediction error before
completing any new policy evaluation. A two-line empty-query guard fixed it before
the implementation freeze; the failed log is retained. The protocol was written
after aggregate feasibility counts had been inspected. API prompts were frozen after
deterministic feasibility, before API calls. Both timing facts prevent a fresh
confirmatory interpretation. See `DEVIATIONS.json`.

## 7. Decisions and the next scientifically justified gate

**Retain:** validated RKT and sparse-hub defaults within their existing scope.

**Keep in research:** task-specific RKT acquisition, conditional empirical and
norm-neighbour controls, all source/trace audits and negative results. The ordinary
threshold endpoint has modest headroom; robustness and turnaround value are unresolved.

**Reject promotion:** this integrated hypothesis/revision selector. It adds no
demonstrated yield, and its scientific prose can drift away from the observable objective.
Do not repair the result by adding calls or selecting a favorable subset.

**Defer:** new activity calibration, large knowledge-graph models, dynamic virtual-cell
simulation and RNA-to-viability claims. None was validated here.

**Next opportunity, conditional on data availability:** a model-failure investigation
where the agent can retrieve a genuinely additional, source-qualified observation
that distinguishes two explicit explanations, for example target-specific response
versus generalized stress using matched genetic perturbation and an orthogonal
protein/functional endpoint. The world model should estimate context transfer and
identify its disagreement; the agent should locate and qualify missing evidence;
deterministic code should compute information value and terminal decisions. Freeze
the endpoint, full candidate population, independent culture/plate units, first-stage
data access and matched retrieval/acquisition budgets before outcomes are opened.

No independently suitable unexposed dataset was qualified in this study. Existing
GSE70138, PRISM and prior MAESTRO confirmation outcomes cannot supply that gate.
Until a distinct observable and adequate independence exist, a larger autonomous
agent experiment is scientifically premature.

## Reproduction

From repository root, with existing Block Q source assets and research dependencies:

```powershell
python research/context_discrimination_20261013/experiment.py
python research/context_discrimination_20261013/agent_pilot.py
python research/context_discrimination_20261013/analyze.py
python research/context_discrimination_20261013/verify.py
python -m pytest
```

The first command reads exposed outcomes and rebuilds the local replay cache. The
second resumes saved traces/cached responses; deleting caches can cause paid calls.
For a read-only audit of the delivered results, run only `verify.py`. The full-data
cache and SQLite state are local ignored artifacts. Missing source assets are a
reproduction prerequisite, not permission to fabricate replacements.
