# Selective phenotypic hit triage: pre-registered protocol

Frozen by `FREEZE.json` before any test confirmation outcome was opened. `DEVIATIONS.json` records every later change and is deliberately not hashed.

## 1. Question and claim level

The question: can a decision engine that combines screen evidence, context evidence and a budgeted dose-response follow-up nominate more **independently validated selective hits** than strong conventional triage, at the same confirmation and follow-up cost?

The claim level is a **retrospective independent-platform confirmation on a sealed compound split**:

- This is not prospective discovery. The confirmation data (CTRP v2, published 2015) predate the screen (PRISM 19Q4).
- A positive result shows that MAESTRO's triage recovers selective sensitivities that a second assay platform also measured. It does not show efficacy, target engagement, mechanism or clinical value.

The four claim levels, kept apart throughout:

| Level | Meaning | Here |
|---|---|---|
| Computational screening | a ranking with no outcome | the frozen choices (`TEST_CHOICES.json`) |
| Retrospective validation | the ranking scored against existing data that the design never saw | this study (CTRP v2 test split) |
| Independent confirmation | an untouched dataset from another source, or a new experiment | not available locally; see §11 |
| Prospective discovery | new experiments run after the choices are frozen | not run; see §11 |

## 2. Campaign

- **Context:** phenotypic oncology screen triage. The primary screen is PRISM 19Q4:
  - 4,532 compounds at 2.5 µM for 5 days, on pooled barcoded cell lines;
  - log2 fold change against vehicle.
  It has been used by earlier MAESTRO blocks and is exposed input, never confirmation.
- **Compound universe:**
  - Repurposing Hub compounds in the PRISM primary screen, matched to CTRP v2 by Broad core id (222) or by InChIKey connectivity block (42).
  - Eligible if CTRP holds at least 100 post-QC curves for the compound. That leaves 253 compounds and 506 lines with CCLE expression.
  - Eligibility was set from identifier columns only (`census.py`, `split.py`).
- **Hypothesis unit:** H(c, l), meaning "compound c selectively reduces the viability of line l". A nomination sends H(c, l) to confirmation.
- **Campaigns:** the 128 test compounds are dealt in hash order into 8 campaigns of 16. Each campaign is one triage round with its own budget.

## 3. Endpoints

Endpoint tiers are kept distinct:

| Tier | Source | Role |
|---|---|---|
| Primary activity | PRISM primary, single dose | input to every arm |
| Same-platform dose-response | PRISM secondary, 8 doses | follow-up an arm may *buy* (K per campaign) |
| Independent confirmatory dose-response | CTRP v2 (CellTiter-Glo ATP, 16 doses, 72 h, separate runs) | **the outcome** |
| Target engagement | not measured | `NOT_MEASURED`; no claim |
| Mechanism support | annotation coherence only (target mutation/expression) | descriptive (S6, evidence reliability) |
| Developability | not measured (phase and promiscuity are reported only) | `NOT_MEASURED` |
| Clinical efficacy | out of scope | no claim |

**VALIDATED selective hit (primary outcome)** (`outcomes.py`, `ENDPOINT`): the nominated pair has a CTRP post-QC curve, and both of these hold:

- AUC robust z among all of the compound's CTRP lines is at most −2;
- predicted viability at the top tested concentration is at most 0.5.

AUC and viability are averaged over experiments. A generic response is insufficient: the z-score is within the compound, so a pan-toxic compound's lines do not qualify by being killed.

- `NOT_EVALUABLE`: no CTRP curve for the pair. It counts as a miss, because the budget was spent.
- `PAN_ACTIVE`: compound median top-dose viability at most 0.5. This is the generic-toxicity class (S1), reported but not part of the hit rule.

## 4. Split and leakage control

- **Split** (`split.py`):
  - Mechanism families are connected components over shared Repurposing Hub **MoA strings**. Target genes are excluded because they chain kinase inhibitors into one 122-member component.
  - Families are assigned in salted sha256 order to the smaller split: development has 125 compounds, whose outcomes are opened for design; test has 128, whose outcomes are sealed. No MoA string crosses the split.
