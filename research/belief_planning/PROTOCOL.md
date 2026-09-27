# Belief-planning protocol (belief-planning-1)

Registered 2026-09-27, before any GSE70138 measurement, QC metric or test label was read.
`protocol.json` is the machine-readable version, and `freeze.json` holds the digest of every file
the runs depend on. This document restates both. Where they differ, `protocol.json` rules.

## 1. Question

Can an agent that plans real measurements with a virtual-cell world model reach better terminal
mechanism decisions on unseen compounds than strong simpler policies? It must do so under the same
wrong-decision risk limit and the same experimental budget.

## 2. The agent (candidate `belief`)

- **State.** A belief over the two competing hypotheses, formed only from real readings: a
  uniform prior, then Bayes' rule under the world model. Alongside it, the history of measured
  conditions and their registered readings.
- **Planner.** `maestro.planning.plan_measurement`, an exact expectimax over the remaining budget
  (at most two measurements) within the runner's legal menu. A correct single-survivor decision
  is worth +1, a wrong one -2, and stopping 0; each measurement costs 0.02.
  - The probability that a registered elimination is wrong is the posterior mass of the
    hypothesis it removes.
  - The agent replans after every real reading.
- **Roles.** Forecasts choose actions only. They never enter `EvidenceState`, never remove a
  hypothesis, and are never recorded as measurements. The registered validator makes every
  elimination.
- **World model** (`world.py`). For each measurement and hypothesis h, the distribution of the
  validator's reading, estimated from training references in three layers:
  - the pooled rates at the condition;
  - the references annotated h, shrunk to the pooled rates with strength `s`;
  - the virtual cell: a structural (Tanimoto) kernel over those references, zero below 0.40
    similarity and scaled by `k`, shrunk to the class layer.

  Readings already observed reweight references by whether their own reading matched
  (mismatch weight `e`). `s`, `k` and `e` are fitted per fold by leave-one-out likelihood on
  training references only. `k = 0` means the virtual cell abstains.
- **Secondary candidate `anchored`.** The same agent, leaving the fixed expert order only when
  the forecast gain exceeds 1.645 standard errors (safe policy improvement with baseline
  bootstrapping).

## 3. Controls and comparators

Controls:
- **Virtual cell masked**, and **permuted** (another held-out compound's structure).
- **Feedback withheld**: the agent knows only that the reading did not end the episode.
- **Feedback permuted**: a compatible real reading of another held-out compound.
- **One-step lookahead.**

Comparators: the 2026-09-27 ladder.
- **Fixed expert order** (the primary comparator), random, cheapest.
- **Reference marginal estimates**, **measured-profile retrieval**, structure-kNN magnitude,
  ridge, and mutual information.
- **The non-agent myopic expected decision value**, the 2026-09-27 agent path, the production
  default, and the sparse two-step planner.
- **Oracle**: an upper bound only.

Every arm runs through `sequence_audit.policies.run_matched` on the sealed view, with identical
episodes, menus, budget, QC rule and stopping.

## 4. Data

- **Development.** SciPlex3 tiers A and B, and L1000 Phase I tiers LT and T, on the 2026-09-27
  registered episodes. These are development data only.
- **External.** GSE70138 (LINCS L1000 Phase II), Level 5 signatures. The task is three lines by
  four doses at 24 h, with at most two measurements and 16 assay-days.
  - The lines are the three core lines with the most known reference compounds measured at all
    four doses: MCF7, HT29 and PC3.
  - The doses are the nearest to SciPlex3 B's: 0.04, 0.12, 1.11 and 10 uM.
  - The fixed order is 10 uM in MCF7, then 10 uM in HT29.
  - The reference arm is Phase II compounds already in the development studies (1,053).
  - The test compounds are the 673 new ones (613 units). None shares a Broad ID or InChIKey block
    with any development compound, and none shares a batch with GSE92742. 152 of them share a
    Murcko scaffold with GSE92742 compounds; results are stratified by structural novelty.
  - The hypothesis pool, validator calibration and world-model fit come from the reference arm by
    the frozen rules, inside the vault. Test labels are read only for scoring and to form the
    forced-choice contrast.
- **Not used.** A stricter design used a Phase I reference library for a Phase II line-choice
  task. It gives only 96 development episodes over 4 classes, too few to develop or check a policy.

## 5. Endpoints, gates, status

Endpoints are reported separately:
- correct, wrong and deferred decisions;
- coverage and selective risk;
- measurements, assay-days and wells.

Intervals are unit-cluster bootstraps (2,000 draws). Units are skeletons, components, or
test-compound components.

Gates on paired differences (candidate minus comparator, same episodes):
- **G1.** The upper bound of the candidate's wrong rate is at most 0.05.
- **G2.** The upper bound of the wrong difference is at most +0.005.
- **G3.** The lower bound of the correct difference is above 0, and the estimate is at least 0.02.
- **G4.** The upper bound of the measurement difference is at most +0.10.
- **G5** (virtual cell) and **G6** (feedback). The lower bound of the correct difference is above
  0 against both of the relevant controls.

Status:
- **DEMONSTRATED**: G1-G4 pass externally.
- **INTERNALLY SUPPORTED**: G1-G4 pass on a development tier.
- **REJECTED**: the upper bound of the correct difference is below -0.01, or the lower bound of
  the wrong rate is above 0.05. A contribution is rejected when its upper bound is below 0.02.
- **INCONCLUSIVE**: otherwise.

The single primary test is `belief` against `fixed` on GSE70138. Everything else is descriptive.
No policy becomes a production default under this protocol.

## 6. Calibration and risk

- Calibration is audited for correct- and wrong-elimination forecasts of the chosen action, for
  the true hypothesis, against the realised reading.
- It is broken down by support, line, dose, time, detection, step and structural novelty. ECE is
  diagnostic.
- The risk gate is the directly measured wrong rate and its bound. No development guarantee is
  carried to the external study, because the two studies are not exchangeable.

## 7. Disclosure

- The development decisions made after seeing development results are listed in
  `protocol.json`. They were made on development data before the external study was opened.
- Before the freeze, the external study was read as follows:
  - the metadata files;
  - the gctx schema (names, shapes, ids);
  - the column names of `sig_metrics`.
- No external value or test label was read before the freeze.
