> **File summary**
> - **Path**: `research/topics/virtual_cell_world_models/dual_core_obstruction_map_20260929.md`
> - **Purpose**: module-by-module and data-flow localisation of where the dual core
>   (agent + virtual cell) loses information, with the measured evidence at each link, and the
>   research programme that removes the binding obstructions in order.
> - **Core points**:
>   - Two obstructions sit in series. Forecast side: response-prediction quality binds
>     (oracle ceiling -0.086 nats on SciPlex3). Decision side: the task and validator bind
>     (perfect response knowledge moves decisions by at most +0.008).
>   - A third, structural obstruction gates everything: no backend emits CALIBRATED intervals
>     on the STATE readouts, so the discrimination gate and the revocation ledger are inert.
>   - "Improve the model" is therefore not the next step. The binding links are, in order:
>     lawful-influence channel (calibration), directional readouts, task reformulation where
>     prediction binds (two-compound contrast), and the time axis.
> - **Interfaces / data**: companion to `virtual_cell_wm_audit_20260928.md` (code-level audit);
>   evidence from `research/dual_core_v2/README.md` sections 6-8, 10;
>   `research/viability_contrast/README.md` section 3.7; `research/acquisition_link/README.md`;
>   `research/dynamic_world_model/README.md`; `log/20260928/`.
> - **Depends on**: `PROMPT_consolidation.md` (consolidated portal), `task.md` sections 8, 11.

# Dual-core obstruction map: where information dies, and the research programme to fix it

Date: 2026-09-29. Status: analysis and design record; every quantitative claim cites a frozen,
registered record. Nothing here is a new measurement.

## 1. The end-to-end data flow and its seven links

```
perturbation + context
   │  (L1) population → pseudobulk shift
   ▼
signed shift vector Δx (artifact)
   │  (L2) readout projection
   ▼
served readouts (state_change scalars)
   │  (L3) prediction → reading forecast conversion
   ▼
per-hypothesis outcome probabilities
   │  (L4) forecast → action selection
   ▼
chosen measurement
   │  (L5) real result → validator → belief update
   ▼
decision (hypothesis set)
   │  (L6) predicted vs realised reconciliation → trust ledger
   ▼
revocable influence on the next round
   │
   ▼  (L7) data coverage bounds every link above
```

## 2. Link-by-link findings (all measured on this repository)

### L1 — population → pseudobulk: NOT binding

Observed single-cell distributions add no mechanism signal beyond the mean on the mechanism-class
task (`dual_core_v2` section 9: B − A log loss +0.033 [+0.002, +0.065], abundance +0.015
[−0.010, +0.041], shuffled control behaves like the distribution arm). Verdict: for the current
tasks, pseudobulk is not where value dies.

### L2 — readout projection: binding, and mis-built in production

Two facts, same link:
- The production STATE path serves `‖Δx‖₂` and mean-abs only (`src/virtual_cell/state_adapter.py:58,
  620-623`): direction is discarded at the source. The magnitude readout then failed its frozen
  keep rule in the pre-registered evaluation (`acquisition_link` README section 7: tier-B wrong
  eliminations +0.044; tier-A utility interval includes zero; not enabled).
- In the research path, direction IS recoverable (centred cosine 0.37-0.44, `dual_core_v2`
  section 4), while magnitude-keeping conversions add nothing (`transfer_dist`: step log loss
  −0.002 [−0.007, +0.004]). **Direction is the information; magnitude is not.**

In-tree fix patterns already exist: `pathway_readout.py` (signed gene-set scores + expressivity
audit) and `response_rung.py` (directional `hallmark:*` readouts with conformal intervals).

### L3 — prediction → forecast conversion: response quality binds here (SciPlex3 only)

Perfect response knowledge through the same interface improves reading forecasts by **−0.086 nats
[−0.135, −0.039]** on SciPlex3 (only −0.014 [−0.038, +0.006] on L1000) (`dual_core_v2` section 6).
So on the forecast side, response-prediction quality is the ceiling on SciPlex3 — better models
CAN still pay here. The in-context layer itself reweights nothing of value (v2 changes forecasts
at 33-41% of steps, log loss −0.004/−0.000).

### L4 — forecast → action selection: lossy but not the binding constraint

v2 changes 3.5-4.0% of chosen actions; the oracle 25%/10%. The expectimax-over-two-steps plus
finite menu compresses forecast gains — but the next link shows why fixing this alone is
insufficient.

### L5 — action → decision: THE binding constraint on current tasks

The oracle changes the first action in 312 of 1,056 SciPlex3 episodes and the decision in only
34: net correct **+0.008 [−0.004, +0.021]** (`dual_core_v2` section 6). Most readings are
"undetected" or "ambiguous" whichever condition is bought; the fixed order already reaches
63-99% of the oracle's correct decisions (protocol v2 headroom). Independently, on the PRISM
viability task, v5b measured the same wall from the other side: perfect response prediction
WITHOUT the label qualifies nothing (0.77-0.87 wrong — active Goodhart under margin
acquisition), and only the reading+label conjunction certifies (0.002 wrong, CP UCB 0.0092)
(`viability_contrast` README section 3.7).

**Conclusion: on every task registered so far, the decision side binds. No predictor
improvement — not even perfection — moves decisions by more than about one percentage point.**

### L6 — decision → reconciliation → trust: structurally inert (code audit)

