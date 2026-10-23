# Program revision on PRISM: report

Study `program_revision_20261017`. Pre-registered in `PROTOCOL.md` and frozen 2026-10-17 (`FREEZE.json`), before the development arms ran and before any future outcome was opened. Future strata were first opened at 2026-10-17T13:09:54Z (`ACCESS.json`) and evaluated once. `python -B verify.py` prints VERIFIED.

## Question and answer

**Question.** Does MAESTRO improve future decisions by autonomously revising a shared library of executable, observably gated response programs on top of a strong inductive model?

**Answer, on PRISM 19Q4: no.**
- A small library of conditional programs did improve decisions on future cell lines and, more strongly, on unseen lineages. But that library was the **pre-specified textbook seed**.
- The MAESTRO revision loop added nothing beyond it, with or without the LLM, and with or without joint measurement edits.
- Conventional stepwise search over the same language added nothing either.
- The development wells spent on revision (≈ 4,300 per arm) bought no decision gain over the free seed.

Four claims are kept separate below:

| Claim | Status |
|---|---|
| Value of prior knowledge | supported within this screen |
| Value of revision | not supported |
| Value of the LLM | none; claim withdrawn |
| Independent confirmation | not available |

## Set-up (details in PROTOCOL.md)

- **Data and splits.**
  - Drugs: 966 source and 322 novel, in held-out structure groups (median max Tanimoto to source 0.32).
  - Lines: 231 source lines in 10 development projects (support 128 / query 103), 67 future lines in seen lineages, and 180 future-lineage lines (breast, gastric, kidney, ovary, pancreas, skin, urinary tract).
- **Decision and endpoint.** Per line, nominate 10 drugs; the utility is qualified confirmed hits.
  - A qualified hit is mean(X2, X3) ≤ −1, ≤ the drug's source median − 1, with every available replicate < 0.
  - Unknown outcomes (both replicates missing) are counted separately, never as inactive.
- **Strong model.** Rank-20 ALS, with a feature-ridge line prior and Bayesian updating from probe wells. It beats a drug-specific ridge: Stage B I2 +0.33 hits/line [0.12, 0.52].
- **Information conditions.**

  | Condition | Inputs | Wells |
  |---|---|---|
  | I0 | lineage | — |
  | I1 | + 50-gene DNA panel | 0 (zero-observation) |
  | I2 | + 8 A-optimal probe wells | 8 (few-observation) |
  | I3 | + RNA-seq | 8 |

- **Program language.** scope (MoA/target token) × state (mut/lin/probe/b/expr atoms with and, andnot, mul). Loadings are fitted on cross-fitted residuals and shrunk to a shared loading. Novel drugs use the shared loading. Capacity is ≤ 12 programs and ≤ 3 atoms per program; there are no identifiers.
- **MAESTRO loop.** 20 steps (10 projects × 2 rounds), ≤ 6 candidates per step, ≤ 120 evaluated per arm. Each step:
  1. diagnose counterexamples on support lines;
  2. propose edits;
  3. validate them, with named refusals;
  4. commit predictions and a digest;
  5. run a distinguishing experiment on development query lines, at 2 wells per revealed pair;
  6. apply the frozen acceptance rule: LLR ≥ 3, net hits ≥ 1, and the committed direction holds.

## Stage A: qualification (source development data only; `STAGE_A.json`)

- **Endpoint.** Known for 84.8% of pairs; under the original both-replicates rule only 61.6% were known. Hit rate is 10.3% of known pairs.
- **Missingness.** Not outcome-related: P(X1 ≤ −1) is 0.330 when the endpoint is known and 0.329 when it is unknown.
- **The probe predicts the endpoint.** Corr(X1, mean(X2, X3)) = 0.89. P(hit | X1 passes the threshold) = 0.50, against 0.05 when it fails.
- **Variance.** Drug means explain 78% of variance. Rank 20 reaches in-sample R² 0.90. Replicate noise is 3% of the variance of a 3-replicate mean.
- **Batch.** Pool explains 5.7% of within-drug residual variance, below the within-lineage shuffled-pool null of 8.9%: no pool structure.
- **Near-duplicates.** 25 source pairs have Tc ≥ 0.8; their line-profile correlation is 0.16, against 0.07 for random pairs.
- **Decision ladder** (development query lines, hits per line at K = 10):

  | Arm | Hits/line |
  |---|---|
  | Item prior | 2.18 |
  | Additive | 2.58 |
  | Rank 1 | 2.85 |
  | S I0 | 2.60 |
  | S I1 | 2.83 |
  | **S I2** | **4.16** |
  | S I3 | 4.42 |
  | Ridge I2 | 3.80 |
  | S I2 + seed | 4.19 (+0.04, ns) |
  | 16 probes | 4.37 |
  | 32 probes | 5.22 |
  | Unpriced full-X1 reference | 6.95 |

  Interaction structure beyond potency and sensitivity is worth about +1.6 hits per line. Measurement is the largest single lever.
