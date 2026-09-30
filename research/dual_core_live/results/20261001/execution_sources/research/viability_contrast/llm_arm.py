"""LLM-agent arm for the viability-contrast task (registered phase-B arm, .env DeepSeek).

File summary
- Path: research/viability_contrast/llm_arm.py
- Purpose: a BioDiscoveryAgent-style baseline inside the same contract: DeepSeek chooses the
  next menu line from a textual card (candidate classes, readings so far, menu with tissue
  annotations), while the score-margin validator and the budget stay algorithmic. The margin
  tau of planner_reference is applied (registered as approximate transfer across policies).
  Determinism: temperature 0, fixed card format, every raw response logged.
- Interfaces / data: reads .env (DEEPSEEK_API_KEY/BASE_URL/MODEL); reads the frozen pack and
  run3's episodes.csv to skip completed episodes; writes
  outputs/viability_contrast_20260928/llm/{calls.jsonl, episodes.csv, summary.json}.
- Depends on: research/viability_contrast/{prepare.py, qualify2.py}, openai-compatible HTTP
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from . import prepare, qualify2

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/viability_contrast_20260928/llm"
KEY = "viability-contrast-3"
BUDGET = 16
EPISODE_LIMIT = 24


def load_env():
    env = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def chat(env, messages, log):
    req = urllib.request.Request(
        env["DEEPSEEK_BASE_URL"].rstrip("/") + "/chat/completions",
        data=json.dumps({
            "model": env["DEEPSEEK_MODEL"],
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 2000,
            "reasoning_effort": "none",
        }).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {env['DEEPSEEK_API_KEY']}"},
        method="POST",
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read())
    log.append({"latency_s": round(time.time() - t0, 2),
                "usage": body.get("usage"),
                "content": body["choices"][0]["message"]["content"]})
    return body["choices"][0]["message"]["content"]


CARD = """You are designing a viability experiment. A held-out compound was screened in a pooled viability assay; you may buy its 8-dose viability curve (readout: AUC, lower = stronger killing) in one cell line per step, at most {budget} curves, to identify its mechanism class among {n_classes} candidates.

Candidate classes:
{classes}

Cell-line menu (id: tissue):
{menu}

