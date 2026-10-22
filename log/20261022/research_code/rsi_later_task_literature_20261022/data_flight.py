"""Decode captured Next.js text payloads as JSON, never execute website scripts."""
import json
from pathlib import Path
import re
import sys


OUT = Path(__file__).resolve().parents[2] / "log/20261022/rsi_later_task_literature/data"
name = sys.argv[1]
target = OUT / (name + ".flight.txt")
if target.exists():
    raise RuntimeError("Derived flight text already exists")
raw = (OUT / (name + ".body")).read_text(encoding="utf-8")
parts = []
for match in re.finditer(r"self\.__next_f\.push\((.*?)\)</script>", raw, re.DOTALL):
    value = json.loads(match.group(1))
    if len(value) > 1 and isinstance(value[1], str):
        for token in re.findall(r'"(?:[^"\\]|\\.)*"', value[1]):
            text = json.loads(token, strict=False)
            if len(text) >= 25 and not text.startswith(("static/", "data:", "Container_")):
                parts.append(text)
target.write_text("\n".join(dict.fromkeys(parts)), encoding="utf-8")
print(target)
