# FAR Reproduction and Methods Audit (2026-10-19)

**Conclusion: retain `FAR_NOT_SUPPORTED`, but describe the evidence as a cross-validated development study on exposed data, not as a strictly isolated search → select → test validation.** The original results reproduce in the original local environment; the current `maestro` environment does not fully reproduce them. This audit did not test a new MoA/target hypothesis and did not retrain or modify the frozen model.

Post-cleanup note: statements in this report about the original verifier writing `decision` and the runner checking for overwrites too late describe the versions inspected during the audit. Cleanup changed these to read-only verification and early overwrite guards. The frozen core, model, thresholds, and original results are unchanged; cleanup and regression checks for non-frozen scripts are documented in the [working entry point](../README.md) and `../CLEANUP.json`.

## Checks Performed

1. Ran the original `verify.py` with `D:/anaconda/envs/maestro/python.exe`: it returned `VERIFIED`, and the original files were unchanged.
2. Independently recomputed all **118 saved contrasts** for search/select/test/vault using family-level resampling (utility and hits; 4,000 bootstrap draws). Point estimates, 95% intervals, and one-sided lower bounds matched the saved values to less than `1e-9`. This validates the calculation from archived records to statistics, not the independence of the original design.
3. Rebuilt select fold 2 and test folds 3 and 4 from the original PRISM/L1000/SMILES data. Ran the frozen model across **54 fold × policy × repair combinations**, compared per-drug utility/hit contribution arrays, and rebuilt the three failure-signature atlases.
4. In the original (`base`) environment with its default thread configuration, every array and atlas matched exactly (maximum error 0); FAR-v2 also loaded and reproduced successfully.
5. In the current `maestro` environment, the other 51 combinations completed but records did not match exactly, and FAR-v2 failed to load. A single-thread sensitivity check was also completed in the original environment.
6. Used synthetic perturbations to check stage dependencies and audited IDs, MoA labels, and slice sizes. SHA-256 hashes of files directly in the original study directory were unchanged; audit outputs are confined to this subdirectory.

For search/vault, this audit recomputed statistics from saved records only. It did not refit the search model or replay vault outcomes. The vault was never an independent confirmation.

## Reproduced Primary Results

These are the original frozen results reproduced in the original environment, not a new independent experiment. Utility is selective killing log2FC per nomination.

| Contrast | Select | Test |
|---|---:|---:|
| FAR − exploit-first | −0.01342 [−0.02773, −0.00420] | +0.00606 [−0.00279, +0.01774] |
| FAR-v2 − exploit-first | −0.01993 [−0.03834, −0.00661] | −0.00012 [−0.00655, +0.00627] |
| FAR assay + gate − no assay | +0.02104 [+0.00004, +0.04923] | +0.03895 [+0.00944, +0.08502] |

Neither primary contrast met the lower-bound requirement for the prespecified practical threshold of `0.010`; the original decision not to run Agent, 2x2, or transfer phases remains valid. This does not establish that FAR is generally ineffective, nor does it test the falsification or repair ability of a modern foundation Virtual Cell. This study tested only the current kernel/kNN + L1000 transfer implementation.

## Methodological Corrections

### 1. The stages are not strictly isolated

The actual reference definition in `far_core.py:19` is:

| Evaluation fold | Reference outcomes used by the predictive model |
|---|---|
| search fold 0 | folds 1 and **2 (select)** |
| search fold 1 | folds 0 and **2 (select)** |
| select fold 2 | folds 0 and 1 |
| test fold 3 | folds 0, 1, 2, and **4 (the other test fold)** |
| test fold 4 | folds 0, 1, 2, and **3 (the other test fold)** |

Thus search already uses select PRISM labels, and the two test folds provide training labels to each other. In the synthetic perturbation check, changing fold 2 labels changed search predictions by up to 5.270; changing fold 4 labels changed test-fold-3 predictions by up to 7.385. This confirms an actual computational dependency.

This can be described as a cross-fitted evaluation of the frozen procedure: each query fold is excluded from its own training references. **It is not a strict three-stage holdout evaluation**; in particular, select was not held out from search. The original bootstrap, which independently resampled families within each fold, also did not reconstruct the shared training dependence between test folds.

`far_data.load()` reads the full PRISM CSV each time. `Campaign` computes transfer/repair for all query L1000 values before applying the measured mask. In synthetic checks, the acquisition features for primary FAR/FAR-v2 did not change with query L1000 values (maximum change 0), so no explicit use of unpurchased L1000 values by primary acquisition was found. However, there was no independent evaluator enforcing a hidden-data access boundary, and file hashes cannot establish the historical order of data access.

### 2. The “exactly equal cost, 25%” claim does not hold by drug count

`np.array_split(order, 16)` only ensures slice sizes differ by at most one. If cost means buying four fixed-size plates/blocks, the number of actions can be equal. If cost means the number of drugs measured, as stated in the original report, costs are not exactly equal:

| Pool | Drugs per slice | Possible drugs across 4 slices | FAR observed mean | Exploit observed mean |
|---|---:|---:|---:|---:|
| select fold 2, 113 drugs | 7 or 8 | 28–29 | 28.346 | 28.172 |
| test fold 3, 149 drugs | 9 or 10 | 36–40 | 37.563 | 37.254 |
| test fold 4, 180 drugs | 11 or 12 | 44–48 | 45.221 | 45.024 |

The primary FAR arm measures slightly more drugs than exploit-first and should not be described as a strict equal-drug-count comparison. The difference is much smaller than in discarded run0, but it should be reported. The original results were not rewritten post hoc to adjust the budget.

