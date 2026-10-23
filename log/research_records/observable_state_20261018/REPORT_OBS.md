# Per-family typed-edit bets: result (internal development assessment, exposed PRISM 19Q4)

**Decision: the agent claim is withdrawn and the typed-edit thesis is withdrawn for this arena.** The Scientific Agent (deepseek-flash) did not
beat a conventional enumerator, a non-LLM target-gene rule or random edits by the registered margins, and no proposer's confirmation rate rose
meaningfully above the null. This is a result about this design on exposed data, not a project-wide STOP. Run order followed the contract:
FREEZE0 (11 files) -> `run_stage1.py` (edits, 272 agent calls, 0 invalid) -> FREEZE1 -> one masked transfer read (`ACCESS_LEDGER.jsonl`) ->
`analyse_obs.py`. No sealed tier opened, nothing committed or pushed. `verify.py` recomputes the freezes and `RESULTS_OBS.json`.

## Design as run
136 MoA-family episodes; within-family chemical split (Tanimoto < 0.5, whole connected components); 7 held-out lineages (175 lines); 1,187 admissible state
variables (DepMap expression-above-median and driver mutation); each arm proposed one `ResearchEdit` per family from search-side data only (held-out lineage
columns and the family's held-out compounds blanked; scramble-tested). Confirmed = registered sign, |contrast| >= max(declared, 0.10 log2FC), one-sided
family-label permutation p < 0.05 on held-out compounds x held-out lineages versus a purged comparator set. Zero = 20 random admissible edits per family.

## Results (confirmation rate over 136 families)

| Arm | Rate | Edits |
|---|---|---|
| Zero (random) | 0.051 | 2,720 |
| A2 enumerator (max search-side \|t\|) | 0.059 | 136 |
| A2k target-gene knowledge rule | 0.088 | 133 |
| **A3 agent** | **0.081** | 136 |
| A3-blind (identities masked) | 0.059 | 136 |

* The Zero rate (5.1%) equals the nominal 5%: the confirmation test is calibrated, so a gain would have been detectable.
* Family-cluster paired contrasts (95% interval; one-sided 95% bounds; Holm-adjusted p for the three registered comparisons):
  * P1 agent - enumerator **+0.022** [-0.022, +0.074]; upper bound +0.059 < +0.10 -> **withdrawn**; Holm p 0.55.
  * Agent - knowledge rule **-0.007** [-0.037, +0.015]; lower bound -0.029 <= 0 -> withdrawn; Holm p 0.87.
  * Agent - zero **+0.029** [-0.005, +0.069]; lower bound 0.000 <= 0 -> withdrawn; Holm p 0.20.
  * Agent - agent-blind +0.022 [-0.022, +0.074] (identity knowledge adds nothing resolvable).
  * Typed-edit thesis: neither A2 (+0.007) nor A3 (+0.029) beats Zero by more than 0.10 -> withdrawn.
  * Target-class clustering gives intervals of the same width (`RESULTS_OBS.json`).
* Exploratory, outside the registered family: A2k - Zero +0.037 [+0.003, +0.075], unadjusted p 0.028. A target-gene-state rule carries a weak signal
  that the search-side enumerator and the agent do not extract; it is below the 0.10 practical margin and would not survive adjustment for the six
  contrasts examined.
* Calibration: the agent's stated probability averaged 0.45 against an observed confirmation rate of 0.081 (Brier 0.389 versus 0.369 for the
  enumerator); the enumerator's bootstrap-stability p averaged 0.46 against 0.059. All proposers were overconfident roughly five-fold.
* Power: the interval half-width of P1 is about 0.05, so an effect of 0.10 or more was excluded (MDE ~0.12 predicted).

## Reading
* Prior from `program_revision_20261017` (LLM vs enumeration +0.004) is reproduced in a better-powered, differently scored test: the agent adds
  nothing over a conventional proposer here.
* Search-side evidence in small families (4-10 compounds, 1,187 candidate variables) mostly selects noise: the enumerator's confirmation rate is
  indistinguishable from random; the agent's shortlist-reading did not change that.
* Neither identity knowledge (A3 vs A3-blind +0.022) nor reading residuals rescued the agent.

## What this does not show
Exposed data; memorisation could only inflate the agent, so the null is the stronger statement. Bets were restricted to a closed vocabulary of
expression/mutation states and one edit per family; other primitives (split, merge, observation requests), richer state definitions, decision-level
utility (S2/H0 were not run) and a larger or independent screen remain untested. Families without target annotation or cytotoxic content dilute all
arms equally. The unadjusted A2k signal is a lead, not a finding.

## Next (not started)
Treat "knowledge-informed state variables" as the only live lead (A2k), test it with a pre-registered, non-LLM, target-and-pathway rule on independent
data; keep the typed-edit scaffold only as bookkeeping. Cost: 272 deepseek-flash calls (token cost not logged by the client).
