"""Package layout, tool scoping, and the English-only language rules.

File summary
- Path: tests/test_repository_shape.py
- Purpose: Package layout, tool scoping, and the English-only language rules.
- Core points: assertions here are contract tests, not biological results; each test pins one boundary that must not silently move.
- Interfaces: `test_source_is_separated_by_core_agent_and_virtual_cell_responsibility()`, `test_tools_are_folder_scoped_runtime_components()`, `test_log_is_one_dated_experiment_record_per_working_day()`, `test_log_index_declares_every_file_in_the_record()`, `test_project_markdown_has_no_chinese_prose()`, `test_python_sources_are_english_only()`
- Depends on: maestro
"""
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_source_is_separated_by_core_agent_and_virtual_cell_responsibility():
    source_packages = sorted(
        path.name
        for path in (ROOT / "src").iterdir()
        if path.is_dir() and (path / "__init__.py").is_file()
    )
    assert source_packages == ["agent", "evaluation", "maestro", "virtual_cell"]
    assert (ROOT / "src" / "maestro" / "contrast.py").is_file()
    assert not (ROOT / "src" / "maestro" / "agent.py").exists()
    assert (ROOT / "src" / "agent" / "orchestrator.py").is_file()
    assert (ROOT / "src" / "virtual_cell" / "interface.py").is_file()
    assert not (ROOT / "scripts").exists()
    assert not (ROOT / "results").exists()


def test_tools_are_folder_scoped_runtime_components():
    assert (ROOT / "tools" / "registry.yaml").is_file()
    manifests = sorted((ROOT / "tools").glob("*/manifest.json"))
    assert {path.parent.name for path in manifests} == {
        "column_summary",
        "data_profile",
        "table_filter",
        "evidence_bundle_optimize",
        "multimodal_alignment",
        "virtual_cell_query",
    }
    assert all((path.parent / "tool.py").is_file() for path in manifests)
    assert not (ROOT / "tools" / "tool.py").exists()
    # `tools/shared/` is support code for tools, offline runners and tests. It must
    # carry no manifest, or the router would offer it to the selecting model as a
    # dataset tool it is not.
    shared = ROOT / "tools" / "shared"
    assert shared.is_dir(), shared
    assert not (shared / "manifest.json").exists()
    assert (shared / "stub_client.py").is_file()
    assert (shared / "state_fixture.py").is_file()
    assert not (shared / "tool.py").exists()
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
    excluded = THIRD_PARTY
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if not any(part in path.relative_to(ROOT).as_posix() for part in excluded)
    )


def test_project_markdown_has_no_chinese_prose():
    """Project markdown is English-only; Chinese may survive only inside paths.

    No Chinese term glosses, headings, table cells, or prose are allowed. The
    only tolerated CJK is inside an inline code span or a path-like
    parenthetical, because a real identifier may carry a non-ASCII name.
    """

    offenders = []
    for path in _project_markdown():
        text = path.read_text(encoding="utf-8")
        assert text.strip(), path
        scrubbed = INLINE_CODE.sub("", text)
        scrubbed = MARKDOWN_LINK_DESTINATION.sub("", scrubbed)
        scrubbed = PATH_LIKE_GROUP.sub("", scrubbed)
        for line_number, line in enumerate(scrubbed.split("\n"), start=1):
            if CJK_PATTERN.search(line):
                offenders.append(f"{path.relative_to(ROOT).as_posix()}:{line_number}: {line.strip()[:90]}")
    assert not offenders, "Chinese prose found outside paths:\n" + "\n".join(offenders)


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
LOG_DAY_ROW = re.compile(r"^\| `(\d{8})/README\.md` \|", re.MULTILINE)
LOG_RECORD_FIELDS = ("> - **Path**:", "> - **Purpose**:", "> - **Core points**:")
LOG_REQUIRED_SECTIONS = (
    "Record control",
    "Research questions and hypotheses",
    "Materials, data and computational environment",
    "Experimental design and controls",
    "Experiment register and results",
    "Deviations, failures and corrections",
    "Interpretation and claim boundaries",
    "Reproduction and artifact ledger",
    "Open items and next experiments",
    "Curation provenance",
)
# A day record covers code and architecture. Housekeeping -- pruning, archiving,
# summarising, reformatting -- is not recorded in it, so these words must not
# reappear as a section heading in a record.
LOG_OUT_OF_SCOPE_HEADINGS = (
    "## consolidation",
    "## log consolidation",
    "## housekeeping",
    "## pruning",
    "## tree consolidation",
)


