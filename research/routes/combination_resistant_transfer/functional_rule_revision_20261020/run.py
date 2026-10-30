"""Study runner: one entry point, explicit stages, a ledger of what each stage may read.

    python -m ... run.py qualify     parse originals, build groups, partition, seal outcomes by role
    python run.py freeze             S-only design, tuning limits, precision pilot, panel; writes FREEZE.json
    python run.py challenge          initial model -> predictions -> disclose C -> diagnose -> revise -> seal nominations
    python run.py retention          single G query per arm, deployed procedures
    python run.py final              single F evaluation, results, report tables
    python run.py all

Stages are idempotent only up to their sealed outputs: a later stage refuses to run if its
predecessor's output is missing, and `final` refuses to run twice.
"""
from __future__ import annotations

import os

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_name, "4")

import hashlib
import json
import pickle
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import adapter  # noqa: E402
import design as D  # noqa: E402

ROOT = HERE.parents[1]
WORK = ROOT / "tmp" / "functional_rule_revision_20261020"   # regenerable caches and sealed role files (git-ignored)
SEALED = WORK / "sealed"


def dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- table persistence
def save_tables(T: adapter.GroupTable) -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    comb = np.array([list(r) for r in T.comb_rows], dtype=np.int64)
    mono_i = np.array([list(r) if r else [0] * 8 for r in T.mono_rows_i], dtype=np.int64)
    mono_j = np.array([list(r) if r else [0] * 8 for r in T.mono_rows_j], dtype=np.int64)
    np.savez_compressed(
        WORK / "groups.npz", drugs=np.array(T.drugs), cells=np.array(T.cells),
        pair_a=np.array([p[0] for p in T.pairs]), pair_b=np.array([p[1] for p in T.pairs]),
        g_pair=T.g_pair, g_cell=T.g_cell, g_batch=T.g_batch.astype(str), g_i=T.g_i, g_j=T.g_j,
        a_ref=T.a_ref, a_mono_i=T.a_mono_i, a_mono_j=T.a_mono_j, eligible=T.eligible,
        reason=T.reason.astype(str), first_row=T.first_row, n_rows=T.n_rows, n_dose_matched=T.n_dose_matched,
        comb_rows=comb, mono_rows_i=mono_i, mono_rows_j=mono_j)


def load_tables() -> adapter.GroupTable:
    z = np.load(WORK / "groups.npz", allow_pickle=False)
    pairs = tuple(zip(z["pair_a"].tolist(), z["pair_b"].tolist()))
    return adapter.GroupTable(
        tuple(z["drugs"].tolist()), tuple(z["cells"].tolist()), pairs, z["g_pair"], z["g_cell"],
        z["g_batch"].astype(object), z["g_i"], z["g_j"], z["a_ref"], z["a_mono_i"], z["a_mono_j"],
        z["eligible"], z["reason"].astype(object), z["first_row"], z["n_rows"], z["n_dose_matched"],
        [tuple(r) for r in z["mono_rows_i"]], [tuple(r) for r in z["mono_rows_j"]], [tuple(r) for r in z["comb_rows"]])


# --------------------------------------------------------------------------- stage: qualify
def working_tree_manifest() -> dict:
    """Targeted manifest of the files this study consumes (no secrets, no unrelated artefacts)."""
    consumed = ["tools/datasets/combination_screens.py", "tools/datasets/oneil_sources.py", "src/agent/llm.py",
                "data/ONEIL_SOURCES.json", "data/ONEIL_STRUCTURE.json", "data/INVENTORY.md",
                "log/20261020/NEXT_RESEARCH_PROMPT.md", "log/20261020/PREPARATION.md",
                "requirements-preparation.lock", "pyproject.toml"]
    entries = {}
    for rel in consumed:
        path = ROOT / rel
        entries[rel] = {"sha256_lf": adapter.sha256_text(path), "bytes": path.stat().st_size} if path.exists() else {"missing": True}
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    status = subprocess.run(["git", "status", "--short", "--"] + consumed, cwd=ROOT, capture_output=True, text=True).stdout
    return {"head": head, "branch": branch, "consumed_files": entries,
            "git_status_of_consumed_files": status.splitlines(),
            "note": "HEAD alone does not capture the input state: preparation changes are uncommitted; the hashes above do."}


