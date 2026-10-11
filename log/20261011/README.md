# Experiment record: 2026-10-11

> - **Path**: `log/20261011/README.md`
> - **Purpose**: Record block N, which asks where an LLM adds value to a virtual cell. The task is
>   predicting which cancer lines a compound kills (PRISM 19Q4), using the requirements added on
>   2026-10-11: knowledge-heavy LLM roles, few cheap datasets, ablation against strong non-LLM
>   methods.
> - **Core points**:
>   - On 421 sealed drugs (101 killers), the virtual cell's L1000 transfer beat curated targets
>     (+0.116 [+0.053, +0.181]) and chemistry (+0.100) for unseen mechanisms.
>   - It replicated on the independent secondary screen and added to a 160-line partial screen
>     (+0.049).
>   - No LLM role added value. The critic (-0.052) and the forecaster added to the virtual cell
>     (-0.025) harmed it.
>   - The transfer was promoted to `src/virtual_cell/transcriptional_transfer.py`.

## 1. Record control

**Block N** (`research/astra/mechanism_routing_20261011`):
* registered and frozen at `2026-10-10T18:02:47Z` (755 files and 1,408 development agent
  outputs; 2026-10-11 02:02 local);
* evaluated once on the sealed confirmation tier (`RESULTS.json`, run 285 s);
* verified (`VERIFIED.json`, `VERIFIED_SUPPLEMENT.json`).

Timestamps are UTC unless marked local. The block folder is named for the local date.

Changes outside the block folder:
* `.gitattributes`: a `-text -whitespace` entry, so freeze hashes survive checkout;
* `pyproject.toml`: test-scope registration;
* `src/virtual_cell/transcriptional_transfer.py` and `tests/test_transcriptional_transfer.py`
  (promotion);
* `README.md`, `research/EVIDENCE.md`, `research/REPORT.md` and `research/INDEX.md`.

`git status` and a file-time scan showed no change by another actor between the freeze and this
record. Two Codex sessions (01:41 and 01:48 local, before the freeze) ran in `D:\SASG-ST`,
not this tree.

## 2. Research questions and hypotheses

Can the dual core predict which of 578 lines a compound kills at 2.5 uM, scored as selective r
after removing the generic killing profile? Does the LLM add value beyond the virtual cell (VC)
and strong non-LLM methods?

Registered contrasts (`PROTOCOL.md`), with predictions set from projected power:

* **VC:**
  * V1-V3: unseen class, VC vs targets, vs chemistry, vs the L+T+C ensemble.
  * V4: known class, VC added to the class mean.
  * V5-V6: VC vs ridge on a 40-line partial screen; VC added to ridge on a 160-line partial
    screen.
  * V7: V1 on the secondary screen.
  * V8: trust by top similarity.
* **Agent:**
  * A1-A3: forecaster vs targets; forecaster added to the VC; literature vs none.
  * A4: critic vs the VC.
  * A5-A6: explainer vs mining; explainer added to the VC.
  * A7: agent judgement added to VC trust.
* **Headline:**
  * VC value confirmed if V1 and V6 pass.
  * Agent value shown if any A contrast passes.

## 3. Materials, data and computational environment

All inputs are local and public, with no download beyond those already in `data/`:
* GSE92742 L1000 Level 5 (block M extraction): 9 lines x 6/24 h, 10 uM;
* PRISM Repurposing 19Q4: primary screen, and secondary screen at the dose closest to 2.5 uM;
* CCLE 19Q4 expression and mutations;
* Drug Repurposing Hub 2020-03-24 annotations, for non-commercial use.

Tiers are extracted once (`TIERS_RECEIPT.json`):
* open: `block_n_prism_open.npz`, 982 drugs;
* sealed: `block_n_prism_sealed.npz`, 421 drugs, refused with `TIER_SEALED` until the freeze.

Literature came from Europe PMC (keyless), up to 6 abstracts per drug. Hits mentioning
PRISM, Corsello, Repurposing Hub or DepMap were dropped.

The LLM was deepseek-flash through `agent.llm`, thinking off, with JSON completion. Development
also ran flash with thinking and deepseek-v4-pro (`models.py`).

## 4. Experimental design and controls

* **Units.** 1,403 drugs split within mechanism class (seed 20261011): 701 reference,
  281 development, 421 confirmation. At confirmation the reference pool was 982 drugs.
