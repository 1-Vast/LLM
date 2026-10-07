# Independent verification of the imported repeat study

Verification performed in the actual `maestro` environment on 2026-10-06. This review independently checks delivered bytes, saved measurements, saved candidate scores and database links. It does not retrain models, open sealed outcomes, certify independent cultures, reconstruct normalization from absent raw intensities, or infer physical experiment costs.

## Reproducible entry and preservation

`verify_snapshot.py` is the single maintained audit entry. It uses the Python standard library, opens databases by escaped read-only URI and prints JSON by default. An optional `--output` uses exclusive creation and refuses to replace an existing receipt. Both stdout/receipt equivalence and overwrite refusal were exercised successfully. Imported study files and database bytes remain unchanged.

```powershell
& D:/anaconda/envs/maestro/python.exe research/astra/repeat_optimization_20261006/verify_snapshot.py
```

The saved result is `verification_receipt.json`.

| Check | Independently observed result |
|---|---|
| Archive SHA256 | `25d246b5931ff7eb3b3534e9acde7d2ef036bedfd13ce51fd64e4e15a74f7ae1` |
| Archive entries against checkout bytes | 94 exact |
| RUN_MANIFEST file entries | 93 exact |
| Five current-study freezes | 32 exact entries and 4 LF-equivalent entries; no unexplained difference or missing dependency |
| LF-equivalent external files | `plate_hierarchy.csv` in three freezes; `partition.json` in one freeze |
| Unpackaged large source inputs | Fitted Jaaks CSV, original raw ZIP and full DepMap CRISPR CSV absent |

LF equivalence is a separate observation about text content. It does not make the raw hashes equal. Original recorded hashes are retained in the receipt beside actual checkout hashes. The absence of the three large inputs blocks complete raw-data reconstruction/refitting in this checkout; it does not invalidate the delivered snapshot checks.

## Saved-output reconstruction

The audit uses a separate scalar Pearson implementation, CSV parsing, explicit deterministic score sorting and measurement accounting. It does not import the original analysis or verification routines.

| Estimate | Reconstruction |
|---|---:|
| Fitted matched repeat rows | 4,519 |
| Fitted Pearson, equal line weighting after role averaging | 0.6972729813050332 |
| Fitted split-history residual Pearson | 0.49458683042815277 |
| Raw matched repeat rows | 4,424 |
| Raw Pearson | 0.5835883162636465 |
| Raw split-history residual Pearson | 0.3788965702969759 |
| Saved raw plate endpoint rows | 112,037 |
| Raw event values reconstructed from saved plate endpoints | 13,008 |
| Independent target identities | 14 cell lines, with 111 disjoint training identities |

The raw reconstruction averages saved plate endpoints per anchor concentration, then takes the declared maximum across concentrations. This verifies the aggregation into the saved repeat table. It does not independently verify the earlier blank/control normalization because original intensity data are absent. Raw complete-case coverage is 4,424/4,519; the excluded 95 pairs must remain visible when interpreting sensitivity results. Repeated seeding labels are not certification of independently thawed biological units.

The audit reproduced 84 RNA policy runs and 252 recovered biology policy runs across 28 line/role groups, including screen/verification capacity, confirmation counts, total measurement counts and R2-positive counts.

- RNA, shuffled RNA and simple arms each yield mean P2 confirmations 3.25 and mean P2 measurements 27.178571428571427.
- True hotspot, dependency, target-dependency and binary-RNA arms yield 3.2857142857142856 P2 confirmations. The feature-free `prior_control` yields precisely the same value.
- More strongly, each of those four true biological arms has the **same confirmed pair set as the static control in every one of the 28 groups**. This is independently reconstructed from scores and hit labels, not inferred from equal totals.
- Their screen choices and measurement totals need not be identical. Mean P2 costs are hotspot 27.25, dependency 27.321428571428573, target dependency 27.214285714285715 and binary RNA 27.214285714285715; static control also uses 27.214285714285715.

The +1/28 confirmation difference against the simple comparator therefore does not isolate a biological information contribution. All results are post hoc on previously exposed outcomes. Neither identity-disjoint training nor successful receipt reproduction turns them into untouched confirmation evidence. Saved bootstrap intervals were not independently rerun; the present receipt covers point estimates and accounting only.

