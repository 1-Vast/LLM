# Block Q: routed knowledge transfer and certificate-planned profiling (2026-10-12)

**Headline: `PARTIAL`.**
* **Virtual-cell claim: `CONFIRMED`.** It passed all three primary hypotheses (P1-P3).
* **Decision claim: `NOT_CONFIRMED`.** P5 and P7 passed; P4 and P6 failed.

Run details:
* frozen 2026-10-12T12:24:32Z (`FREEZE.json`, 34 files);
* run once on the sealed GSE70138 tier; `verify.py`: VERIFIED;
* no deviations (`DEVIATIONS.json`).

Protocol: `PROTOCOL.md`. Disclosure: `DISCLOSURE.md`.

## What was tested

Two papers motivated a virtual cell that transfers biological knowledge to compounds never
profiled:
* PRESAGE (Littman et al., bioRxiv 2025): knowledge-source encoders; cross-system Perturb-seq is the
  strongest source;
* MAP (Feng et al., Nat. Mach. Intell. 2026): a 694k-edge drug-gene knowledge graph with
  multimodal pretraining for unprofiled drugs.

**The virtual cell: RKT, routed knowledge transfer.** RKT keeps each knowledge source as a typed
route:
* **context**: the same compound in other lines, through ridge line-to-line maps;
* **phenotypic analogues**;
* **structural analogues**;
* **knowledge analogues**: Repurposing Hub targets and mechanisms plus signed MAP-KG edges.

How a prediction is built:
1. Each route gets its own meta-model certificate: the expected specific cosine after the line's
   generic response is removed.
2. The routes are pooled by those certificates.
3. The prediction is decomposed as γ·generic + ρ·√(1-γ²)·specific.

That decomposition has two uses. It gives an analytic expected accuracy, and it lets a query refuse
the specific direction by name (`SPECIFIC_DIRECTION_UNSUPPORTED`, `NO_TRANSFER_ROUTE`).

**The agent layer.** An equal-well campaign completes a compound x line map. The `maestro` planner
spends wells by certificate value of information, which counts both direct gain and transfer gain to
the compound's other lines. It was compared against:
* fixed designs, including PRESAGE's untested "sparse across systems" claim;
* route-blind and activity-greedy adaptive planners;
* three deepseek-flash agents.

## Confirmation tier

| Item | Value |
|---|---|
| Library | 702 GSE70138 compounds absent from GSE92742 (28 structure duplicates excluded), 4,808 cells |
| Lines | 7 |
| Active cells | 1,105 (23%) on 348 compounds |
| Reference atlas | 979 compounds |
| Campaigns | 11 of 63-64 compounds |
| Primary budget | one well per compound |

## Results

### Prediction tier

Centred cosine on active cells, with the compound as the unit:

| Regime | RKT pooled | Generic | Best single route | Monolithic ridge | Expected (certificate) | Refused |
|---|---|---|---|---|---|---|
| A: all other lines visible | 0.585 | 0.287 | context 0.598 | 0.318 | 0.584 | 0.1% |
| **A1: one line visible** | **0.529** | 0.287 | context 0.510 | 0.318 | 0.547 | 0.3% |
| B: never profiled | 0.360 | 0.287 | knowledge 0.262 (84% coverage) | 0.318 | 0.394 | 45% |

**Primary hypotheses (Bonferroni one-sided α = 0.00714):**
* **P1** (pooled vs generic, A1): **PASS**, +0.218 [+0.202, +0.235]; 320 compounds favour, 26 oppose.
* **P2** (pooled vs the context route, A1): **PASS**, +0.033 [+0.015, +0.052]; p = 0.0003.
* **P3** (certificate ranks errors better than applicability distance, A1): **PASS**. AURC 0.347
  against 0.428; difference +0.081 [+0.055, +0.102].

**Secondary results.**
* **Regime B, versus generic (V2a):** +0.050, PASS.
* **Regime B, versus the monolithic PRESAGE-style ridge (V2b):** +0.025, PASS.
* **Regime B, certificate AURC (V3B):** +0.091, PASS.
* **Regime A:** pooling does not beat context alone (+0.004, p 0.30).
* **Activity AUROC:** 0.89 (A), 0.85 (A1), 0.64 (B).

**Exploratory: CRISPR knockout genetic route.** Specific cosine 0.078 at 19% coverage. It is weak,
but above the shRNA route on development (0.027).

### Campaign tier

Utility at W = N: the mean over truly active cells, where a profiled cell earns 1 and an unprofiled
cell earns the centred cosine of its fill.

