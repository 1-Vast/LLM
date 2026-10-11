# Budgeted feedback development replay

This experiment tests whether a small number of feedback rounds can justify their cost against a strong batch method. It uses an existing empirical cell-response surrogate; no LLM, paid API, external download, or new biological measurement is involved. Every query compound was exposed in earlier studies. The 421-compound report is retrospective development evidence, **never fresh confirmation**.

**Result: NOT_SUPPORTED.** The value gate saves declared resources but does not establish an advantage over the fit-selected strongest batch baseline. The gated net-utility difference is +0.00082, with a mechanism-cluster 95% bootstrap interval of [-0.01102, +0.01290].

| Policy | Utility | Net utility | Reads | Rounds | Declared resource |
|---|---:|---:|---:|---:|---:|
| Strong batch, Gaussian IVR | 0.15894 | 0.14094 | 16.00 | 1.00 | 18.00 |
| Two-stage Gaussian KG | 0.15471 | 0.13671 | 14.00 | 2.00 | 18.00 |
| Value-gated two-stage | 0.15309 | 0.14176 | 8.44 | 1.44 | 11.33 |
| Source-only transfer | 0.11026 | 0.11026 | 0.00 | 0.00 | 0.00 |

The gate stops after four reads on 55.58% of replay compounds and saves 37.05% of declared resource versus batch16. Its unpenalized utility is lower by 0.00585; the experiment does not establish noninferiority. Two-stage adaptation versus the fixed split of the identical Gaussian batch plan gives +0.00189 [-0.00701, +0.01017]. Correct feedback versus shuffled feedback gives +0.06463 [+0.04305, +0.08770], confirming outcome dependence in this replay while leaving the case for adaptive acquisition unsupported. These additional contrasts are exploratory.

Reliability remains a failure: the gated policy covers all selected candidates along its decision path on 370/421 campaigns (87.89%) and 68/101 active-drug campaigns (67.33%). Mean final interval width is 2.937 selective-residual units. The fit-fixed risk strata have 66 and 74 calibration compounds; no infinite-radius refusal was needed. Marginal coverage and active-drug coverage remain distinct requirements. These selected-path rates cannot be directly compared with the old 62.38% active-drug rate, which covered every terminal candidate rather than only those selected.

The secondary paired contrast is -0.01772 [-0.05640, +0.01575], with only 120 eligible pairs and 301 missing or ineligible campaigns. It does not confirm benefit. Runtime was 402.7 seconds for 702 compounds and 7,722 directly replayed arm-campaigns. Adding the gated policy yields 8,424 independently verified ledgers, with maximum utility reconstruction error 4.44e-16 and no duplicate or terminal-line purchase. Nine behavior tests pass.

## Decision and cost contract

Each campaign holds **one compound fixed**, buys recorded responses in discovery cell lines, and selects the ten predicted most sensitive terminal cell backgrounds. It does not choose drugs for one fixed cellular context. Dose, time, assay-platform transfer, independent prospective replication and mechanism validation remain separate tasks.

The shared resource cap is 18 declared read-equivalents. A read costs 1 and a turnaround costs 2. Therefore a single batch buys 16 reads, whereas two rounds can buy 4 followed by 10. Net utility subtracts 0.001 times total declared resource from terminal selective-cell-line utility. These are transparent cost scenarios, not laboratory prices. Historical L1000 measurements and source data are shared inputs. Compute and real assay procurement costs remain unpriced, so the conclusion does not establish monetary cost effectiveness.

The Gaussian posterior is unchanged between batch and two-stage arms. The first four measurements are committed together. After they return, the second batch is designed using the updated posterior; its ten actions are committed before any of their outcomes return. A fixed 4+10 split of the original batch plan controls for the same posterior, reads and turnarounds. A shuffled-feedback arm checks that apparent benefit depends on correctly assigned measurements.

The strongest baseline is selected on the 141 fit compounds from source-only transfer and Gaussian IVR/KG designs using 4, 14 or 16 measurements. The gate partitions campaigns at the fit median of predicted remaining KG value. That feature is the sum of sequential covariance-only fantasy KG values, not the joint EVSI of a ten-read batch. It purchases the second batch only when its group's fit-bootstrap lower estimate of incremental observed utility exceeds the declared incremental cost of 0.012. This is an exploratory group-average gate; it is not a certified campaign-specific EVSI lower bound. The gate can stop after four measurements, and retained counterfactuals permit an independent audit of that choice.

## Reliability and endpoints

