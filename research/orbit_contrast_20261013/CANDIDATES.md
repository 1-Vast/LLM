# Deliverables B and C: competing algorithmic hypotheses, ranking and selection

## Why earlier approaches failed

This section reconstructs, from the MAESTRO record, why knowledge-conditioned prediction has not
held up.

* **Knowledge reality (PRISM viability).** Knowledge added +0.0056 r over chemistry for unseen
  compounds.
  * Relabelling genes within degree, variance and mutation strata reproduced the whole gain
    (p 0.95).
  * The gain was mechanism-class membership (which compounds share annotations), not target
    biology.
  * On compounds whose targets no training compound shares, the gain was +0.0007.
* **Block Q (RKT, L1000).** Typed routes with per-query certificates.
  * With no profiled line, knowledge analogues added little over the generic direction: 0.360
    against 0.287.
  * The genetic route was not admitted. On development, its specific cosine was 0.025 for
    knockdowns and 0.078 for CRISPR at 19% coverage.
  * The certificate predicts route accuracy. It cannot say whether the accuracy comes from the
    entity's identity.
* **Agents.** Agent loops and LLM arms were null or harmful against fixed workflows (blocks P, Q,
  triage).
  * The Agent–Virtual Cell framework adds no decision utility when the Virtual Cell's evidence is
    itself generic.

The common defect: every pipeline credited knowledge by its marginal accuracy gain. A generic gain
(sparsity, degree, mechanism-class smoothing, consensus-signature artefacts) is indistinguishable
from an identity-specific one unless the null is part of the method. Literature §4 shows the same
pattern in the field.

## Candidates

### H1. OCEA: orbit-contrast evidence admission (falsification-calibrated evidence use)

**Algorithm.**

* **Setting.**
  * A query is q = (entity e, context c). The outcome y_q is a centred response vector.
  * A route r turns knowledge K into a prediction f_r(q; K).
  * Each route declares a semantic group Π_r: relabellings of the identities its claim relies on,
    restricted to declared nuisance strata (degree, coverage, signature strength, landmark status).
* **Orbit decomposition.**
  * Sample M relabellings π_m of the query's knowledge record.
  * Generic part: ḡ_r(q) = mean_m f_r(q; π_m K).
  * Identity residual: δ_r(q) = f_r(q; K) − ḡ_r(q).
* **Falsification label** (training queries only). The identity contrast is
  c_r(q) = cos(f_r(q; K), y_q) − mean_m cos(f_r(q; π_m K), y_q).
* **Admission model.**
  * ĉ_r(q) = E[c_r | φ_r(q)] is fitted with out-of-fold labels.
  * The descriptors φ_r(q) never read y or the entity's identity:
    * route support;
    * the orbit separation ‖δ_r‖ / orbit spread;
    * cos(f_r, ḡ_r);
    * norms;
    * the line.
* **Prediction.** ŷ(q) = base(q) + Σ_r v_r ḡ_r(q) + Σ_r λ_r max(ĉ_r(q), 0) δ_r(q).
  * The coefficients come from vector least squares on unit truth, with out-of-fold features.
  * The generic terms are kept, and credited to the null-invariant model.

**Inputs and outputs.**

* In: typed evidence records (see [INTERFACE.md](INTERFACE.md)), training outcomes and the strata
  declarations.
* Out:
  * the prediction;
  * the generic/identity split per route;
  * a per-query identity certificate ĉ_r(q);
  * a named refusal `IDENTITY_NOT_ADMITTED` when every ĉ_r ≤ 0.

**Novelty claim, and where related work conflicts** ([LITERATURE.md](LITERATURE.md) §8). The null
becomes part of the estimator and the supervision, not a post-hoc diagnostic. Conflicts:

* Model-X CRT and knockoffs (global tests);
* Systema (outcome-side decomposition);
* randomised-graph controls (diagnostics);
* MoE gating and the block Q certificate (accuracy-supervised).

**Data, compute, identifiability.**

* Data: local L1000 phase-1 compound and knockdown signatures, Hub and MAP-KG annotations, ESM
  protein features.
* Compute: CPU minutes per task (M orbit draws × kNN routes).
* Identifiability: c_r is identified only when the strata make the orbit exchangeable with the
  real record on everything except identity. A stratum mismatch puts generic signal into δ, which
  the end-to-end relabelled pipeline (F1 below) detects.

**Two decisive failure tests.**

* **F1.** Run the whole pipeline on globally relabelled knowledge, refitting the admission model.
  * Expected: Δ_id ≈ 0, and the true Δ_id above every relabelled run.
  * If the relabelled pipelines reach the true Δ_id, OCEA attributes generic signal to identity.
    It is then **rejected**.
* **F2.** OCEA must beat both of its ablations on held-out queries:
  * the unconditional residual (admission removed);
  * the accuracy-supervised gate (block Q-style certificate on the full route).
  * If it beats neither, falsification supervision adds nothing. The method contribution is
    **rejected**, and at most the decomposition survives as an evaluation device.

**Positive control.** Under knockdown, a landmark gene's own transcript falls. That self-identity
route must be admitted and must yield Δ_id > 0. If not, OCEA is insensitive.

**Generalisation scope.** Any predictor that consumes labelled relational knowledge:

* genes, targets and pathways in biology;
* materials and element identities;
* retrieved documents for an LLM, where the orbit is shuffled-entity retrieval.

