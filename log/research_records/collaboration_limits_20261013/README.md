# Limits of Agent-Virtual Cell collaboration (2026-10-13)

**Status: FROZEN, run once.**
- **GCP fresh-line confirmation tier.** Pre-registered in [PROTOCOL.md](PROTOCOL.md) and frozen in [FREEZE.json](FREEZE.json) before any outcome in A549, NPC or Astrocyte was downloaded. Both primary hypotheses pass.
- **L1000 analyses.** Exploratory, on the already-exposed Block Q tier.
- **Promoted:** `maestro.endpoint_decision`.
- **Not promoted:** any agent role, any memory loop, any new transfer model.
- **Costs:** 0 laboratory wells, 0 provider calls ($0), 12 public LVL3 plates downloaded.

## Answer in brief

The largest limitation was not the agent and not the virtual cell. It was the **decision layer between them**:
- The frozen decoder ranked follow-ups by the largest *standardised* prediction.
- The experiment counts a hit only when the *raw* mean clears 0.5 log2 and every replicate agrees in sign.

Replacing that ranking with the probability of meeting the criterion changed decisions on three target lines the study had never seen:
- Same frozen forecast: per-line hits 55/141 → 77/141 (+15.6 points [+9.2, +22.7], p = 5e-5).
- Calibrated abstention separated 81% hit decisions from 38% ones.

The rest of the brief resolves into limits that are confirmed, not defects to patch:
- **14 against 12.** The gap between the deterministic model and the agents did not replicate; it reversed on the fresh lines.
- **Agent donors.** Agent-selected pharmacological donors carried less response information than measured anchor similarity, on every tier tested.
- **No-anchor degradation.** It is an identifiability ceiling. The same compound in another line carries 0.81 specific cosine; the best between-compound relation carries 0.48, and only rarely.
- **Memory.** It has no learning pathway in production. In simulation:
  - single-line sparse measurements cannot feed cross-line transfer;
  - one campaign is worth at most +0.003 to +0.005 cosine;
  - self-training raises the zero-shot proxy while lowering decision quality.

## Prioritised root causes

Status words: **confirmed defect** (wrong code or objective, fixed, effect confirmed on fresh data), **confirmed limit** (a property of the data or design, measured), **supported** (consistent on development and fresh data but not significant on fresh), **refuted**.

| Rank | Question | Root cause | Status | Decisive evidence | Response |
|---|---|---|---|---|---|
| 1 | Q3 objective | Decoder ranks standardised effects; hit needs raw 0.5 log2 plus replicate agreement. 29 of 34 features have reference SD below 0.5, and replicate SD (median 0.24) is close to between-compound SD (0.32). | confirmed defect | Fresh P1: +22 per-line hits (p 5e-5); S1 across-line 18 → 29 (p 0.004); S2: scale alone +20 (p 0.0002) | `maestro.endpoint_decision` promoted |
| 2 | Q3 uncertainty | Uncalibrated P(hit) is overconfident on the chosen action. Reference LOO expected 54, realised 43. | confirmed defect | Fresh P2: calibrated q ≥ 0.5 hit 81% (54 decisions) vs 38% (87); lower bound +0.27; CITL -0.03 per decision | Platt step and named refusal `HIT_PROBABILITY_BELOW_THRESHOLD` |
| 3 | Q2 anchor | No-anchor transfer must use between-compound relations, which carry little compound-specific direction. | confirmed limit | L1000: same compound other line, mapped 0.81; Tanimoto ≥ 0.6 0.48 (121 pairs; 16% of active cells have Tanimoto ≥ 0.5); same MoA 0.25; shared target 0.13; random 0.00. Oracle best donor 0.60 needs the outcome. GCP S5: anchor 77 vs no-anchor 53 hits | Anchor measurement where follow-ups are dense (see below) |
| 4 | Q1 14 vs 12 | Decoder instability on near-ties, plus sampling noise. 2 of the 4 discordant compounds had a top-two margin of 0.04 z. | refuted as an agent effect | Fresh S4, frozen endpoint: no-agent 7/20 vs integrated 9, conventional 9, agent-only 4, initial 9 | Report decisions with margins; aligned decoder |
| 5 | Q4 donors | Agent swaps the strongest donor signal (anchor-phenotype similarity, within-query Spearman 0.73) for pharmacology, which adds little beyond it. Partial r given anchor similarity: annotated MoA/target 0.15 [0.02, 0.28]; description text 0.02 [-0.05, 0.09]. | supported | Agent donors' mean phenotype rank 6.6-7.9, Jaccard with top five 0.47-0.61. Residual cosine lower on the exposed test (0.56-0.59 vs 0.62-0.66). Fresh S3: every agent arm negative, all CIs include 0 (integrated -0.008 [-0.032, +0.009]) | Agent should not choose donors when an anchor exists |
| 6 | Q5 memory | Production `run_profiling` never admits measured rows as references; CaseStore replays receipts only. | confirmed limit (code fact) | No code path from outcome to reference atlas | Outcome admission kept in research; see below |
| 7 | Q5 memory | Sparse hub designs put almost every measurement in one line; single-line rows cannot feed line-to-line maps or residual routes. | confirmed limit (post hoc) | L1000: 63 of 64 cells in the hub line; fills in the other lines changed by 0.0 (line 4: 0.04); map utility exactly 0 in all 10 campaigns | Paired-profile admission needed (experiment E4) |
| 8 | Q5 memory | Even full-profile admission has a small ceiling at ~1,000 references. | confirmed limit | Learning curve +0.032 (no anchor) and +0.050 (one line) per doubling: +0.003 / +0.005 per 64-compound campaign | Learning is a slow asset, not a fix |
| 9 | Q5 memory | Self-training (admitting fills as measurements) inflates zero-shot agreement while harming decisions. | confirmed (exposed data) | Pseudo-label: zero-shot +0.014 (10/10, p 0.002), map utility -0.0029 (10/10, p 0.002) | Refuse predicted values as references |

