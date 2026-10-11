# Block P protocol (registered; written before any sealed outcome is read)

Status: **DRAFT until `FREEZE.json` exists.** The confirmation geometry is filled in from F9 and the
arm list from F10 before the freeze; nothing below is changed afterwards. Corrections after the
freeze are appended to `DEVIATIONS.json` with their timing, never edited in.

## 1. What was already seen (disclosure)

All development results in `feasibility/README.md` were produced before this protocol and are
disclosed in full: F0-F10 on the 1,403 block-N compounds, whose outcomes block N exposed on
2026-10-10. The registered thresholds and predictions below are set from those results.

From the **sealed** tier the author has seen exactly one statistic, recorded in
`EXTRACT_RECEIPT.json`: 325 of 987 candidate new compounds kill at least 5% of lines
(log fold change < -1), computed at about 11:20 local on 2026-10-11 while sizing the pool. No
lineage-selectivity statistic, no per-compound outcome and no hit count has been seen.

The LLM prior for all 2,378 compounds (including the 975 new ones) was generated before the freeze
from names and annotations only. No viability value entered any prompt. The records are hashed into
`FREEZE.json`, so the prompts and replies cannot change afterwards.

## 2. Units, endpoint and cost

* **Campaign** = (library, target lineage). The reference library is all 1,403 block-N compounds.
  The 975 new compounds are split into **3** disjoint sub-libraries of 325 by a seeded permutation
  (`runner.libraries`, seed 20261011). Lineages are the 14 PRISM primary tissues with at least 20
  lines. The geometry was chosen in F9 before any sealed outcome was read.
* **Budget = 10% of the library (33 screens), batch 5.** This is the value every development
  experiment used (F0-F11); it is *not* selected from the F12 budget sweep. F12 (10%, 20%, 30%) is
  run and reported as a disclosed sensitivity analysis, and its result does not change the
  registered budget. Every constant is listed with its provenance in `PROTOCOL_CONFIG.json`.
* **Action** = screen one compound, revealing its 578-line primary profile. One action = one
  compound-well in the pooled screen. One round = one plate turnaround.
* **Budget** = 10% of the library, in batches of 5. Arms that use no feedback spend their whole
  budget in one round.
* **Hit** for lineage T: mean log2 fold change over T's lines at least 0.5 below the mean over all
  other lines, **and** T's own mean at most -0.5.
* **Unexpected hit**: a hit whose annotated Repurposing Hub mechanism string has no hit for that
  lineage among the **reference** compounds. Fixed at the start of each campaign from the reference
  set alone, so it does not move with what an arm buys. F13 showed this exact-string definition
  coincides with a stricter token-overlap definition on development data (99 of 99), so it is not a
  loose notion of novelty. A strictest variant (also sharing no annotated target and at Morgan
  Tanimoto below 0.4 from every known hit) is reported as a descriptive, not as the endpoint.
* **Verified hit**: a hit whose independent secondary-screen selectivity is at most -0.25 (different
  plates, dose-response run). Undefined where the compound is absent from the secondary screen;
  those are reported separately and never counted as verified.

**Primary endpoint:** unexpected hits found. **Secondaries:** total hits, verified hits.
**Cost:** compound-screens spent and rounds used, reported per arm; provider spend reported
separately and excluded from the cost metric.

## 3. Arms

Every arm receives the same library, reference set, budget, batch size and menu, and sees no
outcome it has not bought.

| id | arm | planner | evidence sources | feedback |
|---|---|---|---|---|
| A0 | `random` | uniform random | none | no |
| A1 | `fixed` | fixed workflow: rank once by annotated class-mean selectivity | `klass` | no |
| A2 | `det` | deterministic adaptive planner | `klass`, `target`, `chem` | yes (refit each round) |
| A3 | `vc_only` | virtual cell without an agent: rank once | `vc_native`, `vc_cross` | no |
| A4 | `agent_novc` | the same agent as A6 without virtual-cell predictions | `klass`, `target`, `chem`, LLM prior | yes |
| A5 | `conv` | conventional LLM agent with a virtual-cell tool (`conv_agent.py`) | virtual cell via tool, LLM selects | yes |
| A6 | `maestro` | the proposed system (`maestro_agent.py`): one pooled world model, refit every round, with verification, stopping and named refusals | all five sources + gated LLM prior | yes |
| A7 | `maestro_explore` | A6 plus the two-stream portfolio (2 of 5 seats to novel mechanism classes, ranked by the virtual cell, seats moved by observed yield) | as A6 | yes |
| A8 | `maestro_perm` | A6 with permuted feedback | as A6 | permuted within each batch |
| A9 | `conv_perm` | A5 with permuted feedback | as A5 | permuted within each batch |
| - | `oracle` | upper bound, not an arm | true outcomes | - |

The primary agent A6 carries **no** explore stream: feasibility F10 found the portfolio neutral on
unexpected hits (+3 [-4, +12]) and slightly negative on total hits (-5 [-16, +7]). Rather than drop
the component silently, it is registered as A7 with its own hypothesis (H9), so a component this
block built and does not believe in still gets a sealed test.

The permutation controls shuffle the revealed profiles within each batch, so an arm's beliefs are
wrong while the truth used for scoring is unchanged (`test_block_p.py`).

## 4. Hypotheses, predictions and verdict rules

### The registered test

