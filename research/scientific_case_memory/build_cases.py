"""Build typed cases from a fold's training references, and the adaptation record between them.

File summary
- Path: research/scientific_case_memory/build_cases.py
- Purpose: turn the reference compounds of one (dataset, tier, fold) task into `Case` documents, type
  each as canonical, contrastive or failure, derive the adaptation table from pairs of references,
  and write an append-only snapshot with a digest. The memory a forecast reads is exactly this set.
- Core points:
  - Fold discipline. A snapshot for fold f contains only compounds not in fold f. Each reference's
    readings are the registered validator's readings with its whole independent unit left out
    (`belief_planning.world.group_out_outcomes`), so a case never encodes the held-out compound.
    `fold = -1` builds the full library used for real user problems, where no compound is held out.
  - Case typing (declared before any replay). FAILURE: undetected at every measured condition, or at
    least a quarter of scored readings match the decoy. CONTRASTIVE: not a failure, and a structural
    neighbour of another class and another independent unit has Tanimoto >= 0.50, so the same
    structure has been seen with a different mechanism. CANONICAL: everything else that was measured.
  - Measurement status per condition: not planned (the design never ran it), QC failed (planned, ran,
    failed), undetected, ambiguous (every decoy unresolved) or qualified (at least one decoy was
    eliminated or matched). A missing value is never a zero.
  - Adaptation. For pairs of same-class references of different units, the reading of the source at
    its condition is compared with the target's at another (or the same) condition; success is equal
    codes. Counts are aggregated by difference signature into an `AdaptationTable`; representative
    pairs are written as ADAPTATION cases with the table's cost and the conditions where transfer held
    or failed.
  - Everything is deterministic: `created_at` is a fixed string supplied by the caller, and the
    sampling of representative adaptation pairs is seeded.
- Interfaces: `TaskInputs`, `Snapshot`, `load_inputs`, `build_snapshot`, `type_cases`,
  `build_adaptation`, `CONTRAST_TANIMOTO`, `MISLEADING_SHARE`
- Depends on: case_schema.py, case_store.py, case_index.py, adaptation_model.py, protocol_library.py,
  research/protocol_v2 (tasks_v21, contracts), research/belief_planning (world, arms, tasks)
"""
from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import adaptation_model as AM
from . import case_index as CI
from . import case_retrieval as CR
from . import case_schema as S
from . import case_store as CS
from . import protocol_library as PL

CONTRAST_TANIMOTO = 0.50
MISLEADING_SHARE = 0.25
ROOT = Path(__file__).resolve().parents[2]


@dataclass
class TaskInputs:
    dataset: str
    tier: str
    fold: int
    data: object
    ctx: object
    setting: object
    design: dict
    fp: np.ndarray
    pos: dict
    unit_of: dict
    klass_of: dict
    smiles_of: dict
    training: tuple
    sources: dict


@dataclass
class Snapshot:
    snapshot_id: str
    store: CS.CaseStore
    index: CI.CaseIndex
    adaptation: AM.AdaptationTable
    manifest: dict
    inputs: TaskInputs

    def cases(self):
        return self.store.latest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                              timeout=10).stdout.strip() or "unknown"
    except Exception:  # pragma: no cover - environment
        return "unknown"


def load_inputs(dataset: str, tier: str, fold: int) -> TaskInputs:
    """The protocol-v2.1 fold context, structure fingerprints and unit maps for one task."""
    from research.belief_planning import arms as BA
    from research.belief_planning import tasks as T
    from research.protocol_v2 import tasks_v21 as V

    data, ctx, setting, design = V.load(dataset, tier, fold)
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    unit_col = "component" if "component" in comp.columns else "skeleton"
    unit_of = {c: str(g) for c, g in comp[unit_col].items() if isinstance(g, str)}
    fp, pos = BA.fingerprints(data.compounds)
    klass_of = {c: k for c, k in comp.klass.items() if isinstance(k, str)}
    smiles_of = {c: s for c, s in comp.smiles.items() if isinstance(s, str)}
    heldout = set(comp.index[comp.fold == fold]) if fold >= 0 else set()
    training = tuple(c for c in ctx.tier.compounds if c not in heldout and klass_of.get(c) in ctx.tier.pool)
    prepared = {"sciplex3": ("outputs/dynamic_world_model_20260926/prepared/conditions.csv",
                             "outputs/dynamic_world_model_20260926/prepared/shifts.npz"),
                "l1000": ("outputs/sequence_audit_20260926/l1000/prepared/conditions.csv",
                          "outputs/sequence_audit_20260926/l1000/prepared/shifts.npz")}[dataset]
    sources = {p: sha256_file(ROOT / p) for p in prepared}
    return TaskInputs(dataset, tier, fold, data, ctx, setting, design, fp, pos, unit_of, klass_of, smiles_of,
                      training, sources)


