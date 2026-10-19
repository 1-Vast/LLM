# MAESTRO-FAR dev-arena test: report (2026-10-19)

**Verdict: FAR_NOT_SUPPORTED in this arena.** The failure signatures carry no information about where the base Virtual Cell fails, and choosing the L1000
assay slices by failure signature or by a learned expected-benefit model did not beat exploit-first slice choice (or random). The orthogonal assay plus a
fixed repair does help, but that effect is not specific to falsification-aware selection. The agent, 2x2, transfer and EG-RPT phases were not run: the frozen
rule (`FREEZE_PROTOCOL.md`) makes them conditional on a deterministic FAR advantage. All data are exposed; this is internal development evidence. Nothing here
validates MAESTRO-FAR, EG-RPT or any LLM contribution.

## What was run (Observed)
* Arena (`far_data.py`): PRISM 19Q4 primary log-fold-change (578 lines) x L1000 landmark signatures (9 lines, block-Q array) x ECFP4. 848 dev drugs in 242
  chemistry/MoA-connected families (5 family folds); 279 reused-vault drugs (block-N names). Selective residual = compound mean and reference line-mean removed.
* Task: pool = one fold; target line = each of about 540 lines; nominate 16; utility = mean selective killing (log2FC) of the nominees. Base Virtual Cell = mean
  of a Tanimoto-kernel ridge and a Tanimoto kNN trained on other folds with Tanimoto >= 0.5 purged. Assay = L1000 signature of 4 of 16 equal-size slices
  (25% of the pool; equal cost for every policy). Repairs: none, fuse, gate (primary), residual expert, abstain.
* Policies: none, random, coverage, exploit-first, probability-of-hit, FAR (logistic model of false progression on three pre-assay signatures), FAR-v2
  (gradient-boosted expected-benefit model), all slices (4x cost ceiling), split-line oracle and per-line oracle (hindsight, unattainable).
* Stages: search folds 0,1; select fold 2; freeze; test folds 3,4 read once; one reused-vault check (not independent). Family-cluster bootstrap, 4,000 draws.

## Results (utility in log2FC per nomination; 95% intervals)
| Contrast | select (fold 2) | test (folds 3,4) | reused vault |
|---|---|---|---|
| Phase 1: signatures with AUROC lower 90% bound > 0.60 | 0 of 3 (AUROC 0.47-0.50) | 0 of 3 (0.49-0.52) | 0 of 3 (0.49-0.51) |
| C1 FAR - exploit-first (gate: lower bound > 0.010) | -0.013 [-0.028, -0.004] | +0.006 [-0.003, +0.018] | +0.006 [-0.004, +0.019] |
| C2 FAR-v2 - exploit-first | -0.020 [-0.038, -0.007] | -0.000 [-0.007, +0.006] | +0.015 [-0.006, +0.042] |
| FAR - random | +0.005 [-0.006, +0.018] | +0.010 [-0.007, +0.034] | +0.004 [-0.020, +0.029] |
| assay + gate repair - no assay (FAR slices) | +0.021 [0.000, +0.049] | +0.039 [+0.009, +0.085] | +0.047 [+0.009, +0.095] |
| exploit-first - no assay | +0.035 [+0.007, +0.076] | +0.033 [+0.008, +0.071] | +0.040 [+0.010, +0.079] |
| all slices - random (4x cost) | +0.058 [+0.018, +0.109] | +0.070 [+0.028, +0.124] | +0.110 [+0.029, +0.218] |
| split-line oracle - random (hindsight; slices chosen on other lines) | +0.039 [+0.009, +0.080] | +0.059 [+0.015, +0.113] | +0.089 [-0.001, +0.208] |

Cross-fit correlation of the expected-benefit model inside search was -0.002 and +0.009. Hits per nomination (selective residual >= 1 log2FC) give the same ordering.

## Interpretation
1. **Falsification targeting failed here for a measurable reason.** None of the three pre-assay signatures (domain distance, neighbour dispersion, model
   disagreement) predicts a false progression, and a gradient-boosted model could not predict the benefit of measuring a compound. FAR captured at most about 0.006
   of the roughly 0.06 headroom that a line-agnostic hindsight slice choice shows.
2. **The headroom is real but not predictable from these features.** The split-line oracle is reproducibly above random in select and test, so some slices are
   worth more than others across lines. What predicts which is untested. This is a lead, not a result; any further feature search needs a new frozen protocol and
   fresh data, because the test folds and the vault have now been read.
3. **The assay-plus-repair effect is real in this arena** (+0.03 to +0.05; lower bounds above zero in test and vault), consistent with the earlier
   transcriptional-transfer result. Exploit-first (measure what you would nominate) is the best cheap policy.
4. The test interval for C1 (upper edge +0.018) does not exclude a modest advantage over exploit-first, so FAR is not shown to be useless, only unsupported.

## Limitations
One arena (PRISM selective killing, L1000 transfer); chemistry and L1000 are the only inputs; the Virtual Cell is a kernel/kNN ensemble, not a modern foundation
model (none was trained or evaluated); the test stage is two folds; the vault is a reuse; no wet-lab or JUMP edge; FAR-v2 and the signature model were developed on
the same search folds; `far_run.py` and `far_analyse.py` were not in the hash set (`DEVIATIONS.json`). The LLM agent contribution was not tested.

## Reproduce
Use the Anaconda Python (`/d/anaconda/python -B ...`), from this folder: `far_data.py` (arena counts), `far_run.py search` (writes MODEL.json and
records_search.npz, write-once), `far_v2_search.py` (VALUE_MODEL.pkl), `far_run.py select`, then the freeze, `far_run.py test`, `far_vault.py`,
`far_analyse.py <stage> U` and `<stage> hits`, `far_decide.py`, `verify.py`.
