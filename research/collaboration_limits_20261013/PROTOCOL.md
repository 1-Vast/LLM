# Protocol: limits of Agent-Virtual Cell collaboration (2026-10-13)

Written before any outcome in the fresh GCP target lines (A549, NPC, Astrocyte) is downloaded or read. Base revision `17900821`. No paid API call is authorised or needed: every agent decision used here is the cached output of the frozen 2026-10-13 evidence-transfer run.

## Questions

1. Why did the development-selected deterministic GCP model find 14/20 hits while agent-integrated arms found 12/20?
2. Why does RKT degrade without a measured anchor?
3. Is the decision objective aligned with the experimental success criterion?
4. Does agent-selected pharmacological evidence add information, or does it introduce unreliable donor selection?
5. Why has persistent memory not produced cross-case learning?
6. Which shift, evidence, calibration, leakage and cross-assay limits apply?

## Evidence already seen (development; disclosed, not confirmatory)

All of these come from reference leave-one-out, the development split, or the exposed GCP test (`diagnostics_gcp.json`, `donor_information.json`, `development_decoder.json`):

* **Scale mismatch.** The frozen decoder chooses the largest *standardised* prediction, but a hit needs a *raw* log2 effect above 0.5. 29 of 34 features have a pooled reference SD below 0.5, and replicate SD (median 0.24) is close to the between-compound SD (median 0.32).
* **Decoder comparison per (compound, target line):**

  | Data | Frozen decoder hits | Aligned P(hit) decoder hits |
  |---|---|---|
  | Reference leave-one-out | 73/198 | 94/198 |
  | Development | 30/81 | 45/81 |

  A raw-scale argmax recovers most of this: 90/198 and 44/81.
* **Calibration.** A two-parameter logistic recalibration fitted on reference leave-one-out gives 43.0 expected hits against 45 realised on development.
* **Donor information.** Single-donor transfer accuracy tracks anchor-phenotype similarity (within-query Spearman 0.73). After accounting for phenotype similarity:
  * description text: partial r 0.02 [-0.05, 0.09];
  * annotated MoA/target overlap: partial r 0.15 [0.02, 0.28].

  Pharmacology-led donor policies lower residual cosine: 0.48-0.51 against 0.59 on reference leave-one-out.
* **Exposed test.** Agent donors had lower residual-transfer cosine than the phenotype top five (0.56-0.59 against 0.62-0.66). The 14-versus-12 gap persisted under every single-reference jackknife (difference 1-4).
* **Dry run.** A code check on the already-opened original lines reproduced the frozen agent hit counts exactly. Its own outcomes are not evidence.

## Fresh confirmation tier (GCP, pre-registered)

**Data.** Panorama LINCS GCP 2020, 24 h. The anchor is A375 at each compound's frozen selected dose. The fresh target lines are A549, NPC and Astrocyte, whose plates no MAESTRO study has downloaded.

**Eligibility** (metadata only, `FRESH_METADATA.json`): at least two samples at the selected dose in A375 and in all three fresh lines. This gives 65 references and 47 queries (27 development and 20 test compounds of the frozen connectivity split).

**Normalisation** is identical to the prior study: LVL3 minus the same-plate per-probe DMSO median, using vehicle wells only. Features are the probe intersection across the 16 A375/fresh plates. The modelled features are those finite in every reference mean in all four lines; this is a reference-only rule.

**Integrity rules:**
* Query targets are read only by `fresh-evaluate`, after `fresh-choose` has saved every decision with a hash.
* A query anchor's missing features are imputed with the reference A375 mean (inherited rule).
* A missing target makes that decision a non-hit.

**Models.** All are fitted on references only:
* the frozen no-agent blend (0.5 ridge + 0.5 similarity-weighted phenotype top five);
* ridge alone and phenotype alone;
* `reference_mean`, the zero arm with no anchor information.

Agent arms are re-decoded from the cached frozen donor sets for the 20 test compounds. Integrated and conventional use 0.5 ridge + 0.5 equal-weight donors; agent-only uses donors alone; the initial (pre-disclosure) set is also re-decoded. A donor absent from the fresh references is dropped. An empty set falls back to the phenotype weights (frozen rule).

**Decoders:**
* `z`: the frozen largest absolute standardised prediction.
* `raw`: the largest absolute log2 prediction.
* `phit`: the largest P(hit), where P(hit) is the probability that the observed mean exceeds 0.5 log2 in the predicted direction and every replicate agrees. It uses:
  * shrunk mean b x prediction;
  * the true mean's SD sigma around it, net of replicate noise;
  * replicate SD tau;
  * design replicate counts taken from metadata;
  * 4,000 Monte Carlo draws with a fixed seed.

  b, sigma, tau and the logistic recalibration come only from reference leave-one-out in the fresh lines (`decision_model`).