# ---------------------------------------------------------------------------------------- cases
def _readings(inputs: TaskInputs) -> dict:
    """key -> {(name, decoy): code}, unit-out readings of every reference at every key."""
    from research.belief_planning import world as W

    ctx = inputs.ctx
    out = {}
    for key in ctx.tier.keys:
        raw = W.group_out_outcomes(ctx.ft, key, ctx.params["floor"], ctx.params["margin"], inputs.unit_of)
        out[key] = {k: W.CODE[v] for k, v in raw.items()}
    return out


def _kind_of_codes(codes: np.ndarray) -> S.ReadingKind:
    scored = codes[codes >= 0]
    if len(scored) == 0:
        return S.ReadingKind.QC_FAILED
    if (scored == 1).any():
        return S.ReadingKind.MISLEADING
    if (scored == 3).all():
        return S.ReadingKind.NEGATIVE
    if (scored == 2).all():
        return S.ReadingKind.AMBIGUOUS
    return S.ReadingKind.CANONICAL


def _status(codes: np.ndarray, qc: bool, planned: bool, has_row: bool) -> S.MeasurementStatus:
    if not planned:
        return S.MeasurementStatus.NOT_PLANNED
    if not has_row or not qc:
        return S.MeasurementStatus.QC_FAILED
    scored = codes[codes >= 0]
    if len(scored) == 0 or (scored == 3).all():
        return S.MeasurementStatus.UNDETECTED
    if (scored == 2).all():
        return S.MeasurementStatus.AMBIGUOUS
    return S.MeasurementStatus.QUALIFIED


