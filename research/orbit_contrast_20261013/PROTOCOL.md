# Protocol: orbit-contrast evidence admission (OCEA) on two perturbation tasks

Study folder: `research/orbit_contrast_20261013/`.

**Status.** Pre-registered on 2026-10-13, before any run of this study read an outcome.

* Every design choice below is fixed in this document. The development stage (S1) checks the
  machinery and computes power. It does not tune.
* Any change after S1 goes to `DEVIATIONS.json` before the freeze. The freeze does not hash that
  file.

The hypothesis, candidates and literature are in [CANDIDATES.md](CANDIDATES.md),
[LITERATURE.md](LITERATURE.md) and [INTERFACE.md](INTERFACE.md).

## 1. Data, exposure and authorisation

| Asset | Content | Exposure |
|---|---|---|
| `data/external/lincs_l1000_gse92742/derived/blockq_phase1.npz` | GSE92742 level-5 landmark consensus: 7,760 compounds (10 µM, 24 h) and 4,342 shRNA knockdown CGS signatures (96 h preferred), 9 core lines; vehicle signatures | Used in blocks M, N and Q (development) |
| `repurposing_drugs_20200324.txt` | Hub targets and MoA | Used in blocks Q and R |
| `mapkg_20261009/` | MAP-KG drug–gene edges | Used in blocks Q and R |
| `map_module_replacement_20261009/PROTEIN_FEATURES.npz` | ESM protein embeddings for 1,241 genes | Not used for prediction before |

* **Grade.** Every outcome here was exposed to earlier MAESTRO studies, although never to this
  method. The validation stage is therefore an internal held-out test on exposed data, of
  **exploratory replication grade, not confirmatory**.
* **Not touched.** PRISM 24Q2 stays sealed. Nothing is downloaded.
* **Costs.** No provider call is made: 0 wells, 0 turnarounds and 0 USD; only CPU time.

## 2. Tasks

* **A′. Cold-start compound response.**
  * Query: (compound d, line T), with d never profiled in any line.
  * Outcome: the landmark response centred by the mean of the training compounds in T.
  * Entities: compounds with at least one knowledge token (a Hub target or MoA, or a signed MAP-KG
    edge).
  * Primary population: test cells whose raw response norm exceeds the line's vehicle 95th
    percentile ("active", the block Q convention).
  * Secondary populations: all test cells; cells with a knockdown-covered target; the
    strict-new-mechanism stratum (no training compound shares any token).
* **B. Unseen-gene knockdown response.**
  * Query: (gene g, line T), with g never profiled.
  * Outcome: the knockdown CGS signature centred by the mean of the training genes in T.
  * Entities: all 4,342 knockdown genes.
  * Primary population: all test cells.
  * Secondary population: genes with at least one annotated compound measured in T.
* **C. Decision utility: target-hypothesis triage.** It does not substitute for A′ or B, and runs
  only under §9.

A′ is a transcriptional response, not viability. A viability version needs CRISPR dependency data,
which are not local (§10).

## 3. Splits and nesting

* **Folds.** fold(e) = int(sha256("orbit-contrast:" + key), 16) mod 5. The key is the compound key
  (A′) or the gene symbol (B).
* **Outer folds.**
  * Development (S1): fold 0 is the test set.
  * Validation (S2): folds 1–4, each tested once with the other four as training. Fold 0 is
    training-only in S2 and is never scored there.
* **Inner nesting**, within outer test fold k:
  * Route features for a training entity in fold j use references from folds other than j and k.
  * Test entities use references from all folds other than k.
  * The admission and certificate models give out-of-fold predictions for training entities. For
    fold j, they are fitted on the other training folds.
  * The stacker is fitted on those out-of-fold features.
* **Normalisers.** Centring means and the generic direction come from training entities only.
* **Cross-task evidence.** Knockdown signatures may serve as evidence in A′, and compound
  signatures in B, because they are not that task's outcome.

## 4. Routes, orbits and evidence

Evidence is read through `evidence.py`. Missing evidence makes a route unavailable; it is never
treated as zero evidence. Every orbit draw uses M = 16 relabellings per query with fixed
hash-derived seeds. Routes without an orbit are the non-knowledge baseline.

### Task A′ routes

| Route | Prediction | Orbit (acts on; strata; destroys) |
|---|---|---|
| generic | the line's generic direction (unit mean of unit active training responses) | — (base) |
| chem | Morgan Tanimoto kNN (k 10, power 2, floor 0.3) over training compounds in T | — (base) |
| know | Jaccard kNN (k 10, power 1, floor 0) over target and MoA tokens of training compounds in T | compound; token-count bin {1, 2–3, 4–7, ≥8} × has-Hub-target; which compounds share the query's mechanism |
| genetic | signed mean of knockdown signatures in T of the compound's signed targets (`knockdown_as_inhibition_proxy`; Hub sign, then MAP-KG inhibition +1 / activation −1, binding excluded) | gene, per line; landmark × annotated-compound degree {0, 1, 2–4, ≥5} × knockdown-norm tercile in T; which genes the compound acts on |

