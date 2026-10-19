"""Source / query / evaluator separation and the access ledger.

Process-level isolation, not a security sandbox: the decision process runs in a child interpreter
(`-I`) whose working tree holds copies of the source and query views and the policy code only. The
evaluator vault lives outside that tree and its path is never passed to the child. The child sees no
outcome, no outcome-bearing record id, no vault file name and no log of the evaluator. Running an LLM
agent would need an OS-level sandbox or ACLs on top of this; none was run in G0/G1.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
HIDDEN_RECORDS = ("S1-R29", "S1-R30", "S1-R31", "S1-R32")
MENU_PRIVATE_FIELDS = ("outcome_in_records", "record_ids")


class OutcomeUnavailable(Exception):
    """The evaluator holds no real outcome for this bundle."""


class AccessLedger:
    """Append-only list of access events; written by the evaluator and the view builder only."""

    def __init__(self, path: Path | None = None):
        self.path = path
        self.events: list[dict] = []

    def log(self, event: str, actor: str, subject: str, detail: dict | None = None):
        row = {"seq": len(self.events) + 1, "event": event, "actor": actor, "subject": subject, "detail": detail or {}}
        self.events.append(row)
        return row

    def dump(self):
        text = "".join(json.dumps(e, sort_keys=True) + "\n" for e in self.events)
        if self.path:
            self.path.write_text(text, encoding="utf-8", newline="\n")
        return text


def strip_menu(menu: list[dict]) -> list[dict]:
    return [{k: v for k, v in a.items() if k not in MENU_PRIVATE_FIELDS} for a in menu]


def build_views(dest: Path, records: list[dict], menu: list[dict], unit: dict, ledger: AccessLedger | None = None):
    """Write `source/` and `query/` under `dest`; hidden evaluator records never enter either."""

    source = [r for r in records if r["id"] not in HIDDEN_RECORDS]
    (dest / "source").mkdir(parents=True, exist_ok=True)
    (dest / "query").mkdir(parents=True, exist_ok=True)
    (dest / "source" / "records.json").write_text(json.dumps(source, sort_keys=True, indent=1), encoding="utf-8", newline="\n")
    query = {
        "task": unit["task"], "target": unit["target"], "context": unit["context"],
        "implementations": unit["implementations"],
        "menu": strip_menu(menu),
        "budget_wells": sum(a["wells_min"] for a in menu),
    }
    (dest / "query" / "query.json").write_text(json.dumps(query, sort_keys=True, indent=1), encoding="utf-8", newline="\n")
    if ledger is not None:
        ledger.log("views_built", "view_builder", str(unit["unit_id"]),
                   {"source_records": len(source), "hidden_records_excluded": list(HIDDEN_RECORDS), "menu_actions": [a["action_id"] for a in menu]})
    return query


class Evaluator:
    """Holds unpurchased outcomes. Releases exactly one observation per legal purchase."""

    def __init__(self, vault: dict, ledger: AccessLedger):
        self._vault = vault
        self.ledger = ledger
        self.released: dict[str, str] = {}

    def purchase(self, action_id: str, wells: int):
        out = self._vault["outcomes"].get(action_id)
        if out is None:
            self.ledger.log("purchase_refused_unavailable", "evaluator", action_id, {})
            raise OutcomeUnavailable(action_id)
        if action_id in self.released:
            self.ledger.log("purchase_refused_repeat", "evaluator", action_id, {})
            raise ValueError(f"{action_id} already released")
        self.released[action_id] = out["outcome"]
        self.ledger.log("outcome_released", "evaluator", action_id, {"simulated_wells_charged": wells})
        return {"action_id": action_id, "outcome": out["outcome"]}


def run_policy_isolated(workdir_parent: Path, query_dir_src: Path, source_dir_src: Path, observed: dict, premises: dict) -> dict:
    """Run the proposal in a child interpreter whose tree contains only source, query, policy and state."""

    tree = Path(tempfile.mkdtemp(prefix="idv1_", dir=workdir_parent))
    try:
        shutil.copytree(source_dir_src, tree / "source")
        shutil.copytree(query_dir_src, tree / "query")
        (tree / "policy").mkdir()
        for name in ("logic.py", "g1_policy.py"):
            shutil.copy2(HERE / name, tree / "policy" / name)
        (tree / "state.json").write_text(json.dumps({"observed": observed, "premises": premises}, sort_keys=True), encoding="utf-8", newline="\n")
        proc = subprocess.run([sys.executable, "-I", str(tree / "policy" / "g1_policy.py"), "--workdir", str(tree)],
                              cwd=tree, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr[-2000:])
        files = sorted(str(p.relative_to(tree)).replace("\\", "/") for p in tree.rglob("*") if p.is_file())
        return {"proposal": json.loads(proc.stdout), "stdout_sha256": hashlib.sha256(proc.stdout.encode()).hexdigest(),
                "stderr": proc.stderr, "tree_files": files}
    finally:
        shutil.rmtree(tree, ignore_errors=True)
