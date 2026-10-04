> **File summary**
> - **Path**: `research/certified_discovery/DESIGN.md`
> - **Purpose**: the literature-grounded design of certified dual-core discovery, written before
>   the confirmatory screen was opened; the protocol (`protocol/confirmatory.json`) and the
>   frozen verdict code implement it.
> - **Core points**: move the dual core to a task where prediction binds decisions; let the
>   world model learn in context from the agent's own purchases; and give every claim about
>   untested candidates a design-based certificate that holds for any acquisition policy,
>   including an LLM planner.
> - **Interfaces / data**: `world.py`, `agent.py`, `certify.py`, `llm_agent.py`, `verdict.py`;
>   O'Neil 2016 (development), NCI-ALMANAC 2017 (confirmatory).
> - **Depends on**: `research/topics/virtual_cell_world_models/dual_core_obstruction_map_20260929.md`.

# Certified dual-core discovery

## 1. Why this task

The obstruction map of 2026-09-29 found that on every task registered before it the *decision
side* binds: perfect response prediction moved mechanism-class decisions by at most +0.008, and
the fixed expert order reached 63-99.4% of the oracle. A better world model cannot show its
value there. It also found a second, recurring defect: forecasts are about 2x too optimistic on
the actions the planner selected (dual_core E2, dual_core_v2, maestro_vc_v1), and no
recalibration transferred.

This design addresses both. It qualifies `task.md` Task 3 (combination and synergy) in a form
where purchases decide outcomes directly. A lab screens a new cell line against a drug-pair
library with a budget of 10% of the experiments, in four rounds. Every candidate's outcome was
measured in a full-factorial public screen, so each arm's choices are scored against hidden
measured labels without any modelling. The oracle ladder (random 0.11, oracle 0.996 of a line's
hits at a 10% budget on the development screen) shows prediction binds here.

## 2. Architecture: two cores plus a certifying layer

| Component | Role | What it may not do |
|---|---|---|
| World model (`world.TransferWorld`) | Empirical-Bayes prediction of each candidate's synergy label in the target line. History from other lines gives the prior mean; single-agent responses give the cell-state context; the agent's purchases in the line update a line effect and drug-in-line effects in closed form. | Read the target line's labels except through purchased measurements |
| Agent (`agent.run_campaign`, arms, `llm_agent`) | Chooses each batch and, in the last round, either exploits or spends the batch on a random audit of its own shortlist. Planners range from fixed rules to an LLM. | Claim an untested candidate is a hit; it may only nominate through a certificate |
| Certificate (`certify.certify`) | Converts the world model's ranking of untested candidates into an FDR-controlled nomination set and an exact lower bound on hits remaining | Use labels other than the audit's; use any model calibration assumption |

The world model is an in-context transfer model rather than a deep network. In-context
conditioning on measured responses is the idea shared by State and Stack (State, Cell 2026) and
ScreenShot (de Mathelin, Tosh and Tansey, 2026). Earlier blocks found that linear and
retrieval baselines match larger models (Ahlmann-Eltze et al., 2025). Everything is
closed-form through the Woodbury identity (dimension = drugs + 1), so a campaign costs
milliseconds and a world build about 0.1 s.

## 3. The certificate, and why it holds for a black-box agent

After round R-1 the agent fixes a shortlist S (the top kappa x batch untested candidates) and a
score for each member, using only data already bought. It then measures a uniformly random
batch-sized audit A from S, using randomness independent of every label in S.

Two facts hold conditional on everything before the draw. Nothing so far has used any label
in S. And the split of S into A and the remainder is uniformly random. So audit and remainder
are jointly exchangeable. That is the only assumption of conformal selection (Jin and Candes,
JMLR 2023, with the joint-exchangeability form of Gui, Jin, Nair and Ren 2025). Hence:

- conformal p-values with the clipped score, followed by Benjamini-Hochberg at alpha, nominate
  a subset of the remainder with FDR <= alpha;
- inverting the hypergeometric tail gives a 1-delta lower bound on the remainder's hits
  (finite-population sampling).

Neither statement depends on how the earlier batches were chosen. Weighted conformal methods
for feedback loops (Fannjiang et al., PNAS 2022; Prinster et al., ICML 2024) need the
acquisition policy's likelihood ratios. Conformal policy control (Prinster et al., ICML 2026)
needs a safe reference policy's data. An LLM planner has neither. Design-based randomisation
inside the agent's own shortlist needs nothing from the planner, which is what lets an
arbitrary agent make lawful claims.

The cost is real and is measured. The final batch is drawn at random from the top 2 x batch
instead of being the top batch. `price_of_certification` reports the hits given up. The
guarantee is marginal: it bounds the expected false-discovery proportion, not the error of
any one nomination list. When audits are small, nominations are rare and a non-empty list can
still be mostly wrong. The pooled precision of nominations is therefore reported beside the
FDR.

## 4. Labels, units and costs (declared before any label was computed)

- **Label**: the Bliss excess in percentage points, averaged over the experiment's combination
  dose grid. A hit is a label above 10, the SynergyFinder convention (score > 10: likely
  synergistic).
  - O'Neil: expected = min(rA,1) x min(rB,1) on the published X/X0 scale, with single agents
    interpolated in log concentration from the same batch.
  - ALMANAC: NCI's own per-well SCORE (ExpectedGrowth - PercentGrowth), averaged over all
    combination records of the pair x line.
- **Unit**: the target cell line, one campaign per line. History is every other line of the
  same screen. Audit draws and random seeds are averaged within a line, and intervals
  bootstrap lines.
