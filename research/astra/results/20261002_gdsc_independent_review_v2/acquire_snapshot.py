"""Restore the exact inspected PR snapshot into a new local directory."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
commit = "15fec7c53c5334ceca96832e8342ae2ebc1fde75"
subprocess.run(["git", "fetch", "origin", commit], check=True)
paths = subprocess.check_output(["git", "diff", "--name-only", "84da724", commit,
                                 "--", "research/astra"], text=True).splitlines()
paths = [name for name in paths if "gdsc" in name.lower()] + ["research/astra/__init__.py"]
args.out.mkdir(parents=True, exist_ok=False)
hashes = {}
for name in paths:
    content = subprocess.check_output(["git", "show", commit + ":" + name])
    target = args.out / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    hashes[name] = hashlib.sha256(content).hexdigest()
(args.out / "snapshot_manifest.json").write_text(json.dumps(
    {"commit": commit, "paths": hashes}, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"commit": commit, "snapshot": str(args.out), "files": len(hashes)}))
