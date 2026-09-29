"""QA acceptance gate for sciplex_pilot_v2 (construction protocol v2).

File summary
- Path: tools/datasets/qa_sciplex_pilot_v2.py
- Purpose: structural/scientific-contract gate with nonzero exit on failure, plus
  descriptive diagnostics and figures that use only valid contrasts and retain negative
  effects. Descriptive thresholds are pre-stated feature-row counts, NOT differential
  expression or biology certificates.
- Exit: 0 if all gate checks pass, 1 otherwise (diagnostics never affect the exit code).
- Run: `python -m tools.datasets.qa_sciplex_pilot_v2`
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.case_memory import sha256

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/processed/sciplex_pilot_v2"
QA = ROOT / "outputs/sciplex_pilot_v2"
SRC = ROOT / "data/external/sciplex_family"

SEED = 20260929
DESCRIPTIVE_THRESHOLD = 0.1

gates: list[dict] = []
diagnostics: list[dict] = []


def gate(name: str, passed: bool, detail: str) -> bool:
    gates.append({"name": name, "passed": bool(passed), "detail": detail})
    print(("GATE PASS " if passed else "GATE FAIL ") + name + " — " + detail)
    return bool(passed)


def diag(name: str, detail: str) -> None:
    diagnostics.append({"name": name, "detail": detail})
    print("DIAGNO " + name + " — " + detail)


def safe_sha256(path: Path) -> str:
    """Hash a file, returning 'MISSING_OR_UNREADABLE' instead of raising."""
    try:
        return sha256(path)
    except OSError:
        return "MISSING_OR_UNREADABLE"


def run_checks(out_dir: Path = OUT, qa_dir: Path = QA, src_dir: Path = SRC,
               make_figures: bool = True) -> tuple[int, list[dict]]:
    """Run all gate checks; return (exit_code, gates). Any unexpected exception (e.g. a
    corrupted or nonconforming package) becomes a FAILED gate and a nonzero exit."""
    del gates[:], diagnostics[:]
    try:
        return _run_checks_inner(out_dir, qa_dir, src_dir, make_figures)
    except Exception as exc:  # noqa: BLE001 - an invalid package must fail, not crash
        gates.append({"name": "qa_execution_completed", "passed": False,
                      "detail": f"QA could not complete on this package: {exc!r}"})
        return 1, list(gates)


def _run_checks_inner(out_dir: Path, qa_dir: Path, src_dir: Path,
                      make_figures: bool) -> tuple[int, list[dict]]:
    manifest = json.loads((out_dir / "pilot_manifest.json").read_text())

    # --- 1. source and derived checksums (run first: no artifact loading) ---
    ok = True
    for tag, fn in (("sciplex2", "SrivatsanTrapnell2020_sciplex2.h5ad"),
                    ("sciplex4", "SrivatsanTrapnell2020_sciplex4.h5ad")):
        ok &= safe_sha256(src_dir / fn) == manifest["sources"].get(tag, {}).get("sha256")
    gate("source_checksums", ok, "h5ad sha256 match manifest")
    derived_ok = True
    bad_files = []
    for f, h in manifest.get("content_hashes", {}).items():
        actual = safe_sha256(out_dir / f)
        if actual != h:
            derived_ok = False
            bad_files.append(f)
    gate("derived_checksums", derived_ok,
         "all output file hashes match manifest" if derived_ok
         else f"mismatched: {bad_files}")

    # --- load artifacts as a checked step (a corrupted package fails, not crashes)
    try:
        with np.load(out_dir / "response_arrays.npz", allow_pickle=False) as archive:
            z = {key: archive[key] for key in archive.files}
        genes = (out_dir / "response_genes.txt").read_text().splitlines()
        prov = pd.read_csv(out_dir / "observation_provenance.csv")
        cls = pd.read_csv(out_dir / "condition_classification.csv")
        idx = pd.read_csv(out_dir / "response_index.csv")
        gmap = pd.read_csv(out_dir / "gene_mapping.csv")
        quar = pd.read_csv(out_dir / "quarantine_ledger.csv")
        recon = pd.read_csv(out_dir / "sample_sheet_reconciliation.csv")
        rescue = pd.read_csv(out_dir / "rescue_contrast_ledger.csv")
        wells = pd.read_csv(out_dir / "well_summaries.csv")
        gate("package_files_readable", True, "all package artifacts load")
    except Exception as exc:  # noqa: BLE001
        gate("package_files_readable", False,
             f"package artifact missing or corrupted: {exc!r}")
        return 1, list(gates)

    # --- 2. shapes and axis identity ----------------------------------------
    n_feat = manifest["gene_mapping"]["input_feature_rows"]
    n_s2 = int((prov.study == "sciplex2").sum())
    n_s4 = int((prov.study == "sciplex4").sum())
    shapes_ok = (z["means::sciplex2"].shape == (n_s2, n_feat)
                 and z["effects::sciplex2"].shape == (n_s2, n_feat)
                 and z["means::sciplex4"].shape == (n_s4, n_feat)
                 and z["effects::sciplex4"].shape == (n_s4, n_feat)
                 and len(genes) == n_feat
                 and list(gmap["feature_name"].astype(str)) == genes
                 and list(gmap["feature_index"]) == list(range(n_feat)))
    gate("mean_effect_shapes_and_axis_identity", shapes_ok,
         f"means/effects match manifest rows ({n_s2}, {n_s4}) x features ({n_feat}); "
         "gene_mapping axis identical to response_genes.txt")

    # --- 3. availability masks and missingness representation ---------------
    mask_ok = True
    detail = []
    for tag, n_rows in (("sciplex2", n_s2), ("sciplex4", n_s4)):
        eff = z[f"effects::{tag}"]
        sub = idx[idx.block == tag].sort_values("row")
        avail = sub.available.to_numpy()
        nan_mask = np.isnan(eff).all(axis=1)
        if not (nan_mask == ~avail).all():
            mask_ok = False
            detail.append(f"{tag}: NaN rows != unavailable rows")
        finite = eff[avail]
        if not np.isfinite(finite).all():
            mask_ok = False
            detail.append(f"{tag}: available rows contain non-finite values")
        zero_rows = sub[sub.contrast_kind == "baseline_self"]
        for r in zero_rows.itertuples():
            if not np.allclose(eff[r.row], 0.0):
                mask_ok = False
                detail.append(f"{tag}: baseline_self row {r.row} not exactly zero")
    gate("availability_masks_and_missingness", mask_ok,
         "; ".join(detail) if detail else
         "NaN occurs exactly where unavailable (both directions); available rows finite; "
         "baseline self-contrasts are defined zeros")

    # --- 4. identity completeness and quarantine separation -----------------
    n_src = sum(manifest["studies"][t]["source_cells"] for t in ("sciplex2", "sciplex4"))
    n_ident = sum(manifest["studies"][t]["identifiable_cells"] for t in ("sciplex2", "sciplex4"))
    identity_ok = (len(quar) == n_src - n_ident
                   and (quar.reason == "missing_identity_fields").all()
                   and (quar.missing_fields.str.len() > 0).all()
                   and not any("nan" in k.lower() or "none" in k.lower()
                               for k in prov.condition_key)
                   and not prov.condition_key.str.contains("@nan|nan::|::nan|@@", regex=True).any())
    gate("identity_completeness_and_quarantine", identity_ok,
         f"quarantine ledger {len(quar)} rows == source-identifiable "
         f"({n_src}-{n_ident}); no missing-like tokens in any condition key")

    # --- 5. complete two-intervention classification ------------------------
    s4cls = cls[cls.study == "sciplex4"]
    rule_ok = True
    for r in s4cls.itertuples():
        c1 = str(r.first_intervention) == "control"
        c2 = str(r.second_intervention) == "control"
        expect = ("vehicle_vehicle" if c1 and c2 else
                  "agent1_only" if not c1 and c2 else
                  "agent2_only" if c1 and not c2 else "combination")
        if r.classification != expect:
            rule_ok = False
    n_a2 = int((s4cls.classification == "agent2_only").sum())
    n_a1 = int((s4cls.classification == "agent1_only").sum())
    n_combo = int((s4cls.classification == "combination").sum())
    gate("two_intervention_classification", rule_ok and n_a2 > 0,
         f"sciPlex4 classification follows the complete-intervention rule for all "
         f"{len(s4cls)} conditions: {n_a1} agent1_only, {n_a2} agent2_only "
         "(v1 mislabeled these as vehicle controls), {n_combo} combination".format(
             n_a1=n_a1, n_a2=n_a2, n_combo=n_combo))

    # --- 6. plate/cell control matching -------------------------------------
    s4 = prov[prov.study == "sciplex4"]
    s4_treat = s4[s4.contrast_kind == "treatment_vs_vehicle"]
    s4_avail = s4[s4.available]
    match_ok = bool(
        s4_treat.control_matching_rule.eq("same_cell_same_plate_dmso_dmso").all()
        and len(s4_treat) > 0)
    if len(s4_treat) > 0:
        treat_plate = s4_treat.condition_key.str.split("@").str[2]
        ctrl_plate = s4_treat.control_key.str.split("@").str[2]
        match_ok &= bool((treat_plate == ctrl_plate).all())
    unavail_reasons_ok = bool(
        s4[~s4.available].unavailability_reason.str.len().gt(0).all())
    baseline_rule_ok = bool(
        s4[s4.contrast_kind == "baseline_self"].control_matching_rule.isna().all())
    s2 = prov[prov.study == "sciplex2"]
    s2_avail = s2[s2.available & (s2.contrast_kind == "treatment_vs_vehicle")]
    s2_ok = bool(s2_avail.control_matching_rule.isin(
        ["same_agent_zero_dose_same_cell", "global_control_token_fallback"]).all()
        and (s2_avail.control_key.str.split("@").str[1]
             == s2_avail.condition_key.str.split("@").str[1]).all())
    gate("control_matching_and_unavailable_ledger",
         match_ok and unavail_reasons_ok and s2_ok and baseline_rule_ok,
         f"sciPlex4: all {len(s4_treat)} treatment-vs-vehicle contrasts use same-cell "
         f"same-plate DMSO/DMSO; {int((s4.contrast_kind == 'baseline_self').sum())} "
         f"baselines are self-contrasts; all {int((~s4.available).sum())} unavailable "
         f"contrasts carry a reason; sciPlex2: {len(s2_avail)} contrasts use the "
         "declared rule")

    # --- 7. rescue reference eligibility ------------------------------------
    combo_rows = rescue[rescue.contrast_kind == "combination_vs_vehicle"]
    n_combo_ledger = len(combo_rows)
    any_available = bool(rescue.available.any())
    verdict = manifest["rescue_contrasts"]["sciplex4"]["verdict"]
    verdict_ok = ((not any_available) == ("NOT CONSTRUCTIBLE" in verdict))
    gate("rescue_reference_eligibility",
         n_combo_ledger == n_combo and verdict_ok,
         f"rescue ledger covers {n_combo_ledger} combination conditions; any constructible "
         f"contrast: {any_available}; manifest verdict: '{verdict}'")

    # --- 8. gene mapping: conflicts, ambiguity, reconciliation ---------------
    gmap = gmap.fillna({c: "" for c in gmap.columns if gmap[c].dtype == object})
    gm = manifest["gene_mapping"]
    methods = gm["mapping_method_counts_mutually_exclusive"]
    recon_ok = (sum(methods.values()) == gm["input_feature_rows"]
                and gm["mapped_rows"] + gm["ambiguous_rows"] + gm["unresolved_rows"]
                == gm["input_feature_rows"]
                and gm["unique_target_ids"] <= gm["mapped_rows"])
    mum1 = gmap[(gmap.feature_name == "MUM1")
                & (gmap.ensembl_id == "ENSG00000160953")]
    # the stable ID must win: PWWP3A selected, and the alias evidence contains IRF4
    # (the target the v1 first-wins alias lookup would have silently chosen)
    mum1_ok = (len(mum1) == 1 and mum1.iloc[0].selected_symbol == "PWWP3A"
               and mum1.iloc[0].mapping_method == "stable_id"
               and "IRF4" in mum1.iloc[0].symbol_candidates)
    ac = gmap[(gmap.feature_name == "AC000061.1")
              & (gmap.ensembl_id == "ENSG00000083622")]
    ac_ok = len(ac) == 1 and ac.iloc[0].selected_symbol == "CFTR-AS2"
    amb = gmap[gmap.mapping_method == "symbol_alias_ambiguous"]
    amb_ok = bool((amb.selected_symbol == "").all()) and len(amb) > 0
    cd99 = gmap[gmap.feature_name.isin(["CD99", "CD99:1"])]
    cd99_ok = (len(cd99) == 2
               and cd99.ensembl_id.nunique() == 1
               and cd99.collision_group.nunique() == 1
               and (cd99.shared_ensembl_in_collision == "yes").all())
    matr3 = gmap[gmap.feature_name.isin(["MATR3", "MATR3:1"])]
    matr3_ok = (len(matr3) == 2
                and matr3.ensembl_id.nunique() == 2
                and (matr3.shared_ensembl_in_collision == "no").all())
    gate("gene_mapping_conflicts_and_reconciliation",
         recon_ok and mum1_ok and ac_ok and amb_ok and cd99_ok and matr3_ok,
         f"counts reconcile ({gm['mapped_rows']} mapped + {gm['ambiguous_rows']} ambiguous "
         f"unselected + {gm['unresolved_rows']} unresolved = {gm['input_feature_rows']}); "
         f"MUM1->PWWP3A via stable ID (IRF4 was the alias trap): {mum1_ok}; "
         f"AC000061.1->CFTR-AS2 via stable ID: {ac_ok}; ambiguous aliases unselected "
         f"({len(amb)} rows): {amb_ok}; CD99 shared-ID collision: {cd99_ok}; "
         f"MATR3 differing-ID collision: {matr3_ok}")

    # --- 9. sample-sheet reconciliation is a real join ----------------------
    for tag in ("sciplex2", "sciplex4"):
        sub = recon[(recon.study == tag) & (recon.level == "condition")]
        n_matched = int((sub.status == "matched").sum())
        gate(f"sample_sheet_join_{tag}",
             n_matched == manifest["sample_sheet_reconciliation"][tag]["matched"]
             and n_matched > 0
             and len(sub) == (manifest["sample_sheet_reconciliation"][tag]["expected_conditions"]
                              + manifest["sample_sheet_reconciliation"][tag]
                              ["observed_not_in_sheet"]),
             f"{n_matched} matched conditions; {int((sub.status != 'matched').sum())} "
             "discrepancy records with scoped statuses")

    # --- 10. no evidence promotion, no invented labels/replication ----------
    ev = pd.read_csv(out_dir / "typed_evidence.csv")
    gate("no_evidence_promotion_or_labels",
         not ev.evidence_class.eq("qualified_experimental_evidence").any()
         and not ev.qualified_experimental_evidence.any()
         and ev.label_kind.eq("none (no outcome labels constructed)").all()
         and ev.biological_replicate_id.eq(
             "unavailable (hash/index rows are not replicates)").all(),
         "no qualified_experimental_evidence anywhere; label_kind none; replication "
         "unavailable")

    # --- 11. required provenance VALUES -------------------------------------
    s2_treat = s2[s2.contrast_kind == "treatment_vs_vehicle"]
    treat_ctrl = prov.loc[prov.contrast_kind == "treatment_vs_vehicle",
                          "control_key"].fillna("")
    pv_ok = bool(
        s2_treat.control_matching_rule.fillna("").ne("").all()
        and s4_treat.control_matching_rule.fillna("").ne("").all()
        and treat_ctrl.ne("").all()
        and prov.dose_unit.str.contains("unverified").all()
        and prov.sampling_frame.str.contains("no attempted-experiment denominator").all())
    gate("provenance_values_not_just_columns", pv_ok,
         "every treatment-vs-vehicle contrast has a nonempty control_matching_rule and "
         "control_key; dose units and sampling frame carry required restrictive values")

    # --- 12. wells ------------------------------------------------------------
    gate("well_summaries_retained",
         len(wells) == int(wells.groupby("study").size().sum())
         and (wells.n_cells > 0).all()
         and all(z[f"wells::{tag}"].shape == (int((wells.study == tag).sum()), n_feat)
                 and np.issubdtype(z[f"wells::{tag}"].dtype, np.floating)
                 and np.isfinite(z[f"wells::{tag}"]).all()
                 for tag in ("sciplex2", "sciplex4"))
         and manifest["aggregation_estimand"]["name"]
         == "well-unweighted mean of per-well mean log1p-CP10K",
         f"{len(wells)} per-well summaries retained with positive cell counts and finite "
         "numeric arrays on the feature axis; estimand explicitly named")

    # ---------------- descriptive diagnostics (never gates) ------------------
    rng = np.random.default_rng(SEED)
    cols = np.sort(rng.choice(n_feat, size=min(6000, n_feat), replace=False))
    for tag, n_rows in (("sciplex2", n_s2), ("sciplex4", n_s4)):
        eff = z[f"effects::{tag}"]
        means = z[f"means::{tag}"]
        finite = eff[np.isfinite(eff)]
        zero_frac = float(np.mean(finite == 0.0)) if finite.size else float("nan")
        never = int((means == 0).all(axis=0).sum())  # feature axis = columns
        diag(f"zero_fraction_never_detected_{tag}",
             f"zero-entry fraction among finite effect entries: {zero_frac:.4f}; "
             f"never-detected features (all-condition means exactly zero): {never}")
        pos = float(np.mean(finite > 0)) if finite.size else float("nan")
        diag(f"effect_direction_balance_{tag}",
             f"positive fraction of finite effect entries: {pos:.4f} (both directions "
             "retained)")
    # correct absolute-count dose table for sciPlex2
    s2_idx = idx[idx.block == "sciplex2"]
    prov_s2 = prov[prov.study == "sciplex2"].set_index("condition_key")
    dose_table = {}
    for ck in s2_idx.condition_key:
        agent = ck.split("::")[0]
        dose = ck.split("::")[1].split("@")[0]
        try:
            d = float(dose)
        except ValueError:
            continue
        if d == 0.0:
            continue
        row = int(s2_idx[s2_idx.condition_key == ck].row.iloc[0])
        if avail_check(s2_idx, ck):
            eff = z["effects::sciplex2"][row]
            dose_table.setdefault(agent, {})[dose] = (
                abs_above(eff, DESCRIPTIVE_THRESHOLD),
                int(np.sum(eff > DESCRIPTIVE_THRESHOLD)),
                int(np.sum(eff < -DESCRIPTIVE_THRESHOLD)))
    diag("dose_response_abs_counts_sciplex2",
         f"feature rows with |effect|>{DESCRIPTIVE_THRESHOLD} (abs, pos, neg), valid "
         f"contrasts only: {json.dumps(dose_table)}. Descriptive token-threshold counts, "
         "NOT differential-expression discoveries and NOT a monotonicity or biology "
         "certificate.")

    # ---------------- figures -------------------------------------------------
    if make_figures:
        make_figures_fn(qa_dir, manifest, z, prov, cls, idx, gmap, quar, rescue, s2_idx)

    n_fail = sum(not g["passed"] for g in gates)
    return (1 if n_fail else 0), gates


def avail_check(idx_df: pd.DataFrame, ck: str) -> bool:
    row = idx_df[idx_df.condition_key == ck]
    return len(row) == 1 and bool(row.available.iloc[0])


def abs_above(effect: np.ndarray, threshold: float) -> int:
    return int(np.sum(np.abs(effect) > threshold))


def make_figures_fn(qa_dir, manifest, z, prov, cls, idx, gmap, quar, rescue, s2_idx):
    plt.rcParams.update({"figure.dpi": 150})

    # F1: condition coverage by cell x plate (sciPlex4)
    s4 = prov[prov.study == "sciplex4"]
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    cov = (s4.groupby(["cell_line", "plate"]).size().unstack(fill_value=0))
    cov.plot(kind="bar", stacked=True, ax=ax, colormap="tab20")
    ax.set_title("sciPlex4 condition coverage by cell line and plate")
    ax.set_ylabel("conditions")
    ax.legend(fontsize=6, ncol=2)
    fig.tight_layout()
    fig.savefig(qa_dir / "fig1_condition_coverage_cell_plate.png")
    plt.close(fig)

    # F2: matched vs unavailable controls per cell x plate
    fig, ax = plt.subplots(figsize=(7, 3.4))
    tab = (s4.assign(status=np.where(s4.available, "available", "unavailable"))
           .groupby(["cell_line", "plate", "status"]).size().unstack(fill_value=0))
    tab.plot(kind="bar", stacked=True, ax=ax, color=["#4878a8", "#c44e52"])
    ax.set_title("sciPlex4 contrasts: available vs unavailable (same-plate control rule)")
    ax.set_ylabel("conditions")
    fig.tight_layout()
    fig.savefig(qa_dir / "fig2_matched_vs_unavailable.png")
    plt.close(fig)

    # F3: exclusion/quarantine counts
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    counts = quar.groupby(["study", "reason"]).size()
    counts.plot(kind="barh", ax=ax, color="#c44e52")
    ax.set_title("quarantined cells", fontsize=10)
    fig.tight_layout()
    fig.savefig(qa_dir / "fig3_quarantine.png")
    plt.close(fig)

    # F4: mapping outcomes + ambiguity/collision
    gm = manifest["gene_mapping"]
    methods = gm["mapping_method_counts_mutually_exclusive"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    axes[0].barh(list(methods.keys()), list(methods.values()), color="#4878a8")
    axes[0].set_title("mapping methods (mutually exclusive)")
    axes[1].bar(["conflicts", "ambiguous\nrows", "collision\ngroups",
                 "collisions\n(shared ID)", "collisions\n(differing ID)"],
                [gm["stable_id_vs_symbol_conflicts"], gm["ambiguous_rows"],
                 gm["collision_groups"], gm["collision_groups_with_shared_ensembl"],
                 gm["collision_groups_with_different_ensembl"]],
                color=["#c44e52", "#dd8452", "#55a868", "#8172b3", "#937860"])
    axes[1].set_title("ambiguity / conflict / collision counts")
    for a in axes:
        a.tick_params(axis="x", labelsize=7)
    fig.tight_layout()
    fig.savefig(qa_dir / "fig4_gene_mapping.png")
    plt.close(fig)

    # F5: positive and negative response distributions (valid contrasts only)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
    for ax, tag in zip(axes, ("sciplex2", "sciplex4")):
        eff = z[f"effects::{tag}"]
        vals = eff[np.isfinite(eff)]
        vals = vals[vals != 0.0]
        ax.hist(vals[np.clip(vals, -3, 3) > 0], bins=100, alpha=0.7,
                color="#c44e52", label="positive")
        ax.hist(np.clip(vals[vals < 0], -3, 0), bins=100, alpha=0.7,
                color="#55a868", label="negative")
        ax.set_yscale("symlog")
        ax.set_title(f"{tag} effect entries (valid contrasts, both directions)")
        ax.set_xlabel("log1p-CP10K delta vs same-plate vehicle")
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(qa_dir / "fig5_effect_distributions.png")
    plt.close(fig)

    # F6: descriptive dose-response with both directions, sciPlex2
    fig, ax = plt.subplots(figsize=(9, 3.8))
    agents = sorted({ck.split("::")[0] for ck in s2_idx.condition_key
                     if ck.split("::")[0] != "control"})
    agent_colors = dict(zip(agents, ("#c44e52", "#4878a8", "#55a868", "#8172b3")))
    per_agent = {}
    for ck in s2_idx.condition_key:
        agent = ck.split("::")[0]
        if agent not in agent_colors or not avail_check(s2_idx, ck):
            continue
        d = ck.split("::")[1].split("@")[0]
        try:
            dv = float(d)
        except ValueError:
            continue
        if dv == 0.0:
            continue
        row = int(s2_idx[s2_idx.condition_key == ck].row.iloc[0])
        eff = z["effects::sciplex2"][row]
        per_agent.setdefault(agent, []).append(
            (dv, int(np.sum(eff > DESCRIPTIVE_THRESHOLD)),
             int(np.sum(eff < -DESCRIPTIVE_THRESHOLD))))
    doses_all = sorted({dv for v in per_agent.values() for dv, _, _ in v})
    xpos = {d: i for i, d in enumerate(doses_all)}
    n_ag = len(agents)
    bw = 0.8 / n_ag / 2
    for ai, agent in enumerate(agents):
        rows = sorted(per_agent[agent])
        xs = [xpos[dv] + (ai - (n_ag - 1) / 2) * bw - bw / 2 for dv, _, _ in rows]
        ax.bar([x - bw / 2 for x in xs], [p for _, p, _ in rows], bw,
               color=agent_colors[agent], label=f"{agent} up")
        ax.bar([x + bw / 2 for x in xs], [n_ for _, _, n_ in rows], bw,
               color=agent_colors[agent], alpha=0.45, label=f"{agent} down")
    ax.set_xticks(range(len(doses_all)))
    ax.set_xticklabels([str(d) for d in doses_all])
    ax.set_xlabel("dose token (units unverified)")
    ax.set_ylabel(f"feature rows |effect|>{DESCRIPTIVE_THRESHOLD}")
    ax.set_title("sciPlex2 descriptive dose-response (valid contrasts, up solid / down faded)")
    ax.legend(fontsize=6, ncol=4)
    fig.tight_layout()
    fig.savefig(qa_dir / "fig6_dose_response_descriptive.png")
    plt.close(fig)


def main() -> int:
    QA.mkdir(parents=True, exist_ok=True)
    code, gate_results = run_checks()
    report = {
        "protocol": "research/dataset_discovery/CONSTRUCTION_PROTOCOL_V2.md",
        "qa_run_at": pd.Timestamp.now().isoformat(),
        "seed": SEED,
        "descriptive_threshold": DESCRIPTIVE_THRESHOLD,
        "gates": gate_results,
        "diagnostics": list(diagnostics),
        "summary": f"{sum(g['passed'] for g in gate_results)}/{len(gate_results)} gates passed",
    }
    (QA / "qa_report.json").write_text(json.dumps(report, indent=1))
    lines = ["# QA Report — sciplex_pilot_v2 (acceptance gate)", "",
             f"- QA run: {report['qa_run_at']} (seed {SEED})", "",
             f"- **{report['summary']}** (gates must all pass; diagnostics are descriptive)",
             "", "## Gates", ""]
    for g in gate_results:
        lines.append(f"## {'PASS' if g['passed'] else 'FAIL'} — {g['name']}")
        lines.append(g["detail"] + "\n")
    lines += ["## Descriptive diagnostics (NOT validity criteria)", ""]
    for d in diagnostics:
        lines.append(f"- **{d['name']}**: {d['detail']}")
    (QA / "QA_REPORT.md").write_text("\n".join(lines))
    print(report["summary"])
    return code


if __name__ == "__main__":
    sys.exit(main())
