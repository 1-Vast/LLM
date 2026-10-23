# Measure or predict: a horizon- and transport-aware dual core (block K, 2026-10-10)

Status: **registered protocol**. Section 10 discloses everything seen during development.
`FREEZE.json` hashes this file, the analysis code, `GATE.json` and the development receipts
before any confirmation-tier, held-out or time-course outcome is parsed. The sealed extractors
(`prism_extract.py`, `mixseq_extract.py`) refuse those tiers by name (`TIER_SEALED`) until the
freeze exists.

## 1. Question

The 2026-10-10 phenotype-anchored block found two things. First, a perfect transcriptional
forecast adds nothing over basal transfer for 24 h survival selectivity in Tahoe spheroids.
Second, STATE's distinct held-out signal was cell-cycle composition. This block asks the dynamic
follow-up question:

> When a decision concerns a **later** fate (5-day viability), can a virtual cell's forecast of the
> **early** (24 h) cell state stand in for measuring that state? If not, is it because the early state
> carries no information beyond a strong cheap prior (no ceiling), or because the forecaster does not
> transport to the assay in which the decision is made (no transport)? And how early must one look?

The agent's decision is three-way: **ADMIT_WORLD_MODEL** (predict), **MEASURE_EARLY** (buy a
24 h pooled single-cell observation) or **USE_PRIOR**. It is computed per domain on development
units (`gate.py`, `GATE.json`):

* `ceiling = r(B + observed early state) - r(B)`;
* `forecast = r(B + world-model forecast of the early state) - r(B)`.

Here B is the best development cheap prior. Combinations are equal-weight sums of z-scores, with
no fitted weights. Then:

* ADMIT if `forecast >= MUB`;
* else MEASURE if `ceiling >= MUB`;
* else USE_PRIOR.

The minimum useful benefit is `MUB = 0.05` r.

## 2. Data and identities

| Source | Identity | Use |
|---|---|---|
| Tahoe-100M filtered (obs codes, X_hvg) | `arcinstitute/State-Tahoe-Filtered@fdf87abe` (extracted 2026-10-10) | 24 h same-spheroid survival, phase, basal and treated RNA |
| STATE ST-HVG-Tahoe zero-shot `final.ckpt` | sha256 `2c9b2e74...`, arc-state `9bbfe78a` | forecasts |
| PRISM Repurposing 19Q4 | figshare 9393293 v4, md5-verified files | 5-day viability (primary 2.5 uM; secondary 8-dose) |
| MIX-Seq (McFarland 2020), scPerturb copy | `mcfarland_2020.h5ad`, sha256 `94a72400...` | 24 h pooled responses, trametinib 3-48 h time course |
| DepMap 19Q4 CCLE expression | figshare 11384241 v3, md5 `684862866f...` | DepMap-scale basal prior |
| Candidate STATE gene order | Rhaister `static_2k_genes.json`, sha256 `6a29f993...` | MIX-Seq projection onto STATE's axis |

`DRUG_MATCH.json` maps Tahoe drugs to PRISM compounds by InChIKey connectivity and name (219
primary, 120 secondary).

## 3. Units and splits (fixed before any outcome was parsed)

* **Tahoe** (`SPLIT.json`, seed 20261010). The 31 count-qualified reference lines with PRISM
  are split into 15 development and 16 confirmation lines. Three STATE zero-shot lines have
  PRISM (Hs 766T, PANC-1, C32); HepG2/C3A and HOP62 are refused (`LATE_ENDPOINT_UNMEASURED`).
  The zero-shot lines' PRISM values **stay sealed in this block**. The development gate for this
  domain is USE_PRIOR even for a perfect early state, so a STATE forecast could not be admitted;
  spending untouched units would add nothing.
* **MIX-Seq** (`MIXSEQ_SPLIT.json`, seed 20261010).
  * Pool A: 93 lines, 24 h, eight drugs, two sub-pools with their own DMSO channels. Unseen
    lines with at least 20 control cells form 24 development and 48 confirmation lines. 11 lines
    are STATE-training lines; 10 unseen lines are refused (`CONTEXT_UNDERCOUNTED`).
  * Pool C: 114 lines, an independent trametinib 24 h experiment.
  * Pool D: 24 lines, a trametinib 0.1 uM time course at 3, 6, 12, 24 and 48 h, each time
    with its own DMSO hash.
* **External PRISM references**: about 400 PRISM lines that appear in no MIX-Seq pool and no
  sealed Tahoe tier. They are used only as references for the DepMap-scale prior.

Units are cell lines. Drugs within a line, genes within a response, and time points within a line
are not independent replicates.

## 4. Early readouts

