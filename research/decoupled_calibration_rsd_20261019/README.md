# Decoupled calibration RSD, 2026-10-19

Development-only test of a decoupled calibration layer for the replicate-identified Virtual Cell posterior:
- decisions (D1 context selection, D2 candidate progression) rank with the frozen Gaussian RSD posterior
  (`../replicate_decisions_20261019`);
- value claims and 80% predictive intervals for the chosen pairs come from the compound-level Student-t model of
  `../heavy_tail_rsd_20261019`.

Arena: the exposed HTS002 reads (0.625 and 10 uM primary, 2.5 uM secondary). No unopened arena is authorised, so the
confirmatory stage is blocked pending the owner's decision.

| File | Content |
|---|---|
| `REPORT.md` | Result, verdict, what it does and does not show |
| `PROTOCOL.md` | Frozen protocol (method, arena, arms, hypotheses, thresholds, verdict rule, blocked confirmatory stage) |
| `DEVELOPMENT_LOG.md` | Every pre-freeze step and what it saw (2.5 uM search block only) |
| `FREEZE.json` | Hashes (study files, imported frozen RSD and heavy-tail files, read caches, metadata), thresholds, composition |
| `DEV_RESULT.json` | Write-once development readout: per-unit records, pooled and per-dose aggregates, verdict |
| `dev/` | Write-once development record of the smoke run (2.5 uM search block) |

Code (maestro conda env; run from this folder):

```
python -B dc_run.py dev <tag> <block>     # development record, 2.5 uM only
python -B freeze.py                       # write-once FREEZE.json (refuses if DEV_RESULT.json exists)
python -B dc_run.py devread               # write-once DEV_RESULT.json (requires FREEZE.json)
python -B dc_run.py confirm               # refuses: no authorised unopened arena
python -B verify.py [--replay]            # read-only verification
python -B -m pytest test_dc.py -p no:cacheprovider -q
```

- **Imported frozen modules.** The RSD modules (`rsd_core`, `rsd_data`, `rsd_run`) and the heavy-tail modules
  (`ht_core`, `ht_data`, `ht_run`) are imported and never modified. Their hashes are checked at freeze, at the readout
  and by `verify.py`.
- **Reads.** All reads come from the heavy-tail study's existing caches. Nothing is written outside this folder.
- **Unfrozen files.** `verify.py` and this README are read-only tooling and documentation and are not hashed in
  `FREEZE.json`. `devread_stage.log` is the readout's console log.

No LLM or paid call, no sealed tier, nothing committed.
