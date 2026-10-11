# Independent implementation review

Reviewed 2026-10-11 (Asia/Shanghai). Status: completed source, behavior and independent artifact audit; `VERIFICATION.json` records the checked final artifacts.

The reviewer inspected `model.py`, `test_model.py` and `data/prepare.py` while the study was being assembled. No target response values were read for the pre-execution inspection. Nine model behavior tests and three complete-pipeline tests passed under `D:/anaconda/envs/maestro/python.exe`. Target response values were subsequently opened only after the final commitment and scoring artifacts existed and their hashes were checked, for independent arithmetic reconstruction.

## Source findings

No blocking model-side isolation defect was identified in the inspected implementation:

- The prediction API receives a fitted reference object, one target basal vector and explicitly purchased probe scalars. It has no target response-vector parameter.
- The crossfit prior refits scaling, high-variance basal-gene selection and prediction within each complete-context training fold. Missing reference outcomes remain missing in raw residuals, and are centered/zero-filled only inside reference covariance banks.
- Probe selection uses differential reference residual diversity. The low-rank correction can change drug ranking; offset calibration is an intentionally invariant control. The empirical conditional comparator is refitted on the functional endpoint and is not described as importing historical RNA weights.
- Metadata establishes context roles before outcome reads. Exact-dose HTS eligibility, representative treatment columns and alias components do not depend on target outcomes. Drug completeness uses reference contexts only. Target missingness remains evaluator bookkeeping.
- The source manifest correctly limits the claim to known drugs transferred to unseen outcome contexts, not new chemical identities or lineage-held-out generalization. It declares the absence of independent calibration and raw culture/plate provenance.

## End-to-end verification

The model-level poisoning test alone checks an already fitted model's API boundary. The completed `test_pipeline.py` additionally reruns fitting, setting selection, probe identities and commitments after setting every unpurchased evaluation response to NaN. Its complete prediction and record equality checks passed. This synthetic-data pipeline test supports model-side isolation; it does not undo publisher preprocessing.

The data producer permits partially missing basal input vectors while the model requires finite vectors. The final source packet contains zero missing basal values, so this discrepancy does not affect the executed study.

The common terminal menu excludes the fixed probes for every arm, including zero purchase. Thus cost comparisons answer whether probes improve decisions in that specified future menu. They do not establish superiority in a whole-library discovery campaign where a zero-purchase method could nominate a probe drug itself.

Keep all eligible contexts in the intention-to-evaluate ledger. Missing probes must follow the same frozen fallback and incur attempted measurement costs. Missing selected endpoints must not trigger replacement candidates. Complete-pair summaries, if necessary, are conditional on observability and cannot establish population-wide benefit when primary pairs are missing.

The runner was corrected before its execution to bind paired results to a real frozen problem hash and write `PROBE_FREEZE.json` before any development scoring. The final verifier found no remaining blocking artifact inconsistency. It imports none of the producer model, runner, utility or inference routines, and independently checks:

- All frozen source/input hashes, commit and scoring hashes; metadata-only split assignment and reference completeness.
- Every included response against the original exact-dose HTS source column, including NaNs.
- All 636 committed context-arm choices, top-10 membership, six arms' costs, fallback behavior, errors and utility calculations.
- All nine paired contrasts and a separate lineage-cluster bootstrap implementation.
- The offset arm's identical selected identities and the full-population gate's closure because five of 106 intended contexts lack complete selected endpoints.

Sign-flip p-values were not independently recalculated; they do not determine the diagnostic status. The verifier does not certify physical acquisition ordering from file timestamps. The frozen code's control flow places probe freezing before development scores, and commitments before terminal scoring.

## Decision from the completed diagnostic

The final status `NOT_ESTABLISHED` is supported by the artifacts. The 101 fully scored contexts are an observability-conditioned subset; six of the 106 intended contexts had at least one missing probe and correctly incurred the full attempted cost while falling back to the prior.

| Contrast | Mean top-10 utility change | Nominal lineage-bootstrap 95% interval |
|---|---:|---:|
| Low-rank correction minus paid no-update | -0.011933 | [-0.035300, +0.010253] |
| Conditional residual correction minus paid no-update | -0.005818 | [-0.031524, +0.022059] |
| Low-rank correction minus shuffled identities | +0.030915 | [+0.006280, +0.056091] |
| Low-rank correction minus zero purchase, price 0.001 | -0.021933 | [-0.045300, +0.000253] |

Correct probe identities outperform shuffled identities, but this does not establish a gain over the strong prior or justify paying for probes. The conditional comparator reduces available-terminal MSE from 0.309734 to 0.278741 (about 10%) while failing to improve selected-drug utility. Low-rank MSE is 0.784205; offset-only MSE is 0.784245, showing that the shared offset itself is harmful for mean calibration in this panel. These MSE summaries use available outcomes and are diagnostic, not population-level guarantees.

The appropriate decision is to stop progression of this particular complex feedback branch to KG acquisition or Agent attribution on the strength of this replay. This is a negative result for the fixed panel, candidate models, endpoint and reference/development split; it does not establish that all feedback designs or all cell contexts lack value. Further work would need a separately stated hypothesis or a better-qualified endpoint/data source, rather than retuning this evaluation split into a positive result.

Reproduce the independent audit from the repository root:

```powershell
& 'D:/anaconda/envs/maestro/python.exe' research/context_probe_20261011/review/verify.py --output research/context_probe_20261011/runs/fixed8
```

## Scientific limits

The original published PRISM matrices were already control-normalized, ComBat-adjusted and replicate-collapsed. Treatment-wise ComBat used cell-line pool/replicate information. This implementation can verify model-side target masking but cannot undo or certify target isolation in publisher preprocessing. Time is not available per treatment in the local collapsed metadata. All results are exposed retrospective algorithm diagnostics. Positive findings would still need independently acquired condition-qualified biological measurements.
