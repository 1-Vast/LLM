# GAT development log (exposed data only)

Every number here comes from the development pool: the block N PRISM 19Q4 open and sealed tiers (1,403
compounds, 578 lines, opened 2026-10-11) joined to the block M landmark signatures. A compound is active when at
least 5% of its lines have LFC ≤ −1 (348 compounds). The primary statistic is the mean selective r over actives
(`selective_r`, generic profile = mean of the references). No NCI-60 or PRISM 24Q2 outcome was related to any
L1000 input during development. Times are UTC on 2026-10-31. Scripts are in `dev/`.

## 1. Noise ceiling (03:25Z)

Selective r between the 19Q4 primary and secondary screens of the same compound: 0.299 on actives (n = 295),
0.222 on all compounds with both (n = 467). A transfer prediction is unlikely to exceed about 0.30.

## 2. Leave-one-out grid of generic-axis removal (`dev_abtt.py`, 03:20Z)

The query is held out; directions are fitted on all 1,403 signatures (including the query's, so this grid is
optimistic for every D > 0 by the same mechanism and was used only to pick candidates).

| Similarity | k = 5 | k = 10 | k = 20 |
|---|---|---|---|
| raw cosine | 0.2002 | 0.2146 | 0.2248 |
| centred | 0.2014 | 0.2182 | 0.2274 |
| remove top 1 | 0.2087 | 0.2205 | 0.2315 |
| remove top 2 | 0.2148 | 0.2287 | 0.2361 |
| remove top 3 | 0.2186 | 0.2311 | 0.2379 |
| remove top 5 | 0.2195 | 0.2347 | 0.2409 |
| remove top 10 | 0.2231 | 0.2398 | 0.2450 |
| remove top 20 | 0.2162 | 0.2302 | 0.2351 |

## 3. Why removal should help: neighbour diagnostic (03:25Z)

Under raw cosine (D = 0), 75 compound pairs have similarity above 0.7. Their selective profiles correlate only
0.216 on average. Examples: alvocidib with doxorubicin (0.846), triptolide (0.838) and AT-7519 (0.851) — global
transcriptional shutdown, not shared selectivity. After removing 10 directions, no pair exceeds 0.7 and the
median best-neighbour similarity falls from 0.306 to 0.151.

## 4. Weighting, whitening and kernel ridge (`dev2.py`, 03:24Z, leave-one-out)

Paired differences against raw cosine k = 5 on actives, with bootstrap 95% intervals:

- Softmax weights were worse than clipped-similarity weights at every k (for example, removal k = 20:
  +0.0294 softmax vs +0.0448 clipped).
- PCA whitening (50 or 100 components) at k = 20: +0.0322 and +0.0381, below removal of 10 directions
  (+0.0448).
- Kernel ridge with power-3 kernels reported 0.48 to 0.64. **These numbers are void:** the leave-one-out
  shortcut centred the targets in-sample, so the held-out row leaked (check at 03:27Z on 40 actives: shortcut
  0.555, explicit refit 0.272). Kernel ridge was re-run in section 8 with reference-only centring and fold
  refits.

## 5. Ten-fold comparison (`dev_enc.py`, folds = permutation by `default_rng(7)`, 04:17Z)

Directions are fitted on the references of each fold only.

| Similarity | k = 5 | k = 10 | k = 20 | k = 40 |
|---|---|---|---|---|
| raw cosine | 0.1981 | 0.2100 | 0.2201 | 0.2222 |
| remove top 10 | 0.2206 | 0.2332 | 0.2415 | 0.2422 |

Removal of 10 directions at k = 20 minus raw cosine at k = 5: +0.0433 [+0.0338, +0.0532].

## 6. Contrastive encoder, two attempts

Both encoders map one 978-gene signature to a 256-dimensional embedding (MLP 978-1024-512-256, projection head
128, InfoNCE with τ = 0.1, 20% feature corruption, 12,000 steps of 512 pairs). Neither saw a viability value.

