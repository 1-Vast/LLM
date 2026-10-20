# Protocol: typed experimental/state programs that are tested, nominated, inherited and retired (development prototype)

Frozen (hash in `FREEZE.json`) after software controls and the source-side headroom check, before any comparative real-data scoring.
This is a bounded development prototype on exposed internal data. A hidden partition is not independent confirmation; passing software
tests is not scientific validation. The object under test is a procedure (what to measure, how to turn it into a state, how the state
changes a prediction), not a molecular mechanism.

## 1. Question and claims in scope

A new cell background arrives with limited parallel pair-grid measurements. Can a small versioned library of *typed programs* — a measurement
plan **Q**, a state map **phi**, a conditional response model **f**, and an applicability record **Omega** — be grown from released
backgrounds so that later backgrounds get a better combination shortlist than (a) the same history used by a fixed refit, (b) the same budget
used by a conventional acquisition rule, and (c) conventional joint learners? Not claimed: new drugs, unseen pairs across all backgrounds,
patient efficacy, resistance, sequencing, or any wells/cultures/money figure. The query unit is one pair-by-cell 4x4 dose grid, counted once.

## 2. Information boundary

* Environment: the allowlisted export `tmp/self_improving_virtual_cell_20261020/env_export.npz` = old S outcomes (350 pairs) plus only the 60 acquired
  old-C challenge pairs (their ids equal the `disclose_C` ledger of the prior study), 410 pairs x 39 cells. The 27 non-acquired C pairs, G and F were never
  opened. No raw workbook was reparsed. Endpoint A = 1 - mean(X/X0) over the 16 points; reference A_ref is the multiplicative (Bliss-type) reference
  of the two monotherapy summaries (checked exactly in tests); R = A - A_ref. All methods get the same monotherapy information.
* Backgrounds are cells; membership is fixed from metadata only (SHA-256 order of `svc20261020|<cell>`): H0 9 cells (initial history), D1/D2/D3 3 cells each
  (released one batch per generation), A 6 common anchor tasks (checkpoint curve), T 15 final test tasks. No cell appears in two roles. Synthetic worlds use 6/2/2/2/4/8.
* Q, phi and f execute without reading evaluation targets: a program sees released history (full labels of released cells), the common monotherapy information of the new
  cell, and the recorded results of units it queried. Unqueried outcomes are never imputed; interpolated references are not measurements. Queried candidates keep their recorded value in
  the final shortlist ("direct-measurement replay"); the **unqueried-only** utility is reported as a separate endpoint.
* The campaign object enforces the budget and the legal probe set; a re-read of the same unit counts once.

## 3. Two contracts

* **E, end-to-end**: all pairs legal to measure; nominate 5 from the whole pool; direct confirmation allowed and counted (it is a baseline action).
* **T, transfer of abstraction**: per (cell, seed) a hash-fixed random half of the pairs is legal to probe, the other half is the nomination pool; probe and target sets are disjoint by canonical pair;
  direct confirmation of a target is impossible; a program's confirm stage is spent as additional probes.

Budgets 8 and 16 units per cell. Shortlist size 5. Seeds 0, 1, 2 (probe masks, tie-break random draws, candidate-sampling streams); the cell split is fixed.

## 4. Program language (grammar version 1)

Spec = {phi, Q, f}. phi: entries `global`, `class(a,b)` (module-pair class), `drug`, one `latent(k<=4)` block (SVD factors of released-history residuals). Q: 1-3 stages, at least one probe, rule in
{random, coverage, variance, aoptimal, witness, exploit, focus}, an optional condition (`coord`, `thr`, `else`) on the state, at most one trailing confirm. f: ridge on scope-gated state features with optional class/anchor/product
interactions, penalty lam. Limits: <= 8 state entries, complexity <= 14. Baseline-only rule `bayes_voi` and gradient-boosted f exist for comparators and are not proposer vocabulary.
Programs are fitted by simulating their own measurement plan on every released cell leave-that-cell-out (state z from probed residuals; f trained on the remaining pairs), so f is trained on the
state the program will actually see. `Fitted.to_json` stores prior statistics, coefficients, normalisation, anchor scaling, state scale, class sigmas, spec and history version; a saved program reloads and reproduces nominations and predictions (tested; gradient-boosted baselines are explicitly not serialisable programs).
Omega records scope classes, unknowns, support, counterexamples and version dependencies; it is declared, not certified.