**Hit** (inherited): observed signed mean > 0.5 log2, at least two finite replicates, and every replicate in the predicted direction.

### Primary hypotheses

Bonferroni over two hypotheses, one-sided alpha 0.025 each.

* **P1, aligned decision.** Unit: one decision per (query, fresh target line), 141 decisions in 47 compound clusters. The no-agent model with `phit` finds more hits than with `z`.
  * Test: exact or 20,000-draw cluster sign-flip on per-compound hit differences (`tools.evaluation.scoring.cluster_signflip_test`). Pass if `p_greater` < 0.025.
  * Report the hit-rate difference with a compound bootstrap 95% interval.
* **P2, uncertainty-aware abstention.** Among the same `phit` decisions, the hit rate when the recalibrated P(hit) is at least 0.5 exceeds the hit rate below 0.5.
  * Pass if the 2.5% compound-bootstrap quantile of the difference (10,000 draws) is above zero.
  * Report calibration-in-the-large (expected minus realised per decision, with interval) descriptively. An absolute value at most 0.10 is the declared target, not a pass condition.

### Secondary analyses

No family-wise claims are made from these; all are reported.

* **S1.** Across-line decision (the frozen endpoint, one per compound): `phit` versus `z`.
* **S2.** Per-line `raw` versus `z` (scale alone), and `phit` versus `raw` (uncertainty and replicate model beyond scale).
* **S3, question 4.** On the 20 test compounds in the fresh lines, compare cached agent donor sets with the deterministic donors. Comparators:
  * integrated, conventional and initial against the no-agent blend;
  * agent-only against phenotype alone.

  Metric: residual cosine between predicted and observed (target minus anchor) in standardised units, averaged over lines; two-sided exact sign-flip. Also report per-line `phit` hits.
* **S4, question 1 replication.** The frozen across-line `z` endpoint in the fresh lines: no-agent model against each agent arm on the 20 test compounds.
* **S5, question 2 analogue.** Anchor value: `phit` hits of the no-agent model against the no-anchor `reference_mean` zero arm.
* **S6, question 5 (exploratory).** Memory loop. Queries are processed in sha256 order. After each decision the chosen across-line `phit` line is "measured", and its complete response is admitted with the A375 anchor as a partial reference for later queries. Admission requires a complete measured response; admitted anchors are imputed like query anchors.
  * Arms: `no_memory`; `memory`; `shuffled`, which admits the same line's response of the next compound in the order, breaking the anchor-response link at equal data volume.
  * The decision model (b, sigma, tau) is held fixed.
  * Report hits and residual cosine against `no_memory` for all later queries and for the second half.

### Refusals and stopping

* `fresh-prepare` and `fresh-choose` refuse without a matching `FREEZE.json` (`FREEZE_MISSING`, `FREEZE_MISMATCH`).
* `fresh-evaluate` is one-shot (`ALREADY_EVALUATED`) and refuses altered choices (`CHOICES_TAMPERED`).
* No threshold, blend, decoder, prior or seed may change after the freeze. Any departure is logged in `DEVIATIONS.json`, which the freeze does not hash.

## L1000 analyses (exposed data; pre-specified, exploratory)

The Block Q sealed tier (702 GSE70138 compounds) was used once and is now exposed. These analyses explain; they do not confirm.

* **Question 2, no-anchor ceiling.** On active cells:
  * the best single-reference donor cosine (an oracle upper bound for analogue transfer);
  * regime-B accuracy binned by maximum Tanimoto to references;
  * the specific-direction similarity of the same compound across lines, compared with same-MoA, same-target, Tanimoto-at-least-0.6 and random reference pairs.

  Prediction: same-compound cross-line similarity far exceeds every between-compound relation, which bounds no-anchor transfer.
* **Question 5, learning curve.** RKT regime-B and A1 accuracy with the reference library subsampled to 1/8, 1/4, 1/2 and the full set (three subsamples each, frozen certifier). Fit accuracy against log2(library size), and convert the slope into the expected gain from admitting one campaign of sparse measurements.
* **Question 5, sequential memory.** Across the 11 Block Q campaigns, the fixed sparse-hub design at one well per compound. Arms:
  * no memory;
  * admitted measured cells, which become partial references;
  * shuffled admitted responses within line;
  * pseudo-label memory, which admits RKT fills as if measured: the self-training control.

  Endpoint: each later campaign's regime-B (pre-measurement) cosine on active cells, and map utility. Cluster: campaign.

## Costs

* Laboratory wells: 0. All outcomes are retrospective public records.
* Provider calls: 0.
* Downloads: 12 public GCP LVL3 plates (about 1 MB each).
