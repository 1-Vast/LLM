# Context transfer with verified bridges: protocol

Study `context_transfer_20261017`. Written 2026-10-17.

* **Development.** Ran on PRISM 19Q4, an exposed MAESTRO asset (development grade). Every
  development configuration and its result is disclosed in `DEVELOPMENT.json` and §9.
* **Confirmation.** Beat AML 2.0, downloaded on 2026-10-17 and never used by MAESTRO before.
  Before the freeze, only identifier and design columns of its curve-fit table were read
  (`census.py`, `CENSUS.json`). No AUC value was parsed.
* **Freeze.** `FREEZE.json` records this protocol, the code, the development results, the census
  and the bytes of every confirmation input. `confirm.py` refuses to run if any digest differs,
  and writes `RESULTS.json` once.

## 1. Question

Can a dual-core research system move its knowledge into a new biological context? It works on a
small well budget. It may measure a few *bridge* items first and verify the transfer before
nominating the rest. Whether bridging is worth an extra assay round in a domain is decided from
that domain's own source data. The questions are:

* Does it find more context-specific hits at equal wells than:
  * the strongest conventional transfer workflows;
  * a standard exploit-first two-stage design;
  * pilot-screen matching without a response model?
* Does the method, designed on cancer cell lines, transfer unchanged to primary leukaemia samples
  from patients?

The review in `log/transfer_review_20261017/REVIEW.md` motivates the design: verification and
paired bridges, retrieval of analogues, and a Virtual Cell judged by decisions.

## 2. Domains

| | Development (PRISM 19Q4) | Confirmation (Beat AML 2.0) |
|---|---|---|
| Context | cancer cell line (568; 561 with basal expression) | primary AML RNA-seq sample with basal expression (520 samples, 479 patients) |
| Item | compound (4,532 Broad cores) | single-agent inhibitor (166) |
| Response | log2 fold change at 2.5 µM, replicate-collapsed | probit-fit AUC, release paper-inclusion set |
| Context feature | CCLE 19Q4 log2 TPM | release normalised expression |
| Dependence cluster | primary tissue (24) | patient (dbGaP subject) |
| Outer folds | 5, SHA-256 of DepMap ID | 5, SHA-256 of subject ID |
| Well budget W / bridge k | 32 / 8 | 16 / 4 (§9) |

Lower response means a stronger effect in both domains.

## 3. Endpoint (inherited)

The selective event is taken from `research/knowledge_reality_20261013` §5 and applied to the
full measured matrix.

* G is the per-context median over items.
* Each item's response is residualised on [1, G] across contexts.
* An event is a robust z of that residual ≤ −3, for items measured in at least 100 contexts.
* The PRISM absolute gate log2 FC ≤ −1 is kept in development.
* The gate is dropped for Beat AML, because AUC has no comparable constant.
* An unmeasured pair is never an event.
* A well spent on an unmeasured pair is consumed, reveals nothing and is not a hit.
* No arm's candidate set depends on the target's outcome availability.

## 4. The system (dual core)

* **Virtual Cell** (`vc.ContextModel`), fitted on source contexts only.
  * Response model: y_c = μ + V f_c + ε, with rank r.
  * Fit (version 2): unmeasured source pairs are imputed by 15 iterations of EM-SVD at rank r.
    Each item's noise variance is its residual variance on measured pairs, corrected for the r
    fitted loadings by n_i/(n_i − r). Version 1 used mean imputation and in-sample noise.
  * Prior on f_c: a ridge map from 30 principal components of the 2,000 most variable source
    genes. Alpha is chosen by leave-one-out. The prior covariance is the covariance of the
    leave-one-out residuals.
  * Measured items update f_c by Bayesian linear regression.
  * Per-item event thresholds come from source-only residual fits on G, so P(event) targets the
    grader's rule.
  * Every score is an expected hit per well: q_i × P(event), where q_i is the item's source
    measurement rate. A well on an unmeasured pair yields nothing. Information gains are weighted
    by the same q_i.
    * This was added after the census showed that Beat AML measures about 69% of sample–inhibitor
      pairs (`CENSUS.json`, design columns only).
    * PRISM measures about 97.5%, so the change is nearly neutral there.
    * `knn` and `match_panel` already score by neighbour event counts, which include
      unmeasured pairs as non-events.
  * **Rank, chosen by decisions.** In each outer fold, every rank in {5, 10, 20, 40} is replayed
    in a 3-fold inner cross-validation on that fold's source contexts (inner folds by patient on
    Beat AML). Inner events are recomputed from source outcomes only. The rank is the one with
    the most inner Virtual Cell hits; ties go to the smaller rank. Every Virtual Cell arm of the
    fold uses this rank.
