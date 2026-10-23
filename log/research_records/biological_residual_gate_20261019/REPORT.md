# P0 Biological Residual Information Gate: report

2026-10-19. The question: does biological information about how a drug intervenes (target annotations, quantitative
binding) carry reproducible, transferable, decision-relevant information beyond the strongest functional
drug-response predictor?

- Data: the exposed Jaaks 2022 screen only, so this is **development evidence**.
- Protocol (PROTOCOL.md) frozen before the run (FREEZE.json); run once; `verify.py` ALL OK.
- No LLM or paid call, no new download, no sealed tier opened. Not committed.

## Decision: UNDERPOWERED (by the frozen rule), with STOP for this action space

- **Frozen rule.** Gate 1 UNDERPOWERED, Gate 2 UNDERPOWERED, Gate 3 FAIL, which gives **UNDERPOWERED**.
- **What the numbers say beyond the label:**
  - **Target annotation adds at most a few percent beyond functional similarity.** +2.8%, with a family-level interval
    reaching 7.7%. Real targets beat shuffled ones, but on balanced accuracy the combination is *lower* than function
    alone.
  - **Biological mismatch does not predict B5's consequential errors** on held-out families: AUROC 0.48, below chance.
    The kinobeads test (`../kinobeads_substitution_20261019`, NOT_SUPPORTED) agrees: measured binding was worse than B5.
  - **The decision space is too small.** The reproducible opportunity in choosing among same-family alternatives is
    0.012 ECB-like units per decision, below the pre-registered minimum useful gain of 0.02. **Even a perfect selector
    could not reach the useful threshold on this data**, whatever the sample size.
- **Recommendation.** Close the action-substitution direction on Jaaks:
  - Do not build Virtual Cell or Agent layers on it.
  - Keep functional similarity (F) as the reference predictor.
  - Keep feedback on the strongest prior (below) as the only live mechanism.
  - Any biological-residual claim needs a different action space. The AstraZeneca 2024 matrix screen is the only
    qualified candidate found; it is unopened, and its use needs a new pre-registered protocol and the user's approval
    to download.

## Deliverable A: repository audit

- HEAD `9bb87d19` ("Add latest October 19 research progress"), which is the reference commit. It contains
  `research/action_substitution_20261019` as committed.
- Working tree at start: one log file modified by another session, plus the kinobeads study (untracked, written by a
  session this one started).
- **Reproduction:**
  - `action_substitution_20261019/verify.py`: ALL OK (hashes plus recomputation of MSE from saved unit tables).
  - B5 was **recomputed from raw cells** by `p0.py`: 1,950/1,950 units, max |difference| 1e-16 against the saved
    `d_B5`. All P0-A arms are recomputed, not read from the earlier results.
- **Verification levels reached:**
  1. hashes;
  2. statistical recomputation;
  3. full computational reproduction of B5 and the P0 arms from the source file.

  Not reached: (4) independent biological confirmation.
- Stale status corrected: the earlier README and REPORT said "nothing committed". Both now carry a dated amendment
  line. Frozen files are untouched.

## Deliverable B: corrected interpretation of the earlier study

Confirmed defects and corrections (AUDIT.json):

1. **B5 is not purely functional.** Its weight is exp(-(1 - rho)/0.2) x (1 + 2J): single-agent profile correlation
   times target Jaccard. P0-A splits these: function carries almost all of it (below).
2. **"Agent value bounded at zero" was overstated.** That claim holds only for:
   - epsilon 0.03;
   - the fixed refinement weight w of about 0.2 (range 0.17-0.22 across folds);
   - the annotation prior.

   With w = 0.2 and a zero prior, a probe has to show |Delta| > 0.15 to flip a decision. Single-cell noise SD is 0.057
   and the partner-level SD is 0.028, so flips were nearly impossible. This is a property of the update rule and
   threshold, not a bound on every strategy.
