"""Package layout, tool scoping, and the English-only language rules."""
import ast
import base64
from contextlib import ExitStack
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
import zipfile

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
    assert not (ROOT / "src" / "maestro" / "agent.py").exists()
    assert (ROOT / "src" / "agent" / "orchestrator.py").is_file()
    assert (ROOT / "src" / "virtual_cell" / "interface.py").is_file()
    assert not (ROOT / "scripts").exists()
    assert not (ROOT / "results").exists()
    assert (ROOT / "src/agent/case_store.py").is_file()
    assert "CaseStore" in (ROOT / "src/agent/memory.py").read_text(encoding="utf-8")
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
THIRD_PARTY = ("reference/paper/", "data/external/", ".pytest_cache/", "__pycache__/", ".workbuddy/", ".workbuddy-ai/", "outputs/", "log/research_records/", "log/20261021/", "log/20261022/", "log/20261023/")


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
            and not any(part in name for part in THIRD_PARTY)
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


def _registered_research_assets(registry):
    for name in registry.get("workspaces", []):
        yield name, registry.get("workspace_storage", {}).get(name, {}), ["README.md"]
    for study in registry["studies"]:
        assert study["status"] in {"exploratory", "frozen", "completed"}
        required = [study["protocol"], study["verification"]]
        if study["status"] == "frozen":
            required.append(study.get("freeze", "FREEZE.json"))
        yield study["path"], study.get("storage", {}), required


