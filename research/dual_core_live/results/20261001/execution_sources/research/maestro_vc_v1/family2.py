"""Second case family: genetic-pharmacological discrepancy and engagement cases, with typed premises.

File summary
- Path: research/maestro_vc_v1/family2.py
- Purpose: bring the 58 typed-premise mechanism-contrast cases (`real_v3`) and the 6 engagement cases
  into the case memory as structured cases, build each one's hypothesis graph, and evaluate retrieval on
  them leave-one-target-gene-out, comparing semantic similarity with pattern-aware, adaptation-aware
  retrieval.
- Core points:
  - Each case becomes a `Case` whose kind follows its declared evidence pattern: concordant program
    support is canonical; unattributed pharmacology, pan-essential attribution and mode
    non-equivalence are contrastive (genetic and pharmacological evidence disagree); no discriminating
    evidence and implementation gap are failures (no menu action can change the decision, or a needed
    measurement is unavailable). The mapping is fixed here and named in `PATTERN_KIND`.
  - Hypotheses are the case's two registered claims plus three advisory ones (compensatory response,
    artifact, molecular response real but functionally irrelevant); the graph runs from intervention
    through target engagement to the observed assay. Layers with no measurement stay `not_planned`, and
    the graph validator refuses a measured claim into them.
  - A processed record that is not condition-matched is `ambiguous`, not `qualified`: a CRISPR score
    beside a screening curve does not measure engagement.
  - Retrieval evaluation is descriptive: 58 cases over 40 genes cannot support an inferential claim.
    The target's own gene is excluded from its precedents (the package's split rule). Three retrievers:
    `semantic` (shared compound, gene family word or lineage, as a text index would find), `pattern`
    (numeric evidence-vector similarity), and `adaptation` (pattern similarity with the case-score terms:
    Reactome pathway compatibility, evidence quality, an adaptation cost for each difference in
    lineage, compound and available premises, a domain-shift term, and abstention when no precedent
    is effectively supported).
  - The licensed decision is a declared evidence-sufficiency rule, not biological truth; agreement with
    it is reported as agreement with that convention.
- Interfaces: `PATTERN_KIND`, `load_rows`, `to_case`, `build_store`, `feature_vector`, `evaluate_retrieval`
- Depends on: research/scientific_case_memory (schema, store, graph, cards), numpy, pandas
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from research.scientific_case_memory import case_schema as S
from research.scientific_case_memory import case_store as CS
from research.scientific_case_memory import evidence_cards as EC
from research.scientific_case_memory import hypothesis_graph as HG

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "data/evaluation/cases/real_v3"
ENGAGEMENT = ROOT / "data/evaluation/cases/engagement_v1"
MANIFEST = ROOT / "data/evaluation/derived/real_case_manifest_v3.json"
PATTERN_KIND = {"concordant_program_support": S.CaseKind.CANONICAL,
                "unattributed_pharmacology": S.CaseKind.CONTRASTIVE, "pan_essential_attribution": S.CaseKind.CONTRASTIVE,
                "mode_non_equivalence": S.CaseKind.CONTRASTIVE,
                "no_discriminating_evidence": S.CaseKind.FAILURE, "implementation_gap": S.CaseKind.FAILURE}
FEATURES = ("gene_effect", "index_auc", "index_curve_r2", "abundance_log2_tpm1", "dependent_model_fraction")
ADVISORY = (("H_compensatory", "The observed response is a compensatory stress response downstream of a different primary effect."),
            ("H_artifact", "The observed phenotype is a screening or batch artifact of the retrospective records."),
            ("H_irrelevant", "The molecular record is real but functionally irrelevant to the phenotype."))


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_rows() -> list[dict]:
    """Manifest rows joined with each case's public and private JSON."""
    rows = []
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for m in manifest["cases"]:
        pub = json.loads((PACKAGE / "public" / f"{m['case_id']}.json").read_text(encoding="utf-8"))
        priv = json.loads((PACKAGE / "private" / f"{m['case_id']}.results.json").read_text(encoding="utf-8"))
        rows.append({"manifest": m, "public": pub, "private": priv, "family": "genetic_pharmacological"})
    for path in sorted((ENGAGEMENT / "public").glob("*.json")):
        pub = json.loads(path.read_text(encoding="utf-8"))
        priv = json.loads((ENGAGEMENT / "private" / f"{path.stem}.results.json").read_text(encoding="utf-8"))
        rows.append({"manifest": {"case_id": pub["identifier"], "archetype": "engagement_repair", "gene": _gene(pub),
                                  "model_id": pub.get("context_identifier", "").split(":")[0], "index_compound": _compound(pub),
                                  "split": "engagement", "source_cluster": _gene(pub), "licensed_decisions": [],
                                  "critical_actions": []},
                     "public": pub, "private": priv, "family": "engagement"})
    return rows


