# Certified-discovery Gate 0 (headroom) and Gate 1 (validity): pre-registered protocol

## October 23 pre-freeze amendment

The original protocol below remains a historical proposal, not an executed validity claim. No `FREEZE.json` or prepared numeric data existed when this amendment was added. The current [independent reviews and smaller diagnostic](../evidence_portfolio_optimization/README.md) take priority before any real Gate 0/1 execution.

- Gate 1 outputs are `GATE1_DIAGNOSTIC_PASS`, `_FAIL` or `_INCOMPLETE`; the mathematical certification status remains `NOT_ESTABLISHED`. All required pools and cells must exist before a diagnostic pass. Gate 1b is a plate-rank diagnostic.
- A finite null grid does not prove the composite null. Reusing data to fit nuisance parameters, shared-plate dependence, t differences not having the single-read t law, and the nonmonotone t likelihood ratio invalidate stronger interpretations below. In particular, mirroring positive signals does not guarantee lower likelihood ratios pointwise. Do not treat pseudo-null diagnostics as verified null controls.
- Half weight at each multiplier does not guarantee half of standalone base wealth over time. A protected fixed-capital wallet provides a same-stream bound only; neither construction guarantees the performance of a different allocation policy. Retrospective scores cannot identify unobserved actions or entire counterfactual adaptive histories.
- Detailed NPZ arrays, weights, traces and replay CSVs now belong in `data/processed/certified_discovery_gates_20261023/`; key JSON summaries and reports remain here. The execution-order filenames below must be resolved using that split.
- The synthetic harness now exits nonzero on any failed test or an empty test selection. Limited new regression checks are recorded in the optimization record; the full historical suite has not been rerun by this amendment.

Do not open the AZ reserve or promote runtime code on the basis of this prototype. A matched real-data diagnostic and explicit conditional-validity contract would be required before considering further certification work.

**Status.** Pre-registration, 2026-10-23. `FREEZE.json` binds this file, `START.md`, `CENSUS.json`, all code and the input archives. The freeze is written before this study converts any response value. Every later change is recorded in `DEVIATIONS.md`, which the freeze does not hash.

**Scope.** Exposed development data only:
- Jaaks 2022 (fully exposed).
- AZ2024 GDSC_007 rows of the 320 exposed MASTER cells of `log/20261022/az_paid_reference_gate/DESIGN.json` (train, validation and test).

Excluded:
- No row of the 413 reserve cells, nor of unassigned cells, has any field used beyond MASTER_CELL_ID.
- The GDSC_008, GDSC_009, GDSC_010 and Sandpiper-01 members stay unopened.
- No world model, LLM, PRISM or LINCS asset enters.

## 1. Questions and decision labels

**Gate 0 (headroom).** With certification held fixed (e-BH at alpha = 0.1 on e-processes), how many more certified discoveries per 1,000 confirmation wells would perfect knowledge of the true effects buy over the fixed confirmation workflow (A1)?
- Asset PASS: the ratio of mean efficiencies ORACLE / A1 is at least 1.20 at budget c = 1, two rounds, semi-synthetic replay, and its 95% bootstrap lower bound is above 1.00.
- Asset FAIL: otherwise.
- Asset NOT_TESTABLE: both arms have zero discoveries in more than half the replays.
- Combined result:
  - both assets pass: `GATE0_PASS`;
  - exactly one passes: `GATE0_MIXED_PRISM_TIEBREAK_PENDING`;
  - neither passes: `CERTIFIED_DISCOVERY_HEADROOM_INSUFFICIENT`.

**Gate 1a (validity of the model-based certification pipeline used by Gate 0).** Every cell of Section 8 must pass on both assets: `GATE1_PASS`. Otherwise `VALIDITY_NOT_ESTABLISHED_IN_REPLAY`, with the failing cells listed.

**Gate 1b (design-based positional validity in GDSC layouts).** `DESIGN_BASED_POSITIONAL_VALIDITY_PASS` or `_FAIL`. This informs future prospective designs. It is not part of the Gate 1 decision.

## 2. Data, units and reads

### Jaaks

**Unit.** u = (SIDM, ANCHOR_ID, ANCHOR_CONC, LIBRARY_ID). ANCHOR_CONC is normalised as `repr(float(x))`.

**Read.** SYNERGY_DELTA_EMAX, defined as Bliss-expected minus observed viability at the highest library concentration. Positive means synergy.

