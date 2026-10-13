# Orbit-contrast evidence admission: is knowledge credited for identity, and does a falsification-calibrated rule use it better?

Study folder: `research/orbit_contrast_20261013/`. Brief 6 governs.

* **Status.**
  * Pre-registered and frozen before validation (21 files).
  * The single validation stage (S2, outer folds 1–4) ran once.
  * Task C ran once under a hashed addendum.
  * Every number below is recomputed from the result files by `verify.py`.
* **Grade.** Exploratory replication. Every outcome was exposed to earlier MAESTRO studies, though
  never to this method.
* **Recommendation.**
  * **NO-GO** for OCEA as a method, and for any agent or LLM layer on top of it.
  * The orbit decomposition is kept as an evaluation device.
* **Cost.** 0 wells, 0 turnarounds, 0 provider calls and 0 USD. No dataset was downloaded; only
  Figshare file metadata was read. CPU time:
  * about 63 minutes for S2, plus 54 minutes for the crashed first attempt (D4);
  * 75 seconds for Task C.

## 0. The answer

**The verdict.**

> Verdict: IDENTITY_WITHOUT_METHOD

> Functional-genetic-knowledge claim: MECHANISM_CLASS_ONLY

> Task C decision: NOT_SUPPORTED

Read under the frozen rules (`verdict.py`, PROTOCOL §9), these mean:

* **Knowledge does carry identity-specific value for cold-start compounds.**
  * On 392 held-out compounds, none of them profiled in any training fold, real knowledge beats
    the null-invariant model built from its own relabelling orbit.
  * The value is mechanism-class membership: which compounds share target and MoA annotations.
  * Relabelled knowledge earns nothing, end to end.
  * The positive control is detected.
* **The rule adds nothing, so there is no methodological originality.**
  * Admitting identity residuals per query, with a gate trained on falsification contrasts, is
    worse than using them unconditionally (H2a significantly negative in A′).
  * It is no better than an accuracy-trained gate (H2b).
  * The identity gate predicts the realised identity contrast no better than the accuracy gate on
    any route.
* **Functional genetic knowledge adds nothing beyond mechanism class.**
  * The knockdown route transports signed target knockdowns. Its signal is real: flipping the
    target signs reverses its identity contrast.
  * It adds no accuracy once mechanism class is used.
  * In unseen-gene knockdown prediction (B), pharmacology, co-targeting and protein-embedding
    knowledge carry no identity value, with power 1.00 at the minimal effect of interest.
* **No decision utility.**
  * In target triage, connectivity between a compound's signature and knockdown signatures,
    orbit-calibrated or not, nominates targets at about the random rate.
  * Training-annotation degree does better, and chemical-neighbour target transfer far better.

For Brief 5's final call, see §9.

## 1. Deliverables map