def build_snapshot(inputs: TaskInputs, *, created_at: str, snapshot_id: str | None = None,
                   path: str | Path | None = None) -> Snapshot:
    ctx, data, setting = inputs.ctx, inputs.data, inputs.setting
    pool = tuple(ctx.tier.pool)
    keys = tuple(ctx.tier.keys)
    snapshot_id = snapshot_id or f"{inputs.dataset}-{inputs.tier}-f{inputs.fold}"
    readings = _readings(inputs)
    tables = ctx.ft.tables
    members = {key: set(t.names) for key, t in tables.items()}
    names = sorted({n for t in tables.values() for n in t.names if inputs.klass_of.get(n) in pool})
    training = set(inputs.training)
    protocol = _protocol(inputs)
    actions = tuple(p.to_action_spec() for p in protocol)
    action_by_key = {tuple(p.key): p.action_id for p in protocol}
    refs = tuple(S.RawDataRef(uri=uri, sha256=sha, role="prepared_state_table")
                 for uri, sha in sorted(inputs.sources.items()))
    cases: dict[str, S.Case] = {}
    for name in names:
        klass = inputs.klass_of[name]
        planned = inputs.design.get(name, frozenset())
        observations, measurements, updates, quality_rows = [], [], [], []
        for key in keys:
            row = data.index.get(key, {}).get(name)
            aid = action_by_key[tuple(key)]
            in_table = name in members[key]
            codes = np.full(len(pool), -1, dtype=int)
            if in_table:
                for j, o in enumerate(pool):
                    if o != klass:
                        codes[j] = readings[key].get((name, o), -1)
            qc = row is not None and bool(_qc(data, row))
            status = _status(codes, qc, tuple(key) in planned, row is not None)
            detected = bool(ctx.detected[row]) if row is not None else None
            agreement = float(data.agreement[row]) if row is not None and np.isfinite(data.agreement[row]) else None
            value = float(np.linalg.norm(data.shift[row])) if (row is not None and status.biological) else None
            observations.append(S.Observation(
                condition_id=aid, status=status, assay=protocol[0].assay, cell_line=key[0], time_h=float(key[1]),
                dose_nM=float(key[2]), readout="transcriptome_shift_norm" if value is not None else None, value=value,
                replicate_agreement=agreement, detected=detected,
                state_ref=S.RawDataRef(uri=list(inputs.sources)[1], sha256=list(inputs.sources.values())[1],
                                       role="state_vector", row=int(row)) if row is not None else None))
            if status.biological:
                measurements.append(S.Measurement(aid, status, CI.LABEL_OF_CODE.get(int(_mode(codes)), "not_scored"), 1,
                                                  f"{inputs.dataset}:{name}"))
                eliminated = tuple(pool[j] for j in np.flatnonzero(codes == 0))
                updates.append(S.HypothesisUpdate(aid, (klass, "*pool*"), "unit_out_reading_vs_each_pool_class",
                                                  eliminated, status is S.MeasurementStatus.QUALIFIED,
                                                  _kind_of_codes(codes), "", CI.encode_codes(codes)))
            quality_rows.append((status, agreement))
        cases[name] = _assemble(inputs, name, klass, observations, measurements, updates, quality_rows, actions, refs,
                                pool, created_at, snapshot_id, name in training)
    typed = type_cases(cases, inputs, pool, keys, snapshot_id)
    store = CS.CaseStore(path)
    for case in typed.values():
        store.append(case)
    table = build_adaptation(inputs, cases, readings, pool, keys)
    adaptation_cases = _adaptation_cases(inputs, cases, readings, pool, keys, table, created_at, snapshot_id, actions, refs)
    for case in adaptation_cases:
        store.append(case)
    ref_cases = [c for c in store.latest() if c.case_kind is not S.CaseKind.ADAPTATION]
    index = CI.CaseIndex.from_cases(ref_cases, pool, keys, fingerprints=inputs.fp, fp_pos=inputs.pos)
    manifest = {"snapshot_id": snapshot_id, "digest": store.snapshot_digest(), "fold": inputs.fold,
                "dataset": inputs.dataset, "tier": inputs.tier, "cases": len(ref_cases),
                "training_cases": sum(c.context_fingerprint["is_training"] for c in ref_cases),
                "adaptation_cases": len(adaptation_cases),
                "kinds": _count(c.case_kind.value for c in store.latest()),
                "reading_kinds": index.reading_kind_counts(), "pool": list(pool),
                "adaptation_table_rows": table.rows()}
    return Snapshot(snapshot_id, store, index, table, manifest, inputs)


def _qc(data, row) -> bool:
    from research.dynamic_world_model import common as C
    return C.qc_passed(data, row)


def _mode(codes: np.ndarray) -> int:
    scored = codes[codes >= 0]
    return int(np.bincount(scored, minlength=4).argmax()) if len(scored) else -1


def _count(items) -> dict:
    out: dict = {}
    for i in items:
        out[i] = out.get(i, 0) + 1
    return dict(sorted(out.items()))


def _protocol(inputs: TaskInputs):
    ctx, setting = inputs.ctx, inputs.setting
    detected_at = {}
    for key, t in ctx.ft.tables.items():
        detected_at[tuple(key)] = (int(np.asarray(t.detected, dtype=bool).sum()), len(t.names))
    planned_any = {tuple(k) for c in inputs.training for k in inputs.design.get(c, frozenset())}
    assay = "sci-RNA-seq3 transcriptome" if inputs.dataset == "sciplex3" else "L1000 bead-based expression signature"
    return PL.build_protocol_library(ctx.tier.keys, setting.days, assay=assay, detected_at=detected_at,
                                     planned=[k for k in ctx.tier.keys if tuple(k) in planned_any])


