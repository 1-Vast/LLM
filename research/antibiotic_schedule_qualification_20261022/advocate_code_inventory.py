"""Verify and inventory already obtained public repo metadata; no blob fetches."""
import base64
import hashlib
import json
from collections import Counter
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/antibiotic_schedule_qualification/code_discovery"
SRC = OUT / "sources"
target = OUT / "INVENTORY.json"
if target.exists() or (OUT / "LIST_README.md").exists():
    raise FileExistsError("Refusing inventory overwrite")
readme = json.loads((SRC / "LIST_README.json").read_text(encoding="utf-8"))
tree = json.loads((SRC / "LIST_TREE.json").read_text(encoding="utf-8"))
body = base64.b64decode(readme["content"])
git_blob_sha = hashlib.sha1(b"blob " + str(len(body)).encode("ascii") + b"\0" + body).hexdigest()
assert git_blob_sha == readme["sha"]
assert len(body) == readme["size"]
readme_entry = next(item for item in tree["tree"] if item["path"] == "README.md")
assert readme_entry["sha"] == git_blob_sha
assert not tree["truncated"]
(OUT / "LIST_README.md").write_bytes(body)
text = body.decode("utf-8")
blobs = [item for item in tree["tree"] if item["type"] == "blob"]
files = [{key: item.get(key) for key in ("path", "type", "size", "sha")} for item in blobs]
interesting = [item for item in files if any(token in item["path"].lower() for token in (
    "supplementary", "growth_data", "curve_fitting", "synergy_results", "512 chip seq", "calculation", "colony analysis"))]
ledger = json.loads((SRC / "NETWORK.json").read_text(encoding="utf-8"))
result = {
    "repo": "https://github.com/Uchicago-TAY/LIST", "branch": "Code", "tree_sha": tree["sha"],
    "tree_truncated": tree["truncated"], "tree_entry_count": len(tree["tree"]), "blob_count": len(blobs),
    "readme_git_blob_sha": git_blob_sha, "readme_bytes": len(body), "readme_sha_verified": True,
    "extensions": dict(Counter(Path(item["path"]).suffix.lower() for item in blobs)),
    "readme_contains_exact_paper_doi": "10.1101/2025.10.30.684665" in text,
    "readme_contains_exact_paper_title": "Massively multiplexed microfluidics maps combinatorial and sequential antibiotic responses in 3D".casefold() in text.casefold(),
    "readme_dois": sorted(set(value.rstrip(".") for value in re.findall(r"10\.\d{4,9}/[A-Za-z0-9./_-]+", text))),
    "candidate_data_manifest_files_metadata_only": interesting,
    "all_file_metadata": files,
    "http_requests": len(ledger), "retained_complete_response_body_bytes": sum(x["retained_body_bytes"] for x in ledger),
    "all_responses_complete_under_budget": all(x["complete_under_budget"] for x in ledger),
    "outcome_data_or_image_contents_opened": False,
    "paper_code_exact_linkage_authenticated": False,
    "repo_to_zenodo_link_authenticated_from_readme": "10.5281/zenodo.18362221" in text,
}
target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in result.items() if k not in ("all_file_metadata", "candidate_data_manifest_files_metadata_only")}, ensure_ascii=False, indent=2))
