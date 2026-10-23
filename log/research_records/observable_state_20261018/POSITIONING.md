# Research positioning: observable, decision-sufficient response states

> Historical proposal written against an earlier repository state. The completed test narrowed and rejected the Agent/typed-edit claim for this arena; consult [`REPORT_OBS.md`](REPORT_OBS.md) for the current evidence and [`NOVELTY_REVIEW.md`](NOVELTY_REVIEW.md) for the proposal's literature/repository review.

Study: `research/observable_state_20261018`. Status: **proposal for review; no result.** Written 2026-10-18 against HEAD
`3c6f8f1f`. Nothing here is an experimental finding, and nothing claims a new response state.

## 1. What the repository already shows (checked against records)

All quoted numbers reproduce from `acquisition_program_20261018/RESULTS.json` and `HINDSIGHT_CLARIFICATION.json`
(`PRIOR_CHECK.json`, 14 of 14 match).

| Class | Statement | Source |
|---|---|---|
| Supported within a defined replay | Feedback propagates to unmeasured pairs: ridge-plus-feedback − prior +1.056 [+0.626, +1.526] events/64 compounds; the no-feedback prior is 0.931 against 1.822 for the fixed design | `feedback_propagation_20261018`, `acquisition_program_20261018` |
| Exposed-data development | One-step lookahead beat the fixed design in development (337 vs 305 events) | `acquisition_program_20261018` DEV_BASELINES |
| Unconfirmed / reversed | Held-out lookahead 1.717 vs fixed 1.822 (−0.106 [−0.262, +0.022]); agent incumbent 1.725 (−0.097 [−0.232, +0.026]; vs lookahead +0.008 [−0.033, +0.054]) | RESULTS.json |
| Stopped method claims | R1 repair of propagation (P1 +0.139 [−0.579, +0.870]); low-rank state model on Beat AML (G1); PRISM seed-arena revision/stepwise/LLM/grammar search | their studies |
| Independent confirmation | **None.** Every PRISM tier is exposed; sealed tiers stay closed | `research/EVIDENCE.md` |

Headroom, in the Section-3 language of the brief: the second-pool choice had **+7.3% held-out hindsight headroom
(704 vs 656 events) against +34% in development** (410 vs 305). That is a low-H task and a development lead that reversed
on held-out groups. It argues for changing the action abstraction, not for more proposals.

## 2. Prior art: what is verified and what is not

Verification level is stated honestly: I read **search results and abstracts**, not full texts, in this session.

| Lead | Primary identity found | What it establishes | What it does *not* establish for drug discovery |
|---|---|---|---|
| AI Scientist-v2 | arXiv 2504.08066 | Agentic tree search over experiments and manuscripts; one workshop paper above the average acceptance threshold | Any wet-lab or drug decision value |
| AlphaEvolve | arXiv 2506.13131 (summaries only) | LLM + automated evaluator evolving programs | A scientific abstraction edit language |
| Darwin Gödel Machine | arXiv 2505.22954 | Self-modifying coding agents validated on coding benchmarks, archive-based | Biological transfer |
| AIRA₂ | arXiv 2603.26499 (version-dependent numbers) | Search labels hidden from the agent; a validation set used only for final selection; "overfitting" largely evaluation noise | Domain with real cost and cluster dependence |
| Model Discovery Agent | arXiv 2608.09696 | LLM-proposed model structures tested with Bayesian experiment design on physics, chemistry, a neuron benchmark | Drug response; cluster-dependent campaigns |
| AHOIS / Socratic agents | arXiv 2606.26722 | Hypothesis / Socratic-critic loop on a multimode-fibre platform | Anything biological |
| AssayLoop / AssayFormer | arXiv 2609.11877 | Amortised acquisition across 1,389 CRISPR screens, with an LLM-prior handoff | Drug-response campaigns; typed model edits |
| Learning to Measure (meta-AFA) | search found an L2M meta adaptive-feature-acquisition paper; I did not confirm it is the one meant | In-context acquisition across tasks | Same |
| BATCHIE | bioRxiv 10.1101/2023.12.18.572245; Nature Communications 2025 | Prospective Bayesian batch design for combination screens | A learned research abstraction; no agent |
| PS-BAX | arXiv 2410.20596 (NeurIPS 2024) | Posterior-sampling design for target-set properties | Drug screening validation |
| R-IDeA | arXiv 2506.07805 | Representative, informative and error-de-amplifying acquisition under misspecification | Drug data |
| Systema | Nature Biotechnology 2025, doi 10.1038/s41587-025-02777-8 (secondary summaries read) | Systematic variation inflates perturbation-response metrics; simple baselines match models | Drug campaign decisions |
| TxPert | arXiv 2505.14919 | Graph-prior generalisation to unseen perturbations / cell lines | Edit-based revision |
| **Not found by search** | AIDE², EvalResearchBench, "Learning to Outgrow a Theory", MIST-WM, CMonge; "MAP" is ambiguous (the repo also holds an unrelated `data/external/MAP`) | — | Do not cite or build on these until located |

Consequences: the *method* ingredients (tree/evolutionary search, hidden-selection splits, Bayesian experiment design,
amortised acquisition, misspecification-aware acquisition, metric-inflation controls) all exist. Applying them to drugs is
**not** novel by itself.

## 3. The gap, and why this is not just AutoML, active learning or a bigger Virtual Cell

The testable gap is narrower than "agent + virtual cell". It is the conjunction of three requirements on a *state
abstraction* rather than on a model or a policy:

1. The edit is a typed scientific change with competing, pre-registered predictions and a discriminating assay (MDA and
   AHOIS do this on physical systems; nobody has shown it on a cost-constrained drug campaign with cluster-dependent data).
2. It is judged on **decision utility and assay cost**, not prediction error: this repository has direct evidence that prediction
   improves without decisions improving (R1: error lower in 3 of 3 folds, utility +0.139, CI crossing zero).
3. It is judged on **transfer to new chemical families, contexts and campaigns**, with a role-gated hidden-outcome
   interface (search / select / transfer) so the agent cannot tune against the held-out signal.

Why each cheaper reading fails to cover it:

* **AutoML / program search**: searches a space chosen in advance; the repository has already shown that grammar search over
  this space does not help when headroom is +7%. A typed *scientific* edit changes what is represented and what is measured.
* **Active learning / BATCHIE / PS-BAX**: choose experiments for a fixed model class. They are *baselines* here, not the
  contribution. The question is whether a revised state definition beats them at equal assay budget.
* **A stronger Virtual Cell**: gains in prediction need not change decisions (above). The Virtual Cell is an editable
  response-world model whose *consequences* feed decisions; it is not the claim.
* **Generic model revision**: revision without a discriminating experiment and rejection condition is what failed in the
  PRISM seed arena (revision added 0).

The honest status: the gap is a hypothesis about what could work; the repository's own evidence (negative on the same arena)
makes a positive result *less* likely than the brief's aspirations, and the power table (`POWER.json`) shows which
contrasts can be resolved at all.

## 4. What remains untested

Whether any compact state exists that (a) changes a downstream nomination, (b) is identified by a legal assay program at
affordable cost, and (c) transfers across families and lineages. All three are open. No PRISM tier is independent, so the
best the planned study can deliver is an *internal development assessment*; confirmation needs independent data.