- **Synthetic checks.**
  - **Linear-in-feature plants (S4a, S4b) are absorbed by S.** The true edit has LLR 16 to 59 but no decision gain, and is rejected.
  - **Positive control (S4c).** The plant is a conjunction orthogonalised to linear features. It is accepted (LLR 20.6, net +11 hits), and the enumerative loop raises development hits from 2.70 to 3.30 per line (ceiling 5.77).
  - **False acceptance.** Null world: 0 of 56 candidates accepted.
  - **Aliasing (S1).** With a hidden state, I1 is stuck at 3.16 hits per line. I2 recovers to 4.93 through ordinary updating alone, with no program needed.
  - **Crossed design (S2).** Not identifiable; the validator refuses it.
  - **Null and semantic-duplicate edits (S3).** All refused, with zero credit.
- **Pre-freeze changes.** Stage A changed four things before the freeze (PROTOCOL.md section 0):
  - the endpoint rule;
  - the strong-model rank;
  - a full composition screen: the hierarchical screen missed S4c's pure interaction;
  - one bug fix: the acceptance tuple lost its digest.

## Development arms (`LIBRARIES.json`, `trajectories/*.jsonl`)

| Arm | Evaluated | Accepted | Final library | Development wells |
|---|---|---|---|---|
| seed_fixed | 0 | — | 10 seed | 0 |
| stepwise (all query outcomes) | 86 | 1 | seed + EGFR×mul(HDAC-probe, MLH1) | 167,722 (every query outcome) |
| maestro_enum | 92 | 1 | seed + p38×mul(BET-probe, CDKN2A) | 4,410 |
| **maestro_llm** (primary) | 113 | **0** | seed | 4,260 |
| maestro_enum_empty | 102 | 3 | p38×…, HDAC5×andnot(CDKN2A, BRAF), MDM×andnot(TP53, EGFR) | 4,550 |
| maestro_llm_empty | 108 | 1 | MDM2×mul(Aurora-probe, TP53) | 4,286 |
| maestro_enum_joint | 93 (15 measurement edits) | 1 (no design change) | as maestro_enum | 7,785 |
| maestro_llm_joint | 110 (0 measurement edits proposed) | 0 | seed | 3,798 |

**Outcomes for LLM candidates.**

| Outcome | Share of LLM candidates |
|---|---|
| Insufficient evidence | 62–73% |
| Direction contradicted | 20–23% |
| Gate too rare | 6–9% |

Only one direction-contradicted candidate would otherwise have passed: MDM inhibitor × mut:TP53, committed as "sensitising". TP53 mutation confers resistance; the fitted loading is +0.28, protective. The check caught a biological error.

**LLM spend.** deepseek-flash only: 90 ledger calls, 0 errors, USD 0.287 upper bound. Of this, USD 0.088 was the pre-freeze smoke run.

## Stage B: frozen decisions on 247 future lines (`RESULTS.json`)

Hits per line at K = 10, pooled over future_line and future_lineage. Brackets are 95% cluster-bootstrap intervals over 17 lineages.

| Arm | I1 (0 wells) | I2 (8 wells) | I3 |
|---|---|---|---|
| S | 2.98 | 4.26 | 4.34 |
| drug ridge | 2.80 | 3.94 | — |
| seed_fixed | 3.42 | 4.47 | 4.64 |
| stepwise | 3.42 | 4.47 | 4.65 |
| maestro_enum | 3.42 | 4.47 | 4.64 |
| maestro_llm | 3.42 | 4.47 | 4.64 |
| maestro_enum_empty / maestro_llm_empty | 2.98 / 2.98 | 4.32 / 4.31 | 4.45 / 4.42 |
| AFA (8 adaptive wells, 8 rounds) | — | 4.49 | — |
| AFA + maestro_llm | — | 4.47 | — |

