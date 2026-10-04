> **File summary**
> - **Path**: `research/certified_discovery/README.md`
> - **Purpose**: report of the certified dual-core discovery block. It covers the design,
>   development on O'Neil 2016, the single pre-registered confirmatory run on NCI-ALMANAC
>   2017, promotion to `src/` and `tools/`, limits and reproduction.
> - **Core points**:
>   - Confirmatory verdict: H1 PASS, H2 PASS, framework SUPPORTED, with a modest effect.
>     The certified loop finds +2.8% more measured synergies than static retrieval at equal
>     wells and days (+4.9% without the audit); random finds 6.6x fewer.
>   - In-context feedback and the history-trained prior carry the gain. Single-agent cell
>     state and uncertainty-aware acquisition add nothing. An LLM planner added nothing on
>     development and could not be tested on confirmation, where every selection was invalid.
>   - Certificates hold on real data under every planner, including the LLM. The world
>     model's own claims are 1.4-2.1x too optimistic.
> - **Interfaces / data**: `DESIGN.md` (frozen design), `protocol/` (plans, freeze, vault log),
>   `results/` (receipts); promoted modules `src/maestro/certification.py`,
>   `src/virtual_cell/combination_world.py`, `src/agent/discovery.py`,
>   `tools/datasets/combination_screens.py`, `tools/evaluation/discovery_replay.py`.
> - **Depends on**: `research/topics/virtual_cell_world_models/dual_core_obstruction_map_20260929.md`.

# Certified dual-core discovery

## 1. Question and answer

Can the dual core decide better than simple policies, and can its claims be trusted, on a task
where predictions actually decide outcomes? Here the agent plans purchases and claims, and the
virtual-cell world model predicts each cell line's combination responses.

The answer is a qualified yes. One registered run on an independent screen (NCI-ALMANAC,
60 cell lines, 304,943 experiments, 8,722 measured hits, opened once at 17:58:48 against an
intact freeze) gives:

| Registered test | Result | Verdict |
|---|---|---|
| H1: certified dual-core loop vs static retrieval, hits per line | +2.58 [0.57, 4.93] (34 lines better, 25 worse) | PASS |
| H2: certified nominations | FDR 0.043 [0.032, 0.054] (rule <= 0.2, upper bound <= 0.25); yield-bound coverage 0.958 (rule >= 0.87) | PASS |
| Framework claim (both) | | SUPPORTED |

The effect is real but small: the certified loop finds 5,752 hits and history-based retrieval
5,597. Static retrieval is a strong baseline here, recovering 64% of a line's hits with 10% of
its experiments. The design and its literature basis are in [DESIGN.md](DESIGN.md), written and
frozen before the opening.

## 2. What was built

- **World model** (`world.py`; promoted as `virtual_cell.combination_world`). It is an
  empirical-Bayes transfer model:
  - a prior mean from combinations measured in other lines and from single-agent cell state;
  - an in-context residual of a line effect plus drug-in-line effects, updated in closed form
    from the agent's purchases;
  - variances fitted only on history lines.
  The Woodbury form keeps all algebra at (drugs + 1) dimensions. A world build fell from 24 s
  (first, dense version) to 0.1 s, and a campaign over 5,000 candidates takes 0.27 s.
- **Agent** (`agent.py`, `llm_agent.py`; promoted as `agent.discovery`). Planners range from
  fixed rules, retrieval and world-model variants to a DeepSeek planner that sees the line's
  evidence with (`named`) or without (`blind`) the model's scores. The last round either
  exploits or buys a uniformly random audit from the world model's top 2 x batch.
- **Certificate** (`certify.py`; promoted as `maestro.certification`). From the random audit
  it gives:
  - conformal p-values with Benjamini-Hochberg, so nominations from the untested remainder
    have FDR <= alpha;
  - an exact hypergeometric lower bound on the hits still in the remainder.
  Both hold whatever chose the earlier purchases, because the audit is design-randomised
  inside the agent's own shortlist.

## 3. Protocol

