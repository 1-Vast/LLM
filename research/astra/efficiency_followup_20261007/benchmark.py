"""Software execution benchmark; no inference or new scientific evidence."""
import argparse
import cProfile
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import tempfile
import time
import sys
import tracemalloc

from agent.case_store import CaseStore
from agent.context import ContextBuilder, ContextPacket, TaskIntent
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryStore, RunLogger
from agent.prediction import PredictionCoordinator
from agent.tool_runtime import LocalToolCatalog, ToolRouter
from maestro.models import EvidenceAction, MechanismContrast

ROOT = Path(__file__).resolve().parents[3]


class Client:
    def complete_json(self, messages, **kwargs):
        return {"tool_id": "column_summary", "dataset_id": "dataset_1", "arguments": {"column": "value"},
                "rationale": "Declared numeric fixture."}, None


def benchmark(output, baseline=False):
    catalog_type, router_type = LocalToolCatalog, ToolRouter
    if baseline:
        source = Path(__file__).with_name("tool_runtime_before.py.txt")
        spec = importlib.util.spec_from_file_location("agent.efficiency_baseline", source,
            loader=__import__("importlib.machinery", fromlist=["SourceFileLoader"]).SourceFileLoader("agent.efficiency_baseline", str(source)))
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        catalog_type, router_type = module.LocalToolCatalog, module.ToolRouter
    with tempfile.TemporaryDirectory() as folder:
        work = Path(folder)
        path = work / "data.csv"
        path.write_text("value\n1\n2\n3\n")
        intent = TaskIntent("analysis_planning", "Inspect declared data.", (), (), None, None, (), (), (), False)
        context = ContextPacket(intent, (), (), "Inspect declared data.")
        builder = ContextBuilder(EvidenceLedger(work / "e.sqlite"), MemoryStore(work / "m.sqlite"))
        store = CaseStore(work / "case.sqlite")
        store.open_case("fixture", budget=10)
        coordinator = PredictionCoordinator(None, RunLogger(work / "logs"))
        action = EvidenceAction("fixture", "Fixture", 0, ())
        contrast = MechanismContrast("fixture", (), (), action, (), ())
        catalog = catalog_type(ROOT / "tools")
        router = router_type(Client(), ROOT / "tools")
        workloads = {
            "catalog_warm": catalog.discover,
            "router_warm": lambda: router.select_and_execute(context, (path,)),
            "router_cold": lambda: router_type(Client(), ROOT / "tools").select_and_execute(context, (path,)),
            "context_warm": lambda: builder.build(intent),
            "context_cold": lambda: ContextBuilder(EvidenceLedger(work / "e.sqlite"), MemoryStore(work / "m.sqlite")).build(intent),
            "case_snapshot": lambda: store.snapshot("fixture"),
            "case_cold": lambda: CaseStore(work / "case.sqlite").snapshot("fixture"),
            "prediction_no_backend": lambda: coordinator.query(contrast, intent, None, "fixture", "s", (action,), prediction_request=None, template=None),
            "prediction_cold_no_backend": lambda: PredictionCoordinator(None, RunLogger(work / "logs")).query(contrast, intent, None, "fixture", "s", (action,), prediction_request=None, template=None),
        }
        results = {}
        for name, run in workloads.items():
            timings = []
            for repeat in range(15):
                start = time.perf_counter()
                run()
                timings.append(time.perf_counter() - start)
            results[name] = {"median_seconds": statistics.median(timings), "first_seconds": timings[0], "samples": timings}
        profiler = cProfile.Profile()
        profiler.runcall(catalog.discover)
        profiler.dump_stats(str(output.with_suffix(".prof")))
        tracemalloc.start()
        catalog.discover()
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        source = Path(__file__).with_name("tool_runtime_before.py.txt") if baseline else ROOT / "src/agent/tool_runtime.py"
        with output.open("x", encoding="utf-8") as handle:
            json.dump({"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "baseline_snapshot": baseline,
                       "catalog_peak_python_bytes": peak, "results": results,
                       "limitation": "15 serial local software calls; no backend, provider, response or measurement work."}, handle, indent=2)
        print(json.dumps({name: row["median_seconds"] for name, row in results.items()}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    benchmark(args.output, args.baseline)