**Primary family** (I2; one-sided sign-flip p, Holm-adjusted):

| Contrast | Mean [95% CI] | Holm p | Verdict |
|---|---|---|---|
| H1 maestro_llm − S | +0.211 [0.097, 0.340] | 0.004 | CONFIRMED, but see H4: entirely the seed |
| H2 maestro_llm − stepwise | +0.008 [0.000, 0.030] | 1.0 | NOT_CONFIRMED |
| H3 maestro_llm − maestro_enum (LLM value) | +0.004 [0.000, 0.012] | 1.0 | NOT_CONFIRMED |
| H4 maestro_llm − seed_fixed (revision value) | 0.000 [0, 0] | 1.0 | NOT_CONFIRMED |

**Secondary contrasts** (exploratory, unadjusted):

| Contrast | Mean [95% CI] |
|---|---|
| Seed, zero-observation I1: pooled | +0.445 [0.084, 0.921] |
| Seed, zero-observation I1: future lineages | +0.556 |
| Seed, zero-observation I1: future lines | +0.149 |
| Seed at I2: future lineages | +0.250 [0.104, 0.409] |
| Seed at I2: future lines | +0.104 [0.013, 0.250] |
| Revision-learned programs from an empty start: enum | +0.057 [0.022, 0.104] |
| Revision-learned programs from an empty start: LLM | +0.045 [0.000, 0.114] |
| AFA vs fixed design | +0.223 [0.104, 0.400] |
| Library on top of AFA | −0.012 [−0.147, 0.111] |
| Probes vs DNA panel | +1.29 [0.83, 1.71] |
| RNA vs probes | +0.08 [−0.05, 0.20] |

**Program ablation** (I2, full minus without):

| Program | Effect [95% CI] |
|---|---|
| MDM×TP53 | +0.077 [0.025, 0.128] |
| RAF×BRAF | +0.057 [0.000, 0.152] |
| PI3K×PIK3CA | +0.028 |
| Every revision-added program | −0.004 to −0.008 |

**Novel drugs (unseen structure groups)** (322 drugs; nominate 10 per line):

| Setting | Zero-observation: S / potency control | Few-observation (1 pooled well per drug): S / potency control |
|---|---|---|
| Known lines | 2.87 / 1.64 | 3.30 / 1.27 |
| Future lines at I2 | 2.02 / 1.56 | 2.03 / 1.20 |
| Future lines at I1 | 1.61 / 1.44 | 1.65 / 1.45 |

- The S model's drug-line interaction beats the potency control in every setting except future lines at I1, where the interval crosses 0.
- Libraries through shared loadings add nothing: +0.02 [−0.02, 0.07] down to −0.04 [−0.09, 0.00]. **Program transfer to unseen drug groups fails.**
- The pooled probe helps on known lines (+0.43) but not on new lines.

## Stage C: complete campaigns, 28 wells per future line

| Policy (rounds) | S | seed = maestro_llm library |
|---|---|---|
| 8 fixed probes → 10 confirmations (2) | 4.28 | — |
| 8 fixed probes → 5 + 5 with feedback (3) | 4.45 | 4.63 |
| exploit-first 5 + 5 + 4 with feedback (3) | 4.83 | **5.26** |
| 8 adaptive probes (AFA) → 5 + 5 (10) | 4.64 | 4.63 |

Registered contrasts:

| Contrast | Mean [95% CI] | Verdict |
|---|---|---|
| Structural, exploit-first | +0.437 [0.041, 0.889] | CONFIRMED (unadjusted) |
| Structural, fixed-probe feedback | +0.186 [−0.014, 0.382] | NOT_CONFIRMED |
| Total: pre-specified maestro policy (fixed probes + feedback) − S exploit-first | −0.194 [−0.556, 0.113] | NOT_CONFIRMED |
| Fixed probes vs exploit-first | −0.381 [−0.665, −0.066] | HARMFUL |
| Feedback vs one-shot | +0.166 [0.07, 0.29] | CONFIRMED |
| AFA vs fixed probes | +0.198 [0.04, 0.39] | CONFIRMED, at 10 rounds instead of 3 |

**Payback.** The registered calculation compares each library with S. For maestro_llm it reports 3,632 lines to repay 4,260 wells. But maestro_llm equals the seed, which cost 0 development wells. Its incremental gain over the seed is 0, so **the revision cost is never repaid.**

## Diagnosis of the revision failure (`DIAGNOSTICS.json`, post hoc, development data only)

