# Heavy-tail RSD, 2026-10-19

Development-grade test of the REVISE recommendation of `../replicate_decisions_20261019/REPORT.md`: replace the
Gaussian pair-level noise of the replicate-identified Virtual Cell posterior by a Student-t scale mixture identified from
reference replicate differences, and check whether candidate progression (D2) and selected-pair calibration recover
while context selection (D1) keeps its gain. Test arena: HTS002 0.625 uM and 10 uM reads of the same (exposed)
compounds, opened once after the freeze.

**Verdict: HEAVY_TAIL_DOES_NOT_FIX_D2.** Pooled over 0.625 and 10 uM:
- `ht - rsd` D2 -0.007 [-0.011, -0.003]; `ht - raw` D2 +0.015 [-0.014, +0.046].
- `ht - raw` D1 +0.043 (Holm p 0.060).
- Selected-pair coverage 0.690. Compound-level noise reaches 0.749 but costs D2 -0.048.
- The frozen RSD D1 gain replicates in sign (+0.057), at half its 2.5 uM size.
- `verify.py` VERIFY OK.

| File | Content |
|---|---|
| `REPORT.md` | Result, verdict, what it does and does not show |
| `PROTOCOL.md` | Frozen protocol (method, arena, arms, hypotheses, thresholds, verdict rule) |
| `DEVELOPMENT_LOG.md` | Every pre-freeze design step and what it saw (2.5 uM only) |
| `FREEZE.json` | Hashes (study code, imported frozen RSD files, data), thresholds, grids, test-arena composition |
| `RESULT.json` | Write-once test record: per-(dose, block) records, pooled and per-dose aggregates, verdict |
| `dev/` | Write-once development records on the exposed 2.5 uM reads |

Code (maestro conda env; run from this folder):

```
python -B ht_run.py dev <tag> <block>     # development records, 2.5 uM only
python -B dev_explore.py <tag> [signal]   # development exploration, 2.5 uM only
python -B dev_noise_anatomy.py            # development diagnostic of the reference noise, 2.5 uM only
python -B freeze.py                       # write-once FREEZE.json (refuses if test-dose reads were loaded)
python -B ht_run.py evaluation            # write-once RESULT.json (requires FREEZE.json)
python -B verify.py [--replay]            # read-only verification
python -B -m pytest test_ht.py -p no:cacheprovider -q
```

* `ht_data.py`: frozen RSD arena with reads at any HTS002 dose; refuses test doses before the freeze.
* `ht_core.py`: Student-t tail fit from reference replicate differences, VB-EM posterior, predictive CDF, reference-only
  selection of nu.
* `ht_run.py`: arms, pooled stratified cluster bootstrap, verdict rule, stages.
* The frozen RSD modules (`rsd_core`, `rsd_data`, `rsd_run`) are imported from `../replicate_decisions_20261019` and never
  modified; their hashes are checked at freeze, at evaluation and by `verify.py`.
* `verify.py` and this README are read-only tooling/documentation written around the freeze and are not hashed in
  `FREEZE.json`; `evaluation_stage.log` is the test stage's console log. `cache/` holds regenerable read caches
  (git-ignored).

No LLM or paid call, no sealed tier, nothing committed.
