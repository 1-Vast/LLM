"""One-shot final-stage orchestration (run only after FREEZE.json): claim the stage, train M1/M2 (30 epochs) and M3 (45 epochs), seeds 0 and 1, on dev+sel
with the 7 final lineages held out, then run the frozen evaluation.  Uses the isolated GPU interpreter.  usage: python run_final.py"""
import subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import ptv_data as D
PY = "D:/MAESTRO/tmp/gpu_venv/Scripts/python.exe"
OUT = str(HERE / "RUN" / "final")
t0 = time.time()
D.open_stage("final")
for variants, epochs in (("full,no_traj", "30"), ("no_fp", "45")):
    subprocess.run([PY, str(HERE / "drive_stage.py"), "final", epochs, "16", "0,1", OUT, variants], check=True)
subprocess.run([PY, str(HERE / "final_eval.py"), "final"], check=True)
print("final done", round(time.time() - t0))