def stage_qualify(force: bool = False) -> None:
    if (SEALED / "outcomes_F.npy").exists() and not force:
        print("qualify: sealed files already exist; refusing to rewrite (use --force only before freeze)")
        return
    t0 = time.time()
    single = adapter.read_single_agent()
    comb = adapter.read_combination()
    T, outcomes = adapter.build_groups(comb, single)
    # identity-only partition: no outcome is passed to this call
    roles_pair, part_meta = D.make_partition(T.pairs, T.drugs)
    role_of_group = roles_pair[T.g_pair]
    receipts = adapter.write_sealed(SEALED, outcomes["a_obs"], role_of_group)
    save_tables(T)
    drug_degree = {d: 0 for d in T.drugs}
    for p in T.pairs:
        drug_degree[p[0]] += 1
        drug_degree[p[1]] += 1
    s_degree = {d: 0 for d in T.drugs}
    for p, r in zip(T.pairs, roles_pair):
        if r == "S":
            s_degree[p[0]] += 1
            s_degree[p[1]] += 1
    partition = {
        "rule": "disjoint canonical unordered drug pairs; 60/15/10/15; every drug in >= 9 S pairs; first satisfying seed",
        "meta": part_meta, "n_pairs": len(T.pairs), "role_counts": {r: int((roles_pair == r).sum()) for r in "SCGF"},
        "roles": {"|".join(p): str(r) for p, r in zip(T.pairs, roles_pair)},
        "drug_pair_degree": drug_degree, "drug_S_pair_degree": s_degree,
        "all_cells_and_doses_follow_pair": True}
    dump(HERE / "PARTITION.json", partition)
    reasons = {}
    for r in T.reason:
        reasons[r or "eligible"] = reasons.get(r or "eligible", 0) + 1
    batch_rows = {b: int((comb["batch"] == b).sum()) for b in ("1", "2", "3")}
    provenance = {
        "sources": load(ROOT / "data" / "ONEIL_SOURCES.json"),
        "workbook_sha256_local": {name: adapter.sha256_file(adapter.ONEIL_DIR / name)
                                  for name in (adapter.ONEIL_COMBINATION, adapter.ONEIL_SINGLE)},
        "rows": {"single_agent": int(len(single["row"])), "combination": int(len(comb["row"])), "combination_by_batch": batch_rows},
        "primary_batches": list(adapter.PRIMARY_BATCHES), "batch_3": "excluded (selected repeat); not an automatic second test",
        "groups": {"pair_cell_groups": int(len(T.g_pair)), "pairs": len(T.pairs), "cells": len(T.cells), "drugs": len(T.drugs),
                   "by_batch": {b: int((T.g_batch == b).sum()) for b in ("1", "2")}},
        "endpoint": {"activity": "A = 1 - mean(X/X0) over the 16 published grid points, equal weight, no clipping",
                     "reference": "A_ref = 1 - mean(Xa(ca) * Xb(cb)); same-batch log-concentration interpolation of single-agent X/X0; "
                                  "never extrapolated or borrowed from another batch; derived, not observed",
                     "residual": "R = A - A_ref (= mean of expected-minus-observed X/X0); an interpolated functional reference residual, not validated Bliss synergy",
                     "raw_viability_columns": "retained in the original workbook (4 combination / 6 single-agent technical repeats); X/X0 is publisher-derived"},
        "measured_vs_derived": {"measured_or_publisher_derived_per_row": ["viability1..4/6", "mu/muMax", "X/X0"],
                                "derived_here": ["A", "A_ref", "R", "drug-cell monotherapy activity", "gates", "modules"]},
        "dose_matching": {"rel_tol": adapter.REL_TOL, "abs_tol": adapter.ABS_TOL,
                          "grid_points_matching_both_single_agent_doses": int(T.n_dose_matched.sum()),
                          "grid_points_total": int(T.n_rows.sum()),
                          "interpretation": "most reference values are interpolated, not dose-matched"},
        "technical_repeats": "4 combination / 6 single-agent columns are technical repeats; no plate, well, control, stock or bundle identifiers",
        "controls": "publisher DMSO normalisation; control wells are not exported; no control is borrowed across batches",
        "common_initial_information": {
            "monotherapy_panel": "complete single-agent curves (16,752 rows, 2,094 batch-cell-drug curves x 8 concentrations)",
            "role": "identical for every method; its cost is recorded as common initial information, not as incremental cost"},
        "receipts_sealed_outcome_files": receipts,
        "eligibility_counts": reasons,
        "table_file_sha256": adapter.sha256_file(WORK / "groups.npz"),
        "working_tree": working_tree_manifest(),
        "python": sys.version.split()[0], "seconds": round(time.time() - t0, 1)}
    dump(HERE / "PROVENANCE.json", provenance)
    print("qualify ok:", reasons, partition["role_counts"], part_meta)


