# Agent enhancement: edits as many small registered bets (2026-10-18)

> Historical proposal, not evidence. The proposed experiment was subsequently run with recorded deviations; see [`REPORT_OBS.md`](REPORT_OBS.md) and [`DEVIATIONS.json`](DEVIATIONS.json) for the result and actual access pattern.

Status: design note, no result. Nothing was run and no outcome or sealed file was opened. For the agent thesis this replaces `ENHANCEMENT.md`; the L1000 exchange rate is withdrawn (NOVELTY_REVIEW.md: it repeats Block N).

[V] = checked in a primary source (abstract level) or in repository records. [U] = not verified.

## 1. Why the agent has been null here

Evidence [V, EVIDENCE.md and memory index]:

| Study | Result |
|---|---|
| program_revision | LLM vs enumeration +0.004; 62-73% of proposals had insufficient evidence; 20-23% committed to the wrong direction |
| acquisition_program | 10 of 12 proposals rejected; agent vs lookahead +0.008 [-0.033, +0.054] |
| Block P | A conventional ReAct agent matched the agent loop |
| Block N | LLM critic -0.052, forecaster -0.025 (harmful) |
| knowledge_reality | The knowledge gain was mechanism-class membership |
| certified_discovery | Planner returned the whole menu (format failure) |
| feedback_validation | LLM failed exact-k selection (format failure) |

Diagnosis: the agent was asked to rank or weight what a fitted model already ranks. Each time it was scored on one large utility contrast (+7% headroom, SE up to 0.199). It was never scored on the job only it could do: naming a context state variable *outside* the fitted features, with a direction and a magnitude, from a handful of examples.

## 2. The design

**Unit of the claim.** A ResearchEdit is one small, pre-registered, falsifiable bet. Power comes from the number of independent bets.

**Episode.** One MoA family F, seen only through its `D_search` compounds:
- ridge-plus-feedback residuals across the search lineage groups;
- local DepMap 19Q4 features (mutation, expression, lineage);
- target annotations.

**What each arm returns.** Exactly one `interaction`, `split` or `local_exception` edit, accepted by `validate()` and hashed before outcomes. The edit names:
- a state variable z;
- the sign and a minimum magnitude of the crossed contrast `[Y(F,z=1)-Y(F',z=1)] - [Y(F,z=0)-Y(F',z=0)]`;
- a scope;
- a stated confirmation probability p.

**Test cell.** Held-out compounds of the same family (scaffold split, Tanimoto 0.5 purge) × held-out lineage groups. It uses the published PRISM matrix: no campaign, no synthetic noise, no hypothetical costs.

**Confirmed** = registered sign, one-sided p < 0.05 in the cell, and at least the registered magnitude.

**What the agent might do that the enumerator cannot.** In small families, an enumerator ranking thousands of family × feature pairs on 4-10 compounds mostly picks noise. The agent can combine the residual pattern with prior biology (the target gene's own status, pathway dependence). This is the mechanism BioDiscoveryAgent reports (+21% over Bayesian optimisation on gene selection) [V, arXiv 2405.17631 abstract].

**Cheap falsification:**
- The agent's edge must show in the pre-registered small-support stratum.
- It must beat **A2k**, a non-LLM knowledge rule ("target gene mutated or highly expressed").
- Its edge is compared against **A3-blind** (names, targets and gene symbols masked). If A3-blind matches A3, the value lies in reading residuals, the stronger claim. If only unmasked A3 wins and A2k matches it, the agent is an expensive annotation lookup.

**Distinctness:**
- POPPER [V, arXiv 2502.09858, ICML 2025] falsifies given hypotheses sequentially. It does not compare proposers.
- BioDiscoveryAgent scores hit-finding, not falsifiable state edits.
- MDA, AHOIS and AIRA2 [U] are not drug-context interactions.

Paired confirmation of proposers at matched grammar and data appears unreported [U].

## 3. Estimand, unit, MDE

**Primary P1.** Mean over episodes of (Y_A3 − Y_A2), where Y = 1 if confirmed. Paired by episode, clustered by target class. The SE is about sqrt(discordance / E), where E is the number of episodes.

| Discordance | Episodes E | MDE (80% power, one-sided 0.025) |
|---|---|---|
| 0.3 | 100 | 0.15 |
| 0.3 | 150 | 0.125 |
| 0.4 | 80 | 0.20 |

This needs about 100 families with at least 4 search and 3 held-out compounds. The count is metadata only and not yet made [U]. Each family is used once, so far fewer than 4,528 compounds are needed.

**S1, calibration.** Brier score of the stated p, A3 vs A2. A2's p comes from bootstrap stability. This tests whether the agent knows which of its bets are weak (the refusal claim).

**S2, decision.** Confirmed edits may change only the observation request and the refusal scope of later campaigns. The backend stays fixed, so the contrast is acquisition-like.
- The recorded agent-vs-lookahead SE is 0.022 at 2,304 compounds: MDE 0.062, about 0.044 at 4,528 [V, POWER.json]. That SE comes from near-identical arms, so it must be re-measured.
- Edits that change the predictor take the R1 SE (0.199; MDE 0.56 / about 0.40). Those are declared descriptive in advance.
- S2 runs only if H0 headroom is at least 15%.

## 4. Arms (same episodes, grammar, data, one edit each)

| Arm | What it does |
|---|---|
| **Zero** | Random admissible edit. Gives the base rate and the empirical false-positive rate. |
| **Fixed** | "No interaction". For S2: the fixed A-optimal read order. |
| **A1** | `policies.PSBAXPolicy` posterior sampling (S2 only, no edits). |
| **A2** | Conventional enumerator: all family × feature edits ranked by the `fit_interaction` F-statistic with a stability bootstrap. |
| **A2k** | Non-LLM knowledge rule. |
| **A3** | Agent: deepseek-flash, at most 3 calls per episode, about $1-3 total [U]. |
| **A3-blind** | A3 with identities masked. |

Every arm gets the same aggregate `D_search` view through `masked_interface`.

## 5. Kill and stop rules

- **Stage 0 (metadata only):** stop if fewer than 80 eligible families. Pilot on fold 0: stop if the projected MDE exceeds 0.20.
- **Agent claim withdrawn** if any of:
  - the one-sided 95% upper bound of P1 is below +0.10;
  - the lower bound of A3 − A2k is at or below 0;
  - A3 does not beat Zero.
- **Typed-edit thesis withdrawn** if neither A2 nor A3 beats Zero's false-positive rate by more than 0.10. That means there is no identifiable family × state structure.
- **No decision claim** unless H0 passes and the lower bound of S2 exceeds 0.1875.

## 6. Three ways this could be wrong

1. **Memorised biology.** deepseek-flash may recall published PRISM or DepMap associations (for example MDM2 × TP53), so a win could be retrieval. A2k and A3-blind bound this but cannot exclude it, and every tier is exposed. Confirmation needs a later screen, such as the sealed PRISM 24Q2, which needs the user's authorisation.
2. **Truer edits that do not move decisions (the R1 precedent).** P1 can pass while S2 is null. That would support "proposes truer edits", not "improves campaigns".
3. **Dependence and multiplicity.** Families share targets and lineages, so clustering may roughly double the SE. The confirmation test's error rate also varies with cell size. The guard is Zero's empirical false-positive rate. Otherwise the MDEs above are optimistic.