The audit also independently reconstructed the architecture agent's `decision_headroom.json`. Holding the static prior's first-round screening set fixed, only SIDM00453/VS has more first-round hits (14) than verification capacity (11). Current verification confirms nine pairs there; an oracle that already knows R2 could confirm ten. Across all 28 groups, perfect verification reordering can therefore add only one confirmation. This is a fixed-screen bound. A whole-menu oracle or a different first-round screen addresses a different decision problem and cannot be called this bound, nor interpreted as an attainable scheduler gain.

## Databases

Both databases return `PRAGMA integrity_check = ok`, match registered hashes and counts, and are unchanged after read-only inspection.

| Experimental table | Rows |
|---|---:|
| assay_condition | 12,247 |
| measurement | 37,348 |
| benchmark_pair | 4,519 |
| candidate_prediction | 54,228 |
| raw_repeat_endpoint | 4,424 |
| model_recipe | 1 |

All measurement, prediction, benchmark and raw endpoint condition references resolve. Non-null R1/R2/R3 links reference measurements under the same condition. The feature database has 65 drug records, 124 target annotations, 1,750 pathway scores, 67,208 hotspot entries and 5,734 target dependency values. These counts denote feature records, not independently measured intervention evidence. CRISPR dependency is not pharmacologic target engagement.

## Tests and actual boundary findings

Four imported synthetic test files pass with explicit namespace-aware import mode: **14 passed**. The first normal-pytest attempt produced **four collection errors**, each `attempted relative import with no known parent package`. This is a real portability issue, not four failed scientific invariants. Frozen files were not changed to add package initializers.

```powershell
& D:/anaconda/envs/maestro/python.exe -m pytest research/astra/repeat_signal_20261005/test_analysis.py research/astra/repeat_signal_20261005/test_rna.py research/astra/repeat_signal_20261005/test_raw.py research/astra/repeat_signal_20261005/test_biology_recovery.py --import-mode=importlib -q -o addopts= -p no:cacheprovider
```

Constructive probes of the historical `plate_endpoint()` helper expose small input-contract defects relevant before migration into a general tool:

1. Multiple plate barcodes are accepted and the first is assigned to the output. The historical runner groups by barcode, so this probe does not demonstrate corruption of the saved run. A reusable helper should require exactly one plate.
2. Contradictory intensities for a duplicated control position silently select the first record. A duplicated same-position combination annotation can instead be excluded and return success with zero outputs. A reusable helper should distinguish exact repeated annotations, legitimate compound mixtures and inconsistent physical-well readings; the latter should be rejected explicitly.
3. Missing/NaN essential control values correctly produce `invalid_controls`; zero-valued measured intensities should remain numerical observations rather than missingness.

Minimal migration regressions should cover one-plate identity, equal intensity for repeated physical positions, exact-duplicate annotation invariance, explicit missing controls, and preserved compound-mixture exclusion. None requires changing the old normalization formula, QC thresholds, action menu or frozen outputs.

## Production and portability boundaries

- Original analysis imports `research.astra.feedback_validation_20261003.jaaks` and `tools.datasets.combination_screens`; original tests need namespace-aware loading. Importing the entire study into production would preserve these research dependencies and fixed external paths.
- Original `verify_results.py` appends an outcome-access ticket and rewrites `verification.json`; `finalize_evidence.py` also enriches databases and rewrites manifests. Neither was executed. They are historical pipeline stages, not safe read-only review entries.
- The experimental database contains relative ranking scores and a recipe hash. It explicitly records `serialized_coefficients = False`. It is not a production-loadable trained model artifact, and its scores are not calibrated outcome probabilities.
- The feature database schema (`cell_context`, `hotspot_mutation`, `target_dependency`) differs from the earlier biological-knowledge snapshot schema. Sharing the SQLite suffix does not establish interface compatibility.
- Scientific selection, fitted thresholds and historical priors stay in research. Only independently useful, tested parsing/identity/normalization responsibilities should be migrated, with fresh wrappers that refuse destructive writes.

Full raw reconstruction, biological-arm refit, bootstrap rerun, production/LLM evaluation and new biological measurements were not run. The imported receipts and failed/negative interpretations were preserved.