The old 281 development compounds are deterministically divided into 141 fit and 140 calibration compounds. The policy and gate are frozen before the 421 exposed replay compounds execute. Calibration scores are the largest standardized prediction error over the ten selected terminal cell lines at every eligible decision snapshot. Two-stage policies include both the after-four and final selections. A fixed order statistic produces a global bound and bounds in two observable first-batch innovation strata. Hidden activity labels are used only for reporting. Empty or insufficient calibration strata produce an infinite radius, reported as refusal to certify an interval; they do not receive a borrowed finite bound.

The old surrogate temperature and observation noise had already been tuned on all 281 development compounds. The new split cannot erase that exposure. Coverage is therefore an empirical diagnostic, not a newly independent conformal guarantee. We report selected-path coverage, active-compound coverage, stratum sample sizes, final selected interval width, and refusals. The selected-candidate path endpoint differs from the old all-terminal simultaneous endpoint, so their numeric coverage rates are not directly comparable.

This implementation uses a **value gate followed by a post hoc reliability audit**. Reliability is computed by `analyze` after the replay; it does not gate continuation or reject an unreliable feedback value. The frozen exploratory success rule uses coverage point estimates and has no practical maximum-width threshold, coverage-confidence lower bound or minimum active-support threshold. Even a passing result would not certify reliable deployment. `VERIFIED.json` adds descriptive Wilson intervals as an explicitly postexecution audit; it does not revise the gate or the success rule.

PRISM secondary measurements are scored only and never enter fitting, acquisition, stopping or interval calibration. Paired statistics use the available intersection. Availability depends on selected candidates and the secondary assay uses different doses; those measurements do not establish a matched-context biological endpoint or a causal mechanism. No Agent contribution can be inferred from these deterministic policies.

## Reproduction and audit

The shared reference model and source verifier are imported from `research/dual_core_scientific_20261011/experiment`. The four pre-existing derived NPZ inputs are required and are not shipped in a clean checkout. Their acquisition and transformation provenance is retained by the earlier experiment's source receipts. This replay does not silently substitute synthetic or imputed query outcomes.

From the repository root with the existing `maestro` environment:

```powershell
& D:/anaconda/envs/maestro/python.exe -m unittest discover -s research/budgeted_feedback_20261011/experiment -p test_study.py -v
& D:/anaconda/envs/maestro/python.exe research/budgeted_feedback_20261011/experiment/verify.py
```

`study.py run` writes its source freeze before evaluation and refuses a repeated run in the same directory. There is no output-directory argument. For an independent rerun, copy only `study.py` and `PROTOCOL.json` to an otherwise empty sibling study directory at the same depth so its repository root resolves correctly:

```powershell
New-Item -ItemType Directory -Path research/budgeted_feedback_replay/experiment
Copy-Item research/budgeted_feedback_20261011/experiment/study.py,research/budgeted_feedback_20261011/experiment/PROTOCOL.json research/budgeted_feedback_replay/experiment/
& D:/anaconda/envs/maestro/python.exe research/budgeted_feedback_replay/experiment/study.py run
```

`study.py analyze` reconstructs summaries from retained raw rows and the local ledger with the frozen gate; it does not fit on the exposed replay set. Its entry point does not verify hashes itself, so first run `verify.py` before reconstructing existing summaries. The statistics and quantile dependency in the earlier `run.py` is transitively pinned by the original `CALIBRATION_FREEZE.json`, which is directly hashed in this study's `FREEZE.json`. `verify.py` validates that chain and records the expected and observed dependency hashes; this is a postexecution audit of an existing pin, not a new freeze.

Nine behavior tests check resource equality, no hidden terminal influence, paid-feedback sensitivity, an entire batch planned before observing its values, no duplicate or terminal purchase, identical-posterior fixed-split equivalence, planning without mutation, and gate independence from replay outcomes. `verify.py` independently recomputes utility, selected-path error and all resource charges from both compressed ledgers. It also checks source hashes and uses the promoted `CampaignBudget` contract.

`FREEZE.json`, `GATE_FREEZE.json`, `RELIABILITY.json`, `RECEIPT.json` and `VERIFIED.json` retain provenance. `RAW_ROWS.csv` contains all replayed counterfactual policies; `ROWS.csv` adds the gated policy. `LEDGER.jsonl.gz` and `GATED_LEDGER.jsonl.gz` retain full predictions, selected identities, purchased values, batch plans, updates and stopping reasons. The compressed ledgers are kept locally and ignored by Git. A clean checkout therefore needs the source NPZ assets and regenerated or separately retained matching ledgers before `verify.py` or `study.py analyze` can run; the compact receipts alone cannot reconstruct assay data. No predictive or planning algorithm from this experiment is promoted to production.