**Pool.** Units with at least one original-screen row and at least two validation-screen plates with a finite read.

**Primary read.** p_u is the mean finite original-screen read over the unit's original plates; n_o is the count of those plates.
- If no original value is finite, p_u is NaN. A1 then ranks the unit last, and the primary-model fit excludes it.
- Evidence reads come only from the validation screen. The original screen is never evidence, because the validation subset was chosen from original-screen results.

**Read order.** For replay r, a unit's validation reads are ordered by SHA256(f"{r}|{unit}|{BARCODE}").

**Wells per read.** 7: the unit's combination wells on that plate.

**Inactive flag (Gate 1a pool J-P2).** Mean original ANCHOR_VIABILITY >= 0.9 and mean original LIBRARY_EMAX >= 0.9, both finite.

### AZ (GDSC_007, exposed cells)

**Matrix read.** For each matrix (BARCODE, cmatrix), the read is the mean of the finite well-level Bliss_excess values. At least 80% of the matrix's wells must be finite; otherwise the read is NaN and dropped.

**Wells per read.** The matrix's well count (49 or 35).

**Unit.** (MASTER_CELL_ID, sorted lib1/lib2 drug ids). Every read of a unit comes from a distinct plate (census: no within-plate replicates).

**Groups.**

| Group | Finite reads | Content |
|---|---|---|
| G1 | 1 | single-plate units |
| G2 | 2-3 | replicated non-control units |
| G3 | 4 or more | the 50 control combinations |

**Pools.**
- Real-read matched pool: G2. The primary read is the first read in the replay's order; the evidence reads are the rest.
- Semi-synthetic prospective pool: every unit with at least one finite read.

**Inactive flag (Gate 1a pool AZ-P2).** Over all wells of all the unit's matrices, the maximum lib1_yhat and the maximum lib2_yhat (fitted single-agent inhibition) are both finite and at most 0.1. This is the AZ counterpart of the Jaaks viability >= 0.9 rule.

## 3. World fit (development; all exposed reads)

**Noise.**
- Use every unit with n >= 2 finite reads (Jaaks: validation reads of pool units; AZ: G2 and G3).
- Fit single-read Student-t noise (sigma > 0, nu in [2.1, 100]) by maximising the location-invariant likelihood: the product over units of the integral over m of the product over reads of f_t(x - m). This is the exact density of each unit's within-unit contrasts, and it does not depend on the effect prior.
  - Optimiser: L-BFGS-B, started from the residual fit below.
  - Quadrature: the trapezoid rule on m = unit mean + s tan(theta), with 2,001 interior theta points and s fixed at the residual-fit sigma.
- Reported but not used: a location-0 t fitted to residuals r = (x - mean) * sqrt(n/(n-1)).
- AZ diagnostic: separate invariant fits for G2 and G3.

**Prior G.**
- Grid: 401 points on [-1, 1].
- NPMLE by EM until the relative log-likelihood change is below 1e-10, or for 5,000 iterations.
- Jaaks: pool units, validation reads only.
- AZ: all units, all reads.

**Primary model.**
- Jaaks: p = a + b mu + eta, with eta ~ t(nu, sigma_p / sqrt(n_o)). (a, b, log sigma_p) are fitted by marginal likelihood with G and the noise model held fixed.
- AZ: p is one read, so p = mu + eps with the evidence noise model.

## 4. e-values and certification

**Read multiplier.** For a bet m > 0, LR(x; m) = f_t(x - m) / f_t(x), using the fitted (sigma, nu). The null boundary is mu = 0, and the claim is mu > 0.

**Composite-null check (pre-run, on the fitted parameters).**
- For 200 values m/sigma in [0.05, 10] and 101 values mu/sigma in [-5, 0], compute E_mu[LR(.; m)] by numerical integration.
- The valid set M_valid is every m whose maximum over mu is at most 1 + 1e-6.
- Any bet outside M_valid is clipped down to the largest valid m below it.

**Prior-free bettor (PF).** The uniform mixture over m/sigma in {0.25, 0.5, 1, 1.5, 2, 3, 4}: e_u = mean over m of the product over reads of LR(x; m). A mixture of test martingales is itself one.

**Oracle bettor.** m = mu_u. It exists only in semi-synthetic replays, and only units with mu_u > 0 are read.

