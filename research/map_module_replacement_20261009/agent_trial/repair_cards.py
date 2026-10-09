"""Pre-response API schema repair, preserving original source acquisition files."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "outputs/map_module_replacement_20261009/agent_trial"
source = OUT / "SOURCES.json"
target = OUT / "SOURCES.v3.json"
if target.exists():
    raise FileExistsError(target)
data = json.loads(source.read_text(encoding="utf-8"))
for case in data["cases"]:
    for card in case["cards"]:
        record = card.get("target_record") or {}
        card["target_gene_symbols"] = sorted({s["component_synonym"] for c in record.get("target_components", []) for s in c.get("target_component_synonyms", []) if s.get("syn_type") == "GENE_SYMBOL"})
data["derivation"] = {"from_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "reason": "Exact ChEMBL_37 target_component_synonyms key repair; no new or changed raw sources/cases."}
target.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
manifest = {"utc": datetime.now(timezone.utc).isoformat(), "phase": "schema_repair_before_reference_and_LLMresponses", "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "repaired_sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "repair_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(OUT / "SOURCE_REPAIR_FREEZE.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"repaired_cases": len(data["cases"]), "cards_with_gene_symbols": sum(bool(c["target_gene_symbols"]) for s in data["cases"] for c in s["cards"])}))