def _gene(pub: dict) -> str:
    for e in pub.get("initial_evidence", ()):
        g = e.get("conditions", {}).get("gene")
        if g:
            return g
    return "unknown"


def _compound(pub: dict) -> str | None:
    for e in pub.get("initial_evidence", ()):
        c = e.get("conditions", {}).get("compound")
        if c:
            return c
    return None


def _status(result: dict) -> S.MeasurementStatus:
    if not result.get("record_validated", False):
        return S.MeasurementStatus.QC_FAILED
    if result.get("evidence_kind") == "real_measurement" and result.get("biological_quality") == "passed":
        return S.MeasurementStatus.QUALIFIED
    return S.MeasurementStatus.AMBIGUOUS


def to_case(row: dict, *, created_at: str, refs: tuple[S.RawDataRef, ...]) -> S.Case:
    m, pub, priv = row["manifest"], row["public"], row["private"]
    pattern = m["archetype"]
    kind = PATTERN_KIND.get(pattern, S.CaseKind.CONTRASTIVE if row["family"] == "engagement" else S.CaseKind.CANONICAL)
    problem_type = S.ProblemType.ENGAGEMENT_REPAIR if row["family"] == "engagement" else S.ProblemType.GENETIC_PHARMACOLOGICAL
    hyp = [S.HypothesisClaim(h["identifier"], h["description"]) for h in pub["hypotheses"]]
    hyp += [S.HypothesisClaim(i, d, (), {}, True) for i, d in ADVISORY]
    actions = tuple(S.ActionSpec(a["identifier"], a["description"], a.get("kind", "evidence_review"), float(a["cost"]),
                                 1.0 if a.get("kind") == "evidence_review" else 7.0, a.get("readout") or a.get("quantity", ""),
                                 None, None, None, tuple(a.get("prerequisites", ()) or ()), (),
                                 None, bool(a.get("available", True))) for a in pub["actions"])
    obs = tuple(S.Observation(e["identifier"], S.MeasurementStatus.AMBIGUOUS if e.get("evidence_kind") != "real_measurement"
                              else S.MeasurementStatus.QUALIFIED, e.get("conditions", {}).get("assay", "processed record"),
                              e.get("conditions", {}).get("model_id"), None, None, e.get("conditions", {}).get("assay"), None,
                              None, None, None, e["statement"]) for e in pub["initial_evidence"])
    measurements, cards = [], []
    known = {a.action_id for a in actions}
    for r in priv["results"]:
        if r["action_identifier"] not in known:
            continue
        st = _status(r)
        measurements.append(S.Measurement(r["action_identifier"], st, r["outcome"], r.get("independent_units"), r["source_id"]))
        if st is S.MeasurementStatus.QUALIFIED:
            cards.append({"action_id": r["action_identifier"], "statement": r["statement"],
                          "evidence_class": S.EvidenceClass.QUALIFIED_EVIDENCE.value})
    licensed = list(m.get("licensed_decisions") or [])
    decision = licensed[0] if licensed and licensed[0] in S.DECISION_STATUSES else "open"
    critical = list(m.get("critical_actions") or [])
    modes = [S.FailureMode(pattern, _PATTERN_TEXT.get(pattern, "engagement-repair discordance between genetic and pharmacological evidence"),
                           severity="major" if kind is S.CaseKind.FAILURE else "informational")]
    if kind is S.CaseKind.CONTRASTIVE:
        modes = [S.FailureMode("contrast_" + pattern, _PATTERN_TEXT.get(pattern, "genetic and pharmacological evidence disagree"))]
    statuses = {"engagement": S.MeasurementStatus.NOT_PLANNED, "function": S.MeasurementStatus.NOT_PLANNED,
                "pathway": S.MeasurementStatus.NOT_PLANNED, "cell_state": S.MeasurementStatus.NOT_PLANNED,
                "phenotype": S.MeasurementStatus.AMBIGUOUS, "assay": S.MeasurementStatus.AMBIGUOUS}
    gene = m.get("gene") or "unknown"
    graph = HG.template_for(m["case_id"], m.get("index_compound") or "compound", gene, pub.get("context_identifier", ""),
                            "viability AUC / gene effect", statuses, action_ids=[a.action_id for a in actions],
                            sources=("DepMap 24Q2", "PRISM 19Q4"))
    fp = {"dataset": "depmap24q2+prism19q4", "assay": "genetic_pharmacological_evidence_review",
          "context": pub.get("context_identifier", ""), "compound": m["case_id"], "unit": m.get("source_cluster") or gene,
          "hypothesis_class": pattern, "gene": gene, "index_compound": m.get("index_compound"), "model_id": m.get("model_id"),
          "cell_line": m.get("cell_line"), "split": m.get("split"), "measurement_type": "evidence_review",
          "intervention_type": "small_molecule", "biological_system": "human_cancer_cell_line", "is_training": True,
          "graph_edges": len(graph.edges), "graph_unmeasured_layers": list(graph.unmeasured_layers()),
          "features": {k: m.get(k) for k in FEATURES}}
    return S.Case(
        case_id=m["case_id"], case_version=1, case_kind=kind, problem_type=problem_type,
        problem_statement=pub["hypotheses"][0]["description"] + " Is it supported?", user_question="What should be done next?",
        raw_data_references=refs, data_quality_report={"usable": True, "note": "retrospective processed public records",
                                                        "passed_fraction": 1.0},
        context_fingerprint=fp, initial_observations=obs, initial_hypotheses=tuple(hyp), candidate_actions=actions,
        retrieved_knowledge=tuple(S.KnowledgeRef("package_limitation", f"{m['case_id']}#{i}", text)
                                  for i, text in enumerate(pub.get("limitations", ())[:4])),
        virtual_cell_predictions=(), predicted_outcome_branches=(), real_measurements=tuple(measurements),
        measurement_quality={}, qualified_evidence=tuple(cards), hypothesis_updates=(),
        final_decision={"status": decision, "licensed": licensed,
                        "basis": "declared evidence-sufficiency rule of the case package, not biological truth"},
        next_action={"critical_actions": critical, "why": "actions the licensing rule requires before the decision"},
        failure_modes=tuple(modes), adaptation_map=(), calibration_history=(),
        provenance={"builder": "maestro_vc_v1.family2", "sources": {"real_case_manifest_v3": _sha(MANIFEST)},
                    "created_at": created_at, "package": str(PACKAGE.relative_to(ROOT).as_posix()),
                    "graph": graph.payload()})


