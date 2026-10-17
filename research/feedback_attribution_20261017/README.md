# Feedback attribution (study `feedback_attribution_20261017`)

The context-transfer confirmation (`research/context_transfer_20261017`) returned CONFIRMED. Its
claims amendment (`CLAIMS.json` there) shows that only one effect is established: four measured
responses, used to update a low-rank model, improved the next twelve choices on Beat AML. This
study does two things:

* **Audit (Phase 1).** It audits the implementation and evidence behind that result: claim
  mapping, resource units, missingness, event-probability coherence, planning and inner selection.
  The findings are in `AUDIT.md`.
* **Attribution (Phase 2).** It runs a pre-registered attribution of the gain on the same data.
  All groups share four probe reads, then differ in prior (population, RNA, drug-specific state
  models) and update (none, low-rank, overall sensitivity only, deranged).

**Result (development).**

* All four registered contrasts are Holm-positive, and none clears 0.05 at its lower bound:
  * feedback without RNA;
  * RNA once feedback is present;
  * RNA prior against the model's population state;
  * low-rank against an overall-sensitivity update.
* The RNA prior does not beat the empirical item prior, and a drug-specific ridge on the same PCs
  beats it.
* The confirmed engine is not shown better than that ridge.
* A coherent event score and eight probes instead of four each help.
* No selector beats tuned exploit-first.

See `REPORT.md`.

**Status: development.** Beat AML is exposed, so no result here confirms a method. Corrected
algorithms live in this folder, not in `src/`. The promoted modules gained documentation and
status markers only (`RULE_STATUS`, `SELECTION_STATUS`), and their behaviour is unchanged.

## Files

| File | Role |
|---|---|
| `PROTOCOL.md` | pre-registration (frozen 2026-10-17T06:45:10Z, before any group outcome) |
| `AUDIT.md` | Phase 1 audit: findings, evidence, where each is fixed or recorded, what stays blocked |
| `RELATED_WORK.md` | verified bibliographic positioning |
| `REPORT.md` | results of the registered analysis and the diagnostics |
| `RESULTS.json` | the registered analysis, written once; `verify.py` recomputes it |
| `DEVIATIONS.json` | deviations from the protocol (not hashed by the freeze) |
| `COST_UNITS.json`, `MISSINGNESS.json`, `COHERENCE.json`, `DECOMPOSITION.json` | audit and diagnostic outputs |
| `common.py` | domain access (the confirmation's Beat AML cache), folds, `paired`, `schedule_matrix` |
| `coherent.py` | development scorer: fixed event, uncertainty in G, global-only update, derangement, Monte Carlo reference |
| `planner.py` | joint Monte Carlo two-stage reference planner (EVSI, opportunity cost, round cost) |
| `attribution.py` | groups A–F, S, coherent variants and planner arms; `--summary` writes RESULTS.json once |
| `tuned.py` | per-procedure rank tuning and the calibrated (generate-then-calibrate) selector |
| `audit_units.py` | `COST_UNITS.json`: logical action → returned data → physical cost |
| `audit_missingness.py` | `MISSINGNESS.json`: reasons for missing pairs and their associations (design only) |
| `coherence.py` | `COHERENCE.json`: counterexample, martingale gaps, calibration (diagnostic) |
| `decomposition.py` | `DECOMPOSITION.json`: variance components, technical noise, what each prior predicts (diagnostic) |
| `test_science.py` | properties the scorer, planner, selector and runner must have, on synthetic data |
| `freeze.py`, `verify.py` | write the freeze once; check it and recompute RESULTS.json from cached records |

## Running

Run every command from this folder, in the `maestro` conda environment
(`D:\anaconda\envs\maestro\python.exe`). The Beat AML domain cache comes from
`context_transfer_20261017/data_beataml.py`.

```
python -m pytest -q test_science.py
python -B audit_units.py
python -B audit_missingness.py
python -B attribution.py primary          # also rank10, rank40, probes_vc, design, panel80
python -B tuned.py
python -B attribution.py --summary        # RESULTS.json, once
python -B coherence.py
python -B decomposition.py
python -B verify.py
```

Records and caches are written to `tmp/feedback_attribution_20261017/`.
