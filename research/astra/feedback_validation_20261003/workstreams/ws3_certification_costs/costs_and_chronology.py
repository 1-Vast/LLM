"""WS3 provider-spend, baseline-acquisition and chronology receipts (read-only over frozen evidence).

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws3_certification_costs/costs_and_chronology.py
- Purpose:
  1. recompute provider spend from every spend.json (and the unreported scratchpad smoke run),
     at the SpendBook rates and at the provider's published off-peak rates, and list calls that
     were never priced;
  2. count the single-agent records each target line's context consumes (never charged);
  3. assemble the chronology from file mtimes, manifests, run_log, vault log, freeze and the
     Claude Code session transcript (tool-call timestamps only), and recheck every freeze digest.
- Core points: nothing in research/certified_discovery is written; ALMANAC is read through
  design columns only (no outcome column) for the baseline count.
- Run: D:/anaconda/envs/maestro/python.exe research/astra/feedback_validation_20261003/workstreams/ws3_certification_costs/costs_and_chronology.py
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
FROZEN = ROOT / "research/certified_discovery"
RESULTS = FROZEN / "results"
SESSION = "b680d5ba-1c34-4a32-9272-ad9ea4067249"
TRANSCRIPT = Path.home() / ".claude/projects/D--MAESTRO" / f"{SESSION}.jsonl"
SCRATCH_SMOKE = Path.home() / f"AppData/Local/Temp/claude/D--MAESTRO/{SESSION}/scratchpad/llm_smoke/spend.json"
SPENDBOOK = {"input_cache_miss": 0.30, "input_cache_hit": 0.006, "output": 1.20}
# api-docs.deepseek.com/quick_start/pricing, fetched 2026-10-03 ~20:00 +0800: deepseek-flash
# (DeepSeek-V4.1-Flash) peak 0.006 / 0.3 / 1.2, off-peak half; peak = 01-04 and 06-10 UTC,
# Monday-Friday, excluding Chinese public holidays. 2026-10-03 is a Saturday inside the
# 1-7 October National Day holiday, so every call that day falls in the off-peak schedule.
PUBLISHED_OFFPEAK = {k: v / 2 for k, v in SPENDBOOK.items()}
TZ = dt.timezone(dt.timedelta(hours=8))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mtime(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime, TZ).isoformat(timespec="milliseconds")


def price(entry: dict, rates: dict) -> float:
    hit = entry["cache_hit_tokens"]
    miss = max(entry["prompt_tokens"] - hit, 0)
    return (miss * rates["input_cache_miss"] + hit * rates["input_cache_hit"] + entry["completion_tokens"] * rates["output"]) / 1e6


def spend_audit() -> dict:
    out = {}
    sources = {"dev_llm_v1_INVALID": RESULTS / "dev_llm_20261003_v1",
               "dev_llm_v2": RESULTS / "dev_llm_20261003_v2",
               "confirm_llm": RESULTS / "confirm_almanac_20261003/llm"}
    for label, run in sources.items():
        book = json.loads((run / "spend.json").read_text(encoding="utf-8"))
        entries = book["entries"]
        recs = [json.loads(l) for l in open(run / "campaigns.jsonl", encoding="utf-8")]
        events = [e for r in recs for e in (r["planner_events"] or [])]
        unpriced = [e for e in events if e.get("code") == "LLM_UNAVAILABLE"]
        by_mode = defaultdict(float)
        for e in entries:
            by_mode[e["label"].split(":")[0]] += e["usd"]
        prompt = np.array([e["prompt_tokens"] for e in entries])
        upper_unpriced = len(unpriced) * (np.percentile(prompt, 95) * SPENDBOOK["input_cache_miss"] + 3000 * SPENDBOOK["output"]) / 1e6
        out[label] = {
            "recorded_total_usd": book["total_usd"], "recorded_calls": book["calls"], "rates_in_file": book["rates"],
            "recomputed_at_spendbook_rates": float(sum(price(e, SPENDBOOK) for e in entries)),
            "recomputed_at_published_offpeak": float(sum(price(e, PUBLISHED_OFFPEAK) for e in entries)),
            "prompt_tokens": int(prompt.sum()), "cache_hit_tokens": int(sum(e["cache_hit_tokens"] for e in entries)),
            "completion_tokens": int(sum(e["completion_tokens"] for e in entries)),
            "api_seconds_sum": float(sum(e["seconds"] for e in entries)),
            "usd_by_mode": dict(by_mode), "planner_events": len(events),
            "unpriced_LLM_UNAVAILABLE_calls": len(unpriced),
            "unpriced_upper_estimate_usd_at_spendbook_rates": float(upper_unpriced),
            "spend_json_mtime": mtime(run / "spend.json"),
            "note": "spend.json has no per-call timestamps; transport retries inside src/agent/llm.py are not ledgered",
        }
    if SCRATCH_SMOKE.is_file():
        book = json.loads(SCRATCH_SMOKE.read_text(encoding="utf-8"))
        out["scratchpad_llm_smoke_UNREPORTED"] = {
            "path": str(SCRATCH_SMOKE), "recorded_total_usd": book["total_usd"], "calls": book["calls"],
            "recomputed_at_published_offpeak": float(sum(price(e, PUBLISHED_OFFPEAK) for e in book["entries"])),
            "spend_json_mtime": mtime(SCRATCH_SMOKE),
            "note": "real API calls (lines 0,5; launched 17:46:45) not included in the README's development spend",
        }
    recorded = sum(v["recorded_total_usd"] for v in out.values())
    out["total_recorded_usd_all_ledgers"] = float(recorded)
    out["total_offpeak_usd_all_ledgers"] = float(sum(v.get("recomputed_at_published_offpeak", 0.0) for v in out.values() if isinstance(v, dict)))
    out["pricing_source"] = "https://api-docs.deepseek.com/quick_start/pricing (fetched 2026-10-03); billed amount unknown without the provider invoice"
    return out


def baseline_acquisition() -> dict:
    """Single-agent measurements of the target line used as context before any purchase."""
    import pandas as pd

    from research.certified_discovery import screens
    from research.certified_discovery.xlsx import iter_rows

    out = {}
    with zipfile.ZipFile(screens.ALMANAC_ZIP) as archive, archive.open("ComboDrugGrowth_Nov2017.csv") as handle:
        frame = pd.read_csv(handle, usecols=["NSC1", "NSC2", "CONCINDEX1", "CONCINDEX2", "CELLNAME", "PLATE"],
                            dtype={"NSC1": "Int64", "NSC2": "Int64", "CELLNAME": "string"}, low_memory=False)
    frame["CELLNAME"] = frame["CELLNAME"].str.strip()
    alone = (frame["CONCINDEX1"] > 0) & ~(frame["CONCINDEX2"] > 0) & frame["NSC2"].isna()
    single = frame[alone]
    per_line = single.groupby("CELLNAME").size()
    plates = single.groupby("CELLNAME")["PLATE"].nunique()
    combo = frame[(frame["CONCINDEX1"] > 0) & (frame["CONCINDEX2"] > 0) & frame["NSC2"].notna()]
    out["almanac"] = {
        "single_agent_records_per_line_mean": float(per_line.mean()), "range": [int(per_line.min()), int(per_line.max())],
        "plates_contributing_single_records_per_line_mean": float(plates.mean()),
        "combination_records_per_line_mean": float(combo.groupby("CELLNAME").size().mean()),
        "note": "columns read: NSC1, NSC2, CONCINDEX1, CONCINDEX2, CELLNAME, PLATE (no outcome column)",
    }
    rows = iter_rows(screens.ONEIL_SINGLE)
    header = next(rows)
    col = {name: header.index(name) for name in ("BatchID", "cell_line", "drug_name", "X/X0")}
    counts = Counter()
    for row in rows:
        if row and row[col["X/X0"]] not in (None, "") and str(row[col["BatchID"]]) == "1":
            counts[row[col["cell_line"]]] += 1
    out["oneil"] = {"single_agent_rows_batch1_per_line_mean": float(np.mean(list(counts.values()))),
                    "lines": len(counts), "range": [min(counts.values()), max(counts.values())]}
    return out


def transcript_events() -> list[dict]:
    if not TRANSCRIPT.is_file():
        return [{"missing": str(TRANSCRIPT)}]
    patterns = {
        "dev_llm_v1 launched": r"llm_replay --out \$R/dev_llm_20261003_v1",
        "dev_llm_v2 launched": r"llm_replay --out \$R/dev_llm_20261003_v2",
        "scratch llm_smoke launched": r"llm_replay --out \$S/llm_smoke",
        "llm_agent.py mode patch": r"research/certified_discovery/llm_agent\.py",
        "INVALID.md written": r"INVALID\.md\", \"content\"",
        "ALMANAC design census": r"almanac_design\(\)",
        "mentions freeze.json": r"freeze\.json",
        "mentions confirm module": r"research\.certified_discovery\.confirm",
        "edits day log": r"log/20261003/README\.md",
    }
    found = []
    for line in open(TRANSCRIPT, encoding="utf-8"):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = event.get("timestamp", "")
        if ts > "2026-10-03T10:40:00":
            break
        message = event.get("message") or {}
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        for c in content:
            if c.get("type") != "tool_use":
                continue
            text = json.dumps(c.get("input"))
            for label, pattern in patterns.items():
                if re.search(pattern, text):
                    local = dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(TZ).isoformat(timespec="seconds")
                    found.append({"utc": ts, "local": local, "tool": c.get("name"), "event": label,
                                  "description": (c.get("input") or {}).get("description", "")})
    return found


def chronology() -> dict:
    files = {
        "dev_plan.json": FROZEN / "protocol/dev_plan.json",
        "dev_v1 campaigns": RESULTS / "dev_20261003_v1/campaigns.jsonl",
        "dev_v2 campaigns": RESULTS / "dev_20261003_v2/campaigns.jsonl",
        "dev_llm_v1 spend.json (last call)": RESULTS / "dev_llm_20261003_v1/spend.json",
        "dev_llm_v1 INVALID.md": RESULTS / "dev_llm_20261003_v1/INVALID.md",
        "llm_agent.py (frozen version)": FROZEN / "llm_agent.py",
        "dev_llm_v2 spend.json (last call)": RESULTS / "dev_llm_20261003_v2/spend.json",
        "verdict_dev.json": RESULTS / "dev_20261003_v2/verdict_dev.json",
        "DESIGN.md": FROZEN / "DESIGN.md", "screens.py": FROZEN / "screens.py", "confirm.py": FROZEN / "confirm.py",
        "analysis.py": FROZEN / "analysis.py", "confirmatory.json": FROZEN / "protocol/confirmatory.json",
        "freeze.json": FROZEN / "protocol/freeze.json", "vault_log.jsonl": FROZEN / "protocol/vault_log.jsonl",
        "almanac_v1.npz (first outcome read)": ROOT / "data/processed/certified_discovery/almanac_v1.npz",
        "confirm replay campaigns": RESULTS / "confirm_almanac_20261003/replay/campaigns.jsonl",
        "src/maestro/certification.py (promoted)": ROOT / "src/maestro/certification.py",
        "promoted parity manifest": RESULTS / "promoted_parity_almanac_20261003/manifest.json",
        "confirm llm spend.json (last call)": RESULTS / "confirm_almanac_20261003/llm/spend.json",
        "confirm verdict.json": RESULTS / "confirm_almanac_20261003/verdict.json",
        "README.md (report)": FROZEN / "README.md", "log/20261003/README.md": ROOT / "log/20261003/README.md",
        "ALMANAC zip download": ROOT / "data/external/nci_almanac_2017/ComboDrugGrowth_Nov2017.zip",
        "oneil_v1_reproducibility.json": ROOT / "data/processed/certified_discovery/oneil_v1_reproducibility.json",
    }
    mt = {k: mtime(p) for k, p in files.items() if p.exists()}
    manifests = {}
    for run in ("dev_20261003_v1", "dev_20261003_v2", "dev_llm_20261003_v1", "dev_llm_20261003_v2",
                "confirm_almanac_20261003/replay", "confirm_almanac_20261003/llm"):
        m = json.loads((RESULTS / run / "manifest.json").read_text(encoding="utf-8"))
        end = (RESULTS / run / "manifest.json").stat().st_mtime
        manifests[run] = {"wall_seconds": m.get("wall_seconds"),
                          "approx_start": dt.datetime.fromtimestamp(end - (m.get("wall_seconds") or 0), TZ).isoformat(timespec="seconds"),
                          "llm_agent.py": m.get("sources", {}).get("llm_agent.py"), "agent.py": m["sources"].get("agent.py"),
                          "screens.py": m["sources"].get("screens.py")}
    freeze = json.loads((FROZEN / "protocol/freeze.json").read_text(encoding="utf-8"))
    recheck = {name: ("OK" if sha(ROOT / name) == digest else "MISMATCH:" + sha(ROOT / name)) for name, digest in freeze["files"].items()}
    vault = [json.loads(l) for l in (FROZEN / "protocol/vault_log.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    return {
        "mtimes": dict(sorted(mt.items(), key=lambda kv: kv[1])), "manifests": manifests,
        "run_log": json.loads((RESULTS / "confirm_almanac_20261003/run_log.json").read_text(encoding="utf-8")),
        "vault_log": vault, "freeze_frozen_at": freeze["frozen_at"], "freeze_invalid_runs": freeze["invalid_runs"],
        "freeze_sha256_now": sha(FROZEN / "protocol/freeze.json"),
        "freeze_digest_recheck": recheck, "freeze_mismatches": [k for k, v in recheck.items() if v != "OK"],
        "not_covered_by_freeze": ["results/ (all receipts, INVALID.md)", "README.md", "data caches", "log/20261003/README.md"],
        "INVALID_md_sha256_now": sha(RESULTS / "dev_llm_20261003_v1/INVALID.md"),
        "transcript": {"path": str(TRANSCRIPT), "events": transcript_events()},
    }


def main() -> int:
    result = {"spend": spend_audit()}
    print(json.dumps({k: (v.get("recorded_total_usd"), v.get("recomputed_at_published_offpeak"), v.get("unpriced_LLM_UNAVAILABLE_calls"))
                      for k, v in result["spend"].items() if isinstance(v, dict)}, indent=1))
    result["baseline_acquisition"] = baseline_acquisition()
    print(json.dumps(result["baseline_acquisition"], indent=1))
    result["chronology"] = chronology()
    (HERE / "costs_and_chronology.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    c = result["chronology"]
    print("freeze mismatches:", c["freeze_mismatches"], "freeze sha now:", c["freeze_sha256_now"])
    for k, v in c["mtimes"].items():
        print(v, k)
    for e in c["transcript"]["events"]:
        print(e.get("local"), e.get("event"), "|", e.get("description"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