* **Agent** (`agent.py`, `procedure.py`).
  * Bridge rules: exploit-first, or decision lookahead. Lookahead is the one-step value of
    information for the final top-(W − k) expected hits, plus the bridge item's own hit chance.
    An unmeasured bridge well spends its well and leaves the decision unchanged.
  * **Source-verified procedure choice** (the "hybrid" rule of `procedure.choose`, selected among
    three candidate rules by the criterion pre-declared in `RULE_CHOICE.md`; §9.5). At the fold's
    rank, the agent compares three procedures on the same inner replay:
    * no bridge (`vc0`);
    * exploit-first bridge (`b_exploit`);
    * lookahead bridge (`b_lookahead`).

    A bridge is adopted only if its paired inner gain over no bridge has z > 1.645, one-sided
    5%, because a bridge costs an extra assay round. If both pass, the larger z wins, and ties go
    to exploit. Otherwise the agent declines to bridge. The inner standard error treats samples
    as independent, although the 520 Beat AML samples come from 479 patients.
  * Verification of the transferred prior (bridge misfit) is reported. No repair is applied:
    development showed covariance-inflation repair to be harmful and model averaging to be
    neutral (§9).
* **Utility.** All W wells count toward utility.

## 5. Arms (equal W wells per context)

The autonomy level follows the six-level spectrum of Zhao et al. (npj Drug Discovery 3, 43,
2026); see `log/transfer_review_20261017/REVIEW.md` §10. All Virtual Cell arms use the fold's
selected rank.

| Arm | Level | Bridge | Final nominations | Role |
|---|---|---|---|---|
| `random` | L0 | none | hash-seeded random | zero arm |
| `item` | L0 | none | source event rate of the item | context-free prior |
| `knn` | L0 | none | event rate in the 10 nearest source contexts by basal expression | conventional context transfer |
| `vc0` | L0 | none | Virtual Cell prior | Virtual Cell alone (non-agent pipeline) |
| `b_exploit` | L1 | top-k prior expected hits | posterior | standard exploit-first two-stage design |
| `b_random` | L1 | random | posterior | bridge-choice control |
| `b_panel` | L1 | fixed population D-optimal panel per fold | posterior | fixed reference panel |
| `b_info` | L2 | target-specific D-optimal on f_c | posterior | response-information design |
| `b_lookahead` | L2 | decision lookahead | posterior | decision-focused design |
| `match_panel` | L1 | same panel as `b_panel` | event rate of the 10 source contexts best correlated on the panel | pilot matching without the Virtual Cell |
| `maestro` | L3 | the procedure the agent selected on source data | as selected | full system |
| `vc0_xshuffle` | control | none | prior from another target's basal profile | context-correspondence control |
| `maestro_yshuffle` | control | as `maestro` | posterior on another target's bridge readouts (equal to `vc0` when no bridge is selected) | permuted-feedback control |
| `llm` (secondary) | L1/L2 | deepseek-flash chooses k of a 30-item shortlist | posterior | agent-reasoning increment |
| `oracle` | — | — | min(W, events) | ceiling |

Secondary repair variants are computed on the lookahead bridge, with that bridge held fixed:

* `maestro@t`: covariance inflation by the misfit when it exceeds t (t = 1, 2, 4). `maestro@inf`
  means no repair.
* `maestro_bma`: Bayesian model averaging of the transferred prior and the population prior,
  weighted by the marginal likelihood of the bridge readouts.

## 6. Hypotheses on Beat AML (confirmatory)

Each primary hypothesis is a per-context paired difference in hits at W = 16 wells.