def _assemble(inputs, name, klass, observations, measurements, updates, quality_rows, actions, refs, pool, created_at,
              snapshot_id, is_training) -> S.Case:
    biological = [o for o in observations if o.status.biological]
    passed = [o for o in observations if o.status.biological]
    planned = [o for o in observations if o.status is not S.MeasurementStatus.NOT_PLANNED]
    agreements = [o.replicate_agreement for o in biological if o.replicate_agreement is not None]
    quality = {"planned": len(planned), "measured": len(biological),
               "qc_failed": sum(o.status is S.MeasurementStatus.QC_FAILED for o in observations),
               "undetected": sum(o.status is S.MeasurementStatus.UNDETECTED for o in observations),
               "passed_fraction": (len(passed) / len(planned)) if planned else 0.0,
               "mean_agreement": float(np.mean(agreements)) if agreements else None, "usable": bool(biological)}
    dataset = inputs.dataset
    assay = actions[0].assay if actions else dataset
    unit = inputs.unit_of.get(name, name)
    fingerprint = {"dataset": dataset, "assay": assay, "context": f"{dataset}:{inputs.tier}", "compound": name,
                   "unit": unit, "hypothesis_class": klass, "tier": inputs.tier, "snapshot": snapshot_id,
                   "measurement_type": "transcriptome_shift", "unit_of_measure": "signed_log2_shift",
                   "time_scale": "hours", "dose_scale": "nM", "control_design": "matched_vehicle",
                   "intervention_type": "small_molecule", "biological_system": "human_cancer_cell_line",
                   "is_training": bool(is_training), "smiles": inputs.smiles_of.get(name)}
    fingerprint["unit"] = unit
    hardest = pool[0] if pool[0] != klass else pool[1]
    hypotheses = (
        S.HypothesisClaim("own", f"The mechanism class of {name} is {klass}.", ("class annotation is a label, not truth",)),
        S.HypothesisClaim("decoy", f"The mechanism class of {name} is {hardest}.", ()),
    )
    knowledge = (S.KnowledgeRef("class_annotation", klass, f"Annotated mechanism class of {name}: {klass}",
                                S.EvidenceClass.MECHANISTIC_INFERENCE),)
    qualified = tuple({"action_id": m.action_id, "statement": f"{m.action_id} eliminated or matched a pool class",
                       "evidence_class": S.EvidenceClass.QUALIFIED_EVIDENCE.value}
                      for m in measurements if m.status is S.MeasurementStatus.QUALIFIED)
    best = max(measurements, key=lambda m: (m.status is S.MeasurementStatus.QUALIFIED), default=None)
    return S.Case(
        case_id=f"{dataset}:{inputs.tier}:{name}", case_version=1, case_kind=S.CaseKind.CANONICAL,
        problem_type=S.ProblemType.MECHANISM_CONTRAST_TRANSCRIPTOMIC,
        problem_statement=f"Which mechanism class does {name} belong to, among {len(pool)} classes of {dataset} tier {inputs.tier}?",
        user_question="What should be measured next to tell the competing mechanism classes apart?",
        raw_data_references=refs, data_quality_report=quality, context_fingerprint=fingerprint,
        initial_observations=tuple(observations), initial_hypotheses=hypotheses, candidate_actions=actions,
        retrieved_knowledge=knowledge, virtual_cell_predictions=(), predicted_outcome_branches=(),
        real_measurements=tuple(measurements), measurement_quality=quality, qualified_evidence=qualified,
        hypothesis_updates=tuple(updates),
        final_decision={"status": "decided", "class": klass, "basis": "annotated mechanism class of a reference compound"},
        next_action={"action_id": best.action_id if best else None,
                     "why": "first condition at which this compound gave a qualified reading" if best else "none measured"},
        failure_modes=(), adaptation_map=(), calibration_history=(),
        provenance={"builder": "scientific_case_memory.build_cases", "sources": dict(inputs.sources),
                    "created_at": created_at, "snapshot": snapshot_id, "code_commit": git_head(),
                    "fold": inputs.fold})


