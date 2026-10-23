# Report: typed experimental/state programs that are tested, nominated, inherited and retired

Executed 2026-10-20 under [PROTOCOL.md](PROTOCOL.md) (hashes in `FREEZE.json`). Bounded development prototype on exposed internal data
(O'Neil 2016 pair-by-cell grids, S pairs + the 60 acquired C panel pairs). A hidden partition is not independent confirmation; passing
software tests is not scientific validation. The object tested is a *procedure* — what to measure, how to turn it into a state, how the
state changes a prediction — not a molecular mechanism, and "state" means only an experimentally grounded response summary for this
intervention set, dose regime (4x4 grid endpoint A) and cell panel.

## Decision

The prototype is executable and its boundaries hold. **No self-improvement claim about effectiveness is supported on the real data.**

| Claim | Decision | Evidence |
|---|---|---|
| 1. Executable prototype and boundary tests | **SUPPORTED (software)** | typed grammar, leave-one-cell-out program fitting, serialisation that reloads and reproduces nominations/predictions, ledgered campaigns; 27 focused tests pass; verifier OK |
| 2. Same-history representation gain (A) | **NOT_SUPPORTED** (real); control-only positive | real T B16 evo_repr - refit -0.0009 (0 wins / 5 losses / 10 ties of 15 cells); compositional synthetic +0.0073 (7/0) |
| 3. Equal-budget acquisition gain (B) | **NO_DECISION_OPPORTUNITY** (E) / **NOT_SUPPORTED** (T) | E: headroom after direct confirmation 0.0047 (B=8) and 0.0015 (B=16) < 0.005; T: evo_proc - refit -0.0002, A-optimal rows - refit -0.0007 |
| 4. Transfer and retention of procedures; inheritance (D) | **NOT_SUPPORTED** | real T B16 evo_full - evo_noinherit -0.0009; frozen / parameter-only / transplant arms within +-0.003; synthetic evo_full - evo_noinherit +0.0015 (2 wins / 3 losses) |
| 5. Bounded multi-generation growth (C) | **NOT_SUPPORTED** (real primary), **PARTIAL in the compositional control** | real primary evo_full - refit -0.0009 vs delta_use 0.00645 -> NOT_SUPPORTED; compositional control +0.009 (7/1) but below the conventional A-optimal and BATCHIE-inspired baselines (-0.005, -0.006) |
| 6. Independent confirmation | **NOT AVAILABLE** | all quantities retrospective on exposed data |

Primary condition (fixed from H0 headroom before scoring): contract T (transfer, probe/target halves disjoint by canonical pair), budget 16 units,
headroom 0.0258, useful-gain criterion delta_use = 0.00645 (25% of headroom; 0.005 not reused). Measured: **evo_full - refit = -0.0009**
(mean over 15 test cells; 0 wins, 5 losses, 10 ties; median 0). The matched anchor-only control moves 0.0000. Label: **NOT_SUPPORTED**.
In the end-to-end contract E the nominal gain over the refit is +0.0045 (B=8; 11 wins / 1 loss / 3 ties) and +0.0014 (B=16), but there is
no decision opportunity beyond direct confirmation (direct 0.7783 vs evo_full 0.7775 at B=8; direct 0.7829 vs 0.7817 at B=16), the
anchor-only control also gains +0.0035 at B=8, and the accepted program only moved budget from probing to confirmation (`frac_less_probe`): a rediscovery of direct confirmation, not a transferable witness.

## 1. Clarification of the closed prior study (additive; its artifacts were not edited)

Checked against its code and stored outputs (`research/functional_rule_revision_20261020/`):

1. The pair bootstrap draws `subset = np.unique(rng.integers(0, n_pairs, n_pairs))` (`evaluation.py:68`); taking unique pairs removes multiplicity, so it is not the standard pair bootstrap and its interval does not support "a useful gain at the registered margin is excluded". The honest reading of that study is: the point estimates were about zero (-0.0005) and the interval is descriptive only.
2. The "full dictionary" comparator is a ridge with all 16 candidate edits switched on, not sparse structure learning or a search over structures.
3. Saved coefficient summaries (`study.py:334`, `_components`) keep means/SDs of cell, drug and theta coefficients, so a fitted model cannot be reconstructed from the stored record. This study serialises full coefficients, normalisation and identity maps.
4. Headroom (0.0076 after the refit) and the minimum detectable effect describe the room for a decision gain; they do not identify why the revision failed (saturation, editor, noise or edit family cannot be separated). This study therefore reports headroom per condition and stops effectiveness claims where it is below 0.005.

## 2. Novelty boundary

Reading depth is stated honestly: the bioRxiv full text of BATCHIE was read (Methods/Results); every other source was checked only at **abstract level** through its arXiv/publisher page in this session (a 403 or paywall prevented anything more for Active Feature-Value Acquisition and the Nature Communications version of BATCHIE). Statements about method details beyond the abstracts below come from general background knowledge and are **unchecked**.

| Source | Checked | What it does (as seen) | Relation to this work |
|---|---|---|---|
| BATCHIE (Tosh et al.; bioRxiv 2023 full text; Nature Comms 2025 not opened) | full text of the preprint | hierarchical Bayesian tensor factorisation (cell embeddings, drug-dose embeddings, interaction embeddings); first batch from a design-of-experiments cover; later batches by simulating posterior outcomes and choosing a submodular batch that reduces posterior uncertainty (the repo lists a `gaussian_dbal` scorer); prospective screen: 206 drugs, 2 doses, 4 dose combinations, adaptively sampled (about 4% of ~1.4M experiments) | closest acquisition comparator. It learns *which experiments* inform one fixed model; our `bayes_voi_joint` arm is a **BATCHIE-inspired decision-weighted A-optimal approximation, not a reproduction**. Its screen is adaptively sampled, so unmeasured actions are not known outcomes: not a complete replay matrix |
| VCLMU (arXiv 2610.04475) | abstract only | latent mechanism units, reusable identity + observation-specific state, two-stage pretraining, genetic perturbations as actions | a state-representation comparator (fingerprint/latent-state side); no acquisition or program learning in the abstract. Our `latent_fingerprint` arm is a generic SVD-latent stand-in, not VCLMU |
| DreamCoder | abstract only | wake-sleep, library of learned symbolic abstractions, neural guidance of program search | closest to "library growth by abstraction"; no measurement choice and no real-world acquisition cost |
| POET | abstract only | co-evolves environments and agents, transfers stepping stones between environments | motivates inheritance across tasks and the shared-anchor control; no experimental measurement |
| Darwin Godel Machine | abstract only | archive of self-modified coding agents, empirical validation on benchmarks | the library/archive and empirical-acceptance pattern; self-modification target is code, evaluated on a fixed benchmark |
| AlphaEvolve | abstract only | LLM-proposed code changes scored by automated evaluators in an evolutionary loop | the proposer/evaluator loop; evaluators are cheap and re-runnable, unlike a wet measurement |
| Open-endedness position paper | abstract only | defines open-endedness via novelty and learnability | framing only; no method comparator |
| BioDiscoveryAgent | abstract only | LLM designs perturbation experiments with literature/code/critic tools; no trained model or acquisition function | agentic experiment choice; no typed executable state or retention rule |
| AI co-scientist | abstract only | generate / critique / tournament-evolve hypotheses; in vitro validation on AML combinations | hypothesis evolution; no measured-witness refinement of a response abstraction |
| Active Feature-Value Acquisition | bibliographic only (publisher page blocked) | *unchecked*: sequential acquisition of feature values by expected utility | the general principle behind probe choice; decision-weighted rules in `programs.choose` are of this family |

Also relevant, unchecked in this session: active matrix completion (A-optimal / uncertainty row selection — implemented here as `matrix_completion_aopt`), meta-learning of a shared initialisation, CEGAR (counterexample-guided abstraction refinement — our diagnosis step finds decision-relevant counterexamples and refines the state), and program-learning/library-learning systems.

**Difference from "functional fingerprint + adaptive predictor".** A fingerprint plus predictor is `latent_fingerprint` / `gbm_multitask` / `adequate_interaction`: a fixed coordinate system, a fixed probe rule, a predictor that adapts its parameters. The claimed extra element is the *measured, transferable witness*: a counterexample from released backgrounds that jointly changes **when** another measurement is needed (conditional Q), **what** it measures (witness/focus rules), **how** the state is represented (new class coordinate, interaction), and **where** a shared prediction rule may still apply (Omega, scope). In this implementation that element is *expressible* (grammar, `cond_focus`, `add_class`, scope-gated features) and its inheritance is testable, but **the real-data results provide no evidence that it adds anything over the conventional comparators**. If the claim were strengthened it would be subsumed by A-optimal matrix completion plus a class-aware predictor; the contribution as it stands is a domain adaptation and a benchmark/control harness (typed programs, matched anchor-only control, two contracts, attribution arms), not a demonstrated algorithmic gain.

## 3. Method (what was built)

`svc_world.py`: retrospective environment with a hidden truth, released-history objects, a ledgered `Campaign` (budget, legal probe set, re-reads count once), realized-utility evaluator, allowlisted export, three synthetic worlds and the anchor-only control. `svc_programs.py`: the typed program language, validation/canonical form, simulation-based fitting (state z from probed residuals, f trained on the remaining pairs of each released cell), execution on a campaign, full JSON serialisation. `svc_evolution.py`: contracts, diagnosis (decision-relevant residuals by module class vs a permutation noise floor, latent share, verdict incl. "no program explains" and "direct confirmation dominates"), representation/procedure operators, the generational library with provisional/demonstrated/retired status. `svc_study.py`: the arm runner. `svc_llm.py`: the bounded API proposer. `svc_verify.py`: the read-only verifier.

Library rules, fixed in advance: accept when paired gain >= 0.0015 and wins >= 60% of decisive cells; judge a provisional program on cells released afterwards; demonstrate if gain >= 0 and wins >= half; else retire and restore the parent. **Weakness found:** under this rule a program with zero change (ties) can be "demonstrated" (e.g. real T B16 seed 0: `evo_full-p02` validated with gain 0.0, 0 wins of 3 cells). Status labels in the library files therefore mean "not contradicted", not "shown useful".

## 4. Worked example (`WORKED_EXAMPLE.json`; real data, contract T, budget 16, seed 0)

Two test backgrounds taken in the fixed split order (no outcome-based selection), two competing programs: `refit` (global + 2 latent factors, coverage probes) and `evo_full-p02` (same state, f with class interaction; accepted at generation 2, demonstrated with a tie).
Predictions recorded **before** any probe: shortlist of 5 and predicted utility from the history-only prior (identical for both programs).

* **RPMI7951.** Prior shortlist (all Gemcitabine pairs: MK-8776, AZD1775, BEZ-235, Dasatinib, Dinaciclib), predicted utility 0.969. After 16 coverage probes the state is z = (global 0.019, latent1 0.565, latent2 -0.235): a modest global shift and a positive first latent factor. `refit` keeps the same five and raises the predicted utility to 0.985; `evo_full-p02` (class interaction) swaps Dinaciclib+Gemcitabine for Gemcitabine+MK-2206 and predicts 0.976. Recorded utility: 0.9404 (prior and `refit`) vs 0.9342 (`evo_full-p02`) — the changed recommendation was slightly worse and both programs over-predicted by about 0.04.
* **LNCAP.** Prior shortlist (BEZ-235+Sorafenib, Dinaciclib+Doxorubicin, Bortezomib+Sorafenib, BEZ-235+MK-2206, Doxorubicin+MK-2206), predicted 0.776. The probes give z = (-0.035, -0.646, -0.860): this background responds less than the prior implies. Both programs lower the predicted utility (0.742 `refit`, 0.752 `evo_full-p02`) and keep the same set (the second program reorders it); recorded utility 0.7901 for both, i.e. the probes correctly said "lower" about the *level* but the ranking decision did not change and the level was in fact higher than predicted.

How the two outcomes change representation and recommendation: a positive latent-1 state moves score toward pairs with large latent-1 loading, a negative state away from them; the class interaction rescales that shift per module class, which is the only way `evo_full-p02` can disagree with `refit`. What remains unknown: whether any probe-derived coordinate predicts *pair-specific* differences among the top pairs (the example shows level shifts, not reliable reordering), what happens at other doses/times, and whether the over-prediction is a calibration issue of the state or noise in the endpoint.

## 5. Results

**Compute.** Real pilot 731 s, synthetic controls 543 s (+510 s superseded preliminary pass, preserved), headroom ~1 min, API arm ~10 s: well inside 120 minutes. No condition was skipped. Ceilings respected (3 generations, 12 candidates, 3 seeds, 6 HTTP attempts, 30,000 tokens).

**Source-side headroom (H0 only; `DEV_HEADROOM.json`).** Oracle 0.816 (E) / 0.805 (T). E: best baseline is direct confirmation (0.8115 at B=8, 0.8146 at B=16), headroom 0.0047 / 0.0015 -> no decision opportunity for any program beyond directly confirming the top predicted pairs. T: every baseline sits at the zero-probe level (0.778-0.782), headroom 0.0233 / 0.0258. This already says that on real data the probe-derived state has not been shown to carry transferable information.

**Real pilot, contract T (primary).** All of zero, refit, A-optimal rows, BATCHIE-inspired VOI, latent fingerprint, boosted trees and evolved programs are within 0.004 of each other and of the zero-probe prior (test means: zero 0.7592, refit 0.7592, evo_full 0.7583, matrix_completion_aopt 0.7585, bayes_voi_joint 0.7581, oracle 0.7706). Of 72 diagnoses in T, 45 returned `no_program_explains` (the deterministic loop proposes nothing then); 27 were `explainable` and produced up to 12 candidates each; the four evolving arms accepted 14 candidates across the three seeds at B=8 and 4 at B=16, none useful on test. Anchor checkpoint curves of evolved and refit arms are indistinguishable (evo_full 0.8275 / 0.8290 / 0.8298 / 0.8285 vs refit 0.8275 / 0.8290 / 0.8295 / 0.8279). Paired descriptive effects (mean over 15 cells, wins / losses / ties):

| Contrast (T, B=16) | mean | W / L / T |
|---|---|---|
| A: evo_repr - refit | -0.0009 | 0 / 5 / 10 |
| A: evo_repr - gbm_multitask | +0.0025 | 4 / 9 / 2 |
| A: capacity_gbm - refit | -0.0044 | 7 / 6 / 2 |
| B: evo_proc - refit | -0.0002 | 0 / 1 / 14 |
| B: evo_proc - matrix_completion_aopt | +0.0005 | 4 / 4 / 7 |
| C: evo_full - refit (primary) | **-0.0009** | 0 / 5 / 10 |
| C: evo_full - bayes_voi_joint | +0.0002 | 3 / 5 / 7 |
| C: interaction (full-proc)-(repr-refit) | +0.0002 | 1 / 0 / 14 |
| D: evo_full - evo_noinherit | -0.0009 | 0 / 5 / 10 |
| D: evo_full - frozen_library | +0.0003 | 7 / 4 / 4 |
| D: evo_full - parameter_only | -0.0009 | 0 / 5 / 10 |
| D: hindsight superset (diagnostic) - evo_full | +0.0012 | 7 / 0 / 8 |

B=8 is the same picture (evo_full - refit -0.0003, 0/1/14). Matched anchor-only control (T): all evolved arms equal the refit exactly (no gain from shared-anchor structure either).

**Real pilot, contract E (no decision opportunity beyond direct confirmation).** B=8: evo_full 0.7775 vs refit 0.7730 (+0.0045, 11/1/3), evo_proc identical, evo_repr no change; direct 0.7783; the gain comes from `frac_less_probe` (25% probe / 75% confirm), accepted at generation 1 and validated (seed 0: +0.0080 on the next batch, 2 of 3 cells); the anchor-only control shows +0.0035 (it is not combination-specific), and the no-inheritance arm ended with the base program in all three seeds (evo_full - evo_noinherit +0.0045). B=16: +0.0014 (6/0/9), also below direct confirmation (-0.0012). Reported descriptively; no effectiveness claim.

**Synthetic controls (software/method controls; not biological evidence).** 3 instances x 2 contracts x 2 budgets:
* `null_anchor` (shared-anchor effects only): evolved arms equal the refit in T (0.0000) and move <= +0.0007 in E; no false win. Loop declines most generations.
* `low_rank` (ordinary-learnable): evo_full - refit within +-0.0012 everywhere; ordinary latent baselines are as good.
* `compositional` (gates, conjunction, nuisance): evo_full - refit +0.0091 (T B16; 7/1), +0.0079 (T B8; 6/1), +0.0065 (E B16; 7/1). Representation evolution carries most of the gain in T (evo_repr - refit +0.0073, 7/0) and procedure adaptation in E (evo_proc - refit +0.0065); the 2x2 shows representation and procedure effects are not additive. Conventional baselines are stronger: A-optimal matrix completion and the BATCHIE-inspired rule beat evo_full by 0.005-0.006 (T B16), and direct confirmation by 0.0025 (E B16). Inheritance: evo_full - evo_noinherit +0.0015 (2 wins / 3 losses) and +0.0023 at B=8 (3/2): not distinguishable. evo_full beats the frozen library by +0.0099 (7/1): refitting parameters on the grown history matters more than a frozen structure. An ad hoc check (not stored in the results files) with a hand-specified oracle program (true target classes + witness probes, valid in the grammar) beat the refit by +0.004 to +0.008 at B=8 and by about +0.001 at B=16, so even the expressible solution has little headroom at these budgets.

**Repair cycle (one, documented).** The first synthetic pass (`SYNTHETIC_RESULTS_PRELIM_V0.json`) accepted almost nothing; two defects were visible in the code, not in the scores: tied cells counted as non-wins in the acceptance rule, and the 12-candidate cap truncated the interleaved operator list toward representation operators. Both were fixed once, the synthetic controls rerun on the final code, and the real data were scored only afterwards. The synthetic worlds were retuned once before that (monotherapy spread reduced so that combination effects matter for ranking), on a single instance, before any comparative run.

**API arm (`API_RESULTS.json`, primary condition, seed 0, one run).** deepseek-flash, 3 requests / 3 HTTP attempts / 3,046 tokens (limits 6 / 30,000), latency 0.9-1.3 s. Visible evidence: opaque class ids and the numeric diagnosis only. Generation 1: `none` (cited all five evidence ids; "all scores below the noise floor"); generation 2: proposed adding class K0 plus a class interaction — valid, executed, dev gain +0.0031, 4 wins / 3 losses -> rejected by the registered rule (57% < 60%); generation 3: `none`. The final program equals the refit; paired test effect vs refit exactly 0 over 15 cells. Prices were not verified: no money figure. The model's refusals matched the deterministic diagnosis, which is evidence that the interface works, not that LLM proposal adds value.

**Serialisation.** Final programs of four evolving arms were fitted (contract E, budget 16, all released history), written to `PROGRAMS/fitted_*.json` with `library_*.json` lineage files (ancestry, status, evidence, Omega), reloaded and re-executed: nominations and predictions identical (`SERIALIZATION_RECEIPT.json`). Gradient-boosted comparators are explicitly not serialisable programs.

## 6. Failed or unsupported hypotheses

* That probe-derived state helps unprobed targets on real data under the transfer contract: no baseline or evolved arm exceeds the zero-probe prior (T B16 range 0.7548-0.7592 vs 0.7592).
* That procedure adaptation beats conventional acquisition at equal budget: no (A-optimal rows and random rows are indistinguishable from coverage; end-to-end the winner is simply more confirmation, i.e. direct confirmation).
* That inheritance matters: the no-inheritance arm equals or ties the inherited arm in every real condition; synthetic differences are 2-3 cells either way.
* That library status is informative: the "demonstrated" rule accepts ties; it needs a strict-improvement criterion before status can mean anything.
* That the headline E gain is a transferable witness: the anchor-only control shows +0.0035 and the accepted edit is a budget reallocation toward direct confirmation.

## 7. What remains untested

Whether a task with larger decision headroom (more candidate pairs per cell, wider response heterogeneity, or a measured grid richer than a single endpoint) shows a probe-state gain; real acquisition costs (no wells/cultures/money statement is made); other doses/times; independent confirmation. Evidence limits: 15 test cells (fixed from metadata), 3 seeds that share them, exposed data, cells not a sampled population (no confidence interval is claimed), one home-built approximation each of matrix completion and BATCHIE, a 4-module drug grouping derived from monotherapy profiles, ridge/boosted-tree learners only, one API run.

## 8. Later stage (one design, named before looking at any further data)

A prospective **complete-replay** design rather than another retrospective release: choose roughly 15 new cell backgrounds and a small fixed drug set (for example 10 drugs = 45 pair grids), measure every pair grid in every background once, pre-register the probe/target split, shortlist size and the 25%-of-headroom criterion computed from this study's H0 data, and score the transfer contract on targets that were never used for design. BATCHIE's public screen is *not* qualified: it is adaptively sampled (about 4% of the space), uses 2 doses and 4 dose combinations rather than a full grid, and its unmeasured actions are not known outcomes; qualifying it would first need its observed-matrix coverage per cell line.

## 9. Reproduction

```
python research/self_improving_virtual_cell_20261020/svc_run.py synthetic | headroom | freeze | real
python research/self_improving_virtual_cell_20261020/svc_post.py api | programs | example | summary
python research/self_improving_virtual_cell_20261020/svc_verify.py
pytest tests/test_self_improving_virtual_cell.py
```
Integrity: `INTEGRITY_BEFORE.json` equals `INTEGRITY_AFTER.json` (prior package hashes, S file hash, stat-only C/G/F, vault state, metadata cache). G, F and the 27 non-acquired C pairs were never opened; the raw workbook was not reparsed; the prior study's stages and vault were not re-run. The verifier fits nothing, calls no API and opens no outcome.
