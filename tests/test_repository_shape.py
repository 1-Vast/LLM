"""Package layout, tool scoping, and the English-only language rules.

File summary
- Path: tests/test_repository_shape.py
- Purpose: Package layout, tool scoping, and the English-only language rules.
- Core points: assertions here are contract tests, not biological results; each test pins one boundary that must not silently move.
- Interfaces: `test_source_is_separated_by_core_agent_and_virtual_cell_responsibility()`, `test_tools_are_folder_scoped_runtime_components()`, `test_log_is_one_dated_experiment_record_per_working_day()`, `test_log_index_declares_every_file_in_the_record()`, `test_project_markdown_has_no_chinese_prose()`, `test_python_sources_are_english_only()`, `test_package_imports_form_a_layered_acyclic_graph()`
- Depends on: maestro
"""
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("package,expected", [
    ("agent", {"MAESTROOrchestrator", "MAESTROCaseLoop"}),
    ("maestro", {"MAESTROAgent", "EvidenceAction", "FunctionalInterventionProfile", "MechanismHypothesis"}),
    ("virtual_cell", {"PredictionRequest", "StatePrediction", "safe_predict"}),
    ("tools.evaluation", {"CaseRepository", "EvaluationRunner"}),
])
def test_package_roots_expose_only_entry_points(package, expected):
    import importlib
    import inspect

    module = importlib.import_module(package)
    assert set(module.__all__) == expected
    symbols = {
        name for name, value in vars(module).items()
        if not name.startswith("_") and (inspect.isclass(value) or inspect.isfunction(value))
    }
    assert symbols == expected
    assert not hasattr(module, "__getattr__")


@pytest.mark.parametrize("module,arguments,expected", [
    ("tools.evaluation.engagement_cases", [], "--require-selective-dependency"),
    ("tools.evaluation.construction", ["build"], "--per-archetype"),
    ("tools.evaluation.construction", ["screen"], "--registry"),
    ("tools.evaluation.scoring", ["adjudicate"], "--public-cases"),
    ("tools.evaluation.scoring", ["table"], "--evaluation"),
    ("tools.case_memory.workflow", [], "sources,pack,graphs"),
    ("tools.datasets.catalog", [], "candidates,source,probe,search,fetch"),
    ("tools.evaluation.cli", [], "--public-cases"),
    ("tools.evaluation.discovery_replay", [], "--library"),
    ("tools.case_memory.audit", [], "quality,figures"),
])
def test_consolidated_command_entrypoints_run(module, arguments, expected):
    result = subprocess.run(
        [sys.executable, "-B", "-m", module, *arguments, "--help"],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout
    assert expected in result.stdout


def test_published_data_tool_modules_import_without_loading_assets():
    import importlib

    for module in (
        "tools.case_memory.build_cases",
        "tools.case_memory.validate",
        "tools.analysis.tool",
        "tools.datasets.catalog",
        "tools.datasets.lincs_pack",
        "tools.datasets.combination_screens",
        "tools.evaluation.discovery_replay",
    ):
        importlib.import_module(module)


def test_source_is_separated_by_core_agent_and_virtual_cell_responsibility():
    source_packages = sorted(
        path.name
        for path in (ROOT / "src").iterdir()
        if path.is_dir() and (path / "__init__.py").is_file()
    )
    assert source_packages == ["agent", "maestro", "virtual_cell"]
    assert (ROOT / "tools" / "evaluation" / "__init__.py").is_file()
    assert (ROOT / "src" / "maestro" / "contrast.py").is_file()
    assert not (ROOT / "src" / "maestro" / "planning.py").exists()
    assert (ROOT / "research/astra/state_readout_repair_20261009/verify.py").is_file()
    assert (ROOT / "research/astra/state_feedback_repair_20261009/verify.py").is_file()
    assert (ROOT / "research/decision_value/verify.py").is_file()
    assert not (ROOT / "src" / "maestro" / "agent.py").exists()
    assert (ROOT / "src" / "agent" / "orchestrator.py").is_file()
    assert (ROOT / "src" / "virtual_cell" / "interface.py").is_file()
    assert not (ROOT / "scripts").exists()
    assert not (ROOT / "results").exists()
    assert (ROOT / "src/agent/case_store.py").is_file()
    assert "CaseStore" in (ROOT / "src/agent/memory.py").read_text(encoding="utf-8")
    assert len(list((ROOT / "research/astra").glob("state_*_repair_20261009"))) == 2
    assert (ROOT / "research/decision_value/verify.py").is_file()
    assert not any((ROOT / "research/identifiability_audit").rglob("*.py"))
    assert not any((ROOT / "research/dual_core_live").rglob("*.py"))
    assert not any((ROOT / "research/dual_core_followup").rglob("*.py"))
    assert not (ROOT / "research/Innovation.md").exists()
    assert not (ROOT / "Innovation.md").exists()


def test_source_packages_do_not_import_research_or_tools():
    offenders = []
    for path in sorted((ROOT / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            else:
                continue
            if any(name.split(".")[0] in {"research", "tools", "evaluation"} for name in names):
                offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert not offenders, "source packages import research or tool code: " + ", ".join(offenders)


def test_current_tools_do_not_import_or_launch_research_code():
    """Ignore inert evidence copies; check static imports and dynamic module requests."""
    offenders = []
    for path in sorted((ROOT / "tools").rglob("*.py")):
        if "audit_results" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            elif isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute)):
                method = node.func.id if isinstance(node.func, ast.Name) else node.func.attr
                names = [arg.value for arg in node.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str)] if method in ("__import__", "import_module") else []
            elif isinstance(node, (ast.List, ast.Tuple)):
                # Catch Python -m research drivers, including f-string module names.
                names = [ast.literal_eval(arg) if isinstance(arg, ast.Constant) else ast.unparse(arg)
                         for arg in node.elts if isinstance(arg, (ast.Constant, ast.JoinedStr))]
                if "-m" not in names:
                    continue
            else:
                continue
            if any(isinstance(name, str) and (name.startswith("research.") or "research." in name and name.startswith("f")) for name in names):
                offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert not offenders, "tools depend on research code: " + ", ".join(offenders)