* **Killers.** Drugs killing >= 5% of lines (log fold change < -1): 101 confirmation drugs.
* **Unseen-class regime.** Same-class drugs are removed from every pool and from the agent's
  vocabulary.
* **VC `L`.** kNN-5 transfer by mean L1000 cosine over shared conditions.
* **Comparators:**
  * Hub target kNN;
  * Morgan kNN;
  * their ensemble with L;
  * the class mean;
  * ridge and top-5 mining on 40 or 160 discovery lines, scored on 281 held-out test lines.
* **Agent arms, one call per drug:**
  * `route_lit` and `route_nolit`: forecaster;
  * `adjudicate_lit`: critic of the VC's 10 neighbours;
  * `explain_full`: top and bottom 20 of 40 discovery lines.

  Trust arms ran for all 421 drugs; the others ran for the killers.
* **Statistics.** Mechanism-class cluster bootstrap, 4,000 draws, Bonferroni within each family
  (8 VC, 7 agent).
* **Controls:**
  * Zero arm: G scores 0, and random trust scores the mean.
  * Outcome poisoning: rehearsed on development drugs and repeated on the sealed tier.
  * Leak rescan.
  * Name masking (development).
  * The development rehearsal reproduced every development number at zero new spend.

## 5. Experiment register and results

Development (open drugs, exploratory; `feasibility/`, `development/`):
* Text-prior claims and anomaly adjudication were weak or underpowered, so they were dropped.
* On 69 killers, the forecaster did not beat targets, and the critic (-0.060) and explainer
  harmed the VC.
* Neither thinking mode nor pro changed the forecaster or explainer.
* Agent trust on all 281 drugs gave no decision gain (AUCC +0.004).

Confirmation (`RESULTS.json`), family-wise intervals:

| id | estimate | interval | verdict | predicted |
|---|---|---|---|---|
| V1 | +0.116 | [+0.053, +0.181] | PASS | PASS |
| V2 | +0.100 | [+0.030, +0.177] | PASS | PASS |
| V3 | +0.039 | [+0.002, +0.078] | PASS | PASS |
| V4 | +0.038 | [+0.007, +0.076] | PASS | NOT_SUPPORTED |
| V5 | +0.059 | [-0.023, +0.148] | NOT_SUPPORTED | NOT_SUPPORTED |
| V6 | +0.049 | [+0.004, +0.097] | PASS | PASS |
| V7 | +0.103 | [+0.049, +0.160] | PASS | PASS |
| V8 | +0.097 | [+0.042, +0.150] | PASS | PASS |
| A1 | +0.011 | [-0.032, +0.055] | NOT_SUPPORTED | NOT_SUPPORTED |
| A2 | -0.025 | [-0.051, -0.003] | HARM | NOT_SUPPORTED |
| A3 | -0.009 | [-0.023, +0.006] | NOT_SUPPORTED | NOT_SUPPORTED |
| A4 | -0.052 | [-0.091, -0.017] | HARM | HARM |
| A5 | -0.012 | [-0.044, +0.018] | NOT_SUPPORTED | NOT_SUPPORTED |
| A6 | -0.020 | [-0.048, +0.012] | NOT_SUPPORTED | NOT_SUPPORTED |
| A7 | +0.007 | [-0.007, +0.027] | NOT_SUPPORTED | NOT_SUPPORTED |

**Headline:**
* VC value confirmed; agent value not shown; agent harm in A2 and A4.
* 13 of 15 predictions held.

Mean selective r for the unseen class:
* VC 0.153;
* targets 0.038;
* chemistry 0.053;
* forecaster 0.049;
* critic 0.101.

Post hoc (`posthoc/`):
* The critic kept none of the VC's 10 neighbours for 64% of killers.
* The forecaster found no routable class for 42%.
* Skipping missing reference values changes mean selective r by ≤ 0.001.

## 6. Deviations, failures and corrections

* **D1.** The frozen verification check `recomputed_contrasts_match` failed.
  * Cause: 16-digit CSV floats turned one last-bit difference between identical routes into a
    tie. That moved one drug in A3's descriptive `share_negative`.
  * Effect: every registered estimate, interval, verdict and the headline match within 8.3e-17
    (`VERIFIED_SUPPLEMENT.json`, post freeze).
  * `verify.py` and `VERIFIED.json` were left as written.
