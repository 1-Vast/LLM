"""Replay the LLM planner arms (named and anonymous) in every target line.

File summary
- Path: research/certified_discovery/llm_replay.py
- Purpose: live-API counterpart of replay.py for the black-box planner arms.
- Core points: one thread per line (calls are I/O bound; rounds within a line stay sequential);
  write-once output directory; spend ledger with a hard ceiling; every planner event (fallback,
  invalid selection, agreement with the world model, rationale) is kept with its campaign.
- Interfaces: `main` (python -m research.certified_discovery.llm_replay).
- Depends on: `agent`, `llm_agent`, `world`, `screens`, src `agent.llm`.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

from . import agent
from .llm_agent import LLMPlannerArm, SpendBook
from .screens import CACHE, ROOT, load_library, sha256
from .world import TransferWorld, WorldConfig

sys.path.insert(0, str(ROOT / "src"))
from agent.llm import DeepSeekChatClient, MAESTROSettings  # noqa: E402

SOURCES = ("screens.py", "world.py", "agent.py", "certify.py", "llm_agent.py", "llm_replay.py")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--library", default=str(CACHE / "oneil_v1.npz"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--modes", default="named,anonymous,blind")
    parser.add_argument("--lines", default="all")
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--ceiling", type=float, default=3.0, help="USD ceiling for this run")
    parser.add_argument("--spec", default="{}")
    args = parser.parse_args(argv)
    out = Path(args.out)
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}: records are write-once")
    out.mkdir(parents=True)
    lib = load_library(Path(args.library))
    spec = agent.CampaignSpec(**json.loads(args.spec))
    client = DeepSeekChatClient(MAESTROSettings.from_workspace(ROOT))
    book = SpendBook(out / "spend.json", args.ceiling)
    lines = range(len(lib.lines)) if args.lines == "all" else [int(x) for x in args.lines.split(",")]
    modes = args.modes.split(",")

    def one(task):
        line, mode = task
        world = TransferWorld(lib, line, WorldConfig())
        batch = int(math.ceil(math.ceil(spec.budget_fraction * world.rows.size) / spec.rounds))
        arm = LLMPlannerArm(world, client, book, batch=batch, mode=mode)
        return agent.run_campaign(lib, world, arm, spec, seed=line)

    started = time.time()
    tasks = [(line, mode) for mode in modes for line in lines]
    with ThreadPoolExecutor(max_workers=args.threads) as pool:
        records = list(pool.map(one, tasks))
    with open(out / "campaigns.jsonl", "w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, default=str) + "\n")
    here = Path(__file__).resolve().parent
    manifest = {"library": lib.name, "library_sha256": sha256(Path(args.library)), "spec": asdict(spec),
                "modes": modes, "lines": len(list(lines)), "records": len(records),
                "provider": client.settings.chat_model, "spend_usd": book.total, "calls": len(book.entries),
                "wall_seconds": round(time.time() - started, 1),
                "sources": {name: sha256(here / name) for name in SOURCES}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"records": len(records), "spend_usd": round(book.total, 4), "calls": len(book.entries),
                      "wall_seconds": manifest["wall_seconds"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
