# Block P: can a dual-core autonomous system discover selective killers an annotation lookup cannot?

**Question.** A compound library has been profiled cheaply by L1000 but not screened. A campaign
wants compounds that **selectively kill one tumour lineage**, under a screening budget. Does the
virtual cell contribute discoveries that target and mechanism annotation cannot anticipate, and does
the autonomous agent loop contribute yield the virtual cell alone cannot reach?

**Answer (38 campaigns, 975 sealed compounds, 1,216 screens per arm):**
* **The virtual cell contributes, and it is confirmed.** +17 unexpected hits [+11, +23], p 0.00098,
  over the identical agent denied its transcriptional sources. Ten informative lineages favoured it,
  three tied, none opposed. +46 over a fixed annotation workflow; +28 hits confirmed on the
  independent secondary screen.
* **The agent loop's contribution is not established.** +14 total hits over the one-shot virtual cell
  at p 0.075, bought with 266 plate turnarounds instead of 38, and level on the primary endpoint.
* **The proposed integration gave no gain over a conventional LLM-agent-with-tool loop** (136 hits
  and 72 unexpected against 141 and 69). That was the registered prediction.
* Headline verdict **`NOT_CONFIRMED`**: the registered rule required the agent contribution too.

Full numbers, controls, verification and boundaries are in `RESULTS.md`. Development evidence is in
`feasibility/README.md`, the problem diagnosis in `PROBLEM.md`, the literature assessment in
`LITERATURE.md`, the registered design in `PROTOCOL.md`, and every correction in `DEVIATIONS.json`.

## Why this task

Block N established the one thing MAESTRO's virtual cell can do on sealed data: transfer killing
profiles between compounds with similar L1000 responses, across annotated mechanism classes. It also
established that every LLM knowledge role tested was null or harmful. What was never tested is the
loop the virtual cell exists for: **choosing which compounds to send to an expensive assay, and
learning from each result.**

Three facts make that loop non-trivial here, all measured before the freeze:

* A compound's own phase-1 (GSE92742) signature is the nearest phase-1 neighbour of its phase-2
  (GSE70138) signature only 11.6% of the time. The same-platform reference library for new
  compounds is small, so **every compound a campaign screens enlarges the virtual cell**.
* Hits replicate on the independent PRISM secondary screen 60-100% of the time, against 1-26% for
  non-hits, so the endpoint can be checked twice.
* At a 10% budget, annotation alone already finds most *total* hits. The virtual cell's measurable
  contribution is concentrated in hits whose mechanism class is not known to kill that lineage.

## Data

| role | source | compounds | status |
|---|---|---|---|
| reference library | block N units: GSE92742 L1000 x PRISM 19Q4 primary | 1,403 | exposed (block N ran 2026-10-10) |
| phase-2 inputs | GSE70138 Level 5, 7 lines x 6 doses, 24 h, 978 landmark genes | 1,517 | open (inputs only) |
| confirmation libraries | GSE70138 compounds **not** block-N units | 975 | PRISM outcomes sealed until `FREEZE.json` |
| independent verification | PRISM 19Q4 secondary screen (different plates, dose response) | 397 of 975 | sealed with the tier |

All data were already local. Nothing was downloaded for this block; `extract.py` verifies the
GSE70138 archive against GEO's published SHA-512 before reading it.

## The two cores as tested

**Virtual cell** (`world.py`): a stacked hit model over five evidence sources - transcriptional
transfer on GSE70138 (`vc_native`), cross-release transfer (`vc_cross`), annotated class mean,
target Jaccard and Morgan chemistry - with a gated LLM literature prior. Per-lineage model
arbitration was built, tested and **rejected** (feasibility F5).

**Agent** (`maestro_agent.py`): persistent campaign state, a world model refit on every result,
two-stream planning (confirm and explore), named refusals, independent verification that never
feeds back into selection, and a parameter-free stopping rule.

**Comparators**, at identical budget, batch and menu: a fixed workflow, a deterministic adaptive
planner, the agent without virtual-cell predictions, the virtual cell without the agent, a
conventional LLM-agent-with-tool loop, feedback-permutation twins for both LLM-driven arms, a random
zero arm, and the reachable oracle.

## What was rejected before the freeze

* **Per-lineage model arbitration** (F5): three arbiters all lost to the pooled stack; the reference
  likelihood is so sharp that the mixture collapses onto one family.
* **The LLM prior as a selector** (F6, F7): informative (hit AUROC 0.76) but weaker than an
  annotation lookup (0.87), and null inside the loop (+2 [-3, +9]). Kept only as a gated feature
  whose weight is learned.
* **LLM-as-world-model** (VCWorld-style), diffusion virtual cells, belief-space MCTS and Cell
  Painting: rejected on evidence or cost, with reasons in `LITERATURE.md`.

## Reproduction

```bash
python extract.py                 # once; writes EXTRACT_RECEIPT.json and the data tiers
python run_prior.py               # LLM lineage priors (cached per compound)
python feasibility/f0_headroom.py # ... through f13; exploratory, exposed units only
python freeze.py                  # hashes code, protocol and priors; opens the sealed tier
python evaluate.py confirm        # the registered run
python verify.py confirm          # independent recomputation from the ledgers
```

Provider ceiling USD 10 (`tmp/selective_discovery_spend.json`), all calls deepseek-flash.
