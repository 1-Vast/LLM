"""The single registered confirmatory run on NCI-ALMANAC: vault, library, replays, verdicts.

File summary
- Path: research/certified_discovery/confirm.py
- Purpose: execute protocol/confirmatory.json exactly once, in order, with timestamps, so the
  confirmatory evidence is one auditable procedure rather than a sequence of manual commands.
- Core points: refuses an existing output directory or an existing confirmatory library cache;
  opens the vault (which refuses a changed freeze); builds the library; runs the non-LLM replay
  and the LLM replay with the registered spec, modes and spend ceiling; writes the registered
  verdicts. Every step's start, end and outcome go to run_log.json, including a failure.
- Interfaces: `main` (python -m research.certified_discovery.confirm).
- Depends on: `screens`, `replay`, `llm_replay`, `verdict`, `analysis`.
"""
from __future__ import annotations

import argparse
import json
import time
import traceback
from pathlib import Path

import numpy as np

from . import analysis, llm_replay, replay, screens, verdict

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "protocol/confirmatory.json"
FREEZE = HERE / "protocol/freeze.json"
VAULT_LOG = HERE / "protocol/vault_log.jsonl"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(HERE / "results/confirm_almanac_20261003"))
    args = parser.parse_args(argv)
    out = Path(args.out)
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    cache = screens.CACHE / protocol["library_cache"]
    if out.exists():
        raise SystemExit(f"refusing: {out} exists (the confirmatory run is write-once)")
    if cache.exists():
        raise SystemExit(f"refusing: {cache} exists; the confirmatory library must be built by this run")
    out.mkdir(parents=True)
    log: list[dict] = []

    def step(name, function):
        entry = {"step": name, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        log.append(entry)
        try:
            result = function()
            entry["status"] = "done"
            return result
        except BaseException as error:
            entry.update({"status": "failed", "error": repr(error), "trace": traceback.format_exc()[-2000:]})
            raise
        finally:
            entry["ended"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            (out / "run_log.json").write_text(json.dumps(log, indent=1), encoding="utf-8")

    ticket = step("open_vault", lambda: screens.open_vault(FREEZE, VAULT_LOG, purpose="confirmatory run"))
    library = step("build_library", lambda: screens.build_almanac(ticket, cache))
    hits = library.hits
    description = {"experiments": len(library), "drugs": len(library.drugs), "lines": len(library.lines),
                   "hits": int(hits.sum()), "hit_rate": float(hits.mean()),
                   "label_quantiles": np.percentile(library.y, [1, 5, 25, 50, 75, 95, 99]).round(3).tolist(),
                   "line_hit_rate_range": [float(min(hits[library.c == l].mean() for l in range(len(library.lines)))),
                                           float(max(hits[library.c == l].mean() for l in range(len(library.lines))))],
                   "provenance": library.provenance}
    (out / "library.json").write_text(json.dumps(description, indent=1, default=str), encoding="utf-8")
    spec = json.dumps(protocol["spec"])
    step("replay", lambda: replay.main(["--library", str(cache), "--out", str(out / "replay"), "--spec", spec,
                                        "--workers", str(protocol["workers"])]))
    step("llm_replay", lambda: llm_replay.main(["--library", str(cache), "--out", str(out / "llm"), "--spec", spec,
                                                "--modes", ",".join(protocol["llm_modes"]),
                                                "--ceiling", str(protocol["llm_ceiling_usd"]),
                                                "--threads", str(protocol["llm_threads"])]))
    for part in ("replay", "llm"):
        step(f"summary_{part}", lambda part=part: analysis.main([str(out / part)]))
    step("verdict", lambda: verdict.main([str(out / "replay"), str(out / "llm"), "--alpha", str(protocol["spec"]["alpha"]),
                                          "--delta", str(protocol["spec"]["delta"]), "--out", str(out / "verdict.json")]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
