# Kinobeads substitution test: protocol

2026-10-19. Written after the Klaeger download and the name mapping (MAPPING.json, design only), **before** any
binding correlation, kernel prediction or test statistic was computed. Frozen in FREEZE.json before the single run.

## Question

The action-substitution study (`research/action_substitution_20261019`, decision NARROW) found post hoc that the
annotated same-target sibling is a good reference in tight families (EGFR/HER2) and the worst in loose multi-kinase
families (Sorafenib, Dasatinib, Axitinib). Its one open falsifier: **does measured kinase binding (Level M evidence)
separate the substitutable same-annotation pairs from the non-substitutable ones on the interaction endpoint
(`SYNERGY_DELTA_AUC`)?**

## Data and exposure

- **Outcome:** Jaaks et al. 2022 GDSC anchored combination screen, original screen. It is exposed: MAESTRO opened it
  in October, and the action-substitution study already computed B0, B5 and the failure labels on exactly these
  units. **This is development evidence.** The only new information is the binding similarity.
- **Binding:** Klaeger et al. 2017 (Science 358:eaan4368) kinobeads apparent Kd, as deposited in ChEMBL (document
  CHEMBL3991601, CC BY-SA 3.0). Downloaded 2026-10-19 with the user's approval by `fetch_klaeger.py`:
  - 70,505 records, 243 drugs × 320 targets;
  - 65,576 records censored at Kd > 30,000 nM and 4,929 measured.
  - The PMC/Science supplement xlsx files sit behind a bot-check page, so the ChEMBL deposit replaces them
    (DEVIATIONS below).
- **No LLM or paid call. No sealed tier.** No other download.

## Mapping (MAPPING.json, done before this protocol)

- Matching: exact normalised name against the ChEMBL preferred name and synonyms. No manual alias was needed.
- **31 of 64** single-agent Jaaks drugs map (coverage gate ≥ 15: PASS).
- **21 of the 27** evaluable phase-2 implementations map: AZD7762, AZD8055, Afatinib, Alisertib, Axitinib,
  BI-2536, BMS-754807, Dactolisib, Dasatinib, Erlotinib, Lapatinib, Linsitinib, MK-1775, MK-2206, OSI-027,
  Palbociclib, Ribociclib, Sapitinib, Sorafenib, Tozasertib, Uprosertib.
- Unmapped evaluable implementations: Docetaxel, Paclitaxel, Navitoclax, Venetoclax, Wee1 Inhibitor, ZM447439. None
  is a Klaeger compound; four are not kinase inhibitors.

## Binding similarity (fixed)

1. pKd = 9 − log10(Kd in nM). A censored record (`>`) takes its censoring value (30,000 nM, pKd 4.52). Several
   records for one (drug, target) are combined by their median. The one record ChEMBL flags "Outside typical range"
   is dropped.
2. c_kb(a, b) is the Pearson correlation of the two drugs' pKd vectors over the targets measured for both, with at
   least 30 shared targets. Otherwise, or if a profile has zero variance, it is undefined.
3. No other transformation, threshold or target subset is used.

## Methods (same partner-level units as phase 2)

The script reuses frozen `lofo.py` by import, unmodified: `cells`, `Ref`, `Drugs`, the implementation set, and the
cell eligibility rule (a reference cell exists and at least one target-overlap sibling is present at the key).

- **B0, sibling copy:** the mean of the siblings' responses at the key.
- **B5, functional kernel** (lofo formula):
  - w_d = exp(−(1 − c_func(X, d)) / 0.2) · (1 + 2 · Jaccard(X, d)) over all reference drugs d at the key;
  - c_func is the single-agent profile correlation in the same role, and 0 when it is undefined.
- **K, binding kernel (tested):** identical to B5 with c_kb in place of c_func. When c_kb is undefined (d or X not
  in Klaeger), it is 0, exactly as B5 treats a missing correlation. Width 0.2 and factor 2 are **not** re-tuned.
- Khyb (secondary): c_kb where it is defined, else c_func.
- Units: (implementation X, role, partner).
  - obs = mean over lines of (y_X − sibling mean).
  - d_m = mean over lines of (prediction_m − sibling mean).
  - Error is (d_m − obs)², pooled over units.
- Sibling similarity of a unit:
  - sim_kb = mean c_kb(X, s) over the siblings s present at each cell, averaged over the unit's cells;
  - sim_kb is undefined when no sibling has a binding profile.
  - sim_func and Jaccard are defined the same way.

