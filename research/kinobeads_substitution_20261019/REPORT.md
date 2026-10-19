# Kinobeads substitution test: report

2026-10-19. One pre-registered falsification test of the open question left by `action_substitution_20261019`
(decision NARROW): does measured kinase binding (Level M evidence) predict which same-annotation drug pairs are
substitutable on the interaction endpoint?

- **Data:** Jaaks 2022 GDSC anchored combination screen (exposed, so development evidence only). Klaeger et al. 2017
  kinobeads apparent Kd, taken from ChEMBL CHEMBL3991601 and downloaded once with the user's approval.
- **Run discipline:** protocol written and frozen before any binding correlation or test statistic was computed. Run
  once. No LLM or paid call, no sealed tier, nothing committed.

## Verdict: NOT_SUPPORTED

| Pre-registered test (20 implementations, 1,586 partner units) | Result | Pass rule | Pass? |
|---|---|---|---|
| **1. Prediction.** Binding kernel K vs functional kernel B5 | MSE_B5 − MSE_K = **−0.000059** [−0.000115, −0.000010] | both lower bounds > 0 | **No.** K is significantly *worse* than B5 |
| **1. Prediction.** K vs sibling copy B0 | MSE_B0 − MSE_K = +0.000197 [+0.000027, +0.000404] | (same rule) | Yes |
| **2. Ranking.** −sim_kb as a ranker of substitution failure (\|Δ\| > 0.03) | AUROC **0.635** [0.476, 0.738] | lower bound > 0.5 | **No** |

- Intervals are 95% cluster bootstrap over held-out implementations (2,000 draws).
- Partner-level MSE: B0 0.000855, B5 0.000599, K 0.000658, Khyb 0.000619. Failure rate 0.246.

Test 1 fails and Test 2 fails, so the verdict is NOT_SUPPORTED. Measured binding similarity does not identify
substitutable same-annotation pairs better than what MAESTRO already had.

## Secondary results (do not change the verdict)

- **Binding is no better than annotation overlap or same-line functional similarity as a failure ranker.** On units
  where both scores are defined:
  - AUROC sim_kb − sim_func = −0.041 [−0.172, +0.062];
  - AUROC sim_kb − Jaccard = −0.024 [−0.182, +0.146].
  - Point AUROCs: functional 0.662, Jaccard 0.643, binding 0.635.
- **Adding binding to functional similarity does not help.** Khyb (c_kb where defined, else c_func) vs B5:
  MSE_B5 − MSE_Khyb = −0.000020 [−0.000053, +0.000012].
- **K beating B0 is not evidence for binding.** Every pooled kernel in phase 2 also beat sibling copy (B5, B4).
  Nothing here isolates binding as the reason.
- **All 27 implementations** (K falls back to annotation weight for unmapped drugs): MSE_B5 − MSE_K = −0.000078
  [−0.000152, −0.000022]. Same conclusion.
- **Across implementations,** the Spearman correlation of mean sibling binding similarity with failure rate is −0.29
  (n = 19, descriptive). The direction is right; the correlation is weak.

## What binding similarity does and does not separate (descriptive)

Mean c_kb to annotated siblings, against the sibling-copy failure rate:

| Implementation | sim_kb | Failure rate | Reading |
|---|---|---|---|
| Afatinib, Sapitinib, Lapatinib | 0.51-0.61 | 0.03-0.12 | tight EGFR/HER2 family: high binding similarity, few failures |
| Sorafenib, Dasatinib | 0.15-0.19 | 0.37-0.60 | loose multi-kinase "family": low similarity, many failures |
| AZD8055, OSI-027 | 0.07 | 0.04, 0.26 | lowest similarity, yet AZD8055 almost never fails (mTOR is poorly captured by kinobeads) |
| Axitinib | 0.26 | 0.02 | low similarity, almost never fails |
| Linsitinib, BMS-754807 | 0.31 | 0.54 | moderate similarity, fails half the time |
| Alisertib / Tozasertib | 0.40 / 0.40 | 0.28 / 0.06 | same pair, very different failure rates (substitution is asymmetric) |