def test_tools_are_folder_scoped_runtime_components():
    assert (ROOT / "tools" / "registry.yaml").is_file()
    manifests = sorted(set((ROOT / "tools").glob("*/manifest.json"))
                       | set((ROOT / "tools").glob("*/*.manifest.json")))
    assert {path.parent.name for path in manifests} == {
        "analysis",
        "prediction",
        "case_memory",
    }
    assert all((path.parent / json.loads(path.read_text(encoding="utf-8"))["entrypoint"]).is_file()
               for path in manifests)
    assert not (ROOT / "tools" / "tool.py").exists()
    shared = ROOT / "tools" / "shared"
    assert not shared.exists()
    assert not list(shared.glob("*.py"))
    assert (ROOT / "tests" / "fixtures" / "stub_client.py").is_file()
    assert (ROOT / "tests" / "fixtures" / "state.py").is_file()
    assert (ROOT / "tests" / "fixtures" / "biological.py").is_file()
    assert not (ROOT / "log" / "artifacts").exists()
    assert not (ROOT / "log" / "design").exists()


CJK_PATTERN = re.compile(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]")
# Chinese survives only where it is part of a real identifier: an inline code
# span or a path-like parenthetical. A supplied reference asset or a data file
# may carry a non-ASCII filename, and rewriting the reference would break it.
INLINE_CODE = re.compile(r"`[^`]*`")
MARKDOWN_LINK_DESTINATION = re.compile(r"\]\([^()]*\)")
PATH_LIKE_GROUP = re.compile(r"\([^()]*/[^()]*\)")
THIRD_PARTY = ("reference/paper/", "data/external/", ".pytest_cache/", "__pycache__/", ".workbuddy/", ".workbuddy-ai/", "outputs/")


def _project_markdown():
    """Markdown this project owns, which is the markdown git tracks.

    Walking the working tree instead swept in whatever a local checkout happened to hold: a
    verification run failed this rule on an empty README inside a downloaded dataset under
    `data/`, which `.gitignore` excludes and which the project does not write. The English-only
    rule is about the project's own prose, so tracked files are exactly the right set, and the
    rule can no longer be broken by a third party's file landing in a local directory.
    """

    listed = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.md"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    if listed.returncode == 0:
        return sorted(
            ROOT / name
            for name in listed.stdout.split("\0")
            if name and (ROOT / name).is_file()
        )
    # Without git, fall back to the working tree minus the directories a checkout does not own.
    excluded = THIRD_PARTY
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if not any(part in path.relative_to(ROOT).as_posix() for part in excluded)
    )


