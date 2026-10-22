"""Conservatively suppress every numeric literal before source-code review."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/efaecalis_dynamic_qualification/code_io"
target = OUT / "MDP_NUMERIC_REDACTED.txt"
if target.exists():
    raise FileExistsError("Refusing projection overwrite")
source = (OUT / "MDP.source").read_text(encoding="utf-8")
pattern = re.compile(r"(?<![A-Za-z_])[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?(?:f32|f64|u\d+|i\d+|usize|isize)?(?![A-Za-z_])")
redacted, count = pattern.subn("<NUM>", source)
numbered = "\n".join(f"{i:04d}: {line}" for i, line in enumerate(redacted.splitlines(), 1))
target.write_text(numbered, encoding="utf-8")
(OUT / "MDP_PROJECTION.json").write_text(json.dumps({
    "numeric_literals_redacted": count, "all_numeric_literals_conservatively_masked": True,
    "raw_source_executed": False, "data_files_opened": False,
    "functions": re.findall(r"\bfn\s+([A-Za-z_][A-Za-z_0-9]*)", redacted)
}, indent=2), encoding="utf-8")
print(numbered)
