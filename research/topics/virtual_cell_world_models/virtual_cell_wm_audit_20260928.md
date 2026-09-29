# Virtual-cell world model: module-by-module audit and an assessment of two external proposals

Date: 2026-09-28. Scope: `src/virtual_cell/`, the agent↔world-model link, the evaluation
infrastructure and data assets, plus verification of the literature cited by two external
review documents ("frozen STATE + observation heads" and "DINO-WM-style latent world model").
Every code claim carries a `file:line` reference. Every literature claim was checked against
the primary source.

## 0. Verdict up front

1. **Neither proposal asks for a model replacement, and none is needed.** The binding
   constraint is not model capacity. It is that the world model's output never reaches the
   decision layer in a form the decision layer is allowed to use.
2. **The single highest-priority defect is the missing calibration layer.** Two independent
   gates — hypothesis discrimination (`contrast.py`) and trust revocation (`reliability.py`) —
   are both keyed on coverage-claiming (CALIBRATED) intervals. No backend emits one for the
   STATE readouts. The closed loop "predict → calibrate → influence → score → revoke" is
   therefore inert end to end.
3. **The magnitude-only readout criticism is correct and already has empirical teeth in this
   repository.** The pre-registered 2026-09-26 evaluation found the L2-magnitude tie-break
   failed its frozen keep rule, and a learned gene-space transition model predicted profiles
   better (cosine +0.283) without improving decisions (+0.003). Prediction quality and
   decision utility have already decoupled once, on this codebase.
4. **The DINO-WM migration is directionally sound but its central hypothesis is contradicted
   by the strongest available benchmark unless the encoder choice is settled first.**
   Ahlmann-Eltze et al. (Nat. Methods 2025) found atlas-pretrained embeddings only marginally
   better than random ones for perturbation prediction, while perturbation-data pretraining
   helped. The encoder negative control is therefore not a formality; it is the experiment
   most likely to fail, and it is cheap. It must run before any dynamics training.
5. **Data, not architecture, bounds the research line today.** Exactly one context
   (`tahoe_c39`) is registered for STATE serving; SciPlex3 has already informed prior designs
   (promotion unavailable); context-held-out evaluation is currently impossible.

## 1. Module-by-module audit

### 1.1 Contract layer (`src/virtual_cell/interface.py`) — healthy

- `StatePrediction.state_change` is `Mapping[str, float]` (interface.py:398): arbitrary readout
  keys are contract-legal. Adding directional pathway scores requires **no contract change** —
  only backend emission plus `supported_variables` registration.
- `safe_predict` enforces readout accountability: requested readouts must appear in
  `state_change` or in `supported_variables` with an artifact (interface.py:659-670).
- The `Interval` type already distinguishes DESCRIPTIVE from CALIBRATED and forces a named
  `basis` for coverage claims (interface.py:347-384). The machinery the proposals ask for
  exists; backends simply do not use it.
- `confidence=None` is contract-valid only when `uncertainty_components` names the unknown
  sources (interface.py:438, 466-469) — a deliberate escape hatch, used by every backend.

### 1.2 STATE adapter (`src/virtual_cell/state_adapter.py`) — the main offender

- Output compressed to `embedding_delta_l2` / `mean_absolute_embedding_delta`
  (state_adapter.py:58, 620-623; runner: state_runner.py:277-278). The signed vector is
  written only to the shift artifact. **Direction is discarded at the source.**
- `intervals={}` (state_adapter.py:632), `confidence=None`, `in_distribution=None`
  (state_adapter.py:633-634). Per interface.py:466-469 this passes the contract only via
  `uncertainty_components`, which honestly lists `training_overlap: "unknown for this context
  and perturbation"` (state_adapter.py:643).
- Capabilities: `supported_modes=("drug",)`, `supports_dose=False`, `supports_time=False`
  (state_adapter.py:442-445). It is a condition-matched transcript-shift simulator and should
  be scoped as such.
- A scale-calibration path exists (`ScaleCalibration`, binding checks, state_adapter.py:546-598)
  but calibrates magnitude only, and only when a bound receipt exists.

### 1.3 The template already in the tree: `response_rung.py` + `pathway_readout.py`

The repository already contains, for SciPlex response readouts, exactly what the first
proposal asks STATE to do:

- `pathway_readout.py`: `GeneSet`, `score_gene_set` (signed mean log2-FC over a registered gene
  set), `SCHEMA = "pathway_score_v1"` — directional scores with an expressivity audit
  (all-zero / constant-output / low-variance gene-set detection).
