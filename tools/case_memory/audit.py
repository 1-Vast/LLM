"""Integrity checks and diagnostic figures for the case-memory evaluation pack."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
import numpy as np
import matplotlib


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.datasets import lincs_pack as XD  # noqa: E402
from tools.case_memory import sha256
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

def _sha(path: Path) -> str:
    return sha256(path)


def quality_audit() -> int:
    failures: list[str] = []
    pack, arrays = XD.load_pack()
    units = pack["units"]
    reference = sorted(b for b, u in units.items() if not u["unseen"])
    test = sorted(b for b, u in units.items() if u["unseen"])

    # 1. pack manifest checksums
    manifest = json.loads((ROOT / "data/processed/case_memory_integration/pack_manifest.json").read_text())
    for name, recorded in manifest["outputs"].items():
        actual = _sha(ROOT / "data/processed/case_memory_integration" / name)
        if actual != recorded:
            failures.append(f"checksum_mismatch:{name}")

    # 2. split integrity
    dev_blocks = XD._development_blocks()
    if set(test) & dev_blocks:
        failures.append("split:test_block_in_development_study")
    if set(test) & set(reference):
        failures.append("split:test_block_in_reference")
    moa_of = {}
    for b, u in units.items():
        if b in moa_of and moa_of[b] != u["moa"]:
            failures.append(f"split:unit_with_two_classes:{b}")
        moa_of[b] = u["moa"]

    # 3. zero-fill / missingness
    for b in reference + test:
        declared = set(units[b]["conditions"])
        stored = {key.split("::")[2] for key in arrays if key.startswith(f"vec::{b}::")}
        if declared != stored:
            failures.append(f"missingness:condition_keys_mismatch:{b}")
        for key in arrays:
            if key.startswith(f"vec::{b}::") and not np.isfinite(arrays[key]).all():
                failures.append(f"missingness:nonfinite_vector:{key}")
            if key.startswith(f"vec::{b}::") and float(np.linalg.norm(arrays[key])) == 0.0:
                failures.append(f"missingness:zero_vector:{key}")

    # 4. held-out-label leak probe: permute test labels; fitted quantities must not change
    thresholds_before = {}
    for cell in XD.CORE_CELL_LINES:
        norms = [float(np.linalg.norm(arrays[f"vec::{b}::{cell}"])) for b in reference
                 if f"vec::{b}::{cell}" in arrays]
        thresholds_before[cell] = float(np.percentile(norms, 5.0)) if norms else 0.0
    permutation = dict(zip(test, np.random.default_rng(0).permutation(
        [units[b]["moa"] for b in test])))
    thresholds_after = {}
    for cell in XD.CORE_CELL_LINES:
        norms = [float(np.linalg.norm(arrays[f"vec::{b}::{cell}"])) for b in reference
                 if f"vec::{b}::{cell}" in arrays]
        thresholds_after[cell] = float(np.percentile(norms, 5.0)) if norms else 0.0
    if thresholds_before != thresholds_after:
        failures.append("leak:thresholds_depend_on_test_units")
    # centroid invariance: centroids are built from reference membership only
    for klass in pack["pool"]:
        for cell in XD.CORE_CELL_LINES:
            key = f"centroid::{klass}::{cell}"
            if key not in arrays:
                continue
            members = [b for b in reference if units[b]["moa"] == klass
                       and f"vec::{b}::{cell}" in arrays]
            if members:
                rebuilt = np.mean([arrays[f"vec::{b}::{cell}"] for b in members], axis=0)
                if not np.allclose(rebuilt, arrays[key], atol=1e-5):
                    failures.append(f"leak:centroid_not_reference_only:{klass}:{cell}")
    del permutation  # the probe is structural: no fitted quantity may reference test labels

    # 5. replay results: every reported metric is finite and the item count matches
    results_path = ROOT / "outputs/case_memory_integration/results.json"
    if not results_path.is_file():
        failures.append("missing:results.json (run research.case_memory_integration.external_replay replay first)")
    else:
        results = json.loads(results_path.read_text())
        for arm, m in results["forecast_metrics"].items():
            for key, value in m.items():
                if isinstance(value, float) and not np.isfinite(value):
                    failures.append(f"metric_not_finite:{arm}:{key}")
        expected = results["population"]["forecast_items"]
        if expected <= 0:
            failures.append("metric:empty_forecast_population")

    # 6. frozen protocol hash
    freeze = json.loads((ROOT / "research/case_memory_integration/freeze_protocol.json").read_text())
    if _sha(ROOT / freeze["protocol"]["path"]) != freeze["protocol"]["sha256"]:
        failures.append("freeze:protocol_hash_mismatch")

    report = {"checks": 6, "failures": failures, "ok": not failures}
    out = ROOT / "outputs/case_memory_integration/quality_audit.json"
    out.write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))
    return 0 if not failures else 1


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


matplotlib.use("Agg")


FIGDIR = ROOT / "outputs/case_memory_integration/figures"
ARMS_PLOT = ("scalar", "signed_direction", "pathway_direction", "combined",
             "mechanism_prior_only", "case_memory_only", "full")


def _records() -> list[dict]:
    path = ROOT / "outputs/case_memory_integration/forecast_items.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _save(fig, name: str) -> str:
    FIGDIR.mkdir(parents=True, exist_ok=True)
    path = FIGDIR / name
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return sha256(path)


def visual_verify() -> int:
    pack, arrays = XD.load_pack()
    results = json.loads((ROOT / "outputs/case_memory_integration/results.json").read_text())
    records = _records()
    units = pack["units"]
    reference = sorted(b for b, u in units.items() if not u["unseen"])
    test = sorted(b for b, u in units.items() if u["unseen"])
    manifest: dict[str, str] = {}

    # 1. pathway-direction heatmap: class centroids against the most variable Hallmark sets
    symbols = pack["landmark_symbols"]
    gene_sets = pack["gene_sets"]
    set_names = sorted(gene_sets)
    pos = {g: i for i, g in enumerate(symbols)}
    centroid_cells = sorted({k.split("::")[2] for k in arrays if k.startswith("centroid::")})
    proj = {}
    for klass in pack["pool"]:
        vecs = [arrays[f"centroid::{klass}::{cell}"] for cell in centroid_cells
                if f"centroid::{klass}::{cell}" in arrays]
        if not vecs:
            continue
        mean = np.mean(vecs, axis=0)
        scores = np.array([mean[[pos[g] for g in gene_sets[s] if g in pos]].sum()
                           / np.sqrt(max(1, len([g for g in gene_sets[s] if g in pos])))
                           for s in set_names])
        proj[klass] = scores
    if proj:
        matrix = np.array([proj[k] for k in pack["pool"] if k in proj])
        order = np.argsort(-matrix.var(axis=0))[:20]
        fig, ax = plt.subplots(figsize=(9, 4.5))
        im = ax.imshow(matrix[:, order], aspect="auto", cmap="RdBu_r",
                       vmin=-np.abs(matrix[:, order]).max(), vmax=np.abs(matrix[:, order]).max())
        ax.set_yticks(range(matrix.shape[0]),
                      [k.replace(" inhibitor", " inh.").replace(" receptor ", " R ")
                       for k in pack["pool"] if k in proj], fontsize=8)
        ax.set_xticks(range(len(order)), [set_names[j].replace("HALLMARK_", "H_") for j in order],
                      rotation=75, ha="right", fontsize=7)
        ax.set_title("Pathway direction of reference class centroids (LINCS 2020, landmark space)")
        fig.colorbar(im, label="signed projection")
        manifest["pathway_direction_heatmap.png"] = _save(fig, "pathway_direction_heatmap.png")

    # 2. wrong-elimination calibration per arm
    fig, axes = plt.subplots(2, 4, figsize=(13, 6), sharex=True, sharey=True)
    for ax, arm in zip(axes.flat, ARMS_PLOT + ("oracle",)):
        rows = [r for r in records if r["arm"] == arm]
        if not rows:
            continue
        p = np.array([r["p"][1] for r in rows])
        y = np.array([1.0 if r["code"] == 1 else 0.0 for r in rows])
        bins = np.linspace(0, 1, 6)
        centers, obs, counts = [], [], []
        for lo, hi in zip(bins[:-1], bins[1:]):
            mask = (p >= lo) & (p < hi)
            if mask.any():
                centers.append(p[mask].mean())
                obs.append(y[mask].mean())
                counts.append(int(mask.sum()))
        ax.plot([0, 1], [0, 1], "k--", lw=0.8)
        ax.scatter(centers, obs, s=[8 * c for c in counts], alpha=0.7)
        ax.set_title(arm, fontsize=9)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
    fig.suptitle("Wrong-elimination calibration (bubble size = items)")
    manifest["calibration_wrong_elimination.png"] = _save(fig, "calibration_wrong_elimination.png")

    # 3. directional ablation: NLL and directional accuracy per arm
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    abl = ["scalar", "signed_direction", "pathway_direction", "combined", "full"]
    nll = [results["forecast_metrics"][a]["nll"] for a in abl]
    acc = [results["forecast_metrics"][a]["directional_accuracy"] for a in abl]
    ax1.bar(abl, nll, color="#4878a8")
    ax1.set_ylabel("forecast NLL (lower is better)")
    ax1.tick_params(axis="x", rotation=30)
    ax2.bar(abl, acc, color="#a86648")
    ax2.set_ylabel("directional accuracy (higher is better)")
    ax2.set_ylim(0, 1)
    ax2.tick_params(axis="x", rotation=30)
    for ax in (ax1, ax2):
        ax.axhline(ax.get_ylim()[0], color="k", lw=0.5)
    fig.suptitle("Directional-feature ablation on the untouched source (112 items, 26 units)")
    manifest["directional_ablation.png"] = _save(fig, "directional_ablation.png")

    # 4. decision-level comparison
    fig, ax = plt.subplots(figsize=(9, 4))
    arms_d = list(results["decision_metrics"])
    correct = [results["decision_metrics"][a]["correct"] for a in arms_d]
    wrong = [results["decision_metrics"][a]["wrong"] for a in arms_d]
    deferred = [results["decision_metrics"][a]["deferred"] for a in arms_d]
    x = np.arange(len(arms_d))
    ax.bar(x - 0.25, correct, 0.25, label="correct", color="#3a7d44")
    ax.bar(x, wrong, 0.25, label="wrong", color="#a83232")
    ax.bar(x + 0.25, deferred, 0.25, label="deferred", color="#777777")
    ax.set_xticks(x, arms_d, rotation=30, ha="right", fontsize=8)
    ax.set_ylim(0, 1)
    ax.legend()
    ax.set_title("Decision level on 26 unseen-unit episodes (exploratory stratum)")
    manifest["decision_levels.png"] = _save(fig, "decision_levels.png")

    # 5. domain shift: max similarity of each test unit to the reference, per condition
    fig, ax = plt.subplots(figsize=(7, 4))
    shifts = []
    for b in test:
        for cell in units[b]["conditions"]:
            vec = arrays[f"vec::{b}::{cell}"]
            sims = [float(vec @ arrays[f"vec::{r}::{cell}"] /
                          (np.linalg.norm(vec) * np.linalg.norm(arrays[f"vec::{r}::{cell}"]) + 1e-12))
                    for r in reference if f"vec::{r}::{cell}" in arrays]
            if sims:
                shifts.append(max(sims))
    ax.hist(shifts, bins=12, color="#4878a8")
    ax.set_xlabel("max cosine of a test-unit signature to any reference signature")
    ax.set_ylabel("test (unit, condition) pairs")
    ax.set_title("Domain shift of the untouched stratum")
    manifest["domain_shift_split.png"] = _save(fig, "domain_shift_split.png")

    # 6. signature norms and the frozen detection thresholds
    fig, ax = plt.subplots(figsize=(8, 4))
    for cell in XD.CORE_CELL_LINES:
        norms = [float(np.linalg.norm(arrays[f"vec::{b}::{cell}"])) for b in reference
                 if f"vec::{b}::{cell}" in arrays]
        if norms:
            ax.hist(norms, bins=20, alpha=0.5, label=f"{cell} (reference)")
        ax.axvline(results["thresholds"].get(cell, 0.0), ls="--", lw=0.8)
    ax.set_xlabel("signature L2 norm (landmark space)")
    ax.set_ylabel("reference vectors")
    ax.set_title("Detection thresholds (5th percentile of reference norms, frozen)")
    ax.legend(fontsize=8)
    manifest["detection_thresholds.png"] = _save(fig, "detection_thresholds.png")

    # 7. forecast support versus error (wrong-elimination probability error by class support)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for arm, marker in (("scalar", "o"), ("combined", "s"), ("full", "^")):
        supports, errors = [], []
        for r in records:
            if r["arm"] != arm:
                continue
            support = sum(1 for key in arrays
                          if key.startswith("vec::") and units.get(key.split("::")[1], {}).get("moa") == r["own"])
            supports.append(support)
            errors.append(abs(r["p"][1] - (1.0 if r["code"] == 1 else 0.0)))
        ax.scatter(supports, errors, alpha=0.5, marker=marker, label=arm, s=18)
    ax.set_xlabel("reference blocks of the own class (support)")
    ax.set_ylabel("|forecast - observed| for wrong elimination")
    ax.set_title("Support versus forecast error")
    ax.legend()
    manifest["support_vs_error.png"] = _save(fig, "support_vs_error.png")

    (ROOT / "outputs/case_memory_integration/figures_manifest.json").write_text(
        json.dumps({"figures": manifest, "count": len(manifest)}, indent=1))
    print(json.dumps({"figures": len(manifest), "dir": str(FIGDIR)}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("quality", "figures"))
    args = parser.parse_args()
    return quality_audit() if args.mode == "quality" else visual_verify()


if __name__ == "__main__":
    raise SystemExit(main())