3. **Accuracy hid class prevalence.** 75% of units pass, so always predicting "substitutes" scores 75%.

   | Method | Sensitivity | Specificity | Balanced accuracy |
   |---|---|---|---|
   | B5 | 0.25 | 0.96 | 0.61 |
   | B1 | 0.37 | 0.85 | 0.61 |
   | B4 | 0.30 | 0.90 | 0.60 |
   | M | 0.40 | 0.80 | 0.60 |

   The learned model was not worse at decisions than B5 on balanced terms. It was worse on MSE.
4. **Replicates share cell stock.** In 100 of 123 multi-date lines a single CELL_ID stock was used across all seeding
   dates, and 48 lines span two campaigns. The "independent seeding events" are repeat assays from a shared stock, not
   independent biological preparations. Reproducibility r = 0.31 is an upper bound on biological reproducibility.
5. **Target overlap is a coarse family.**
   - "Any shared target" gives 29 pairs; an exact target-set match gives 7; a shared first-listed target gives 23.
   - Dasatinib/Sorafenib/Axitinib count as a family under the overlap rule.
   - B0 is a sibling-copy baseline under that loose rule, not a mechanism-equivalence baseline, and not a reproduction
     of PHAROS (which uses MoA-class proxies in a transcriptional state-search setting).
6. **Composites.** Only "Afatinib|Trametinib" ("Afatinib | Trametinib" in the validation screen) is multi-agent. It was
   excluded from phase 2/3 and from P0. In the gate it inflated the target class to 1,568 units, against 1,027 without
   it; the label was unchanged.
7. **Coverage.**
   - 10 of 37 candidates were unevaluable, all for the same reason: no sibling measured with the same partner in the
     same line.
   - Affected: FGFR (AZD4547, PD173074), TOP1 (Camptothecin, Irinotecan), alkylating (Oxaliplatin, Temozolomide),
     TGFBR (SB505124, Galunisertib), ABL (Nilotinib), PI3K (Pictilisib).
   - The evaluable set is therefore biased toward kinase families screened in the same anchor/library blocks.
     DNA-damage agents and FGFR/TGFBR families are absent.
8. **Phase ordering.** Phase 3 ran before phase 2 finished. It was frozen separately, but it is not a conditional
   progression from phase 2, and it stays development evidence.

## Deliverable C: B5 decomposition (P0-A, interaction endpoint S)

Units: 1,950 partner-level units, 27 implementations, **10 families**.

Families:
- taxanes;
- BCL2;
- multi-kinase (Axitinib, Dasatinib, Sorafenib);
- WEE1/CHEK/PLK (AZD7762, BI-2536, MK-1775, Wee1 Inhibitor);
- EGFR/HER2;
- Aurora;
- AKT;
- CDK4/6;
- mTOR/PI3K;
- IGF1R.

| Arm (information) | MSE | Failure AUROC | Sensitivity | Specificity | Balanced accuracy | Calibration slope |
|---|---|---|---|---|---|---|
| B0 sibling copy (annotation; B) | 0.000855 | 0.50 | 0.00 | 1.00 | 0.50 | n/a |
| B1 partner mean (none; B) | 0.000775 | 0.67 | 0.37 | 0.85 | 0.61 | 0.58 |
| T target kernel (annotation; B) | 0.000750 | 0.67 | 0.35 | 0.87 | 0.61 | 0.61 |
| **F functional kernel (panel; A)** | **0.000618** | 0.72 | 0.31 | 0.93 | **0.62** | 0.78 |
| F+T = B5 (panel + annotation; A) | **0.000601** | 0.72 | 0.25 | 0.96 | 0.61 | 0.87 |
| F+T, pathway-shuffled targets (mean of 200) | 0.000617 | | | | | |

- **Function carries the information.**
  - F beats the identity-free partner mean by +0.000157 (family CI +0.000073 to +0.000223).
  - T beats the partner mean by only +0.000025 (CI +0.000011 to +0.000036).
  - Adding F to T gains +0.000149 (CI +0.000052 to +0.000230).