## What was implemented

- [`src/maestro/endpoint_decision.py`](../../src/maestro/endpoint_decision.py) (promoted, NumPy only):
  - `signed_hits` and `pooled_replicate_sd` define the success criterion and the replicate noise.
  - `fit_endpoint_model` estimates the shrinkage slope, the true-mean spread net of replicate noise, and a logistic recalibration, all from reference leave-one-out.
  - `EndpointModel.hit_probability` integrates over spread and replicate noise by Monte Carlo with common random numbers, a fixed seed and an optional fixed draw width (batch-invariant).
  - `choose` returns one decision per target line or per query, with the named refusal `HIT_PROBABILITY_BELOW_THRESHOLD` when calibrated P(hit) is below the caller's threshold.
  - `VALIDATED_SCOPE` is GCP histone peptides at 24 h with an A375 anchor.
- [`tests/test_endpoint_decision.py`](../../tests/test_endpoint_decision.py): 7 contract tests. They cover the hit definition, pooled SD, rejection of large-standardised/small-raw forecasts, replicate-noise sensitivity and sign symmetry, abstention, reproducibility and batch invariance, and recovery of shrinkage and spread.
- [`gcp.py`](gcp.py) (frozen): parity with the prior study, diagnostics, donor information, development decoder, and the one-shot fresh pipeline (`fresh-metadata`, `fresh-prepare`, `fresh-choose`, `fresh-evaluate`).
- [`rkt_limits.py`](rkt_limits.py) (exploratory): `ceiling`, `curve` and `memory` on the exposed Block Q tier.
- [`verify.py`](verify.py): freeze check and replay of every result (see Verification).

The agent was not made more complex. No agent role is promoted, and the cached agent donor sets were re-decoded rather than re-queried.

## Fresh confirmation tier (GCP, run once)

**Setup:**
- A375 anchor at each compound's frozen dose; fresh target lines A549, NPC and Astrocyte.
- 65 references and 47 queries (27 development and 20 test compounds of the frozen connectivity split).
- 37 modelled histone features.
- The decision model was fitted on fresh-line reference leave-one-out only: b 0.861, Platt (-0.273, 0.451).
- Oracle: 118 of 141 (query, line) decisions have at least one attainable hit; random action hit rate 9%.

### Primary hypotheses

| Hypothesis | Result | Pass |
|---|---|---|
| P1: per-line hits, P(hit) vs frozen z decoder, same forecast | 77/141 vs 55/141; +15.6 points, bootstrap [+9.2, +22.7]; cluster sign-flip p_greater 5e-5 (47 compounds) | yes |
| P2: hit rate, calibrated q ≥ 0.5 vs < 0.5 | 0.815 (n 54) vs 0.379 (n 87); difference 0.436, 2.5% bound 0.272. CITL -0.031 per decision [-0.108, +0.050]; expected 72.7, realised 77 | yes |

### Secondary analyses

