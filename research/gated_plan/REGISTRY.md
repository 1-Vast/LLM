# Dataset qualification and experiment registry

Preregistration-ready specifications. **Nothing here has been run as a registered experiment.** Registration needs
a clean commit (`research/protocol_v2/registry.py register`). The machine-readable copy is
[registry.json](registry.json). Numeric thresholds inherit protocol v2 (`research/protocol_v2/protocol.json`) unless
stated.

**Common rules for every entry:**
- Paired comparisons on identical units.
- 95% unit-cluster bootstrap, 2,000 draws, with the seed fixed at registration.
- Utility +1 / -2 / 0 with 0.02 per measurement.
- Laboratory cost in wells and days; compute and provider spend reported separately.
- Results are PASS, FAIL, INCONCLUSIVE or NOT_READY.
- A changed analysis is labelled post hoc.

## 1. Dataset qualification

"Exposure" means which MAESTRO work has already read outcomes from the source.

| Source | Local | Independent units (as used) | Pairing keys and condition overlap | Labels or truth | Licence | Exposure | Uncertainty it could resolve | Decision |
|---|---|---|---|---|---|---|---|---|
| SciPlex3 (Srivatsan et al. 2020) | yes, 2.4 GB h5ad, sha256 sidecar | 180 skeleton units; tiers A 42, B 132 | Same compound, 3 lines at 24 h, A549 also 72 h (47 compounds); 4 doses | Study pathway and target annotation, reduced to a class | CC BY 4.0 (sidecar) | Fully exposed (09-26, 09-27) | Menu choice (time, line, dose); world-model forecasts | **Development and regression only** |
| LINCS L1000 GSE92742 | yes, Level 5 plus metadata | LT 256, T 170 components | 4 lines at 6 h and 24 h | Repurposing Hub, exact joins | GEO (public); licence field not recorded | Fully exposed | Time selection; LT headroom | **Development**; LT eligible but underpowered |
| GSE70138 | yes | 613 units among 673 eligible; 38 label-compatible | MCF7, PC3 and HT29 at 24 h | Hub | GEO | **Consumed** (vault opened once) | none as confirmation | **Development or retrospective only** |
| DepMap 24Q2 + PRISM 19Q4 + GDSC2 8.5 | yes, md5 sidecars | real_v3: 58 cases, 40 genes; engagement_v1: 6 cases | Model ID (ACH/SIDM); no dose or time match between CRISPR and drug | Licensing convention (not biological truth) | DepMap CC BY 4.0 (to confirm in sidecar) | Exposed | Premises of discordance cases | **AG premise source** |
| PISA living-cell K562 (eLife 2024, DOI 10.7554/eLife.95595) | yes, sha256 sidecar | 96 compounds, K562 only | Same cell line as DepMap K562; exposure undeclared, so no condition match to viability | Engagement call with measured false-positive rate 0.036 | eLife CC BY (to confirm) | Exposed (09-14 package; replayed today) | Intervention realisation (engagement), for AG | **AG stage-0 census input** |
| Kinobeads (Klaeger et al. 2017) | yes | lysate binding | Fixed lysate mixture: not a context match | Apparent Kd | publication supplement | Exposed | Orthogonal consistency check only | **Never a supplier** (estimate) |
| Nyman 2020 | yes | 1 melanoma line, time-resolved phosphoproteomics | No overlap with the MoA tasks | - | repository licence | Unused since 09-14 | r(t) method development only | **Defer** |
| LINCS 2020 (clue.io) | **no** | unknown: census needed | Compounds absent from GSE92742 and GSE70138 | Hub | to audit | Unopened | External confirmation of an MoA-task policy | **Metadata-only census**, when a candidate exists and download is approved |
| JUMP / CPJUMP1 (Chandrasekaran et al. 2024) | **no** | reported: compounds plus CRISPR and ORF perturbations of matched genes in U2OS and A549 | **Measured pairing** of genetic and chemical perturbation of the same genes in the same cells and assay | Target annotation | CC0 (to confirm) | Unopened | Whether morphology adds discrimination; a real genetic-pharmacological concordance task | **Highest-value census** for the primary use case, after approval |
| Tahoe-100M | metadata sample only (`arc_state/tahoe_metadata_source`) | cells are never units | 50 lines, many drugs | - | to audit | **Pretraining overlap:** the local State checkpoint is trained on it | Bounded response-model development | **Excluded as unseen cohort** for State arms |
| ChEMBL, OmniPath, Reactome | no | - | - | Answer-bearing compound-target and MoA entries | varied | - | Hypothesis generation | **Defer** until a KB track is registered with an answer-key audit |
| MSigDB (local subset) | yes | - | gene sets | - | licence restricted | Used 09-26 | Pathway readouts | as is |