def test_project_markdown_has_no_chinese_prose():
    """Current project markdown is English-only; immutable source reports are isolated.

    No Chinese term glosses, headings, table cells, or prose are allowed. The
    Outside the content-bound historical manifest, tolerated CJK is inside an inline code span or a path-like
    parenthetical, because a real identifier may carry a non-ASCII name.
    """

    offenders = []
    for path in _project_markdown():
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            continue  # An empty file has no prose to judge; emptiness is its own test below.
        scrubbed = INLINE_CODE.sub("", text)
        scrubbed = MARKDOWN_LINK_DESTINATION.sub("", scrubbed)
        scrubbed = PATH_LIKE_GROUP.sub("", scrubbed)
        for line_number, line in enumerate(scrubbed.split("\n"), start=1):
            if CJK_PATTERN.search(line):
                offenders.append(f"{path.relative_to(ROOT).as_posix()}:{line_number}: {line.strip()[:90]}")
    assert not offenders, "Chinese prose found outside paths:\n" + "\n".join(offenders)


def test_tracked_markdown_is_never_empty():
    """An empty tracked markdown file is a defect, and is reported as that rather than as prose.

    This was previously asserted inside the Chinese-prose test, where an empty file produced a
    failure whose name said the opposite of what had happened.
    """

    empty = [
        path.relative_to(ROOT).as_posix()
        for path in _project_markdown()
        if not path.read_text(encoding="utf-8").strip()
    ]
    assert not empty, f"tracked markdown files are empty: {empty}"


def test_python_sources_are_english_only():
    """Source code is English-only, docstrings and runtime strings included.

    The markdown rule cannot see source files, which is how Chinese term
    glosses survived in docstrings after the prose had been converted. An
    executable literal is covered as well: user-facing text is English, so a
    Chinese literal is a defect rather than a gloss. The pattern is written
    with escapes so this module contains no CJK of its own.
    """

    offenders = []
    for pattern in ("src/**/*.py", "tests/**/*.py", "tools/**/*.py"):
        for path in sorted(ROOT.glob(pattern)):
            text = path.read_text(encoding="utf-8")
            for line_number, line in enumerate(text.split("\n"), start=1):
                if CJK_PATTERN.search(line):
                    relative = path.relative_to(ROOT).as_posix()
                    offenders.append(f"{relative}:{line_number}: {line.strip()[:90]}")
    assert not offenders, "Chinese found in Python sources:\n" + "\n".join(offenders)


LOG_ROOT = ROOT / "log"
LOG_DAY_NAME = re.compile(r"^\d{8}$")
LOG_DAY_ROW = re.compile(r"^\| (\d{8}) \|", re.MULTILINE)
LOG_RECORD_FIELDS = ("> - **Path**:", "> - **Purpose**:", "> - **Core points**:")


def _log_day_directories():
    return sorted(
        path for path in LOG_ROOT.iterdir()
        if path.is_dir() and (path / "README.md").is_file()
    )


def test_log_is_compact_dated_release_record():
    """Each retained date has a compact summary and canonical receipts."""

    assert LOG_ROOT.is_dir(), LOG_ROOT
    assert (LOG_ROOT / "INDEX.md").is_file()
    strays = sorted(
        path.name for path in LOG_ROOT.iterdir()
        if path.is_file() and path.name not in {"INDEX.md", "MANIFEST.json"}
    )
    assert not strays, f"unexpected files at log/ top level: {strays}"
    assert (LOG_ROOT / "MANIFEST.json").is_file()

    days = _log_day_directories()
    assert days, "log/ has no day folders"
    for day in days:
        assert LOG_DAY_NAME.match(day.name), f"day folder is not named YYYYMMDD: {day.name}"
        record = day / "README.md"
        assert record.is_file(), f"{day.name} holds no day record"
        text = record.read_text(encoding="utf-8")
        iso_date = f"{day.name[:4]}-{day.name[4:6]}-{day.name[6:]}"
        titles = [line for line in text.split("\n") if line.startswith("# ")]
        assert titles, f"{day.name} record has no title"
        assert iso_date in titles[0], f"{day.name} title does not carry its date: {titles[0]}"
        assert all(field in text for field in LOG_RECORD_FIELDS), f"{day.name} lacks its compact summary"


