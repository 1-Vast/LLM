# Block Q protocol: routed knowledge transfer and certificate-planned profiling

Pre-registered before the sealed tier is opened. `PROTOCOL.json` is the machine-readable form of
the hypotheses. `DISCLOSURE.md` lists everything seen before the freeze. Deviations go to
`DEVIATIONS.json`, which is not frozen.

## Question

Two questions, one per tier.

**Prediction tier.** Can a virtual cell that transfers biological knowledge along typed routes,
each certified separately, predict the transcriptional response of compounds never profiled in a
reference atlas? It must:
* beat the systematic baseline;
* beat its strongest single route;
* rank its own errors better than applicability distance does.

**Campaign tier.** Do its certificates, used as value of information, let an autonomous profiling
agent complete a compound x line response map with the same number of wells better than the
following?
* fixed designs, including PRESAGE's "sparse across systems" design;
* route-blind and activity-greedy adaptive planners;
* a conventional LLM agent given the same virtual cell as tools.

## Data

| Role | Content |
|---|---|
| Development (open, used for every choice) | GSE92742, 7,760 compounds, nine lines, 10 uM / 24 h, level-5 consensus per compound x line |
| Reference atlas | The 979 GSE70138 compounds that also have a phase-1 response, at 10 uM / 24 h in seven lines (A375, HA1E, HELA, HT29, MCF7, PC3, YAPC) |
| Library (sealed until freeze) | GSE70138 compounds absent from phase 1, with three exclusions below; 702 compounds and 4,808 cells by metadata |

Library exclusions:
* `DUPLICATE_OF_PROFILED`: the InChIKey connectivity block matches a compound profiled at
  10 uM / 24 h in either release (28 compounds);
* fewer than five profiled lines (4 compounds);
* a cell counts only if metadata lists a signature **and** the sealed file holds a response.

**Activity.** A cell is active when its response norm exceeds the line's 95th percentile of
phase-2 24 h vehicle norms.

**What is fitted where.**
* The meta-models (`cache/pooler_all.pkl`) are fitted on the phase-1 development route table,
  nested by compound fold.
* The generic directions, γ, the ridge transfer maps and the transfer table κ are re-estimated on
  the reference atlas. No library response enters any fitted quantity.

## Virtual cell (RKT, `rkt.py`, `pool.py`, `engine.py`)