- **The motivating contrast is recovered,** but only that contrast. Binding similarity reproduces the EGFR/HER2
  versus Sorafenib/Dasatinib difference that prompted the question.
- **It does not generalise to the other families.** The phase-2 functional kernel already ranked the same tight
  families well (sim_func 0.73-0.87), so binding adds nothing beyond it.
- **Two structural reasons it cannot do better here:**
  - The profiles are thin. The median mapped drug has about 15 measured binders out of about 290 targets.
    Lapatinib has one, and Dactolisib none. The EGFR/HER2 similarities rest on a handful of shared binders.
  - Substitution is asymmetric (Alisertib → Tozasertib fails, the reverse rarely does). A symmetric similarity cannot
    represent that.

## Consequence for the action-substitution programme

- **The Level M falsifier is answered.** Kinobeads binding similarity is not a better definition of a pharmacological
  action unit than annotation overlap, and it is a worse substitution kernel than functional similarity measured in
  the same lines.
- The action-substitution decision stays **NARROW**. The Level M branch is closed on this data.
- **Do not build a binding-based action-unit layer.** If substitution is revisited, the only remaining lead is the
  partner-specific counterexample refinement, which needs a decision that binds and untouched data (see
  `action_substitution_20261019/REPORT.md`).

## Limits

- **Exposed outcomes.** B0, B5 and the failure labels on these units were computed by the earlier study. The binding
  similarity is the only new input. A pass would still have needed an untouched screen.
- **The assay is not the context.** Lysate binding comes from the Klaeger cell-line lysates, not from engagement in
  the Jaaks lines. EGFR/ERBB2 and the lipid kinases (PI3K/mTOR) are poorly captured in those lysates.
- **Power.** 20 clusters. Test 1 failed in the opposite direction with a CI excluding zero, so low power is not the
  explanation for Test 1. Test 2's interval is wide.

## Deviations and disclosures

1. **Data source.** ChEMBL CHEMBL3991601 was used instead of the PMC/Science supplement xlsx, because the supplement
   is served behind a bot-check page. The CSV is 8.9 MB, against about 5 MB estimated when asking permission. The
   fetch also read molecule synonyms and assay descriptions from the same API (molecules.json, 137 kB) for name
   mapping.
2. **Primary population** (declared in PROTOCOL.md before the freeze): the 20 of the brief's 27 implementations with
   a defined Klaeger profile.
   - 21 map; Dactolisib has no measured binder.
   - The smoke run's per-drug binder counts led to this restriction before the freeze. The smoke run printed no
     metric.
3. **AUROC tie fragility (found by verify.py).**
   - sim_kb values that are equal in exact arithmetic can differ at about 1e-16, because they are means over cells
     taken in different orders. Ranking then splits those ties arbitrarily.
   - Reading `kb_units.csv` with pandas' default float parser shifts the AUROC by about 1e-4 (0.6353 → 0.6352).
   - verify.py reads with `float_precision="round_trip"` and reproduces the frozen numbers exactly.
   - The effect is far below anything that could change the verdict.

## Files

| File | Contents |
|---|---|
| `PROTOCOL.md` | pre-registration |
| `FREEZE.json` | digests of the protocol, code, mapping, reused action-substitution files and Klaeger data |
| `fetch_klaeger.py` | download (writes `data/external/klaeger2017_chembl/`, with MANIFEST.json) |
| `mapping.py`, `MAPPING.json` | name mapping and coverage (31 of 64; 21 of the 27 evaluable implementations) |
| `kb_run.py` | the test; imports the frozen `action_substitution_20261019/lofo.py` unmodified |
| `kb_run.log`, `KB_RESULT.json`, `kb_units.csv` | the single run |
| `verify.py` | digests, recomputed point estimates, exact bootstrap reproduction, verdict rule (`VERIFY OK`) |