def type_cases(cases: dict, inputs: TaskInputs, pool, keys, snapshot_id: str) -> dict:
    """Assign canonical, contrastive or failure and record the failure modes and contrast partners."""
    from dataclasses import replace
    names = sorted(cases)
    fp, has = _fingerprints(inputs, names)
    tan = CR.tanimoto(fp, fp) if has.any() else np.zeros((len(names), len(names)))
    tan = np.where(has[:, None] & has[None, :], tan, 0.0)
    klass = np.array([cases[n].context_fingerprint["hypothesis_class"] for n in names], dtype=object)
    units = np.array([cases[n].context_fingerprint["unit"] for n in names], dtype=object)
    out = {}
    for i, name in enumerate(names):
        case = cases[name]
        modes: list[S.FailureMode] = []
        all_codes = [CI.decode_codes(u.codes) for u in case.hypothesis_updates]
        scored = np.concatenate([c[c >= 0] for c in all_codes]) if all_codes else np.array([], dtype=int)
        measured = len([o for o in case.initial_observations if o.status.biological])
        for o in case.initial_observations:
            if o.status is S.MeasurementStatus.QC_FAILED:
                modes.append(S.FailureMode("qc_failure", f"{o.condition_id} ran and failed its quality rule", o.condition_id))
        undetected_all = measured > 0 and all(o.status is S.MeasurementStatus.UNDETECTED
                                              for o in case.initial_observations if o.status.biological)
        if undetected_all:
            modes.append(S.FailureMode("undetected_everywhere", "no measured condition produced a detectable response",
                                       severity="major"))
        share = float((scored == 1).mean()) if len(scored) else 0.0
        if share >= MISLEADING_SHARE:
            modes.append(S.FailureMode("misleading_majority", f"{share:.2f} of scored readings matched a decoy class",
                                       severity="major"))
        for u, codes in zip(case.hypothesis_updates, all_codes):
            if (codes == 1).any():
                bad = [pool[j] for j in np.flatnonzero(codes == 1)][:3]
                modes.append(S.FailureMode("misleading_reading", f"profile matched {', '.join(bad)} instead of {klass[i]}",
                                           u.action_id, (klass[i], bad[0])))
        neighbour = np.flatnonzero((tan[i] >= CONTRAST_TANIMOTO) & (klass != klass[i]) & (units != units[i]))
        if len(neighbour):
            j = int(neighbour[np.argmax(tan[i][neighbour])])
            modes.append(S.FailureMode("contrast_structural_neighbour_other_class",
                                       f"{names[j]} (Tanimoto {tan[i][j]:.2f}) has structure like this one but class {klass[j]}",
                                       None, (klass[i], klass[j]), "informational"))
        major = any(m.severity == "major" for m in modes)
        if major:
            kind = S.CaseKind.FAILURE
        elif any(m.code.startswith("contrast") for m in modes):
            kind = S.CaseKind.CONTRASTIVE
        else:
            kind = S.CaseKind.CANONICAL
        out[name] = replace(case, case_kind=kind, failure_modes=tuple(modes))
    return out


def _fingerprints(inputs: TaskInputs, names):
    rows = np.array([inputs.pos.get(n, -1) for n in names], dtype=int)
    fp = np.where((rows >= 0)[:, None], inputs.fp[np.maximum(rows, 0)], 0.0)
    return fp, (rows >= 0) & fp.any(axis=1)


# ---------------------------------------------------------------------------------------- adaptation
def _key_context(inputs: TaskInputs, key) -> AM.Context:
    assay = "transcriptome"
    return AM.Context(inputs.dataset, assay, key[0], float(key[1]), float(key[2]), None)


def build_adaptation(inputs: TaskInputs, cases: dict, readings: dict, pool, keys) -> AM.AdaptationTable:
    """Aggregate every same-class, other-unit pair of references over every ordered pair of conditions."""
    names = sorted(cases)
    klass = np.array([cases[n].context_fingerprint["hypothesis_class"] for n in names], dtype=object)
    units = np.array([cases[n].context_fingerprint["unit"] for n in names], dtype=object)
    code = {key: np.full((len(names), len(pool)), -1, dtype=int) for key in keys}
    for key in keys:
        idx = {n: i for i, n in enumerate(names)}
        for (n, o), c in readings[key].items():
            if n in idx and o in pool:
                code[key][idx[n], pool.index(o)] = c
    # chance: expected agreement of two independent draws from the pooled reading distribution
    pooled = np.zeros(4)
    for key in keys:
        c = code[key][code[key] >= 0]
        pooled += np.bincount(c, minlength=4)
    p = pooled / pooled.sum() if pooled.sum() else np.full(4, 0.25)
    table = AM.AdaptationTable(chance=float((p ** 2).sum()))
    same_unit = units[:, None] == units[None, :]
    for ki, k_src in enumerate(keys):
        for k_tgt in keys:
            diff = AM.differences(_key_context(inputs, k_src), _key_context(inputs, k_tgt))
            sig = AM.signature(diff)
            hits = trials = 0
            for h in pool:
                members = np.flatnonzero(klass == h)
                if len(members) < 2:
                    continue
                for oi, o in enumerate(pool):
                    if o == h:
                        continue
                    s = code[k_src][members, oi]
                    t = code[k_tgt][members, oi]
                    ok_s, ok_t = s >= 0, t >= 0
                    pair_ok = ok_s[:, None] & ok_t[None, :] & ~same_unit[np.ix_(members, members)]
                    agree = s[:, None] == t[None, :]
                    hits += int((pair_ok & agree).sum())
                    trials += int(pair_ok.sum())
            table.add_bulk(sig, hits, trials)
    return table


