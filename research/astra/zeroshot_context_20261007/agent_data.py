"""Per-condition tables for the replicate-well acquisition task (depth-corrected).

Menu: drug-dose labels run in >=100 cells in at least two wells on different plates of every
held-out context (146 labels). Well roles are fixed by a label/plate hash, never by data:
  well A = first-profile (screen) well, purchasable; well B = independent replicate well, revealed
  only to score committed flags.
For context L, label c, well w on plate p_w, with M0 the panel mean in the same well:
  eta_w = Delta(L, c, p_w) - M0(c, p_w)
  z_w   = mean_g eta_w^2 - noise_L - noise_M0         (signed, depth-corrected, never clipped)
  y_w   = sign(z_w) sqrt(|z_w|)                         (root deviation energy; belief scale)
World features (well B, before purchase), all depth-corrected:
  zdisp  panel heterogeneity: mean over panel contexts of their own deviation energy around M0
  dev    basal-similarity deviation energy (M1 family selected in world development)
  state  mean_g devS^2 (held-out contexts only; STATE was trained on the panel)
Training contexts are used leave-one-context-out, simple world only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import world_models as wm  # noqa: E402

MIN_WELL_CELLS = 100


def replicated_labels(file: str, min_cells: int = MIN_WELL_CELLS):
    census = json.loads((HERE / "census" / f"{file}.json").read_text(encoding="utf-8"))
    by = {}
    for label, plate, n in census["condition_plate_counts"]:
        if label != wm.CONTROL and n >= min_cells:
            by.setdefault(label, []).append(plate)
    out = {}
    for label, plates in by.items():
        if len(plates) >= 2:
            ordered = sorted(plates, key=lambda p: hashlib.sha256(f"well-role:{label}:{p}".encode()).hexdigest())
            out[label] = (ordered[0], ordered[1])
    return out


def menu_labels():
    """Labels replicated in every held-out context (metadata census only)."""
    sets = [replicated_labels(f) for f in wm.HELDOUT.values()]
    common = set(sets[0])
    for s in sets[1:]:
        common &= set(s)
    wells = {label: sets[0][label] for label in sorted(common)}
    assert all(s[label] == wells[label] for s in sets for label in common), "well roles must agree across contexts"
    return wells


def root(z):
    z = np.asarray(z, dtype=np.float64)
    return np.sign(z) * np.sqrt(np.abs(z))


def _heterogeneity(panel, cols, exclude=None):
    """Depth-corrected mean deviation energy of panel contexts around their equal mean, per column."""
    avail = panel.avail[:, cols].copy()
    if exclude is not None:
        avail[exclude] = False
    k = avail.sum(0)
    d = panel.delta[:, cols].astype(np.float64)
    centre = (d * avail[..., None]).sum(0) / np.maximum(k, 1)[:, None]
    energy = (np.mean((d - centre[None]) ** 2, 2) - panel.noise0[:, cols]) * avail
    return energy.sum(0) / np.maximum(k - 1, 1)


def _dev_fn(panel, family, basal, W0, lam, exclude=None):
    """Deviation forecast and its own sampling variance for one panel column, per M1 family."""
    if family == "gate":
        def fn(j):
            g, _, ndd = panel.gate(basal, W0, [j], 0.0, exclude=exclude)
            return g[0], ndd[0]
        return fn
    Wd = panel.w_knn_dev(basal, exclude=exclude) if family == "knn" else panel.w_krr_dev(basal, lam, exclude=exclude)
    return lambda j: (panel.apply(Wd, [j])[0], panel.noise_of(Wd, [j])[0])


def _table(panel, delta_L, noise_L, devS, wells, keys_index, W0, dev_fn, exclude=None, context="", meta=None):
    rows = []
    for label, (pa, pb) in wells.items():
        if (label, pa) not in keys_index or (label, pb) not in keys_index:
            continue
        rec = {"context": context, "label": label, "drug": wm.parse_label(label)[0], "dose_uM": wm.parse_label(label)[1],
               "plate_A": pa, "plate_B": pb}
        ok = True
        for tag, plate in (("A", pa), ("B", pb)):
            i, j = keys_index[(label, plate)]
            if not np.isfinite(noise_L[i]):
                ok = False
                break
            m0 = panel.apply(W0, [j])[0]
            n0 = panel.noise_of(W0, [j])[0]
            eta = delta_L[i] - m0
            z = float(np.mean(eta ** 2) - noise_L[i] - n0)
            dvec, dn = dev_fn(j)
            rec[f"z_{tag}"] = z
            rec[f"y_{tag}"] = float(root(z))
            rec[f"noise_{tag}"] = float(noise_L[i] + n0)
            rec[f"zdisp_{tag}"] = float(_heterogeneity(panel, [j], exclude)[0])
            rec[f"dev_{tag}"] = float(np.mean(dvec ** 2) - dn)
            rec[f"m0energy_{tag}"] = float(np.mean(m0 ** 2) - n0)
            rec[f"state_{tag}"] = None if devS is None else float(np.mean(devS[i] ** 2))
            rec[f"state_dev_align_{tag}"] = None if devS is None else float(np.mean(devS[i] * dvec))
        if ok:
            if meta:
                rec.update(meta.get(rec["drug"].strip(), {"targets": None, "moa": None}))
            rows.append(rec)
    return rows


def heldout_table(name, panel, wells, m0_variant, dev_family, lam, meta=None):
    t = wm.target(name, panel)
    keys_index = {k: (i, int(t["panel_index"][i])) for i, k in enumerate(t["keys"])}
    W0 = panel.w_m0(m0_variant)
    fn = _dev_fn(panel, dev_family, t["basal"], W0, lam)
    return _table(panel, t["delta"], t["noise"], t["devS"], wells, keys_index, W0, fn, context=name, meta=meta)


def training_table(li, panel, wells, dev_family, lam, meta=None):
    """Leave-one-context-out simple-world rows for training context li (equal-weight M0)."""
    keys_index = {k: (j, j) for j, k in enumerate(panel.keys)}
    delta_L = panel.delta[li].astype(np.float64)
    noise_L = panel.noise[li]
    W0 = panel.avail.copy()
    W0[li] = False
    W0 = W0 / np.maximum(W0.sum(0), 1)
    fn = _dev_fn(panel, dev_family, panel.basal[li], W0, lam, exclude=li)
    return _table(panel, delta_L, noise_L, None, wells, keys_index, W0, fn, exclude=li, context=panel.files[li], meta=meta)


def drug_metadata():
    """Public Tahoe drug metadata (targets, MoA) keyed by drug name; both arms may read it."""
    import pandas as pd
    root_dir = HERE.parents[2]
    d = pd.read_parquet(root_dir / "tools/datasets/audit_results/20261001_state_prospective/knowledge_sources/tahoe_drugs.raw")
    out = {}
    for row in d.to_dict("records"):
        targets = row["targets"] if isinstance(row["targets"], str) else None
        moa = row["moa-fine"] if isinstance(row["moa-fine"], str) else None
        out[str(row["drug"])] = {"targets": targets, "moa": moa}
    return out


def cell_metadata(name):
    import pandas as pd
    root_dir = HERE.parents[2]
    c = pd.read_parquet(root_dir / "tools/datasets/audit_results/20261001_state_prospective/knowledge_sources/tahoe_cells.raw")
    rows = c[c.cell_name == name]
    drivers = sorted({f"{r.Driver_Gene_Symbol} {r.Driver_ProtEffect_or_CdnaEffect}" for r in rows.itertuples() if isinstance(r.Driver_Gene_Symbol, str)})
    organ = rows.Organ.iloc[0] if len(rows) else None
    return {"name": name, "organ": organ, "driver_variants": drivers[:12]}