## 5. The loop and library rules (fixed before scoring)

Per generation g = 1..3 (history H0, then + D1, + D2): (i) **diagnose** the incumbent by nested leave-one-cell-out on the released cells: decision-relevant residuals (true or predicted top-10 pairs) grouped by module class, a permutation noise floor
(95th percentile of 40 cell-label shuffles), latent share of residual variance, and the verdict `explainable` / `no_program_explains` / `direct_confirmation_dominates` (E only); (ii) **propose** <= 12 distinct valid candidates by operators informed by the diagnosis (empty if the verdict is not `explainable`), interleaving representation and procedure operators;
(iii) **predict before the query**: every candidate is run as a simulated campaign on each released cell with the held-out cell excluded from its fit, its predictions recorded before the held-out outcomes are scored; (iv) **choose** the single best candidate by paired gain; it is accepted as *provisional* only if the gain is >= delta_acc = 0.0015 and it wins on >= 60% of the decisive (non-tied) cells; (v) a provisional program is judged on the cells released *after* it was selected
and becomes *demonstrated* if its paired gain over its parent is >= 0 and it wins on at least half of them, else *retired* with the parent restored; (vi) checkpoint on the common anchor tasks.
The agent may answer "no program explains the data" (no candidate) or "direct confirmation is more valuable" (E verdict). Retirement is also recorded when later evidence contradicts a demonstrated program's Omega (documented, not automated).
Inheritance means a later generation proposes from, and is judged against, the earlier program and its measurement plan; the ablation arms below remove or freeze it.

## 6. Arms

All arms: the same history at each checkpoint, anchors, test tasks, pool, shortlist size and budget; evolving arms share the 12-candidate / 3-generation cap.

| Question | Arm | Definition (approximations named) |
|---|---|---|
| reference | zero | A_ref + pair mean + monotherapy-conditioned shift, no query |
| reference | direct (E only) | whole budget on the top predicted pairs |
| A same history | refit (P0) | base program: global + 2 latent factors, coverage probes then confirmation, ridge |
| A | gbm_multitask, latent_fingerprint, adequate_interaction, capacity_gbm | boosted-tree multitask; 3 latent factors + coverage; ridge with class/anchor/product interactions; larger boosted model |
| A | evo_repr | evolution restricted to phi/f operators, Q fixed |
| B acquisition (fixed family) | random_probe, matrix_completion_aopt, evo_proc, direct | random rows; **active matrix completion = A-optimal rows in the learned latent space**; evolution restricted to Q operators; direct confirmation |
| C full loop | evo_full vs evo_repr / evo_proc / refit (2x2: representation evolution on/off x procedure adaptation on/off), bayes_voi_joint, capacity_gbm | BATCHIE-inspired decision-weighted A-optimal approximation (not a reproduction of BATCHIE) |
| D inheritance | evo_noinherit (raw history kept, learned programs deleted each generation), frozen_library (generation-1 program, parameters fitted on generation-1 history, never updated), parameter_only (generation-1 structure refit on all history), transplant_repr_into_gbm, evolved_Q_on_base_repr, evolved_repr_on_base_Q, hindsight_superset_DIAGNOSTIC | hindsight selects the best ever-generated candidate on the test tasks and is **not a method** |

## 7. Endpoints, headroom and the useful-gain criterion