_PATTERN_TEXT = {
    "concordant_program_support": "genetic dependency and pharmacological response agree; nothing on the menu can change the decision",
    "unattributed_pharmacology": "a pharmacological response exists with no genetic dependency to attribute it to",
    "pan_essential_attribution": "a panel-wide genetic dependency cannot be attributed to the intended target programme",
    "mode_non_equivalence": "genetic and pharmacological perturbation modes are not equivalent for this target",
    "no_discriminating_evidence": "no action in the menu can change the decision within the declared limits",
    "implementation_gap": "a needed measurement is unavailable in the package",
}


def build_store(path: Path | None = None, *, created_at: str = "2026-09-29") -> CS.CaseStore:
    refs = tuple(S.RawDataRef(f"data/raw/{sub}", _sha(ROOT / f"data/raw/{sub}/{name}"), role)
                 for sub, name, role in (("depmap", "Model.csv", "model_metadata"),
                                         ("prism", "secondary-screen-cell-line-info.csv", "prism_cell_lines")))
    store = CS.CaseStore(path)
    for row in load_rows():
        store.append(to_case(row, created_at=created_at, refs=refs))
    return store


# ---------------------------------------------------------------------------------------- retrieval
def feature_vector(case: S.Case) -> np.ndarray:
    f = case.context_fingerprint["features"]
    return np.array([np.nan if f.get(k) is None else float(f[k]) for k in FEATURES])


def _lineage(cell: str | None) -> str:
    return (cell or "").split("_", 1)[1] if cell and "_" in cell else (cell or "")


