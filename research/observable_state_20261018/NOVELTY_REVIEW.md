# Novelty review and decision (2026-10-18)

Status: review record, no result. Nothing was run on data. Inputs: `POSITIONING.md`, `POWER.json`, and `ENHANCEMENT.md` (written by an Opus-5.5-class
subagent at the user's conditional instruction; model output, not evidence).

## Verdict on the original idea

Not sufficiently novel. Its ingredients are all published or already in this repository, the part that is new (typed state edits
judged on decision utility and transfer) cannot be resolved on PRISM (`POWER.json`), and its adaptive layer has no headroom
(+7.3% held-out; batch-EIG is outcome-independent, so it is a fixed design).

## Verdict on the enhanced idea (decision exchange rate of an L1000 read)

Better posed and cheap ($0, local, family-clustered, nulls built in), but **my check against the repository finds three problems the
subagent did not state:**

1. **Large overlap with Block N** (`src/virtual_cell/transcriptional_transfer.py` docstring; EVIDENCE.md "Mechanism routing"): the
   same translator, the same PRISM x GSE92742 intersection and the same question "does L1000 add to a partial viability screen" were
   run on 421 sealed drugs: +0.049 [+0.004, +0.097] over ridge on a 160-line screen, no gain on a 40-line screen. The new content
   is the unit (pool-equivalents), a deranged-profile and a generic-toxicity null, a near/far lineage split, and nomination utility
   instead of selective r. That is a re-expression with extra controls, not a new finding-in-waiting.
2. **Input mismatch.** The promoted translator uses L1000 responses from 9 lines x 6/24 h; the proposal assumes one profile in one
   line (only MCF7, PC3, A375, A549, HT29, HEPG2 have > 1,000 overlapping compounds). A single-line translator is untested and is
   likely weaker; this changes the arms and the power statement.
3. **It drops the Scientific Agent and the typed-edit object**, which are the user's stated thesis. That is a change of research
   question, not an enhancement of the same one, and is the user's decision.

Also unverified (as stated by the subagent): that nobody has published the exchange-rate estimand; the 1 CPU-hour estimate; the
MDE in pool-equivalents (0.35 events per pool is a mean over three pools, not a marginal value). The overlap compounds (about 41% of
PRISM) have already been opened by earlier blocks, so any result is development only.

## Decision

Do **not** launch Stage 1 on the enhanced idea yet. Reasons: the overlap with a completed, sealed-tier block makes the expected
increment small; the single-line input is untested; and it abandons the agent thesis without the user's say. What is justified now:

* keep `research_edit.py`, `masked_interface.py`, `campaign.py` and the baselines (reusable under either direction);
* if the user chooses the exchange-rate direction, the next step is Stage 0 only (no outcomes): a single-line-input translator spec,
  cross-fit rules, near/far strata, hashed freeze, and a feasibility read of the gctx subset (23.4 GB file; h5py is installed).

Options for the user are listed in the closing message of the session; none is run.

## Addendum: agent-centred redesign (`ENHANCEMENT_AGENT.md`, model output), repository cross-check

Direction chosen by the user: keep the agent and typed-edit thesis. The redesign makes each ResearchEdit one small registered bet per MoA family,
scores the share confirmed on held-out compounds x lineages (A3 agent vs A2 enumerator vs non-LLM knowledge rule A2k vs identity-masked A3-blind),
and lets power come from the number of bets. My checks:

* **Differs from earlier work in the estimand and unit, not in the proposal grammar.** `program_revision_20261017` already ran LLM-proposed
  scope x observable-state programs on this same PRISM data: LLM vs enumeration +0.004, 62-88% of candidates had insufficient evidence,
  20-23% committed to the wrong direction, and its own report recommended curated non-LLM proposals as the comparator. The redesign's A2k
  arm is that recommendation, and its prior is a null for the agent. The new test is therefore a well-powered falsification, not an
  expected win; the thesis survives only if the agent beats A2 AND A2k.
* **Stage-0 count (labels only, no outcomes):** 1,145 MoA families, none crossing a fold; families with >= 5 / 7 / 10 / 15 compounds:
  203 / 149 / 102 / 64. The agent note's ~100 eligible families therefore needs >= 10 compounds per family, and that is before the
  within-family chemical separation (held-out compounds at Tanimoto < 0.5 from the family's search compounds) shrinks it further.
  Eligibility must be recounted with that purge before the 80-family stop rule can be applied. Large families may also be generic classes.
* **MDE 0.15-0.20 is a paired-binary formula, not from POWER.json,** and ignores target/lineage dependence (which the note says may double the SE).
* **Memorisation:** every PRISM tier is exposed; A3-blind and A2k bound but do not exclude retrieval. Real confirmation needs data the
  user has not authorised (sealed PRISM 24Q2).

Status: still a proposal. No Stage 0 beyond the label count above has been run; nothing frozen; no LLM call made.