- **Leakage audit** (`leakage.py` → `LEAKAGE.json`, metadata only):
  - zero shared connectivity blocks, CTRP compound ids or MoA strings;
  - zero close analogues (Tanimoto ≥ 0.7, Morgan r2 2048 bits);
  - the median nearest-development similarity is 0.22 and the 95th percentile 0.41;
  - 38 test compounds share an annotated target gene with development, and 8 have nearest similarity ≥ 0.4. S12 repeats P1 and P2 without each set.
- **Shared by design:**
  - Cell lines appear in both splits. The task is triaging new compounds on a known panel, so line-level knowledge legitimately crosses; the memory arm uses it on purpose.
  - The line-sensitivity correction in z_r uses all 4,532 PRISM compounds' primary data. This is screen input, not outcome.
- **Assay and source:**
  - CTRP and PRISM are different platforms (ATP luminescence versus barcode abundance, 72 h versus 5 days, arrayed versus pooled).
  - Both come from the Broad Institute and share many cell-line stocks, so the confirmation is platform-independent, not laboratory-independent.
- **Chronology:** CTRP v2 is public, so an LLM may have memorised published associations. A positive agent effect is therefore suspect; a null is not.
- **Selection bias:** CTRP chose which compounds to profile, so the eligible compounds are enriched for oncology tools and drugs. Generalisation to a novel library is untested.
- **Exposure:** the CTRP archive (sha256 `8f62b3b5…dee3`) had its response values opened for the first time in this study: development in `dev*.py`, test only in `evaluate.py`.

## 5. Information and budgets

Every arm sees the same pre-confirmation evidence per pair (`features.py`, fixed in `DESIGN_LOCK.json` before any outcome was read):