def _assert_manifest_source(source_id, manifest):
    item = manifest["files"][source_id]
    if item["representation"] == "git_blob":
        commit = manifest["source_commit"]
        assert re.fullmatch(r"[0-9a-f]{40}", commit)
        blob = subprocess.run(
            ["git", "rev-parse", f"{commit}:{item['git_path']}"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        assert blob == item["git_blob"], source_id
        payload = subprocess.run(
            ["git", "cat-file", "blob", blob],
            cwd=ROOT, capture_output=True, check=True,
        ).stdout
    else:
        assert item["representation"] == "exact_supplement", source_id
        if "live_path" in item:
            target = (ROOT / item["live_path"]).resolve()
            assert target.is_relative_to(ROOT)
            payload = target.read_bytes()
        else:
            target = (ROOT / item["record_path"]).resolve()
            assert target.is_relative_to(ROOT)
            assert item["offset"] >= 0 and item["length"] > 0
            with target.open("rb") as stream:
                stream.seek(item["offset"])
                record = json.loads(stream.read(item["length"]))
            payload = record["text"].encode("utf-8") if record["encoding"] == "utf-8" else base64.b64decode(record["base64"], validate=True)
    assert len(payload) == item["bytes"], source_id
    assert hashlib.sha256(payload).hexdigest() == item["sha256"], source_id


def test_repository_has_one_scientific_report_and_no_retired_release_tree():
    research = ROOT / "research"
    registry = json.loads((research / "STUDIES.json").read_text(encoding="utf-8"))
    studies = registry["studies"]
    names = {study["path"] for study in studies}
    assert len(names) == len(studies), "Study paths must be unique"
    workspaces = registry.get("workspaces", [])
    assert len(workspaces) == len(set(workspaces))
    assert not names & set(workspaces), "Working areas are distinct from registered studies"
    manifest = json.loads((ROOT / "log/SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    for name, storage, required in _registered_research_assets(registry):
        assert Path(name).name == name
        if storage.get("state") != "archived":
            assert all((research / name / filename).is_file() for filename in required)
            continue
        assert storage["prefix"] == f"research/{name}/"
        for filename in required:
            original_path = f"research/{name}/{filename}"
            candidates = (original_path, "packages/historical_experiments/" + original_path)
            source_id = next((path for path in candidates if path in manifest["files"]), None)
            assert source_id is not None, f"Missing required archived source identity: {original_path}"
            _assert_manifest_source(source_id, manifest)
    tracked = subprocess.run(
        ["git", "ls-files", "-z", "--", "research"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    tracked_roots = {name.split("/")[1] for name in tracked.stdout.split("\0") if name and (ROOT / name).is_file()}
    reports = {"README.md", "EVIDENCE.md", "STUDIES.json"}
    current_studies = {study["path"] for study in studies if study.get("storage", {}).get("state") != "archived"}
    current_workspaces = {name for name in workspaces if registry.get("workspace_storage", {}).get(name, {}).get("state") != "archived"}
    assert tracked_roots <= reports | names | set(workspaces)
    assert reports | current_studies | current_workspaces <= tracked_roots | {"README.md"}
    assert (ROOT / "log/RESEARCH_REPORT.md").is_file()
    assert not (research / "REPORT.md").exists()
    assert (research / "README.md").is_file()
    for name in ("cleanup", "Innovation.md", "task.md", "RELEASE_CHECK.md",
                 "RELEASE_STATS.json", "CURRENT_REPOSITORY_STATS.json", "BLOCKED_ASSETS.md"):
        assert not (ROOT / name).exists(), name
    tracked_root_entries = {name.split("/")[0] for name in tracked.stdout.split("\0") if name}
    assert not any(name.startswith(".build-") for name in tracked_root_entries)
    assert not any(name.startswith("output-") for name in tracked_root_entries)


@pytest.mark.skipif(os.environ.get("MAESTRO_VERIFY_ARCHIVES") != "1", reason="Local research package integration requires MAESTRO_VERIFY_ARCHIVES=1")
def test_local_archived_research_assets_match_retained_sources():
    """Verify local package bytes explicitly; Git source identity is a separate check."""
    registry = json.loads((ROOT / "research/STUDIES.json").read_text(encoding="utf-8"))
    source_index = json.loads((ROOT / "data/processed/research_records/INDEX.json").read_text(encoding="utf-8"))
    archive_sources = {}
    for item in source_index.get("live_files", {}).values():
        if "archive_path" in item:
            key = (item["archive_path"], item["member"])
            if key in archive_sources:
                assert (item["bytes"], item["sha256"]) == (archive_sources[key]["bytes"], archive_sources[key]["sha256"])
            archive_sources[key] = item
    with ExitStack() as stack:
        archives = {}

        def assert_research_assets(name, storage, required):
            assert Path(name).name == name
            if storage.get("state") != "archived":
                return
            package, prefix = storage["package"], storage["prefix"]
            assert prefix == f"research/{name}/"
            target = (ROOT / package).resolve()
            assert target.is_relative_to(ROOT) and target.is_file()
            if package not in archives:
                archive = stack.enter_context(zipfile.ZipFile(target))
                assert len(archive.namelist()) == len(set(archive.namelist())), "Archive members must be unique"
                archives[package] = archive
            archive = archives[package]
            members = {item.filename: item for item in archive.infolist() if item.filename.startswith(prefix)}
            assert members, f"Archived research has no package members: {name}"
            for member, info in members.items():
                if info.is_dir():
                    continue
                item = archive_sources[(package, member)]
                assert item["bytes"] == info.file_size
            for filename in required:
                member = prefix + filename
                assert member in members, f"Missing required archived asset: {member}"
                item = archive_sources[(package, member)]
                payload = archive.read(member)
                assert len(payload) == item["bytes"]
                assert hashlib.sha256(payload).hexdigest() == item["sha256"]

        for name, storage, required in _registered_research_assets(registry):
            assert_research_assets(name, storage, required)


def test_selected_claim_bindings_are_available_without_local_research_data():
    """Check published source/quote availability, not semantic entailment or review authenticity."""
    from tools import retained_records

    registry = json.loads((ROOT / 'research/STUDIES.json').read_text(encoding='utf-8'))
    manifest = retained_records.load_index(ROOT, published=True)
    report = (ROOT / 'log/RESEARCH_REPORT.md').read_text(encoding='utf-8')
    coverage = registry['claim_coverage']
    assert coverage and len({item['id'] for item in coverage}) == len(coverage)
    tracked_sources = next(obj['source_ids'] for obj in registry['objects'] if obj['id'] == 'MAESTRO-CURRENT-REPORT')
    cache = {}
    for claim in coverage:
        assert claim['review']['status'] == 'approved' and claim['review']['reviewer']
        assert report.count(claim['report_quote']) == 1
        assert claim['sources']
        for source in claim['sources']:
            sid = source['id']
            assert sid in tracked_sources, 'Claim source must participate in incremental source tracking'
            if sid not in cache:
                cache[sid] = retained_records._read_bytes(sid, ROOT, manifest)
            payload = cache[sid]
            assert hashlib.sha256(payload).hexdigest() == source['sha256']
            assert source['quote'] in payload.decode('utf-8').replace('\r\n', '\n')


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


def test_case_memory_audit_help_needs_no_scientific_dependencies():
    script = """
import importlib.abc
import runpy
import sys
class NoScientificPackages(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'numpy', 'pandas', 'matplotlib', 'torch'}:
            raise ImportError('Optional dependency loaded during help: ' + fullname)
sys.meta_path.insert(0, NoScientificPackages())
sys.argv = ['tools.case_memory.audit', '--help']
runpy.run_module('tools.case_memory.audit', run_name='__main__')
"""
    result = subprocess.run([sys.executable, "-B", "-c", script], cwd=ROOT,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "--protocol-freeze" in result.stdout
