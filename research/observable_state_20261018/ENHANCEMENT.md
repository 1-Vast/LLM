# Enhancement review: observable-state discovery (2026-10-18)

> Historical design review only. Its statement that no result existed was accurate when written and is now superseded by [`REPORT_OBS.md`](REPORT_OBS.md), which records the completed development assessment and its limits. This note is retained as provenance, not as the current decision.

Status: review note, no result. Nothing was run and no outcome or sealed file was opened. [V] means checked in a primary source or in this repository's own records. [U] means not verified.

## 1. Blunt critique

**What is not new.** The bundle "typed edit + discriminating assay + decision utility + transfer" is made of existing parts (POSITIONING section 2, abstracts only [U]). Moving it to drugs is not a contribution. The ResearchEdit schema is good discipline, not a result.

**What is not testable here:**
- **H3 and H4 cannot be resolved.** A predictor-changing contrast has SE 0.199 at 2,304 compounds and needs 9,600-20,400 compounds. The interaction needs 38,000-82,000. PRISM has 4,528 [V, POWER.json].
- **The adaptive layer has nowhere to win.** Held-out hindsight headroom is +7.3%. Batch-EIG is a fixed design. Lookahead lost (-0.106 [-0.262, +0.022]). Revision, stepwise, LLM and grammar search added 0 [V].
- **The agent adds nothing measurable.** It was null or harmful in blocks N, P and Q, program_revision and acquisition_program [V, EVIDENCE.md].
- **Costs are hypothetical**, so J and Saving90 rest on invented prices.

**What is real.** The headroom is in information, not in choice: the fixed design gets 1.8-2.8 events per 64 compounds against an oracle of 32 [V]. Re-ordering the same viability pools cannot close that gap; only a new kind of observation can. Keep "jointly with the assays that identify them" and cut the rest. The H0 headroom check is still worth running as a cheap side task.

## 2. One sharpened idea: the decision exchange rate of a transcriptional read

**Claim.** For a fresh compound, one L1000 profile (one line, 10 uM, 6/24 h) is worth ρ viability pool reads for nominating selective kills in **unmeasured** PRISM lines. Item-specific value is separated from class membership, and ρ is reported for target lineages near and far from the profiled line.

**Why this attacks the binding constraint:**
- It adds information instead of re-ordering it (headroom and identifiability).
- The near/far split and the deranged control test transport.
- The answer comes in pool-equivalents, so it needs no plate prices.
- In the Gaussian belief, which assay to buy does not depend on outcomes, so the decision is the *composition of a fixed design*. ρ is that decision.

**Distinctness:**
- Multi-information-source optimisation (Poloczek, Wang, Frazier, NeurIPS 2017 [V, abstract]) picks among cheaper biased sources inside an optimiser.
- Szalai et al. 2019 NAR [V, abstract] show that L1000 carries a generic viability signature. Here that becomes a control arm.
- BATCHIE, PS-BAX, AssayLoop, R-IDeA and MDA [U] optimise within one assay or model class.

The contribution is an estimand plus falsifying controls, not a method. That nobody has published this estimand is [U].

**Components:**
- **Virtual Cell: kept, as the cross-modal translator only** (`src/virtual_cell/transcriptional_transfer.py`, already promoted). It added +0.049 to a 160-line partial screen but nothing to a 40-line one [V, module docstring]. Three pools cover about 75 lines, so this test lands in the undecided range. If ridge on raw L1000 components matches it, the VC claim is dropped too.
- **Agent: dropped.** There is nothing to propose or search.

## 3. Minimal staged experiment

**Inputs (all local):**
- PRISM 19Q4 primary screen, replicate-collapsed.
- GSE92742 Level 5 signatures.
- MoA-family folds 0-4.
- About 1,845 overlap compounds, with 6 lines that have more than 1,000 compounds each [V, QUALIFICATION_L1000.json].