Differences are paired per campaign. There are only 14 lineage clusters, which makes a cluster
bootstrap the weaker instrument, so the **verdict is decided by a cluster sign-flip test**: under
the null that two arms are exchangeable within a lineage, each lineage's summed difference is
symmetric about zero, so its sign may be flipped. All 2^14 = 16,384 sign patterns are enumerated,
making the p-value exact (`stats.cluster_signflip`). The cluster-bootstrap interval is still
reported, as the effect size, both nominally and Bonferroni-widened.

A contrast `PASS`es when its one-sided p-value is at most `alpha / k` for a family of `k`
contrasts at `alpha` 0.05, `HARM`s when the opposite one-sided p-value is, and is
`NOT_SUPPORTED` otherwise. A non-inferiority contrast is decided by the family-wise interval
against its margin instead, because a sign-flip test cannot address a shifted null.

**Power, stated in advance.** The exact sign-flip p-value is bounded below by `2^-n` for `n`
lineages that differ consistently, so the primary family needs at least 6 lineages all favouring
`maestro` to reach `p <= 0.025`. In the F9 rehearsal the virtual-cell contrast was positive in 6 of
10 informative lineages and zero in the rest, giving `p = 0.016`. The design is therefore powered
for the development-sized effect but **not** for an effect half that size; this is disclosed
rather than fixed by enlarging the family.

### Primary family (2 contrasts, the two cores' independent contributions)

| id | claim | endpoint | prediction |
|---|---|---|---|
| **H1** | `maestro` > `agent_novc`: the virtual cell adds discoveries annotation cannot anticipate | unexpected hits | PASS |
| **H2** | `maestro` > `vc_only`: the agent loop adds yield the virtual cell alone cannot reach | total hits | PASS |

### Secondary family (6 contrasts)

| id | claim | endpoint | prediction |
|---|---|---|---|
| **H3** | `maestro` > `fixed`: the system beats a fixed scientific workflow | unexpected hits | PASS |
| **H4** | `maestro` > `conv`: the proposed integration beats conventional agent-plus-tool use | unexpected hits | NOT_SUPPORTED |
| **H5** | `maestro` > `maestro_perm`: real feedback beats permuted feedback | total hits | NOT_SUPPORTED |
| **H6** | `maestro` is not inferior to `det` by more than 10% of `det`'s total | total hits | PASS |
| **H7** | `maestro` > `fixed` on hits confirmed by the independent secondary screen | verified hits | PASS |
| **H8** | `conv` > `conv_perm`: the conventional agent uses feedback | total hits | NOT_SUPPORTED |
| **H9** | `maestro_explore` > `maestro`: the two-stream portfolio adds novel discoveries | unexpected hits | NOT_SUPPORTED |

**Headline rule.** Dual-core value is *confirmed* only if **H1 PASSES and H2 PASSES and H6 PASSES**:
the virtual cell must add unexpected discoveries, the agent loop must add yield, and neither may be
bought by sacrificing total yield. Any other pattern is reported as its own result, not as
confirmation.

Predictions are set from development: H1 from F8/F9 (+13 [+3, +25] at a 10% budget on 5 seeds;
+7 [+1, +14] at the confirmation geometry), H2 from F9 (+23 [+1, +47]), H3 from F9
(+15 [+5, +27]), H6 from F2/F3, H7 from F9 (+12 [-2, +28], predicted PASS on the larger
confirmation pool). H4, H5 and H8 are predicted NOT_SUPPORTED because development found feedback
null in the full stack (+1 [-4, +5]) and because no LLM role has added value in blocks M, N or F7.

## 5. Named refusals

An arm must refuse by code rather than guess. Codes recorded in each campaign ledger:

* `VC_NO_NEIGHBOUR`: no reference compound shares a measurable transcriptional similarity with a
  candidate; the virtual-cell features are marked missing, not zero.
* `NO_NOVEL_CANDIDATE`: no remaining candidate's class is free of a known selective member; the
  explore stream is empty and its seats return to the confirm stream.
* `LLM_INVALID_SELECTION` / `LLM_CALL_FAILED`: the reply is unusable; the tool's own ranking fills
  the batch and the number of filled seats is recorded.
* `BUDGET_EXHAUSTED_EARLY`: the stopping rule ended the campaign before the budget was spent. Per
  MAESTRO standards this is a licensed answer, so unspent screens are reported as cost saved and
  the arm is **not** credited with hits it did not buy.
* `SECONDARY_ABSENT`: a hit cannot be verified because the compound is not in the secondary screen.

## 6. Controls

* Zero arm `random`, and `oracle` as the reachable ceiling.
* Feedback permutation twins for both feedback-using agents (A7, A8).
* Outcome permutation: the full evaluation is re-run once with the sealed profiles permuted across
  compounds, to confirm every contrast collapses.
* Name-masked LLM prior (already run on 540 development compounds: AUROC 0.803 named against 0.792
  masked), as the memorisation check.
* Pool compounds never serve as GSE92742 references, so the cross-release source cannot leak a
  candidate's own profile.

## 7. Analysis plan

1. Run the deterministic arms (A0-A4, oracle) over every campaign.
2. Run A5-A8 (LLM calls), caching every reply.
3. Compute the primary and secondary families with `stats.py`.
4. Report per-arm cost (screens, rounds), refusal counts and provider spend.
5. Record deviations in `DEVIATIONS.json`; verify with an independent recomputation (`verify.py`).

Provider ceiling: USD 10 for the block (`tmp/selective_discovery_spend.json`); USD 1.03 of it was
spent on the priors before the freeze.