def _log_day_directories():
    return sorted(path for path in LOG_ROOT.iterdir() if path.is_dir())


def test_log_is_one_dated_experiment_record_per_working_day():
    """log/ is a dated experiment record: INDEX.md plus one folder per working day.

    A day folder is named YYYYMMDD and holds the day's record, which names its
    own path, carries that day's date in its title and opens with the
    structured summary every record in this tree uses. Nothing else may sit at
    the top level: material that is not a day record belongs in the dated
    isolation area beside the repository, declared in the index.
    """

    assert LOG_ROOT.is_dir(), LOG_ROOT
    assert (LOG_ROOT / "INDEX.md").is_file()
    strays = sorted(
        path.name for path in LOG_ROOT.iterdir() if path.is_file() and path.name != "INDEX.md"
    )
    assert not strays, f"log/ may hold only INDEX.md and day folders at top level: {strays}"

    days = _log_day_directories()
    assert days, "log/ has no day folders"
    for day in days:
        assert LOG_DAY_NAME.match(day.name), f"day folder is not named YYYYMMDD: {day.name}"
        record = day / "README.md"
        assert record.is_file(), f"{day.name} holds no day record"
        text = record.read_text(encoding="utf-8")
        for field in LOG_RECORD_FIELDS:
            assert field in text, f"{day.name} record lost its summary field {field}"
        assert f"`log/{day.name}/README.md`" in text, f"{day.name} does not name its own record path"
        iso_date = f"{day.name[:4]}-{day.name[4:6]}-{day.name[6:]}"
        titles = [line for line in text.split("\n") if line.startswith("# ")]
        assert titles, f"{day.name} record has no title"
        assert iso_date in titles[0], f"{day.name} title does not carry its date: {titles[0]}"
        headings = re.findall(r"^## (.+)$", text, re.MULTILINE)
        expected = [f"{index}. {title}" for index, title in enumerate(LOG_REQUIRED_SECTIONS, 1)]
        assert headings[: len(expected)] == expected, f"{day.name} lost or reordered a required section"
        lowered = text.lower()
        offenders = [heading for heading in LOG_OUT_OF_SCOPE_HEADINGS if heading in lowered]
        assert not offenders, (
            f"{day.name} record carries a housekeeping section; log/ records code and "
            f"architecture changes only: {offenders}"
        )


def test_log_index_declares_every_file_in_the_record():
    """The index is the single entry point: no file under log/ may be unlisted."""

    index = (LOG_ROOT / "INDEX.md").read_text(encoding="utf-8")
    declared = set(re.findall(r"`([^`]+)`", index))
    declared.update(re.findall(r"\]\(([^)\s]+)\)", index))

    files = sorted(
        path.relative_to(LOG_ROOT).as_posix()
        for path in LOG_ROOT.rglob("*")
        if path.is_file() and path.name != "INDEX.md"
    )
    undeclared = [
        name
        for name in files
        if not any(entry == name or entry.endswith("/" + name) for entry in declared)
    ]
    assert not undeclared, f"log/ holds files the index does not declare: {undeclared}"

    listed_days = set(LOG_DAY_ROW.findall(index))
    assert listed_days == {day.name for day in _log_day_directories()}, (
        "the reading-order table must list every day folder exactly once"
    )


def test_no_test_module_imports_another_test_module():
    """Shared machinery lives in `tools/shared/`, never in a test module.

    A test module that imports another one makes a test run depend on collection
    order and turns a fixture change into a cross-suite failure. Anything two test
    modules need belongs to `tools/shared/`; this asserts the boundary holds.
    """

    offenders = []
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        source = path.read_text(encoding="utf-8")
        for number, line in enumerate(source.split("\n"), start=1):
            if re.match(r"^\s*(from|import)\s+test_\w+", line):
                offenders.append(f"{path.name}:{number}: {line.strip()}")
    assert not offenders, "a test module imports another test module:\n" + "\n".join(offenders)
