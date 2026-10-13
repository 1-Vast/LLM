# Selective phenotypic hit triage and Scientific Decision Review (2026-10-13)

**Status: FROZEN, run once. One post-opening correction is disclosed.**

- **Pre-registration.** The study was pre-registered in [PROTOCOL.md](PROTOCOL.md) and frozen in [FREEZE.json](FREEZE.json) (32 files) before any test outcome was read. The test choices were locked by digest in [CHOICES_LOCK.json](CHOICES_LOCK.json), and the sealed CTRP v2 outcomes were opened once.
- **Claim level:** retrospective independent-platform confirmation on a sealed compound split. It is not independent confirmation and not prospective discovery (PROTOCOL §1).
- **Correction after opening.** The frozen outcome reader dropped half of the registered endpoint on the test split. The registered-endpoint results are in [TEST_RESULTS_REGISTERED.json](TEST_RESULTS_REGISTERED.json). The as-run file, [TEST_RESULTS.json](TEST_RESULTS.json), is kept but excluded from every claim ([DEVIATIONS.json](DEVIATIONS.json)).
- **Promoted:** three engineering contracts with no fitted model or scientific rule: `maestro.decision_review`, `maestro.claim_audit` and `maestro.hit_triage`. **Not promoted:** MAESTRO_LOOP, the review vetoes, line memory, and any agent role.
- **Costs:**
  - this study: 0 wells, 0 provider calls ($0), 0 downloads;
  - LLM arms (`agent_arms.py`, `agent_review.py`): NOT_RUN, awaiting authorisation (≈ 0.47 USD with deepseek-flash).
- **Audit.** Every result number below carries a claim tag such as [C01]. Design parameters, literature figures and the diagnostics in DEVIATIONS.json are not results and carry none. `verify.py` checks every tag against [RUNS.json](RUNS.json), a manifest of 22 runs: 14 succeeded, 5 negative, 2 failed and 1 excluded.

## Answer in brief

**The success criterion is not met.** The brief asks that MAESTRO find or validate more useful candidates, at equal or lower cost, than *strong non-agentic workflows*.

1. **MAESTRO beats the strongest deterministic rule.**
   - P1 is CONFIRMED: context-aware triage −(z_r + ctx)/√2 found 22 validated selective hits in 128 confirmation curves, against 12 for the two-way residual z [C01–C03].
   - The difference is +10 [+4, +18], one-sided p 0.004 [C04, C45, C46].
   - P1 holds with mechanism-family clusters [C05] and without the 38 test compounds that share a target gene with development [C06, C51].
2. **The closed loop is not confirmed.**
   - P2 is NOT_CONFIRMED: MAESTRO_LOOP found 23 hits, CONV_LOOP 18, with 32 secondaries each (+5, p 0.18) [C07–C09]. Its frontier acquisition had been chosen because it led on development (76 hits) [C38].
   - The factorial shows where the gain comes from. The context score is worth +9 (MAESTRO_top − CONV_LOOP) [C24]. The decision-aware *frontier* acquisition lost 4 hits against simply buying the top compounds [C25].
3. **A strong learner beats the engine at lower cost.** This comparison is post hoc.
   - A gradient-boosted classifier on screen and context features (ML+context, fitted on development) found 38 hits and bought **no** secondary [C21].
   - MAESTRO_LOOP found 23 with 32 secondaries [C22]: a difference of +15, p 0.004 [C29, C30].
   - The all-evidence learner VC was +9 (p 0.085) [C31].
   - The success criterion fails against this comparator. Because the comparison was not registered, the reverse claim ("the learner is better") is not confirmed either.
4. **Why development pointed the wrong way.**
   - One mechanism family holds 82% of development's screen-selective validated pairs [C32]. It is a chained MoA component of 56 compounds, mostly kinase inhibitors, and the family split placed all of it in development [C52].
   - On development, the screen-selective pairs (z_r ≤ −3) validated 30% of the time. On test they validated 9% [C33, C34].
   - D3 therefore beat the out-of-fold learner on development (59 vs 32) [C36, C37]. That is why D3 became the designated comparator and why a hand-built score was preferred.
   - On the test split, compound-specific screen signal transfers weakly. Line-level priors carry the hits: context, learned line effects, and line memory (+10, exploratory) [C23, C47].
