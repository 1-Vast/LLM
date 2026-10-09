# STATE feedback calibration

This registered development study retains fixed STATE-ST forecasts and the
authenticated 39-gene RNA readout. It tests a joint A/B prediction-error update
against the original independent-noise update, with an identical 146-candidate
menu and eight A purchases followed by five B commitments. Complete-cell outer
folds test the new readout/posterior; references overlap STATE pretraining and
the five other backgrounds were already exposed. No independent confirmation,
phenotype benefit, native MAP prediction or LLM-policy benefit is implied.

The result belongs in [EVIDENCE.md](../../EVIDENCE.md); primary-source reasoning
and metadata qualification are in [LITERATURE_AND_SCOPE.md](LITERATURE_AND_SCOPE.md).
Do not interpret the development retention gate as a risk certificate.

Restore the exact packet and sources listed in `FREEZE.json`. From the repository
root, using the maestro environment with NumPy and threadpoolctl:

```powershell
D:/anaconda/envs/maestro/python.exe -m pytest research/astra/state_feedback_repair_20261009/test_posterior.py
D:/anaconda/envs/maestro/python.exe research/astra/state_feedback_repair_20261009/run.py
D:/anaconda/envs/maestro/python.exe research/astra/state_feedback_repair_20261009/verify.py
```

The trial refuses to overwrite an existing output directory. Outputs are under
`outputs/paper_01286/state_feedback_repair/`; execution receipts belong in
`log/20261009/`. Original readout sources, freezes, weights and results remain
unchanged. The posterior is a small research component, not an alternative
production controller or a recreated MAP runtime.
