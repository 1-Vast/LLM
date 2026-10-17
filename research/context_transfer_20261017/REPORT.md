# Context transfer with verified bridges: results

Study `context_transfer_20261017`. One-shot confirmation on Beat AML 2.0, run on 2026-10-17
after the freeze (`FREEZE.json`, 04:43:08Z). The run took 2,209 s. `verify.py` recomputes every
reported number from the cached records and prints `VERIFIED`. Post-hoc analyses (§5) were run
after the confirmation, on now-exposed data, and are labelled as such.

> **Amendment (2026-10-17, after the run): claims and units.**
> * `CLAIMS.json` (`claims.py`) keeps CONFIRMED as the record of protocol execution and states what
>   is established. Supported: the functional-feedback gain under this replay. Not established:
>   * a cell-state model beyond the population prior;
>   * a procedure-selection gain;
>   * an LLM gain;
>   * the repaired planner (development);
>   * a total-cost advantage.
> * As frozen, C3 (adaptivity) is decided by P5 non-inferiority. C4 (beats fixed pipelines)
>   passes on any of P1, P2 or P6. Neither tests what its name says, and P6 beat a defective
>   comparator. "SUPPORTED" means a positive gain; P1's lower bound (0.025) does not show a gain
>   above the frozen minimum useful effect of 0.05.
> * A "well" below is one archived AUC query: one 7-dose profile, 112 treatment wells for 16
>   queries if run. Bridged arms need a second round (about 72 h). The analysed matrix has 165
>   inhibitors (the census's 166 includes one measured only without RNA-seq).
> * Every fold refits on Beat AML source patients. This is workflow transfer, not biological
>   knowledge transfer from PRISM.
> * The follow-up attribution study is `research/feedback_attribution_20261017`.

## 1. Verdict

**Framework verdict: CONFIRMED** under the frozen definitions (C1–C4 all hold). The claims are
narrower than the label suggests:

* The gain comes from the agent bridging. It measures the Virtual Cell's top four inhibitors
  first, then re-ranks the other twelve from the readouts.
* The Virtual Cell prior alone was no better than the context-free item prior.
* The agent matched the standard exploit-first design; it did not beat it.
* The development procedure that the agent rejected (lookahead) lost because of an
  implementation defect (§5), not because value-of-information planning fails on primary
  samples.

All values are per patient sample at 16 wells. Intervals are 95% patient-cluster bootstrap
intervals (479 patients, 520 samples). p values are one-sided sign-flip p values, Holm-adjusted
over P1–P6.

| ID | Contrast | Mean | 95% interval | Holm p | Verdict |
|---|---|---|---|---|---|
| P1 | `maestro` − `vc0` | +0.073 | [+0.025, +0.127] | 0.0075 | SUPPORTED |
| P2 | `maestro` − `b_exploit` | 0.000 | [0.000, 0.000] | 1.0 | NOT_SUPPORTED (same procedure) |
| P3 | `maestro` − `match_panel` | +0.229 | [+0.162, +0.298] | 0.0006 | SUPPORTED |
| P4 | `vc0` − `knn` | +0.075 | [+0.014, +0.137] | 0.017 | SUPPORTED |
| P6 | `maestro` − `b_lookahead` | +0.108 | [+0.051, +0.172] | 0.002 | SUPPORTED |
| P5 | `maestro` − best fixed in hindsight (`b_exploit`) | 0.000 | [0.000, 0.000] | 0.0006 | NON_INFERIOR (trivially) |

Claims: C1 Virtual Cell transfer (P4), C2 Virtual Cell beyond pilot matching (P3), C3 agent
adaptivity (P5) and C4 agent beats fixed pipelines (P1 or P6).

**The agent's choices.** In all five patient-disjoint folds, the source replay chose
exploit-first bridging:

| Fold | Rank | Inner exploit gain (z) | Inner lookahead gain (z) | Inner samples |
|---|---|---|---|---|
| 0 | 40 | +0.114 (3.43) | −0.031 (−1.83) | 413 |
| 1 | 10 | +0.077 (3.18) | −0.054 (−2.77) | 404 |
| 2 | 20 | +0.081 (2.80) | −0.055 (−3.02) | 422 |
| 3 | 20 | +0.075 (2.34) | −0.068 (−3.35) | 438 |
| 4 | 20 | +0.099 (2.96) | −0.047 (−2.45) | 403 |

**The pre-registered expectation was wrong.** PROTOCOL §9.5, written before any outcome was
read, expected the agent to decline to bridge, with PARTIAL as the most likely verdict. On the
AML-shaped PRISM proxies bridging had not paid. On real patient samples the agent bridged in
every fold, and the source replay's choice matched the outcome replay.

## 2. Every arm

| Arm | Level | Hits per sample | Wasted wells per sample |
|---|---|---|---|
| `random` (zero arm) | L0 | 0.200 | 6.01 |
| `item` | L0 | 0.785 | 2.76 |
| `knn` | L0 | 0.702 | 3.67 |
| `vc0` | L0 | 0.777 | 2.34 |
| `b_random` | L1 | 0.762 | 3.41 |
| `b_exploit` | L1 | 0.850 | 2.53 |
| `b_panel` | L1 | 0.717 | 2.66 |
| `b_info` | L2 | 0.746 | 2.69 |
| `b_lookahead` (frozen `lookahead_v1`) | L2 | 0.742 | 4.81 |
| `match_panel` | L1 | 0.621 | 3.29 |
| `maestro` | L3 | 0.850 | 2.53 (see §4) |
| `vc0_xshuffle` (control) | — | 0.696 | 2.32 |
| `maestro_yshuffle` (control) | — | 0.746 | — |
| `llm` (secondary) | L1/L2 | 0.835 | 2.55 |
| `oracle` | — | 1.963 | — |

* Over 8,320 wells, `maestro` found 442 events, `vc0` 404, `item` 408 and the oracle 1,021.
* 283 of 520 samples had at least one event.
* About 62% of sample–inhibitor pairs are measured. A well on an unmeasured pair is spent and is
  never a hit, which is why even `vc0` wastes 2.3 of 16 wells.

## 3. Secondary analyses (no familywise claim)

| Contrast | Mean | 95% interval | One-sided p |
|---|---|---|---|
| `vc0` − `item` | −0.008 | [−0.063, +0.050] | 0.63 |
| `knn` − `item` | −0.083 | [−0.148, −0.021] | 0.99 |
| `vc0` − `vc0_xshuffle` | +0.081 | [+0.031, +0.137] | 0.003 |
| `maestro` − `maestro_yshuffle` | +0.104 | [+0.048, +0.166] | 0.0005 |
| `b_exploit` − `vc0` | +0.073 | [+0.025, +0.127] | 0.002 |
| `b_lookahead` − `vc0` | −0.035 | [−0.070, −0.002] | 0.98 |
| `b_lookahead` − `b_info` | −0.004 | [−0.057, +0.047] | 0.58 |
| `b_lookahead` − `b_panel` | +0.025 | [−0.020, +0.072] | 0.16 |
| `match_panel` − `vc0` | −0.156 | [−0.215, −0.093] | 1.0 |
| `maestro` − `knn` | +0.148 | [+0.085, +0.218] | 0.0002 |
| `llm` − `b_lookahead` | +0.092 | [+0.041, +0.148] | 0.0007 |
| `llm` − `maestro` | −0.015 | [−0.050, +0.010] | 0.86 |
| repair `maestro@1` − none | 0.000 | [−0.014, +0.013] | 0.61 |
| repair `maestro@2` − none | −0.006 | [−0.018, +0.004] | 0.91 |
| repair `maestro@4` − none | −0.002 | [−0.012, +0.006] | 0.75 |
| model averaging − none | −0.004 | [−0.027, +0.017] | 0.69 |
| `maestro` − `item` (post hoc, not registered) | +0.065 | [+0.002, +0.132] | 0.028 |

* **Virtual Cell prior.**
  * It did not beat the item prior. Its P4 win over `knn` is largely `knn`'s own weakness.
  * The basal profile matters against a wrong one (the shuffled-context control) but not, on
    this endpoint, against none.
  * Source scaling, with source patients subsampled and `vc0` against `knn`: 25% gave 0.446
    against 0.323, 50% gave 0.727 against 0.667, 100% gave 0.777 against 0.702.
* **Feedback.** The bridge readouts carry the gain. Readouts from another patient (`maestro_yshuffle`)
  lose 0.104 hits.
* **Repair and model averaging** added nothing, as in development. They were not promoted.
* **Misfit as a failure detector.**
  * The model-level failure rate is 10.2%: 53 samples where `vc0` had fewer hits than `item`.
  * The AUROC of bridge misfit for these failures is 0.578. That is weak.
  * It is computed on the lookahead bridge, as the protocol's repair variants are.
* **LLM arm.**
  * The gate (C1 or C2) opened. deepseek-flash made 520 calls, all valid: 792,288 prompt and
    32,566 completion tokens, at most 0.2768 USD.
  * The registered increment criterion (`llm` − `b_lookahead` > 0, p < 0.025) is formally met.
    But its comparator is the defective lookahead (§5). The LLM picked bridges much as
    exploit-first does: 0.394 bridge hits per sample against exploit's 0.396.
  * It did not beat `maestro` (−0.015) or the corrected lookahead (−0.015 [−0.076, +0.041],
    post hoc).
  * No agent-reasoning increment is claimed.

## 4. Process report (Zhao et al. 2026 categories)

* **Environment-level errors:**
  * wasted wells per arm, in §2;
  * the confirmation's own process report gives 4.81 for `maestro`, which is a reporting error
    (`DEVIATIONS.json`): it is the lookahead arm's figure;
  * the selected procedure, `b_exploit`, wasted 2.53 wells per sample.
* **Model-level errors:** prior failure 10.2%. Recovery given failure (the arm reaches at least
  `item`'s hits):
  * `maestro` 28%;
  * `knn` 43%;
  * `llm` 32%;
  * `match_panel` 30%;
  * `b_lookahead` and `b_panel` 19%.
* **Planning- and tool-level errors:** 0 invalid LLM selections and 0 protocol errors.
* **Sub-task completion:**
  * 93% of samples got at least one lookahead bridge readout;
  * only 29% of lookahead bridge wells returned a readout (§5).
* **Human interventions:** 0, by construction of the replay.

## 5. Post-hoc diagnosis of the lookahead loss (exploratory)

The development winner lost on Beat AML. Its bridge wells came back measured only 29% of the
time, against exploit's 88%, and the bridge items' mean source measurement rate was 0.29,
against 0.62 for the library. Two post-hoc scripts look for the cause. They read Beat AML
outcomes after the confirmation had opened them, and they change no confirmatory number.

**Not a wasted-well effect (`posthoc_availability.py`, `POSTHOC_AVAILABILITY.json`).**
* The script replaces each item's source measurement rate with the target's measured-pair
  indicator. That is the replay analogue of a laboratory where every chosen inhibitor can be
  plated.
* Exploit still beat lookahead by +0.137 [+0.077, +0.203] hits per sample.
* The lookahead still sent 68% of its bridge wells to pairs it knew were unmeasured, which
  have exactly zero value. Its value estimates for measured items had to be negative.

**A baseline defect in the greedy batch step (`agent.bridge_design._lookahead`).**
* After the first pick, the lookahead shrinks the covariance for the items already in the batch
  but keeps the prior hit chances as its baseline.
* The model's own expectation under the shrunk covariance falls below that baseline, so every
  later candidate carries a negative bias of about the same size.
* Multiplied by the measurement rate q, the bias favours rarely measured items, including
  inhibitors that can never be events (q ≈ 0.01).
* On PRISM, q ≈ 0.975 for every item, so the bias barely changed the ranking and the defect
  stayed hidden. The first pick is unaffected by construction. In traced Beat AML samples it was
  a well-measured inhibitor; picks 2 to 4 went to items with q ≈ 0.01.
* A dense-grid check showed that the 12-node Gauss–Hermite quadrature itself is accurate
  (correlation 0.9997).

**The correction (`posthoc_lookahead.py`, `POSTHOC_LOOKAHEAD_*.json`).**
* At every greedy step, the source package's rule `lookahead` re-scores the decision items and
  the baseline under the shrunk covariance. This is the consistent form of the kriging-believer
  batch heuristic (Ginsbourger, Le Riche and Carraro, 2010): the earlier picks are treated as
  observed at their predicted means.
* It also clips the value of information at zero, which theory guarantees.
* The frozen rule is kept as `lookahead_v1`.
* On all three domains, the promoted modules reproduce the study's records context by context
  for `vc0`, `b_exploit` and `lookahead_v1`.

| Domain (post hoc) | `vc0` | `b_exploit` | `lookahead_v1` | corrected `lookahead` | corrected − v1 | corrected − exploit | bridge wells measured (v1 → corrected) |
|---|---|---|---|---|---|---|---|
| Beat AML, W 16, k 4 | 0.777 | 0.850 | 0.742 | 0.850 | +0.108 [+0.060, +0.168] | 0.000 [−0.061, +0.064] | 29% → 89% |
| PRISM 19Q4 line holdout, W 32, k 8, rank 40 | 2.298 | 2.636 | 2.673 | 2.697 | +0.025 [−0.016, +0.064] | +0.062 [−0.031, +0.169] | 97% → 97% |
| PRISM 19Q4 lineage holdout, W 32, k 8, rank 40 | 1.935 | 2.158 | 2.275 | 2.229 | −0.046 [−0.104, +0.003] | +0.070 [−0.043, +0.224] | 97% → 98% |

On PRISM, where q ≈ 0.975 for every item, the correction is neutral. Neither version beats
exploit there with an interval that excludes zero at this configuration. The development
lookahead's edge over exploit was +0.04 to +0.12 hits per line, and only one of four
development configurations had an interval above zero.

**What this changes.**
* P6 stays SUPPORTED as frozen. The agent was right to reject the transferred procedure in this
  domain, and its source check caught the failure before any target well was spent.
* What it caught was a latent defect that appears only when measurement rates vary across
  items. It was not evidence that lookahead planning is worse for primary samples.
* With the defect corrected, lookahead ties exploit on Beat AML. The agent's choice would then
  matter little.
* The corrected rule is development-grade: it was fixed after seeing these outcomes and has no
  confirmation.

## 6. Costs

* **Wells:** 0 purchased (retrospective replay); 16 per sample in every arm.
* **Assay rounds:**
  * `maestro` needs 2 rounds per sample, one extra ex vivo turnaround of about 72 h, with the
    primary sample banked between rounds;
  * `vc0`, `item` and `knn` need 1.
* **API:** 0.2768 USD for the confirmation's LLM arm, plus 0.0156 USD for the PRISM pilot, both
  deepseek-flash. The cap was 3 USD.
* **Data:** about 354 MB of Beat AML 2.0 release files, downloaded 2026-10-17.
* **Compute:** 2,209 s for the confirmation, plus a few minutes per post-hoc script.

## 7. Promoted components and their scope

| Module | Scope (see each docstring) |
|---|---|
| `src/virtual_cell/bridged_transfer.py` | `VALIDATED_SCOPE` = Beat AML 2.0 inhibitor AUC selective events, 16 wells, patient-disjoint. Supported against nearest-context transfer; not against the item prior. |
| `src/agent/bridge_design.py` | Exploit-first bridge confirmed (+0.073 over no bridge). `lookahead_v1` lost (defect). Corrected `lookahead` is development-grade. |
| `src/agent/procedure_selection.py` | `hybrid` rule confirmed with `lookahead_rule="lookahead_v1"`. With the corrected default it has not been re-run on these domains. |
| `tools/datasets/design_census.py`, `tools/evaluation/bridge_replay.py` | Planning aids on exposed data, not confirmations. |

## 8. Limits

* One confirmation domain and one endpoint: Beat AML ex vivo inhibitor AUC, with selective events
  relative to other patient samples.
* The replay cannot grade unmeasured pairs. A prospective campaign could plate every chosen
  inhibitor, so wasted wells would vanish and the availability structure would differ.
* The selector's inner standard error treats samples as independent (520 samples, 479 patients).
* P5 holds trivially, and P2 is zero by construction once the agent chose exploit.
* The Virtual Cell's basal-expression prior did not add over item-level knowledge on this
  endpoint. The useful component here is the updatable response model with bridge feedback.