5. **Scientific Decision Review changed decision validity, not yield.**
   - Admitting virtual-cell predictions as if they were measured replicates caused 15 false NO-GOs, against 3 with measured evidence only (R2 CONFIRMED) [C14–C16].
   - Prediction-based vetoes hit confirmable compounds 13 times in 29: no better than chance [C17].
   - Measured-evidence vetoes were confirmable 3 times in 23, against 15 of 42 left as NEED_MORE_EVIDENCE. R1 is NOT_CONFIRMED (Fisher p 0.045 against α 0.025) [C10–C13].
   - Decision-aware acquisition added 1 hit [C18]; the full review lost 1 [C19]. The LLM debate arm was not run.
6. **Claim verification worked on what it checks.**
   - Every evidence value stored in the review arms' decision records re-derives from the frozen features: 0 unsupported, including the 543 checked for SDR_veto at b = 1 [C20, C50].
   - The audit catches an inflated claim and an omitted negative run (see Verification).
   - It did **not** catch the endpoint error: a log-and-artifact audit checks the report against the artifacts, not whether an artifact was computed correctly. A sanity check found it: as run (excluded), every test compound read as pan-active, against 77 of 125 on development [C53].

## Scientific Decision Review: what Co-Scientist supports and what it does not

The two source papers are Gottweis et al. (*Nature* 2026; read from the Europe PMC full text) and the real-world extension (arXiv:2608.26701). Only principles with measured support were adopted. Tournament ranking was bounded to ordering exploration.

| Principle | Evidence in the papers (literature, not audited here) | In MAESTRO | Measured here |
|---|---|---|---|
| Deterministic claim verification against execution records | Largest controlled effect in the extension: severe result hallucination 4% with the reliability modules, 46% ablated, 90% baseline (50 outputs per arm, expert-rated). Idea quality unchanged. | **Adopted.** `maestro.claim_audit` (claims vs run manifest, negatives must be cited); S14 record audit | 0 unsupported record values [C20]; audit controls pass. It missed an artifact computed wrongly (above). |
| Evidence-grounded criticism | Reviews in both systems cite sources; no isolated ablation | **Adopted as an admission rule.** `decision_review.admit` accepts only qualified measurements or derived analyses in the same assay context. Predictions, annotations and LLM output are context. | R2 CONFIRMED: unverified prediction evidence → 15 vs 3 false NO-GOs [C14–C16] |
| Competing falsifiable explanations and discriminating experiments | Generation and debate are central; their isolated decision value is not reported | **Adopted deterministically.** Three explanations (SELECTIVE / NOISE / GENERIC) and `discriminating_experiments` | Direction right (vetoed 3/23 vs 15/42 confirmable), R1 not significant [C10–C13] |
| Tournament / Elo ranking | Self-evaluated. Agreement with ground truth was measured only on a proxy QA benchmark (GPQA AUC about 0.64-0.65), never on experimental outcomes. Extension: TrueSkill + UCB settings are design defaults, not ablated | **Bounded.** `exploration_tournament` returns an `ExplorationRanking` that refuses use as a probability or as evidence (`RANKING_NOT_PROBABILITY`) | Debate arm NOT_RUN (paid) |
| Evolution, meta-review, search grounding | Small proxy-benchmark gains: GPQA AUC +0.005 to +0.008; evolution precision +4.5 points | **Not adopted.** No decision-level ablation exists. | — |
| Bayesian / uncertainty-driven exploration | UCB parent selection as a default, not ablated | Tested as acquisition | Uncertainty acquisition +5 over MAESTRO_LOOP, n.s. (S11) [C54] |
| Expert oversight | Every wet-lab validation in both papers was expert-curated. In AML, 3 of 5 tested repurposing candidates were active. | **Adopted.** `authorize_execution` refuses any experiment without a human approval bound to the request digest and within budget | No experiment executed |

## Strategy and resource assessment

The brief names five capabilities, A–E. Each status below is what this study's evidence supports.