- The discrimination gate requires a coverage-claiming interval (`contrast.py:696-705`); STATE
  emits `intervals={}` (`state_adapter.py:632`) → the gate can never open.
- The revocation ledger grades only `interval_hit` on CALIBRATED bands (`reliability.py:52-63`)
  → `graded` is always empty, weight stays 1.0, revocation cannot fire.
- `_score_prediction` runs only in `run_case_loop` (`orchestrator.py:1060`); single-shot
  `import_measurement` never reconciles.
- The discrimination gate does not consult the ledger: a revoked model would still certify.
- The initial planner never sees world-model output (briefing reaches only `propose_repair`,
  `planner.py:271, 327`); `predict_all` disagreement is implemented and uncalled
  (`world_model.py:185-205`).

### L7 — data coverage: bounds every link

One registered STATE context (`tahoe_c39`); SciPlex3 episodes are promotion-exhausted
(`acquisition_link` section 9); 72 h support is thin where slow mechanisms separate (mean 2.3
vs 4.8 references); STATE declares `supports_time=False` while time is the measured axis of
value (fixed 24 h→72 h beats every selector, +0.211 tier A); the two-measurement budget makes
multi-prompt aggregation impossible (`dual_core_v2` section 8: 0 steps with ≥2 prompts;
clairvoyant third step adds at most 7% on SciPlex3 B, 1% on L1000).

## 3. The diagnosis in one paragraph

Two obstructions sit in series, and a third gates them both. **(A) Structural:** the
lawful-influence channel is switched off — without CALIBRATED intervals nothing the model says
may certify discrimination or be revoked, so "model performance" currently has no lawful route
to decisions at all. **(B) Forecast side:** response-prediction quality binds (−0.086 nats of
headroom on SciPlex3), but the served readout discards exactly the component (direction) that
carries mechanism information. **(C) Decision side:** the registered tasks bind — the validator
and menu make even perfect prediction worth +0.008 decisions. Improving the world model
addresses only (B), and (B) is upstream of a closed gate (A) and a binding wall (C). That is
why six consecutive blocks measured no decision lift from better prediction.

## 4. Research programme (ordered by what binds; cheap data only)

### R0 — Open the lawful-influence channel (engineering, days; no new data)

Split-conformal CALIBRATED intervals for STATE readouts on a declared partition (replicate the
`response_rung` pattern); guard `_calibrated_model_support` with the reliability ledger; wire
`_score_prediction` into the single-shot import path. Success criteria: coverage receipt ≈
nominal on held-out conditions; the ledger grades its first non-empty scope on every public
execution path; a regression test flips a revoked readout from certifying to non-certifying.
**This is the prerequisite for measuring everything below.**

### R1 — Directional readouts, tested as the rerun of the failed magnitude arm (cheap)

Registered, fixed, external gene-set signatures scored against the STATE artifact vector
(`pathway_readout` pattern; expressivity audit mandatory). Four-arm ablation on the existing
SciPlex3 episode machinery: None / linear / STATE-magnitude / STATE-directional — identical
agent, menu, budget, protocol discipline. This isolates L2 with a clean causal contrast: same
backend, same cases, different observation layer. Endpoint panel: correct decisions, wrong
eliminations, utility, regret, ECE/coverage (multi-metric, per the Virtual Cell Challenge
lesson).

### R2 — Task reformulation where prediction binds (the v5b-registered direction)

Two-compound mechanism contrast (A vs B, one line panel; the framework's native estimand K).
**Census first** (descriptive, no modelling): over PRISM × DepMap × SciPlex3 × LINCS-metadata,
enumerate compound pairs that share a nominal target but carry competing mechanism hypotheses,
and measure per pair: (i) does a decisive condition exist (headroom check, the
`horizon_headroom` pattern); (ii) reference support per condition; (iii) time-point
availability; (iv) independent units per pair. Design requirements imported from v5b: the
elimination statistic must be selection-invariant (un-gameable by acquisition); every ceiling
must ship with a reading-only decomposition control; certification claims require UCB-level
evidence. The census output is the protocol's task table.

### R3 — Data-axis repair (data operations, no training)

Register a second STATE context (a SciPlex3 line or a second Tahoe context) to unlock
context-held-out evaluation; adopt the L1000 subset48 6 h/24 h pairs for the time-aware
evaluation SciPlex3 can no longer host; only then consider the separately-specified
longer-horizon task (SciPlex3 B is the only tier with headroom; 18-24-day budget, three
measurements — `dual_core_v2` section 8).

### R4 — Model improvement proper (only after R0-R2 make it measurable)

Encoder gate-0 comparison (pretrained vs random vs PCA vs scVI under one small dynamics head —
promoted to a gate because Ahlmann-Eltze et al. 2025 showed atlas pretraining ≈ random while
perturbation-data pretraining transfers); then the latent-displacement prototype (MMD/W₂
population loss) against the gene-space ridge baseline that already holds +0.283 cosine. No
latent-space metric is reportable without the paired decision endpoint.

## 5. What "model performance" should mean here

The contribution is not a better perturbation predictor. It is the demonstrated chain:
**prediction → calibrated, directional, revocable influence → measurably better decisions on a
task where prediction binds.** The obstruction map above is itself the reusable methodology:
decompose the dual core link by link, bound each link with an oracle through the same
interface, and never let a prediction metric stand in for a decision endpoint.