* **Pre-freeze correction.** `pearson` now treats variance below 1e-10 as undefined, so a pure
  generic-profile prediction scores 0, not floating-point noise. The development rehearsal was
  identical before and after.
* **Development failures** (before the freeze, recorded in `development/*.log`):
  * flash-with-thinking truncated at 16k tokens; it was retried at 32k, and the failed records
    were kept as `*.failed.json`;
  * the pro run was stopped once pro calls approached the ceiling, and the up to 16 in-flight
    calls were booked at $0.80 reservation.

## 7. Interpretation and claim boundaries

* **Supported.** For compounds whose mechanism has no screened member, transcriptional
  similarity carries killing-pattern information that curated targets and chemistry lack. It is
  replicated on an independent re-screen and complements a partial screen.
* **Not supported:**
  * that the VC replaces a 40-line screen;
  * any LLM contribution in the four tested roles.
* **Harmful roles.**
  * The LLM critic discards the cross-mechanism neighbours that carry the VC's value.
  * Adding the forecaster's mechanism routes dilutes the VC.
* **Out of scope:**
  * other assays and doses;
  * mechanism-of-action claims;
  * clinical response.

The LLM's memorised knowledge of PRISM cannot be excluded, but it could only have inflated agent
scores. The pro critic lead (14 development drugs) is unresolved because the budget would not
cover a confirmation run.

## 8. Reproduction and artifact ledger

Receipts in this folder:

* `MECHANISM_ROUTING.json`: identities, decisions, contrasts, means, trust, verification,
  development and post hoc summaries, spend and promotion;
* `MECHANISM_ROUTING_VERIFY.txt`;
* `MECHANISM_ROUTING_CORE.txt` and `mechanism_routing_core.xml`;
* `MECHANISM_ROUTING_TESTS.txt` and `mechanism_routing_tests.xml`.

Code, protocol, agent outputs, literature, development records, rehearsal, results and post hoc
analyses are in `research/astra/mechanism_routing_20261011/`. Bulk tiers are in
`data/external/prism_19q4/derived/` (git-ignored).

Promoted, with contract tests:
* `src/virtual_cell/transcriptional_transfer.py`
  * tests: `tests/test_transcriptional_transfer.py`;
  * parity with the frozen arithmetic: `test_promotion_parity.py`.

**Spend.**
* Provider: $7.46 of the $10 block ceiling, $1.24 of it for the 1,044 confirmation calls
  (`tmp/mechanism_routing_spend.json`).
* Lab units: none.

## 9. Open items and next experiments

* **Pro critic.** Resolve the lead (14 development drugs) with a registered confirmation run. It
  needs about $3.6 at current rates and a ceiling decision by the owner.
* **A different critic prompt.** Test one that judges neighbours by shared *phenotype* (killing
  pattern, stress response) rather than annotated mechanism. The post hoc failure mode points
  there. It must be registered on new drugs, because the confirmation tier is now exposed.
* **Wiring.** Connect `virtual_cell.transcriptional_transfer` to the orchestrator's prediction
  path, behind a scope check.
* **Second assay.** Test the transfer on GSE70138 phase 2 compounds and a non-PRISM viability
  assay.
* **Pre-existing failure.** `tests/test_repository_shape.py` still fails on the root
  `Innovation.md` (see `log/20261010/README.md` section 9).

## 10. Curation provenance

Prepared on 2026-10-11 from the machine records:
* `RESULTS.json`, `VERIFIED.json`, `VERIFIED_SUPPLEMENT.json` and `DEVIATIONS.json`;
* `posthoc/*.json` and the development JSONs;
* the test receipts.

No number in this record was typed independently of those records. Frozen files were not edited
after the freeze.

## Additional 2026-10-11 record: block P, selective discovery

Block P (`research/astra/selective_discovery_20261011/`) is a separate study recorded on the same
date. It asks whether the dual core helps a *campaign*: given a compound library profiled only by
L1000 and a screening budget, find compounds that selectively kill one tumour lineage. Receipt:
`20261011/SELECTIVE_DISCOVERY.json`.

