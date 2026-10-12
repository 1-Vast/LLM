# Block Q disclosure: everything seen before the freeze

Written before `FREEZE.json`. It lists what the author (this session) saw, computed or tuned, so
a reader can judge what the confirmation can and cannot certify.

## Development tier: GSE92742 (L1000 phase 1), fully open

All method choices were made on phase 1 (7,760 compounds at 10 uM / 24 h, nine lines), with
compound folds `sha256("blockq-dev:" + key) mod 5`. Everything in `cache/dev_*` was seen:

| Step | What was seen |
|---|---|
| Routes, full atlas (`dev_routes`) | Accuracy of each route on active cells: context 0.592, phenotypic 0.562, structural 0.284, knowledge 0.270, genetic 0.025 centred cosine. The genetic route was not admitted. |
| Pooling (`dev_pool`) | Decomposition, HGB meta-models, certificate calibration, AURC. |
| 1,000-reference atlas (`dev_routes2`, `dev_pool2`) | Regime A 0.583, A1 0.547, B 0.440 against generic 0.408. Certificate AURC 0.299 / 0.328 / 0.494 against applicability 0.364 / 0.395 / 0.541. |
| Monolithic comparator (`dev_monolithic`, `dev_mono2`) | Regime B: decomposed monolithic 0.421 against pooled 0.440. Its out-of-fold specific cosine, 0.118, is registered as `MONO_RHO`. |
| Campaigns (`dev_campaign`) | All deterministic arms on about 35 fold campaigns at three budgets. |
| Fixes before the full run | Two fixes were made after the first one-campaign test. A per-compound cap was replaced by sequential greedy batching, because the cap stopped `maestro` completing active compounds at 2N. The LLM arms gained state-preserving recovery: valid picks are kept and the agent is asked for the rest. |
| LLM arms (`dev_llm`) | Six fold-0 campaigns at W = N, deepseek-flash, $0.25 in all. The table after this one gives the means and the counts of campaigns favouring each arm. Two agent-harness fixes followed the first three campaigns: ReAct thoughts are capped at two sentences, with a 6,000-token budget, after replies truncated at 3,000; and tool names are matched tolerantly. |
| Single-round planner (`dev_campaign_static`) | `maestro_static` over `sparse_hub`: +0.064, +0.024 and +0.041 at 0.5N, N and 2N. |
| Dry runs | The phase-1 dry run (fold 0, two campaigns, offline LLM) reproduced the development prediction values and passed `verify.py`. The synthetic dry run used random query responses. |

LLM-arm results on the six development campaigns:

| Arm | Mean utility | Campaigns where `maestro` scored higher |
|---|---|---|
| `maestro` | 0.737 | - |
| `maestro_llm` | 0.716 | 5/6 |
| `llm_conv_vc` | 0.618 | 5/6 |
| `llm_no_vc` | 0.598 | - |

Tuning that used development outcomes:
* the regularisation grids and the route parameters (k, similarity floors);
* the HGB settings, chosen over a ridge/isotonic alternative on dev;
* `rho_min = 0.10`;
* the sequential-greedy fix in `maestro`;
* the LLM-harness fixes listed above.

None were tuned on phase 2.

## Confirmation tiers: GSE70138 (L1000 phase 2)

**Reference tier (open, 979 compounds also in phase 1).**
* Before the freeze, only counts were looked at (979 compounds, 6,605 cells).
* The synthetic dry run built the reference-tier world and printed one statistic: the generic
  share γ = 0.308, against about 0.39 on phase 1. Nothing was changed in response.
* The transfer table κ was written to a dry-run file that was not read.

**Query tier (sealed, 734 compounds absent from phase 1).**
* Responses are written only to `blockq_phase2_query_SEALED.npz`, and `load_query()` refuses with
  `TIER_SEALED` until `FREEZE.json` exists.
* From metadata only (`sig_info`, `pert_info`, MAP-KG drug table), the following were read:
  * the lines profiled per compound (670 in all seven lines);
  * identities and PubChem CIDs (661 of 734 mapped);
  * the InChIKey overlap with profiled compounds: 28 query compounds share a connectivity block
    with a compound profiled at 10 uM / 24 h, and are excluded as `DUPLICATE_OF_PROFILED`.
* The dry runs used random numbers in place of query responses.

**Prior exposure outside this study.** Phase 2 is not a pristine tier for the MAESTRO programme:
* belief planning (2026-09-27) used 38 of its new compounds in an MoA proxy test;
* block P (2026-10-11) used L1000 phase-2 profiles of 975 compounds as inputs to PRISM
  selectivity campaigns;
* block N used L1000 profiles as inputs.

None of these evaluated cross-compound transfer of the response direction, the endpoint here.
Their results are aggregate nulls or positives on other endpoints, which carry no information about
route accuracy on these compounds. This study computed no statistic of query responses before the
freeze.

## Literature and novelty checks (also pre-freeze)

**Papers read in full.**
* PRESAGE (Littman et al., bioRxiv 2025).
* MAP (Feng et al., Nat. Mach. Intell. 2026).

**Searched.**
* Systema.
* TxPert, LPM, IterPert, PerTurboAgent, BioDiscoveryAgent.
* AssayLoop, AnchorDrug, Hodos 2018.
* MechPert, PRESCRIBE, ConfPert, CellAudit, VCWorld, AlphaCell, AssayBench.

**Already published, so not claimed as novel.**
* Anchor or active profiling of new lines: AnchorDrug.
* Tensor completion of L1000: Hodos 2018.

**What is claimed as novel.** Per-query typed transfer certificates with an analytic accuracy
decomposition, and their use as the value of information of a profiling campaign.