Primary endpoint: absolute shortlist utility (mean recorded A of the 5 nominated pairs, macro-averaged over test cells) at a fixed budget, contract and pool, for the contrast **evo_full - refit**. Secondary: the same with each comparator, the unqueried-only utility, anchor checkpoint curves, regret to the oracle shortlist.
Statistics are **paired task-level descriptive effects** (mean, median, min/max, wins/losses/ties over test cells after averaging seeds within cell). No confidence interval is claimed: cells are not an i.i.d. sample from a stated population, seeds are not independent of cells, and the earlier unique()-bootstrap is not reused.
**Source-side headroom** (`DEV_HEADROOM.json`, computed on H0 only, nested leave-one-cell-out, before any later cell was scored): oracle minus the best baseline. The useful-gain criterion is **25% of that headroom** at the condition (0.005 is not reused);
if the headroom is below 0.005 there is no remaining decision opportunity and effectiveness claims for that contract/budget stop (the condition is still run and reported descriptively).
Measured: E, B=8 headroom 0.0047 and B=16 headroom 0.0015 (direct confirmation of the top predicted pairs already nearly reaches the oracle) -> **no decision opportunity beyond direct confirmation**; T, B=8 0.0233 and B=16 0.0258 -> primary condition **T, B=16**, delta_use = 0.00645.
Label rule for a condition with opportunity: SUPPORTED_DEV if mean(evo_full - refit) >= delta_use and wins >= 60% of cells and the matched anchor-only control gain is < half of it; NOT_SUPPORTED if the mean is < delta_use/2; ANCHOR_CONFOUNDED if the control keeps >= half; else INCONCLUSIVE.
Shared-anchor control (`oneil_anchor_only`): the same cells, references and monotherapy information, with each cell's additive drug effects kept and the remaining pair-specific residual permuted across pairs within the cell. A procedure that gains here is using shared-anchor structure, not a combination-specific relationship.

## 8. Controls and execution limits

Synthetic worlds (software/method controls, not biology), three fixed instances each, both contracts, both budgets: `null_anchor` (shared drug-cell effects only), `low_rank` (ordinary-learnable rank-2 cell factors), `compositional` (hidden binary gates on three module classes, a conjunction effect on a fourth, nuisance variation and noise).
Ceilings: <= 3 generations after the initial version, <= 12 new candidates per generation, 3 seeds, 120 minutes of comparative compute (measured; if exceeded, the primary condition runs first and only tasks completed by all arms are compared; limits are not raised after seeing scores).
One documented repair cycle is permitted for software defects; failed or superseded runs are preserved. Disclosed history: (1) a first headroom diagnostic on the nine H0 cells; (2) a first synthetic pass (`SYNTHETIC_RESULTS_PRELIM_V0.json`) after which the synthetic worlds were not changed
but two method defects were repaired once: tied cells were counted as non-wins in the acceptance rule, and operator order truncated the 12-candidate cap toward one family. The headroom file was recomputed with final code and was identical.

## 9. Secondary API arm (after the deterministic prototype works)

`evo_api`: at each generation one request to the maintained DeepSeek flash client proposes a typed program from visible evidence only (opaque class ids K0.., numeric diagnosis, incumbent program, grammar); validation before execution; same acceptance rule and cap (one candidate).
Limits: 6 HTTP attempts, 30,000 cumulative tokens, 1,500 output tokens per request; no credentials persisted; failure or an invalid reply yields no candidate and never blocks the offline experiment. Prices were not verified: no monetary figure is reported.

## 10. Decisions to be reported separately

(1) executable prototype and boundary tests; (2) same-history representation gain (A); (3) equal-budget acquisition gain (B); (4) transfer and retention of procedures and the inheritance ablations (D); (5) bounded multi-generation growth (C and the anchor curve); (6) independent confirmation (not available here; at most one external source or prospective design is named).

## 11. Commands

```
python research/self_improving_virtual_cell_20261020/svc_integrity.py > INTEGRITY_BEFORE.json          # before
python research/self_improving_virtual_cell_20261020/svc_run.py synthetic | headroom | freeze | real
python research/self_improving_virtual_cell_20261020/svc_post.py api | programs | summary
python research/self_improving_virtual_cell_20261020/svc_integrity.py > INTEGRITY_AFTER.json          # after
python research/self_improving_virtual_cell_20261020/svc_verify.py                                    # read-only
pytest tests/test_self_improving_virtual_cell.py
```