**Routes.** Each route reads references only (and the query compound's own visible lines):
* *context*: ridge maps from the same compound's profiled lines;
* *phenotypic analogues*: cross-line cosine kNN;
* *structural analogues*: Morgan Tanimoto kNN;
* *knowledge analogues*: Jaccard kNN over Repurposing Hub targets and mechanisms plus signed MAP-KG
  drug-gene edges.

The genetic route (signed knockdown or knockout consensus) is reported but not admitted; on
development its specific cosine was 0.027.

**Prediction.** A prediction is γ·g_T + ρ·√(1-γ²)·s, where:
* g_T is the line's generic active direction;
* s is the certificate-weighted pooled specific direction, with weights ρ_r / (1-ρ_r²);
* ρ is the meta-model's expected specific cosine.

**Certificate.** The certificate is P(active), the per-route ρ_r, ρ, and the expected centred cosine
√(γ² + ρ²(1-γ²)). The refusal codes are:
* `NO_TRANSFER_ROUTE`;
* `SPECIFIC_DIRECTION_UNSUPPORTED` (ρ < 0.10), after which the prediction is the generic direction.

## Prediction tier

For each library compound and each of its lines T, three visibility regimes:
* **A**: every other profiled line is visible;
* **A1**: exactly one is visible, chosen by `sha256("vis:" + key + ":" + T)`;
* **B**: none is visible.

Scores are computed on active cells. A compound is the statistical unit: it contributes its mean
over its active cells.

| Id | Hypothesis (regime A1) | Test |
|---|---|---|
| P1 | Pooled centred cosine > generic direction | Compound sign-flip, 20,000 draws, one-sided |
| P2 | Pooled > context route alone, on cells where context is available | Same |
| P3 | AURC of the certificate (expected cosine) < AURC of applicability (top analogue similarity), loss = 1 - centred cosine | Compound-cluster bootstrap, 2,000 resamples; p = share of resamples with difference ≤ 0 |

## Campaign tier (`campaign.py`, `llm_arms.py`)

**Campaigns.** The library is ordered by `sha256("confirm-lib:" + key)` and split into 11
campaigns (`order[s::11]`, about 64 compounds each). Each campaign's grid is its profiled cells. A
well profiles one cell.

**Budgets.** W = N wells (one per compound) is primary; 0.5N and 2N are secondary.

**Utility.** The utility is the mean, over the grid's truly active cells, of each cell's credit:
* 1 if the cell was profiled;
* otherwise the centred cosine between the arm's fill and the observed response.

Non-responsive cells do not count. "Usable" is the share of active cells with credit ≥ 0.5.

**Arms.** Every arm gets the same wells.

| Arm | Plan | Fill |
|---|---|---|
| `zero` | none | no change |
| `generic` | none | line generic direction |
| `vc_only` | none | RKT |
| `dense` | random compounds in all their lines | RKT |
| `sparse_random` | random cell per compound per pass (PRESAGE design) | RKT |
| `sparse_hub` | each compound in its best outgoing-transfer line (κ) | RKT |
| `ad_uncertainty` | 4 rounds, lowest analogue similarity, one cell per compound | RKT |
| `activity_greedy` | 4 rounds, highest certified P(active) | RKT |
| `maestro` | 4 rounds, certificate value of information: p·(1 - e) plus transfer p·(e_after - e) to the compound's other lines, sequential greedy batch | RKT |
| `maestro_static` | the same value of information in one round | RKT |
| `oracle` | 4 rounds by realised loss (reference, not a policy) | RKT |
| `llm_no_vc` | deepseek-flash agent; sees identities, mechanisms, targets, line activity rates and its results; no VC | naive: mean of the compound's active profiled lines, else generic |
| `llm_conv_vc` | conventional ReAct agent, ≤ 4 tool steps per round, tools: certificates, transfer table, submit | RKT |
| `maestro_llm` | `maestro` batch, the LLM may swap ≤ 20% with a reason code | RKT |

**LLM arms.**
* They run at W = N only, with temperature 0 and model `deepseek-flash`.
* Recovery: one re-prompt that keeps the valid picks; any remaining shortfall is filled at random
  and counted (`fallback_cells`).
* Responses are cached by request hash.
* Provider ceiling: $3.00 for the confirmation.

| Id | Hypothesis at W = N | Test |
|---|---|---|
| P4 | `maestro` > `sparse_hub` | Exact cluster sign-flip over the 11 campaigns (2,048 patterns), one-sided |
| P5 | `maestro` > `activity_greedy` | Same |
| P6 | `maestro` > `llm_conv_vc` | Same |
| P7 | `sparse_hub` > `dense` (PRESAGE's design claim) | Same |

## Multiplicity and verdicts

P1-P7 form the primary family. Bonferroni gives a one-sided α of 0.05/7 = 0.00714 each.

| Claim | Passes when |
|---|---|
| VC claim | P1, P2 and P3 all pass |
| Decision claim | P4, P5, P6 and P7 all pass |

Headline:
* `CONFIRMED` if both claims pass;
* `PARTIAL` if any primary hypothesis passes, naming the ones that did;
* `NOT_CONFIRMED` if none pass.

A primary hypothesis whose arm could not run is `NOT_RUN` with its refusal code. It is never re-scoped.

## Secondary and exploratory analyses

Secondary analyses are one-sided at 0.05, reported without a multiplicity claim. Each is listed
with its development prediction.

* **C3b** `maestro` > `ad_uncertainty`.
* **C4b** `llm_conv_vc` > `llm_no_vc` (the virtual cell's value inside a conventional agent).
* **C5** `maestro_llm` vs `maestro`, two-sided. Predicted null; prior blocks found LLM components
  neutral or harmful.
* **C6** `sparse_random` > `dense`.
* **C7** `maestro` > `vc_only`.
* **C8** `maestro_static` > `sparse_hub`: certificates at equal turnaround.
* **Budgets.** Every contrast at 0.5N and 2N; usable fraction; arms re-scored under the other
  fill (choice vs fill decomposition).
* **V2.** Regime B: pooled > generic, and pooled > the monolithic ridge (SVD Morgan 128 +
  knowledge 64, decomposed at the registered development ρ = 0.118). Low power; development gains
  were +0.03 and +0.02.
* **V4.** Activity AUROC per regime.
* **Regime A.** Every prediction metric.
* **V5 (exploratory).** CRISPR knockout genetic route on the 53 phase-2 genes.

**Development expectations** (35 phase-1 campaigns, W = N; 3 to 6 campaigns for the LLM arms):

| Contrast | Mean difference | Campaigns favouring |
|---|---|---|
| P4 | +0.090 | 31/35 |
| P5 | +0.063 | 30/35 |
| P7 | +0.140 | 33/35 |
| C3b | +0.147 | 35/35 |
| C8 | +0.024 | 22/35 |
| P6 (6 campaigns) | +0.120 | 5/6 |
| C4b (6 campaigns) | +0.019 | 4/6 |
| C5 (6 campaigns) | -0.021 | 1/6 |

Power at 11 campaigns and α = 0.00714 is 0.84 (P4), 0.80 (P5) and 1.0 (P7). C8 says most of the
four-round planner's gain at W = N comes from adaptivity rather than from the certificates alone.

The prediction-tier development values (1,000-reference atlas, regime A1) were:
* pooled 0.547, against generic 0.408 and context 0.441;
* certificate AURC 0.328, against applicability 0.395.

The phase-2 reference γ is 0.308, against about 0.39 on phase 1. The transfer is therefore across
lines and releases, and the effects may shrink.

## Costs, delay and adjudication

* **Laboratory cost** is in wells (W, equal across arms) and plate turnarounds (rounds): 1 for
  fixed designs and `maestro_static`, 4 for adaptive arms. Every adaptive win carries a fourfold
  turnaround; C8 is the equal-turnaround test.
* **Provider spend** (USD) is reported separately from wells.
* **Adjudication** is blind by construction: every outcome is computed by code from measured
  profiles, and no human or LLM judges any outcome.

## Refusals and aborts

| Code | Consequence |
|---|---|
| `TIER_SEALED`, `NOT_FROZEN`, `FREEZE_MISMATCH`, `ALREADY_RUN`, `COMPOUND_ORDER_MISMATCH` | The run aborts |
| `provider_ceiling_exceeded` | The LLM arms stop; their contrasts are `NOT_RUN` |
| `TOO_FEW_ACTIVE_COMPOUNDS` | That regime's prediction metrics are not computed |

The confirmation is executed once (`python confirm.py --confirm`). `verify.py` recomputes every
reported number from the saved rows.