- **Cost**:
  - O'Neil: experiments; dose points; wells (16 points x 4 replicate wells); 5 days per round
    (96 h assay plus plating).
  - ALMANAC: dose-point records (treated as wells; the release does not state replicate wells
    per record); 3 days per round (48 h assay plus 24 h pre-incubation).
  - Provider spend is reported separately.
- **Label reliability (a limit, not a tuning input)**: in O'Neil's validation repeat (batch 3,
  315 shared experiments) the label correlation is 0.62, and 45% of primary-screen hits recall
  as hits. A hit therefore means a measured hit in the primary screen.

## 5. Literature and the novelty boundary

| Prior work | What it already establishes | Used here as |
|---|---|---|
| RECOVER (Bertin et al., Cell Rep Methods 2023) | Sequential model optimisation enriches synergy 5-10x over random in vitro | Expected discovery effect size |
| BATCHIE (Tosh et al., Nat Commun 2025) | Bayesian active learning on ALMANAC, GDSC2, Merck (O'Neil); prospective sarcoma screen; no FDR for nominated hits | Prior art for adaptive combination screening |
| Wang et al., Sci Rep 2025 | AL finds 60% of synergies with 10% of O'Neil/ALMANAC; cell features matter more than molecular encodings | The 10% budget and the batch-size advice |
| ScreenShot (de Mathelin, Tosh and Tansey, 2026) | In-context foundation model on functional measurements; one-third budget | The in-context, function-first world-model idea |
| Jin and Candes, JMLR 2023; Gui et al. 2025 (ACS) | FDR-controlled selection with conformal p-values; ACS assumes exchangeable, not adaptively collected, labels | The certificate |
| Fannjiang et al., PNAS 2022; Prinster et al., ICML 2024 and 2026 | Validity under feedback covariate shift, given policy likelihood ratios or a safe reference policy | What the audit design avoids needing |
| Smith and Winkler, Management Science 2006 | The optimizer's curse | The naive-claim comparison |
| Wainrib et al. 2026; BioDiscoveryAgent (Roohani et al., ICLR 2025) | LLM agents can use lab-in-the-loop feedback in perturbation discovery | The LLM planner arms and their controls |

**Not claimed**: active learning for combination screens, conformal selection, in-context
response models, LLM experiment planners.

**Claimed, if the protocol passes**: a dual-core discovery loop whose world model learns in
context from the agent's purchases and finds more measured synergies than static retrieval at
equal wells and days, *after* paying for a randomised audit. The audit makes every claim about
untested candidates hold with finite-sample guarantees for any planner, including one whose
selection probabilities are unknowable. The naive claims of the same world model are shown to
be over-optimistic on real screens.

## 6. Hypotheses (confirmatory on NCI-ALMANAC; development results on O'Neil in section 7)

- **H1 (primary, discovery)**: wm_full with certification against history (static retrieval)
  without certification, per line. PASS iff the 95% bootstrap interval of the mean difference
  in measured hits is above 0.
- **H2 (primary, certification)**: for wm_full, the mean FDP over lines x 20 audit draws is <=
  0.2 with an upper bound <= 0.25, and yield-bound coverage is >= 0.87 (1 - delta - 0.03).
- The framework claim needs both.
- **Secondary, estimated with intervals**:
  - S1 feedback (wm_full vs wm_static);
  - S2 cell-state context (vs wm_nocontext, vs wm_shuffled);
  - S3 uncertainty (vs wm_greedy);
  - S4 optimizer's curse (claimed / realised remainder hits; precision of "P(hit) >= 0.5");
  - S5 price of certification;
  - S6 LLM knowledge (llm_blind vs wm_menu_random);
  - S7 LLM as planner (llm_named vs wm_full);
  - S8 certification validity under LLM planners;
  - S9 ladder against random, heuristics and oracle;
  - S10 pooled nomination precision.

## 7. Development evidence (O'Neil 2016; exposed, not confirmatory)

39 lines, 22,737 experiments, 749 hits (3.3%). Budget 59 experiments per line in four rounds;
kappa = 2, alpha = 0.2, delta = 0.1.

**Hits found, of 749:**

| Arm | Hits |
|---|---:|
| oracle | 746 |
| llm_named | 477 |
| wm_full | 475 |
| wm_nocontext | 476 |
| wm_shuffled | 440 |
| wm_menu_random | 438.6 |
| llm_blind | 432 |
| wm_static | 407 |
| history | 401 |
| random | 78.9 |
| heuristic_headroom | 54 |
| heuristic_potency | 12 |

**Registered rule, dev data:** H1 +1.52 hits per line [0.64, 2.57], 24 lines better and 10
worse; H2 FDR 0.045 [0.031, 0.062], coverage 0.972. Development is not confirmation.

**Secondary estimates:**
- Feedback is the active ingredient: +1.74 per line [1.03, 2.51].
- Context: -0.03 [-0.72, 0.69]. Uncertainty: -0.03.
- LLM knowledge: -0.17 [-0.71, 0.36]. LLM as planner: +0.05 [-0.05, 0.15]. The planner
  agrees with the world model's top-k in 91-99% of picks.
- Claimed / realised remainder hits: 1.72 [1.34, 2.39]. "P(hit) >= 0.5" claims 57% precision
  and delivers 33%.
- Nominations are rare at this audit size (15.8 per 39 lines, pooled precision 32%).

**Development choices made on O'Neil:** kappa (2 over 3 or 4: price 15 vs 26 hits); alpha 0.2
(0.1 cannot certify with a 15-experiment audit); four rounds; the LLM modes. A defective LLM
run (`results/dev_llm_20261003_v1/INVALID.md`) is kept as a failure receipt.
