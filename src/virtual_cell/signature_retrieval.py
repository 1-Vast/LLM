"""Find the reference compounds whose measured response a query signature resembles.

File summary
- Path: src/virtual_cell/signature_retrieval.py
- Purpose: compare a measured transcriptional signature with a digest-bound library of measured
  SciPlex3 responses, and report which annotated classes it resembles, against a permutation
  null and beside the procedure's recorded held-out agreement.
- Core points:
  - Query and library are measurements; the output is a derived analysis of them, never a
    prediction, a mechanism verdict or a measured premise.
  - The query is centered on the library's mean response at the same line and dose, so the
    stress response most compounds share cannot decide the ranking.
  - A class is a vendor annotation. Resembling a class is not having its mechanism: similar
    responses arise from different targets, and one compound can act through several.
  - Unsupported input is refused by name in `rejected`; malformed input raises ValueError.
- Interfaces: `SignatureLibrary`, `load_library`, `retrieve`, `signature_retrieval`
- Depends on: numpy, maestro.tool_contracts
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from maestro.tool_contracts import TOOL_SCHEMA_VERSION, json_loads, json_value, object_fields

LIBRARY_SCHEMA = "maestro.virtual_cell.signature_library.v1"
DEFAULT_LIBRARY = Path("data/virtual_cell/sciplex3_signature_library")
MINIMUM_MATCHED_GENES = 200
NULL_DRAWS = 200


@dataclass(frozen=True)
class SignatureLibrary:
    """Measured, uncentered shifts per reference compound, line and dose, plus their metadata."""

    genes: tuple[str, ...]
    lines: tuple[str, ...]
    doses: tuple[float, ...]
    compounds: tuple[Mapping[str, str], ...]
    profiles: np.ndarray          # (entries, genes) log-expression shift against matched vehicle
    entry_compound: np.ndarray    # (entries,) index into compounds
    entry_line: np.ndarray        # (entries,) index into lines
    entry_dose: np.ndarray        # (entries,) index into doses
    systematic: np.ndarray        # (lines, doses, genes) mean shift over reference compounds
    metadata: Mapping[str, Any]

    def profile(self, compound: int, line: int, dose: int) -> np.ndarray | None:
        rows = np.flatnonzero((self.entry_compound == compound) & (self.entry_line == line) & (self.entry_dose == dose))
        return self.profiles[rows[0]] if len(rows) else None


def load_library(directory: Path) -> SignatureLibrary:
    """Load a library and refuse it when its arrays do not match their recorded digest."""

    directory = Path(directory)
    meta = json.loads((directory / "library.json").read_text(encoding="utf-8"))
    if meta.get("schema") != LIBRARY_SCHEMA:
        raise ValueError(f"signature_library_schema_unknown:{meta.get('schema')}")
    arrays = (directory / "library.npz").read_bytes()
    if hashlib.sha256(arrays).hexdigest() != meta.get("arrays_sha256"):
        raise ValueError("signature_library_digest_mismatch")
    data = np.load(directory / "library.npz", allow_pickle=False)
    return SignatureLibrary(
        genes=tuple(meta["genes"]), lines=tuple(meta["lines"]), doses=tuple(float(d) for d in meta["doses"]),
        compounds=tuple(meta["compounds"]), profiles=data["profiles"], entry_compound=data["entry_compound"],
        entry_line=data["entry_line"], entry_dose=data["entry_dose"], systematic=data["systematic"],
        metadata=meta)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(a @ b / denominator) if denominator > 0 else 0.0


def retrieve(library: SignatureLibrary, query: Mapping[str, Any], *, top_k: int = 5, seed: int = 20260926) -> dict[str, Any]:
    """Rank reference classes by the best cosine similarity of their compounds to the query."""

    signatures = query["signatures"]
    excluded = {str(x).casefold() for x in query.get("exclude_reference_compounds", [])}
    rejected: list[dict[str, str]] = []
    gene_index = {g: i for i, g in enumerate(library.genes)}
    parts, used_lines, dose_notes = [], [], []
    shared = None
    for signature in signatures:
        line = signature["context"]
        if line not in library.lines:
            rejected.append({"context": line, "reason": f"context_not_in_library:{line}"})
            continue
        dose = float(signature["dose_nM"])
        if not math.isfinite(dose) or dose <= 0:
            rejected.append({"context": line, "reason": "dose_not_positive"})
            continue
        nearest = int(np.argmin([abs(math.log10(dose) - math.log10(d)) for d in library.doses]))
        if abs(math.log10(dose) - math.log10(library.doses[nearest])) > 1e-9:
            dose_notes.append(f"{line}: query dose {dose:g} nM compared at the nearest library dose "
                              f"{library.doses[nearest]:g} nM")
        values = signature["genes"]
        matched = {gene_index[g]: float(v) for g, v in values.items() if g in gene_index}
        if any(not math.isfinite(v) for v in matched.values()):
            raise ValueError("signature values must be finite")
        shared = set(matched) if shared is None else shared & set(matched)
        parts.append((library.lines.index(line), nearest, matched, bool(signature.get("centered", False))))
        used_lines.append(line)
    if not parts:
        return {"ranking": [], "nearest": [], "rejected": rejected or [{"reason": "no_usable_signature"}]}
    columns = np.array(sorted(shared or ()))
    if len(columns) < MINIMUM_MATCHED_GENES:
        rejected.append({"reason": f"too_few_library_genes_matched:{len(columns)}<{MINIMUM_MATCHED_GENES}"})
        return {"ranking": [], "nearest": [], "rejected": rejected, "genes_matched": int(len(columns))}
    query_vector = []
    for line, dose, matched, centered in parts:
        v = np.array([matched[c] for c in columns])
        query_vector.append(v if centered else v - library.systematic[line, dose, columns])
    q = np.concatenate(query_vector)
    references = []
    for index, compound in enumerate(library.compounds):
        if compound["name"].casefold() in excluded or compound.get("skeleton", "").casefold() in excluded:
            continue
        vectors = []
        for line, dose, _, _ in parts:
            profile = library.profile(index, line, dose)
            if profile is None:
                break
            vectors.append(profile[columns] - library.systematic[line, dose, columns])
        if len(vectors) == len(parts):
            references.append((compound, np.concatenate(vectors)))
    if not references:
        rejected.append({"reason": "no_reference_compound_covers_the_query_lines"})
        return {"ranking": [], "nearest": [], "rejected": rejected}
    matrix = np.stack([v for _, v in references])
    norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(q)
    similarity = np.where(norms > 0, matrix @ q / np.maximum(norms, 1e-12), 0.0)
    order = np.argsort(-similarity)
    best: dict[str, tuple[float, str]] = {}
    for i in order:
        label = references[i][0]["class"]
        if label not in best:
            best[label] = (float(similarity[i]), references[i][0]["name"])
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(NULL_DRAWS):
        shuffled = q[rng.permutation(len(q))]
        null.append(float(np.max(matrix @ shuffled / np.maximum(np.linalg.norm(matrix, axis=1) * np.linalg.norm(shuffled), 1e-12))))
    threshold = float(np.quantile(null, 0.95))
    top = float(similarity[order[0]])
    return {
        "lines_compared": used_lines, "genes_matched": int(len(columns)), "reference_compounds": len(references),
        "ranking": [{"class": label, "best_cosine": round(value, 4), "best_reference": name}
                    for label, (value, name) in sorted(best.items(), key=lambda kv: -kv[1][0])[:top_k]],
        "nearest": [{"compound": references[i][0]["name"], "class": references[i][0]["class"],
                     "cosine": round(float(similarity[i]), 4)} for i in order[:top_k]],
        "permutation_null": {"draws": NULL_DRAWS, "max_cosine_q95": round(threshold, 4),
                             "best_above_null": top > threshold},
        "dose_notes": dose_notes, "rejected": rejected,
    }


def signature_retrieval(parameters: Mapping[str, Any], *, library_directory: Path | None = None,
                        workspace: Path | None = None) -> dict[str, Any]:
    """Tool entry: read a declared signature file and rank the reference classes it resembles."""

    object_fields(dict(parameters), {"dataset_path"}, set(), "parameters")
    path = Path(parameters["dataset_path"])
    data = json_loads(path.read_text(encoding="utf-8"))
    object_fields(data, {"schema_version", "signatures"}, {"exclude_reference_compounds", "top_k"}, "dataset")
    if data["schema_version"] != "1.0":
        raise ValueError("dataset schema_version must be 1.0")
    if not isinstance(data["signatures"], list) or not 1 <= len(data["signatures"]) <= 3:
        raise ValueError("signatures must list one to three per-line signatures")
    for signature in data["signatures"]:
        object_fields(signature, {"context", "dose_nM", "genes"}, {"centered"}, "signature")
        if not isinstance(signature["genes"], dict) or not signature["genes"]:
            raise ValueError("signature genes must be a nonempty object of symbol to shift")
    top_k = data.get("top_k", 5)
    if type(top_k) is not int or not 1 <= top_k <= 20:
        raise ValueError("top_k must be an integer from 1 to 20")
    root = Path(workspace) if workspace else Path(__file__).resolve().parents[2]
    directory = Path(library_directory) if library_directory else root / DEFAULT_LIBRARY
    if not (directory / "library.json").is_file():
        payload = {"ranking": [], "nearest": [], "rejected": [{"reason": "signature_library_missing"}]}
        library_meta: Mapping[str, Any] = {}
    else:
        library = load_library(directory)
        payload = retrieve(library, data, top_k=top_k)
        library_meta = library.metadata
    payload["library"] = {key: library_meta.get(key) for key in ("source", "validation", "created", "arrays_sha256")}
    payload["evidence_kind"] = "derived_analysis"
    payload["contradiction_flag"] = False
    observations = ([f"Most similar reference class: {payload['ranking'][0]['class']} "
                     f"(cosine {payload['ranking'][0]['best_cosine']})"] if payload.get("ranking") else
                    ["No ranking: " + "; ".join(r["reason"] for r in payload["rejected"])])
    limitations = [
        "Similarity of measured 24 h transcriptional responses in three cancer lines; not a mechanism, target "
        "engagement or viability claim.",
        "Classes are vendor annotations: similar responses arise from different targets, and a compound can act "
        "through several.",
        "A derived analysis of measurements; it cannot satisfy a measured premise or eliminate a hypothesis.",
    ]
    return json_value({"schema_version": TOOL_SCHEMA_VERSION, "payload": payload, "observations": observations,
                       "limitations": limitations, "artifacts": []})