| ID | Contrast | Claim |
|---|---|---|
| P1 | `maestro` − `vc0` | The agent's procedure choice adds hits over the Virtual Cell alone |
| P2 | `maestro` − `b_exploit` | The agent beats the standard exploit-first two-stage design |
| P3 | `maestro` − `match_panel` | The system beats pilot matching without the Virtual Cell |
| P4 | `vc0` − `knn` | The Virtual Cell prior beats nearest-context transfer |
| P5 | `maestro` − best fixed procedure in hindsight ≥ −0.05 | The agent's choice is non-inferior to the best of `vc0`, `b_exploit` and `b_lookahead` chosen on target outcomes |
| P6 | `maestro` − `b_lookahead` | The agent beats transferring the development winner unchanged (the lookahead bridge won on PRISM) |

**Statistics.**
* Mean per-context difference.
* 95% interval by patient-cluster bootstrap (2,000 draws).
* One-sided sign-flip p over patient-cluster means (10,000 draws, seed 20261017). For P5 the test
  is on the difference plus the margin 0.05.
* Holm adjustment across P1–P6 at a familywise one-sided α = 0.025.

**Verdicts.**
* P1–P4 and P6:
  * **SUPPORTED:** Holm-adjusted p < 0.025 and the interval's lower bound > 0.
  * **NOT_SUPPORTED:** the interval's upper bound is below the minimal useful effect of 0.05 hits
    per sample, one extra hit per 20 patient samples at the same wells.
  * **HARMFUL:** the upper bound is below 0.
  * **INCONCLUSIVE:** otherwise.
* P5:
  * **NON_INFERIOR:** Holm-adjusted p < 0.025 and the interval's lower bound > −0.05.
  * **NOT_SHOWN:** otherwise.

  The comparator is chosen on target outcomes, so it is optimistic and the test is conservative.
  P5 is informative only where the hindsight-best procedure differs from the agent's choice. If
  the agent picks it in every fold, the difference is 0 and P5 holds trivially; this is reported.

**Secondary analyses** (no familywise claim):
* every arm's mean hits;
* each bridge rule against `vc0`, and `b_lookahead` against `b_exploit`, `b_info` and `b_panel`;
* each repair variant against `maestro@inf`;
* the AUROC of bridge misfit for prior failure (`vc0` < `item`);
* both controls against their parents;
* `llm` against `b_lookahead` (same rank, deterministic bridge) and against `maestro`;
* `vc0` and `knn` with source patients subsampled to 25% and 50% by hash, at the full-source
  ranks;
* the agent's per-fold choices and their inner bridge gains.

**Process report.** This report follows the reporting requirements of Zhao et al. 2026 (REVIEW.md
§10). It is descriptive, with no test.

* Environment-level errors: wasted wells per arm, where a well is spent on an unmeasured pair.
* Model-level errors: prior failure, where `vc0` gets fewer hits than `item`. Report its rate,
  its detection AUROC by bridge misfit, and the recovery rate given failure. Recovery means the
  arm reaches at least `item`'s hits.
* Planning-level errors: `llm_invalid_selection`.
* Tool-level errors: `llm_protocol_error`.
* Sub-task completion: the share of bridge wells that returned a readout, and the share of LLM
  selections that were valid.
* Human interventions: 0, by construction of the replay.

## 7. Decision on the framework claim

| Claim | Requires |
|---|---|
| C1 Virtual Cell transfer | P4 SUPPORTED |
| C2 Virtual Cell beyond pilot matching | P3 SUPPORTED |
| C3 Agent adaptivity | P5 NON_INFERIOR |
| C4 Agent beats fixed pipelines | P1, P2 or P6 SUPPORTED |

* **CONFIRMED:** C1–C4 all hold.
* **PARTIAL:** at least one holds. The holding claims are named.
* **NOT_CONFIRMED:** none holds.

C4 can fail correctly. If bridging adds nothing in this domain and the agent declines to bridge,
P1 is 0 by construction. The value of declining is then P6: the agent against the PRISM winner
transferred unchanged, which also spends an extra assay round. P6 was added before the freeze,
after the proxies showed that bridging may not pay in this domain (§9.6).

**The LLM arm is gated.** A standing project rule holds that paid LLM components are not
activated until independent evidence shows that the underlying scientific method adds value.
`llm` therefore runs only after the deterministic analysis, and only if C1 or C2 holds on Beat
AML. Otherwise it is recorded as `NOT_RUN` with reason `LLM_GATE_CLOSED`, and no call is made.
When it runs, the agent-reasoning increment counts only if `llm` − `b_lookahead` > 0 with
p < 0.025. It is secondary.

