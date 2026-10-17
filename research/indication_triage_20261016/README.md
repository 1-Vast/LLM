# Indication triage for new compounds: measure-or-predict, certified yield (draft protocol)

Status: **exploratory, draft protocol, not frozen.** Development ran on exposed PRISM 19Q4. No
PRISM 24Q2 response value has been downloaded or read.

## What this study asks

A campaign of 64 never-screened compounds faces a 545-line cancer panel. The campaign has two
budgets:

* 16 single-dose probe wells per compound on average;
* 32 follow-up slots, at most 3 per compound.

Which (compound, line) pairs should go to follow-up? `maestro_loop` decides for each compound
where to measure and where to predict:

1. a few seed wells;
2. a world-model posterior;
3. triage by event uncertainty;
4. one adaptive round;
5. a ranking by P(registered event);
6. a design-based yield certificate from a random audit of its own list.

It is compared with conventional workflows and its own non-adaptive ablation at the same wells and
slots. The only primary hypothesis (H1) is whether it puts more true selective events on the
follow-up list than the strongest of them.

## Development result (exposed 19Q4, exploratory)

«README_RESULTS»

## Files

| File | Role |
|---|---|
| `PROTOCOL.md` | the draft pre-registration: cost model, arms, endpoint, power, certificate, stop rules |
| `common.py` | endpoint, campaign and tie-break rules inherited from knowledge_reality |
| `build.py` | development tables and the probe-noise estimate (`BUILD.json`) |
| `world.py` | world model: structure prior, scale-mixture covariance, exact-endpoint event probabilities |
| `policy.py` | every arm, the probe oracle for development, grading and the certificate |
| `develop.py` | tuning on folds 0-1, estimation on folds 2-4 (`DEVELOPMENT.json`) |
| `power.py` | sealed power, `MIN_ACTIVE` and the development gate (`POWER.json`) |
| `verify.py` | seal check, consistency, power replay, quoted numbers, registry |

## Reproduce

From this folder, with Python 3.14 (numpy, pandas, rdkit):

```
python -B build.py      # about 20 s; writes tmp/indication_triage_20261016/tables.npz
python -B develop.py    # about 15 min
python -B power.py
python -B verify.py     # add --replay to rerun develop.py and compare
```

## Not yet built (needed before a freeze)

* `confirm.py`: lock, outcome oracle with a hash-chained access log, the one-shot sealed run,
  and grading.
* `FREEZE.json`, written after the owner's review.
* Development for the L1000 substudy and the LLM agent arm. Both are registered in PROTOCOL.md
  §11 and are not run.
