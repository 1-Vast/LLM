"""Write FREEZE.json (write-once): code/protocol hashes, data hashes, environment, frozen thresholds and grid."""
import datetime
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import sklearn

import rsd_data as D
import rsd_run as R

HERE = Path(__file__).resolve().parent
out = HERE / "FREEZE.json"
if out.exists():
    raise SystemExit("FREEZE.json exists (write-once)")
search = json.loads((HERE / "SEARCH.json").read_text(encoding="utf-8"))
if search["decision"] != "CONTINUE_TO_FREEZE":
    raise SystemExit("search gate did not pass")
code = ["rsd_core.py", "rsd_data.py", "rsd_run.py", "test_rsd.py", "freeze.py", "PROTOCOL.md", "SEARCH.json", "SEARCH_v2.json",
        "search_code_sha256.txt", "search2_code_sha256.txt", "DEVELOPMENT_LOG.md"]
data = [D.TREAT, D.LFC, D.CELLS, D.POOLS, D.PRIM_TREAT, D.PRIM_LFC]
t, lines, Tsim, audit, E = D.build_arena()
rec = dict(
    frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    note="Frozen after the search stage, before any selection- or evaluation-block outcome was read by method code.",
    sha256_text={c: D.sha256_text(HERE / c) for c in code},
    data_sha256={p.relative_to(D.ROOT).as_posix(): D.sha256(p) for p in data},
    environment=dict(python=sys.version.split()[0], platform=platform.platform(), numpy=np.__version__, pandas=pd.__version__,
                     scipy=scipy.__version__, sklearn=sklearn.__version__, rdkit=__import__("rdkit").__version__,
                     interpreter=sys.executable),
    practical_threshold=search["practical_threshold"],
    headroom_search=search["headroom"],
    inner_grid=dict(vc=R.GRID, pca=list(R.PCA_GRID)),
    escalation_fraction=R.ESC_FRAC, n_boot=R.N_BOOT, wells_per_read=R.WELLS_PER_READ,
    arena=dict(audit, refusals=sorted(audit["refusals"])),
    roles={blk: sorted(t.core[t.role == blk]) for blk in ("reference", "search", "selection", "evaluation")},
    purged=t.attrs["purged"],
)
out.write_text(json.dumps(rec, indent=1), encoding="utf-8", newline="\n")
print("frozen", rec["frozen_utc"], rec["practical_threshold"])