| Capability | Priority before | Evidence now | Priority next |
|---|---|---|---|
| A. Mechanism-aware phenotypic hit prioritisation | 1 | Context beats deterministic screen statistics (P1). A learned line-and-context model beats the hand-built engine (post hoc). Generic toxicity is separable: pan-active nominations are reported per arm. | 1: learned triage model, registered against the engine |
| E. Persistent learning from positive and negative outcomes | 4 | Line-reliability memory gave +10 on test (exploratory) [C23] but +2 on development [C41]. Fitting on all development is itself learning from outcomes, and it dominated. | 2: prospective test of outcome-fed line priors |
| B. Evidence-grounded hypothesis reasoning | 2 | Measured-only evidence admission prevents false NO-GOs (R2). Explanations and vetoes do not add hits. LLM generation not yet tested (NOT_RUN). | 3: run the authorised debate ablation, judged on decisions only |
| C. Cost-aware closed-loop experimentation | 3 | P2 not confirmed. Frontier acquisition hurt [C25]. Buying all 98 secondaries added 8 hits [C49], so the same-platform follow-up carries little decision value beyond context. | 4: only with an orthogonal follow-up assay |
| D. Multi-objective developability | 5 | `NOT_MEASURED` locally; no decision-level data | 5: constraint flags with applicability refusals, never a probability of success |

| Resource | What it offers | Endpoint | Fit and limits for this programme |
|---|---|---|---|
| PRISM 19Q4 (DepMap) | Pooled barcoded viability, about 4,500 compounds, about 500 lines | log2 fold change, 2.5 µM, 5 d; secondary 8-dose | **Used:** the primary screen and the bought follow-up. Exposed in earlier MAESTRO blocks, so input only. |
| CTRP v2 | Arrayed CellTiter-Glo, 16 doses, 72 h | AUC, top-dose viability | **Used:** the sealed confirmation platform. Same institution, but a different assay and different runs. It predates PRISM, so the study is retrospective. |
| DepMap / CCLE | Line expression, mutation, CRISPR dependency | Molecular context | **Used:** context and mechanism features. Dependency is a mechanism prior, not engagement. |
| Repurposing Hub | Identity, MoA, targets, phase, SMILES | Annotation | **Used:** identity, mechanism families and the split. Annotation-relative only. |
| ChEMBL | Curated bioactivity (IC50/Ki) with assay provenance | Potency, selectivity across targets | Next: target-engagement priors and selectivity panels for capability D. Assay heterogeneity requires context binding. |
| PubChem BioAssay | HTS results including counter-screens and promiscuity assays | Active/inactive calls | Next: assay-interference and frequent-hitter flags (capability A). Calls are assay-specific and noisy. |
| JUMP Cell Painting | Morphological profiles for about 116k compounds | Image features | Next: orthogonal phenotype for nonspecific-signature detection. It is not a viability endpoint. |
| Open Targets | Target–disease association with genetic evidence | Association scores | Next: capability B (disease relevance, modulation direction). The scores are evidence summaries, not probabilities of efficacy. |
| Therapeutics Data Commons | Curated benchmarks (ADMET, DTI, response) | Task-specific labels | Next: developability predictors (capability D), each with applicability refusals. Leaderboard splits are not prospective. |
| Robin, Biomni, DrugAgent | LLM agent systems: hypothesis generation with expert-selected lab tests (Robin), general biomedical tool use (Biomni), drug-discovery ML programming (DrugAgent) | Case studies and benchmarks | Novelty comparison. As publicly reported, none scores agent decisions against matched-budget deterministic and learned baselines on sealed outcomes. That design is what this study contributes, and here it rejected the agentic advantage. |

Licences must be checked per release before redistribution. This folder stores only identifiers and derived features.

## Architecture and interfaces

The four layers keep MAESTRO's separation. Arrows carry typed records only, and no LLM output can overwrite a measurement, prediction or QC field.