def test_log_manifest_tracks_every_dated_file_and_hash():
    """The machine manifest, not the reading index, owns the file inventory."""
    from tools.log_manifest import build_manifest

    recorded = json.loads((LOG_ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    assert recorded == build_manifest()
    index = (LOG_ROOT / "INDEX.md").read_text(encoding="utf-8")
    assert "| Date | Topic | Canonical receipt |" in index
    listed_days = set(LOG_DAY_ROW.findall(index))
    assert listed_days == {day.name for day in _log_day_directories()}


def test_no_test_module_imports_another_test_module():
    """Test helpers live in `tests/fixtures/`, never in test modules.

    A test module that imports another one makes a test run depend on collection
    order and turns a fixture change into a cross-suite failure. Anything two test
    modules need belongs to `tests/fixtures/`; this asserts the boundary holds.
    """

    offenders = []
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        source = path.read_text(encoding="utf-8")
        for number, line in enumerate(source.split("\n"), start=1):
            if re.match(r"^\s*(from|import)\s+test_\w+", line):
                offenders.append(f"{path.name}:{number}: {line.strip()}")
    assert not offenders, "a test module imports another test module:\n" + "\n".join(offenders)


# Which source packages each package may import when its module is loaded. The layers
# run core -> world model -> agent, so the graph is acyclic by construction.
ALLOWED_EAGER_IMPORTS = {
    "maestro": set(),
    "virtual_cell": {"maestro"},
    "agent": {"maestro", "virtual_cell"},
}
# Upward edges tolerated only inside a function or a TYPE_CHECKING block. maestro types
# a few values in the virtual cell's vocabulary and defers that import on purpose.
ALLOWED_DEFERRED_IMPORTS = {"maestro": {"virtual_cell"}}


def _package_imports() -> dict[str, dict[str, set[str]]]:
    """Cross-package imports per package, split into eager and deferred edges with their sites."""

    packages = set(ALLOWED_EAGER_IMPORTS)
    found: dict[str, dict[str, set[str]]] = {name: {"eager": set(), "deferred": set()} for name in packages}
    for path in sorted((ROOT / "src").rglob("*.py")):
        package = path.relative_to(ROOT / "src").parts[0]
        tree = ast.parse(path.read_text(encoding="utf-8"))
        guarded = {
            id(inner)
            for node in ast.walk(tree)
            if isinstance(node, ast.If) and "TYPE_CHECKING" in ast.unparse(node.test)
            for inner in ast.walk(node)
        }
        top_level = {id(node) for node in tree.body}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                target = package if node.level else (node.module or "").split(".")[0]
            elif isinstance(node, ast.Import):
                target = node.names[0].name.split(".")[0]
            else:
                continue
            if target in packages and target != package:
                kind = "eager" if id(node) in top_level and id(node) not in guarded else "deferred"
                found[package][kind].add(f"{target} <- {path.relative_to(ROOT).as_posix()}:{node.lineno}")
    return found


def test_package_imports_form_a_layered_acyclic_graph():
    """A lower layer never imports a higher one when it loads.

    `agent` once imported `evaluation` through an evaluation arm kept in the wrong
    package, while `evaluation` imports `agent`: a cycle that made import order matter.
    """

    violations = []
    for package, edges in _package_imports().items():
        for kind, allowed in (("eager", ALLOWED_EAGER_IMPORTS[package]),
                              ("deferred", ALLOWED_EAGER_IMPORTS[package] | ALLOWED_DEFERRED_IMPORTS.get(package, set()))):
            violations.extend(
                f"{package} ({kind}): {site}" for site in sorted(edges[kind])
                if site.split(" <- ")[0] not in allowed
            )
    assert not violations, "package import layering violated:\n" + "\n".join(violations)
