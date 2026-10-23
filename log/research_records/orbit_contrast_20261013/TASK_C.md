# Task C addendum: target-hypothesis triage (operational definitions)

PROTOCOL.md §10 designed Task C before S2 and §9 made it conditional. S2 returned
IDENTITY_WITHOUT_METHOD with H1-A′ passing, which permits Task C. This addendum fixes the
operational definitions §10 left open.

* **When it was written.** After the S2 verdict, before any Task C number was computed.
* **How it is locked.** Its SHA-256 and that of `taskc.py` are recorded in DEVIATIONS.json (D5)
  before the run. `taskc.py` writes `RESULTS_C.json` once.
* **Grade.** Exploratory. The data are the exposed L1000 and annotation assets of §1, and the
  definitions were written by an analyst who had seen the S2 results of Tasks A′ and B. Task C
  never substitutes for A′ or B.

## Decision and units

* **Decision.** For a held-out annotated compound d, choose 10 knockdown genes to send to a target
  validation assay.
* **Cost.** 10 assays per compound in every arm (equal budget). Retrospective: 0 wells.
* **Utility.** Hits@10: the number of d's annotated targets among the 10 nominated genes.
  Hits per assay = hits@10 / 10.
* **Truth.** The genes in `ck.signed[d]` (Hub targets, then signed MAP-KG edges; binding
  excluded). Only genes in the candidate universe U(d) count.
* **Candidate universe U(d).** Knockdown genes with a signature in at least one line where d is
  profiled.
* **Units.** Compounds in outer folds 1–4 with at least one true target in U(d). Each fold is
  tested once, with the other four folds (fold 0 included) as training, as in S2.
* **Populations.** Primary: all units. Secondary: active units, with at least one active cell under
  the Task A′ vehicle rule.

## Shared quantities (per outer fold k; training = compounds with fold ≠ k)

* **Compound signature in line T.** Y[d, T] minus the mean of the training compounds profiled in
  T.
* **Knockdown signature.** `TaskA.KDc`: centred by all knockdown signatures in T. Knockdowns are
  evidence, not the outcome.
* **Connectivity.** cos(d, g, T) between the two. Averages run over the lines where both exist.
* **Training degree.** deg_k(g) is the number of training compounds with g in `ck.signed`.
  * Test annotations never enter it, and never enter any stratum.
  * Gene strata per line T: landmark × degree bin of deg_k ({0, 1, 2–4, ≥5}) × knockdown-norm
    tercile in T.
  * Fallbacks as in Task A′: (landmark, degree), then (landmark), with minimum size 5.
* **Ties.** Ranks break ties by a fixed SHA-256 order of gene symbols.

## Arms (each ranks U(d) and nominates its top 10)

| Arm | Score of gene g for compound d |
|---|---|
| Z0 random | a uniform random 10 from U(d) (seeded by compound key) |
| P degree prior | deg_k(g) |
| H chemical-neighbour transfer | Σ over the 10 most Tanimoto-similar annotated training compounds c (≥ 1 signed target) with similarity ≥ 0.3 of sim² · 1[g ∈ targets(c)], plus 1e-6 · deg_k(g) |
| X raw connectivity (Pabon-style) | mean over lines of cos(d, g, T) |
| Zc CMap-style z | mean over lines of (cos(d, g, T) − μ_gT) / σ_gT, where μ and σ are taken over the training compounds profiled in T |
| OC orbit-contrast connectivity | mean over lines of [cos(d, g, T) − mean of cos(d, g′, T) over g's stratum donors g′ in T] |
| F OCEA-admitted | the OC ranking if ĉ(d) > 0; otherwise the P ranking, labelled generic |

**Admission gate ĉ(d).** A ridge model on label-free descriptors of d, with alpha chosen by
leave-one-training-fold-out from {0.1, 1, 10, 100}. It is trained on the eligible training
compounds of fold k.

* **Descriptors:**
  * number of profiled lines with knockdowns;
  * log |U(d)|;
  * fraction of active cells;
  * mean response norm over the line's vehicle threshold;
  * top-1 OC score;
  * mean of the top-10 OC scores;
  * standard deviation of OC over U(d);
  * (top-1 − top-10th) / that standard deviation.
* **Training label: the identity contrast.**
  * c(d) = hits@10(OC) − mean over 16 relabellings of hits@10(OC with gene identities permuted).
  * The permutation is within line-independent strata: landmark × degree bin of deg_k, minimum
    size 5, fallback landmark.
  * Seeds are hash-derived.

The MoA tokens of a test compound are not used by any arm: MoA names often name the target.

## Contrasts and decision rule

* **Statistics.** Paired over unit compounds with `ocea.paired`: entity bootstrap (2,000), one-sided
  sign-flip p (10,000), seed 20261013.
* **C1, primary.** F − Zc: OCEA-admitted triage against the standard connectivity practice.
* **C2, primary.** OC − X: does orbit calibration add decision value to raw connectivity?
* **Reported:** every arm's mean hits@10 and hits per assay; every arm against P, H and Z0; the
  test Spearman of ĉ(d) with the realised c(d); the admitted fraction.

**Decision rule.**

* **DECISION_UTILITY_SUPPORTED:** C1 > 0 with p < 0.025, and neither F − H nor F − P is
  significantly negative (95% CI upper bound < 0).
* **Otherwise:** NOT_SUPPORTED.
* **Separate flag:** ORBIT_CALIBRATION_HELPS when C2 > 0 with p < 0.025.