```
Scientific Agent ──(flags with named reasons; explanations; exploration order)──▶ Decision Engine
Virtual Cell / predictive tools ──(predictions with trust; never evidence)──────▶ Decision Engine
Evidence & Memory ──(qualified measurements in an AssayContext; run manifest)───▶ Decision Engine
Decision Engine ──(GO / NO_GO / NEED_MORE_EVIDENCE + reasons, limitations, provenance)──▶ human approval ──▶ experiment
```

**`src/maestro/decision_review.py`** (promoted contract):

- `Prediction`, `Explanation`: at least two explanations, exactly one marked as progression;
- `EvidenceItem` (kind, measurement status, assay context, source digest), `admit`;
- `discriminating_experiments`: incompatible predictions from different explanations;
- `review` returns a `ReviewDecision` (status, named reasons, limitations, provenance, `decision_digest`). A NEED_MORE_EVIDENCE decision must name an experiment;
- `ExplorationRanking`, `exploration_tournament`: Swiss rounds; the ranking refuses probability use;
- `ExperimentRequest`, `Approval`, `approve`, `authorize_execution`: a human approval bound to the request digest, then `CampaignBudget.require_feasible`.

**`src/maestro/claim_audit.py`** (promoted contract):

- `RunManifest` and `RunRecord`: succeeded, negative, failed and excluded runs. Failed and excluded runs need a reason;
- `Claim`, `audit`, giving the verdicts SUPPORTED, CONTRADICTED, ARTIFACT_MISSING, ARTIFACT_MODIFIED, POINTER_MISSING, RUN_UNKNOWN, FROM_FAILED_RUN and FROM_EXCLUDED_RUN;
- report-level findings OMITTED_NEGATIVE_RUN and MANIFEST_INCOMPLETE.

**`src/maestro/hit_triage.py`** (promoted contract):

- `CompoundIdentity`: Broad core and InChIKey connectivity;
- `AssayContext` and `bind` (`CONTEXT_MISMATCH`);
- `admit_curves`: QUALIFIED, QC_FAILED or PLANNED_MISSING, never a zero;
- `TriageLedger` (`BUDGET_EXCEEDED`);
- `nominate`: capped and order-invariant;
- `OutcomeSeal.release` (`FREEZE_MISMATCH`, `CHOICES_NOT_LOCKED`, `CHOICES_MISMATCH`);
- `assert_disjoint` (`SPLIT_LEAK`).

**Research only** (this folder, not promoted):

- `review.py`: explanation features, vetoes and acquisition rules;
- `test_choose.py`: every arm;
- `agent_arms.py` and `agent_review.py`: LLM arms with a spend ledger, write-once choices and failed calls never cached.

**Tests.** 21 contract tests in `tests/test_decision_review.py`, `tests/test_claim_audit.py` and `tests/test_hit_triage_contracts.py` cover the brief's list:

| Brief item | Tested by |
|---|---|
| Compound identity | `test_compound_identity_collapses_salts_and_refuses_malformed_ids` |
| Assay-context binding | `test_measurements_are_bound_to_their_assay_context` and `test_only_qualified_real_measurements_in_the_same_context_decide` |
| Provenance | `test_decision_digest_is_stable_and_sensitive` and the claim-audit tests |
| QC admission | `test_curve_admission_is_a_named_status_never_a_zero` |
| Refusal | `test_measured_contradiction_is_a_named_no_go` and `test_a_model_prediction_can_neither_falsify_nor_progress_a_candidate` |
| Budget accounting | `test_ledger_books_curves_and_followups_against_shared_budgets` and `test_consequential_experiments_need_a_matching_human_approval_within_budget` |
| Reproducibility | `test_nomination_is_capped_and_independent_of_input_order` and `test_tournament_ranks_exploration_only_and_is_reproducible` |
| Leakage prevention | `test_outcomes_open_only_for_frozen_code_and_locked_choices` and `test_split_leak_is_refused_by_compound_structure_or_family` |

## Protocol summary (PROTOCOL.md)

