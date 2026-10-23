# Execution notes and reproducibility

The repair was developed independently of the original frozen package. No
changes were made to production `src/`, repository tests or the other session's
`.build-1024-dgm-revision`. No commit or push was made.

1. Installed pytest 9.1.1 into the existing isolated CUDA environment under
   `tmp/gpu_venv`. The project `.venv` and system environments were not changed.
2. Fixed a CLI import-path problem exposed outside pytest: the configured client
   needs both repository root and `src` on the import path. A direct CLI-help test
   now covers that path.
3. Trained 30 epochs twice with seed-before-construction and verified bitwise
   equality on this installed CUDA/runtime. This does not promise equality across
   hardware or torch versions. Training/preparation took 46.35 seconds and the
   independent retraining check took 43.91 seconds.
4. The first API reply was truncated at 1,500 completion tokens and failed JSON
   parsing. Its actual usage was recorded and the predeclared fallback was used.
   There was no retry or fabricated valid reply.
5. After five requests, the sixth full prompt exceeded the *conservative token
   reservation*, although actual spent tokens remained below 24,000. The driver
   halted before sending it. Resume was implemented/tested, and repeated JSON
   keys and prior rationale prose were compacted while preserving numeric
   episode evidence and parent code. The sixth request then reserved 6,065
   tokens against 8,021 remaining; final actual total was 18,043. No previous
   proposal or episode was rerun. This is a disclosed implementation adjustment
   during selection, before the regression freeze; the budget was not enlarged.
6. Frozen selected programs were evaluated once by this repair on previously
   exposed old-final data. All nine arms completed. No output-driven changes
   were made to programs or model updates afterward.
7. Verification found documented concurrent cleanup of nonfrozen original files.
   The whole-directory snapshot failure is preserved as exit 2, while original
   frozen science and repair-runtime checks are performed. The verifier-only
   amendment also corrects a mistaken requirement for six different prompts:
   the two arms deliberately share their first matched root prompt; each arm's
   three prompts are distinct. No evaluation result or freeze was regenerated.

The original loader physically loads the public outcome arrays in the trusted
parent. Outcome separation is enforced at the candidate-process and update-input
boundary, not by pretending those historical outcomes are still sealed.

## Commands

Completed run artifacts must not be overwritten. These commands demonstrate the
entry points; preparation refuses an existing prepared run and selection refuses
an already completed selection.

```powershell
tmp/gpu_venv/Scripts/python.exe -B research/dual_core_innovation_validation_20261021_repair1/prepare_replay.py
tmp/gpu_venv/Scripts/python.exe -B research/dual_core_innovation_validation_20261021_repair1/run_replay.py --api
# Only an interrupted, unfinished selection:
tmp/gpu_venv/Scripts/python.exe -B research/dual_core_innovation_validation_20261021_repair1/run_replay.py --api --resume
# Safe repeatable software and artifact checks:
tmp/gpu_venv/Scripts/python.exe -B -m pytest -p no:cacheprovider research/dual_core_innovation_validation_20261021_repair1
tmp/gpu_venv/Scripts/python.exe -B research/dual_core_innovation_validation_20261021_repair1/verify.py
```

The last command currently returns 2 for the explicitly reported original
directory drift. It should not be converted to success by weakening the snapshot
or restoring another session's deliberately removed intermediates.