### Task B routes

| Route | Prediction | Orbit |
|---|---|---|
| generic | unit mean of unit training knockdowns in T | — (base) |
| self (positive control) | −e_g at the gene's landmark index; available for the 946 landmark genes | gene; other landmark genes; which transcript is knocked down |
| pharm | mean over compounds annotated to g and measured in T of sign × centred compound signature, weighted 1/(number of signed targets) | gene, per line; genes with ≥1 annotated compound in T; degree {1, 2–4, ≥5} × landmark; which compounds act on g |
| cotarget | Jaccard kNN (k 10, power 1) over shared-compound sets, among training genes with knockdown in T | gene, same strata as pharm; which genes share g's pharmacology |
| esm | cosine kNN (k 10, power 1, floor 0) over ESM-5120 embeddings, among training genes with knockdown in T | gene; ESM genes × landmark; which protein g is |

Strata with fewer than 5 genes or compounds fall back to the coarser key: the norm tercile is
dropped first, then the degree bin.

## 5. Arms

Every arm is fitted by the same stacker on the same training queries.

* **Stacker.** Vector least squares on the unit truth, Σ‖u(y) − Σ β_j X_j‖² + 1e-6‖β‖².
  * Each component is scaled by its route's training RMS norm.
  * Coefficients are pooled over lines.
  * Fit population: active training cells in A′, all training cells in B.

| Arm | Prediction |
|---|---|
| Z0 zero | systematic mean (ŷ = 0, cosine 0) |
| B0 base | generic (+ chem in A′) |
| O null-invariant | B0 + Σ_r ḡ_r |
| N naive | B0 + Σ_r f_r |
| C accuracy-certified (block Q practice) | B0 + Σ_r ρ̂_r⁺ f_r |
| R unconditional residual | O + Σ_r δ_r |
| C′ accuracy-gated residual | O + Σ_r ρ̂_r⁺ δ_r |
| **F OCEA** | **O + Σ_r ĉ_r⁺ δ_r** |
| F₋r | F without route r's residual (ablation) |

* **Notation.** ḡ_r is the orbit mean, δ_r = f_r − ḡ_r, and x⁺ = max(x, 0).
* **The two gates.** ĉ_r is the predicted identity contrast. ρ̂_r is the predicted route accuracy
  cos(f_r, y).
  * Both use the same descriptors and the same regressor: ridge on standardised descriptors, with
    alpha chosen by leave-one-fold-out from {0.1, 1, 10, 100}.
  * Training labels:
    * identity contrast, c_r = cos(f_r(K), y) − mean_m cos(f_r(π_m K), y);
    * accuracy, cos(f_r(K), y).
* **Descriptors.** None reads y or identity:
  * log support count, top and mean similarity;
  * ‖f‖, ‖ḡ‖, ‖δ‖ and the orbit spread, all over the route RMS;
  * the separation ‖δ‖ / spread;
  * cos(f, ḡ);
  * the route-specific counts (knockdown-covered targets, total targets, knockdown coherence);
  * the line one-hot.

## 6. Metric and statistics

* **Score.** The centred cosine per cell. An entity's score is the mean over its cells in the
  population.
* **Contrasts.** Paired over entities:
  * 95% CI by entity bootstrap (2,000 resamples, seed 20261013);
  * one-sided p by entity sign-flip (10,000 draws).
* **Identity-attributable accuracy.** Δ_id(X) = score(X) − score(O).
* **Multiplicity.** H1 is tested in two tasks, each at one-sided α = 0.025. All other contrasts
  are at α = 0.05 and are labelled secondary.

## 7. Hypotheses and gates (S2 validation, run once)

| Id | Statement | Pass rule |
|---|---|---|
| V1 positive control (B) | The self route's identity is detected | On landmark genes, Δ_id(F) − Δ_id(F₋self) > 0 with p < 0.001; held-out Spearman(ĉ_self, c_self) > 0 |
| V2 type-I (A′, B) | No identity credit for relabelled knowledge | R = 5 end-to-end global relabellings (stratum-preserving, the whole pipeline refitted): true Δ_id(F) > the maximum relabelled Δ_id(F), and the mean relabelled Δ_id(F) < 0.5 × the true Δ_id(F). Reported only if the true Δ_id(F) ≤ 0 |
| H1-A′ | Identity-attributable accuracy for cold-start compounds | Δ_id(F) > 0, p < 0.025 |
| H1-B | Identity-attributable accuracy for unseen genes, with non-trivial knowledge | Pipeline with pharm, cotarget and esm (self excluded): Δ_id(F) > 0, p < 0.025 |
| H2a | Admission beats no admission | score(F) − score(R) > 0, p < 0.05, in ≥1 task; not significantly negative in the other |
| H2b | Falsification supervision beats accuracy supervision | score(F) − score(C′) > 0, p < 0.05, in ≥1 task; not significantly negative in the other |
| H3 (A′, secondary) | Genetic knowledge beyond mechanism class | On the strict-new-mechanism stratum: score(F) − score(F₋genetic) > 0; report the CI (expected underpowered) |

