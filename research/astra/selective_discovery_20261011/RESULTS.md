# Block P results: the virtual cell's contribution is confirmed; the agent's is not

Registered in `PROTOCOL.md`, frozen `2026-10-11T04:32:30Z`, run **once** on the sealed tier of 975
untouched compounds, then verified from the campaign ledgers alone.

**Headline: `NOT_CONFIRMED`.** The registered rule required H1, H2 and H6 to pass. H1 and H6 passed;
H2 did not.

## What the campaigns were

38 campaigns = 3 disjoint libraries of 325 new compounds x the lineages with a reachable hit.
Every arm received the same library, the same 32-screen budget (10%), the same batch size and the
same menu. 1,216 compound-screens per arm. 210 hits were reachable, 131 of them unexpected.

## Totals (identical budget in every row)

| arm | hits | unexpected | strictly novel | verified | screens | rounds |
|---|---|---|---|---|---|---|
| `random` (zero arm) | 18 | 10 | 9 | 13 | 1,216 | 38 |
| `fixed` workflow | 102 | 23 | 16 | 88 | 1,216 | 38 |
| `det` deterministic adaptive planner | 112 | 45 | 13 | 94 | 1,216 | 266 |
| `vc_only` virtual cell, no agent | 127 | 66 | **37** | 102 | 1,216 | 38 |
| `agent_novc` agent without the virtual cell | 117 | 52 | 20 | 98 | 1,216 | 266 |
| **`maestro`** proposed system | **141** | **69** | 31 | **116** | 1,216 | 266 |
| `maestro_explore` + two-stream portfolio | 135 | 68 | 37 | 110 | 1,216 | 266 |
| `maestro_perm` permuted feedback | 129 | 59 | 27 | 106 | 1,216 | 266 |
| `conv` conventional LLM agent + tool | 136 | **72** | **41** | 110 | 1,216 | 266 |
| `conv_perm` permuted feedback | 128 | 65 | 35 | 102 | 1,216 | 266 |
| `oracle` (bound, not an arm) | 210 | 131 | 82 | 167 | 1,216 | 38 |

"Strictly novel" is the descriptive from F13: also sharing no annotated target with a known hit and
at Morgan Tanimoto below 0.4 from all of them.

## Registered verdicts

Verdicts come from the exact cluster sign-flip test over the 14 lineages (all 16,384 patterns),
Bonferroni within family. Intervals are the nominal 95% lineage-cluster bootstrap.

### Primary family (k = 2, alpha 0.025 each)

| id | claim | estimate | nominal 95% | p | verdict | predicted |
|---|---|---|---|---|---|---|
| **H1** | the virtual cell adds unexpected hits | **+17** | [+11, +23] | **0.00098** | **PASS** | PASS |
| **H2** | the agent loop adds total hits over the virtual cell alone | +14 | [-1, +30] | 0.075 | **NOT_SUPPORTED** | PASS |

H1's p-value is `2^-10`, the floor for 10 informative lineages: **every** lineage with a reachable
hit favoured the virtual cell. That is the strongest form this design can produce.

### Secondary family (k = 7, alpha 0.00714 each)

| id | claim | estimate | nominal 95% | p | verdict | predicted |
|---|---|---|---|---|---|---|
| H3 | beats the fixed workflow on unexpected hits | +46 | [+23, +71] | 0.00098 | **PASS** | PASS |
| H4 | beats the conventional LLM agent | -3 | [-17, +13] | 0.689 | NOT_SUPPORTED | NOT_SUPPORTED |
| H5 | real feedback beats permuted feedback | +12 | [+4, +20] | 0.0195 | NOT_SUPPORTED | NOT_SUPPORTED |
| H6 | not inferior to the deterministic planner (margin 11.2) | +29 | [+16, +45] | - | **PASS** | PASS |
| H7 | beats the fixed workflow on independently verified hits | +28 | [+12, +46] | 0.0049 | **PASS** | PASS |
| H8 | the conventional agent uses feedback | +8 | [-3, +20] | 0.139 | NOT_SUPPORTED | NOT_SUPPORTED |
| H9 | the two-stream portfolio adds novelty | -1 | [-12, +9] | 0.625 | NOT_SUPPORTED | NOT_SUPPORTED |

Seven of the nine predictions were correct. The two misses are H2 (predicted PASS, not supported)
and nothing else; H1, H3, H4, H5, H6, H7, H8 and H9 all came out as registered.

## What this means

**1. The virtual cell is the source of discovery value, and it is now confirmed in a decision
setting.** Transfer from transcriptionally similar screened compounds finds selective killers whose
mechanism class is not known to kill that lineage: +17 over the identical agent denied those
sources, unanimous across lineages, and +46 over a fixed annotation workflow. This extends block N's
prediction-level result to the thing that matters, which compounds get bought.

**2. The agent loop's contribution is not established, and it is expensive.** `maestro` found 14
more hits than the one-shot virtual cell (141 vs 127), at p 0.075 against a 0.025 bar. It spent the
same 1,216 wells but **266 plate turnarounds instead of 38** - seven rounds per campaign rather than
one. On the primary endpoint the one-shot virtual cell is level (66 vs 69 unexpected) and *better*
on the strictest novelty count (37 vs 31). A one-shot virtual-cell ranking is the better buy here.

