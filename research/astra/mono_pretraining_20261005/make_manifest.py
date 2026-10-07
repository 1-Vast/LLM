"""Write RUN_MANIFEST.json: environment, commands, timings, hashes of every output, access counts and disclosures."""
import json
import platform
import sys
import time

import numpy as np
import pandas as pd
import scipy
import sklearn
import torch

from . import common as cm


def main():
    out = cm.HERE / "RUN_MANIFEST.json"
    if out.exists():
        raise FileExistsError("manifest exists; write a new one with a new name")
    outs = {}
    for sub in ("results", "decisions", "literature", "data_s0", "archive_v1"):
        for p in sorted((cm.HERE / sub).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and "sources" not in p.parts and p.suffix not in (".npz",):
                outs[str(p.relative_to(cm.ROOT)).replace("\\", "/")] = cm.file_sha256(p)
    for p in sorted(cm.HERE.glob("*")):
        if p.is_file() and p.name != "RUN_MANIFEST.json":
            outs[str(p.relative_to(cm.ROOT)).replace("\\", "/")] = cm.file_sha256(p)
    log = [json.loads(x) for x in cm.ACCESS_LOG.read_text(encoding="utf-8").splitlines()]
    manifest = dict(
        written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        study="mono_pretraining_20261005", status="EXPLORATORY; E sealed (never evaluated); v1 retained, v1.1 repair development-only",
        freezes=dict(v1=cm.file_sha256(cm.FREEZE_V1), v1_1=cm.file_sha256(cm.FREEZE)),
        environment=dict(python=sys.version, platform=platform.platform(), numpy=np.__version__, pandas=pd.__version__,
                         scipy=scipy.__version__, sklearn=sklearn.__version__, torch=torch.__version__, device="cpu",
                         workers=3, threads_per_worker=1),
        commands=["run_s1 checks|select|pretrain|g1", "run_s2 dev --workers 3 (v1 grid, archive_v1 code)",
                  "analyze dev (v1)", "posthoc_ceiling", "posthoc_reliability",
                  "run_s2 dev --workers 3 (v1.1 grid)", "analyze dev (v1.1)", "pytest research/astra/mono_pretraining_20261005"],
        timings_wall=dict(s1_select_s=16, s1_pretrain_127_fits_min=7.6, s2_dev_v1_min=20, s2_dev_v1_1_min=41),
        api_calls=0, llm_calls=0, paid_cost_usd=0.0,
        outcome_reads_logged=len(log), outcome_reads_purposes=sorted({e["purpose"] for e in log}),
        e_lines="combination outcomes of E lines were loaded in the panel but not used for any target, history or statistic;"
                " no E evaluation was run; mono labels of E lines were used in HD-fold mono pretraining (mono only)",
        disclosures=["agent B printed first rows of 7 Jaaks supplementary workbooks (aggregate published statistics for 2-3 breast combinations)",
                     "agent C masked E outcome columns in its verification scripts"],
        deviations=["D1 tier Y fold-wise Jaaks exclusion (design-only protocol excluded all Jaaks lines)",
                    "D2 rotation-invariant combination features", "BCE call head dropped", "10 history draws instead of 3 seeds",
                    "K=10 permutations", "v1.1 grid repair after v1 outcomes were seen (verification finding)"],
        output_sha256=outs)
    out.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    print(f"{len(outs)} files hashed")


if __name__ == "__main__":
    main()