Reported in every case:

* score(F) − score(C) and score(F) − score(N): F against current practice;
* the per-route ablations;
* the held-out Spearman of ĉ_r and of ρ̂_r with the realised c_r.

## 8. Biological falsification controls

These are pre-registered, run once in S2 on Task A′ (genetic and know routes) and Task B (pharm
route), and descriptive.

| Control | Manipulation | Expected if identity is real |
|---|---|---|
| Sign contradiction | Flip every target sign | Mean c_genetic falls, below 0 where it was > 0 |
| Context permutation | Use the evidence from a random other line T′ | Δ_id falls |
| Evidence withdrawal | Drop a random 50% of each query's target or compound records | Δ_id falls but stays ≥ 0 |
| Source snapshot | Hub 2020 only, without MAP-KG | Reported, no direction declared |
| Exclusion | Drop compounds with more than 16 signed targets | Δ_id holds |

## 9. Verdicts and stopping rules

| Verdict | Condition | Meaning |
|---|---|---|
| NO_GO_INSENSITIVE | V1 fails | OCEA cannot detect a known identity effect |
| NO_GO_LEAKY | V2 fails in a task with true Δ_id > 0 | OCEA credits generic signal to identity |
| METHOD_SUPPORTED | V1 and V2 pass; H1 passes in both tasks; H2a or H2b passes; neither H2 contrast is significantly negative | A new, general inference rule with evidence in two tasks |
| IDENTITY_WITHOUT_METHOD | H1 passes in ≥1 task; H2a and H2b both fail | The knowledge has identity value, but the rule adds nothing. **No methodological originality** |
| TASK_SPECIFIC | H1 passes in exactly one task, with H2 support | Generalisation not shown |
| NO_IDENTITY_VALUE | V1 and V2 pass; H1 fails in both tasks with power ≥ 0.8 at the MEI | Knowledge carries no identity-specific value here. OCEA is a falsification tool |
| INSUFFICIENT_EVIDENCE | H1 fails in a task whose power at the MEI is < 0.8 | — |

The minimal effect of interest (MEI) is Δ_id = 0.01 centred cosine in each task. Power is computed
in S1 from the per-entity SD of F − O.

**Mechanism-class rule (Brief 6).** In A′, suppose Δ_id(F) > 0 but every route except know
contributes nothing: F − F₋know carries the gain, and the CI of F − F₋genetic includes 0. Then the
functional-genetic-knowledge claim is reported as **MECHANISM_CLASS_ONLY**, whatever the method
verdict.

**Stopping rules.**

* S0 (synthetic estimator checks) must pass before S1.
* If V1 fails in S1, the study stops there with NO_GO_INSENSITIVE, and no validation is run.
* S2 runs once. Results are write-once.
* Task C runs only after METHOD_SUPPORTED, or after IDENTITY_WITHOUT_METHOD with H1-A′ passing.
* No paid model call is made in any stage. The Agent and LLM roles stay design-only (§11).

## 10. Task C (decision utility), designed and conditional

* **Decision.** For each held-out annotated compound profiled in at least one line, nominate 10
  candidate target genes for validation assays.
* **Cost and utility.** The cost is 10 assays per compound. The utility is the number of annotated
  targets among the 10 (hits per assay).
* **Arms:**
  * degree prior (popularity among training annotations);
  * raw signature–knockdown cosine (Pabon-style);
  * per-gene z against reference compounds (CMap-style);
  * orbit-contrast connectivity;
  * OCEA-admitted connectivity;
  * a zero arm with random genes.
* **Rule.** It is evaluated only under §9, with the same fold split, and it never substitutes for
  A′ or B.

## 11. Roles (design only)

* **Agent.** It owns queries, as-of dates, authorisation and budgets. It may request a route
  computation, and it may never edit evidence. It reports refusals verbatim.
* **Virtual Cell.** It owns routes, orbits, the decomposition and certificates. It returns
  `IDENTITY_NOT_ADMITTED` when every ĉ_r ≤ 0. The prediction is then the null-invariant model,
  labelled as generic.
* **Decision Engine.** It consumes only admitted identity residuals as mechanism evidence. Generic
  components may inform ranking, but may never be reported as mechanism.
* **LLMs.** No LLM component is activated before METHOD_SUPPORTED. Any later activation needs
  explicit authorisation. The deepseek-flash policy applies.

## 12. Deliverables

The deliverables are:

* `RESULTS_S1.json` (development);
* `POWER.json`;
* `FREEZE.json` (before S2);
* `RESULTS.json` (S2, write-once);
* `README.md` (answer, verdict, publication recommendation);
* `verify.py` (replays S0, the freeze and the result claims).