- **Target annotation beyond function is small.**
  - F - F+T = +0.000017, rel +2.8%. Family CI -0.000005 to +0.000047; relative CI -0.9% to +7.7%.
  - The shuffle tests are significant: pathway-preserving p = 0.010, global p = 0.005. Target identity carries a real
    signal, but its size is below the pre-registered 5%.
  - Balanced accuracy drops from 0.619 (F) to 0.605 (F+T), so the gate condition "F+T >= F" fails.
  - **Gate 1 is UNDERPOWERED by rule.** The interval spans both 0 and 5%. The upper end, 7.7%, bounds the plausible
    increment.
- **Family heterogeneity.**
  - F+T is best or tied in 7 of 10 families.
  - Sibling copy is best only for taxanes (0.00054 vs F+T 0.00067).
  - Sibling copy is worst for multi-kinase (0.00171), CDK4/6 (0.00109) and BCL2 (0.00128).
- **Efficacy endpoint E.** F is best (0.00414). F+T is 2.1% worse (CI -8.4% to +5.1%), so target annotation adds
  nothing on efficacy.
- **Scenario B (no functional panel).** The best legal predictor is T, at 0.000750: 3% better than the identity-free
  partner mean and 25% worse than F. A new compound without a single-agent panel gains almost nothing from target
  annotations over ignoring its identity.
- **Scenario A cost.** In Jaaks the single-agent panel came from the same plates. Bought separately it is about 125
  lines x one 7-point curve, about 875 wells per new compound.

## Deliverable D: biological residuals of B5 (P0-B)

- Setup:
  - consequential error = B5's decision at epsilon 0.03 is wrong (21.7% of units);
  - L2 logistic regression and ridge, trained leave-one-family-out (10 folds).
- **Error prediction.**

  | Feature set | AUROC (held-out families) |
  |---|---|
  | generic (functional similarity, potency mismatch, kernel n_eff, disagreement with B1 and B4, partner pathway, role) | 0.452 |
  | bio (1 - Jaccard, exact target-set match, shared primary target, functional-similar-but-target-different) | 0.412 |
  | both | 0.476 |

  - Both - generic = +0.024 (family CI -0.050 to +0.133).
  - All three are below 0.5: what predicts errors inside some families predicts the opposite in others.
- **Residual correction.**
  - The corrected B5 is worse: MSE 0.000660 vs 0.000601 (gain CI -0.00013 to +0.00004).
  - Balanced accuracy 0.614 vs 0.605.
- **Univariate associations with |residual|, descriptive:**
  - shared primary target -0.30;
  - functional similarity -0.21;
  - 1 - Jaccard +0.16.

  The directions make sense, but nothing transfers across families.
- **Gate 2 is UNDERPOWERED by rule** (the CI upper bound reaches 0.05 with only 10 families). On the point estimates
  there is no transferable signal.
- **Quantitative binding.** The kinobeads session (`../kinobeads_substitution_20261019`) mapped 31 of 64 Jaaks drugs to
  Klaeger (CHEMBL3991601), covering 20 of 27 evaluable implementations.
  - Binding kernel vs B5: MSE difference -0.000059 (CI -0.000115 to -0.000010). Binding is significantly worse.
  - Binding as a failure ranker: AUROC 0.635 (CI 0.476 to 0.738).
  - Adding binding to the functional kernel: -0.000020 (CI -0.000053 to +0.000012).
  - So quantitative profiles do not explain B5's errors either.
  - Caveat: kinobeads measure lysate competition binding, not occupancy or pathway inhibition in the screened cells.

## Deliverable E: decision opportunity (P0-C)

