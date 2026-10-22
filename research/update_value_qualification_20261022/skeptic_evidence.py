"""Save exact bounded excerpts and local source bindings; no numerical fitting."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/update_value_qualification/skeptic"
SPECS = {
    "reliable_algorithm_selection": ["density ratios", "guarantee", "multiple hypothesis", "estimated", "held-out", "success criterion", "assumption", "limitation"],
    "decision_focused_design": ["directional uncertainty", "optimality gap", "assumption", "importance weight", "real-world", "stopping time", "finite", "label"],
}
entries = []
for name, terms in SPECS.items():
    parts = json.loads((OUT / f"{name}.projection.json").read_text(encoding="utf-8"))
    excerpts = {term: [{"fragment": i, "text": p} for i, p in enumerate(parts)
                       if term in p.lower() and len(p) > 65][:8] for term in terms}
    (OUT / f"{name}.excerpts.json").write_text(json.dumps(excerpts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    entries.append({"name": name, "evidence_level": "full primary HTML body; targeted method/assumption review",
                    "receipt": f"{name}.receipt.json", "sha256": hashlib.sha256((OUT / f"{name}.body").read_bytes()).hexdigest()})
old = ROOT / "log/20261022/rsi_later_task_literature/skeptic/skeptic_learned_optimizer.body"
entries.append({"name": "learned_gradient_history_optimizer", "url": "https://arxiv.org/html/2610.09604v1",
                "evidence_level": "existing captured full primary body; previously independently reviewed",
                "path": str(old.relative_to(ROOT)), "sha256": hashlib.sha256(old.read_bytes()).hexdigest()})
metadata = []
for name in ("predecessor_discovery", "algorithm_context_discovery"):
    metadata.extend(json.loads((OUT / f"{name}.projection.json").read_text(encoding="utf-8")))
ids = ("1111.2249v1", "1901.08159v1", "2205.13881v1", "2104.09460v2")
selected = [x for x in metadata if any(x["id"].endswith(k) for k in ids)]
(OUT / "ABSTRACT_LEVEL_PREDECESSORS.json").write_text(json.dumps(selected, indent=2) + "\n", encoding="utf-8")
entries.extend({"name": x["title"], "url": x["id"], "evidence_level": "primary arXiv Atom identity and abstract only; not full-text verified"} for x in selected)
for name in ("predecessor_discovery", "algorithm_context_discovery"):
    entries.append({"name": name, "evidence_level": "primary metadata discovery; irrelevant hits not reviewed",
                    "receipt": f"{name}.receipt.json", "sha256": hashlib.sha256((OUT / f"{name}.body").read_bytes()).hexdigest()})
(OUT / "SOURCE_MANIFEST.json").write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"sources": len(entries), "new_GETs": 4, "new_full_primary_bodies": 2}))
