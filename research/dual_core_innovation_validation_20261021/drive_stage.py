"""Run all (held-out, variant, seed) jobs of a stage with bounded parallelism.  usage: python drive_stage.py STAGE EPOCHS HIDDEN SEEDS OUTDIR [VARIANTS]"""
import subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import ptv_data as D
stage, epochs, hidden, seeds, outdir = sys.argv[1], sys.argv[2], sys.argv[3], [int(s) for s in sys.argv[4].split(",")], sys.argv[5]
variants = sys.argv[6].split(",") if len(sys.argv) > 6 else ["full", "no_traj", "no_fp"]
part = D.partition()
if stage == "final":
    helds = ["ALL"]
else:
    cells = {"dev": ["HS578T", "HCC1937", "MCF7", "HCC1806", "BT549"], "sel": ["HCC1143", "MDA-MB-468", "DU4475", "MDA-MB-453", "MDA-MB-231"]}[stage]
    helds = cells
jobs = [(h, v, s) for h in helds for v in variants for s in seeds]
MAXP = 2; run = []
py = "D:/MAESTRO/tmp/gpu_venv/Scripts/python.exe"
t0 = time.time()
while jobs or run:
    run = [p for p in run if p.poll() is None]
    while jobs and len(run) < MAXP:
        h, v, s = jobs.pop(0)
        if (Path(outdir) / f"{stage}_{h}_{v}_s{s}.npz").exists():
            continue
        run.append(subprocess.Popen([py, str(Path(__file__).parent / "run_models.py"), stage, h, v, str(s), epochs, hidden, outdir]))
    time.sleep(5)
print("stage done", round(time.time() - t0))