## 8. Costs

* Retrospective, 0 wells purchased.
* Equal wells per context in every arm.
* Bridge wells count toward the same budget and toward hits.
* Assay rounds:
  * arms without a bridge need 1 round;
  * bridge arms need 2 rounds, one extra assay turnaround (about 72 h for an ex vivo AML panel).
    Primary samples would have to be banked between the rounds. This is a practical cost that
    the replay does not price.
  * `maestro`'s mean rounds per sample are reported.
* API spend for `llm` is reported separately and capped at 3 USD. It is zero if the gate in §7
  stays closed. The 30-line PRISM pilot spent
  0.0156 USD.
* Wall-clock seconds are reported.

## 9. Frozen design choices from development

All development used PRISM 19Q4, an exposed asset, and a PRISM proxy shaped like Beat AML. No
Beat AML outcome was read before the freeze; the census read design columns only. Every
configuration below is in `DEVELOPMENT.json` or `POWER.json` with its per-context records in
`tmp/context_transfer_20261017/`, and `verify.py` recomputes the reported means from them. Times
are UTC on 2026-10-17.

### 9.1 What was frozen

| Choice | Frozen value | Basis |
|---|---|---|
| Wells per context | PRISM 32; Beat AML 16 | Beat AML: about 10% of the 166-inhibitor panel |
| Bridge size k | W/4 (8 on PRISM, 4 on Beat AML) | at W = 32 the lookahead's edge over exploit was +0.07 (k = 4), +0.10 (k = 8), −0.04 (k = 16) |
| Virtual Cell fit | version 2 (EM-SVD imputation, 15 iterations, degrees-of-freedom-corrected noise) | equal to version 1 on PRISM; better Virtual Cell alone on the random proxy (0.403 against 0.386 at rank 10); the structured proxy was run with version 2 only (§9.3) |
| Scores | expected hits per well, q_i × P(event) | added after the census showed about 69% measured pairs |
| Rank | most inner Virtual Cell hits over {5, 10, 20, 40} | the log-density rule did not track decisions (§9.4); the one-SE rule was too conservative (§9.5) |
| Procedure | bridge only if inner paired z > 1.645 (`hybrid` rule) | chosen by the pre-declared minimax-regret criterion (§9.5) |
| Repair | none; misfit reported | covariance inflation harmful, model averaging neutral (§9.2) |
| Endpoint, folds, statistics | as §3, §2 and §6 | inherited or fixed before development |

### 9.2 PRISM development (W = 32)

Round 1 (launched 02:40, maestro environment). Six configurations of the first version: scores
were P(event) without the measurement rate, the lookahead was as in §4 except for the
measurement-rate terms, and `maestro` was the lookahead with covariance-inflation repair at
misfit > 2.

| Configuration | k | Rank | Regime | `vc0` | `b_exploit` | `b_lookahead` | lookahead − `vc0` | lookahead − exploit | repaired − lookahead |
|---|---|---|---|---|---|---|---|---|---|
| `main_w32_b8_r20` | 8 | 20 | line | 2.262 | 2.505 | 2.607 | +0.345 [+0.218, +0.522] | +0.102 [-0.016, +0.243] | -0.032 [-0.071, +0.004] |
| `w32_b4_r20` | 4 | 20 | line | 2.262 | 2.410 | 2.479 | +0.217 [+0.103, +0.360] | +0.069 [-0.007, +0.135] | -0.060 [-0.106, -0.021] |
| `w32_b16_r20` | 16 | 20 | line | 2.262 | 2.618 | 2.577 | +0.315 [+0.179, +0.496] | -0.040 [-0.141, +0.097] | -0.063 [-0.112, -0.014] |
| `w32_b8_r10` | 8 | 10 | line | 2.206 | 2.305 | 2.386 | +0.180 [+0.090, +0.287] | +0.081 [-0.005, +0.167] | -0.056 [-0.099, -0.016] |
| `w32_b8_r40` | 8 | 40 | line | 2.294 | 2.613 | 2.725 | +0.431 [+0.307, +0.610] | +0.113 [-0.021, +0.273] | -0.046 [-0.081, -0.011] |
| `lineage_w32_b8_r20` | 8 | 20 | lineage | 1.900 | 2.130 | 2.252 | +0.352 [+0.238, +0.519] | +0.121 [+0.042, +0.244] | -0.046 [-0.078, -0.020] |