- `response_rung.py`: emits `hallmark:*`-family directional readouts **and** fills
  `intervals[...] = Interval(..., kind=CALIBRATED, level=0.90, basis=...)` from a fitted
  conformal score with a declared calibration split.
- Consequence: the fix for STATE is replication of an in-tree pattern onto the STATE artifact
  vector, not invention of a new subsystem.

### 1.4 Baseline ladder (`src/virtual_cell/ladder.py`)

- `LinearPerturbationBaseline` (ladder.py:123-267): ridge on context + perturbation one-hot +
  log1p(dose); emits DESCRIPTIVE intervals only, with an explicit comment that a residual
  dispersion must not acquire coverage semantics (ladder.py:231-240). Its docstring states the
  promotion rule this project lives by: a pretrained model that does not beat this rung is
  withdrawn, not reported (ladder.py:126-128).
- `DevelopmentMeanShift` rung (ladder.py:~518-709): emits the same two magnitude keys as STATE,
  so same-name readout comparison across these two rungs is arithmetically meaningful.
- Cross-rung comparability caveat: `embedding_delta_l2` (STATE/mean-shift) vs phenotype
  readouts (linear/Hill) are different quantities; `predict_all` disagreement is only
  informative within a shared readout name and unit.

### 1.5 Composite routing (`src/virtual_cell/world_model.py`)

- `predict()` = first eligible backend in registration order (world_model.py:221-227);
  `routing_report` states this rule explicitly (world_model.py:182).
- `predict_all()` exists and preserves per-backend disagreement (world_model.py:185-205), but
  nothing in production calls it. Disagreement-as-signal is implemented and unused.
- Practical cost note: STATE inference is a subprocess call (state_adapter.py:521), so making
  `predict_all` the default multiplies wall-clock per decision. Recommendation: keep
  first-eligible in production; use `predict_all` in evaluation/ablation mode.

### 1.6 Agent↔VC link

- **Consumption is one scalar per action.** `orchestrator.py:751-758` builds
  `registered_predictions[action] = state_change[action.prediction_readout]`; the round record
  keeps one `WorldModelLayer` with a single mean/interval (orchestrator.py:718-748). No vector,
  no disagreement, no per-hypothesis information crosses this boundary.
- **Briefing is faithful but bounded to the same scalar** (`world_model_briefing.py:93-136`):
  per action it renders value, interval, coverage flag, validation status and the reliability
  weight. It already carries everything except direction and disagreement.
- **Gate 1 — discrimination.** A model-dependent action certifies hypothesis separation only
  with a coverage-claiming interval for its readout (`contrast.py:679`, `_calibrated_model_support`
  at contrast.py:696-705). With `intervals={}` from STATE, this gate can never open.
- **Gate 2 — revocation.** `PredictionReliabilityLedger` grades only `interval_hit`, which is
  defined only for coverage-claiming bands (reliability.py:23-27, 52-63, 184-195). With no
  CALIBRATED intervals, `graded` is empty, the ledger stays provisional, and `weight` remains
  1.0 forever (reliability.py:199-210). **The revoke loop cannot fire.**
- **Gate 2b — reconciliation never runs outside the case loop.** `_score_prediction` has a
  single call site, `run_case_loop` (orchestrator.py:1060, defined at orchestrator.py:1311-1425).
  Single-shot `run()` + `import_measurement` (orchestrator.py:2068-2087) and
  `record_revealed_result` (orchestrator.py:2089-2099) never score a prediction. Callers using
  the single-turn API can therefore accumulate no calibration receipts at all — a second,
  independent reason the ledger stays provisional.
- **Boundary hole — revocation does not constrain discrimination certification.**
  `_calibrated_model_support` (contrast.py:696-705) checks `claims_coverage` only and never
  consults the reliability ledger; none of its call paths carries a ledger (orchestrator.py:636,
  1970; repair.py:263, 311). A model whose readout was revoked after 3 consecutive misses
  (reliability.py:211-222) would still certify discrimination for `requires_virtual_prediction`
  actions. The trust mechanism constrains only the tie-break (orchestrator.py:1869-1872).
- **This hole is amplified by the default deployment.** `from_workspace` defaults to
  power-aware selection (orchestrator.py:346), which deliberately drops the magnitude
  tie-break after its pre-registered failure (orchestrator.py:1697-1702). The world model's
  remaining influence channels are exactly two: briefing→LLM-repair, and the boolean
  `_calibrated_model_support` gate — the one channel the ledger does not guard.