def _adaptation_cases(inputs, cases, readings, pool, keys, table, created_at, snapshot_id, actions, refs,
                      per_signature: int = 2) -> list[S.Case]:
    """Representative transfers as ADAPTATION cases: seeded pairs per signature, half successes, half failures."""
    rng = np.random.default_rng([20260929, inputs.fold + 1, int(hashlib.sha256(inputs.tier.encode()).hexdigest()[:6], 16)])
    names = sorted(cases)
    klass = {n: cases[n].context_fingerprint["hypothesis_class"] for n in names}
    unit = {n: cases[n].context_fingerprint["unit"] for n in names}
    idx = {n: i for i, n in enumerate(names)}
    out: list[S.Case] = []
    seen: dict = {}
    for k_src in keys:
        for k_tgt in keys:
            diff = AM.differences(_key_context(inputs, k_src), _key_context(inputs, k_tgt))
            sig = AM.signature(diff)
            for want in (True, False):
                if seen.get((sig, want), 0) >= per_signature:
                    continue
                for _ in range(200):
                    a, b = rng.integers(0, len(names), 2)
                    src, tgt = names[a], names[b]
                    if src == tgt or klass[src] != klass[tgt] or unit[src] == unit[tgt]:
                        continue
                    oi = int(rng.integers(0, len(pool)))
                    if pool[oi] == klass[src]:
                        continue
                    cs = readings[k_src].get((src, pool[oi]))
                    ct = readings[k_tgt].get((tgt, pool[oi]))
                    if cs is None or ct is None or (cs == ct) != want:
                        continue
                    seen[(sig, want)] = seen.get((sig, want), 0) + 1
                    link = AM.make_link(cases[src].case_id, cases[tgt].case_id, _key_context(inputs, k_src),
                                        _key_context(inputs, k_tgt), table, want)
                    out.append(_adaptation_case(inputs, src, tgt, link, want, pool[oi], k_src, k_tgt, created_at,
                                                snapshot_id, actions, refs, len(out)))
                    break
    return out


def _adaptation_case(inputs, src, tgt, link, success, decoy, k_src, k_tgt, created_at, snapshot_id, actions, refs, n):
    fingerprint = {"dataset": inputs.dataset, "assay": actions[0].assay if actions else inputs.dataset,
                   "context": f"{inputs.dataset}:{inputs.tier}", "compound": f"adapt-{n:04d}-{src}-{tgt}",
                   "unit": f"adapt-{src}-{tgt}", "hypothesis_class": None, "snapshot": snapshot_id,
                   "is_training": True, "source": src, "target": tgt}
    return S.Case(
        case_id=f"{inputs.dataset}:{inputs.tier}:adaptation:{n:04d}", case_version=1, case_kind=S.CaseKind.ADAPTATION,
        problem_type=S.ProblemType.MECHANISM_CONTRAST_TRANSCRIPTOMIC,
        problem_statement=f"Can the reading of {src} at {k_src} stand in for {tgt} at {k_tgt} against {decoy}?",
        user_question="Under what differences does a precedent transfer?",
        raw_data_references=refs, data_quality_report={"usable": False, "note": "adaptation record; not a reference"},
        context_fingerprint=fingerprint, initial_observations=(),
        initial_hypotheses=(S.HypothesisClaim("transfers", "The source reading equals the target reading."),
                            S.HypothesisClaim("does_not_transfer", "The source reading differs from the target reading.")),
        candidate_actions=actions, retrieved_knowledge=(), virtual_cell_predictions=(), predicted_outcome_branches=(),
        real_measurements=(), measurement_quality={}, qualified_evidence=(), hypothesis_updates=(),
        final_decision={"status": "decided", "success": success, "basis": "equal registered reading codes"},
        next_action={}, failure_modes=() if success else (S.FailureMode("adaptation_failed",
                                                                        "the source reading did not equal the target's"),),
        adaptation_map=(link,), calibration_history=(),
        provenance={"builder": "scientific_case_memory.build_cases", "sources": dict(inputs.sources),
                    "created_at": created_at, "snapshot": snapshot_id, "code_commit": git_head(), "fold": inputs.fold})
