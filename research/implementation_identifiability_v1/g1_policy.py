"""Deterministic pre-purchase proposal run inside the isolated tree (reads source, query and state only)."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import logic  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    args = ap.parse_args()
    work = Path(args.workdir)
    query = json.loads((work / "query" / "query.json").read_text(encoding="utf-8"))
    state = json.loads((work / "state.json").read_text(encoding="utf-8"))
    model = logic.aurora_model()
    st = logic.initial_state(state["observed"], state["premises"])
    spent = set(state["observed"])
    proposal = logic.propose(model, st, query["menu"], spent)
    proposal["residual_none_flag"] = logic.residual_none(model, st)
    print(json.dumps(proposal, sort_keys=True))


if __name__ == "__main__":
    main()