- **The initial planner is blind to the world model.** The briefing reaches only
  `propose_repair` (planner.py:271, 327; orchestrator.py:525); `propose()` (planner.py:164-262)
  takes no world-model input. First-round hypothesis/action construction never sees a
  prediction. (If intentional, the briefing module docstring should say so.)
- **Interval width and level influence nothing.** Ranking consumes `abs(value)` only
  (orchestrator.py:1866-1872); `interval_level` is rendered (world_model_briefing.py:127) but
  has no consumer. A uselessly wide interval and a tight one tie-break identically.
- **`uncertainty_components` is a dead field** downstream: populated by backends and carried
  through abstentions (interface.py:415, 577-580), consumed by no decision or audit summary.
- **Wrong eliminations are undetectable and irreversible at runtime.** `EvidenceState.apply`
  only removes (outcome.py:296-306); ground-truth comparison exists only in the off-line
  evaluation (research/acquisition_link/analyze.py:169). This makes the *measured* wrong-
  elimination endpoints of §1.7 the only safeguard, and raises the value of every mechanism
  that keeps predictions away from evidence.
- Net effect: the architecture for "prediction → calibration → abstention → influence →
  scoring → revocation" is built; the one component that activates it (a calibrated interval
  on the served readout, wired through every execution path) is missing, and the gate it
  would open is not itself guarded by the trust ledger.

### 1.7 What the decision layer already proved (prior pre-registered work)

- `research/acquisition_link/` (protocol frozen 2026-09-26, 2,496 SciPlex3 episodes): the
  magnitude tie-break raised tier-B utility (+0.298 [+0.205, +0.388]) but also wrong
  eliminations (+0.044) and failed its frozen keep rule in tier A; it is **not enabled** in
  production. The distribution-aware selector (OutcomeForecaster + `select_discriminating_action`)
  was INCONCLUSIVE and stays opt-in. Forecast calibration machinery exists there (ECE 0.058/0.085,
  Dirichlet/Jeffreys), for reference-card forecasts — not for STATE outputs.
- `research/dynamic_world_model/` (same freeze): a learned gene-space ridge transition forecast
  beat persistence (cosine +0.283) yet named mechanism classes no better and changed planning
  by +0.003. **The decoupling of prediction metrics from decision utility is not a hypothesis
  here; it is a measured result on this codebase.**
- Registered metrics already computed in-tree: decision regret vs oracle, wrong-elimination
  rate (also risk-controlled in `research/dual_core_v2/risk_control.py`), ECE/coverage
  (`src/virtual_cell/calibration.py`, cross-conformal, LOSO receipts).

### 1.8 Data and serving assets (`data/INVENTORY.md`, audit of `data/`)

- Real perturbation-response data with matched controls: SciPlex3 (2.46 GB h5ad + 400 MB
  processed subset), Tahoe c39 (~653 MB), L1000 subset48 (774 MB, 6 h/24 h pairs).
- STATE zero-shot checkpoint (~1.07 GB, sha256-registered) under `data/external/arc_state/`.
- **One registered context** (`tahoe_c39`) in `data/virtual_cell/registry.json` →
  context-held-out evaluation is impossible today; SciPlex3 episodes have all informed prior
  designs (promotion unavailable per acquisition_link §9).
- No cell-foundation encoder weights or extraction pipeline (scGPT/Geneformer/scFoundation
  appear in docs only).

## 2. Literature verification

| Claim in the proposals | Verification |
|---|---|
| DINO-WM: frozen DINOv2 features, offline trajectories, ViT predictor, CEM planning, zero-shot = test-time goal conditioning, not data-free dynamics | **Accurate.** Zhou et al., arXiv:2411.04983, ICML 2025. The correction in the proposal (zero-shot refers to goals/tasks, dynamics still need offline trajectories) matches the paper. |
| Nat. Methods 2025 benchmark: deep perturbation models do not beat linear baselines | **Accurate, with a decisive nuance.** Ahlmann-Eltze, Huber, Anders, Nat. Methods 22:1657-1661 (2025). None of GEARS/scGPT/scFoundation/CPA/Geneformer/UCE/scBERT consistently beat linear or even mean baselines. **Nuance the proposals underuse:** a linear model with perturbation embeddings *pretrained on perturbation data* (Replogle cross-line) did beat everything; atlas-pretrained cell embeddings gave only a small benefit over random embeddings. |
| Virtual Cell Challenge 2025 | Verified via Arc's wrap-up: the generalist winner was a flow-matching model (Altos); third place (TransPert) was a statistical, summary-level method with linear scaling. Metric gaming (PDS/DES vs MAE) prompted a multi-metric redesign — directly relevant to endpoint design here. |
| AlphaCell: OT-CFM virtual-cell world model, latent manifold + genome-wide decoder, zero-shot context claims | **Accurate as characterized**: bioRxiv 2026.03.02.709176 (preprint, unreviewed). Correctly classed as a future experimental backend, not a present replacement. |
| 2026 warning: latent WMs sensitive to control-irrelevant slow features; bisimulation-style representations proposed | Plausible and consistent with the direction of recent work; the specific paper was not independently located. Treated as a design risk, not a cited fact. The biological analogues (batch, cell cycle, donor, depth, generic stress) are real and measurable in our data. |

