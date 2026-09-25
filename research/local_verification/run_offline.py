"""Run the free, offline half of the local verification and write a comparable report.

File summary
- Path: research/local_verification/run_offline.py
- Purpose: everything that can be checked without spending a token or reaching a provider, run
  the same way on every machine so two reports can be diffed. It records the environment, the
  test suite, one full agent loop driven by a reviewed template, and hard assertions on the
  topology and evidence invariants that loop must satisfy.
- Core points:
  - No provider is contacted and no key is needed. Environment variables are reported by name and
    presence only; a value is never read into the report.
  - The loop runs with `--planner-template`, `--virtual-cell none` and `--decision-critic off`, so
    a failure here is a defect in MAESTRO rather than a provider's behaviour.
  - The assertions are the point: expected `steps_to_executable`, a named capability gap, no
    supply cycle, budget respected, and no prediction admitted as a measurement.
- Interfaces: `main()`
- Depends on: the fixture pack beside this file; pytest for the suite phase.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path
from xml.etree import ElementTree
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIXTURES = HERE / "fixtures"

# The fixture catalogue is built so these are the only correct answers. A chain is the start
# action plus each supplier, so the depth counts the action itself.
EXPECTED_STEPS = {"engagement_shift": 2, "proximal_activity": 3, "viability_readout": 4, "orthogonal_rescue": None}
EXPECTED_GAP = {"orthogonal_rescue": ["genetic:rescue_allele_available"]}
PROVIDER_VARIABLES = (
    "DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL", "DEEPSEEK_VISION_MODEL",
    "TYPESAFE_API_KEY", "TYPESAFE_ENDPOINT", "TYPESAFE_MODEL", "TYPESAFE_TIMEOUT_SECONDS",
    "MAESTRO_LOG_DIRECTORY",
)
OPTIONAL_MODULES = ("numpy", "scipy", "pandas", "h5py", "anndata", "sklearn", "torch", "rdkit", "pytest")


def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, cwd=ROOT, **kwargs)


def git(*arguments: str) -> str:
    outcome = run(["git", *arguments])
    return outcome.stdout.strip() if outcome.returncode == 0 else f"unavailable: {outcome.stderr.strip()[:120]}"


def variable_report() -> dict[str, str]:
    """Report configuration by name and shape only. No value is ever recorded."""

    report: dict[str, str] = {}
    for name in PROVIDER_VARIABLES:
        value = os.environ.get(name)
        if value is None:
            report[name] = "unset in the process environment"
        elif name.endswith("_API_KEY"):
            report[name] = f"set, {len(value)} characters (value not recorded)"
        else:
            report[name] = "set (value not recorded)"
    dotenv = ROOT / ".env"
    if dotenv.is_file():
        names = sorted(
            line.split("=", 1)[0].strip()
            for line in dotenv.read_text(encoding="utf-8").splitlines()
            if "=" in line and not line.lstrip().startswith("#")
        )
        report[".env"] = "present; declares " + ", ".join(names)
    else:
        report[".env"] = "absent"
    return report


def phase_environment() -> dict[str, Any]:
    modules: dict[str, str] = {}
    for name in OPTIONAL_MODULES:
        try:
            module = __import__(name)
        except Exception as error:  # noqa: BLE001 - an import failure is the finding.
            modules[name] = f"absent ({type(error).__name__})"
        else:
            modules[name] = str(getattr(module, "__version__", "present"))
    return {
        "python": sys.version.split()[0],
        "platform": f"{platform.system()} {platform.release()} {platform.machine()}",
        "git_head": git("rev-parse", "HEAD"),
        "git_tree": git("rev-parse", "HEAD^{tree}"),
        "git_branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "git_dirty_paths": [line[3:] for line in git("status", "--porcelain=v1").splitlines() if line][:20],
        "local_directories": {
            name: "present" if (ROOT / name).is_dir() else "absent"
            for name in ("data", "dataset", "log", "outputs", "reference", "tools")
        },
        "configuration": variable_report(),
        "modules": modules,
    }


def phase_suite(output: Path) -> dict[str, Any]:
    """Run the suite and read its counts from the JUnit report rather than its prose.

    pytest's final count line is formatting that has moved between versions; the JUnit report is
    a contract. The text log is kept beside it for the detail of any one failure.
    """

    junit = output / "junit.xml"
    started = time.monotonic()
    outcome = run([
        sys.executable, "-m", "pytest", "-q", "--continue-on-collection-errors", f"--junitxml={junit}",
    ])
    (output / "pytest.txt").write_text(outcome.stdout + outcome.stderr, encoding="utf-8")
    counts: dict[str, Any] = {}
    failing: list[str] = []
    if junit.is_file():
        root = ElementTree.parse(junit).getroot()
        suite = root if root.tag == "testsuite" else root.find("testsuite")
        if suite is not None:
            counts = {
                key: int(suite.get(key) or 0) for key in ("tests", "failures", "errors", "skipped")
            }
            counts["passed"] = counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
            for case in suite.findall("testcase"):
                if case.find("failure") is not None or case.find("error") is not None:
                    where = (case.get("classname") or "").replace(".", "/")
                    failing.append(f"{where}::{case.get('name')}" if where else str(case.get("name")))
    return {
        "seconds": round(time.monotonic() - started, 1),
        "exit_code": outcome.returncode,
        "counts": counts,
        "summary_line": (
            "{passed} passed, {failures} failed, {errors} errors, {skipped} skipped".format(**counts)
            if counts
            else "no JUnit report was produced; read pytest.txt"
        ),
        "failing_count": len(failing),
        "failing": sorted(failing),
        "full_output": "pytest.txt",
    }


def hermetic_workspace(output: Path) -> Path:
    """A throwaway workspace whose provider settings point at a closed local port.

    MAESTRO requires the provider block to be present even when a reviewed template answers every
    structured call, so this supplies one that cannot resolve to anything. It is what makes the
    offline phase provably free: no real base URL is in scope for this subprocess.
    """

    workspace = output / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / ".env").write_text(
        "DEEPSEEK_API_KEY=offline-phase-uses-a-reviewed-template\n"
        "DEEPSEEK_BASE_URL=http://127.0.0.1:9\n"
        "DEEPSEEK_MODEL=none\n"
        "DEEPSEEK_VISION_MODEL=none\n",
        encoding="utf-8",
    )
    return workspace


def phase_offline_loop(output: Path) -> dict[str, Any]:
    state = output / "state"
    trace = output / "trace.json"
    workspace = hermetic_workspace(output)
    command = [
        sys.executable, "-m", "agent",
        "Is the transcriptional response realised in this context at 24 h?",
        "--workspace", str(workspace),
        "--actions", str(FIXTURES / "actions.json"),
        "--profile", str(FIXTURES / "profile.json"),
        "--hypotheses", str(FIXTURES / "hypotheses.json"),
        "--rules", str(FIXTURES / "rules.json"),
        "--results", str(FIXTURES / "results.json"),
        "--planner-template", str(FIXTURES / "planner_template.json"),
        "--virtual-cell", "none",
        "--decision-critic", "off",
        "--case-id", "local-verification-offline",
        "--budget", "1",
        "--max-rounds", "2",
        "--state-directory", str(state),
        "--trace", str(trace),
    ]
    # The process environment wins over the dotenv file, so a real key exported in this shell
    # would otherwise reach the subprocess. Override the provider block and drop the typed-model
    # block, so this phase cannot contact anything whatever the shell holds.
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    environment.update(
        DEEPSEEK_API_KEY="offline-phase-uses-a-reviewed-template",
        DEEPSEEK_BASE_URL="http://127.0.0.1:9",
        DEEPSEEK_MODEL="none",
        DEEPSEEK_VISION_MODEL="none",
    )
    for name in ("TYPESAFE_API_KEY", "TYPESAFE_ENDPOINT", "TYPESAFE_MODEL"):
        environment.pop(name, None)
    started = time.monotonic()
    outcome = run(command, env=environment)
    (output / "loop_stdout.txt").write_text(outcome.stdout + outcome.stderr, encoding="utf-8")
    return {
        "seconds": round(time.monotonic() - started, 1),
        "exit_code": outcome.returncode,
        "stdout_tail": outcome.stdout.strip().splitlines()[-3:],
        "stderr_tail": outcome.stderr.strip().splitlines()[-3:],
        "trace": str(trace) if trace.is_file() else None,
    }


def phase_assertions(trace_path: Path) -> dict[str, Any]:
    """Hard checks on the loop's own record. Each one names the invariant it pins."""

    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    if not trace_path.is_file():
        check("trace_written", False, "the loop wrote no trace, so nothing downstream can be checked")
        return {"passed": 0, "failed": 1, "checks": checks}

    payload = json.loads(trace_path.read_text(encoding="utf-8"))
    record = payload.get("record", {})
    turns = record.get("turns") or [record]
    first = turns[0]
    topology = first.get("action_topology") or {}

    check("planner_was_a_reviewed_template", payload.get("planner") == "reviewed_template",
          f"planner={payload.get('planner')!r}")
    check("template_digest_recorded", bool(payload.get("template_sha256")),
          f"sha256={str(payload.get('template_sha256'))[:16]}...")

    steps = topology.get("steps_to_executable") or {}
    mismatched = {k: steps.get(k) for k, v in EXPECTED_STEPS.items() if steps.get(k) != v}
    check("supplier_chain_depths_are_exact", not mismatched,
          f"expected {EXPECTED_STEPS}, mismatched {mismatched}")

    gaps = {k: list(v) for k, v in (topology.get("unsupplied_premises") or {}).items()}
    check("capability_gap_is_named_not_substituted", gaps == EXPECTED_GAP,
          f"expected {EXPECTED_GAP}, got {gaps}")
    check("no_spurious_supply_cycle", not topology.get("supply_cycles"),
          f"cycles={topology.get('supply_cycles')}")

    selected = [action.get("identifier") for action in first.get("selected_actions") or []]
    catalogue = {item["identifier"]: item for item in json.loads((FIXTURES / "actions.json").read_text("utf-8"))}
    spend = sum(float(catalogue[name]["cost"]) for name in selected if name in catalogue)
    check("selection_respects_the_budget", spend <= 1.0, f"selected={selected} spend={spend}")
    frontier = set(topology.get("executable_now") or ())
    check("selection_is_on_the_executable_frontier", bool(selected) and set(selected) <= frontier,
          f"selected={selected} frontier={sorted(frontier)}")
    check("no_gap_action_was_selected", "orthogonal_rescue" not in selected, f"selected={selected}")

    blob = json.dumps(record)
    check("no_prediction_was_admitted_as_a_measurement", '"is_measurement": true' not in blob,
          "holds trivially while predictions are off; the same check is the point of the paid phase")
    check("a_stop_reason_is_recorded", bool(record.get("stop_reason")), f"stop_reason={record.get('stop_reason')}")
    check("a_real_result_was_imported", bool(record.get("reflections")),
          f"reflections={len(record.get('reflections') or [])}")

    return {
        "passed": sum(1 for item in checks if item["passed"]),
        "failed": sum(1 for item in checks if not item["passed"]),
        "checks": checks,
    }


