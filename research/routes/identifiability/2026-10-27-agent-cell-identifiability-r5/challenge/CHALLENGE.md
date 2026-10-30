# CHALLENGE — I003.v1 / PROTOCOL E006

No results in `r5/` yet; citations are E006 line numbers.

## 1. A vs B separable? — **Fails**

B is A with the data removed: H009 (l.37) runs inside self-authored bootstrap worlds, so B can be true while A is false. The stop rule keeps A when B fails (l.48) with no mirror clause, so B survives A's death as the answer to a problem A says does not exist.

The branch table is the get-out-of-jail: p<0.05 → "order is detectable" (progress); p≥0.05 with power≥0.8 → "shared order suffices"; p≥0.05 with power<0.8 → "evidence-gap report". All three count as gains. C unlocks on one guaranteed rejection plus one self-chosen simulation.

## 2. Is M0 faithful? — **Fails**

M0 puts one shared rank vector on every cell (l.29, "已由 s 强制"), so truth is ρ=1. With σ_w≈0.04 against unit-value SD 0.15–0.25, the null sits at ρ≈0.97–0.99; real cross-line agreement is far lower (published analogue ~0.6). **H008 is pre-ordained: p lands on the 1/1000 floor whatever σ, λ_c or injected noise is used.** The shrink-and-reinject is a fair parametric bootstrap *of a null false by construction*.

Smuggled in: the relevant alternative is absent. R4 §3: the only observable separating shared from context-specific order is a **sign reversal**; the π family (l.30) relocates units at random — diffuse, magnitude-free, individually mostly unreadable. Rejecting on it licenses "diffuse heterogeneity exists", not "orderings resolve". λ_c uses R4's level-dependent σ (0.018–0.059), so one pooled value over-shrinks; iid injection omits row/column effects shared by all files.

## 3. S1 vs S2 fairness — **Fails**

(a) "不看响应" (l.25) holds only for the constant 2√2σ_w. Which pairs qualify depends on a "参考剖面" E006 never defines; if it is R̂ it comes from ȳ, so selection is on response-estimated separation — worst in the admitted 3-cell layouts (l.13), where each cell supplies a third of R̂. "FPR≤0.10 under M0" cannot catch this: the bootstrap repeats the selection.

(b) 0.113 is 2.83σ pooled, ~1.9σ in the high-viability bin (0.0589) where S2's tail pairs live.

(c) "+0.10 absolute" (l.37) on [0,1] is unsatisfiable when S1's power ≥0.90, which a π=0.2 reshuffle (~50 of 250 units) delivers to a Fisher-z mean. H009 is either auto-failed or set by the author's single choice of π — no effect-size justification, no paired CI, no power curve. They also replicate over different units (≤66 cell pairs vs unit pairs), so the +0.10 is not like-for-like.

## 4. Is the p honest? — **Fails**

(i) H008 (l.36) never names its statistic — S2 is 主 (l.24) but the criterion says only "统计量", so with two tests at α=0.05 unsplit, p is whichever rejects. (ii) B=1000 puts p at 0.001, where it will land; effect size unreported. (iii) Fisher-z treats within-plate cell pairs as independent, and layouts share plates and a day: demand layout-clustered resampling and a drug-pair block permutation. (iv) 18 per-layout + pooled + 2 statistics + 4 π need a hierarchical gate, α/2, per-layout results descriptive. (v) The "CI（自举百分位）" of l.39 is a category error: the M0 distribution is the null, not a CI. (vi) No null-calibration test.

## 5. vs BATCHIE's entropy term — **Holds only if restated**

The objects differ (BATCHIE reweights queries, B reweights evidence), but in E006 B never acts, so "把限制条件变成动作原则" is a category error. The cut is on *separation*, not SNR: under level-dependent σ, hard-0.113 and a 1/σ(level) weight pick different sets, and E006 has no soft-weight or level-matched comparator, so it cannot separate B from a hard-thresholded reweighting. Distinguishing test: concordance under (a) hard 2√2σ_pooled, (b) hard 2√2σ(level), (c) soft 1/σ²; if (a)−(c) is inside the clustered CI, B is a discretisation. Acquisition value needs C.

## 6. Disclosure — **Fails**

The null was built after R4 read A673/BJ and found 0.312±0.058 magnitude heterogeneity with unreadable sign; arbitrary h_c absorbs exactly that, so the design encodes the readout. R2 scored models on these plates (6×4×5 loop), so they are *used* — l.7 calls the test 描述性, then H008's p<0.05 gates A and hence C. That contradiction is the contamination: a descriptive p cannot gate a claim. σ_w is estimated from these same layouts, with no profile over 0.041–0.090. Undisclosed: these are BATCHIE's published validation plates, "random unseen combinations" from *remaining* space — a design-conditioned sample, and the space in which S2's separations are computed.

## 7. False positive and cheapest check — **Fails**

H008 rejects at the floor and is read as "context-specific order is detectable here", reverting R4 without ever touching a sign reversal. Cheapest pre-registered check: the **split-half same-cell control** — each cell's two files as two pseudo-cells, same layout, same pipeline. Truth is M0, so observed S1 must land inside the M0 null (p≥0.05) and S2 must still select a pair set; outside means the null is misspecified and no H008 p holds.

## What I would require before this counts

1. One named primary statistic on a *defined* leave-one-cell-out reference profile; the rest descriptive.
2. A scientific null: a pre-registered sign-reversal alternative with explicit magnitude (≥10% of pairs reversing at |δ|≥0.10 in ≥1 context) and power against *that*; π-reshuffle licenses neither branch.
3. The split-half control passing before any H008 p.
4. M0 carrying level-dependent σ and row/column offsets; verdict invariant across σ column, pooled vs level-matched, leave-one-out vs mean reference.
5. Layout-clustered inference; no p from a used scoring set may gate A or C — A stays exploratory until an independent plate batch confirms.
6. H009 with a paired CI at the 0.08–0.10 effect size, drawn as a power curve, not an absolute margin, against (b) and (c) of §5.