## 3. Assessment of the two proposals

### 3.1 Proposal 1 (frozen STATE → observation heads → calibration → four-arm ablation)

**Endorsed, with three amendments.**

1. **Reprioritize: calibration before new readouts.** The proposals order observation heads
   first. The code says otherwise: two decision gates (§1.6) are keyed on CALIBRATED intervals,
   so without them neither new readouts nor `predict_all` disagreement can influence anything
   that is scored or revoked. The in-tree `response_rung` pattern (conformal, declared split,
   named basis) makes this a bounded change.
2. **The four-arm experiment is partially done — use its negative result.** "Magnitude tie-break"
   is arm C's readout; it already failed promotion (§1.7). The informative remaining contrast is
   B (linear) vs C′ (frozen STATE + directional heads + calibrated intervals), plus D
   (adapter). Framing the ablation as a rerun of the failed arm with the readout layer fixed
   makes the causal attribution clean: same backend, same cases, same protocol discipline,
   different observation layer.
3. **New readouts must pass the existing expressivity audit** (`pathway_readout.py`) and must
   be pre-registered, external, fixed signatures (e.g., MSigDB hallmark weights frozen before
   any evaluation), or the attribution chain the proposals value is broken at the head.

### 3.2 Proposal 2 (DINO-WM-style: frozen cell encoder + small latent dynamics + test-time planning)

**Directionally endorsed as the research line; its premise must survive two in-house
counterexamples before any training budget is spent.**

1. **The representation hypothesis is the weak link.** DINO-WM works because DINOv2 features
   are demonstrably control-relevant. The Nat. Methods 2025 result shows the cellular analogue
   is not established: atlas pretraining ≈ random embeddings; perturbation-data pretraining is
   what transferred. Therefore the encoder comparison (`E_pretrained` vs `E_random` vs `E_PCA`
   vs `E_scVI`, identical small dynamics head, pseudobulk SciPlex3 + Tahoe c39) is promoted
   from "negative control" (proposal §16) to **gate 0 of the research line**. It is cheap and
   falsifies the line's premise fastest.
2. **The latent-MSE trap is already documented here.** Our ridge transition predicted held-out
   profiles well and moved decisions not at all (§1.7). The research line must therefore never
   report latent/vector-space metrics without the paired decision endpoint (regret, wrong
   eliminations, utility) under the acquisition_link protocol discipline. Multi-metric
   reporting also follows the Virtual Cell Challenge's published lesson on metric gaming.
3. **Unpaired-population training is correctly identified** as the key methodological
   difference from DINO-WM (proposal §7-8): set/distribution losses (MMD, OT/W₂) over
   pseudo-bulked populations are the right frame, and STATE's population formulation plus
   CellOT/CellFlow precedent support it. The minimal prototype (latent displacement,
   `Δz = μ_P − μ_C`, small MLP) is the correct first rung — and it should also be run in gene
   space as a sanity baseline, since our gene-space ridge already sets the bar.
4. **Zero-shot must be split three ways** (task / perturbation / context — proposal §10).
   Only zero-shot *task* planning is currently testable: context-held-out is blocked by the
   single registered context (§1.8); perturbation-held-out is feasible on SciPlex3/Tahoe
   pseudobulk with existing split precedent.
5. **Slow-feature contamination (proposal §19) is checkable before modeling**: cell-cycle
   scores and vehicle-well nulls already exist in `research/dynamic_world_model/prepare_time.py`;
   batch/plate composition is in the SciPlex obs. A representation audit (how much latent
   variance these factors explain) belongs in gate 0.

### 3.3 What both proposals miss