Round 2 (launched 03:14, maestro environment). Expected-hit scoring, the fixed lookahead, every
arm and control, and the repair sweep, at rank 40, for both fit versions and both split regimes.

| Configuration | `item` | `knn` | `vc0` | `b_exploit` | `b_lookahead` | `match_panel` | `vc0_xshuffle` | lookahead − `vc0` | `vc0` − `knn` | inflation@2 − none | averaging − none |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `v1_line_w32_b8_r40` | 1.621 | 1.928 | 2.305 | 2.581 | 2.717 | 1.449 | 1.394 | +0.412 [+0.293, +0.584] | +0.377 [+0.223, +0.510] | -0.039 [-0.072, +0.000] | -0.030 [-0.068, +0.017] |
| `v1_lineage_w32_b8_r40` | 1.585 | 1.588 | 1.937 | 2.220 | 2.312 | 1.248 | 1.507 | +0.375 [+0.243, +0.536] | +0.349 [+0.154, +0.534] | -0.030 [-0.064, +0.018] | -0.009 [-0.057, +0.043] |
| `v2_line_w32_b8_r40` | 1.621 | 1.928 | 2.298 | 2.636 | 2.673 | 1.415 | 1.359 | +0.375 [+0.278, +0.510] | +0.370 [+0.237, +0.494] | -0.039 [-0.067, -0.010] | -0.042 [-0.102, +0.004] |
| `v2_lineage_w32_b8_r40` | 1.585 | 1.588 | 1.935 | 2.158 | 2.275 | 1.254 | 1.470 | +0.340 [+0.238, +0.481] | +0.347 [+0.183, +0.512] | -0.037 [-0.067, -0.008] | -0.030 [-0.067, +0.005] |

* Bridging pays on PRISM: the lookahead bridge adds 0.34–0.41 hits per line over the Virtual Cell
  alone at the same 32 wells, in both regimes and both fit versions.
* The Virtual Cell prior beats nearest-context transfer by 0.35–0.38 hits per line. With another
  line's basal profile (`vc0_xshuffle`), it falls below the context-free item prior in both
  regimes. So the prior's value comes from the context correspondence.
* Pilot matching on the fixed panel without the Virtual Cell is far worse than the Virtual Cell
  alone (−0.68 to −0.88).
* Repair: covariance inflation at thresholds 1 and 2 is worse than no repair (−0.04 to −0.06).
  Its intervals exclude 0 for the version-2 fit and reach or cover 0 for version 1. Model
  averaging is −0.01 to −0.04, with every interval covering 0. Both were dropped.

### 9.3 Proxy shaped like Beat AML (W = 16, k = 4)

Two proxies from PRISM: 166 items measured in at least 300 lines, masked per item to a Beat AML-like
measurement rate (a quarter of items at 0.4–19%, the rest at 60–97%). "Random" picks items by hash;
"structured" picks inhibitor MOA families with at least 3 members, ranked by mean events.

| Configuration | Proxy | Rank | `item` | `knn` | `vc0` | `b_exploit` | `b_lookahead` | `b_panel` | `match_panel` | lookahead − `vc0` | `vc0` − `knn` |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `v1_w16_b4_r10` | random | 10 | 0.342 | 0.326 | 0.386 | 0.386 | 0.393 | 0.359 | 0.290 | +0.007 [-0.016, +0.026] | +0.060 [+0.014, +0.103] |
| `v2_w16_b4_r5` | random | 5 | 0.342 | 0.326 | 0.401 | 0.377 | 0.386 | 0.377 | 0.324 | -0.016 [-0.049, +0.011] | +0.076 [+0.025, +0.117] |
| `v2_w16_b4_r10` | random | 10 | 0.342 | 0.326 | 0.403 | 0.379 | 0.380 | 0.386 | 0.294 | -0.023 [-0.046, -0.003] | +0.077 [+0.035, +0.108] |
| `v2_w16_b4_r20` | random | 20 | 0.342 | 0.326 | 0.408 | 0.370 | 0.364 | 0.400 | 0.308 | -0.044 [-0.076, -0.015] | +0.083 [+0.045, +0.116] |
| `s_v2_w16_b4_r5` | structured | 5 | 0.614 | 0.683 | 0.688 | 0.680 | 0.662 | 0.687 | 0.516 | -0.026 [-0.082, +0.024] | +0.005 [-0.070, +0.071] |
| `s_v2_w16_b4_r10` | structured | 10 | 0.614 | 0.683 | 0.708 | 0.697 | 0.692 | 0.651 | 0.479 | -0.016 [-0.053, +0.014] | +0.025 [-0.042, +0.080] |
| `s_v2_w16_b4_r20` | structured | 20 | 0.614 | 0.683 | 0.732 | 0.739 | 0.694 | 0.644 | 0.461 | -0.039 [-0.090, +0.002] | +0.049 [-0.029, +0.120] |

