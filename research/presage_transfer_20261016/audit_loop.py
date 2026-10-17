"""Reproduce thin-loop limitations against pinned HEAD and retain engineering evidence."""
import json
from pathlib import Path
import subprocess
import sys
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
from maestro import research_loop as current


def original():
    content = subprocess.check_output(
        ["git", "show", "6e6a2e4f:src/maestro/research_loop.py"], cwd=ROOT, text=True)
    module = types.ModuleType("original_research_loop")
    sys.modules[module.__name__] = module
    exec(compile(content, "pinned_HEAD/research_loop.py", "exec"), module.__dict__)
    return module


def checks(module):
    class Executor:
        def execute(self, action):
            return module.Observation(action.identifier, "a", source_id="declared_only",
                                      context_identifier="cell", independent_units=1)
    actions = (module.ActionCandidate("first", 1, 2), module.ActionCandidate("second", 1, 1))
    forecasts = {a.identifier: module.Forecast(a.identifier, {"a": .5, "b": .5},
                                               scope="other", support=0) for a in actions}
    loop = module.ResearchLoop(module.HypothesisPair("a", "b"), actions, forecasts, Executor(), budget=2)
    first = loop.step()
    frequencies = loop._posterior()
    return {"unsupported_execution": bool(first.selected_actions),
            "label_frequency_after_one": frequencies,
            "forecast_recomputed": loop.forecasts != forecasts}


if __name__ == "__main__":
    result = {"pinned_HEAD": checks(original()), "current": checks(current),
              "interpretation": "Engineering checks only. No likelihood update, dynamic value recomputation or evidence authentication has been added. Scoped validation is local; declaration is not independent support."}
    assert result["pinned_HEAD"]["unsupported_execution"]
    assert not result["current"]["unsupported_execution"]
    (HERE / "ENGINEERING.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
