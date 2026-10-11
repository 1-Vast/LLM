"""Build an exact-dose PRISM context benchmark without target-outcome filtering.

Run from the repository root:
    python research/context_probe_20261011/data/prepare.py

Only metadata, basal input availability and reference response missingness determine
eligibility. Target outcomes remain in the evaluator-owned output; consumers must
explicitly mask them before fitting or selecting probes.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SPLIT_SALT = "maestro-context-probe-20261011-v1"
REFERENCE_COMPLETENESS = 0.95
SOURCE_PATHS = {
    "treatments": "data/external/prism_19q4/raw/primary-screen-replicate-collapsed-treatment-info.csv",
    "responses": "data/external/prism_19q4/raw/primary-screen-replicate-collapsed-logfold-change.csv",
    "prism_contexts": "data/external/prism_19q4/raw/primary-screen-cell-line-info.csv",
    "prism_readme": "data/external/prism_19q4/raw/primary-screen-readme.txt",
    "basal": "data/external/depmap_19q4/CCLE_expression.csv",
    "contexts": "data/external/depmap_19q4/sample_info.csv",
    "old_split_for_dose_audit_only": "research/astra/mechanism_routing_20261011/SPLIT.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def context_role(identity_key: str) -> str:
    digest = hashlib.sha256(f"{SPLIT_SALT}|{identity_key}".encode()).hexdigest()
    fraction = int(digest, 16) / 2**256
    return "reference" if fraction < 0.6 else "development" if fraction < 0.8 else "evaluation"


def identity_groups(treatments: pd.DataFrame) -> list[dict]:
    """Conservatively keep aliases together without chemical-identity claims."""
    rows = treatments.sort_values("column_name").reset_index(drop=True)
    parent = list(range(len(rows)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    seen: dict[tuple[str, str], int] = {}
    for i, row in rows.iterrows():
        match = re.match(r"^(BRD-[A-Z]\d{8})(?:-|$)", row.broad_id)
        if not match:
            raise ValueError(f"Unrecognized Broad identity: {row.broad_id}")
        keys = [("broad", match.group(1))]
        if row["name"]:
            keys.append(("name", normalize_name(row["name"])))
        for key in keys:
            if key in seen:
                parent[find(i)] = find(seen[key])
            else:
                seen[key] = i
    members: dict[int, list[int]] = {}
    for i in range(len(rows)):
        members.setdefault(find(i), []).append(i)

    groups = []
    for indices in members.values():
        group = rows.iloc[indices]
        names = sorted(set(group["name"]))
        prefixes = sorted(set(group.broad_id.str[:13]))
        structures = sorted({item.strip() for text in group.smiles for item in text.split(",") if item.strip() and item != "NA"})
        representative = group.iloc[0]
        groups.append({
            "drug_id": prefixes[0],
            "drug_name": representative["name"],
            "representative_column": representative.column_name,
            "representative_broad_id": representative.broad_id,
            "names": names,
            "broad_prefixes": prefixes,
            "source_columns": group.column_name.tolist(),
            "n_columns": len(group),
            "multiple_broad_prefixes": len(prefixes) > 1,
            "n_distinct_metadata_smiles": len(structures),
            "multiple_metadata_structures": len(structures) > 1,
            "structure_verification": "Metadata strings only; no canonicalization or molecular identity guarantee",
            "metadata_smiles": structures,
        })
    return sorted(groups, key=lambda group: group["drug_id"])


def missing_summary(matrix: np.ndarray) -> dict:
    finite = np.isfinite(matrix)
    return {
        "shape": list(matrix.shape),
        "observed": int(finite.sum()),
        "missing": int((~finite).sum()),
        "observed_fraction": float(finite.mean()) if finite.size else None,
        "complete_contexts": int(finite.all(axis=1).sum()),
        "complete_drugs": int(finite.all(axis=0).sum()),
        "observed_fraction_per_context_quantiles": np.quantile(finite.mean(axis=1), [0, 0.25, 0.5, 0.75, 1]).tolist() if len(matrix) else [],
    }


def main() -> None:
    treatments = pd.read_csv(ROOT / SOURCE_PATHS["treatments"], keep_default_na=False)
    numeric_dose = pd.to_numeric(treatments.dose, errors="raise")
    exact = treatments.loc[(treatments.screen_id == "HTS") & (numeric_dose == 2.5)].copy()
    if exact.column_name.duplicated().any():
        raise ValueError("Duplicate treatment metadata column names")
    groups = identity_groups(exact)

    response_path = ROOT / SOURCE_PATHS["responses"]
    response_columns = pd.read_csv(response_path, nrows=0).columns.tolist()
    absent = sorted(set(exact.column_name) - set(response_columns))
    if absent:
        raise ValueError(f"Exact-dose treatment columns absent from response file: {absent}")
    response_ids = pd.read_csv(response_path, usecols=[0]).iloc[:, 0].astype(str)
    if response_ids.duplicated().any():
        raise ValueError("Duplicate response context rows")

    prism_contexts = pd.read_csv(ROOT / SOURCE_PATHS["prism_contexts"])
    context_info = pd.read_csv(ROOT / SOURCE_PATHS["contexts"], keep_default_na=False).set_index("DepMap_ID")
    basal_frame = pd.read_csv(ROOT / SOURCE_PATHS["basal"], index_col=0)
    if context_info.index.duplicated().any() or basal_frame.index.duplicated().any():
        raise ValueError("Duplicate basal/context metadata identities")
    passing = prism_contexts.loc[prism_contexts.passed_str_profiling.eq(True) & prism_contexts.depmap_id.notna()]
    if passing.depmap_id.duplicated().any():
        raise ValueError("Ambiguous passing PRISM context identities")
    row_to_context = dict(zip(passing.row_name, passing.depmap_id))
    contexts = []
    excluded = []
    for row_id in response_ids:
        context_id = row_to_context.get(row_id)
        reason = None
        if context_id is None:
            reason = "No passing STR / noncontrol identity"
        elif context_id not in context_info.index:
            reason = "No sample_info metadata"
        elif context_id not in basal_frame.index:
            reason = "No basal expression input"
        elif not np.isfinite(basal_frame.loc[context_id].to_numpy(dtype=float)).any():
            reason = "Basal expression input entirely missing"
        if reason:
            excluded.append({"response_row_id": row_id, "context_id": context_id, "reason": reason})
            continue
        info = context_info.loc[context_id]
        identity_key = f"RRID:{info.RRID}" if info.RRID else f"DepMap:{context_id}"
        contexts.append({
            "context_id": context_id,
            "response_row_id": row_id,
            "lineage": info.lineage or "unknown",
            "ccle_name": info.CCLE_Name,
            "identity_key": identity_key,
            "role": context_role(identity_key),
        })
    contexts = pd.DataFrame(contexts).sort_values("context_id").reset_index(drop=True)
    alias_contexts = contexts.loc[contexts.identity_key.duplicated(keep="first")]
    for row in alias_contexts.to_dict(orient="records"):
        excluded.append({"response_row_id": row["response_row_id"], "context_id": row["context_id"], "reason": "Shared RRID; retain lexicographically first eligible DepMap identity", "identity_key": row["identity_key"]})
    contexts = contexts.loc[~contexts.identity_key.duplicated(keep="first")].reset_index(drop=True)
    # No response values have been read before context identities and roles freeze.
    representatives = [group["representative_column"] for group in groups]
    response_frame = pd.read_csv(response_path, usecols=[response_columns[0], *representatives], index_col=0)
    y_all = response_frame.loc[contexts.response_row_id, representatives].to_numpy(dtype=np.float64)
    if np.isinf(y_all).any():
        raise ValueError("Infinite response values are not supported")
    roles = contexts.role.to_numpy(dtype=str)
    reference_observed_fraction = np.isfinite(y_all[roles == "reference"]).mean(axis=0)
    eligible = reference_observed_fraction >= REFERENCE_COMPLETENESS
    for i, group in enumerate(groups):
        group["reference_observed_fraction"] = float(reference_observed_fraction[i])
        group["eligible"] = bool(eligible[i])
    drugs = [group for group in groups if group["eligible"]]
    y = y_all[:, eligible]
    basal = basal_frame.loc[contexts.context_id].to_numpy(dtype=np.float32)

    old_split = json.loads((ROOT / SOURCE_PATHS["old_split_for_dose_audit_only"]).read_text(encoding="utf-8"))
    dose_by_column = dict(zip(treatments.column_name, numeric_dose))
    mixed = []
    for name, unit in sorted(old_split["units"].items()):
        columns = unit["prism_columns"]
        doses = sorted({float(dose_by_column[column]) for column in columns})
        if len(doses) > 1:
            mixed.append({"old_name": name, "doses_um": doses, "columns": columns})

    manifest = {
        "schema": "maestro.context_probe.exactdose_data.v1",
        "status": "EXPOSED_RETROSPECTIVE_ALGORITHM_DIAGNOSTIC",
        "endpoint": {
            "name": "PRISM primary HTS replicate-collapsed log2-fold-change relative to negative controls",
            "dose_um": 2.5,
            "dose_filter": "Strict numeric equality; no tolerance",
            "screen_id": "HTS",
            "platform": "Pooled barcoded cell lines; Luminex fluorescence readout",
            "direction": "Lower log2-fold-change indicates lower relative viability; no absolute death/apoptosis claim",
            "time_hours": None,
            "time_limitation": "No per-treatment exposure-time field in local collapsed metadata; nominal publication protocol needs separate verification",
            "publisher_preprocessing": "Control normalization, QC, ComBat, median collapse; see hashed primary readme",
            "preprocessing_limitation": "Publisher normalization/ComBat may use joint plate or pool information. Raw culture-level preprocessing was not reconstructed or held out.",
            "replicate_plate_culture_ids_available": False,
        },
        "context_roles": {
            "salt": SPLIT_SALT,
            "algorithm": "sha256(salt + '|' + identity_key) / 2**256; <0.6 reference, <0.8 development, otherwise evaluation",
            "identity_key": "Nonempty sample_info RRID; otherwise DepMap ID. Shared RRID keeps only the lexicographically first eligible DepMap ID.",
            "training": "Reference outcomes only; development for selection; evaluation never fitted",
            "claim": "Known drugs, unseen response context; lineages overlap and are not held out",
            "calibration": "No independent calibration role is reserved in this initial information diagnostic; no coverage guarantee is claimed",
            "counts": contexts.role.value_counts().sort_index().to_dict(),
            "lineage_by_role": pd.crosstab(contexts.lineage, contexts.role).to_dict(orient="index"),
            "excluded_alias_contexts": alias_contexts.to_dict(orient="records"),
        },
        "eligibility": {
            "context": "Response row with passing STR mapped identity, sample metadata and at least one finite basal value; no response completeness or response magnitude filter",
            "drug": "Metadata alias group representative with >=95% finite reference outcomes only",
            "reference_min_observed_fraction": REFERENCE_COMPLETENESS,
            "target_missingness": "Preserved; may cause failed probe or unscorable committed selection. It must not alter fitted features, probes, decisions, drug pool or context inclusion.",
            "drug_identity": "Connected components sharing NFKC/casefold/whitespace-normalized name OR Broad compound prefix; metadata-only conservative alias blocking",
            "duplicate_rule": "Lexicographically first exact-dose HTS treatment column per component; no outcome-based choice, averaging, missing-value substitution or cross-dose aggregation",
            "chemical_identity_limitation": "Equal names/prefixes are not independently verified chemical identity. Conflicting metadata structures are flags, not filtered with target outcomes.",
        },
        "counts": {
            "raw_response_contexts": len(response_ids),
            "eligible_contexts": len(contexts),
            "excluded_contexts": len(excluded),
            "exactdose_treatment_columns": len(exact),
            "metadata_identity_groups": len(groups),
            "eligible_drugs": len(drugs),
            "basal_genes": basal.shape[1],
            "basal_nonfinite_values": int((~np.isfinite(basal)).sum()),
            "identity_groups_multiple_columns": sum(group["n_columns"] > 1 for group in groups),
            "identity_groups_multiple_broad_prefixes": sum(group["multiple_broad_prefixes"] for group in groups),
            "identity_groups_multiple_metadata_structures": sum(group["multiple_metadata_structures"] for group in groups),
            "old_mixed_dose_groups": len(mixed),
        },
        "missingness_eligible_drugs_by_role": {role: missing_summary(y[roles == role]) for role in sorted(set(roles))},
        "missingness_all_metadata_drugs_by_role": {role: missing_summary(y_all[roles == role]) for role in sorted(set(roles))},
        "basal": "All source columns and source values retained as float32; no fitted scaling, feature selection or imputation. These must use reference inputs only downstream.",
        "array_schema": {
            "context_id": "[N] DepMap ID strings",
            "lineage": "[N] sample_info lineage strings",
            "identity_key": "[N] role grouping identity strings",
            "role": "[N] reference/development/evaluation strings",
            "basal": "[N,G] float32 source expression values; no learned transform",
            "gene_id": "[G] source expression column names",
            "drug_id": "[D] minimum Broad compound prefix in the alias component",
            "drug_name": "[D] representative treatment metadata name",
            "y": "[N,D] float64 source log2-fold-change; NaN retained",
            "available": "[N,D] boolean finite response mask; evaluator bookkeeping only",
            "metadata": "scalar JSON string with schema and manifest filename",
        },
        "sources": [{"name": name, "path": relative, "bytes": (ROOT / relative).stat().st_size, "sha256": sha256(ROOT / relative)} for name, relative in SOURCE_PATHS.items()],
        "prepare_sha256": sha256(Path(__file__)),
    }
    np.savez_compressed(
        OUT / "output.npz",
        context_id=contexts.context_id.to_numpy(dtype=str),
        lineage=contexts.lineage.to_numpy(dtype=str),
        identity_key=contexts.identity_key.to_numpy(dtype=str),
        role=roles,
        basal=basal,
        gene_id=basal_frame.columns.to_numpy(dtype=str),
        drug_id=np.asarray([drug["drug_id"] for drug in drugs]),
        drug_name=np.asarray([drug["drug_name"] for drug in drugs]),
        y=y,
        available=np.isfinite(y),
        metadata=np.asarray(json.dumps({"schema": manifest["schema"], "manifest": "MANIFEST.json"})),
    )
    contexts.to_csv(OUT / "contexts.csv", index=False)
    missing_rows = contexts.copy()
    missing_rows["n_observed_eligible_drugs"] = np.isfinite(y).sum(axis=1)
    missing_rows["n_missing_eligible_drugs"] = (~np.isfinite(y)).sum(axis=1)
    missing_rows.to_csv(OUT / "context_missingness.csv", index=False)
    for filename, payload in [("drug_groups.json", groups), ("excluded_contexts.json", excluded), ("old_mixed_dose_groups.json", mixed)]:
        (OUT / filename).write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    manifest["output_npz_sha256"] = sha256(OUT / "output.npz")
    manifest["derived_file_sha256"] = {filename: sha256(OUT / filename) for filename in ["contexts.csv", "context_missingness.csv", "drug_groups.json", "excluded_contexts.json", "old_mixed_dose_groups.json"]}
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"counts": manifest["counts"], "roles": manifest["context_roles"]["counts"], "missingness": manifest["missingness_eligible_drugs_by_role"]}, indent=2))


if __name__ == "__main__":
    main()