- **Decision.** The original drug A was measured with partner P in line c. Choose one alternative from A's family,
  with the alternatives' combinations unmeasured, to maximise ECB-like benefit = min(single-agent X, single-agent P)
  minus observed combination AUC. That is the benefit over the better single agent, an HSA-type approximation of the
  ECB in Vis et al. 2024.
- **Eligible decisions.**
  - 33,029 (key, A) choice sets, but only **5 families** have 3 or more members measured at a common key: multi-kinase,
    WEE1/CHEK/PLK, EGFR, Aurora, mTOR.
  - On average 2.2 alternatives per set.
- **Opportunity.**
  - Oracle best minus random: 0.034.
  - Choosing by one seeding-date half and scoring on the other, the reproducible opportunity is **0.012** (family CI
    0.007 to 0.021, 834 sets).
  - 84% of sets have some alternative with ECB > 0.02.

| Selector (alternatives unmeasured) | ECB gain over random | Family CI | Wrong advancement | Efficacy gain |
|---|---|---|---|---|
| F | +0.0080 | +0.0055 to +0.0113 | 7.1% | +0.018 |
| F+T (B5) | +0.0075 | +0.0045 to +0.0111 | 7.3% | +0.016 |
| T | +0.0021 | -0.0001 to +0.0048 | 8.6% | -0.001 |
| B1 / B0 (no information) | +0.0022 / 0 | | 8.6% | 0 |

- Wrong advancement means the chosen alternative has ECB <= 0 while a better alternative with ECB > 0.02 existed.
- F+T - F = -0.0005 (CI -0.0016 to +0.0001): target information changes no selection for the better.
- **Gate 3 FAIL** on all three conditions:
  - the reproducible opportunity (0.012) is below the minimum useful gain (0.02);
  - F+T's gain (0.0075) is below 0.02;
  - F+T - F is not above 0.
- Functional similarity does capture about two-thirds of the reproducible opportunity (0.008 of 0.012). The
  opportunity itself is too small to pay for diagnostic experiments, at about 70 wells per combination block.
- **Could an Agent have a meaningful choice?** Not in this space. With at most 0.012 of reproducible value per
  decision and about 2 alternatives per set, no planner can reach the useful threshold.

**Feedback against the strongest prior** (descriptive; the epsilon 0.03 conclusion of PROTOCOL_P3 is unchanged). Same
units, probe lines and fold weights as phase 3; 85,060 probe-unit evaluations.

| Prior | Probe | MSE (remaining lines) | Balanced accuracy | Sensitivity / specificity |
|---|---|---|---|---|
| B0 | none | 0.000743 | 0.500 | 0.00 / 1.00 |
| B0 | one same-partner probe | 0.000634 | 0.517 | 0.05 / 0.98 |
| **B5** | none | **0.000538** | 0.599 | 0.23 / 0.97 |
| **B5** | one same-partner probe | **0.000451** | **0.627** | 0.30 / 0.95 |

- Feedback keeps its value on top of the strongest prior: -16% MSE and +0.028 balanced accuracy.
- B5 without a probe already beats B0 with a probe.
- This is the only mechanism here that improves both prediction and decision on the strongest prior. Its size is
  small and it is development-grade.

## Deliverable F: dataset qualification

| Resource | Status | Use |
|---|---|---|
| Jaaks 2022 original and validation screens | Exposed (October 2026 and this study) | Development only |
| Klaeger 2017 kinobeads (ChEMBL CHEMBL3991601) | Downloaded by the kinobeads session with approval; 31/64 drugs mapped | Tested and NOT_SUPPORTED; lysate binding, not occupancy |
| Vis et al. 2024 (Cell Rep Med; 51 combinations, 757 lines; anchored design) | Unopened by MAESTRO | 49 of 51 combinations overlap Jaaks (46 at the same anchor concentrations): same platform, same compounds. Almost no same-target alternative sets (taselisib/pictilisib). **Not independent and not qualified** for substitution. Total 51 published vs about 19 MAESTRO-usable is consistent: most are Jaaks repeats or lack alternative identities. |
| AstraZeneca pan-cancer screen (Cancer Discovery 2024; figshare project 163378; 109 combinations, 37 drugs, 7x7 matrices, 755 lines) | **Unopened**; metadata only | Genuine alternative sets sharing partners: MCL1 (AZD5991, tapotoclax), BCL2 (venetoclax, S55746, S55748), MEK (selumetinib, trametinib), AKT (capivasertib, ipatasertib, MK2206), PI3K (taselisib, AZD8186, BYL719). Different compound portfolio and full matrices, but a shared cell-line source (735 lines in common with GDSC2) and some Sanger involvement in the analysis tooling. The only qualified future endpoint candidate. |