- **Campaign:** triage of the PRISM 19Q4 primary screen. The unit is H(c, l): "compound c selectively reduces line l".
- **Universe:** 253 Repurposing Hub compounds matched to CTRP v2 by Broad core (220) or InChIKey connectivity (33). All 33 name differences are synonyms of structure-matched compounds [C35].
- **Split:** union-find over MoA strings gives 125 development and 128 test compounds. No test compound is a close analogue (Tanimoto ≥ 0.7) of a development compound [C42].
- **Campaigns:** 8 test campaigns of 16 compounds.
- **Budget per campaign:**
  - B = 16 confirmation curves (b = 1; also 0.5 and 2), at most 3 lines per compound;
  - K = 4 secondary dose-responses for loop arms.
- **Endpoint (VALIDATED selective hit):** CTRP AUC robust z within the compound ≤ −2, *and* top-dose viability ≤ 0.5. A missing curve is a miss. Under this endpoint, 1,076 of 54,130 evaluable test pairs validate [C27, C48], and 74 of 128 compounds are pan-active [C43].
- **Primary tests (family P):** one-sided compound sign-flip at α 0.025 each, at b = 1. P1: MAESTRO > D3. P2: MAESTRO_LOOP > CONV_LOOP.
- **Decision-review tests (family R):** α 0.025 each. R1: veto correctness (Fisher). R2: evidence verification (sign-flip).

## Results (registered endpoint, b = 1, 128 confirmation curves per arm)

| Arm | Class | Validated hits | Secondaries (budget) |
|---|---|---:|---:|
| zero (line sensitivity only) | zero arm | 9 | 0 |
| random primary hit | zero arm | 12 | 0 |
| D1 magnitude | deterministic | 7 | 0 |
| D2 within-compound z | deterministic | 12 | 0 |
| **D3 two-way residual z** | deterministic (designated) | **12** | 0 |
| D3f / D4 | deterministic | 14 / 11 | 0 |
| ML (screen features) | strong ML | 30 | 0 |
| **ML+context** | strong ML | **38** | 0 |
| ML+mechanism / ML+transcriptional | strong ML | 28 / 31 | 0 |
| VC (all evidence) | virtual cell without agent | 32 | 0 |
| VC+S | virtual cell with secondaries | 32 | 98 (recorded as 0; see DEVIATIONS) |
| **MAESTRO** −(z_r + ctx)/√2 | engine, no follow-up | **22** | 0 |
| **CONV_LOOP** | conventional two-stage | **18** | 32 |
| **MAESTRO_LOOP** | engine, closed loop | **23** | 32 |
| CONV_frontier / MAESTRO_top | factorial cells | 16 / 27 | 32 |
| CONV_ALL / MAESTRO_ALL | full-cost loop | 23 / 31 | 98 |
| LOOP_uncertain / LOOP_top | learned loop | 28 / 29 | 32 |
| SDR_veto / SDR_acquire / SDR_veto_acquire | decision review | 23 / 24 / 24 | 32 |
| SDR_unverified / SDR_full | review ablations | 21 / 23 | 32 |
| AGENT_conventional, AGENT_maestro, SDR_debate | LLM arms | NOT_RUN | — |

Every number in the table is a claim (`T-<arm>`).

**Primary family P:**

| Hypothesis | Difference | p (one-sided) | Verdict |
|---|---|---|---|
| P1: MAESTRO > D3 | +10 [+4, +18] | 0.004 | **CONFIRMED** [C01, C04, C45, C46] |
| P2: MAESTRO_LOOP > CONV_LOOP | +5 | 0.18 | **NOT_CONFIRMED** [C07–C09] |

**Decision-review family R:**

| Hypothesis | Result | Verdict |
|---|---|---|
| R1: vetoed compounds are less often confirmable | 3/23 vs 15/42, p 0.045 | **NOT_CONFIRMED** [C10–C13] |
| R2: unverified predictions cause more false NO-GOs | 15 vs 3 | **CONFIRMED** [C14–C16] |
| R3: SDR_veto hits vs MAESTRO_LOOP (descriptive; differ in 1 nomination) | 0 [C55] | non-inferior, uninformative |

**Secondaries** (descriptive):

- Line memory over no memory: +10, p 0.015 [C23, C47]. On development it was +2 [C41].
- Full follow-up: +8 hits for 66 more secondaries [C49].
- Calibration: the development calibrator expected 43.8 hits for MAESTRO_LOOP, and 23 were realised [C26]. Development-fitted probabilities do not transfer to this split.

