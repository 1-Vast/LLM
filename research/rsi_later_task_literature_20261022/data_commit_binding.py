"""Bind already captured author files to one Git tree without further network access."""
import hashlib
import json
from pathlib import Path


OUT = Path(__file__).resolve().parents[2] / "log/20261022/rsi_later_task_literature/data"
target = OUT / "CELLSCIENTIST_COMMIT_BINDING.json"
if target.exists():
    raise RuntimeError("Commit binding already exists")
tree = {x["path"]: x for x in json.loads((OUT / "cellscientist_fixed_tree.body").read_text())["tree"]}
mapping = {"README.md": "cellscientist_readme.body", "data/README.md": "cellscientist_data_schema.body",
           "data/release_manifest.json": "cellscientist_manifest.body", "cellscientist/controllers.py": "cellscientist_fixed_controller.body",
           "configs/bbbc036_047_formal.json": "cellscientist_fixed_config.body"}
checks, hashes = {}, {}
for path, file in mapping.items():
    body = (OUT / file).read_bytes()
    digest = hashlib.sha1(b"blob " + str(len(body)).encode() + b"\0" + body).hexdigest()
    checks[path] = digest == tree[path]["sha"]
    hashes[path] = {"git_blob_sha1": digest, "body_sha256": hashlib.sha256(body).hexdigest()}
result = {"source_commit": "e27a5941378e8259cbeca7d336a26f52a09f7cc4", "checks": checks, "all_pass": all(checks.values()),
          "files": hashes, "paper_v1_implementation_equivalence_claimed": False}
target.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({"source_commit": result["source_commit"], "all_pass": result["all_pass"], "files": len(checks)}))
