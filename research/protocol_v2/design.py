"""Study-design tables: which conditions each study planned for each compound, from metadata only.

File summary
- Path: research/protocol_v2/design.py
- Purpose: give protocol v2.1 a legal menu that the study design fixes before any outcome exists.
  Protocol v2 offered a condition only when the prepared outcome table had a row for it, and the
  prepared SciPlex3 table drops a replicate group with fewer than 20 surviving cells. Cell survival
  at a toxic dose is an outcome, so the menu moved with an outcome: 12 SciPlex3 conditions were
  profiled and then hidden (block 4 audit, D8).
- Core points:
  - SciPlex3. The release is a factorial screen: every compound screened in a (cell line, time)
    was plated at every dose of that screen. A condition is planned when the compound appears in
    the raw release's cell metadata (`obs`: cell line, perturbation, dose, time) for that cell line
    and time at any dose. No expression value, cell count threshold or QC field is read.
  - L1000 (GSE92742). A condition is planned when the release's instance metadata lists at least
    one plated well for it (`subset48/conditions.json`, aggregated from `inst_info`). Signature
    presence, replicate correlation and detection are outcomes and are not read.
  - A planned condition with no usable prepared row is a measurement that ran and failed QC
    (`contracts.Lifecycle.MEASURED_QC_FAILED`): it is offered, charged and never scored as a
    biological reading.
  - Tables are written once as CSV with a SHA-256 in a manifest (`write`), so later code reads the
    frozen design rather than recomputing it from a moving tree.
- Run: python -m research.protocol_v2.design --out DIR
- Interfaces: `sciplex3_design`, `l1000_design`, `by_compound`, `load`, `write`, `DESIGN_DIR`
- Depends on: h5py, pandas; research/biological_depth/prepare.py (`obs_column`);
  data/raw/sciplex3/SrivatsanTrapnell2020_sciplex3.h5ad; data/external/lincs_l1000_phase1/subset48
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DESIGN_DIR = ROOT / "outputs" / "protocol_v2_1_20260927" / "design"
SCIPLEX_RAW = ROOT / "data/raw/sciplex3/SrivatsanTrapnell2020_sciplex3.h5ad"
L1000_CONDITIONS = ROOT / "data/external/lincs_l1000_phase1/subset48/conditions.json"
SCIPLEX_CONTROLS = {"vehicle", "control", "dmso", "nan", "none", ""}
COLUMNS = ["cell_line", "time", "dose", "compound"]


def sciplex3_design(path: Path = SCIPLEX_RAW, *, compounds=None) -> pd.DataFrame:
    """Planned (cell line, time, dose nM, compound) of the SciPlex3 release, from `obs` metadata."""
    import h5py
    sys.path.insert(0, str(ROOT / "research/biological_depth"))
    from prepare import obs_column

    with h5py.File(path, "r") as handle:
        obs = handle["obs"]
        meta = pd.DataFrame({name: obs_column(obs, name) for name in ("cell_line", "perturbation", "dose_value", "time")})
    meta["compound"] = meta.perturbation.astype(str).str.strip()
    meta = meta[~meta.compound.str.lower().isin(SCIPLEX_CONTROLS)]
    meta["time"] = meta.time.astype(float)
    meta["dose"] = meta.dose_value.astype(float)
    meta = meta[meta.dose > 0]
    if compounds is not None:
        meta = meta[meta.compound.isin(set(compounds))]
    screened = meta[["cell_line", "time", "compound"]].drop_duplicates()
    doses = meta.groupby(["cell_line", "time"]).dose.unique()
    rows = [(r.cell_line, r.time, float(d), r.compound) for r in screened.itertuples()
            for d in doses[(r.cell_line, r.time)]]
    return pd.DataFrame(rows, columns=COLUMNS).sort_values(COLUMNS).reset_index(drop=True)


def l1000_design(path: Path = L1000_CONDITIONS) -> pd.DataFrame:
    """Planned (cell line, time h, dose nM, pert_id) of GSE92742, from plated-well metadata."""
    frame = pd.DataFrame(json.loads(path.read_text(encoding="utf-8")))
    frame = frame[frame.n_wells.astype(int) >= 1]
    out = pd.DataFrame({"cell_line": frame.cell_id, "time": frame.time_h.astype(float),
                        "dose": (frame.dose_um.astype(float) * 1000.0).round(6), "compound": frame.pert_id})
    return out.drop_duplicates().sort_values(COLUMNS).reset_index(drop=True)


def by_compound(frame: pd.DataFrame) -> dict:
    """compound -> frozenset of planned (cell line, time, dose) keys."""
    out: dict = {}
    for r in frame.itertuples():
        out.setdefault(r.compound, set()).add((r.cell_line, float(r.time), float(r.dose)))
    return {c: frozenset(v) for c, v in out.items()}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(out: Path = DESIGN_DIR) -> dict:
    """Write both design tables once; refuse to overwrite a table whose content differs."""
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"rule": __doc__.split("- Core points:")[1].split("- Run:")[0].strip(), "tables": {}}
    for name, frame in (("sciplex3", sciplex3_design()), ("l1000", l1000_design())):
        path = out / f"{name}_design.csv"
        text = frame.to_csv(index=False, lineterminator="\n").encode("utf-8")
        if path.exists() and path.read_bytes() != text:
            raise RuntimeError(f"design_table_changed:{path}")
        if not path.exists():
            path.write_bytes(text)
        manifest["tables"][name] = {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "rows": int(len(frame)),
                                    "compounds": int(frame.compound.nunique()), "sha256": _sha256(path)}
    (out / "manifest.json").write_bytes(json.dumps(manifest, indent=1).encode("utf-8") + b"\n")
    return manifest


@lru_cache(maxsize=4)
def load(dataset: str, directory: str = str(DESIGN_DIR)) -> dict:
    """The frozen design of `dataset` as compound -> planned keys; built in memory if not written yet."""
    path = Path(directory) / f"{dataset}_design.csv"
    if path.is_file():
        frame = pd.read_csv(path)
    else:
        frame = sciplex3_design() if dataset == "sciplex3" else l1000_design()
    return by_compound(frame)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(DESIGN_DIR))
    args = parser.parse_args()
    manifest = write(Path(args.out))
    for name, entry in manifest["tables"].items():
        print(name, entry["rows"], "planned conditions,", entry["compounds"], "compounds", entry["sha256"][:12])


if __name__ == "__main__":
    main()