**e-BH (alpha = 0.1).** Unread units have e = 1. Over the K pool units, k* = max{k : e_(k) >= K/(alpha k)}, and the k* largest are rejected. The computation is done in log space.

## 5. Arms (Gate 0)

**Budget and rounds.**
- Budget: B reads.
- Round 1 spends B1 = floor(B/2); round 2 spends B - B1.
- A unit can take at most R_u reads, revealed in its fixed order.
- Within a round, reads are dealt in passes down the round's priority list: one read per listed unit with remaining availability per pass, until the round's budget is spent.

**Arms.**

- **A0 (zero arm).**
  - Round 1 priority: a random permutation of units.
  - Round 2 priority: a random permutation of units with availability left.
  - PF bets; no stopping.
- **A1 (fixed workflow: top-k retest, verify-hits, P2 stopping).**
  - Round 1 priority: descending p, with NaN last and random tie-breaks.
  - Then compute PF e-values, k1 = the number of round-1 e-BH discoveries, and T = K/(alpha * max(k1, 1)).
  - Round 2 priority, in order:
    1. round-1 units with 1 <= e < T, by descending e;
    2. unread units, by descending p;
    3. round-1 units with e < 1, by descending e.
  - Units with e >= T are stopped.
  - PF bets.
- **OA-PF (oracle allocation, prior-free bets).**
  - Round 1: units with mu > 0, by descending mu.
  - Round 2: the same units with e < T (T from OA-PF's own round-1 e-values), by descending mu.
  - Units with mu <= 0 are never read.
  - PF bets.
- **ORACLE.** As OA-PF, with oracle bets, and T computed from the oracle's e-values.
- **A1c (descriptive only; the conformal certificate of PERSPECTIVE section 5.1).**
  - That certificate works in a regime (audit much smaller than shortlist) that c >= 1 budgets do not create. It is therefore run once per replay with a 10% uniform audit of the pool, one read per audited unit, so wells = 7 x audit size.
  - Shortlist: the whole pool, scored by p.
  - Audit label: read > 0.
  - Nominations: conformal p-values with BH(0.1), using `conformal_pvalues`, `benjamini_hochberg` and `minimum_audit` from `src/maestro/certification.py`. These are the nominations of `certify()`; the yield bound is skipped because it is O(n^2) in Python.
  - In real-read replays, the realised false-label rate is measured on each nominee's first unrevealed read.
  - A1c certifies a label for unmeasured candidates, a different estimand, and never enters a decision.

## 6. Budgets and metrics

**Budgets.** c in {1, 2, 3} reads per pool unit, with B = min(round(cK), the sum of R_u). c = 1 is primary.

**Per replay.**
- D: e-BH discoveries after round 2.
- D1: discoveries after round 1.
- Reads and wells spent.
- Efficiency = 1000 D / wells (0 if no wells are spent).

**Aggregation.** Means over replays. Ratios of means between arms carry a 95% percentile bootstrap over replays (2,000 resamples, paired by replay).

## 7. Gate 0 procedure

**Semi-synthetic replays.** 200 per asset and budget.
- Each replay draws mu_u iid from G, then the primary reads and evidence reads.
- Availability R_u:
  - Jaaks: the real R_u.
  - AZ prospective: R_u = 3.
  - AZ matched: the real 1-2 evidence reads.
- All arms share the replay's world.

**Real-read replays.** 200 per asset and budget, for A0, A1 and A1c, on the matched pools. Read orders and A0 draws change per replay.

**Primary statistic.** R0 = ORACLE / A1 efficiency at c = 1, from the semi-synthetic replays: the Jaaks pool, and the AZ prospective pool.

**Calibration flag.** At c = 1, the real-read A1 mean efficiency must lie inside the 2.5–97.5% range of the semi-synthetic matched-structure A1 replays. The matched structure is the Jaaks pool for Jaaks, and AZ matched for AZ. Otherwise the asset's label gets the suffix `_SIMULATOR_MISCALIBRATED`.

**Also reported, for every budget:**
- A1/A0;
- OA-PF/A1 (allocation headroom);
- ORACLE/OA-PF (betting headroom);
- D1 against D.

## 8. Gate 1a: model-based validity

### Pseudo-null pools

- **J-P1.** All Jaaks pool units. Pseudo-reads are z_k = (x_(2k-1) - x_(2k)) / sqrt(2) over disjoint consecutive pairs in the replay order. Allocation uses the unit's real p.
- **J-P2 (mirrored).** Inactive Jaaks pool units, with their real validation reads negated.
  - Why mirror: true synergy among inactive pairs can only lower the mirrored e-values, so contamination cannot cause a false fail.
  - Why this pool matters: it is the only Jaaks pool that tests the single-read noise law; pair differences are partly averaged.
  - The pool is NOT_TESTABLE if fewer than 200 units qualify.
- **AZ-P1.** G2 and G3 units, with pseudo-reads formed as in J-P1. Allocation uses the unit's mean read as p.
- **AZ-P2 (mirrored).** Inactive AZ units (Section 2), using all their real reads negated, with the unit's mean read as p. The pool is NOT_TESTABLE if fewer than 200 units qualify.

### Allocation

- Round 1: J-P2 by descending p; the P1 pools and AZ-P2 in random order.
- Round 2: verify-hits by descending current e of the bettor in use.
- Units with e >= T are stopped, with T as in A1.

### Bettors

- **b1:** PF.
- **b2:** fixed m = 3 sigma.
- **b3:** adaptive per-step predictable portfolio.
  - Experts: PF, m = 1 sigma, m = 3 sigma, and a learned m.
  - Round-1 reads use uniform weights.
  - Round-2 reads use q = 0.5 on PF plus 0.5 x softmax over the other experts' summed round-1 log-multipliers, summed across all units read in round 1.
  - The learned m is max(0.25 sigma, the mean of positive round-1 reads).

### Grid

Budgets c in {1, 2}. Stopping times: the end of round 1 and the end of round 2. 200 replays.

### Pass criteria, per cell (pool x bettor x budget x stopping time)

Every cell must pass (a), (b) and (c). In addition, the composite-null check must find every checked bet valid for both assets: all 200 values of m/sigma in [0.05, 10].

- **(a) Capped stopped e-values match the fitted model.**
  - Statistic: over pseudo-null units read at least once, pool min(e, 20) over replays and units.
  - Reference: the same statistic on pools simulated from the fitted model, with the same units, availability, p, allocation, bettor and budget, over 200 simulated replays. Pair-difference pools simulate (t1 - t2)/sqrt(2); single-read pools simulate single t reads.
  - Pass: statistic <= reference + 3 sqrt(SE_obs^2 + SE_sim^2). SE_obs is the bootstrap SE over units (2,000 resamples); SE_sim is the replay-to-replay SE of the simulated statistic.
  - Under the fitted model, E[e] <= 1 holds by the composite-null check, so passing (a) means the pseudo-null e-values show no departure from the model. The uncapped mean e (point and bootstrap upper bound) and P(e >= 20) are diagnostics, each reported next to its simulated value.
- **(b) All-null FWER**, the fraction of replays with at least one e-BH discovery: at most 0.1 + 2 sqrt(0.09/200) = 0.1424.
- **(c) Mixed pool.**
  - Construction: every pool's pseudo-null units are added as extra units to the asset's real pool (Jaaks pool, or AZ matched for AZ).
  - Under A1 allocation with the bettor in question, the mean over replays of V_pseudo / max(R, 1) must be at most alpha K_pseudo / K + 2 SE. This follows from e-BH's per-null bound E[1{j rejected}/R] <= alpha/K.

### Diagnostics (no pass/fail)

- Mean and median of pseudo-null reads, with the standard error of the mean (bias).
- Two-sample KS distance between pseudo-null reads and model-simulated pseudo-reads.
- Read-level calibration: the mean of LR(x; m) for m in {0.5, 1, 2, 3, 4} sigma, with its SE, next to the same on model-simulated reads.
- The uncapped mean e and P(e >= 20), each next to its simulated value.
- For J-P2 and AZ-P2: e-BH discoveries among inactive units on their unmirrored reads, which estimates true synergy among inactive pairs.

## 9. Gate 1b: design-based positional validity (Jaaks raw, original screen)

**Per plate.**
- References: the 114 NC-1 wells.
- Type N pseudo-treatments: 10 randomly drawn NC-1 wells, each ranked among the other 113.
- Type L pseudo-treatments: the lowest-dose (D7) single-agent wells of libraries inactive in that line. Inactivity means a leave-plate-out mean original LIBRARY_EMAX >= 0.9 over other plates with the same (SIDM, LIBRARY_ID). Each well is ranked among the plate's 114 NC-1 wells.

**Ranking and design e-value.**
- Ranks are by INTENSITY ascending, with random tie-breaks.
- The bottom set is ranks <= ceil(0.05 (k+1)).
- The design e-value is (k+1) / |bottom| x 1[rank in bottom]. Its expectation under exchangeability is 1.

**Role of each type.**
- Type N is a code sanity check only. A uniformly drawn NC-1 well ranked among the other NC-1 wells has a uniform rank by symmetry, whatever the positional effects, so Type N cannot detect them.
- Type L decides the Gate 1b label.

**Pass (per type).** Point estimate at most 1.10, and the 95% bootstrap upper bound (resampling plates) at most 1.25. The design e-value is bounded by about 19.2, so this upper bound is stable.

**Diagnostics.** The KS distance of normalised ranks from uniform, and the top-5% frequency.

## 10. Structural checks

- **Jaaks:** the original and validation barcodes are disjoint, and each unit's validation reads sit on distinct barcodes.
- **AZ:** each unit's reads sit on distinct barcodes, and the primary read and the evidence reads never share a plate.

**Recorded design-based caps.**
- A within-plate synergy rank bet gains at most a factor of 5 per plate, about 1.6 nats.
- Any symmetry-only e-value from n reads is at most 2^n. For n <= 3 that is at most 8, below the 1/alpha = 10 that e-BH needs.

## 11. Deviations from PERSPECTIVE sections 5.2–5.3, decided before any outcome

| ID | Deviation | Reason |
|---|---|---|
| D1 | The oracle knows the true effects in a semi-synthetic replay calibrated to real reads. | An oracle whose truth is "all-replicate means" bets on, and allocates by, the very reads it is certified with (winner's curse). |
| D2 | The primary e-values are model-based, with calibrated t noise. Design-based validity is checked separately in Gate 1b. | Section 10 caps design-based evidence below what certification needs. Validation raw wells are absent. AZ has no control wells. |
| D3 | The gate comparator is A1 allocation with the same e-BH certification. The conformal certificate is descriptive (A1c). | The two certify different estimands. |
| D4 | The pass rule needs both Jaaks and AZ. One pass is MIXED, with PRISM as the tiebreak (not run here). | Only two assets are in scope. |
| D5 | The Gate 1 criterion is replaced by Section 8 (a)–(c). | Two reasons. Exact nulls give E[e] = 1, so the original "upper bound <= 1" rule would fail from sampling noise alone. And under heavy-tailed noise, the mean of e-values is dominated by a few extreme units (Section 15). |
| D6 | Budgets are c reads per pool unit, capped at availability, with c = 1 primary. | The perspective's "1, 2, 3 reads per hypothesis" needed an operational form. |
| D7 | The "self-improvement loop" is represented by the adaptive portfolio b3. | No world-model refit exists yet. |
| D8 | AZ Gate 0 is primarily a prospective-structure simulation. | Exposed AZ has replicate plates for only 336 non-control units. |

## 12. Seeds and numerics

- Every random draw uses `numpy.random.default_rng(int(sha256("cdg|" + "|".join(labels)).hexdigest()[:16], 16))`. The labels name the pool, the mode, the budget, the replay, and the arm or bettor where one applies (`common.replay_rng`). World draws are shared by all arms of a replay; each arm has its own tie-break stream.
- Bootstrap seed: 20261023.
- All e-values are computed in log space.

## 13. What this study does not test

- The world model (A3) and direct predictors (A2).
- Portfolio efficiency (A4, A5).
- A conventional agent (A6).
- Any LLM.
- PRISM or LINCS.
- Any reserve.
- Prospective validity.

## 14. Execution order

1. `census.py` (done; metadata only).
2. Code and `test_synthetic.py`, producing `SYNTHETIC_TESTS.txt`.
3. `freeze.py`, producing `FREEZE.json`.
4. `prepare.py`, producing `DATA_JAAKS.npz`, `DATA_JAAKS_RAW.npz`, `DATA_AZ.npz` and `PREPARE_RECEIPT.json`. This is the first response conversion in this study.
5. `gate1.py`, producing `WORLD_FIT.json/.npz`, `GATE1_RESULTS.json` and `GATE1_TRACE.npz`.
6. `gate0.py`, producing `GATE0_RESULTS.json`, `GATE0_REPLAYS.csv` and `GATE0_TRACE.npz`.
7. `verify.py`, an independent recomputation, producing `VERIFICATION.json`.
8. `DECISION.md`.