Rules: reply with exactly one line of the form `LINE: <depmap_id>` naming the cell line to measure next, choosing the line whose result would best separate the remaining candidate classes. No other text."""


def main():
    env = load_env()
    pack = prepare.load_pack()
    auc, compounds, lines = pack["auc"], pack["compounds"], pack["lines"]
    meta, folds, menu = pack["meta"], pack["folds"], pack["menu"]
    classes = menu["classes"]
    class_index = {c: i for i, c in enumerate(classes)}
    idx = pack["index"]
    line_index = pack["line_index"]
    labels = np.full(len(compounds), -1)
    for c in compounds:
        lab = meta.loc[c, "moa_main"]
        if lab in class_index:
            labels[idx[c]] = class_index[lab]
    pool = [line_index[l] for l in menu["pool_lines"] if l in line_index]
    pos_of_line = {lj: p for p, lj in enumerate(pool)}
    cl_info = pd.read_csv(ROOT / "data/raw/prism/secondary-screen-cell-line-info.csv")
    tissue = dict(zip(cl_info["depmap_id"], cl_info["primary_tissue"]))
    pool_arr = np.asarray(pool)
    world_fit = json.loads((ROOT / "outputs/viability_contrast_20260928/run3/world_fit.json").read_text(encoding="utf-8"))

    # deterministic episode subsample from folds 0 and 1
    eps = []
    for f in ("0", "1"):
        eps += [(f, c) for c in folds[f] if labels[idx[c]] >= 0]
    rng = np.random.default_rng(int(qualify2.sha(f"{KEY}|llm")[:16], 16))
    order = rng.permutation(len(eps))
    eps = [eps[i] for i in sorted(order[:EPISODE_LIMIT])]

    OUT.mkdir(parents=True, exist_ok=True)
    done = set()
    if (OUT / "episodes.csv").exists():
        done = set(pd.read_csv(OUT / "episodes.csv")["compound"])
    rows = []
    log_path = OUT / "calls.jsonl"
    log_fh = open(log_path, "a", encoding="utf-8")
    menu_text = "; ".join(f"{lines[l]}: {tissue.get(lines[l], '?')}" for l in pool)
    for f, c in eps:
        if c in done:
            continue
        tau = world_fit[f]["tau"]["planner_reference"]
        exploratory = tau is None
        if exploratory:
            tau = float("inf")  # never crosses; forced argmax at budget end below
        x = idx[c]
        truth = labels[x]
        heldout_set = set(folds[f])
        train = [t for t in compounds if t not in heldout_set and labels[idx[t]] >= 0]
        med, scale, valid, med_p, scale_p = qualify2.build_templates_v2(
            auc, [[idx[t] for t in train if labels[idx[t]] == ci] for ci in range(len(classes))])
        val_m = np.where(valid, med, med_p[None, :])[:, pool_arr]
        val_s = np.where(valid, scale, scale_p[None, :])[:, pool_arr]
        scores = np.zeros(len(classes))
        traj = []
        history = []
        purchased = set()
        for step in range(BUDGET):
            card = CARD.format(budget=BUDGET, n_classes=len(classes),
                               classes="\n".join(classes), menu=menu_text)
            if history:
                card += "\n\nReadings so far:\n" + "\n".join(history)
            calls = []
            try:
                reply = chat(env, [{"role": "user", "content": card}], calls)
            except Exception as e:  # noqa: BLE001
                reply = f"ERROR: {e}"
            for call in calls:
                call.update({"compound": c, "step": step})
                log_fh.write(json.dumps(call) + "\n")
                log_fh.flush()
            line_id = None
            for tok in str(reply).replace("`", "").split():
                if tok.startswith("ACH-"):
                    line_id = tok.strip(".,;")
                    break
            measurements = step + 1
            lj = pos_of_line.get(line_id) if line_id else None
            if lj is None or lj in purchased:
                history.append(f"step {measurements}: invalid or repeated choice ({line_id}); charged, no reading")
                top = int(np.argmax(scores))
                rest = np.delete(scores, top)
                traj.append((float(scores[top] - rest.max()), top, measurements, True))
                continue
            purchased.add(lj)
            a = auc[x, pool_arr[lj]]
            if not np.isfinite(a):
                history.append(f"step {measurements}: {line_id} -> QC failure (no curve)")
                top = int(np.argmax(scores))
                rest = np.delete(scores, top)
                traj.append((float(scores[top] - rest.max()), top, measurements, True))
                continue
            z = (a - val_m[:, lj]) / val_s[:, lj]
            t = -0.5 * np.minimum(z * z, 9.0) - np.log(val_s[:, lj]) - qualify2.LOG_SQRT_2PI
            scores = scores + t
            top = int(np.argmax(scores))
            rest = np.delete(scores, top)
            traj.append((float(scores[top] - rest.max()), top, measurements, False))
            history.append(f"step {measurements}: {line_id} AUC={a:.3f}")
        if exploratory and traj:
            top = traj[-1][1]
            out = {"decided": True, "correct": bool(top == truth),
                   "measurements": traj[-1][2],
                   "qc_failures": int(sum(1 for _, _, _, q in traj if q)),
                   "reason": "forced_argmax_exploratory"}
        else:
            out = qualify2.outcome_at_tau(traj, truth, tau)
        rows.append({"fold": f, "compound": c, "unit": str(meta.loc[c, "unit"]),
                     "class": classes[truth], "arm": "llm_agent", "tau": tau,
                     "exploratory_forced_argmax": exploratory, **out})
        pd.DataFrame(rows).to_csv(OUT / "episodes.csv", index=False)
    log_fh.close()
    if rows:
        df = pd.DataFrame(rows)
        summary = {
            "episodes": len(df),
            "correct": float(df["correct"].mean()),
            "coverage": float(df["decided"].mean()),
            "conditional_wrong": float((~df.loc[df["decided"].astype(bool), "correct"]).mean())
            if df["decided"].any() else None,
            "measurements": float(df["measurements"].mean()),
            "mode": "exploratory forced argmax (planner_reference tau is +inf: the registered "
                    "tau-gated arm is blocked by the same floor finding as every realistic arm)",
        }
        (OUT / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
        print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