This study tests two biological tasks only.

### H2. ITT: intervention-type transport (intervention-aligned representations)

**Algorithm.**

* Learn, per line T, a reduced-rank map W_T from knockdown-signature space to compound-signature
  space: y_d ≈ W_T Σ_g s_dg KD_T[g], fitted on annotated training compounds.
* The map models that a knockdown is not an inhibition: partial versus complete loss, scaffold
  versus catalytic function, 96 h versus 24 h.
* Variant: inverse transport, compound to knockdown, for unseen genes.

**Inputs and outputs.** In: knockdown signatures, signed target annotations and compound
signatures. Out: a predicted compound signature.

**Novelty.** Weak.

* LPM, X-Pert and PertOmni already align chemical and genetic perturbations in shared spaces.
* Pabon et al. and DeepTarget use the same linkage for target inference.

**Data, compute, identifiability.**

* Data: about 1,400 compounds with knockdown-covered targets.
* Compute: a 978 × 978 map, so it needs rank ≤ 20.
* Identifiability: W_T can learn the generic "knockdown-like to drug-like" shift without using the
  target's identity.

**Two decisive failure tests.**

1. A map trained on relabelled targets matches the real map. The map is then generic: rejected.
2. On strict-new-target compounds the real map does not beat the generic direction. There is then
   no transport: rejected.

**Scope.** Genetic to pharmacological, L1000 only.

### H3. EQMT: evidence-qualified mechanism transfer

**Algorithm.** Mechanism-class analogues (shared targets and MoA) weighted by evidence quality:

* provenance tier (curated, assay text, binding);
* availability time;
* relation sign;
* potency.

**Inputs and outputs.** In: typed edges with provenance. Out: a weighted analogue prediction.

**Novelty.** Low. This is MAP-KG weighting plus RKT's know route. Knowledge reality already found
that relation typing and provenance weighting add nothing measurable on viability.

**Data, compute, identifiability.**

* Data: Hub plus MAP-KG.
* Compute: trivial.
* Identifiability: by construction it can only recover mechanism-class similarity, which Brief 6
  says to reject as the main claim.

**Two decisive failure tests.**

1. Gain over unweighted analogues ≤ 0.
2. The gain is reproduced by shuffling the weights across edges within tiers.

**Scope.** Wherever curated mechanism annotations exist.

### H4. DAA: decision-aware acquisition

**Algorithm.**

* Choose which (compound, line) cells to profile so that the downstream decision gains most:
  * which compounds to advance;
  * which target hypothesis to test.
* Use expected value of information under the predictor's identity certificates.
* Decision-focused training of the stacker.

**Inputs and outputs.** In: a predictor with calibrated certificates, a budget in wells and a
utility. Out: an acquisition plan and its expected utility in wells and turnarounds.

**Novelty.** Moderate as a combination. Bayesian experimental design and decision-focused learning
are established.

**Data, compute, identifiability.**

* Block Q found the certificate planner lost to a fixed sparse design at budget N, and won at 2N.
* The value depends on a predictor whose identity part is real, so it is downstream of H1.

**Two decisive failure tests.**

1. No gain over a fixed sparse design at equal wells.
2. The gain is reproduced with relabelled-knowledge certificates.

**Scope.** Any campaign with a profiling budget.

## Ranking

The scale is 1–5; higher is better.

| Criterion | H1 OCEA | H2 ITT | H4 DAA | H3 EQMT |
|---|---|---|---|---|
| Novelty, against [LITERATURE.md](LITERATURE.md) | 3 (new inference rule, known parts) | 1 | 2 | 1 |
| Directly addresses the failure mode (generic gain credited as knowledge) | 5 | 3 | 1 | 1 |
| Falsifiable on local exposed data, without new downloads | 5 | 5 | 3 | 5 |
| Has a positive control | 5 (knockdown self-effect) | 2 | 1 | 1 |
| Generality beyond this domain | 5 | 2 | 4 | 2 |
| Depends on another candidate succeeding | no | no | yes (H1) | no |
| **Rank** | **1** | 2 | 3 | 4 |

H2 is subsumed as a route inside H1's Task A′ test. A learned map would add parameters without a
new principle, so only the direct genetic route is tested. H4 is designed (Task C in
[PROTOCOL.md](PROTOCOL.md)) but runs only if H1 passes. H3 is not pursued.

## Selected hypothesis (deliverable C)

> **OCEA.** For knowledge-conditioned prediction of perturbation responses, crediting and using
> knowledge only through its stratum-preserving relabelling-orbit residual, admitted per query by
> a model trained on held-out identity contrasts, yields:
>
> * (i) accuracy attributable to entity identity (Δ_id = OCEA − null-invariant model > 0) on
>   unseen entities in two distinct tasks, namely cold-start compound responses (A′) and
>   unseen-gene knockdown responses (B);
> * (ii) more Δ_id than the same decomposition without admission, or with accuracy-supervised
>   admission;
> * (iii) zero Δ_id when the knowledge is relabelled end to end.

This is the single new inference rule. If (ii) fails, the study reports that there is **no
methodological originality**, whatever the accuracy. If (i) fails while (iii) passes, the
knowledge has no identity-specific value on these tasks. The decomposition then serves as a
falsification tool, not as a better predictor.