| Arm | Utility | Turnarounds |
|---|---|---|
| oracle (reference) | 0.910 | 4 |
| `sparse_hub` (fixed, transfer-informed) | **0.623** | 1 |
| `maestro_static` | 0.602 | 1 |
| `sparse_random` (PRESAGE sparse design) | 0.592 | 1 |
| `maestro` (certificate value of information) | 0.579 | 4 |
| `maestro_llm` (bounded LLM override) | 0.565 | 4 |
| `llm_conv_vc` (ReAct agent + VC tools) | 0.555 | 4 |
| `activity_greedy` | 0.545 | 4 |
| `llm_no_vc` (agent without VC) | 0.517 | 4 |
| `ad_uncertainty` | 0.497 | 4 |
| `dense` (PRESAGE exhaustive design) | 0.442 | 1 |
| `vc_only` (no wells) | 0.359 | 0 |
| `generic` (no wells) | 0.286 | 0 |

**Primary hypotheses** (exact sign-flip over 11 campaigns, so the smallest attainable p is 1/2048):

| Id | Contrast | Verdict | Difference | Campaigns favouring | p |
|---|---|---|---|---|---|
| P4 | `maestro` > `sparse_hub` | **FAIL** | -0.044 | 0 of 11 | |
| P5 | `maestro` > `activity_greedy` | **PASS** | +0.034 | 10 of 11 | 0.001 |
| P6 | `maestro` > `llm_conv_vc` | **FAIL** | +0.024 | 8 of 11 | 0.029 (above 0.00714) |
| P7 | `sparse_hub` > `dense` | **PASS** | +0.181 | 11 of 11 | 0.0005 |

P7 confirms PRESAGE's design claim; `sparse_random` also beats `dense` (C6: +0.151, 11 of 11).

**Secondary contrasts.**
* **C3b:** `maestro` > `ad_uncertainty` +0.082, PASS.
* **C4b:** the VC inside a conventional agent, `llm_conv_vc` > `llm_no_vc`, +0.038 (8 of 11),
  p 0.027, PASS.
* **C5:** the LLM override against `maestro` is -0.014, two-sided p 0.098. No difference was
  detected, and the direction is negative, as predicted.
* **C8:** `maestro_static` < `sparse_hub` (-0.021), FAIL.
* **At 2N:** `maestro` beats `sparse_hub` +0.053 (10 of 11, p 0.0015); certificates pay once every
  compound can be covered.
* **At 0.5N:** the arms are level.

**Provider spend:** $0.32 over 214 calls, separate from wells.

## Interpretation

1. **The virtual cell transfers.** Routed, certified transfer from a single profiled line predicts a
   new compound's response in the other six lines:
   * far better than the systematic response (0.53 against 0.29);
   * better than its strongest route;
   * better than a monolithic knowledge-feature model.

   The certificate is close to calibrated (expected 0.547 against realised 0.529), and it ranks
   errors better than nearest-analogue similarity. On never-profiled compounds the gain is real but
   small, and almost half of queries correctly refuse a specific direction.
2. **Coverage beat cleverness at one well per compound.** The fixed design that profiles every
   compound once, in the line that transfers best, beat every adaptive planner. That includes the
   certificate planner and all LLM agents, and the fixed design needs a quarter of the turnaround.

   This is a post-hoc reading, labelled exploratory in `DEVIATIONS.json`. The confirmation library
   was three times as active as development (23% against 7%), and certified P(active) is
   under-predicted and weakly ranked for compounds with no profiled line (AUROC 0.64). Those are the
   conditions in which concentrating wells loses to coverage.
3. **LLM components.** A conventional ReAct agent gained from being given the virtual cell
   (+0.038). It did not beat the deterministic planner at the family-wise level, and a bounded LLM
   override of the planner did not help. This repeats blocks N and P.

## Promoted

| Module | Content |
|---|---|
| `src/virtual_cell/knowledge_transfer.py` | The RKT core: atlas, routes, certificates, refusals, transfer table, certifier fit with lazy scikit-learn. Parity with this study's code is at float32 rounding (direction max diff 5e-8). |
| `src/maestro/transfer_value.py` | `sparse_transfer_design` (default, the confirmed coverage design); `profiling_value` / `plan_batch` (the value-of-information planner, documented as beating adaptive baselines at N and the fixed design only at 2N, secondary). |
| `src/agent/profiling.py` | The campaign runner: state, certification, design or planner, replanning, wells and turnarounds. |
| `tools/evaluation/transfer_metrics.py` | Specific cosine, AURC, compound-clustered tests, map utility. |

## Files

| Group | Files |
|---|---|
| Frozen code | `rkt.py`, `engine.py`, `pool.py`, `campaign.py`, `llm_arms.py`, `metrics.py`, `confirm.py`, `verify.py`, `verify_freeze.py` |
| Records | `PROTOCOL.md` / `.json`, `DISCLOSURE.md`, `FREEZE.json`, `RESULTS.json`, `DEVIATIONS.json`, `results/` (rows, LLM cache, spend ledger), `confirm_run.log` |
| Development scripts | `dev_*.py`, `extract_*.py` |

Large caches (`cache/*.npz|npy|pkl`) are local and git-ignored. Their hashes are in `FREEZE.json`.