**Record control.** Registered in the block's `PROTOCOL.md`, frozen `2026-10-11T04:32:30Z`
(67 files and 2,920 pre-freeze LLM prior records hashed), run once on a sealed tier of **975 PRISM
compounds that appear in GSE70138 and in no earlier block**, then verified from the campaign
ledgers. Pre-freeze disclosure: one sealed-tier statistic had been seen (325 of 987 candidates kill
at least 5% of lines), recorded in `EXTRACT_RECEIPT.json`.

**Design.** 38 campaigns = 3 disjoint libraries of 325 x the lineages with a reachable hit. Every
arm received the same library, budget (32 screens, 10%), batch size (5) and menu: 1,216
compound-screens each. The primary endpoint is the **unexpected hit**, a hit whose annotated
mechanism class has no selective member for that lineage among the 1,403 reference compounds.
Verdicts come from an exact cluster sign-flip test over the 14 lineages.

**Results.** Headline `NOT_CONFIRMED`: the registered rule required H1, H2 and H6, and H2 failed.

* **H1 PASS.** The virtual cell adds unexpected hits: **+17** [+11, +23], p = 0.00098. Ten lineages
  favoured it, three tied, none opposed, so the p-value is at the floor this design can reach.
* **H2 NOT_SUPPORTED.** The agent loop adds +14 total hits over the one-shot virtual cell
  (141 vs 127) at p = 0.075 against a 0.025 bar, and it spends **266 plate turnarounds instead of
  38** for the same wells. On the primary endpoint the one-shot virtual cell is level (66 vs 69) and
  better on the strictest novelty count (37 vs 31).
* **H4 NOT_SUPPORTED, as predicted.** A conventional LLM-agent-with-tool loop matched the proposed
  system: 136 hits and 72 unexpected against 141 and 69. The architectural elaboration is not
  justified by its own evidence.
* H3 PASS (+46 unexpected over a fixed workflow), H6 PASS (not inferior to the deterministic
  planner), H7 PASS (+28 hits confirmed on the independent secondary screen).
* H5, H8, H9 NOT_SUPPORTED, all as predicted: feedback is directionally positive (+12 [+4, +20]) but
  fails family-wise; the conventional agent's feedback sensitivity is weaker (+8); the two-stream
  portfolio adds nothing (-1).
* Seven of nine registered predictions were correct; the single miss is H2.

**Controls.** Zero arm 18 of 210 reachable hits. Outcome permutation collapses every arm
(maestro 141 to 20, virtual cell 127 to 31, random 18 to 12). Feedback-permutation twins are
registered arms. The LLM prior scores the same with compound names withheld (AUROC 0.803 against
0.792), so its signal is annotation rather than recall of PRISM. **No refusal code fired in 418
campaign runs**, including the stopping rule, so those paths are tested but unexercised.

**Verification.** 418 campaign ledgers recomputed from the recorded selections: 0 mismatches on
hits, unexpected hits and verified hits, and 0 integrity violations. Both primary contrasts
reproduce to 0.0 with identical verdicts. `ok` is false only for three declared file-hash
mismatches, recorded as deviations D1 (a two-line plumbing fix after the run crashed on its first
LLM campaign, both hashes recorded), D2 (the freeze wrongly hashed its own deviations log) and D3 (a
tie tolerance added to the sign-flip test after a parity test caught a last-bit disagreement;
recomputation showed all nine verdicts bit-identical).

**Cost.** 1,216 compound-screens per arm, 13,376 across the 11 arms; 38 turnarounds for one-shot
arms and 266 for adaptive ones. Provider USD 1.32 of a USD 10 ceiling over 3,261 deepseek-flash
calls, of which USD 1.03 and 2,920 calls were the pre-freeze priors. No other model was used.

**Promotion.** Only `tools.evaluation.scoring.cluster_signflip_test`, beside the existing
`cluster_bootstrap_interval`, with parity tests. The campaign agent is **not** promoted, because H2
and H4 leave its contribution unestablished.

**Another session's block on this date.** `research/astra/adaptive_investigation_20261011/` belongs
to the block N session, which left it running. It completed unattended and **reversed its own 8-unit
smoke result**: adaptive viability acquisition beats a fixed panel on 247 units (0.210 against 0.169
at budget 16). Read-only copies and provenance are in the block P packet's `preserved/`. Block P
neither designed nor registered it.