## 2. Experiment registry

### E-DATA1: matched-cohort menu and second-step headroom qualification (MoA proxy task)

- **Hypothesis.**
  - (a) Some development task and menu has oracle-minus-fixed* correct headroom of at least 0.04 with a lower bound of
    at least 0.02, where fixed* is the best fixed sequence chosen on training folds.
  - (b) Expanding the menu raises the oracle ceiling, or lowers fixed* cost at non-inferior correctness and wrong rate.
    Candidate expansions use only measured conditions: all doses at 6 h and 24 h in L1000; the A549 72 h conditions in
    SciPlex3; a third measurement as a confirmation step.
- **Exposure:** development (exposed); scope limited to the proxy task.
- **Units:** SciPlex3 skeleton units; L1000 components. Identical eligible units for base and expanded menus; attrition
  reported.
- **Splits:** existing folds. Pools rebuilt per fold from training compounds (P0-2), with the legacy pools reported
  alongside for comparability.
- **Arms:**
  - fixed (legacy expert order);
  - fixed* (training-fold search over every sequence of length at most the budget);
  - random legal (seeded);
  - `myopic_edv`;
  - oracle (hindsight bound, never a competitor).
- **Estimands:**
  - headroom (correct and utility);
  - Δ oracle ceiling;
  - fixed* cost change;
  - unidentifiable and misleading shares;
  - second-step headroom, conditional and **per all episodes**;
  - units required under three variance scenarios (`belief`-like, `safe`-like, and twice `belief`'s departure rate).
- **Thresholds:**
  - A task and menu is `primary_eligible` if headroom ≥ 0.04 and the lower bound ≥ 0.02.
  - It is `powered` if the units required under the `belief`-like scenario do not exceed those available.
  - An expansion qualifies if Δ ceiling ≥ 0.02 with a lower bound above 0, or if fixed* uses at least 0.1 fewer
    measurements with correct no worse than -0.01 and wrong no worse than +0.005.
- **Failure rule:** if nothing qualifies, planner-superiority work stops on these data. The tasks stay regression and
  safety tests, and the next step is data acquisition (census).
- **Budget:** at most 2 CPU hours, no downloads, $0.
- **Artefacts:** `outputs/e_data1_<date>/`, a copy under the log day folder, and a registry record.
- **Status:** READY after P0-1 and P0-2 and a clean-commit registration.

### E-CAL1: cross-study and selected-action calibration (existing forecasts)

- **Hypothesis.** The world model's wrong-elimination forecast, or a registered conservative bound on it, covers the
  observed rate on the actions each frozen arm actually selects, per step and **per episode**, on both
  leave-one-study-out targets.
- **Exposure:** development plus GSE70138 post hoc (consumed; descriptive only).
- **Items:**
  - executed QC-passed steps of `belief`, `safe` and `myopic_edv`;
  - episode-level cumulative false elimination among decided episodes;
  - deferral and coverage.
- **Methods, simplest first:** raw; the planner's Jeffreys bound; Platt; hierarchical (κ = 20); discounted (λ = 0.5).
  Isotonic or conformal methods are allowed only where there are 200 or more items per target and exchangeability is
  stated; with 2 studies they stay exploratory.
- **Gate for any risk-controlled stop:**
  - The bound covers the observed rate overall and in at least 95% of strata with 20 or more items, on both targets.
  - No stratum is significantly above the bound.
  - The bound is informative: its mean is at most 3 times the observed rate.
  - The last rule is new. The current planner bound passes coverage while being 10-35 times too high.
- **Failure rule:** no forecast-driven stop and no risk claim. Conservative heuristics may be explored, not promoted.
- **Budget:** minutes of CPU, no downloads.
- **Artefacts:** `outputs/e_cal1_<date>/`.
- **Status:** READY (records exist); register first.

### E-WM1: dose, time and realisation conditioning of the forecast

- **E-WM1a (time-only).** On L1000 LT (6 h and 24 h) and SciPlex3 A549 (24 h and 72 h), compare three world models
  behind the same `OutcomeForecast` interface:
  - M0: per-condition empirical (current);
  - M1: pooled across dose within time;
  - M2: dose plus time smoothing (ridge on registered covariates).

  Endpoints: held-out log loss and Brier of registered reading labels (WM-G1), then one-step action regret (WM-G2).
  Same eligible units and charged inputs.
- **E-WM1b (deployable realisation):** **NOT_READY.** No condition-matched realisation measurement exists before the
  candidate action for these compounds. The PISA exposure is undeclared, it is single-context K562, and its overlap
  with the task compounds is not censused.
- **E-WM1c (privileged measured r(t), upper bound only):** **NOT_READY** for the same reason.
- **Thresholds:** see WM gates below.
- **Status:** E-WM1a READY after E-DATA1 qualifies L1000 LT (or a successor); b and c NOT_READY. Minimum data for b:
  engagement or proximal function measured at the task's dose and time, in the task's cell line, for at least 50 units.

### E-AG1: prerequisite-directed repair

- **Stage 0 (AG-G0 census).** Premise and metadata only; no engagement value is read.
  - Enumerate (compound, target, context) triples with a strong selective dependency, an inactive or weak phenotype,
    and an intact-cell engagement or proximal-function capability in the same context.
  - Current evidence: 865 screened candidates gave 6 cases (5 K562 and 1 MCF7; 5 genes).
  - The census re-runs the package's own screening rules. It also lists what CPJUMP1 and LINCS 2020 metadata could add
    (download approval required).
- **Stage 1 (AG-G2 development test).**
  - Task: engagement-gap discordance (engagement_v1 archetypes).
  - Unit: case. Cluster: primary target gene.
  - **Arms:**
    - F: fixed expert (menu).
    - S: outcome-aware one-shot (menu).
    - A0a: registry-expanded one-shot selection, with the same capabilities admitted in advance.
    - A0b: exact contingent optimum over the closed legal space, with the same declarations (`evaluation.contingent`).
    - A1: `registry_repair_rule`.
    - R: random proposal.
    - An LLM proposal arm only if LLM-specific value is claimed; it is not claimed now.
    - Every arm shares the same typed admission and licensing rules.
  - **Endpoints:**
    - Primary: wrong development action rate (at most 0.02 worse than A0a); over-deferral rate; cost units.
    - Secondary (plan construction): capability evaluations and compilations per licensed decision on a registry of
      100 or more offers.
    - Scoring: licensing verdict, plus the independent kinobeads final test where a partition exists, plus the
      registered blind adjudication (`data/evaluation/preregistrations/20260914_blind_adjudication.md`).
  - **Thresholds.** AG-G2 PASSES if either condition holds:
    - (i) A1 reduces over-deferral by at least 0.10 versus A0a, with the 95% cluster CI above 0, wrong actions
      non-inferior, and cost no higher;
    - (ii) at identical decisions, A1 needs at most 50% of A0a's capability evaluations.
  - **The trap to avoid:** A1 cannot beat A0b under matched information and a small enumerable space. Matching A0b is
    efficiency, not superiority.
- **Exposure:** engagement_v1 is exposed. New cases need the stage-0 census and a fresh preregistration.
- **Current evidence (replay today, 6 cases, not inferential):**
  - A1 and A0a reach the same licensed decisions at the same cost in 4 of 4 decisive cases.
  - They differ on ABL1/dasatinib (a different licensed decision) and on MCF7/AZD2014 (A1 spends 2.0 against 0; both
    defer).
- **Minimum units:** exploratory at least 30 target-gene clusters; confirmatory from stage-1 variance.
- **Status:** stage 0 READY; stage 1 NOT_READY (6 cases, 5 clusters).

### E-JOINT1: two-core 2 x 2 attribution

- **Arms.**
  - A0W0, A1W0, A0W1, A1W1, where A is as in E-AG1.
  - W0: the class-conditional empirical frequencies of registered reading labels behind `OutcomeForecaster`.
  - W1: the candidate conditional predictor (`ReferenceWorld` with structural kernel, or a future engagement
    predictor).
  - The prediction-free fallback F runs as a fifth, named arm.
  - Masking and permutation keep the applicability handling, legal menu and validator. Permutation swaps forecasts
    between compounds within the same condition and support bin.
- **Endpoint J:** per-unit utility (+1 licensed correct, -2 wrong development action, 0 deferral) minus 0.02 per cost
  unit, higher is better. Paired by unit, cluster-bootstrapped.
- **Effects:**
  - simple effects J(A1W·) - J(A0W·) and J(A·W1) - J(A·W0);
  - the interaction I = (J_A1W1 - J_A1W0) - (J_A0W1 - J_A0W0).
- **Priority:** agent simple effect at W0; world-model simple effect at A0; then I. I is **exploratory** unless the
  registered power for I is at least 0.8.
- **Prerequisites (both missing):**
  - a code path that feeds `OutcomeForecast` to repair selection (PLAN.md P1-4);
  - a task where the prerequisite result or the downstream readout is forecastable from pre-decision information with
    support of at least 20 references per branch.
- **Status:** NOT_READY.

### EXT-1: conditional external confirmation

- **Trigger:** a frozen candidate passes WM-G3 or AG-G2 on development. Nothing does today.
- **Cohort:** an unopened study with at least max(500, units required) label-compatible units (MoA task, for example
  LINCS 2020 compounds new to both GSE studies), or, for the agent, new discordance cases with condition-matched
  engagement.
- **Procedure:**
  - metadata-only census and manifest;
  - pool and contrasts from references;
  - freeze of code, model, preprocessing, menu, calibrator, rules, thresholds, seeds and analysis;
  - clean-commit registration;
  - evaluator-only single reveal;
  - disclosure of any prior exposure (analysts, agents, pretrained models, validators, knowledge base).
- **Generalisation claim** named in advance: new compounds; new scaffolds; new cell contexts; new study. Target-study
  reference fitting is adaptation and is labelled as such.
- **Status:** NOT_READY.

## 3. Gates

| Gate | Definition and numeric threshold | Current status | Evidence |
|---|---|---|---|
| WM-G0 | Simple baselines (training mean or pooled, class-empirical, nearest reference, ridge; plus zero-effect and PCA for profiles) reproduce their recorded held-out metrics within ±0.005 on leakage-controlled splits (D7, D8 and D10 pass) | **NOT_READY** | Baselines exist; D7 and D8 are open |
| WM-G1 | Candidate beats the best simple baseline on held-out log loss of registered labels by at least 0.02 nats per step (CI above 0), with observed/forecast wrong-elimination ratio in [0.67, 1.5] on both leave-one-study-out targets, and a competence flag that separates error rates (CI above 0) | **FAIL** for `ReferenceWorld`'s structural kernel | Kernel strength 0 on L1000; ratio 2.0-5.0 |
| WM-G2 | One-step action regret at least 0.01 below the best simple baseline (CI above 0), with no more than 0.1 extra measurements | **FAIL** | Action change at most 4.5% with no regret gain |
| WM-G3 | Paired correct difference against fixed of at least 0.02 (CI lower bound above 0); wrong rate at most +0.005; measurements at most +0.1; days at most +0.6; confirmatory units; scaffold, study and line sensitivity | **FAIL** (development), **INCONCLUSIVE** (GSE70138) | H6 |
| WM-G4 | The frozen G3 result reproduces on an eligible unopened cohort (EXT-1) | **NOT_READY** | - |
| AG-G0 | A genuine interpretation-prerequisite gap exists on development observations, a feasible measurement supplies it, and it changes an evidence-supported decision | **PASS (existence, 6 real cases); NOT_READY (population)** | 4 of 6 cases change from deferral |
| AG-G1 | A trace shows identification, repair, verification against real results and a scope-limited update | **PASS** (implementation correctness only) | [DATAFLOW.md](DATAFLOW.md) section 4; 123 invariant tests |
| AG-G2 | E-AG1 stage-1 thresholds against A0a and A0b | **INCONCLUSIVE**: no additional algorithmic contribution identified on 6 cases | Replay today |
| AG-G3 | The frozen AG-G2 result reproduces on unopened units | **NOT_READY** | - |
