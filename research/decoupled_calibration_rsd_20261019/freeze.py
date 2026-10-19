"""Write FREEZE.json (write-once) after development on the 2.5 uM search block and before the development readout.

Records: line-ending-normalised hashes of this study's code, protocol, development log and development records; hashes
of the frozen RSD and heavy-tail files this study imports (each checked against its own study's FREEZE.json); hashes of
the already-opened read caches it reads; environment; pre-registered thresholds, arms, doses, bootstrap settings; the
arena composition (from the heavy-tail freeze for 0.625 and 10 uM). Refuses to run if FREEZE.json or DEV_RESULT.json
exists. Opens no read.
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
import dc_run as DC  # noqa: E402

D, HD = DC.D, DC.HD
out = HERE / "FREEZE.json"
if out.exists():
    raise SystemExit("FREEZE.json exists (write-once)")
if (HERE / "DEV_RESULT.json").exists():
    raise SystemExit("DEV_RESULT.json exists: the readout must follow the freeze")

# verify.py and README.md are read-only tooling/documentation and are not frozen
code = ["dc_run.py", "test_dc.py", "freeze.py", "PROTOCOL.md", "DEVELOPMENT_LOG.md"]
code += sorted(p.relative_to(HERE).as_posix() for p in (HERE / "dev").glob("*.json"))
imported = ["heavy_tail_rsd_20261019/" + f for f in ("ht_core.py", "ht_data.py", "ht_run.py", "FREEZE.json", "RESULT.json")]
imported += ["replicate_decisions_20261019/" + f for f in ("rsd_core.py", "rsd_data.py", "rsd_run.py", "FREEZE.json")]
ht_fz = json.loads((DC.HT / "FREEZE.json").read_text(encoding="utf-8"))
for f in ("ht_core.py", "ht_data.py", "ht_run.py"):
    if D.sha256_text(DC.HT / f) != ht_fz["sha256_text"][f]:
        raise SystemExit(f"heavy-tail {f} differs from the heavy-tail freeze")
rsd_fz = json.loads((DC.RSD / "FREEZE.json").read_text(encoding="utf-8"))
for f in ("rsd_core.py", "rsd_data.py", "rsd_run.py"):
    if D.sha256_text(DC.RSD / f) != rsd_fz["sha256_text"][f]:
        raise SystemExit(f"RSD {f} differs from the RSD freeze")
caches = {}
for dose in DC.PRIMARY_DOSES + DC.SECONDARY_DOSES:
    names = DC.require_cache(dose)
    if len(names) != 1:
        raise SystemExit(f"expected one read cache for {dose} uM, found {names}")
    z = np.load(HD.CACHE / names[0], allow_pickle=False)
    if str(z["lfc_sha256"]) != ht_fz["data_sha256"]["data/external/prism_19q4/raw/secondary-screen-logfold-change.csv"]:
        raise SystemExit(f"read cache {names[0]} was not built from the frozen log-fold-change file")
    caches[names[0]] = D.sha256(HD.CACHE / names[0])
data = [D.TREAT, D.CELLS, D.POOLS]

rec = dict(
    frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    note="Frozen after the 2.5 uM search-block development smoke run and before the pre-registered development readout. "
         "All reads are already opened (exposed); no unopened arena is authorised, so the confirmatory stage is blocked.",
    grade="DEVELOPMENT_ONLY",
    sha256_text={c: D.sha256_text(HERE / c) for c in code},
    imported_frozen_sha256_text={f: D.sha256_text(HERE.parent / f) for f in imported},
    read_cache_sha256=caches,
    data_sha256={p.relative_to(D.ROOT).as_posix(): D.sha256(p) for p in data},
    environment=dict(python=sys.version.split()[0], platform=platform.platform(), numpy=np.__version__, pandas=pd.__version__,
                     scipy=scipy.__version__, rdkit=__import__("rdkit").__version__, interpreter=sys.executable),
    primary_doses=list(DC.PRIMARY_DOSES), secondary_doses=list(DC.SECONDARY_DOSES), blocks=list(DC.BLOCKS),
    arms=list(DC.ARMS), rank_by=DC.RANK_BY, contrasts=[f"{a}-{b}" for a, b in DC.CONTRASTS],
    coverage_contrasts=[f"{a}-{b}" for a, b in DC.COV_CONTRASTS], levels=list(DC.LEVELS),
    thresholds=DC.THRESHOLDS, n_boot=DC.N_BOOT, seed=DC.SEED, wells_per_read=DC.WELLS_PER_READ,
    compound_candidates=[DC.H.cand_key(c) for c in DC.COMPOUND_CANDS],
    arena_composition={d: ht_fz["test_arena_composition"][d] for d in ("0.625", "10.0")},
    confirmatory=dict(status="BLOCKED_NO_AUTHORISED_UNOPENED_ARENA",
                      rule="an independent tier needs the owner's authorisation and a frozen amendment; not chosen here"),
)
out.write_text(json.dumps(rec, indent=1), encoding="utf-8", newline="\n")
print("frozen", rec["frozen_utc"])
