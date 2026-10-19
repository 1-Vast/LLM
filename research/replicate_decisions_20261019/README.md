# Replicate-identified Virtual Cell decisions (RSD), 2026-10-19

Development-grade study on exposed PRISM 19Q4 data. Can a Virtual Cell posterior whose signal and noise geometry is
identified from replicate plates of reference compounds improve one-read research decisions on new compound classes,
when the decisions are graded on a replicate plate that no policy can read?

Read in this order:

| File | Content |
|---|---|
| `REPORT.md` | Final report: results, what is demonstrated / unsupported / future, recommendation |
| `EVIDENCE_MAP.md` | What earlier MAESTRO studies established before this one |
| `LITERATURE.md` | Verified literature tables (2024+), access level, same-mechanism-under-other-names check |
| `CANDIDATES.md` | Three candidate directions, trade-offs, selection, roles of Agent and VC, novelty claim |
| `PROTOCOL.md` | Frozen protocol (hypotheses, roles, endpoints, arms, statistics, stopping rules) |
| `DEVELOPMENT_LOG.md` | Every pre-freeze design change and defect, with what it saw |
| `FREEZE.json` | Code/protocol/data hashes, environment, thresholds, grid, arena audit, role lists (exposure manifest) |
| `SEARCH.json`, `SEARCH_v2.json` | Search block (development) records: first pass and final procedure |
| `SELECTION.json` | Go/no-go gate on the selection block (read once) |
| `EVALUATION.json` | Evaluation block (read once) with the pre-specified verdict |
| `DIAGNOSTIC_D2.json` | EXPLORATORY post hoc diagnosis of the D2 failure (`diagnose_d2.py`); changes no verdict |

**Verdict (evaluation block):** H1-D1 context selection SUPPORTED (`rsd - raw` +0.118 [+0.084, +0.157], above delta
0.067; equals two raw reads at half the wells; cross-run +0.090). H1-D2 candidate progression NOT_SUPPORTED (-0.008).
Knowledge-gradient escalation = exploit-first; chemistry prior hurts new classes; selected-candidate optimism +0.07 vs
+1.08 for raw reads, but selected-pair coverage 0.675. Recommendation: REVISE the Gaussian pair-noise assumption.

Code (maestro conda env, Python 3.11; run from this folder):

```
python -B rsd_run.py search|search2|selection|evaluation   # write-once stages (all already run)
python -B verify.py            # read-only: freeze hashes, stage rules, verdict recomputed
python -B verify.py --replay   # also re-runs the evaluation block and compares headline estimates
python -B -m pytest test_rsd.py -p no:cacheprovider -q     # isolation / poisoning / accounting checks (real arena)
```

* `rsd_data.py`: arena (identity audit, families, clusters, roles, purging, replicate roles); reads only metadata for
  roles. Cached reads go to `cache/` (regenerable).
* `rsd_core.py`: Virtual Cell (chemistry prior + replicate-identified signal/noise covariance), reference-only inner
  selection, baselines, decisions, sealed `Evaluator`.
* `rsd_run.py`: arms, cluster bootstrap, escalation agent (D3), calibration, stage gates, verdict rule.
* `freeze.py`: wrote `FREEZE.json` (write-once). `verify.py` and `diagnose_d2.py` were written after the freeze and are
  not frozen (read-only tooling / exploratory diagnosis).

No LLM or paid call, no sealed tier opened, nothing committed.