# --------------------------------------------------------------------------- real-data context and stages
def real_context():
    import study
    T = load_tables()
    part = load(HERE / "PARTITION.json")
    roles = np.array([part["roles"]["|".join(p)] for p in T.pairs])
    return study.Context(T, roles, SEALED, study.CONFIG, state_path=WORK / "vault_state.json")


def real_proposer(ctx):
    """Bounded DeepSeek proposer: one logical request, at most four HTTP attempts, receipts without credentials."""
    import study
    import llm_arm
    T = ctx.T
    forbidden = list(T.drugs) + list(T.cells) + ["o'neil", "oneil", "almanac", "drugcomb", "figshare", "aacr", "jaaks", "prism", "l1000"]

    def run(summary, allowed, legal):
        try:
            from agent import llm
            settings = llm.MAESTROSettings.from_workspace(ROOT)
            client = llm.DeepSeekChatClient(settings)
        except Exception as error:  # missing configuration is an API-arm failure, never a blocker
            receipt = llm_arm.ApiReceipt(outcome="API_FAILURE", error=f"configuration: {type(error).__name__}")
            study.jdump(HERE / "API_RECEIPT.json", receipt.as_dict())
            return receipt.as_dict()
        with llm_arm.AttemptCounter(llm) as counter:
            receipt = llm_arm.propose(summary, allowed, legal, forbidden, client, attempts_used=0, count_attempts=counter)
        out = receipt.as_dict()
        out["provider_ledger"] = client.provider_usage
        out["limits"] = {"max_http_attempts": llm_arm.MAX_HTTP_ATTEMPTS, "max_logical_requests": llm_arm.MAX_LOGICAL_REQUESTS,
                         "max_output_tokens": llm_arm.MAX_OUTPUT_TOKENS, "max_input_tokens_conservative": llm_arm.MAX_INPUT_TOKENS}
        out["no_credentials_or_headers_persisted"] = True
        study.jdump(HERE / "API_RECEIPT.json", out)
        return out

    return run


def stage_freeze_real():
    import study
    if (HERE / "FREEZE.json").exists():
        print("freeze: FREEZE.json already exists; refusing to overwrite a frozen configuration")
        return
    ctx = real_context()
    freeze = study.stage_freeze(ctx, HERE, here=HERE)
    print("freeze ok:", freeze["design_label"], "margin", freeze["margin"], "panel", freeze["panel"]["n_pairs"])


def stage_challenge_real(use_api: bool = True):
    import study
    ctx = real_context()
    freeze = study.jload(HERE / "FREEZE.json")
    study.verify_freeze(ctx, HERE, freeze)
    proposer = real_proposer(ctx) if use_api and freeze["api_registration"]["include_api_arm"] else None
    trace = study.stage_challenge(ctx, HERE, freeze, proposer=proposer)
    print("challenge ok:", {k: v.get("candidate") for k, v in trace["arms"].items()})


def stage_retention_real():
    import study
    ctx = real_context()
    freeze = study.jload(HERE / "FREEZE.json")
    study.verify_freeze(ctx, HERE, freeze)
    res = study.stage_retention(ctx, HERE, freeze)
    print("retention ok:", {k: v["accepted"] for k, v in res["decisions"].items()})


def stage_final_real():
    import study
    ctx = real_context()
    freeze = study.jload(HERE / "FREEZE.json")
    study.verify_freeze(ctx, HERE, freeze)
    res = study.stage_final(ctx, HERE, freeze)
    print("final ok:", res["verdict"])


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else ""
    flags = sys.argv[2:]
    if stage == "qualify":
        stage_qualify(force="--force" in flags)
    elif stage == "freeze":
        stage_freeze_real()
    elif stage == "challenge":
        stage_challenge_real(use_api="--no-api" not in flags)
    elif stage == "retention":
        stage_retention_real()
    elif stage == "final":
        stage_final_real()
    elif stage == "all":
        stage_freeze_real()
        stage_challenge_real(use_api="--no-api" not in flags)
        stage_retention_real()
        stage_final_real()
    else:
        raise SystemExit(f"unknown stage {stage!r}")
