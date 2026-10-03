"""Check this convergence's moved responsibilities and byte-preserved historical evidence."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess


BASE = "3b7935f73f2cf1eb88e64e64cc767039546b36f9"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source(root, revision, path):
    return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=root).decode("utf-8")


def functions(text, owner=None):
    tree = ast.parse(text)
    body = next(node.body for node in tree.body if isinstance(node, ast.ClassDef) and node.name == owner) if owner else tree.body
    return {node.name: node for node in body if isinstance(node, ast.FunctionDef)}


class PredictionNames(ast.NodeTransformer):
    names = {"_virtual_cell": "backend", "_prediction_cache": "cache", "_max_parallel_predictions": "max_parallel_predictions",
             "_query_world_model": "query", "_predict_many": "predict_many", "_backend_name": "backend_name", "_predict_virtual_cell": "predict"}

    def visit_FunctionDef(self, node):
        node.name = self.names.get(node.name, node.name)
        return self.generic_visit(node)

    def visit_Attribute(self, node):
        node.attr = self.names.get(node.attr, node.attr)
        return self.generic_visit(node)


def audit(root):
    original = functions(source(root, BASE, "src/agent/orchestrator.py"), "MAESTROOrchestrator")
    extracted = functions((root / "src/agent/prediction.py").read_text(), "PredictionCoordinator")
    prediction = {}
    for old, current in {**PredictionNames.names, "_reused_prediction": "_reused_prediction", "_record_prediction": "_record_prediction",
                         "_build_action_prediction_requests": "_build_action_prediction_requests", "_build_prediction_request": "_build_prediction_request"}.items():
        if old in original:
            prediction[old] = ast.dump(PredictionNames().visit(original[old])) == ast.dump(extracted[current])
    previous_memory = source(root, BASE, "src/agent/memory.py")
    original_store = functions(previous_memory, "CaseStore")
    extracted_text = (root / "src/agent/case_store.py").read_text()
    extracted_store = functions(extracted_text, "CaseStore")
    store = {name: ast.dump(node) == ast.dump(extracted_store[name]) for name, node in original_store.items()}
    helpers = {name: ast.dump(functions(previous_memory)[name]) == ast.dump(functions(extracted_text)[name])
               for name in ("connect", "_now", "_refusal")}
    moved = {}
    for filename, names in {"resistrace_retrospective.py": None, "state_evidence_followup.py": ("control_action", "replay", "run"),
                            "state_raw_reconstruction.py": ("run",), "state_prospective_certify.py": ("prepare",),
                            "state_prospective_review.py": ("run",)}.items():
        prior = functions(source(root, BASE, "tools/datasets/" + filename))
        current = functions((root / "research/astra" / filename).read_text())
        moved[filename] = {name: ast.dump(prior[name]) == ast.dump(current[name]) for name in (names or prior.keys())}
    initial = json.loads((root / "research/astra/results/20261003_convergence_v1/before.json").read_text())
    frozen = json.loads((root / "research/astra/results/20261003_responsibility_followup_v2/before.json").read_text())["protected_sha256"]
    differences = [name for name, expected in frozen.items() if digest(root / name) != expected]
    prefix = (root / "log/20261003/README.md").read_bytes()[:initial["log_prefix_bytes"]]
    return {"base": BASE, "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
            "prediction_method_parity": prediction, "case_store_existing_method_parity": store, "transaction_helper_parity": helpers,
            "experimental_function_parity": moved, "parity_rule": "AST equality after prediction ownership/name changes only; no biology inferred",
            "protected_files": len(frozen), "protected_differences": differences,
            "old_day_log_prefix_preserved": hashlib.sha256(prefix).hexdigest() == initial["log_prefix_sha256"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    groups = [result["prediction_method_parity"], result["case_store_existing_method_parity"], result["transaction_helper_parity"],
              *result["experimental_function_parity"].values()]
    if not all(all(group.values()) for group in groups) or result["protected_differences"] or not result["old_day_log_prefix_preserved"]:
        raise SystemExit("Convergence parity or byte-preservation failed; inspect the saved receipt.")


if __name__ == "__main__":
    main()
