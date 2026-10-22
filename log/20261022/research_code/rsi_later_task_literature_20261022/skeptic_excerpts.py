"""Evidence projections for the six-source skeptical review."""
import json
from pathlib import Path
import re
import sys

BASE = Path(__file__).resolve().parents[2] / "log/20261022/rsi_later_task_literature/skeptic"
stem, pattern = sys.argv[1:3]
source = json.loads((BASE / (stem + ".projection.json")).read_text(encoding="utf-8"))
selected = [{"projection_index": i, **p} for i, p in enumerate(source["paragraphs"])
            if re.search(pattern, p["text"], re.I)]
suffix = re.sub(r"[^a-z0-9]+", "_", pattern.lower())[:45]
(BASE / (stem + ".excerpts_" + suffix + ".json")).write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf-8")
for p in selected:
    print(f'{p["projection_index"]} [{p["tag"]} {p["id"]}] {p["text"]}')
