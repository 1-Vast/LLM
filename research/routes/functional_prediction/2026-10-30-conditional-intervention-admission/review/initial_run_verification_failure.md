# Initial Stage1 arithmetic verification failure

2026-10-30. Overall goal remains ACTIVE / NOT_ACHIEVED. This note records an implementation failure and a narrow independent diagnosis, without a scientific outcome decision.

The coordinator reported that the frozen v1.1 independent verifier was executed once against the first complete development matrix and stopped at `aligned/fold 0: frequency top20 differs from source counts/lexical ties`. I did not rerun the complete verifier. After that failure, the coordinator authorized access to the existing development labels/ranks solely to diagnose the mismatch. Neither frozen verifier source nor either pre-access freeze was edited or weakened.

## Inputs and read scope

The diagnosed inputs are `D:/MAESTRO/data/processed/conditional_interventions_20261030/cgi/stage1/labels.npz` and `ranks.npz`.

| Input | SHA256 |
| --- | --- |
| labels.npz | `cfff8e9e89f11726ee1dffdb2a9c5219b06be3ee8b9fb699a2ef4b578a43f4c8` |
| ranks.npz | `aaa66ae907df673f7a0358c9e9ab9ee1167b1743bf3b5efddce35f03c4773dc6` |

I read development compound IDs, canonical gene IDs, boolean calls and fold IDs, plus the aligned frequency indices/scores. The compound set was exactly the 231 frozen development representatives, with zero of the 63 held-out IDs present. Only aligned frequency fold0 was diagnosed. No chemistry scores, null metrics, root code, run/summary/decision JSON, source S1E rows, held-out outcomes, continuous CGI scores, GI/dose outcomes or synthesis were read. No model was fitted and no corrected output was executed.

## Independent count and tie evidence

Fold0 has 161 source compounds and 70 query compounds. Exact source call counts yield 792 eligible genes under `count>0` and `10*count<=161`. The exact frequency top20 is ordered by descending source count and then lexical gene ID.

Of the 70 saved query rows, 68 match this exact ranked top20. The two mismatching rows are zero-based row202 (`Chem-0297`) and row228 (`Chem-0339`). Both retain the same top20 gene set as the exact baseline, but reorder ranks13–16:

| Rank | Exact count/lexical order | Saved order in both rows | Saved score |
| --- | --- | --- | --- |
| 13 | CHKA | FLVCR1 | 0.06832298136645963 |
| 14 | CNOT8 | SZT2 | 0.06832298136645963 |
| 15 | FLVCR1 | CHKA | 0.06832298136645962 |
| 16 | SZT2 | CNOT8 | 0.06832298136645962 |

All four genes have exactly 11 source calls. Each declared frequency is therefore `11/161`, whose float64 value is `0.06832298136645963` (hex `0x1.17d9d6a88becfp-4`). The lower saved value is the immediately adjacent float64 `0x1.17d9d6a88becep-4`. Equal exact frequencies were separated numerically, overriding the required lexical tie order.

Across all 70×20 saved frequency entries in fold0, the largest absolute difference from independently calculated `source_count/161` is `1.3877787807814457e-17`; the maximum is one local float64 ULP. Thus the inspected saved score deviations are only roundoff-sized. Their effect on the declared ranked output is still a reproducible verification failure. Root implementation was not read, so this diagnosis does not identify its particular floating aggregation operation.

The same gene set in the two diagnosed rows implies that these two order changes alone cannot change an unordered top20 call count. I did not compare performance metrics, inspect other folds/nulls for this diagnosis, or infer that the complete first output is otherwise correct.

## Corrected-input verification command

The existing frozen v1.1 verifier already has `--data-dir` and `--output-dir`; no code/schema extension is needed. `--data-dir` selects labels.npz, ranks.npz and, with `--compare-root`, summary.json/decision.json. Shapes and all arithmetic remain governed by the original frozen contract. The corrected root inputs must remain separate from the first input directory.

```powershell
& 'D:/anaconda/envs/maestro/python.exe' 'D:/MAESTRO/research/routes/functional_prediction/2026-10-30-conditional-intervention-admission/review/verify_stage1_independent_v1_1.py' --data-dir 'D:/MAESTRO/data/processed/conditional_interventions_20261030/cgi/stage1_corrected' --output-dir 'D:/MAESTRO/research/routes/functional_prediction/2026-10-30-conditional-intervention-admission/review/independent_metrics_corrected' --compare-root
```

Current frozen verifier SHA256 remains `7dc11bfb045fcb8b51de64b8761e744f81c2f30645ab3b91cef65658e6be57af`. Current freeze-manifest SHA256 remains `c70e6b74f1956f5861f13aacc8bc2684c86eb72122be4e3743d3c8ed1395ff30`.

The coordinator's proposed exact source-count/N frequency correction directly addresses this declared-rule mismatch. Its proposed exact donor-count/5 neighbor correction was not examined here. This note does not authorize tuning, change a threshold, certify a corrected run, release held-out outcomes or establish a desired scientific verdict.