1. **The arena is underpowered and misaligned.**
   - Offered as add edits on the development arena, the frozen rule would accept only 2 of the 10 textbook seed programs: MDM×TP53 (LLR 31.9, net +6) and CDK×RB1.
   - It rejects RAF×BRAF (net 0) and PI3K×PIK3CA (LLR 2.0), the programs that later carried the gain on unseen lineages.
   - Their gates are rare on development query lines: 6 BRAF-mutant lines there, against 37 in the future lineages; PIK3CA-mutant 12 against 30.
   - Within-lineage support → query revision cannot see structure whose value lies in lineages the source barely contains.
2. **The strong model absorbs.** With a feature prior and probe updating it absorbs most linear gated structure (S4a/b). The remaining residual clusters are mostly noise at 103 query lines: 62–88% of candidates had insufficient evidence.
3. **The LLM has no edge.**
   - It proposed only add edits, and 20–23% of them came with the wrong committed direction.
   - The enumerative screen produced comparable or better programs at no cost.
   - It never proposed a measurement edit in joint mode.
4. **Measurement edits.** Those proposed by the screen changed many nominations (LLR up to 55) but reduced hits. The A-optimal design was not improved.

## Verdicts

| Question | Verdict |
|---|---|
| Method value (autonomous revision) | **Not supported.** H1's gain is the fixed seed (H4 = 0; H2 ≈ 0); revision-added programs have ≤ 0 ablation value. |
| Prior knowledge (pre-specified programs) | **Supported within PRISM 19Q4.** +0.21 (I2), +0.45 (I1), +0.44 on exploit-first campaigns; largest on unseen lineages. This is knowledge use, not discovery. |
| LLM value | **None. The LLM claim is withdrawn.** H3 +0.004; empty start LLM +0.045 vs enum +0.057; wrong-sign biology caught by the direction check. |
| Transfer | Seed programs transfer to unseen lineages (stronger than to unseen lines of seen lineages). Shared program loadings do not transfer to unseen drug structure groups. Joint measurement learning produced no accepted change. |
| Independent confirmation | **Not available.** Same screen, platform and release. Named set: PRISM 24Q2 REP.1M (sealed in `knowledge_reality_20261013`, authorisation pending). |
| Mechanism | Not claimed. |

Two findings outside the hypothesis:
- In complete policies, exploit-first confirmation with feedback beats spending 8 wells on probes (−0.38, HARMFUL for probes). This repeats the Beat AML finding on a different dataset.
- AFA beats a fixed design, but needs 10 rounds of turnaround.

## Next experiment (concrete)

**Lineage-disjoint knowledge revision with independent confirmation.**
1. **Arena.** Revise against lineage-disjoint arenas. Hold out one whole source lineage per step as the distinguishing arena, requiring ≥ 15 gated lines per candidate gate across arenas (pooled), so that acceptance tests extrapolation like the future strata.
2. **Proposal sources.** The enumerative screen, plus curated biomarker–drug pairs from a named public resource (for example OncoKB levels 1–3), mapped into the same language as non-LLM knowledge proposals. The LLM's only role is translating curated records, scored against a no-LLM translation.
3. **Endpoint.** Library + exploit-first feedback against S + exploit-first at 28 wells per line, the best Stage C policy here.
4. **Confirmation set.** Apply once to PRISM 24Q2 REP.1M lines and compounds not in 19Q4 HTS002, after authorisation.
5. **Pre-registered success.** ≥ +0.10 hits per line over the seed library (not over S), with lower bound > 0.

## Reproduce

```
python -B build_splits.py   # refuses: SPLITS_EXIST
python -B stage_a.py --sections A0,A1,A2,A3,A4,S && python -B stage_a.py --merge
python -B freeze.py          # refuses: FREEZE_EXISTS
python -B develop.py         # development arms (LLM calls served from the ledger cache)
python -B evaluate.py        # future strata; ACCESS.json is write-once
python -B diagnostics.py     # post-hoc diagnostics
python -B verify.py
python -m pytest -q test_science.py
```

Ledgers and per-line records live in `tmp/program_revision_20261017/`: `llm_ledger.jsonl`, `units_future.json`, and the `stage_a_parts/` cache.

Compute:

| Step | Time |
|---|---|
| Stage A | about 20 min |
| Development bench | 75 s |
| Arms | 27–196 s each |
| Frozen evaluation | 58 s |