- Independent confirmation of anything in this study: **BLOCKED_INDEPENDENT_ENDPOINT**. Nothing untouched is local,
  and P0 did not pass the gates that would justify opening one.
- **Leakage review.**
  - Target annotations are the GDSC 2022 annotations shipped with the screen.
  - Single-agent panels are measured on the same plates as the outcomes (Scenario A), so plate effects are shared.
    This favours F and B5, not a biological arm.
  - No pretrained representation or knowledge graph is used.

## Deliverable G: architecture recommendation

- **Retain:**
  - functional-similarity weighting (F) as the reference predictor for implementation transfer;
  - feedback updates on the strongest prior;
  - grouped (family-level) evaluation;
  - balanced decision metrics.
- **Suspend:**
  - action-unit learning and target-annotation features for substitution;
  - quantitative-binding integration;
  - any Virtual Cell or Agent work on same-family substitution in Jaaks.
- **Simplify:** substitution needs no new representation. A kernel over measured single-agent responses captures what
  is reproducible here.
- **Agent:** do not resume Agent development on this task. Revisit only if a qualified action space shows reproducible
  opportunity above the minimum useful gain.
- **Interfaces:** none need changing. Nothing is promoted to `src/` or `tools/`.

## Deliverable H: final decision

**UNDERPOWERED by the frozen rule; for this action space the evidence supports STOP.**

| Gate | Label | Key measurement | Uncertainty |
|---|---|---|---|
| 1. Biological increment over function | UNDERPOWERED | F - F+T +2.8%; real vs shuffled p = 0.010; balanced accuracy lower | family CI -0.9% to +7.7% |
| 2. Transfer to consequential errors | UNDERPOWERED | AUROC 0.48 (below chance); corrected MSE worse; kinobeads worse than B5 | family CI -0.05 to +0.13 |
| 3. Practical decision opportunity | FAIL | reproducible opportunity 0.012 < 0.02 minimum; F+T - F -0.0005 | CI 0.007 to 0.021 |

- **Main limitations:**
  - 10 families (5 for decisions);
  - exposed data;
  - replicates share cell stock;
  - the evaluable set excludes DNA-damage and FGFR/TGFBR families;
  - ECB is approximated from anchored curves.
- **Costs:** 0 wells, 0 USD, no new download. About 14 min of local compute (P0 run 11:48-12:02 UTC on one core,
  dominated by the 800 shuffle evaluations), plus a 3-minute smoke run.
- **Recommended next experiment.** Only if the user wants this line kept alive:
  1. A metadata-only eligibility census of the AstraZeneca 2024 screen: compound identities, shared partners, matrix
     doses, overlap with Jaaks lines. Use the published supplementary tables only.
  2. A pre-registered protocol whose primary endpoint is the reproducible ECB opportunity among alternatives,
     estimated from replicate structure before any model.

  The download and the opening of outcomes need the user's approval. Otherwise, close the direction.

Sources:
- PHAROS bioRxiv 10.64898/2026.09.08.749477
- Vis et al., Cell Rep Med 2024, PMC11384948
- AstraZeneca screen, Cancer Discovery 2024, PMC11061612
- Klaeger et al., Science 2017, PMID 29191878