def _pathways(genes: set[str]) -> dict[str, set]:
    """Reactome pathway sets per gene symbol (local NCBI2Reactome and HGNC)."""
    import pandas as pd

    hgnc = pd.read_csv(ROOT / "data/external/hgnc/hgnc_complete_set.txt", sep="\t", dtype=str, usecols=["symbol", "entrez_id"])
    entrez = hgnc[hgnc.symbol.isin(genes)].dropna().set_index("symbol").entrez_id.to_dict()
    wanted = set(entrez.values())
    sets: dict[str, set] = {v: set() for v in wanted}
    with open(ROOT / "data/raw/ontology/NCBI2Reactome.txt", "r", encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 6 and parts[0] in wanted and parts[5] == "Homo sapiens":
                sets[parts[0]].add(parts[1])
    return {g: sets.get(entrez.get(g, ""), set()) for g in genes}


def evaluate_retrieval(cases: list[S.Case], *, top_k: int = 5) -> dict:
    """Leave-one-target-gene-out: does the retrieved precedent predict the target's pattern and licensed decision?"""
    fam = [c for c in cases if c.problem_type is S.ProblemType.GENETIC_PHARMACOLOGICAL]
    X = np.stack([feature_vector(c) for c in fam])
    scale = np.nanstd(X, axis=0)
    scale[scale == 0] = 1.0
    genes = {c.context_fingerprint["gene"] for c in fam}
    paths = _pathways(genes)
    pattern = np.array([c.context_fingerprint["hypothesis_class"] for c in fam])
    decision = np.array([c.final_decision["status"] for c in fam])
    gene = np.array([c.context_fingerprint["gene"] for c in fam])
    lineage = np.array([_lineage(c.context_fingerprint.get("cell_line")) for c in fam])
    compound = np.array([c.context_fingerprint.get("index_compound") or "" for c in fam])
    avail = np.array(["|".join(sorted(a.action_id for a in c.candidate_actions if a.available)) for c in fam])
    quality = np.array([np.clip(c.context_fingerprint["features"].get("index_curve_r2") or 0.5, 0.0, 1.0) for c in fam])
    out = {"cases": len(fam), "genes": len(genes), "retrievers": {}}
    majority = float(max((pattern == p).mean() for p in set(pattern)))
    out["majority_pattern_share"] = majority
    votes: dict[str, list] = {"semantic": [], "pattern": [], "adaptation": []}
    kish_list = []
    for i in range(len(fam)):
        pool = np.flatnonzero(gene != gene[i])
        diff = np.abs(X[pool] - X[i]) / scale
        with np.errstate(invalid="ignore"):
            dist = np.nanmean(diff, axis=1)
        dist = np.where(np.isfinite(dist), dist, np.nanmax(dist[np.isfinite(dist)]) if np.isfinite(dist).any() else 1.0)
        pattern_sim = np.exp(-dist)
        semantic = ((compound[pool] == compound[i]) & (compound[i] != "")).astype(float) * 2.0 \
            + (lineage[pool] == lineage[i]).astype(float)
        semantic = semantic + 1e-6 * np.arange(len(pool))[::-1] / len(pool)  # deterministic tie-break
        pi = paths[gene[i]]
        mech = np.array([len(pi & paths[gene[j]]) / max(len(pi | paths[gene[j]]), 1) for j in pool])
        cost = 0.25 * ((lineage[pool] != lineage[i]).astype(float) + (compound[pool] != compound[i]).astype(float)
                       + (avail[pool] != avail[i]).astype(float))
        shift = 1.0 - pattern_sim.max()
        score = pattern_sim + mech + 1.0 + 1.0 + quality[pool] + 0.5 - cost - shift
        for name, s in (("semantic", semantic), ("pattern", pattern_sim), ("adaptation", score)):
            order = np.argsort(-s)[:top_k]
            w = s[order] - s[order].min() + 1e-6 if name != "semantic" else np.maximum(s[order], 1e-6)
            v = {}
            for j, wj in zip(pool[order], w):
                v[(pattern[j], decision[j])] = v.get((pattern[j], decision[j]), 0.0) + float(wj)
            best = max(v, key=v.get)
            share = v[best] / sum(v.values())
            kish = float(w.sum() ** 2 / (w ** 2).sum())
            votes[name].append({"pattern": best[0], "decision": best[1], "share": share, "kish": kish,
                                "top_score": float(s[order[0]])})
        kish_list.append(votes["adaptation"][-1]["kish"])
    threshold = float(np.median([v["top_score"] for v in votes["adaptation"]]))
    for name, v in votes.items():
        hit_p = np.array([x["pattern"] == p for x, p in zip(v, pattern)])
        hit_d = np.array([x["decision"] == d for x, d in zip(v, decision)])
        rec = {"pattern_accuracy": float(hit_p.mean()), "decision_agreement": float(hit_d.mean())}
        if name == "adaptation":
            answer = np.array([x["top_score"] >= threshold and x["share"] >= 0.5 for x in v])
            rec.update({"answered_share": float(answer.mean()),
                        "pattern_accuracy_when_answered": float(hit_p[answer].mean()) if answer.any() else None,
                        "decision_agreement_when_answered": float(hit_d[answer].mean()) if answer.any() else None,
                        "abstention_rule": "answer only when the top case score reaches the median and the vote share is at least 0.5"})
        rng = np.random.default_rng(20260929)
        units = {g: k for k, g in enumerate(sorted(genes))}
        codes = np.array([units[g] for g in gene])
        sums = np.bincount(codes, weights=hit_p.astype(float), minlength=len(units))
        counts = np.bincount(codes, minlength=len(units)).astype(float)
        idx = rng.integers(len(units), size=(2000, len(units)))
        boot = sums[idx].sum(1) / counts[idx].sum(1)
        rec["pattern_accuracy_ci"] = np.quantile(boot, [0.025, 0.975]).tolist()
        out["retrievers"][name] = rec
    out["semantic_neighbour_shares_pattern"] = float(np.mean([
        (pattern[np.flatnonzero(gene != gene[i])][int(np.argmax(
            ((compound[gene != gene[i]] == compound[i]) & (compound[i] != "")).astype(float) * 2.0
            + (lineage[gene != gene[i]] == lineage[i]).astype(float)))] == pattern[i]) for i in range(len(fam))]))
    return out
