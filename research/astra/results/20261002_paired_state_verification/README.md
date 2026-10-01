# Paired STATE technical verification

The historical plate1 baseline contains **30**, not 32, real control rows. We retained the frozen pool unchanged. Sixteen ordered indices were sampled once with replacement and used for each of three Trametinib actions. This is a technical development-fixture test, not a prospective biological or efficacy experiment.

Both runs succeeded, each invoking the official `run_tx_infer` once in its own maestro subprocess: one control forward with 30 rows and three planned-action forwards with 16 rows each. Eight actual forwards in total; zero physical experiments; cost unknown. The control inference path was not replaced. Planned batches remained homogeneous by action, retaining one-hot and batch metadata.

All planned actions used basal SHA256 `70d2bfeac1a861fa29188e30a1ae3b0a8d10cc78a2c871d3f77ceb645f891ad5`. Ordered source indices and original sample IDs are stored per action in `paired_trace.json`.

The 48 x 2,000 request output matrices were bitwise identical between v1 and v2: maximum absolute difference **0.0**. Predicted EGR1 means were 0.1424637288, 0.01764867455, and 0.0 for 0.05, 0.5, and 5.0 uM. Of 96,000 returned request values, 90,743 were zero. These are model-returned post-activation outputs, not a pre-ReLU diagnosis or observed efficacy.

v1 ran before source-snapshot bookkeeping was added to the driver; its freeze receipt does not claim an execution-source SHA256. v1 is retained. Final v2 freezes and saves the execution source, and its receipt, source snapshot, freeze and current module hashes all match `bda8350632f5bf7d7e028b9c66dc3f8a03b6d86ddb50138f2c7ac94d4c1985e7`. Both versions restore the process-local hook; v2 records restoration by function identity. No numerical algorithm, output, menu, or threshold was changed between these versions.

Eight focused contracts passed in maestro: shared actual tensors, preserved metadata and control path, rejected count/menu/encoding/repeated-window changes, rejected missing actions and input mutation, and hook restoration after failure. The ASTRA adapter also imports successfully and resolves the existing production state runner, without copying it.

## Reproduce

Run from `D:\MAESTRO`, with a fresh output directory:

```powershell
& 'D:\anaconda\envs\maestro\python.exe' -m pytest research/astra/test_paired_state.py -q
& 'D:\anaconda\envs\maestro\python.exe' -c "from pathlib import Path; from research.astra.paired_state import run_comparison; import json; r=run_comparison(Path('D:/MAESTRO'), Path('D:/MAESTRO/tools/datasets/audit_results/20261001_state_response/sensitivity_v1/baseline_plate1.h5ad'), Path('D:/MAESTRO/research/astra/results/20261002_paired_state_reproduce'), [str([('Trametinib', x, 'uM')]) for x in (0.05,0.5,5.0)]); print(json.dumps(r)); raise SystemExit(0 if r['valid'] else 1)"
```

The recorded subprocess CLI is in each `receipt.json`. Predictions do not establish predecision state availability, independent biological state, prediction improvement, or utility gain. This comparison fixes the specific unpaired-basal confound; it does not validate the entire biological experiment.