| Analysis | Result |
|---|---|
| S1 across-line (one decision per compound) | 29/47 vs 18/47; p_greater 0.004 |
| S2 scale alone (raw vs z) | +20 per-line hits, p 0.0002 |
| S2 uncertainty beyond scale (P(hit) vs raw) | +2, p 0.68: the gain is the scale; the uncertainty model supplies calibrated abstention |
| S3 donor residual cosine, test compounds | All four agent arms below their comparator, none significant. integrated -0.008 [-0.032, +0.009]; conventional -0.023 [-0.058, +0.007]; agent-only -0.024 [-0.076, +0.021]; initial -0.012 [-0.032, +0.004]. Per-line P(hit) hits: 26, 25, 27 vs 28; agent-only 18 vs 22 |
| S4 frozen endpoint replication | no-agent 7/20; integrated 9; conventional 9; agent-only 4; initial 9. No difference significant |
| S5 anchor value | 77 vs 53 hits for the no-anchor reference mean, p 5e-5 |
| S6 memory loop (exploratory) | memory -3 hits (p 0.45), cosine +0.0003; shuffled -5 hits (p 0.30); second-half cosine -0.030 (p 0.039) |

**Descriptive, post hoc, on exposed outcomes:**
- **What the anchor buys.** The no-anchor arm always chooses the same three generic actions, one per line, and hits 53/141. The anchored model departs from them in 112 decisions and hits 62 of those, where the generic action would have hit 38. All 24 extra hits come from compound-specific choices.
- **When the anchor pays per well-set.** It pays only when a compound gets several follow-ups:
  - three per-line follow-ups: 0.41 hits per well-set with the anchor vs 0.38 without;
  - one follow-up per compound: 0.31 vs 0.34.
- **The endpoint rewards generic responses.** A directional histone change can be met by a generic responder. P1 shows better decisions on the registered endpoint, not better mechanism-specific prediction; S3 tracks the specific part.

## L1000 analyses (exploratory, exposed Block Q tier)

All on 702 GSE70138 compounds, 7 lines and 1,105 active cells, with the frozen GSE92742 certifier.

**Ceiling, question 2** ([rkt_ceiling.json](rkt_ceiling.json)):
- Centred cosine: no anchor 0.360, one profiled line 0.528.
- Best single reference donor, chosen with the outcome: 0.600; top five oracle 0.531.
- Nearest-structure donor: 0.120. The oracle donor's mean Tanimoto is only 0.15, so the best donor is not found by structure.
- No-anchor accuracy is not monotone in the nearest Tanimoto: bin means range from 0.32 to 0.44, and the closest analogues (Tanimoto at least 0.8, 14 cells) give 0.42.

**Learning curve, question 5** ([rkt_learning_curve.json](rkt_learning_curve.json)):

| References | 122 | 245 | 490 | 979 |
|---|---|---|---|---|
| No anchor | 0.292 | 0.325 | 0.356 | 0.388 |
| One line | 0.418 | 0.466 | 0.524 | 0.559 |

These are means of three subsamples (one at full size), on 240 queries.

**Sequential memory, question 5** ([rkt_memory.json](rkt_memory.json)), 11 campaigns at one well per compound:

| Arm minus no memory | Zero-shot cosine | Map utility |
|---|---|---|
| memory | +0.0037 (10/10, p 0.002) | 0.0 exactly |
| shuffled | -0.0030 (p 0.014) | 0.0 exactly |
| pseudo-label | +0.0140 (p 0.002) | -0.0029 (p 0.002) |

**Interpretation:**
- Measured memory helps only the hub line's zero-shot generic direction.
- Shuffled memory hurts, so integrity of admitted outcomes matters.
- Self-training is refused: it looks better on agreement and is worse for decisions.

## Question 6: shift, evidence, calibration, leakage, cross-assay transfer

- **Domain shift.**
  - The fresh lines include two non-cancer backgrounds (NPC, Astrocyte).
  - The recalibration slope fitted in the fresh lines (0.45) is flatter than on development (0.80): raw P(hit) grows more overconfident under shift. It must be refitted per line set, never carried over.
  - Calibration-in-the-large stayed within -0.03 per decision once refitted.
- **Evidence dependence.** Everything above the generic response depends on a measured anchor (rank 3). Without one, both RKT and GCP fall back to generic directions or generic actions.
- **Calibration.**
  - Block Q certificates were near-calibrated in their own scope.
  - Uncalibrated P(hit) is not (rank 2).
  - Nothing here calibrates agent-stated confidence; it is never used as a weight.
- **Leakage and exposure.**
  - The GCP original test, the Block Q tier and now the fresh GCP lines are all exposed.
  - All seven GCP cell backgrounds have now been opened at 24 h.
  - Public data may sit in the language model's pretraining.
  - The connectivity split separates structures, not mechanism families, laboratories or cultures.
  - Replicates are records within plates, not independent cultures.