def render(report: dict[str, Any]) -> str:
    lines = ["# Local verification — offline phases", ""]
    environment = report["environment"]
    lines += [
        f"- commit `{environment['git_head'][:12]}` tree `{environment['git_tree'][:12]}` branch `{environment['git_branch']}`",
        f"- python {environment['python']} on {environment['platform']}",
        f"- uncommitted paths: {environment['git_dirty_paths'] or 'none'}",
        "",
        "## Environment",
        "",
        "| Item | State |",
        "|---|---|",
    ]
    for name, state in environment["local_directories"].items():
        lines.append(f"| directory `{name}` | {state} |")
    for name, state in environment["configuration"].items():
        lines.append(f"| `{name}` | {state} |")
    for name, state in environment["modules"].items():
        lines.append(f"| module `{name}` | {state} |")

    suite = report["suite"]
    lines += [
        "",
        "## Test suite",
        "",
        f"- `{suite['summary_line']}`",
        f"- exit code {suite['exit_code']} in {suite['seconds']}s, {suite['failing_count']} failing ids",
        "",
    ]
    if suite["failing"]:
        lines.append("<details><summary>failing ids</summary>")
        lines.append("")
        lines += [f"- `{name}`" for name in suite["failing"]]
        lines += ["", "</details>", ""]

    loop = report["loop"]
    lines += [
        "## Offline agent loop",
        "",
        f"- exit code {loop['exit_code']} in {loop['seconds']}s",
        "- stdout: " + ("; ".join(loop["stdout_tail"]) or "none"),
    ]
    if loop["stderr_tail"]:
        lines.append("- stderr: " + "; ".join(loop["stderr_tail"]))

    assertions = report["assertions"]
    lines += [
        "",
        "## Acceptance checks",
        "",
        f"{assertions['passed']} passed, {assertions['failed']} failed.",
        "",
        "| Check | Result | Detail |",
        "|---|---|---|",
    ]
    for item in assertions["checks"]:
        mark = "pass" if item["passed"] else "**FAIL**"
        detail = item["detail"].replace("|", "\\|")
        lines.append(f"| `{item['check']}` | {mark} | {detail} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the offline half of the local verification.")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "local_verification")
    parser.add_argument("--skip-suite", action="store_true", help="Skip pytest; useful when iterating on the loop.")
    arguments = parser.parse_args()
    output = arguments.output
    output.mkdir(parents=True, exist_ok=True)

    print("phase 1/4  environment")
    report: dict[str, Any] = {"environment": phase_environment()}
    print("phase 2/4  test suite" + (" (skipped)" if arguments.skip_suite else ""))
    report["suite"] = (
        {"summary_line": "skipped", "exit_code": 0, "seconds": 0.0, "counts": {}, "failing_count": 0, "failing": [], "full_output": None}
        if arguments.skip_suite
        else phase_suite(output)
    )
    print("phase 3/4  offline agent loop")
    report["loop"] = phase_offline_loop(output)
    print("phase 4/4  acceptance checks")
    report["assertions"] = phase_assertions(output / "trace.json")

    (output / "report.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    rendered = render(report)
    (output / "report.md").write_text(rendered, encoding="utf-8")
    print()
    print(rendered)
    print(f"artifacts in {output}")
    return 1 if report["assertions"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
