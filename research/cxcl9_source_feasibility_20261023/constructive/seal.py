"""Seal independent opinion, result, code and explicitly read inputs."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
role = root / "log/20261023/cxcl9_source_feasibility/constructive"
source = root / "log/20261023/cxcl9_source_feasibility/source"
paths = [p for p in role.iterdir() if p.is_file() and p.name != "FIRST_SEAL.json"]
paths += list(Path(__file__).parent.glob("*.py"))
paths += [root / "log/20261023/action_rule_search/DECISION.md"]
paths += [source / name for name in [
    "README.md", "01_mechanistic_model/01_preparing_inputs.R",
    "01_mechanistic_model/utils.R", "02_active_learning/optimization.R",
    "02_active_learning/utils.R", "data/cxcl9_assay/metadata.md",
    "data/cxcl9_assay_active_learning/metadata.md",
    "data/model_inputs_active_learning/AsPC1/metadata.md",
]]
files = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
         for p in sorted(paths)}
payload = {"stage": "independent pre-peer opinion", "files": files,
           "numeric_biological_payload_read": False,
           "new_source_gets": 0, "api_calls": 0,
           "native_model_token_money_attested": False}
target = role / "FIRST_SEAL.json"
if target.exists():
    raise SystemExit("Preserving existing first seal")
target.write_text(json.dumps(payload, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"files": len(files), "seal": str(target)}))