- **Time is the measured axis of value here.** The 2026-09-26 result found fixed "24 h → 72 h"
  beat every selector in tier A (+0.211), and slow mechanisms (DNMT, BET, Aurora) separate only
  at 72 h. STATE declares `supports_time=False`. Any observation-head or latent-dynamics work
  that ignores the time axis optimizes the wrong variable first. The L1000 subset48 6 h/24 h
  pairs are the in-tree candidate for a time-aware evaluation that SciPlex3 can no longer
  provide (promotion exhaustion, acquisition_link §9).
- **`predict_all` disagreement is implementable today but must share readout names/units**;
  cross-rung disagreement on unlike quantities is not arithmetic (§1.4).

## 4. Staged plan (each stage independently verifiable)

- **P0 — Close the calibration loop for STATE readouts** (highest priority, smallest change).
  Fit split-conformal intervals for `embedding_delta_l2` (and any new readout) on a declared
  calibration partition; emit `Interval(kind=CALIBRATED, level, basis)` from the STATE adapter,
  replicating the `response_rung` pattern. Wire scoring into the single-shot execution paths
  (`import_measurement` / `record_revealed_result`), not only `run_case_loop`. Verification:
  coverage receipt on held-out conditions ≈ nominal level; `_calibrated_model_support` can
  return True on a registered case; the reliability ledger grades its first non-empty scope
  on every public execution path.
- **P0b — Guard the discrimination gate with the ledger.** `_calibrated_model_support` (or an
  orchestrator-side wrapper) must treat a revoked or down-weighted readout as non-certifying.
  Verification: a regression test in which 3 consecutive calibrated misses flip a
  `requires_virtual_prediction` action from certifying to non-certifying.
- **P1 — Directional observation heads on the STATE artifact vector.** Registered, fixed,
  external gene-set signatures scored by `pathway_readout.score_gene_set` against the stored
  signed shift; new `state_change` keys + `supported_variables` + `served_readouts`;
  expressivity audit mandatory. Verification: same case run with old and new readouts leaves
  contract, briefing and evidence paths unchanged; heads are not all-zero/constant.
- **P2 — Four-arm ablation, reframed.** Arms: None / linear baseline / frozen STATE (P0+P1
  readouts) / STATE + adapter. Reuse acquisition_link episode machinery; needs a
  backend-as-arm abstraction, a linear-rung `OutcomeForecaster` wrapper, and an explicit None
  arm. Endpoints: correct-decision rate, wrong eliminations, utility, regret, ECE/coverage.
  Verification: protocol frozen before any arm runs; verdict by the same frozen-rule
  discipline as 2026-09-26.
- **P3 — Research-line gate 0: encoder comparison + representation audit.** `E ∈ {pretrained
  (STATE-SE embedding or scGPT if obtained), random, PCA, scVI}` × identical displacement MLP,
  pseudobulk SciPlex3 + Tahoe c39, perturbation-held-out; plus variance explained by
  batch/cell-cycle/depth. Verification: pretrained beats random/PCA on held-out dynamics
  *and* the representation is not dominated by nuisance factors; otherwise the latent-WM line
  stops here and the engineering line (P0-P2) carries the project.
- **P4 — Latent dynamics prototype.** `G_θ(μ_C, e_u, c) → Δz`, MMD/W₂ population loss;
  gene-space ridge as the sanity baseline (it already holds the +0.283 cosine result).
  Verification: beats ridge on held-out perturbations on distribution metrics, then — and only
  then — enters a decision-endpoint evaluation.
- **P5 — Decision integration of disagreement.** `predict_all` in evaluation mode; disagreement
  surfaced as an epistemic warning in the briefing; planning objective through the registered
  rules (D-statistic lineage), never raw latent distance. Verification: disagreement stratifies
  realized error on held-out cases.

## 5. Open risks

1. **Signature-selection risk (P1):** fixed external signatures cap head quality; fitted
   signatures reopen leakage. Mitigation: pre-registration + expressivity audit + reporting
   per-signature provenance.
2. **Single-context serving:** one registered STATE context limits both evaluation honesty and
   the zero-shot-context claim. Registering a second context (SciPlex3 lines are candidates,
   subject to the promotion-exhaustion caveat) is a data-operations task, not a modeling one.
3. **Metric gaming:** single endpoints get optimized rather than biology (Virtual Cell
   Challenge 2025 lesson). All evaluations report the multi-metric panel.
4. **Preprint churn:** AlphaCell-class backends are tracked as future rungs behind the existing
   contract; no refactor is justified by an unreviewed model.
