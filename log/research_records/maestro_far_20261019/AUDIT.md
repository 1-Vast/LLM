# MAESTRO-FAR current-state audit (2026-10-19)

Labels: **Observed** = executed, auditable analysis in the repository; **Draft** = recorded, not frozen, reproduced or validated; **Proposed** = future hypothesis, threshold or design.
Nothing in this folder is a result of MAESTRO-FAR. No outcome matrix, sealed tier, download, LLM call or test run was used in producing it.

## 1. Repository state
Branch `main`, HEAD `cc73c1d9` ("Add EG-RPT policy transfer draft", committed by the user after the previous turn), working tree clean at the start of this audit.
EG-RPT is therefore committed but **Draft**: not frozen, not run, no estimate of any policy-transfer effect. Its only analytical output is the noise diagnostic below.

## 2. Evidence the proposal rests on (all on exposed data; development only)
| Item | Label | Value (interval) | What it does and does not support |
|---|---|---|---|
| Beat AML G1: candidate − ridge | Observed | +0.098 [0.045, 0.153] | feedback matters; strict gate lower bound −0.005 net of a round |
| Beat AML G1: low-rank prior − ridge | Observed | −0.027 [−0.065, 0.011] | no validated low-rank latent-state advantage |
| Beat AML G1: ridge+feedback vs candidate | Observed | +0.015 [−0.036, 0.066] | feedback, not the latent state |
| Beat AML attribution: engine vs ridge | Observed | ≈ +0.023 (not significant); same-PC ridge ≥ RNA prior | extra prior unproven |
| Seed attribution: repaired seed policy | Observed, unconfirmed | +0.356 [−0.088, +0.856]; ridge on same ten features −0.004 | seed signal unconfirmed |
| Feedback propagation: ridge+feedback − prior | Observed | +1.056 [0.626, 1.526] | feedback propagates to unmeasured pairs |
| Feedback propagation: R1 − ridge | Observed | +0.139 [−0.579, +0.870] | R1 may help error, not decisions |
| Acquisition: fixed / lookahead / agent | Observed | 1.822 / 1.717 / 1.725 | no agent or lookahead advantage here |
| Observable state: random / enumerator / target gene / agent | Observed | 0.051 / 0.059 / 0.088 / 0.081 | typed-edit claim withdrawn; target-gene rule is an unadjusted lead; agent stated confidence ≈0.45 |
| EG-RPT noise diagnostic | Observed (descriptive) | mean abs. ridge/R1 difference 1.86 vs 1.95 expected under noise; hit-count correlation 0.27 | the 131-vs-100 best-of figure is not evidence of selectable headroom |
| EG-RPT 13 records | Draft | 4 dependence groups, 6 units | too few for a transfer policy; retrieval only |
| Phase 0 edge counts (this folder) | Observed (labels) | see §4 | identity overlap only |

Scope limits that must stay attached: a nominal 5% random-edit rate does not show that all edit effects are small; the agent failures describe the evaluated arena (PRISM 19Q4 folds, one-edit vocabulary, Beat AML, exposed data), not agents in general; a failed hypothesis retires that hypothesis.

## 3. What is implemented and reproducible
Reusable: `observable_state_20261018` (masked interface with role caps and write-once ledger, typed `ResearchEdit` with competing-explanation and rejection-condition validation, decision-weighted discrimination and a robust objective, campaign core, baselines), `feedback_propagation_20261018` (ridge, kNN, R1, records), `acquisition_program_20261018`, `eg_rpt_20261019` (experience records, reliability-gated choice). None of it implements a Virtual Cell failure atlas, an orthogonal-assay action set with a utility evaluator for FAR, repair primitives, or a certificate schema. Those are **Proposed**.

## 4. Data access, provenance, compute (Phase 0, metadata only; `EDGES.json`, `qualify_edges.py`)
* **PRISM 19Q4 − L1000 (GSE92742):** 1,805 unique overlapping compounds (earlier 1,845 counted cells before the PRISM-line filter), 1,783 with an MoA label, 496 distinct MoA labels (115 with ≥5 compounds), 6 lines with ≥300 overlapping compounds spanning 6 tissues. Passes the **proposed** counts (≥300 perturbations, ≥8 MoA groups) on identity overlap. Remaining mismatches: 5-day viability versus 6/24 h transcription, ~2.5 µM versus mostly 10 µM, 13-character Broad-id matching without structure check. The intersection and sealed GSE70138 were used in blocks N/P/Q, so use here is development.
* **JUMP / Cell Painting:** `data/external/jump_target` is empty; no precomputed profiles are local. This edge is **blocked**. No raw imaging download was started.
* **DepMap features:** present (591 MB); they supply line features, not an outcome-assay edge.
* Fewer than two outcome edges qualify, so per the brief the pilot uses the strongest feasible edge (PRISM→L1000 transcriptional readout plus DepMap features) and the limitation is reported; this is not a failure of the direction.
* Compute: CPU only; dependencies as in existing studies (the Anaconda Python carries pandas; Python314 carries the Block Q pickle). No new dependency or dataset is needed for Phases 0-3.
* External confirmation: no unexposed independent source is cleared; sealed PRISM 24Q2 needs authorisation. Phase 7 is **blocked**.