| Brief 6 deliverable | Where |
|---|---|
| A. Literature map and novelty audit | [LITERATURE.md](LITERATURE.md) |
| B. Competing hypotheses, specifications, failure tests, ranking | [CANDIDATES.md](CANDIDATES.md) |
| C. Selected hypothesis | [CANDIDATES.md, selected hypothesis](CANDIDATES.md#selected-hypothesis-deliverable-c) |
| Domain-general query and evidence interface | [INTERFACE.md](INTERFACE.md), implemented in [evidence.py](evidence.py) |
| D. Implementation | [sources.py](sources.py), [routes.py](routes.py), [ocea.py](ocea.py), [run.py](run.py), [run_s2.py](run_s2.py), [taskc.py](taskc.py) |
| E. Pre-registered protocol | [PROTOCOL.md](PROTOCOL.md), [verdict.py](verdict.py), [TASK_C.md](TASK_C.md), [FREEZE.json](FREEZE.json), [DEVIATIONS.json](DEVIATIONS.json) |
| F. Results | §0 and §3–§7; [RESULTS.json](RESULTS.json), [RESULTS_C.json](RESULTS_C.json), [CLAIMS.json](CLAIMS.json) |
| G. Publication recommendation | §8 |

## 2. The method in one page

**The defect it targets.**

* Every earlier MAESTRO pipeline credited knowledge by its marginal accuracy gain.
* In block Q and in knowledge reality, a relabelling that keeps degree and sharing structure
  reproduced that gain.
* An accuracy certificate cannot tell whether an accurate route owes its accuracy to generic
  structure or to the entity's identity.

**The rule: OCEA, orbit-contrast evidence admission.** For each knowledge route r:

1. Predict with the real knowledge, f_r, and with M = 16 stratum-preserving relabellings of it.
   * The relabellings keep each entity's stratum: degree bin, landmark status, knockdown
     strength, annotation count.
   * They therefore keep what is generic about the knowledge and destroy identity.
2. Split the prediction into two parts.
   * The orbit mean ḡ_r is the generic part. It enters every arm, including the null-invariant
     reference O.
   * The residual δ_r = f_r − ḡ_r is the identity part.
3. On inner folds, label each training query with its identity contrast,
   c_r = cos(f_r, y) − mean_m cos(f_r(π_m K), y). Fit a ridge model ĉ_r on label-free
   descriptors: support, similarity, norms, orbit spread, separation, line.
4. Predict O + Σ_r λ_r max(ĉ_r, 0) δ_r, with λ stacked by least squares on training queries.

**Scoring.**

* Δ_id(X) = score(X) − score(O): the accuracy that only identity can explain.
* The rule is a contribution only if it beats the same decomposition without admission (R) and
  with an accuracy-supervised gate (C′).

**The tasks.** L1000 GSE92742, landmark genes, centred cosine. All data are local and exposed.

* **A′, cold-start compounds.** Unseen compounds, 10 µM, 24 h, 9 core lines.
  * Primary population: active cells, whose response norm exceeds the line's vehicle 95th
    percentile.
  * Base: the line's generic direction plus Morgan-fingerprint neighbours.
  * `know` route: Jaccard over Hub and MAP-KG target and MoA tokens, i.e. mechanism class.
  * `genetic` route: signed knockdown responses of the compound's targets in the same line,
    through the declared `knockdown_as_inhibition_proxy` transport.
* **B, unseen-gene knockdown.** Consensus shRNA knockdown signatures of genes held out by fold.
  * `self`: −1 at the gene's own landmark coordinate, for the 946 landmark genes. This is the
    positive control.
  * `pharm`: responses to compounds that target the gene.
  * `cotarget`: knockdowns of genes that share compounds.
  * `esm`: protein-sequence-embedding neighbours.
  * The hypothesis pipeline (B non-trivial) excludes `self`.

**Splits.**

* Entities are hashed into 5 folds.
* Fold 0 was development (S1). Folds 1–4 were scored once (S2), after the freeze.
* Gates and stackers are cross-fitted on inner folds only.

## 3. Gates (S2, run once)

Populations:

* A′ primary population: 392 compounds, 805 active cells
* B primary population: 3481 genes, 24787 cells
* S0 synthetic check: PASS
* Power at MEI 0.01 (S1), A′ / B: 0.97 / 1.00

| Gate | Result | Reading |
|---|---|---|
| V1 positive control | V1 positive control (landmark self-knockdown), F − F₋self: +0.0998 [+0.0884, +0.1114], p < 0.0001 | pass |
| V1 gate check | V1 identity-gate Spearman with the realised self contrast: 0.160 | pass (> 0) |
| V2 type-I, A′ | V2 A relabelled Δ_id(F), 5 runs, mean and max: -0.0002 / -0.0001 | pass: relabelled knowledge earns nothing |
| V2 type-I, B | V2 B relabelled Δ_id(F), 5 runs, mean and max: -0.0002 / -0.0000 | pass |
| H1-A′ | H1-A Δ_id(F) = F − O: +0.0104 [+0.0074, +0.0140], p < 0.0001 | **pass** |
| H1-B | H1-B Δ_id(F) = F − O: +0.0005 [-0.0004, +0.0014], p 0.1475 | fail, powered |
| H2a-A′ | H2a-A F − R: -0.0045 [-0.0071, -0.0019], p 0.9998 | **fail, significantly negative** |
| H2a-B | H2a-B F − R: -0.0001 [-0.0007, +0.0006], p 0.5710 | fail |
| H2b-A′ | H2b-A F − C′: +0.0001 [-0.0002, +0.0004], p 0.2863 | fail |
| H2b-B | H2b-B F − C′: -0.0001 [-0.0002, +0.0001], p 0.7907 | fail |
| H3 (secondary) | H3 strict-new F − F₋genetic: -0.0004 [-0.0023, +0.0007], p 0.5976 | no genetic value for new mechanisms |

H3 is measured on this stratum: A′ strict-new-mechanism stratum: 19 compounds, 31 cells

The development value agreed with validation: S1 development A′ Δ_id(F): +0.0091 [+0.0007, +0.0204], p 0.0311

## 4. Where the identity value sits

**Task A′, mean centred cosine.** A mean centred cosine B0 / O / N / F: 0.4365 / 0.4374 / 0.4519 / 0.4479

* **The generic part of the knowledge adds almost nothing:**
  A O − B0 (orbit means over base): +0.0010 [+0.0005, +0.0015], p < 0.0001
* **The naive integration's whole gain is identity-attributable:**
  A N − O (naive identity gain): +0.0145 [+0.0098, +0.0195], p < 0.0001
  * Contrast knowledge reality on PRISM viability, where a gene relabelling reproduced the whole
    gain.
  * Here the `know` orbit relabels which compounds share annotations. The true pairings carry
    the signal.
* **The value is mechanism class:**
  * A′ F − F₋know: +0.0099 [+0.0069, +0.0133], p < 0.0001
  * A′ F − F₋genetic: +0.0005 [-0.0001, +0.0011], p 0.0554
  * On the cells where the genetic route has coverage:
    A′ knockdown-covered active cells, F − F₋genetic: +0.0007 [-0.0001, +0.0016], p 0.0650
* **How the frozen rule reads this.** The `know` ablation carries ≥ 0.5 × Δ_id(F), and the
  genetic ablation's CI includes 0, so the functional-genetic claim is MECHANISM_CLASS_ONLY.
* **Secondary populations** (RESULTS.json, not separately gated):
  * all 9,335 test cells: Δ_id(F) +0.0032;
  * without promiscuous compounds (> 16 signed targets): +0.0107.
  * On all cells, the genetic ablation reaches +0.0003 [+0.0002, +0.0005]: real, and about
    1/30 of the MEI.

**Task B (non-trivial pipeline).** B mean centred cosine B0 / O / N / F: 0.0462 / 0.0459 / 0.0467 / 0.0464

* B N − O (naive identity gain): +0.0007 [-0.0002, +0.0016], p 0.0543
* B O − B0 (orbit means over base): -0.0003 [-0.0007, +0.0002], p 0.8784
* Route ablations:
  * B F − F₋pharm: +0.0001 [-0.0000, +0.0003], p 0.0433
  * B F − F₋cotarget: +0.0003 [-0.0004, +0.0010], p 0.2163
  * B F − F₋esm: +0.0000 [-0.0004, +0.0005], p 0.4753
* On genes with an annotated compound measured in the line:
  B pharm-available cells, F − F₋pharm: +0.0006 [-0.0004, +0.0016], p 0.1121
  * On these 730 genes, Δ_id(F) is +0.0048 (p 0.033), secondary and uncorrected.
  * At most, pharmacology helps the minority of genes that have drugs.

## 5. Does the rule add anything?

**No. OCEA against current practice, in A′:**

* A F − C (accuracy-certified full routes): +0.0007 [+0.0001, +0.0013], p 0.0081
* A F − N (naive integration): -0.0041 [-0.0067, -0.0014], p 0.9991

**The same in B:**

* B F − C (accuracy-certified full routes): -0.0003 [-0.0007, +0.0002], p 0.8860
* B F − N (naive integration): -0.0002 [-0.0009, +0.0005], p 0.7262

**Why.** In A′, the unconditional residual R reaches Δ_id +0.0150, and the naive N reaches
+0.0145.

* The gate admits 94% of `know` queries. It weights each admitted residual by a per-query
  estimate that tracks the realised contrast only weakly (Spearman 0.139).
* Against a constant weight, that costs about a third of the identity gain.

**The certificates show why the gate cannot do better.** Its supervision, the identity contrast,
is no more predictable from label-free descriptors than accuracy is.

* A know gate Spearman with realised contrast, identity / accuracy: 0.139 / 0.129 (mean contrast +0.0949, admitted 0.94)
* A genetic gate Spearman with realised contrast, identity / accuracy: -0.021 / -0.007 (mean contrast +0.0124, admitted 0.80)
* B pharm gate Spearman with realised contrast, identity / accuracy: -0.009 / -0.019 (mean contrast +0.0079, admitted 0.85)
* B cotarget gate Spearman with realised contrast, identity / accuracy: -0.003 / 0.002 (mean contrast +0.0079, admitted 0.67)
* B esm gate Spearman with realised contrast, identity / accuracy: -0.000 / 0.015 (mean contrast +0.0051, admitted 0.51)
* Bfull self gate Spearman with realised contrast, identity / accuracy: 0.160 / 0.160 (mean contrast +0.1221, admitted 1.00)
* Bfull pharm gate Spearman with realised contrast, identity / accuracy: -0.009 / -0.019 (mean contrast +0.0079, admitted 0.85)
* Bfull cotarget gate Spearman with realised contrast, identity / accuracy: -0.003 / 0.002 (mean contrast +0.0079, admitted 0.67)
* Bfull esm gate Spearman with realised contrast, identity / accuracy: -0.000 / 0.015 (mean contrast +0.0051, admitted 0.51)

**Conclusion.** The decomposition does what it promises: V1 and V2 pass, and the identity
contrasts are positive and sign-sensitive. The per-query admission is the part that fails. The
claim that survives is an evaluation device, not a better predictor.

## 6. Biological falsification controls (descriptive, run once in S2)

* **Sign contradiction:** Sign contradiction, mean genetic contrast real → flipped: +0.0291 → -0.0303
  * The genetic route's identity is directional. Inhibitors look like their targets' knockdowns,
    and the opposite sign looks like the opposite.
  * So the knockdown transport is biologically meaningful. It is redundant with mechanism class
    for prediction.
* **Context permutation:** A′ context permutation, Δ_id(F) variant vs real: +0.0095 vs +0.0104
  * Reading knockdowns from another line costs little, because the value sits in `know`, which
    has no line context.
* **Evidence withdrawal:** A′ evidence withdrawal, Δ_id(F) variant vs real: +0.0071 vs +0.0104
  * Δ_id falls but stays positive, as expected if identity is real.
* **Source snapshot:** A′ Hub-2020 snapshot, Δ_id(F) variant vs real (same compounds): +0.0120 vs +0.0117
  * MAP-KG (2026) adds nothing over the Hub 2020 annotations.
* **B context permutation:** B context permutation, Δ_id(F) variant vs real: +0.0007 vs +0.0005
* **B evidence withdrawal:** B evidence withdrawal, Δ_id(F) variant vs real: +0.0005 vs +0.0005
  * B's pharmacology has no line-specific signal, and withdrawing half its evidence changes
    nothing.

## 7. Task C: decision utility (target-hypothesis triage)

**Why it ran.** PROTOCOL §9 permits Task C after IDENTITY_WITHOUT_METHOD with H1-A′ passing.

**How it was locked.** [TASK_C.md](TASK_C.md) fixed its definitions after the S2 verdict and
before any Task C number. D5 hashes the addendum and its code.

**The decision.** Nominate 10 knockdown genes per held-out annotated compound for a validation
assay. Every arm spends 10 assays per compound.

**Population and hits:**

* Task C units (all): 1148 compounds, 3.04 annotated targets each
* Task C hits@10 (all) Z0 / P / H / X / Zc / OC / F: 0.0122 / 0.4338 / 0.9843 / 0.0174 / 0.0166 / 0.0192 / 0.1864
* Task C units (active): 276 compounds, 3.43 annotated targets each
* Task C hits@10 (active) Z0 / P / H / X / Zc / OC / F: 0.0109 / 0.2935 / 0.9928 / 0.0435 / 0.0362 / 0.0435 / 0.0978

The arms are:

* Z0: random;
* P: training-annotation degree;
* H: chemical-neighbour target transfer;
* X: raw connectivity;
* Zc: CMap-style z;
* OC: orbit-contrast connectivity;
* F: OCEA-admitted, falling back to P.

**Primary contrasts:**

* Task C (all) C1 F-Zc: +0.1699 [+0.1359, +0.2056], p < 0.0001
* Task C (all) C2 OC-X: +0.0017 [-0.0026, +0.0070], p 0.3677
* Task C (active) C1 F-Zc: +0.0616 [+0.0181, +0.1123], p 0.0053
* Task C (active) C2 OC-X: +0.0000 [-0.0145, +0.0145], p 0.6847

**C1 is positive only because F falls back to the degree prior** when the gate does not admit. The
pre-registered guard catches this:

* Task C (all) F-P: -0.2474 [-0.2883, -0.2090], p 1.0000
* Task C (all) F-H: -0.7979 [-0.8728, -0.7256], p 1.0000
* Task C (active) F-P: -0.1957 [-0.2717, -0.1268], p 1.0000
* Task C (active) F-H: -0.8949 [-1.0725, -0.7391], p 1.0000

**Connectivity to shRNA knockdowns is close to random in a universe of about 4,000 genes:**

* Task C (all) X-Z0: +0.0052 [-0.0052, +0.0174], p 0.2349
* Task C (active) X-Z0: +0.0326 [+0.0000, +0.0725], p 0.0667

**Priors are what work:**

* Task C (all) P-Z0: +0.4216 [+0.3737, +0.4721], p < 0.0001
* Task C (active) P-Z0: +0.2826 [+0.2065, +0.3659], p < 0.0001
* Task C (all) H-P: +0.5505 [+0.4869, +0.6150], p < 0.0001
* Task C (active) H-P: +0.6993 [+0.5580, +0.8659], p < 0.0001

**The gate does not know when connectivity will work:**

* Task C (all) admission gate Spearman with realised contrast, admitted fraction: 0.053, 0.66
* Task C (active) admission gate Spearman with realised contrast, admitted fraction: -0.098, 0.86

Task C orbit calibration helps: no

**In costs.** Chemical-neighbour transfer finds about one annotated target per 10 assays (0.098
hits per assay). Signature connectivity finds about one per 500–600 assays on all compounds, and
one per 230 on active ones.

* The literature's stronger connectivity results (Pabon 2018) were on curated compound–target
  pairs.
* Here the gene universe is the whole knockdown library, and shRNA seed effects dominate
  knockdown similarity.
* A decision engine for target triage should start from chemical-neighbour transfer.
  Transcriptional connectivity does not earn its assays.

## 8. Publication recommendation (deliverable G)

* **A novel-method paper: no.**
  * The pre-registered criterion for originality (H2a or H2b) failed in both tasks.
  * H2a is significantly negative in A′.
  * The identity gate is no better than the accuracy gate on any route.
  * By the selected hypothesis's own terms (CANDIDATES.md), there is **no methodological
    originality**.
* **A benchmark or evaluation note: possible, not yet.**
  * The orbit decomposition plus its two gates is a usable evaluation device for any
    knowledge-conditioned predictor:
    * Δ_id against the null-invariant model;
    * a positive control (V1) and end-to-end relabelling (V2).
  * It separates mechanism-class value (+0.010 here, identity-attributable) from functional
    genetic value (none beyond class).
  * Every outcome here was exposed to earlier MAESTRO studies, so the claim is exploratory.
  * A note would need the same frozen code run on a tier MAESTRO has never opened, and a second
    readout.
* **A systems paper on the agent: no.** No agent or LLM component was activated (PROTOCOL §11),
  and nothing here gives them incremental value to build on.
* **Negative-result value.** Two results are worth reporting with an external replication:
  * signed shRNA target knockdowns carry real, sign-reversible identity signal for compound
    responses, yet add nothing to mechanism-class neighbours;
  * signature-to-knockdown connectivity is near random for target nomination against simple
    priors.

## 9. Relation to earlier MAESTRO results, and Brief 5's final call

**Agreement with knowledge reality** (PRISM 19Q4 viability, 2026-10-13). That study found
mechanism-class membership and no target biology in context. OCEA reaches the same reading on a
second readout (L1000 transcription), with a stricter construction:

* the null is part of the estimator;
* the genetic route uses signed, line-matched knockdowns instead of graph features.

**Block Q (RKT).** It did not admit the genetic route. This study gives the reason: the route's
identity signal is real but redundant with mechanism class.

**Brief 5's question.** Does independent target-gene functional dependency improve
cold-start selective-sensitivity prediction (M3 − M1)?

* **Final call: INSUFFICIENT EVIDENCE.**
* The exact reasons:
  1. The question needs CRISPR dependency data (DepMap 19Q4 `Achilles_gene_effect.csv`,
     218.3 MB). It is not local, and its download has not been authorised.
  2. The local surrogate (shRNA knockdowns, transcription) is negative beyond mechanism class.
     It is not the same source: CRISPR dependency avoids shRNA seed effects, and block Q measured
     a higher specific cosine for CRISPR (0.078 against 0.025).
  3. The only untouched viability tier, PRISM 24Q2, must stay sealed. Its evaluator has the
     defects documented in the [evaluator audit](../evaluator_audit_20261013/README.md), and no
     protocol yet adopts corrections C1–C7.
* **For confirmation: NO-GO.** Spending the sealed tier would be premature.
* **The minimum next gate,** if authorised: an exploratory M3 − M1 test on exposed PRISM 19Q4,
  with the OCEA orbit (gene relabelling within dependency strata) as the mandatory null and
  corrections C1–C7 applied.

## 10. Roles of Agent, Virtual Cell and Decision Engine (design only)

| Component | What it owns | What this study changes |
|---|---|---|
| Agent | Queries, as-of dates, authorisations and budgets, through the [evidence interface](INTERFACE.md); it never edits evidence and reports refusals verbatim | Nothing activated (§11 of the protocol: no LLM before METHOD_SUPPORTED) |
| Virtual Cell | Routes, orbits, the decomposition and certificates; `IDENTITY_NOT_ADMITTED` when every ĉ_r ≤ 0 | The decomposition is worth keeping as an evaluation device; the admission gate is not |
| Decision Engine | Consumes admitted identity residuals as mechanism evidence; generic components may rank but are never reported as mechanism | Task C: for target triage, chemical-neighbour transfer dominates; connectivity evidence should not drive assays |

## 11. Limits

* **Exposure.** Every outcome was exposed to blocks M, N and Q, though never to this method.
  The grade is exploratory replication, not confirmation.
* **A′ is transcriptional, not viability.** The viability question is Brief 5's and is open (§9).
* **Knockdown quality.** shRNA consensus signatures carry seed effects. The null result for the
  genetic route may not transfer to CRISPR knockouts.
* **Strata define the orbit.** A relabelling that kept less (degree only) would credit more to
  identity, and one that kept more would credit less. The strata were fixed before S1 and
  passed V2.
* **Small subgroups.** The strict-new-mechanism stratum (19 compounds) is too small for H3 to
  mean much.
* **Task C is exploratory.** Its definitions were written after Tasks A′ and B were seen, though
  before any Task C number. The truth set is annotation, which is incomplete: a "miss" may be an
  unannotated true target.
* **Deviations.** The S2 rerun after a crash is D4 (§14).

## 12. Integrity work done alongside, kept separate from the science

* **Freeze-schema defect (Brief 5 §1).** The old `tools/research_validation.py` read only the
  `inputs` schema, so it silently authenticated nothing for the frozen studies.
  * Those studies declare `sha256` (collaboration limits, knowledge reality, selective hit
    triage) or `files` (block Q).
  * It now authenticates all three schemas.
  * It refuses any other schema as `BLOCKED/FREEZE_SCHEMA_UNSUPPORTED`, and it refuses paths
    that escape the checkout.
  * Block Q's mixed study-relative and checkout-relative keys resolve study-first.
  * The regression tests fail against the old validator.
* **CI.** `.github/workflows/tests.yml` installs no research assets.
  * It runs the default suite on Python 3.11, 3.12 and 3.13.
  * It asserts that the unconfigured preflight exits 2 with `BLOCKED/ASSET_MISSING`.
  * Local emulation passed on Windows (3.11, 3.12, 3.14) and Linux 3.12. Python 3.13 was not
    available locally.
  * Nothing was pushed, so the workflow has not run on GitHub.
* **Evaluator audit.** [research/evaluator_audit_20261013](../evaluator_audit_20261013/README.md)
  covers the frozen knowledge-reality `confirm.py`. It found:
  * normalisation on the test batch, with labels that depend on it;
  * eligibility and nomination masks read from outcome missingness;
  * unfrozen identity metadata.
  * It proposes corrections C1–C7 for any future protocol. The frozen study is untouched.
* **Three status levels**, kept separate:
  1. software tests: the default suite passes;
  2. research verification: this study's `verify.py`;
  3. the scientific verdict: §0.
  * A green CI run is neither of the other two.

## 13. Authorisations needed (none was used)

| Item | What it would allow | Size or cost |
|---|---|---|
| DepMap 19Q4 `Achilles_gene_effect.csv` (Figshare file 22543640) | Brief 5's M3 − M1 test, exploratory, on exposed PRISM 19Q4 with the OCEA null; the local `depmap_19q4` already holds expression, mutations and sample_info, matching the release in size | 218.3 MB download |
| Selective-hit-triage LLM arms (frozen, NOT_RUN) | Their pre-registered comparison | about 0.47 USD, deepseek-flash |
| PRISM 24Q2 REP.1M outcomes | Not requested. They stay sealed until a new, independently justified, powered protocol adopts audit corrections C1–C7 | 72.5 MB |

## 14. Deviations

All are recorded in [DEVIATIONS.json](DEVIATIONS.json). The freeze does not hash that file.

* **D1.** The S0 criterion was made relative to an oracle after a first synthetic run fell short
  of an uncalibrated absolute threshold (0.044 < 0.05).
* **D2.** The stacker penalty is relative.
* **D3.** `verdict.py`'s operational definitions were written after S1 and before the freeze.
* **D4.** The frozen `run.py s2` crashed in the controls step after 54 minutes.
  * The cause: `stage` passed the dict of Task B pipelines where `run_controls` expects the
    non-trivial result.
  * No estimate had been written or printed.
  * `run_s2.py` wraps that one call and leaves `run.py`'s frozen bytes unchanged.
  * The wrapped path was run end to end on development fold 0 first.
  * S2 then ran once. The computation is deterministic: the real pass and the relabellings
    finished at the same elapsed times as the crashed run.
* **D5.** Task C's operational definitions, locked by hash before Task C ran.

## 15. Reproduce

From the study folder, with the phase-1 L1000 assets of PROTOCOL §1 in place:

```bash
python run.py s0
```

```bash
python run.py s1
```

```bash
python freeze.py check
```

```bash
python run_s2.py
```

```bash
python taskc.py
```

```bash
python claims.py
```

```bash
python verify.py
```

* `run_s2.py` and `taskc.py` refuse to overwrite their write-once result files.
* `verify.py` needs no outcome access. It:
  * checks the interface refusals and the orbit partitions;
  * replays S0;
  * authenticates the freeze and the D4/D5 locks;
  * recomputes all claims and confirms that each appears in this README.
* `python verify.py --replay` also reruns S1 (about 3 minutes).
