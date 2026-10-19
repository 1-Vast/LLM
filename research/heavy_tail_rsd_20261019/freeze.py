"""Write FREEZE.json (write-once) before any 0.625 or 10 uM read is loaded.

Records: line-ending-normalised hashes of this study's code, protocol, development log and development records; hashes
of the frozen RSD files this study imports (checked against the RSD study's own FREEZE.json); data file hashes;
environment; pre-registered thresholds, grids, bootstrap settings; the test-arena composition from metadata only.
Refuses to run if FREEZE.json exists or if any test-dose read cache exists (it would mean test reads were loaded).
"""
import datetime
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ht_core as H  # noqa: E402
import ht_data as HD  # noqa: E402
import ht_run as HR  # noqa: E402
import rsd_data as D  # noqa: E402
import rsd_run as R  # noqa: E402

out = HERE / "FREEZE.json"
if out.exists():
    raise SystemExit("FREEZE.json exists (write-once)")
test_cache = [p.name for p in (HERE / "cache").glob("reads_*.npz") if not p.name.startswith("reads_2p5uM_")] \
    if (HERE / "cache").exists() else []
if test_cache:
    raise SystemExit(f"test-dose reads were loaded before the freeze: {test_cache}")

# verify.py is read-only tooling and is not frozen (it can only be exercised once RESULT.json exists)
code = ["ht_core.py", "ht_data.py", "ht_run.py", "test_ht.py", "freeze.py", "dev_explore.py", "dev_noise_anatomy.py",
        "PROTOCOL.md", "DEVELOPMENT_LOG.md"]
code += sorted(p.relative_to(HERE).as_posix() for p in (HERE / "dev").glob("*.json"))
rsd_files = ["rsd_core.py", "rsd_data.py", "rsd_run.py", "FREEZE.json", "EVALUATION.json", "REPORT.md", "PROTOCOL.md"]
rsd_fz = json.loads((HD.RSD / "FREEZE.json").read_text(encoding="utf-8"))
for f in ("rsd_core.py", "rsd_data.py", "rsd_run.py"):
    if D.sha256_text(HD.RSD / f) != rsd_fz["sha256_text"][f]:
        raise SystemExit(f"frozen RSD file {f} differs from the RSD freeze")
data = [D.TREAT, D.LFC, D.CELLS, D.POOLS, D.PRIM_TREAT]

t, lines, Tsim, audit, E = HD.arena()
composition = {}
for dose in HD.TEST_DOSES:
    cols = HD.columns_at(t, dose)                                  # metadata only (treatment table)
    present = cols.colA.notna().to_numpy()
    row = {}
    for blk in HR.BLOCKS:
        purged = set(t.attrs["purged"][blk])
        refm = (t.role == "reference").to_numpy() & ~t.core.isin(purged).to_numpy()
        qm = (t.role == blk).to_numpy()
        row[blk] = dict(queries=int((qm & present).sum()), queries_absent=int((qm & ~present).sum()),
                        references=int((refm & present).sum()), references_absent=int((refm & ~present).sum()))
    composition[str(dose)] = row

rec = dict(
    frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    note="Frozen after development on the exposed 2.5 uM reads, before any 0.625 or 10 uM read was loaded by this study.",
    sha256_text={c: D.sha256_text(HERE / c) for c in code},
    rsd_frozen_sha256_text={f: D.sha256_text(HD.RSD / f) for f in rsd_files},
    data_sha256={p.relative_to(D.ROOT).as_posix(): D.sha256(p) for p in data},
    environment=dict(python=sys.version.split()[0], platform=platform.platform(), numpy=np.__version__, pandas=pd.__version__,
                     scipy=scipy.__version__, rdkit=__import__("rdkit").__version__, interpreter=sys.executable),
    test_doses=list(HD.TEST_DOSES), blocks=list(HR.BLOCKS), arms=list(HR.ARMS), contrasts=[f"{a}-{b}" for a, b in HR.CONTRASTS],
    thresholds=HR.THRESHOLDS, n_boot=HR.N_BOOT, seed=HR.SEED, level=HR.LEVEL,
    candidates=[H.cand_key(c) for c in HR.CANDS],
    nu_grid=list(H.NU_GRID), nu_ml_grid=list(H.NU_ML_GRID), quadrature=dict(k_lambda=H.K_QUAD, k_diff=H.K_DIFF),
    vb=dict(n_iter=H.N_ITER, tol=H.TOL), gaussian_inner_grid=dict(vc=R.GRID, pca=list(R.PCA_GRID)),
    test_arena_composition=composition,
)
out.write_text(json.dumps(rec, indent=1), encoding="utf-8", newline="\n")
print("frozen", rec["frozen_utc"])