**Negative and failed runs** (listed in RUNS.json and cited here):

- P2 [C07];
- R1 [C10];
- the strong-learner comparison [C29];
- the development review, which added no hits; its re-rank coefficient was 2.6 in one fold and about 0 elsewhere [C39, C40, C44];
- development memory [C41];
- the first design lock (refused, rebuilt before any outcome);
- the first endpoint correction, which refused on 13 pairs exactly at the viability threshold [C28] and was replaced by an exact re-read.

### The post-opening endpoint correction

`outcomes.qualified_outcomes` guessed the viability unit per split: it assumed percent when any value exceeded 2.

- **What went wrong.** The test split holds four overgrowth curves (maximum 2.66). Every test viability was therefore divided by 100, so the "top-dose viability ≤ 0.5" condition always passed.
- **Development was unaffected:** its maximum is 1.93.
- **The fix.** [`evaluate_registered.py`](evaluate_registered.py) re-reads the archive exactly, as a fraction. That is the column's unit, and development already used it. It checks every pair against the frozen reader before rescoring with the frozen code. The fix involves no free choice, but it was made after the as-run results had been seen.
- **Effect on verdicts.** As run, the P1, P2 and R2 verdicts are unchanged, and R1 was CONFIRMED. Under the registered endpoint, R1 is not confirmed. This comparison comes from the excluded run and is not audited.

## Staged roadmap

| Stage | Goal | Gate to pass before the next stage |
|---|---|---|
| 0 (done) | Typed contracts, sealed retrospective triage, claim audit | This report; contracts tested |
| 1 | Learned triage against the engine | Register ML+context vs MAESTRO_LOOP vs D3 on an untouched compound set. Promote the winner only if it is confirmed there. |
| 2 | Nonspecific-activity filters (capability A) | PubChem frequent-hitter and counter-screen flags and JUMP morphology as *named* NO-GO reasons. Each must lower false GOs at fixed curves on a sealed set. |
| 3 | Evidence-grounded hypotheses (capability B) | Authorised LLM debate and agent arms (≈ 0.47 USD) judged only by false NO-GOs, confirmable NEED_MORE_EVIDENCE and hits, never by review scores |
| 4 | Closed loop with an orthogonal follow-up (capability C) | Buy follow-up only where its expected decision change exceeds its cost, and prove it against "buy nothing" (the learner) |
| 5 | Cumulative learning (capability E) | Outcome-fed line priors, registered prospectively, with shuffled-memory controls |
| 6 | Developability constraints (capability D) | TDC/ChEMBL-based flags with applicability refusals, never an overall probability of success |

**Frozen future protocol.** PROTOCOL §11 stays as frozen: MAESTRO_LOOP against CONV_LOOP and D3 on a post-2026-10-13 compound set, with the same endpoint and the P2 test. Promotion requires P2 to be confirmed on both sets, and it was not confirmed here.

**Before the next freeze** (post hoc lessons, not frozen):

- add ML+context as a registered comparator, with the brief's success criterion as a primary contrast;
- fix the viability unit from metadata, never from the data;
- book every secondary any model reads;
- cap any one mechanism family's share of the development signal.

## Verification

```bash
cd research/selective_hit_triage_20261013
D:/anaconda/envs/maestro/python.exe verify.py
D:/anaconda/envs/maestro/python.exe verify.py --replay
```

The default run:

- checks the freeze (32 files; DEVIATIONS.json unhashed);
- recomputes and reproduces TEST_CHOICES.json and its lock;
- reproduces CLAIMS.json and RUNS.json;
- runs `maestro.claim_audit.audit`, which must give every claim SUPPORTED, no claim on the excluded run, and no omitted negative run or unlisted result file.

Two controls must also behave: an inflated claim must be CONTRADICTED, and dropping a negative run's claims must raise OMITTED_NEGATIVE_RUN. `--replay` reruns the one-shot evaluation, the registered-endpoint correction and the post hoc analysis, each of which must print REPRODUCED.