* On the random proxy, no bridge rule beats the version-2 Virtual Cell alone at any rank. On the
  structured proxy, exploit-first bridging gains a little at ranks 20–40 (+0.03 hits at rank 40
  in the menu), and lookahead gains nothing. The panel is small and sparse: bridge wells cost a
  large share of the budget, and many land on unmeasured pairs.
* The Virtual Cell prior beats nearest-context transfer on both proxies, by 0.06–0.08 (random)
  and 0.005–0.05 (structured).
* Conclusion carried to the design: whether to bridge depends on the domain, so the agent must
  decide from the domain's own source data (§4).

### 9.4 Rank

`RANK_CHECK.json`: the inner log-density rule (`vc.select_rank`) chose ranks 10–20 on PRISM, where
rank 40 gave the most hits, so a likelihood rule does not track decisions. It is kept in `vc.py`
but not used. The rank is chosen by inner decisions instead.

### 9.5 Procedure selector

Each rule cell gives the mean hits, the relative regret, and the folds that bridge.

| Setting | Best fixed (hindsight) | `evidence` | `max` | `hybrid` |
|---|---|---|---|---|
| PRISM, line holdout | `b_lookahead@40` 2.673 | 2.643, 1.1%, 5/5 | 2.644, 1.1%, 5/5 | 2.629, 1.6%, 5/5 |
| PRISM, lineage holdout | `b_lookahead@40` 2.275 | 1.903, 16.3%, 2/5 | 2.190, 3.7%, 5/5 | 2.183, 4.0%, 5/5 |
| Proxy, random | `vc0@20` 0.408 | 0.410, -0.4%, 0/5 | 0.398, 2.6%, 2/5 | 0.405, 0.9%, 0/5 |
| Proxy, structured | `b_exploit@40` 0.771 | 0.688, 10.7%, 0/5 | 0.710, 8.0%, 5/5 | 0.727, 5.7%, 2/5 |

Maximum relative regret: `evidence` 16.3%, `max` 8.0%, `hybrid` 5.7%. The pre-declared criterion (`RULE_CHOICE.md`, written before either proxy menu had finished) selects **`hybrid`**, which is frozen. Per-fold choices are in `RULE_CHOICE.json`.

The frozen system (`hybrid`) in development. Each cell is the mean per-context difference with
its cluster-bootstrap 95% interval. Primary-contrast analogues compare against arms at the
selected rank (`sel_*`), as in the confirmation.

| Setting | P1 analogue (− `vc0`) | P2 (− `b_exploit`) | P6 (− `b_lookahead`) | P3 (− `match_panel`) | P4 (`vc0` − `knn`) |
|---|---|---|---|---|---|
| PRISM, line | +0.336 [+0.230, +0.485] | +0.009 [−0.074, +0.116] | −0.032 [−0.111, +0.052] | +1.213 [+0.902, +1.609] | +0.364 [+0.231, +0.497] |
| PRISM, lineage | +0.262 [+0.169, +0.399] | +0.018 [−0.078, +0.144] | −0.007 [−0.025, 0.000] | +0.930 [+0.772, +1.139] | +0.333 [+0.156, +0.487] |
| Proxy, random | 0 (never bridges) | +0.028 [+0.010, +0.045] | +0.025 [0.000, +0.056] | +0.111 [+0.065, +0.150] | +0.079 [+0.035, +0.115] |
| Proxy, structured | −0.012 [−0.045, +0.019] | −0.014 [−0.038, +0.011] | +0.023 [−0.014, +0.063] | +0.248 [+0.121, +0.408] | +0.056 [−0.023, +0.127] |