**3. The proposed integration bought nothing over a conventional agent.** A plain ReAct-style loop -
LLM picks from a virtual-cell shortlist each round - matched or beat it: 136 hits against 141, and 72
unexpected against 69, 41 strictly novel against 31. H4 was registered as a prediction of exactly
this and it held. The elaboration this block added (pooled stacked arbitration, gated prior,
two-stream planning, parameter-free stopping) is not justified by its own evidence.

**4. Feedback is directionally real but unproven.** Permuting the revealed profiles within each
batch cost 12 hits (141 vs 129) and 10 unexpected hits, nominally [+4, +20]. It fails the
family-wise bar. The conventional agent's feedback sensitivity is weaker still (+8, p 0.139),
consistent with Gupta et al. 2025 finding LLM design agents insensitive to feedback.

**5. The gains survive an independent assay.** 116 of `maestro`'s 141 hits reproduce on the PRISM
secondary screen (different plates, dose response), against 88 of `fixed`'s 102: +28 [+12, +46].
**Caveat:** every hit found happened to have secondary data (`unverifiable` is 0 for every arm),
because the secondary screen followed up compounds with primary activity. Verification is therefore
conditioned on an activity-enriched subset, not a random one.

**6. No refusal fired.** `VC_NO_NEIGHBOUR`, `NO_NOVEL_CANDIDATE`, `LLM_INVALID_SELECTION`,
`LLM_CALL_FAILED`, `BUDGET_EXHAUSTED_EARLY` and `SECONDARY_ABSENT` are all implemented and tested,
and none triggered in 418 campaign runs. The stopping rule never fired, exactly as the protocol
predicted: it compares the planned batch with a random batch using the model's own probabilities,
and the model is confident enough that the comparison never closes. A refusal path that never
executes is not evidence that it works.

**7. The world model is well calibrated in aggregate and over-confident per pick.** Summed
pre-reveal P(hit) was 148.1 against 141 realised for `maestro` (5% over), 127.2 against 117 for
`agent_novc`, 118.2 against 112 for `det`. Individual top picks reach P = 0.99997, so the
aggregate calibration hides per-pick over-confidence.

## Controls

* **Zero arm.** `random` found 18 of 210 reachable hits; every other arm beat it.
* **Outcome permutation.** Profiles permuted across compounds with the recorded selections kept:
  `maestro` 141 → 20, `vc_only` 127 → 31, `agent_novc` 117 → 16, `random` 18 → 12. Every advantage
  collapses to roughly the random level.
* **Feedback permutation.** Registered as arms A8 and A9 (H5, H8 above).
* **Memorisation.** The LLM prior scores the same with compound names withheld (AUROC 0.803 named
  against 0.792 masked on 540 development compounds), so its signal is annotation, not recall.
* **Cross-release leakage.** Pool compounds never served as GSE92742 references, so no candidate's
  own profile could reach it through the weak cross-release source.

## Verification

`verify.py confirm` recomputed everything from the 418 campaign ledgers, not from `RESULTS.json`:

* **0 ledger mismatches** on hits, unexpected hits and verified hits;
* **0 integrity violations**: no duplicate purchase, nothing bought outside its library, none over
  budget, and every pre-reveal prediction recorded in the order its compound was revealed;
* both primary contrasts reproduced to 0.0 with identical verdicts;
* the outcome-permutation control above.

`ok` is nonetheless `false`, for three declared file-hash mismatches: `evaluate.py` (deviation D1, a
two-line fix after the run crashed on its first LLM campaign, with both hashes recorded),
`DEVIATIONS.json` and `feasibility/README.md`. The latter two are a flaw in this block's freeze,
recorded as D2: a freeze must not hash its own deviations log, which exists to be appended to after
the freeze. `FREEZE.json` is left exactly as written so the mismatch is the audit trail.

## Cost

* **Laboratory:** 1,216 compound-screens per arm, 13,376 in all across the 11 arms. One-shot arms
  used 38 plate turnarounds, adaptive arms 266.
* **Provider:** USD 1.32 of the USD 10 ceiling, 3,261 deepseek-flash calls, of which USD 1.03 and
  2,920 calls were the pre-freeze lineage priors. No other model was used.
* Run time 2,762 s for the registered run.

## Boundaries

* One assay, one dose (PRISM 19Q4 primary at 2.5 uM, 5 days), one screening platform.
* "Unexpected" is novelty relative to Repurposing Hub mechanism annotation of 1,403 reference
  compounds, not biological novelty. No mechanism is claimed for any hit.
* Selective killing of a lineage is not a therapeutic claim, and lineage is a crude proxy for the
  genetic context that drives selectivity.
* The LLM's memorised knowledge of PRISM cannot be excluded, only bounded by the name-masking check.
* H2's failure is a statement about this budget and this task. At 20-30% of the library every arm
  converges on the ceiling (feasibility F12), so no planner can show value there either.

## What is promoted

Only one component earned promotion: the **exact cluster sign-flip test**, as
`tools.evaluation.scoring.cluster_signflip_test`, beside the existing `cluster_bootstrap_interval`.
It is a statistical contract, not a scientific claim, it decided every verdict here, and
`test_promotion_parity.py` holds it to exact agreement with the frozen copy.

**Not promoted:** `maestro_agent.Maestro`. Its contribution over the one-shot virtual cell was not
established (H2), and it did not beat a conventional agent-with-tool loop (H4). Promoting it would
contradict this block's own evidence.

`src/virtual_cell/transcriptional_transfer.py` (promoted by block N) gains decision-level support
from H1 but is unchanged.
