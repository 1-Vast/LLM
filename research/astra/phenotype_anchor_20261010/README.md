# Phenotype-anchored dual core (2026-10-10)

Does a frozen virtual cell (STATE `final.ckpt`) help an agent find the drugs that **selectively**
reduce an unseen cancer line's survival? Survival is measured in the same Tahoe-100M spheroid as
the RNA the world model predicts. [PROTOCOL.md](PROTOCOL.md) is the registered design,
[LITERATURE.md](LITERATURE.md) records the sources read, and `FREEZE.json` hashes everything
fixed before held-out access. Results and limits are in the
[evidence register](../../EVIDENCE.md#phenotype-anchored-dual-core--2026-10-10).

## Stages

| Stage | Command | Reads |
|---|---|---|
| 1 obs codes | `python obs_extract.py` | per-cell condition, plate, well, QC and phase codes (no expression) |
| 2 RNA | `python extract_expression.py` | 24 treated rows per well and 256 (held-out: 512) DMSO rows per plate of `obsm/X_hvg` |
| 3 gate | `python gate.py` | reference lines only: LOO hyperparameters, oracles, menu, WMVC gate |
| 3b phase readout | `python phase_classifier.py` | reference DMSO cells |
| freeze | `python freeze.py` | refuses if any held-out artefact exists |
| 4-5 held-out | `bash run_heldout.sh` | obs, RNA, STATE forecasts (target and permuted basal), LLM, evaluation, verification |

Bulk arrays live under `data/external/tahoe_phenotype_20261010/` (git-ignored). Every remote byte
range is hashed in `obs/ledgers` and `expression/ledgers`. Re-staged STATE assets are verified
against `STATE_STAGING.json`.

```bash
python -m pytest research/astra/phenotype_anchor_20261010/test_phenotype_anchor.py -o addopts= -q
python research/astra/phenotype_anchor_20261010/verify.py
```

`development/` holds the reference-only scripts that were run before the protocol, listed in its
section 9.