- **Cross-assay transfer.**
  - The RKT certificate is validated only for L1000 landmark responses.
  - The endpoint decoder is validated only for GCP histone peptides.
  - No RNA-to-histone bridge is claimed or built, and `VALIDATED_SCOPE` strings say so.

## What this does not show

- That any agent role adds scientific value. None was found; the agent's donor selection was weakly harmful on every tier.
- That outcome memory improves decisions. No production pathway exists, and the simulated pathway was worth at most +0.005 cosine per campaign.
- Prospective validity. Every outcome is a retrospective public record, and every tier used here is now exposed.
- Mechanism specificity or efficacy. The endpoint is a directional histone-peptide change.

## Experimental plan

Each experiment needs a new pre-registered freeze, a zero arm, a fixed deterministic baseline, costs in wells and turnarounds, and named refusals.

- **E1, decoder transfer to a new endpoint (cross-assay; data are public and unopened).**
  - Pick the next qualified unopened tier, for example GCP at another time point or P100 phosphopeptides with the same connectivity split, after a metadata-only census of eligible units.
  - Arms: frozen z, raw, P(hit). Primary: per-line P(hit) vs z. Secondary: abstention separation and calibration-in-the-large.
  - Power: at the fresh effect and spread (+15.6 points, per-compound SD 0.24), 19 compounds give 80% power at one-sided 0.025. If the effect halves on a new endpoint, about 75 are needed. Require at least 40, and state the minimum detectable effect before opening outcomes.
- **E2, strategic anchor at equal wells.**
  - Arms:
    1. no anchor, generic P(hit) actions;
    2. anchor then P(hit) follow-ups;
    3. gated anchor: measure it only when the no-anchor calibrated P(hit) of the best action falls below a pre-set threshold, or when two or more follow-ups are planned.
  - Endpoint: hits per well-set at fixed total wells.
  - Prediction from the fresh tier, to be tested: arm 2 beats arm 1 only with two or more follow-ups per compound; arm 3 beats both.
- **E3, agent role restricted to evidence gaps.**
  - The agent never selects donors when an anchor exists. It may only:
    - request an anchor measurement;
    - flag a query whose calibrated P(hit) is low for abstention or wait;
    - propose a pre-specified annotated-MoA tie-break inside the deterministic donor ranking.
  - Arms: the fixed deterministic workflow, a conventional ReAct agent and the restricted agent, all at equal wells and calls.
  - Primary: hits per well-set; the agent must beat the fixed workflow, not just match it.
  - Cost: deepseek-flash only, with an explicit ceiling approved before the run.
- **E4, paired-profile memory.**
  - Change admission, not the model: reserve a fixed fraction of each campaign's wells (for example 1 in 8) for a second line on hub compounds, so admitted rows are paired.
  - Arms: no memory, single-line memory, paired memory, shuffled paired memory, all at equal total wells.
  - Endpoint: next-campaign map utility and decision hits.
  - Pre-declared expectation: an effect at most the learning-curve ceiling (+0.005 per campaign). The study therefore needs about 10 or more campaigns to detect it. Stop if the ceiling, re-estimated on the new library, is below the minimum detectable effect.
- **E5, prospective confirmation.**
  - Once E1 to E3 pass, run one wet-lab campaign with sealed outcomes, independent cultures and a mechanism-family holdout.
  - Wells and turnarounds are budgeted before the start; P(hit), the fixed workflow and the zero arm run in parallel.

## Verification

```bash
D:/anaconda/envs/maestro/python.exe research/collaboration_limits_20261013/verify.py
```

**Default run (maestro env):**
- Checks the freeze digests, the fresh-cache and plate hashes, and the binding of choices to the freeze.
- Replays `FRESH_METADATA`, `FRESH_CHOICES`, `fresh_predictions`, `FRESH_RESULTS`, `development_decoder`, `diagnostics_gcp` and `donor_information` into temporary folders.
- Shows that `maestro.endpoint_decision` makes all 141 per-line and 47 per-query frozen decisions with bit-identical P(hit).
  - Platt gap: 7.8e-08 (Newton here, BFGS in the frozen module).
  - Abstention flips: 0.
- Result: all replays reproduced.

```bash
C:/Python314/python research/collaboration_limits_20261013/verify.py --l1000
```

This replays the three L1000 JSON files. It needs Python 3.14 with scikit-learn 1.8: the Block Q certifier pickle does not load under scikit-learn 1.9.

Deviations from the protocol are listed in [DEVIATIONS.json](DEVIATIONS.json), which the freeze does not hash.