* **Tahoe 24 h** (5 uM label, plate mean, relative to the same plate's DMSO):
  * `s24`: relative survival (spheroid share);
  * `g24`: G1 log-odds shift;
  * `k24 = log2 rho`, the kinetic readout. Phase fractions are converted to phase-duration shares
    `u_k = T_k / T_c` of an asynchronous, exponentially growing population (age density
    `~2^(-a/T_c)`). Under lengthening-only drug action the minimal cycle slowdown is
    `rho = min_k u'_k / u_k`.
* **MIX-Seq 24 h**. Treated cells are compared with the line's own sub-pool control on the 1,905
  STATE-axis genes present in MIX-Seq, in projection v1:
  * `log1p(x / total * T)`, with T matched to Tahoe's mean log level on shared lines;
  * absent axis genes are set to the Tahoe pooled basal mean.

  Readouts:
  * response vector O and magnitude `R_mag = -||O||`;
  * abundance `log2((n_treated + 0.5) / (n_control + 0.5))`;
  * G1 shift, from a full-gene, fixed-reference Tirosh phase call.
* **World-model forecasts**. STATE's paired delta (forecast minus DMSO forecast on the identical
  256-cell tensor of the line's own control cells). The analogous magnitude is
  `S_mag = -||paired delta||`.

  MIX-Seq doses map to the nearest STATE dose on a log scale:

  | Drug | MIX-Seq dose (uM) | STATE dose (uM) |
  |---|---|---|
  | trametinib | 0.1 | 0.05 |
  | afatinib | 0.5 | 0.5 |
  | everolimus | 10 | 5 |
  | gemcitabine | 0.1 | 0.05 |

## 5. Late endpoints and priors

* **MIX-Seq domain**: PRISM secondary dose-integrated mean log2 fold change (`secondary_mean`,
  5 days), across lines per drug. Primary 2.5 uM is secondary. Drugs: trametinib, afatinib,
  everolimus, gemcitabine, taselisib and JQ1 (the pool-A drugs with PRISM data); STATE covers the
  first four.
* **Tahoe domain**: PRISM primary log2 fold change at 2.5 uM, within-line selectivity (value minus
  the external-reference drug mean), over 217 drugs.
* **Priors** (chosen on development; `GATE.json` config):
  * MIX-Seq: PCA(50) + ridge(alpha = 100) on CCLE expression, with references = external lines
    plus MIX-Seq development lines;
  * Tahoe: CCLE kernel (tau 0.1, top 20), with references = external lines plus Tahoe
    development lines.

## 6. Gate decisions (development; `GATE.json`)

| Domain | B | B + observed early | Ceiling | B + forecast | Decision |
|---|---|---|---|---|---|
| MIX-Seq 24 h to 5 d | 0.307 | 0.446 | +0.139 | -0.150 vs B | **MEASURE_EARLY** (`WM_TRANSPORT_UNQUALIFIED`) |
| Tahoe 24 h to 5 d selectivity | 0.673 | 0.491 | -0.182 | not evaluated | **USE_PRIOR** (`WM_CEILING_BELOW_MUB`) |
| Tahoe 24 h survival (block P1) | 0.527 | 0.530 | +0.003 | below B | **USE_PRIOR** |

## 7. Confirmatory hypotheses (one-time, after freeze)

Statistics: 2,000 line-bootstrap resamples (seed 20261010); means over drugs within each resample.

**Domain M** (48 MIX-Seq confirmation lines)

* **M1 (primary; measurement complements the prior)**. The mean over six drugs of
  `r(B + R_mag) - r(B)` is greater than 0. Pass requires the 95% CI to exclude 0 and at least 4 of
  6 drugs to improve.
* **M2 (co-primary; forecast transport)**. The mean over four drugs of `r(B + S_mag) - r(B)`.
  Transport refusal is confirmed if the upper 95% CI is below MUB. Also reported:
  * RNA-level transport: per-line r of STATE's context deviation versus the observed one, against
    Tahoe-transfer, MIX-Seq-transfer and permuted-context controls and the split-half ceiling;
  * same-line cross-platform concordance (11 STATE-training lines: Tahoe observed versus MIX-Seq
    observed context deviation);
  * the cross-experiment trametinib replicate (pool A versus pool C).
* **M3 (decision)**. Each policy commits the 10 lines with the lowest predicted 5-day viability per
  drug:
  * P0: prior only;
  * P1: prior plus STATE;
  * P2: prior plus 24 h measurement;
  * P3: 5-day oracle.

  Utility is minus the mean observed 5-day viability of the committed lines. Pass requires
  `U(P2) - U(P0)` to have a CI excluding 0 and at least 4 of 6 drugs to improve. Also reported:
  `U(P1) - U(P0)`, the policy the gate selects, and costs.

**Domain T** (pool D, 24 lines, trametinib; estimation with CIs, no pass rule)

* **T1 (when to observe)**: r of `R_mag(t)`, abundance, G1 shift and kinetic readout at each time
  with 5-day PRISM. Also the increment of prior + `R_mag(t)` over the prior, and the earliest time
  within MUB of the best. Registered expectation: the information increases from 3 h toward
  24-48 h.
* **T2 (temporal fingerprint)**: for STATE's 24 h trametinib forecast and Tahoe's observed 24 h
  response, the generic r and least-squares scale against MIX-Seq's observed mean response at
  each time, plus the line-specific r. Registered expectation, if STATE encodes a 24 h horizon:
  generic similarity peaks at 12-48 h and the scale crosses about 1 near 24 h. A flat direction
  over 6-48 h would mean a time-agnostic response direction.
* **T3 (kinetic readout as a rate)**: `k(t)` versus the next interval's abundance change, pooled
  over the four intervals. Registered expectation: r > 0.

**Domain K** (16 Tahoe confirmation lines)

* **K1 (selectivity ceiling)**: `r(B + R_dyn) - r(B)` within line. R_dyn uses the development
  bridge, `-0.1575 s24 - 0.1965 k24`. The USE_PRIOR decision is confirmed if the upper CI is below
  MUB.
* **K2 (potency)**: the drug-level r of the Tahoe panel-mean `k24` versus `s24` with the
  confirmation lines' mean 5-day PRISM (moa-fine drug-cluster bootstrap). Registered direction:
  `k24 > s24`.
* **K3 (class-dependent leading indicator)**: the mean across-line r of `g24` with 5-day PRISM
  for the 29 development top-variance drugs. Registered sign: positive.

## 8. Controls and integrity

* Zero and permuted-context arms are included (`S_perm`, random expectation in M3).
* No confirmation outcome selects anything: priors, bridges, readouts and combinations come from
  `GATE.json`.
* `verify.py` independently checks:
  1. freeze precedence over every sealed extraction receipt;
  2. poisoning (replacing every sealed 5-day outcome with noise leaves all predictions and
     selections bit-identical);
  3. an exact rerun;
  4. arithmetic of M1 and M3 by a separate implementation;
  5. gate arithmetic from the development receipts.
* Laboratory costs (pooled wells, days) are reported separately from compute and API costs.

## 9. Named refusals

`TIER_SEALED`, `LATE_ENDPOINT_UNMEASURED`, `CONTEXT_UNDERCOUNTED` (fewer than 20 controls, or fewer
than 10 treated cells for an RNA response), `LABEL_NOT_IN_CHECKPOINT`, `NO_CCLE_EXPRESSION`,
`WM_CEILING_BELOW_MUB`, `WM_TRANSPORT_UNQUALIFIED`, `WM_FORECAST_NOT_EVALUATED`.

## 10. Disclosure of what was seen before freeze

1. **Tahoe → PRISM development** (15 lines; `development/dev_horizon.json`, `dev_perdrug.json`,
   `dev_direction.json`, `dev_gate.json`, `dev_ccle.json`):
   * cross-screen reliability within line is 0.33;
   * early readouts give within-line r of about 0.02-0.04;
   * within-dev basal transfer gives -0.04;
   * the CCLE kernel gives 0.67;
   * drug-level potency r is 0.48 for k24 versus 0.38 for s24;
   * for the top-29 variable drugs the across-line G1 r is +0.19 [0.07, 0.29], partial r given
     cycling is 0.20, and the leave-one-line-out fit is -0.26.

   The kinetic probe on 40 reference lines (`kinetic_probe.json`) gives 24 h survival r 0.06 for
   k24 and 0.004 for g24.
2. **MIX-Seq development** (24 lines; `dev_mixseq_rna.json`, `dev_mixseq_late.json`,
   `dev_ccle.json`, `dev_complement.json`). STATE's context-deviation r is about 0 (trametinib
   0.07); generic transport is trametinib 0.31-0.42, other drugs about 0. Late prediction:
   * DepMap ridge 0.31;
   * R_mag 0.34;
   * prior + R_mag 0.45;
   * prior + S_mag 0.14;
   * within-dev basal transfer -0.09.

   Projection variants v0, v1 and v2 were compared; v2 produced artefacts and v1 was chosen.
3. **Axis feasibility** (`axis_probe.json`). The MIX-Seq control profiles of 18 shared lines
   identify their own Tahoe line 18 out of 18 (permuted-axis null 0.03). The candidate gene list
   contains no canonical S/G2M marker gene.
4. **Earlier exposure.**
   * The Tahoe 24 h phenotypes and STATE forecasts of all Tahoe lines, including the zero-shot
     lines, were opened by block P1.
   * The repository's 2026-09-28 viability-contrast study used the PRISM *secondary* AUC matrix
     across many lines for a compound-class task; no line-level sensitivity of these lines was
     analysed in this session.
   * The PRISM primary values of the confirmation, held-out and MIX-Seq sealed tiers, MIX-Seq
     treated cells of those tiers, pool C treated cells and every pool D treated hash are unread.
   * Aggregate per-condition MIX-Seq cell totals (not per line) were printed while mapping
     experiments.
5. **Prior literature**. MIX-Seq reported that 24 h transcriptional responses predict viability
   better than baseline features (McFarland et al. 2020). M1 is therefore a replication under a
   stronger prior, not a new phenomenon. The contribution under test is the measure-or-predict
   decision and the transport failure of a frozen virtual cell.