### 3. Data alignment and family boundaries remain incomplete

* L1000 `pert_ids` can contain values like `BRD-...|BRD-...`. The current code treats the full string as one key. Across all HTS treatment metadata, exact matching finds 1,491 IDs; splitting on `|` finds 1,737 tokens, leaving 246 potential ID matches. **This does not mean the arena should necessarily include 246 more drugs**; tier, signature coverage, structural identity, and deduplication still need review.
* Among deduplicated HTS treatment rows, 2,015 rows contain comma-separated SMILES; 109 contain more than one canonical SMILES. The current “take the first” parser succeeds, but duplicate strings and identical structures are not equivalent. Differences may involve salts, stereochemistry, or other standardization and require item-level identity review. These counts are for all HTS metadata and do not represent ambiguity among the 848 development drugs.
* Families use only the first MoA label. Among retained development drugs, **27 full MoA labels cross folds**, including FLT3, KIT, and PDGFR. The current split holds out “first MoA + chemistry-connected family,” not all MoA labels. Using all labels would require redefining groups and sample sizes; existing fold IDs and intervals cannot simply be reused.

### 4. The scope of intervals and headroom must be narrowed

The original bootstrap reweights contribution arrays for already-selected nominations by drug family. It does not retrain models, reselect slices, or rerank, and it does not resample cell lineages/sources. These are conditional intervals for a fixed replay, not generalization guarantees for new contexts, assays, or the full training/selection procedure.

The split-line oracle selects slices on the same drugs using true outcomes from another random half of cell lines. It provides a hindsight-headroom signal within this arena. The random halves do not isolate lineages and share drugs and response structure, so this is not evidence of learnable headroom on future independent tasks. MoA/target remains an untested hypothesis.

### 5. Reproducibility and check scope

| Package | Current `maestro` environment | Full reproduction environment (`base`) |
|---|---:|---:|
| NumPy | 2.4.6 | 1.26.4 |
| pandas | 2.3.3 | 2.3.2 |
| SciPy | 1.17.1 | 1.10.1 |
| scikit-learn | 1.9.0 | 1.6.1 |
| RDKit | 2026.3.6 | 2025.9.2 |

In `maestro`, loading `VALUE_MODEL.pkl` raises `ModuleNotFoundError: No module named '_loss'`. Re-running in this environment gives a FAR − exploit test point estimate of about +0.00213, compared with +0.00606 in the original environment; neither meets the original practical floor. No packages were modified and no pickle was converted. The environment-dependent result is not treated as a new test-set result.

The original environment reproduces fully with its default OpenBLAS 24 / MKL 20 threads. With one thread, some discrete decisions in fold 3 change (split-line oracle utility changes by about +0.00208); folds 2 and 4 still match. This confirms sensitivity to versions/thread configuration but does not identify a specific library or floating-point path as the cause.

The original `verify.py` recomputes one test contrast from saved records and recalculates the decision from existing JSON; it does not load FAR-v2 or replay the models. It also hard-codes the expected `FAR_NOT_SUPPORTED` verdict. Its `VERIFIED` status therefore applies only to the file/statistical checks it declares.

The freeze hashes do not cover the runner, analysis, vault runner, decision logic, or raw data. This audit saved SHA-256 hashes of current inputs for future comparison; these cannot establish which data versions were used at freeze time. `far_decide.py` applies a 2.5th percentile lower-bound threshold to both contrasts, a conservative Bonferroni-style rule rather than full Holm step-down. Neither contrast passed, so this does not change the verdict.

There is also a rerun hazard: the write-once check in `far_run.py search` occurs after `MODEL.json` may be rewritten. Do not rerun this command in the original study directory. This audit used a read-only reconstruction path to avoid that issue.

## How to Use This Evidence

Retain two findings: current failure signatures did not meet their threshold, and L1000 + gate benefit can be reproduced in the fixed replay, but no FAR-specific advantage was demonstrated.

If the study is reopened, first freeze truly isolated reference/selection/evaluation rules, structural identity and multi-MoA grouping, exact costs, data/runtime dependency versions, and evaluator boundaries. Then test whether MoA/target information predicts assay value using search data. Original test and vault data are exposed; repartitioning them provides development evidence only. External confirmation requires separately qualifying unexposed data and a protocol. This audit did not start a new branch.

## Artifacts and Reproduction Commands

* `audit.py`: independent statistical implementation, read-only policy replay, metadata checks, and synthetic dependency checks.
* `RESULTS.json`: `maestro` environment results and compatibility failures.
* `RESULTS_original_env.json`: original environment with default threads; all reproduction checks passed.
* `RESULTS_original_env_1thread.json`: single-thread sensitivity results from the historical audit run.

Run from `D:/MAESTRO` in PowerShell:

```powershell
& 'D:\anaconda\envs\maestro\python.exe' -B research/maestro_far_20261019/audit_20261019/audit.py

# On Windows, register the DLL directory for the original environment; this affects only the child process.
& 'D:\anaconda\python.exe' -B -c 'import os,runpy; h=os.add_dll_directory("D:/anaconda/Library/bin"); runpy.run_path("research/maestro_far_20261019/audit_20261019/audit.py",run_name="__main__")' --original-env
```

No downloads, paid/LLM calls, wet-lab work, PRISM 24Q2, or other newly sealed outcomes were accessed. This audit made no commit or push. The full repository test suite was not run during the audit: only independent audit tooling and reports were added, with no product-code changes.