**Read values.** Reads use published values with no synthetic noise. Read pairs and graded pairs are disjoint, so the real measurement noise is not shared. This removes the noise-draw component that moved earlier contrasts six-fold [V]. Sensitivity grader: the secondary screen at 2.5 uM, an independent experiment [V, file present].

**Stage 0 (no outcomes):**
- One profile per compound, line priority MCF7 > PC3 > A375 > A549 > HT29 > HEPG2, 10 uM, 24 h before 6 h.
- The profiled line is excluded from nomination targets.
- The translator's reference library is cross-fitted by MoA fold.
- Near/far lineage strata are fixed.
- Freeze, hashing with eol=lf.

**Arms** (all use ridge-plus-feedback and the fixed A-optimal pool order):
- **Z0** (zero): structure prior only.
- **F_k**: k = 1..4 viability pools (the reference curve).
- **T + F_(k-1)**: translator prior plus k-1 pools.
- **R + F_(k-1)** (strong simple baseline): ridge on 50 L1000 principal components.
- **D + F_(k-1)** (class null): the profile of a random other compound in the same family. Knowledge_reality's gain turned out to be only class membership.
- **G + F_(k-1)** (generic null): a scalar viability-signature score only.

**Primary metric.** Paired within compound: Δ_T = U(T + F_2) − U(F_2). U counts qualified events among the top-32 nominated unmeasured pairs per 64 compounds, at most 3 per compound, with the registered event rule.

**Secondary metrics:**
- ρ = Δ_T / δ, where δ = U(F_3) − U(F_2).
- Δ_T − Δ_D (item-specific value).
- Δ_T − Δ_R (VC value).
- A curve over follow-up budgets 8-64.

**Cluster unit.** MoA family; lineage group for the descriptive transport stratum. Bootstrap 4,000 draws, seed 20261018, one-sided family sign-flip.

**Minimum detectable effect** (80% power, one-sided 0.025, POWER.json scaled to about 1,800 compounds):

| SE assumption | MDE (events per 64) | In pool-equivalents |
|---|---|---|
| Acquisition-like (0.081) | 0.23 | about 0.65 |
| R1-like (0.225) | 0.63 | about 1.8 |

One pool is about 0.35 events per 64: the average of ridge − prior = +1.056 at 3 pools [V]. The marginal third pool is probably worth less.

**Stage 1 (folds 0-1, about 40% of compounds):**
- Measure the paired SE of Δ_T.
- **Descriptive only** if the projected MDE at full n exceeds 1 pool-equivalent.
- **Kill** if the point estimate shows Δ_T ≤ Δ_D or Δ_T ≤ 0.

**Stage 2 (folds 2-4):** one evaluation. Development, not confirmation, because every tier is exposed.

**Kill condition.** The one-sided 95% upper bound of Δ_T − Δ_D is below 0.1875 events per 64 (no item-specific decision value).

**Verdicts:**
- **Substitute:** lower bound of Δ_T − δ > 0.
- **Complement:** lower bound of Δ_T > 0.1875.
- **VC dropped:** lower bound of Δ_T − Δ_R ≤ 0.

**Cost:** 0 wells, $0, about 1 CPU-hour [U].

## 4. Three biggest ways this could be wrong

1. **Leakage and exposure.** The translator was built on PRISM, and blocks N/P/Q used this intersection [V]. Cross-fitting may miss near-duplicate structures. At 10 uM, L1000 may mostly encode generic toxicity. The D and G arms bound this, but they cannot exclude memorised class knowledge.
2. **Unresolvable, or a prediction gain without a decision gain.** Top-32 counts may be as noisy as R1 (MDE about 1.8 pools). The budget curve could improve without moving the operating point. Stage 1 must refuse rather than promote on a secondary metric.
3. **No transport.**
   - The overlap (about 41% of PRISM) is enriched for well-annotated drugs.
   - Dose (2.5 vs 10 uM), time (5 d vs 6/24 h) and identity by 13-character id are unmodelled.
   - A real ρ needs a prospective paired assay with plate costs. This study can only say whether designing that assay is worthwhile.