**Expectations for Beat AML, written before any outcome is read.** These come from the
AML-shaped proxies, which may not resemble real patient samples. Approximate power at 479
patient clusters is from `POWER.json`. It is computed at one-sided α = 0.025/4, and the Holm
family now has six tests, so it is slightly optimistic.

* P3: likely SUPPORTED (+0.11 to +0.25; power ≈ 1).
* P4: uncertain. Power is 0.87 on the random proxy and 0.12–0.26 on the structured proxy.
* P1: near 0 if the agent declines to bridge, as it did on the random proxy.
* P2 and P6: small positive gains if the agent declines (+0.02 to +0.03). Power is 0.13–0.44, so
  INCONCLUSIVE is the most likely verdict.
* P5: likely NON_INFERIOR, possibly trivially (§6).
* So the most likely framework verdict is PARTIAL, with C2 and C3 holding.

### 9.6 Deviations and incidents during development

* **Lookahead baseline (fixed 03:07).** When the measurement rate q was added (02:52), the
  lookahead's baseline still counted items already in the bridge batch, while the candidate's
  value excluded them. Before q, that offset was the same for every candidate and changed no
  choice. With q, it was scaled by q_c and so favoured rarely measured items: only about 1 of 4
  bridge wells returned a readout. Affected: the five round-1 proxy runs `aml_*` (their
  lookahead-based arms `b_lookahead`, `maestro`, `maestro@t`, `maestro_yshuffle` are
  uninterpretable; other arms are valid), the LLM pilot's `b_lookahead` and `maestro` values,
  and two `final_*` PRISM runs, which were stopped before writing. After the fix about 3.1 of 4
  bridge wells return a readout.
* **Interpreter.** The `aml_*` runs, the rank check and the LLM pilot ran under C:\Python314
  (numpy 2.4.4). Every other run used `D:\anaconda\envs\maestro\python.exe` (Python 3.11.16,
  numpy 2.4.6, scipy 1.17.1), which is the confirmation interpreter. Round-2 and later outputs
  record it themselves. For round 1, the interpreter is known from the launch command.
* **Proxy mask.** A first version of the proxy compared a 256-bit hash with a rate, so every pair
  was masked; fixed (02:57) before any proxy run.
* **Selector variant A (superseded).** A joint argmax over rank × {no bridge, exploit, lookahead,
  lookahead with model averaging}, with any positive inner gain switching to a bridge
  (`procedure_variant_a.py`; runs `v1_auto_w16_b4`, `v2_auto_w16_b4`, `s_v2_auto_w16_b4`). It
  followed inner noise. Two runs of a no-margin rule with the final structure (`*_autoF_*`) were
  stopped unfinished and are not reported. Every later rule was chosen with knowledge of these
  runs.
* **LLM pilot.** 30 PRISM lines, 30 valid exact-k selections, no refusal, 0.0156 USD. Its hits
  decide nothing.
* **Changes to the confirmatory design made before the freeze, with knowledge of development.**
  * P6 (`maestro` − `b_lookahead`) was added to the Holm family. C4 now also holds if P6 is
    SUPPORTED. The reason: the proxies showed that bridging may not pay on a small, sparse panel,
    so the agent's decision to decline is best tested against transferring the PRISM winner.
  * The LLM arm was gated on C1 or C2, to respect the standing rule on paid LLM components.
  * The selection rule went through three stages:
    * "max" was replaced by "evidence" after the variant-A runs;
    * "evidence" then proved too conservative on the PRISM lineage menu;
    * the frozen rule was chosen among "evidence", "max" and "hybrid" by a criterion written down
      (`RULE_CHOICE.md`, 04:21) after both PRISM menus and before either proxy menu had finished.
    The "hybrid" rule itself was defined after the PRISM menus had been seen.
  * No Beat AML outcome had been read at any of these changes.
* **Selector compute on PRISM.** Inner targets are capped at 40 per inner fold on PRISM only;
  Beat AML uses every source sample.