## Reproduction gate (before any metric)

- The recomputed B0, B5 and obs must equal the frozen `lofo_units_SYNERGY_DELTA_AUC.csv`: 1,950 units, no unmatched
  key, every absolute difference < 1e-9.
- If the gate fails, the script stops without computing any metric.

## Profile sparsity (from the smoke run, before the freeze)

- The smoke run printed only matrix shape, mapped and finite-pair counts, the reproduction gate, and the number of
  measured binders (pKd > 4.53) per mapped drug. These are binding facts, not outcomes.
- Median about 15 measured binders per mapped drug.
- **Dactolisib has none**: zero variance, so c_kb is undefined. Lapatinib, AZD8055 and AZD6482 have one each, and
  Pictilisib, Alpelisib and Trametinib two each.
- Kinobeads lysates capture few lipid kinases, and EGFR/ERBB2 are poorly expressed in them. So the EGFR/HER2 and
  PI3K/mTOR profiles are thin.
- Consequence: the primary population is restricted to implementations with a **defined** binding profile. The
  metric is not changed.

## Primary population

- Units whose held-out implementation is a mapped evaluable implementation with a defined binding profile: the
  **20** implementations, that is the 21 mapped ones listed above without Dactolisib.
- If fewer than 10 such implementations had units, the verdict would be BLOCKED.
- All 27 implementations, with K falling back to c_kb = 0 for unmapped X, are a **secondary** sensitivity
  (DEVIATIONS).

## Pre-specified tests

Inference for both tests is a cluster bootstrap over held-out implementations: 2,000 draws, seed 20261019, 95%
percentile intervals.

- **Test 1, prediction.** Does K beat both B5 and B0 on partner-level MSE?
  - Pass if the lower CI bound of MSE_B5 − MSE_K is > 0 **and** the lower CI bound of MSE_B0 − MSE_K is > 0.
- **Test 2, ranking.** Does binding similarity rank units by how often sibling substitution fails?
  - Failure is |obs| > 0.03 AUC, as in phase 2.
  - Score = −sim_kb: lower binding similarity to the siblings should mean more failure.
  - Units with undefined sim_kb are dropped.
  - Pass if the lower CI bound of the AUROC is > 0.5.

## Verdict

| Condition | Verdict |
|---|---|
| Test 1 and Test 2 both pass | **SUPPORTED** |
| Anything else | **NOT_SUPPORTED**; each test's own result is reported |
| Fewer than 15 Jaaks drugs map, or fewer than 10 mapped implementations have units | **BLOCKED** |

- Both tests are required (intersection-union), so no multiplicity correction applies.

## Secondary and descriptive (do not change the verdict)

- MSE of Khyb against B5 and B0.
- On units where both scores are defined, the sim_kb AUROC minus the sim_func AUROC, and minus the Jaccard AUROC.
- Per-implementation table: failure rate, mean sim_kb, MSE per method.
- Spearman correlation across implementations of mean sim_kb against failure rate.
- c_kb between annotated siblings (the tight-versus-loose families).
- The same statistics on all 27 implementations.

## Known limits, stated in advance

- **20 clusters.** The phase-2 B0 − B5 gap was +0.00025 with CI width about 0.0003, so K must clearly beat a strong
  same-line functional kernel to pass Test 1.
- **The lysate is not the context.** Kinobeads binding is a lysate measurement, not condition-matched engagement in
  these lines.
- **Coverage is partial.** Non-kinase reference drugs (chemotherapies, BCL2 inhibitors) have no binding profile, so K
  falls back to annotation weight for them, while B5 has a real correlation. This handicap of K is intended: the
  question is whether binding evidence alone carries the substitution information.
- **Exposed data.** A pass would be development evidence only and would need an untouched combination screen.

## DEVIATIONS from the brief (declared before running)

1. **Source.** ChEMBL CHEMBL3991601 replaces the PMC/Science supplement xlsx. Both are the Klaeger 2017 apparent-Kd
   data, and the supplement could not be fetched without passing a bot check. The CSV is 8.9 MB, against about 5 MB
   estimated when asking for permission.
2. **Primary population.** The 20 implementations of the brief's 27 that have a defined Klaeger profile (21 map; Dactolisib
   has no measured binder), because a held-out drug without a binding profile has no binding similarity to test. All
   27 are reported as a secondary.