| Step | Record |
|---|---|
| Development plan before any arm ran | `protocol/dev_plan.json` (17:40) |
| Development runs (O'Neil, exposed) | `results/dev_20261003_v1`, `_v2`, `dev_llm_20261003_v2`; invalid run kept: `dev_llm_20261003_v1/INVALID.md` |
| Confirmatory protocol and verdict code | `protocol/confirmatory.json`, `verdict.py` |
| Dry run of the whole confirmatory procedure on a synthetic release | caught one analysis crash before the freeze |
| Freeze | `protocol/freeze.json`, 18 files, SHA-256 `222ef72b...5508`, 17:58:20; digest written into `log/20261003/README.md` section 16 before opening |
| Single opening | `protocol/vault_log.jsonl` (prior openings 0), `results/confirm_almanac_20261003/run_log.json` |

- **Unit**: the target cell line, with history drawn from the other lines.
- **Budget**: 10% of a line's candidates in four rounds, kappa 2, alpha 0.2, delta 0.1, and 20
  audit draws and 20 random seeds per line.
- **Labels**: the dataset's own Bliss-type excess. For ALMANAC this is NCI's SCORE. A hit is a
  label above 10 (the SynergyFinder convention).
- **Costs**:
  - O'Neil: 64 wells per experiment and 20 days per campaign.
  - ALMANAC: dose-point records (median 9 per experiment) and 12 days per campaign.
  - Provider spend is reported separately.

## 4. Confirmatory results (NCI-ALMANAC 2017)

Hits found at equal budget (sum over 60 lines; 8,722 hits exist; budget about 513
experiments per line):

| Arm | Exploit | Certify | Recall (exploit) |
|---|---:|---:|---:|
| oracle (ceiling) | 8,658 | 8,539 | 0.993 |
| wm_nocontext | 5,897 | 5,779 | 0.676 |
| wm_greedy | 5,887 | 5,773 | 0.675 |
| **wm_full (dual core)** | **5,873** | **5,752** | 0.673 |
| wm_static (no feedback) | 5,744 | 5,704 | 0.659 |
| wm_shuffled (context permuted) | 5,638 | 5,544 | 0.646 |
| history (static retrieval) | 5,597 | 5,566 | 0.642 |
| wm_menu_random (random choice from the model's 2k menu) | 5,521 | 5,509 | 0.633 |
| heuristic_potency | 1,916 | 1,900 | 0.220 |
| heuristic_headroom | 1,103 | 1,108 | 0.126 |
| random (zero arm) | 875 | 873 | 0.100 |

LLM arms: section 4.3.

### 4.1 Registered secondary estimates (per line, 95% bootstrap over lines)

| Estimate | Value | Reading |
|---|---|---|
| S1 feedback: wm_full - wm_static | +2.15 [0.70, 3.62] per line (sum +129) | The closed loop helps. On ALMANAC the history-trained prior also beats raw retrieval (+2.45 [0.63, 4.73]); on O'Neil it did not |
| S2a cell-state context: wm_full - wm_nocontext | -0.40 [-1.82, 1.20] (sum -24) | Single-agent context adds nothing, as on development |
| S2b vs shuffled context | +3.92 [1.88, 6.25] (sum +235) | Permuted context hurts; true context is merely neutral |
| S3 uncertainty: wm_full - wm_greedy | -0.23 [-0.75, 0.30] (sum -14) | P(hit) acquisition adds nothing over the posterior mean |
| S4 optimizer's curse | claimed / realised remainder hits 1.58 [1.39, 1.80]. "P(hit) >= 0.5": claimed 84.4 of 139.4 true (61%), measured 40.3 (29%) | The model's own claims about what it selected are about 1.6-2x optimistic. This replicates on a new task and screen the 2x under-forecast that blocks E2, dual_core_v2 and maestro_vc_v1 |
| S5 price of certification | 121 hits (2.1%); 2.02 [1.37, 2.70] per line | The audit costs about 2 hits per line |
| S9 ladder | 6.6x random; 3.0x the best single-agent rule | Prediction binds this task, unlike the mechanism-class proxy |
| S10 nominations | 28.2 nominated over 60 lines (7.6 true) | The marginal FDR guarantee is honest but weak in practice, because the audit hit rate after exploitation is 6.2% |

The lawful claim that carries weight here is the **yield bound**. Over 60 lines the certified
lower bounds sum to 224.5 of the 469 hits still in the untested remainders, with coverage
0.958. "At least this many hits remain in these 127 untested candidates" is something a lab
can plan on. The model's own expected count would overstate it by 1.58x.

### 4.2 Development compared with confirmation

| | O'Neil 2016 (development, 39 lines) | NCI-ALMANAC 2017 (confirmatory, 60 lines) |
|---|---|---|
| Base rate | 3.3% | 2.9% |
| wm_full[certify] - history, per line | +1.52 [0.64, 2.57] | +2.58 [0.57, 4.93] |
| Relative gain over history (exploit) | +18.5% | +4.9% |
| Feedback (S1) | +1.74 [1.03, 2.51] | +2.15 [0.70, 3.62] |
| Context (S2a) | -0.03 [-0.72, 0.69] | -0.40 [-1.82, 1.20] |
| Claimed / realised | 1.72 [1.34, 2.39] | 1.58 [1.39, 1.80] |
| FDR / coverage | 0.045 / 0.972 | 0.043 / 0.958 |
| Price of certification | 15 hits (3.1%) | 121 hits (2.1%) |

The direction of every registered estimate replicated. The relative discovery gain shrank by
almost four-fold, which is the expected regression after development choices were made on
O'Neil.

### 4.3 LLM planner arms (secondary S6-S8)

The registered LLM comparisons failed their own validity check on the confirmatory screen. They are
reported as protocol failures, not as tests of an LLM planner.

- **What went wrong.** Each round asked DeepSeek (deepseek-flash, temperature 0) to choose about
  128 of 256 shortlisted ids. In every one of 480 rounds it returned the whole menu or more
  (median 256 ids, at most 464) instead of choosing:
  - 468 rounds were recorded as `LLM_INVALID_SELECTION`;
  - 12 more as `LLM_UNAVAILABLE` (unparseable replies).
  The registered repair keeps the first k valid ids. At k = 15 on O'Neil every selection was
  valid; at k of about 128 none was.
- **llm_named.** It echoed the menu in the world model's order, so its purchases equal
  wm_full's (S7 = 0.00 in every line). That is an artefact of the repair and says nothing about
  LLM judgment.
- **llm_blind.** It returned a re-ordered shuffled menu. The first k of its order found 5,639
  hits, against 5,521 for a uniform choice from the same menu. The registered S6 estimate is
  +1.96 [0.75, 3.19] per line, but every one of those rounds broke the validity rule. On
  O'Neil, where the blind planner's selections were valid, it equalled random choice
  (-0.17 [-0.71, 0.36]). It never beat the world model's own ranking (5,639 vs 5,873).
  Whether the language model contributes pharmacology therefore stays **unresolved**, and no
  value is claimed.
- **S8, the point the black-box arms were meant to test, holds.** These planners were
  hybrids: partial LLM orderings repaired from the world model, a policy whose selection
  probabilities nobody can write down. Their certificates stayed valid:
  - llm_blind: FDR 0.090 [0.075, 0.106] at alpha 0.2, yield-bound coverage 0.932;
  - llm_named: FDR 0.043, coverage 0.956.
- **Cost.** Provider spend was USD 1.53 for 468 priced calls; development cost about USD 0.34 including
  the invalid run. A campaign took 18-19 s with the LLM against 0.27 s without it.

Next time, ask for a ranking, or a fixed small number per call, when k is large, and record the
presented order so a blind planner's ordering can be audited.

## 5. What is and is not established

**Established on an independent, pre-registered screen:**
- A world model that learns in context from the agent's purchases finds more measured
  synergies than static retrieval at equal wells and days, even after paying for a random
  audit.
- Design-randomised audits give valid finite-sample certificates on real data, for every
  planner tried.
- The world model's own claims about its selections are optimistic by 1.4-2.1x.

**Not established:**
- that single-agent cell-state context or uncertainty-aware acquisition adds decision value
  (both null);
- that an LLM planner does. It was null on O'Neil; on ALMANAC it was untestable, because every
  confirmatory round was an invalid selection;
- that nominations are reliable one list at a time (the guarantee is marginal);
- any mechanism, causal or clinical claim;
- that a hit replicates. O'Neil's validation repeat recalls only 45% of primary hits (label
  r = 0.62), so a hit means a hit in the primary screen.

**Novelty boundary:** active learning for combination screens (RECOVER, BATCHIE, Wang et al.
2025, ScreenShot), conformal selection and LLM experiment planners are prior art. What this
block adds is the design-based certificate for a black-box planner's discoveries, its measured
price, and the demonstration on two screens that uncertified world-model claims are
over-optimistic.

**Further limits:**
- Line campaigns share the drug library, so the generalisation population is new lines
  screened with this library.
- ALMANAC aggregates three screening centres.
- ALMANAC costs are dose-point records, because replicate wells per record are not published.
- Both screens are public. Development used one, and the LLM may have seen either.
- The tree was not committed at freeze time. Integrity rests on the digests and the vault log.

## 6. Promotion and efficiency

| Promoted component | From (frozen) | Parity evidence |
|---|---|---|
| `src/maestro/certification.py` (standard library only) | `certify.py` | 200 random cases identical to the frozen version (`tests/test_combination_screens.py`); 7 core tests |
| `src/virtual_cell/combination_world.py` (numpy only) | `world.py` | Features and prior identical. Nelder-Mead reaches an equal or better likelihood than the frozen scipy fit, whose line variance stopped early; drug and noise variances agree within 2% |
| `src/agent/discovery.py` | `agent.py` loop | Typed claims; a prediction is never a measured hit; double purchase refused |
| `tools/datasets/combination_screens.py` | `screens.py`, `xlsx.py` | O'Neil library identical (22,737 rows, 749 hits); synthetic ALMANAC release and vault refusals |
| `tools/evaluation/discovery_replay.py` | `agent.py`, `replay.py`, `analysis.py` | O'Neil development totals reproduced (history 401 exact, world-model arms within 3). On the confirmatory library, history 5,597, wm_static 5,744 and wm_full 5,873 are exact; the certify branch is within audit-draw noise (`results/promoted_parity_almanac_20261003`) |

- Not promoted: the LLM planner (no demonstrated decision value) and the verdict and protocol code (study
  specific).
- The research copies stay frozen, because the evidence references their digests.
- Efficiency:
  - The default core suite is 354 tests in 48.8 s; the 12 new core tests add 1.3 s.
  - No existing module changed except one `pyproject.toml` scope registration.
  - The full 60-line confirmatory replay of 11 arms took 86 s on 20 workers.

## 7. Deviations and failure receipts

- On the confirmatory screen the LLM never chose exactly k of about 128 ids (section 4.3). The
  named repair code made this visible; no post-hoc fix was applied to the confirmatory run.
- `dev_llm_20261003_v1`: a scripted edit silently failed, so `blind` sent the `named` prompt
  and every final round asked for one experiment too many. The run is kept and marked invalid,
  then rerun after assertion checks.
- The first certification negative-control test was mis-specified, and was replaced before any
  real-data run.
- The pre-freeze dry run found that summarising an LLM-only replay crashed, because its
  reference arm was absent. The bug was fixed before the freeze.
- The promoted optimizer differs from the frozen one (section 6), and this is disclosed rather
  than forced to match.
- A synthetic test fixture in the promoted tests had misaligned columns. The fixture was
  fixed; the builder was unchanged.

## 8. Reproduce

```powershell
$py = 'D:/anaconda/envs/maestro/python.exe'
& $py -m research.certified_discovery.replay --out NEW_OUTPUT --spec '{\"kappa\":2}'      # O'Neil development
& $py -m research.certified_discovery.llm_replay --out NEW_OUTPUT --spec '{\"kappa\":2}'  # needs .env provider keys
& $py -m research.certified_discovery.verdict RUN_DIR [LLM_RUN_DIR]
& $py -m pytest research/certified_discovery tests/test_certification.py tests/test_combination_world.py tests/test_combination_screens.py -o addopts=
```

The confirmatory run (`python -m research.certified_discovery.confirm`) refuses to run again
into the same output; a second opening would be recorded as such by the vault log.