- Seed 0 (positives: two signatures of the same compound in any context; trained on L1000 compounds outside the
  development pool, the NCI-60 keys and the 24Q2 sealed list). Ten-fold, k = 20: 0.1936, below raw cosine
  (0.2201). Minus removal of 10 directions: −0.0478 [−0.0609, −0.0356]. Likely cause: positives from the same
  plate let the encoder match batch rather than compound.
- Variant 2 (positives forced to two different core lines; transductive: trained on all 7,707 L1000 compounds
  with at least two lines, including the development, NCI-60 and 24Q2 compounds' signatures, never their
  viability). Final contrastive top-1 0.516. Ten-fold, k = 20: 0.2093 (centred embeddings 0.2171), still below
  raw cosine at k = 20. Minus removal of 10 directions: −0.0322 [−0.0426, −0.0218].

Decision: the encoder arm C2 does not enter the confirmatory test, and hypotheses H2 and H4 are withdrawn
before the freeze. The encoder result is a development negative: compound-identity contrastive learning on
L1000 did not produce a better neighbour space for viability transfer than training-free removal of shared
directions, and did not beat raw cosine at matched k.

## 7. Aborted run

`dev5.py` (ten-fold grid with SVD per fold) was stopped by its own 3,000 s timeout after 7 folds. Its partial
output was not used. `dev6.py` replaced it with the study's eigendecomposition code.

## 8. Ten-fold grid with the study code (`dev6.py`)

Selection rule, written at 04:44Z before any `dev6.py` result was read (only its per-fold timing lines had been
seen):

- D: the smallest D in {3, 5, 10, 15, 20, 30} whose ten-fold active mean at k = 20 is within 0.005 of the best D
  at k = 20.
- K: the smallest k in {5, 10, 20, 40} within 0.005 of the best k at the chosen D.
- Kernel ridge (reference-centred targets, explicit fold refits, clipped cosine kernel to power 2 or 3,
  λ ∈ {1, 3, 10}) enters as an extra arm only if its best setting beats the chosen kNN arm by at least 0.010 on
  ten-fold actives with a bootstrap 95% interval above 0. Otherwise it is a development negative.

Results (written 04:46Z, same folds as section 5; exact means from `dev6_res.npz`, output in `dev/dev6.out`):

| Similarity | k = 5 | k = 10 | k = 20 | k = 40 |
|---|---|---|---|---|
| raw cosine | 0.1981 | 0.2100 | 0.2201 | 0.2222 |
| centred | 0.1987 | 0.2132 | 0.2235 | 0.2221 |
| remove top 3 | 0.2115 | 0.2259 | 0.2346 | 0.2367 |
| remove top 5 | 0.2146 | 0.2282 | 0.2366 | 0.2387 |
| remove top 10 | 0.2206 | 0.2332 | 0.2415 | 0.2422 |
| remove top 15 | 0.2203 | 0.2340 | 0.2412 | 0.2402 |
| remove top 20 | 0.2183 | 0.2323 | 0.2376 | 0.2379 |
| remove top 30 | 0.2139 | 0.2269 | 0.2323 | 0.2309 |

Kernel ridge (best λ per kernel power): raw cosine 0.2331 (λ = 3, power 2), 0.2301 (λ = 3, power 3); after
removing 10 directions 0.2426 (λ = 10, power 2), 0.2345 (λ = 10, power 3).

Applying the rule:

- D: best at k = 20 is D = 10 (0.241469). D = 5 is 0.236554, a gap of 0.004916, inside the 0.005 margin by
  0.000084. D = 3 is outside (gap 0.006907). **D = 5.** D = 10 had the best development mean; the rule prefers
  fewer removed directions when the difference is within the margin.
- K at D = 5: best is k = 40 (0.238653); k = 20 is 0.236554 (gap 0.002099); k = 10 is outside. **K = 20.**
- Kernel ridge: best setting (remove 10, λ = 10, power 2) minus D = 5 kNN-20 = +0.0061 [−0.0002, +0.0129] on 348
  actives. Below the 0.010 entry bar, so it does not enter. Development negative: with explicit refits, kernel
  ridge adds little once shared directions are removed. On raw cosine it adds more (0.2331 vs 0.2201 at k = 20),
  consistent with its inverse kernel partly discounting redundant generic neighbours, which removal does
  directly.
