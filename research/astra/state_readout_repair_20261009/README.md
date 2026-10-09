# Named STATE readout calibration

Canonical result and limits:
[EVIDENCE.md](../../EVIDENCE.md#state-readout-repair-20261009).
This uses fixed, authenticated STATE-ST scalar responses, not the unresolved
MAP decoder or new native STATE-SE predictions. All target backgrounds are
already exposed; reference contexts overlap STATE pretraining.

Restore the boundary-acquisition packet2 files and exact assets in `FREEZE.json`.
Run from `D:/MAESTRO` using the maestro environment (NumPy, SciPy, RDKit and
scikit-learn are needed by the reused frozen replay module):

```powershell
D:/anaconda/envs/maestro/python.exe -m pytest research/astra/state_readout_repair_20261009/test_readout.py
D:/anaconda/envs/maestro/python.exe research/astra/state_readout_repair_20261009/run.py
D:/anaconda/envs/maestro/python.exe research/astra/state_readout_repair_20261009/verify.py
```

`run.py` refuses to overwrite existing trial predictions/results. `verify.py`
checks the freeze, independently reconstructs coefficients and numerical outcomes,
poisons evaluator answers and executes a temporary complete numerical rerun.
It preserves trial results. Outputs live in
`outputs/paper_01286/state_readout_repair/`; execution receipts live in `log/20261009`.

Source recovery receipts describe inspected public releases/branches/discussions
without claiming an exhaustive search or posting any message. No deleted MAP
runtime is restored, no gene map is guessed and no production backend is enabled.
The simple readout is retained for a development prediction signal, not evidence
of higher final yield. Drug coefficients must remain bound to their complete
registered candidate/source/endpoint menu; they are not generic intervention effects.
