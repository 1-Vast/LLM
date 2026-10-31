"""Decode a GitHub notebook blob and admit source cells only, never outputs."""
import argparse
import base64
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("blob", type=Path)
parser.add_argument("prefix")
args = parser.parse_args()
blob = json.loads(args.blob.read_text(encoding="utf-8"))
raw = base64.b64decode(blob["content"])
notebook = json.loads(raw)
episode = Path(__file__).resolve().parent
args.blob.with_name(args.prefix + ".ipynb").write_bytes(raw)
source = []
for number, cell in enumerate(notebook["cells"], 1):
    code = "".join(cell.get("source", []))
    source.append(f"\nCELL {number} ({cell.get('cell_type')})\n{code}\n")
output = episode / (args.prefix + "_source_only.txt")
output.write_text("".join(source), encoding="utf-8")
print(output)
print("".join(source))
