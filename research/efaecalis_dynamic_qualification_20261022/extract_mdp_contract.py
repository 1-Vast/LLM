"""Extract method-only constants and path contracts; never execute author code."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/efaecalis_dynamic_qualification/code_io"
target = OUT / "MDP_IO_CONTRACT.json"
if target.exists():
    raise FileExistsError("Refusing contract overwrite")
source = (OUT / "MDP.source").read_text(encoding="utf-8")
tree = json.loads((OUT / "TREE_MANIFEST.json").read_text(encoding="utf-8"))
paths = {item["path"] for item in tree["tree"]}
inputs = re.findall(r'read_csv\("([^\"]+)"\)', source)
lines = source.splitlines()
# These are scalar algorithm configuration, row indexing, parser/discretization
# and state-update statements, not biological response observations or arrays.
method_line_numbers = list(range(17, 21)) + [43, 75, 104, 133, 195] + list(range(209, 221)) + list(range(229, 237))
contract = {
    "full_tree_sha": tree["full_tree_sha"], "tree_truncated": tree["truncated"],
    "tree_entry_count": len(tree["tree"]),
    "csv_inputs": [{"path": path, "present_in_tree": path in paths} for path in inputs],
    "file_outputs": re.findall(r'File::create\("([^\"]+)"\)', source),
    "method_constants_and_statements_only": [{"line": i, "code": lines[i - 1]}
        for i in method_line_numbers],
    "response_array_values_projected": False, "author_source_executed": False,
    "data_file_bytes_read": 0,
}
target.write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(contract, ensure_ascii=False, indent=2))
