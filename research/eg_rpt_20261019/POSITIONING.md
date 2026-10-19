# EG-RPT positioning and evidence audit (proposal; no experimental result)

Study: `research/eg_rpt_20261019`. HEAD `c9f169c6`, clean tree at the start. **EG-RPT (Evidence-Grounded Research Policy Transfer) is a proposed
direction, not a validated method.** Nothing here claims that policy transfer, a Virtual Cell reliability layer or an agent improves drug-discovery decisions.

## 1. Evidence table (what is supported, unconfirmed, failed, blocked)

Numbers are checked against `research/EVIDENCE.md` text; three are recomputed from result files (`EXPERIENCES_CHECK.json`, 13 records, all valid).
Units are not comparable across rows.

| Class | Statement | Source / tier |
|---|---|---|
| Supported within a replay | Feedback propagates to unmeasured pairs: ridge-plus-feedback − prior +1.056 [+0.626, +1.526] events/64 at 3 pool reads | feedback_propagation, exposed PRISM |
| Supported within a replay | Feedback on Beat AML: ridge-plus-feedback − drug ridge +0.083 [+0.042, +0.127] hits/16 queries | beataml_g1, exposed |
| Supported, narrow | Exploit-first bridge feedback +0.073 (workflow within Beat AML, not biology) | context_transfer |
| Supported, scoped | VC transcriptional transfer +0.116 [+0.053, +0.181] over target kNN for unseen classes; adds only on a 160-line screen, not 40 lines | Block N, sealed tier already used |
| Unconfirmed | Seed library policy +0.356 [−0.088, +0.856]; a ridge on the same ten features matches it | seed_attribution |
| Unconfirmed (lead) | Non-LLM target-gene state rule − random +0.037 [+0.003, +0.075], unadjusted | observable_state, exploratory |
| Failed / not supported | Lookahead − fixed −0.106 [−0.262, +0.022]; agent − lookahead +0.008 [−0.033, +0.054]; held-out headroom of the second-pool choice +7.3% | acquisition_program |
| Failed / not supported | R1 repair − ridge+feedback +0.139 [−0.579, +0.870] (development +0.81 did not replicate) | feedback_propagation |
| Failed gate | Low-rank candidate − ridge +0.098 [+0.045, +0.153], net lower bound −0.005 | beataml_g1 |
| Withdrawn | Agent claim and typed-edit thesis (confirmation 0.081 vs enumerator 0.059 vs random 0.051; agent − enumerator +0.022 [−0.022, +0.074]; stated p 0.45 vs 0.081) | observable_state |
| Not tested | Decision utility of any edit (S2); policy-transfer across tasks; any independent confirmation | — |
| Blocked | Independent confirmation: all local PRISM tiers are exposed; sealed PRISM 24Q2 needs authorisation | — |

**Reading of the null result (precision):** a random confirmation rate of 0.051 shows the confirmation test sat near its nominal level in this setting, not that
power is adequate for every effect; the agent margin (+0.10) was excluded for this vocabulary, split and one-edit-per-family design only. The target-gene
rule is a lead, not a finding.

### New audit finding: the campaign-level "best-of" headroom is not identified
`NOISE_HEADROOM.json` (36 complete 64-compound campaigns, public records): best-of-two excess over the mean of ridge and R1 is exactly Σ|d|/2 = 33.5
hits (the 131-vs-100 figure). The observed mean |d| is 1.86 against 1.95 expected if d were pure Gaussian noise with the same SD (2.44), and the two
predictors' hit counts correlate only 0.27 across campaigns. A second probe-noise draw earlier moved R1 − ridge as much as the interval. So **policy-selection
headroom between update rules is unidentified**, and the earlier "hindsight" figures must not be read as a ceiling on what a policy chooser can gain. Phase 0 of
the protocol makes a split-noise reliability test the first gate.

### Feasibility of learning policy transfer from the repository's own history
13 records, 4 dependence groups (PRISM 19Q4, Beat AML, L1000/GSE70138, PRISM-L1000), 6 incommensurable utility units: far too little to fit a learned
transfer model. The honest first step is therefore a **generated** panel of tasks with fully observed per-task policy utilities (replay), not learning from the
13 study-level records.

## 2. Prior art (verification level stated)

Verified from search results and abstracts only unless marked; full texts were not read.

| Lead | Identity | What it establishes | Does not establish for drug-discovery policy transfer |
|---|---|---|---|
| AI Scientist-v2 | arXiv 2504.08066 | Agentic tree search over experiments and paper writing; its objective is manuscript quality | Drug-discovery utility |
| Google AI co-scientist | arXiv 2502.18864 | Generate/debate/evolve hypotheses with tournament ranking; expert and wet-lab checks in three biomedical areas | That agent consensus tracks experimental utility; transfer across tasks |
| STATE / Virtual Cell Challenge | Arc Institute page and bioRxiv (June 2025); 2026 challenge is zero-shot to unseen cell contexts | Embedding + transition model for perturbation response; benchmark framing | Calibration, refusal, or decision value; numbers read from news/Arc pages |
| Tahoe-100M | bioRxiv 10.1101/2025.02.20.639398 | ~100M cells, public since Feb 2025 (drug count differs between sources: unverified) | Independence: public data used for model development cannot also be independent confirmation |
| DreamerV3 | arXiv 2301.04104 | World-model planning, one configuration, 150+ tasks | Any biological transfer (a hypothesis) |
| pi0.5 | arXiv 2504.16054 (CoRL 2025) | Co-training on heterogeneous tasks generalises to new homes | Biological analogue (interface idea only) |
| SAMPLE | Nature Chemical Engineering 2024 (DOI 10.1038/s44286-023-00002-4) | Closed design-test-learn loop with a robotic lab; four agents converged on thermostable enzymes | Cost-matched drug policy transfer |
| Perturbation benchmarks | Nature Methods 2025 (DOI 10.1038/s41592-025-02772-6): deep models did not beat simple linear baselines | Baseline discipline | The 2026 "in-the-wild" preprint named in the brief was **not found** |
| Batch / adaptive design | BATCHIE (Nat. Commun. 2025), PS-BAX (arXiv 2410.20596), MDA, AHOIS, AIRA2, AssayLoop | see `observable_state_20261018/POSITIONING.md` | abstract level only |

## 3. What EG-RPT would have to show to be more than a relabelling

Not "LLM + Virtual Cell + memory + active learning". The testable difference: a **policy choice conditioned on evidence about similar past tasks and on a Virtual
Cell reliability report**, evaluated on tasks not used to build the memory, against (a) a single fixed best policy, (b) a non-LLM meta-selector on the same task
descriptors, and (c) the strongest task-specific rule, at comparable total cost. Existing systems (Co-Scientist, AI Scientist-v2, AssayLoop, MAP-style amortised
policies) address hypothesis generation, paper-level search or amortised acquisition on one assay family; none is shown to transfer *research procedures* across drug
tasks with failure-aware applicability. That remains **unverified and untested**; and our own record (agent null in five studies, headroom unidentified) makes a
positive result unlikely without a task panel where policies genuinely differ.