- **Screen:** lfc; within-compound robust z (z_c); two-way residual z (z_r); line median and noise; compound promiscuity, MAD and rank.
- **Context:** ctx (the compound's mean z_r in the 25 expression-nearest lines, line excluded); lineage mean.
- **Mechanism:** target mutation; target expression z; leave-line-out biomarker slope prediction.
- **Transcriptional virtual cell:** L1000 transfer prediction and trust (k = 5, self and connectivity duplicates excluded).
- **Secondary**, only after purchase: within-compound z of mean 8-dose LFC, and dose slope.

Budgets per campaign of 16 compounds:

| Budget | Value | Cost meaning |
|---|---|---|
| Confirmation | B = b × 16 pairs, b ∈ {0.5, **1**, 2}; at most 3 lines per compound | one CTRP 16-dose curve per pair |
| Follow-up (loop arms) | K = 4 compounds (25%) | one PRISM 8-dose secondary screen per compound, across all lines |
| Full follow-up (S5) | every compound with a secondary available (98 of 128) | the same unit |
| Turnaround | loop arms add one follow-up round before confirmation | 1 round |
| LLM | 0 calls in the non-LLM arms | 0 USD |

The two follow-up and confirmation units have no recorded exchange rate, so costs are reported in their own units, and break-even rates are given where arms trade one for the other.

## 6. Arms (`arms.py`, `test_choose.py`, `agent_arms.py`)

| # | Arm | Comparator class | Definition |
|---|---|---|---|
| 0 | `zero` | zero arm | lines' general sensitivity only, with no compound measurement |
| 0 | `random` | zero arm | hash-random among primary hits (lfc ≤ −1) |
| 1 | `D1_magnitude` | deterministic | most negative lfc |
| 1 | `D2_compound_z` | deterministic | within-compound robust z |
| 1 | **`D3_two_way_z`** | deterministic (designated) | two-way residual z, line sensitivity and compound median removed |
| 1 | `D3f_two_way_z_hits` / `D4_target_mutation` | deterministic | D3 restricted to primary hits / target-mutated selective hits first |
| 2 | `ML` | strong ML | gradient-boosted classifier (HGB, fixed hyperparameters), screen features, fitted on all development pairs |
| 2 | `ML+context` / `ML+mechanism` / `ML+transcriptional` | ML factorial | ML plus one evidence group |
| 3 | `VC` | virtual cell without agent | HGB on all evidence groups |
| 3 | `VC+S`, `LOOP_uncertain`, `LOOP_top` | learned closed loop | HGB with secondary, applied to compounds bought by uncertainty or by top probability |
| 3 | **`MAESTRO`** | MAESTRO engine, no follow-up | −(z_r + ctx)/√2 |
| 3 | **`CONV_LOOP`** | conventional two-stage workflow | buy secondaries for the K compounds with the best −z_r, then −(z_r + sec)/√2 if bought, else −z_r |
| 3 | **`MAESTRO_LOOP`** | MAESTRO engine, closed loop | *frontier* acquisition: buy for the K compounds whose best capped pair ranks nearest the cutoff B on −(z_r + ctx); then −(z_r + ctx + sec)/√3 if bought, else −(z_r + ctx)/√2 |
| 3 | `CONV_frontier` / `MAESTRO_top` | factorial cells | the swapped acquisition rule |
| 3 | `CONV_ALL` / `MAESTRO_ALL` | full-cost loop | every available secondary bought |
| 4 | `AGENT_conventional` | conventional tool-using LLM agent | deepseek-flash: `buy_secondary` (K), then `submit_nominations` (B) over all evidence; no engine |
| 5 | `AGENT_maestro` | full MAESTRO Agent–VC | MAESTRO_LOOP engine plus an LLM reviewer that may flag up to ceil(B/4) pairs in the engine's top 2B with a named reason. Flagged pairs are replaced in engine order; numbers cannot change. |
| 6 | `MEM` / `SHUF` vs `MAESTRO_LOOP` (= no-memory) | memory controls | line reliability log-odds (Beta prior 20, λ = 1) learned from development plus own revealed nominations in earlier campaigns, added to MAESTRO_LOOP's final score; SHUF permutes the training labels before each campaign |

**Typed contract.** No LLM output can overwrite a measurement, prediction or QC field:

- agent outputs are parsed against a schema, and an invalid output is refused as `INVALID_AGENT_OUTPUT`;
- a refused output falls back to the arm's deterministic default (conventional: CONV_LOOP acquisition, then D3 nominations; MAESTRO: no flags).

## 7. Hypotheses and decision rules

There are two primary hypotheses, both at b = 1 (128 confirmation curves) with validated selective hits as the outcome. Each uses a one-sided sign-flip test over compounds (128 clusters, `cluster_signflip_test`) at **α = 0.025**, which gives family-wise 0.05 over the two. A 95% compound-bootstrap interval of the difference is also reported.

- **P1 (context-aware triage beats the strongest deterministic rule):** `MAESTRO` > `D3_two_way_z`.
- **P2 (coordinated modelling + experiment selection beats a conventional two-stage workflow at equal cost):** `MAESTRO_LOOP` > `CONV_LOOP`. Both buy 32 secondaries and both nominate 128 pairs.

Each is CONFIRMED if the difference is positive and p ≤ 0.025, REVERSED if negative with p_less ≤ 0.025, and NOT_CONFIRMED otherwise. A NOT_CONFIRMED P2 means MAESTRO's closed loop is not shown to beat conventional triage, whatever the secondaries say.

**Secondary analyses** are exploratory and make no confirmatory claim:

- S1: pan-active (generic toxicity) nominations per arm; D1 is expected to be dominated by them.
- S2: flexible learners versus D3, and evidence-group increments over ML.
- S3: factorial decomposition of P2 (score effect, acquisition effect).
- S4: P1 and P2 at b = 0.5 and b = 2.
- S5: full-cost loops (`*_ALL`, 98 secondaries) versus MAESTRO_LOOP (32): hits and cost per hit.
- S6: discovery breadth. This covers compounds with at least one validated hit, launched versus not, target-mutation-explained hits, and hits found by one arm but missed by the reference.
- S7: calibration of MAESTRO_LOOP and D3. It uses a logistic map fitted on development, and reports expected versus realised hits, Brier score and bins. It also gives the abstention curve (`INSUFFICIENT_EVIDENCE` below τ), with curves saved and hits lost.
- S8: memory. MEM − NO_MEM and MEM − SHUF, with sequential per-campaign hits.
- S9: P1 and P2 with mechanism-family clusters (64 test families).
- S10: D3 versus zero, random and D1 (sanity checks).
- S11: learned loop arms versus MAESTRO_LOOP.
- S12: P1 and P2 without target-sharing or similar compounds (§4).
- Evidence reliability: hit rate of MAESTRO_LOOP nominations by context agreement, secondary purchase, target mutation and pan-activity.

**Agent hypotheses.** These are scored only if the paid run is authorised; AGENT_RESULTS.json is separate and write-once. There are 3 replicates, and each replicate is scored.

- A1: `AGENT_maestro` > `MAESTRO_LOOP`, meaning the flags add value. A1 passes only if all three replicates are positive and the pooled sign-flip p ≤ 0.025.
- A2: `AGENT_conventional` versus `CONV_LOOP` and versus `MAESTRO_LOOP`. This asks whether an unconstrained agent matches the engine.
- Flag precision: the fraction of flagged pairs that validated anyway.

## 7b. Scientific Decision Review (separately registered family R)

This section was added at the owner's request (2026-10-13), before the freeze and before any test outcome. It applies principles from Co-Scientist (Gottweis et al., *Nature* 2026; arXiv:2502.18864v2) and from its real-world extension (Schmidgall et al., arXiv:2608.26701) only where they have measured support.

**Principles adopted:**

- **Deterministic claim verification against execution records.** The extension's ablation measured the largest controlled effect: severe result-hallucination rate fell from 46% (ablated) and 90% (baseline) to 4%, with no loss of idea quality.
- **Competing falsifiable explanations, plus experiments chosen to discriminate between them.**
- **Expert approval for consequential experiments.** Every wet-lab validation in both papers was expert-curated.

**Principles bounded:**

- Elo and tournament rankings are self-evaluated, with no ground-truth concordance reported. They are used here **only to order exploration** and never as probabilities.
- Evolution, meta-review and search grounding gave small proxy-benchmark gains (GPQA AUC +0.005 to +0.01). They are not adopted without a decision-level ablation.

**Explanations** (`review.py`). For a screen-selective pair (c, l):

| Explanation | Claim | Predictions |
|---|---|---|
| SELECTIVE (progression) | a coherent sensitive subpopulation | selective breadth (lines with z_r ≤ −2.5) ≥ 2; bought secondary z ≤ −2 on the best line |
| NOISE | an isolated single-dose outlier | breadth ≤ 1; secondary z > −1 |
| GENERIC | broad cytotoxicity | a high fraction of lines with lfc ≤ −1 |

**Evidence admission** (`maestro.decision_review.admit`): only qualified real measurements, or analyses derived from them in the same assay context, may support or contradict a prediction. Virtual-cell predictions, retrieved annotations and LLM outputs are context only.

**Decisions per compound:**

- **GO:** pairs funded within B.
- **NO_GO**, always named:
  - `NO_SELECTIVE_SIGNAL`;
  - `ISOLATED_OUTLIER_UNREPLICATED` (breadth ≤ 1 and no replicating bought secondary);
  - `NON_REPLICATING` (bought secondary z > −1 on the best line).
- **NEED_MORE_EVIDENCE:** not falsified and not funded. The record names the discriminating experiment (PRISM secondary if available and unbought, otherwise orthogonal confirmation of the best line).

Every record stores its evidence values. S14 re-derives them all from `features.npz`, and any mismatch is an unsupported claim.

**Arms** (at all budgets, K = 4, the same engine as MAESTRO_LOOP; the engine must reproduce MAESTRO_LOOP's choices exactly, `REVIEW_ENGINE_MISMATCH`):

| Arm | Acquisition | Veto | Evidence admitted for vetoes | Re-rank |
|---|---|---|---|---|
| MAESTRO_LOOP (existing Agent–VC engine baseline) | frontier | — | — | — |
| SDR_veto | frontier | yes | measured only | — |
| SDR_acquire | explanation (unsettled breadth 1–3 inside the 2B window first) | — | — | — |
| SDR_veto_acquire | explanation | yes | measured only | — |
| SDR_unverified | frontier | yes | **virtual-cell predictions admitted as replicates** | — |
| SDR_full | explanation | yes | measured only | breadth/generic, fitted on all development (β 0.023, γ −0.83) |
| SDR_debate (LLM, NOT_RUN) | deepseek-flash explanation generation plus a 3-round Swiss tournament (`agent_review.py`) | yes | measured only | — |

A compound is **confirmable** when any of its screen-selective pairs (z_r ≤ −2) validates in CTRP. A NO-GO on a confirmable compound is a **false NO-GO**.

**Confirmatory hypotheses (family R).** The family is controlled separately from family P; each test is at one-sided α = 0.025.

- **R1 (veto correctness).** Compounds vetoed by measured evidence in SDR_veto at b = 1 are confirmable less often than SDR_veto's NEED_MORE_EVIDENCE compounds (one-sided Fisher exact test).
- **R2 (evidence verification).** SDR_unverified makes more false NO-GOs than SDR_veto at b = 1. This is a paired sign-flip test over compounds on the false-NO-GO indicator.

**Descriptive and secondary analyses:**

- **R3:** SDR_veto − MAESTRO_LOOP hits at b = 1, with a −6 non-inferiority margin. This is known to be nearly structural before opening: the two arms differ in 1 of 128 nominations at b = 1 (3 of 256 at b = 2).
- **R4:** decision-aware acquisition, SDR_veto_acquire − SDR_veto.
- **R5:** re-ranking, SDR_full − SDR_veto_acquire.
- **R6:** the debate arm versus SDR_veto_acquire and SDR_veto. Each replicate must beat SDR_veto_acquire at p ≤ 0.025 to pass. The unsupported-citation rate of its explanations is also reported.
- **S13:** decision quality of every arm (GO with a validated nomination, false NO-GO, confirmable NEED_MORE_EVIDENCE).
- **S14:** the record audit.

**Report audit:** every quantitative claim in the study README is listed in `CLAIMS.json` with its run and JSON path. `verify.py` checks them with `maestro.claim_audit.audit` against `RUNS.json`, a manifest of every successful, negative, failed and excluded run. The report is released only if the audit passes, which requires every negative run to be cited.

**Human approval:** this retrospective study executes no experiment. `maestro.decision_review.authorize_execution` refuses any experiment without a human approval bound to the request digest and within budget (`APPROVAL_MISSING`, `APPROVAL_MISMATCH`, `SELF_APPROVAL`). Any prospective use must pass through it.

## 8. Development evidence disclosed before the freeze

The development outcomes (125 compounds) were opened. Everything seen is in `DEVELOPMENT.json` and `DEV_EXPLORE{,2,3}.json`. The design choices it drove:

**Data:** 53,309 evaluable pairs, with a base rate of 2.9% (4.4% among primary hits). 105 of 125 compounds have at least one validated pair; 77 are pan-active.

**Arms at b = 1 (125 nominations):**

| Arm | Validated hits |
|---|---|
| D1 magnitude | 10 (112 pan-active nominations) |
| D2 | 57 |
| D3 | 59 |
| ML | 32 |
| VC | 48 |
| VC+S | 62 |
| zero | 6 |
| random | 7 |

- Flexible learners trained across mechanism families lose to D3, which is why D3 is the designated deterministic comparator.
- Context improves both D3 (D3+ctx, 65) and ML (+18, p 0.0003).
- The transcriptional virtual cell adds nothing (+2). The target biomarker adds nothing beyond context.

**Acquisition and score normalisation** (DEV_EXPLORE2), at b = 1 with 32 bought:

| Arm | Validated hits |
|---|---|
| conventional top | 62 |
| conventional frontier | 70 |
| MAESTRO top | 70 |
| **MAESTRO frontier** | **76** |

√-normalised sums beat plain sums. These numbers chose the P2 arms, so the development gap (+14) is optimistic. The test is the arbiter.

**Memory** (DEV_EXPLORE3):

| Arm | Validated hits at b = 1 |
|---|---|
| line memory | 67 |
| shuffled | 65 |
| no memory | 65 |

Lineage memory hurt (60 versus 71 shuffled). Line memory at λ = 1 was chosen, and S8 is exploratory.

**Learned-model calibration:** VC out-of-fold predictions under-predict in mid bins. Abstention did not raise the hit rate (38% → 42% at τ 0.3, losing 19 hits).

**Scientific Decision Review** (`DEV_REVIEW.json`, b = 1). Most MAESTRO_LOOP failures sat in compounds funded for a single line: 11 of 13 such compounds had no validated hit.

| Arm | Hits | Evidence NO-GOs (confirmable) | NEED_MORE_EVIDENCE (confirmable) |
|---|---|---|---|
| MAESTRO_LOOP | 76 | 0 | 67 (23, 34%) |
| SDR_veto | 75 | 20 (2, 10%) | 48 (22, 46%) |
| SDR_veto_acquire | 74 | 17 (1) | 48 (20) |
| SDR_unverified | 72 | 37 (**13**) | 34 (13) |
| SDR_full | 70 | — | — |

- The breadth re-ranking did not survive out of fold. One fold gave β = 2.6; the other four gave about 0.
- No review variant added hits.
- The breadth threshold was chosen after seeing that single-line compounds failed, so R1 is optimistic on development.

## 9. Refusals

| Refusal | Raised when |
|---|---|
| `FREEZE_MISSING` / `FREEZE_MISMATCH` | test outcomes requested before or after any change to frozen files |
| `CHOICES_MISMATCH` | the locked choices differ from recomputation or from their lock digest |
| `RESULTS_MISMATCH` | a rerun of the one-shot evaluation does not reproduce it exactly |
| `CTRP_ARCHIVE_MISMATCH` | the confirmation archive hash changed |
| `INSUFFICIENT_EVIDENCE` | an abstention below τ (S7, descriptive) |
| `INVALID_AGENT_OUTPUT` | an agent answer violates its schema, budget, cap or candidate set |
| `SPEND_CEILING` | a paid call would cross the authorised USD ceiling |
| `MODEL_NOT_AUTHORISED` | any model other than deepseek-flash |
| `AGENT_CHOICES_EXISTS` | a second paid agent run |
| `NOT_MEASURED` | target engagement and developability (no claim made) |
| `REVIEW_ENGINE_MISMATCH` | the review engine does not reproduce MAESTRO_LOOP's frozen choices |
| `ACQUISITION_OUTSIDE_BUDGET_OR_AVAILABILITY` | an externally chosen purchase exceeds K or picks a compound without a secondary |
| `RANKING_NOT_PROBABILITY` | a tournament ranking is read as a probability or used as evidence |
| `APPROVAL_MISSING` / `APPROVAL_MISMATCH` / `SELF_APPROVAL` | a consequential experiment lacks a matching human approval |
| `ISOLATED_OUTLIER_UNREPLICATED` / `NON_REPLICATING` / `NO_SELECTIVE_SIGNAL` | named NO-GO reasons |

## 10. Costs of this study

- 0 wells, 0 LLM calls and 0 USD were spent in the non-LLM arms.
- There were no downloads: every source was local and hash-recorded in `CENSUS.json`.
- **Agent arms, if authorised:**
  - `agent_arms.py`: 8 campaigns × 3 replicates × 3 calls = 72 deepseek-flash calls, about 0.55 M input and 70 k output tokens, **≈ 0.26 USD**;
  - `agent_review.py`: 8 campaigns × 3 replicates × (1 generation + about 14 matches), about 360 calls, 0.25 M input and 0.12 M output tokens, **≈ 0.21 USD**;
  - a hard ceiling is set by `--authorized-usd`. Failed calls are ledgered but never cached, and the choice files are write-once.

## 11. Frozen future protocol for independent and prospective confirmation

No local untouched confirmation source exists:

- GDSC2 was opened in the mono-pretraining block.
- GSE70138 and Jaaks are exposed.
- The Vis 2024 release is sealed, but it is a combination screen with no single-agent selectivity endpoint for these compounds.

A future test therefore runs the frozen `MAESTRO_LOOP` against `CONV_LOOP` and `D3` with these settings unchanged:

- **Data:** a compound set and screen released after 2026-10-13, or a new wet-lab campaign. Examples are a later PRISM release with compounds absent from 19Q4, confirmed in an orthogonal arrayed viability assay.
- **Design:**
  - 16-compound campaigns with B = 16 confirmation curves and K = 4 follow-up dose-responses;
  - the same endpoint (within-compound AUC robust z ≤ −2 and top-dose viability ≤ 0.5);
  - the same P2 test at α 0.025;
  - choices frozen by digest before any confirmation plate is read.
- **Promotion rule:** `MAESTRO_LOOP` is promoted from `research/` to production only if P2 is CONFIRMED here *and* on that future set.
