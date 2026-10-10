# MAESTRO Research Report

As of 2026-10-10, MAESTRO has a verified operational agent–decision–virtual-cell loop and reproducible development experiments. **Independent scientific decision gain from knowledge feedback or an LLM policy is not established.** The latest advance qualifies the 39 endpoint coordinates in two source files; it does not validate feedback or release active procurement.

The [evidence register](EVIDENCE.md) owns cross-study numerical results. The [research index](INDEX.md) routes to detailed protocols and frozen receipts, and [scientific status](SCIENTIFIC_STATUS.json) records units, limitations and gates. Generated assets may be absent from a clean checkout. `python -m tools.research_validation --verify` must report missing or mismatched assets rather than substitute outcomes.

The 2026-10-10 phenotype-anchored study evaluated Tahoe relative-survival selectivity and phase
shift on five checkpoint-held-out lines, using phenotypes measured in the same spheroids as RNA.
For survival selectivity, basal-similarity transfer beat STATE (delta r -0.23); a perfect RNA
oracle added only 0.003 r over the prior on reference lines, below the registered 0.05 minimum
useful benefit. The gate refused STATE for this endpoint, and held-out oracle results supported
that refusal. STATE's distinct held-out signal was predicted-cell G1 composition (+0.25 r on E2).
This scoped result does not establish apoptosis, mechanism or general decision value. See the
[canonical evidence](EVIDENCE.md#phenotype-anchored-dual-core--2026-10-10) and
[study packet](astra/phenotype_anchor_20261010/README.md).

Block K (2026-10-10) asked when a virtual cell's forecast of the early state can replace measuring
it for a later-fate decision. It separated three possible failures: no ceiling, no transport and
wrong timing. All three appeared.

* **Transport.** On 48 MIX-Seq lines unseen by STATE, the forecast harmed a DepMap-scale prior
  for 5-day PRISM viability (-0.091 [-0.182, -0.005]). Its line-specific RNA skill was about 0.
  The same lines' observed Tahoe and MIX-Seq responses agreed at r of 0.13 or less, while two
  MIX-Seq experiments agreed at 0.65. What STATE learned about lines is bound to its platform.
* **Measurement.** The development gate's MEASURE_EARLY call (+0.139 on 24 lines) did not confirm
  (-0.021 [-0.109, +0.078]). Its post hoc interval was [-0.049, +0.298].
* **Timing.** In a trametinib time course, 5-day information appeared at 24-48 h; only 48 h added
  to the prior. STATE's 24 h forecast matched the 12 h response best.
* **Prior wins.** For Tahoe, the early state did not add to the CCLE prior.

Gate decisions now use interval lower bounds (`plan_measure_or_predict`, which can abstain). See
the [block K evidence](EVIDENCE.md#measure-or-predict-across-platform-and-time--2026-10-10) and
[packet](astra/kinetic_horizon_20261010/README.md).

Block M (2026-10-10) asked whether the agent and a world model can **falsify** mechanism
hypotheses with a calibrated error rate. The test used 424 Repurposing Hub classes, 502 sealed
L1000 drugs and four profiles per drug. Three findings:

* **Calibration is necessary but not yet sufficient.**
  * Neither the agent's own eliminations nor likelihood elimination is a falsification test. The
    agent alone kept the true mechanism in 0 of 100 drugs, and 90% credible sets in 22%.
  * A conformal test with relative scores, energy bins and episode-calibrated adaptive design
    covered 0.892 on average.
  * It failed the registered rule on the most active drugs (0.776, n 49), exactly where sets
    shrink.
* **The world model's class content falsifies** (19 fewer survivors than shuffled labels). It
  ranks mechanisms no better than class-mean cosine, and like kNN-1 with four profiles.
* **No agent contribution survived its controls.**
  * Literature, critique, analogies and hypothesis content were tested, and a generic prototype
    did as well.
  * Neither planner reduced sets: the expected-survivor planner nor agent-chosen observations.
  * The agent reading p-values lost coverage.
  * Identifiability prediction matched a pair-blind baseline.
  * The test never declared a hypothesis set inadequate.

Nothing was promoted. See the
[block M evidence](EVIDENCE.md#calibrated-falsification-of-mechanism-hypotheses--2026-10-10) and
[packet](astra/mechanism_falsification_20261010/README.md).

A forecast may influence endpoint selection only after a same-unit readout-to-endpoint bridge
(same culture unit, dose and time) and a reference ceiling pass: substitute observed responses
for forecasts, score leave-one-context-out, and beat the best cheap prior by the declared minimum
useful benefit. Passing admits evaluation; it does not certify the forecast. Unsupported
cross-assay, cross-dose or cross-time bridges and undercounted contexts are refused.

The current endpoint is a signed 39-gene RNA response. It does not establish functional phenotype, protein activity, causal mechanism, clinical efficacy or the value of an experiment. Five target cell backgrounds in the current STATE studies were previously exposed, and reference contexts overlap STATE pretraining.

## What has passed

The operational contracts cover condition-bound requests, bounded execution, result persistence, feedback and restart. Historical STATE prediction evidence records approximately 41% lower RNA error than an empirical baseline across three checkpoint-held-out contexts. Later readout repair improves reference MSE by 2.17% and exposed-target MSE by 7.84%, without changing final equal-budget selections. These recorded prediction results do not establish independent decision value; source recovery requirements remain in the evidence register.

The separately registered P0.5R extension uniquely matches **39/39 coordinates in c44 and c45** against all **62,710 source genes** with unchanged `log1p(stored normalized X)` and `1e-5` tolerance. Maximum differences are 1.4416e-7 and 1.4611e-7. c44 reuses 252 exposed cells and adds zero RNA bytes; without nine previously read consistency cells, its 243-cell subset still aliases TNF and SDK2. c45 receives exactly **133,564 bytes** for eleven frozen discriminating cells, 60.7% less new expression payload than the earlier 340,068-byte proposal. MILP minimality applies only to the retained pool and binary alias constraints.

An initial parser failure is preserved. A separately frozen offline repair uses already received bytes; a distinct logical-slice/blockwise arithmetic implementation agrees. Old protected studies remain unchanged. This is historical/adaptive file-local identity evidence, not a fresh holdout or biological confirmation. The [extension receipt](../log/20261010/P05R_EXTENSION.json) records execution, cost and reproduction.

## What has failed or remains unqualified

MAP known-target retrieval is useful content evidence but does not reliably exceed Morgan or simple controls. Generic outgoing molecule–relation–protein fusion fails its primary retrieval gate; incoming and name-anchored results remain separate known-graph findings. Native MAP RNA comparison is blocked by output-axis and training-forward authentication, not solved by restoring embedding weights.

Sparse-history MAP feedback exceeds empirical feedback by 11.17% at eight histories but not reliably Morgan, molecule, shuffled knowledge or no-screen. In the condition-bound pairwise study, knowledge+feedback regret is **0.00653089 versus 0.00640195** for no-update, with **43 corrected and 51 harmful flips**; the registered gate fails. All 6,192 policy rows have recorded separate reconstruction.

V3 reconstructs all 3,870 rows, but feedback adds only **0.0000128654** terminal B utility over mean-only: nominal 95% CI **[-0.0000130981, +0.0000388290]**, Holm p=0.48456. No-update remains slightly better. Empirical and MAP residual banks select identical final sets; transfer and knowledge-attribution gates fail. Prebuy stopping reduces A purchases from 129 to 35 without changing matched-arm actions. Simulated total profiles fall 774→680; no-update costs 645. This supports avoiding unused purchases, not positive net information value or agent superiority.

On difficult source tasks, lexical LLM and typed MAP+LLM complete 27/72 and 26/72 packages; deterministic same-tool routing completes 72/72. Actual provider usage is 456 calls and 932,407 tokens; monetary cost is unauthenticated. These repeated source cases are not independent biological units. The risk study certifies no conditional threshold and obtains only 2.6–3.4% marginal coverage, below its 20% gate.

## Current gate and next step

Original P0.5/P0.5R failures remain frozen: control-only matching was 27/39 c40 and 34/39 c44; the later compact panel was 16/39 c44 and 23/39 c45. The extension changes only the qualified c44/c45 data-coordinate prerequisite. It does not certify the complete 2,000-gene dataset axis or STATE checkpoint output order. The old c40/c44 250-cell noise plan is still blocked.

The next eligible research task is a **new frozen P0.6 observation-reliability protocol**. Bind exact source revision, endpoint coordinates, exclusions, treated/control rows, actual group sizes, reference weights, shared-control uncertainty, source-repeat estimands and exact acquisition costs before reading expression. The proposed 24 line/plate treatment strata represent **12 pooled samples**, not 24 independent cultures. Source-wide 24-hour exposure is documented; per-sample timestamps and a third confirmation source remain absent. See [P0.6 readiness](decision_value/axis_extension_20261010/P06_READINESS.md).

P0.6 execution is not released, P2 remains closed, and experimental feedback stays in research. Stable A-to-B transfer, beneficial final selection, harms, authenticated costs and untouched qualifying biological units are separate future gates. The endpoint remains an equal positive `+1/39` RNA expression-change mean, not viability, apoptosis, protein engagement or mechanism causality.
