"""Action-only program runner; authoritative scoring and model updates stay here.

Each choice runs in a fresh restricted Python process with JSON observations.
This reduces accidental/easy evaluator tampering; it is NOT an OS sandbox for
arbitrary hostile code. Candidate code never receives an Episode or a backend.
"""
from __future__ import annotations

import ast
import builtins
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time


SAFE_BUILTINS = {name: getattr(builtins, name) for name in (
    "len", "range", "min", "max", "sum", "sorted", "abs", "round", "float",
    "int", "list", "dict", "set", "tuple", "enumerate", "zip", "any", "all",
    "bool", "reversed", "str", "isinstance", "ValueError", "Exception",
)}
SAFE_NUMERIC = {name: getattr(math, name) for name in (
    "sqrt", "log", "exp", "isfinite", "floor", "ceil",
)}
SAFE_METHODS = {
    "get", "items", "keys", "values", "copy", "append", "extend", "pop",
    "sort", "reverse", "index", "count", "add", "discard", "remove",
    "update", "intersection", "union", "difference", "issubset", "issuperset",
}
FORBIDDEN_NAMES = {
    "open", "eval", "exec", "compile", "getattr", "setattr", "delattr",
    "globals", "locals", "vars", "dir", "type", "input", "help", "breakpoint",
    "memoryview", "super", "print", "exit", "quit",
}
FORBIDDEN_SYNTAX = (
    ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal, ast.ClassDef,
    ast.AsyncFunctionDef, ast.Await, ast.With, ast.AsyncWith, ast.Yield,
    ast.YieldFrom, ast.AsyncFor,
)


def check_source(source: str):
    """Keep the search language small, with no reflection, modules or file API."""
    if not isinstance(source, str) or len(source) > 50000:
        raise ValueError("source must be text of at most 50000 characters")
    tree = ast.parse(source)
    choices = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "choose"]
    if len(choices) != 1:
        raise ValueError("program must define exactly one choose(obs)")
    args = choices[0].args
    if len(args.posonlyargs) + len(args.args) != 1 or args.vararg or args.kwarg or args.kwonlyargs:
        raise ValueError("choose must accept exactly one observation argument")
    for node in ast.walk(tree):
        if isinstance(node, FORBIDDEN_SYNTAX):
            raise ValueError(f"forbidden syntax: {type(node).__name__}")
        if isinstance(node, ast.FunctionDef) and node.decorator_list:
            raise ValueError("decorators are unavailable")
        if isinstance(node, ast.Name) and (node.id.startswith("__") or node.id in FORBIDDEN_NAMES):
            raise ValueError(f"forbidden name: {node.id}")
        if isinstance(node, ast.Attribute):
            if node.attr not in SAFE_METHODS or not isinstance(node.ctx, ast.Load):
                raise ValueError(f"forbidden attribute: {node.attr}")
    return tree


def _json_copy(value):
    return json.loads(json.dumps(value, allow_nan=False))


def _choose(source, observation, timeout):
    # The child receives no inherited credentials, raw data paths or Python path.
    child_env = {k: v for k, v in os.environ.items()
                 if k.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP"}}
    completed = subprocess.run(
        [sys.executable, "-I", "-S", "-B", str(Path(__file__).resolve()), "--worker"],
        input=json.dumps({"source": source, "observation": observation}, allow_nan=False),
        capture_output=True, text=True, encoding="utf-8", timeout=timeout, env=child_env,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"runner exited {completed.returncode}")
    if len(completed.stdout) > 100000:
        raise RuntimeError("runner output exceeded limit")
    response = json.loads(completed.stdout, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    if not isinstance(response, dict) or set(response) not in ({"ok", "action"}, {"ok", "error"}):
        raise RuntimeError("malformed runner response")
    if response["ok"] is not True:
        raise ValueError(f"candidate: {response.get('error', 'unknown error')}")
    return response["action"]


def checked_result(result):
    """Selection and proposer evidence must both reject failed executions."""
    if not isinstance(result, dict):
        raise RuntimeError("invalid program evaluation: result is not an object")
    value = result.get("yield")
    if (result.get("status") != "ok" or result.get("error") is not None
            or type(value) not in (int, float) or not math.isfinite(value) or value < 0):
        raise RuntimeError(f"invalid program evaluation: {result.get('error', 'missing result')}")
    return result


def _predictions(episode, backend, drugs):
    raw = backend.predict() if backend is not None else episode["W"]
    if set(raw) != set(drugs):
        raise ValueError("predictions must contain exactly the episode drug pool")
    result = {d: float(raw[d]) for d in drugs}
    if any(not math.isfinite(p) or p < 0 or p > 1 for p in result.values()):
        raise ValueError("predictions must be finite probabilities")
    return result


def _model_id(backend):
    return str(getattr(backend, "model_id", "updating")) if backend is not None else "static"


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False,
                                    separators=(",", ":")).encode()).hexdigest()


def _backend_config(backend):
    """Bind evidence to the supplied trusted update configuration and covariates."""
    config = {}
    if backend is not None and hasattr(backend, "steps"):
        config["steps"] = int(backend.steps)
    if backend is not None and hasattr(backend, "optimizer"):
        optimizer = backend.optimizer
        config["optimizer_type"] = type(optimizer).__module__ + "." + type(optimizer).__name__
        config["optimizer_groups"] = [{k: v for k, v in group.items() if k != "params"}
                                       for group in optimizer.param_groups]
    if backend is not None and hasattr(backend, "inputs"):
        h = hashlib.sha256()
        for key, tensor in sorted(backend.inputs.items()):
            array = tensor.detach().cpu().contiguous().numpy()
            h.update(key.encode())
            h.update(str((array.dtype, array.shape)).encode())
            h.update(array.tobytes())
        config["inputs_sha256"] = h.hexdigest()
        config["drug_rows"] = dict(backend.drug_rows)
    return _json_copy(config)


def run_program(source: str, episode: dict, backend=None, timeout=10):
    """Run a complete episode, refreshing predictions after every paid query.

    Valid status is ``ok``; any execution/action/backend failure gives status
    ``invalid`` and yield=None, even if earlier paid actions were valid. Timeout
    is the candidate execution budget across the episode, excluding trusted
    model-update time. A fresh backend must be supplied for each episode.
    """
    trace, predictions = [], {}
    started = time.monotonic()
    candidate_seconds = 0.0
    error, stop_reason = None, "stop"
    provenance = {"source_sha256": hashlib.sha256(source.encode()).hexdigest()
                  if isinstance(source, str) else None,
                  "episode_sha256": None, "backend_type": None,
                  "initial_model_id": None, "backend_config": None,
                  "evaluation_context_sha256": None}
    try:
        check_source(source)
        episode = _json_copy(episode)
        provenance.update(episode_sha256=_digest(episode),
                          backend_type=type(backend).__module__ + "." + type(backend).__name__,
                          initial_model_id=_model_id(backend), backend_config=_backend_config(backend))
        provenance["evaluation_context_sha256"] = _digest(
            {k: provenance[k] for k in ("episode_sha256", "backend_type", "initial_model_id", "backend_config")})
        drugs = episode["drugs"]
        if not isinstance(drugs, list) or not drugs or any(not isinstance(d, str) for d in drugs) or len(drugs) != len(set(drugs)):
            raise ValueError("drugs must be unique nonempty strings")
        labels, mol = episode["labels"], episode.get("mol", {})
        if set(labels) != set(drugs) or any(type(y) not in (int, float) or y not in (0, 1) for y in labels.values()):
            raise ValueError("each drug needs an observed binary label on the evaluator side")
        if set(mol) - set(drugs):
            raise ValueError("molecular observations contain unknown drugs")
        budget, lam, timeout = float(episode.get("budget", 5)), float(episode.get("lam", .5)), float(timeout)
        if not all(math.isfinite(v) for v in (budget, lam, timeout)) or budget < 0 or lam <= 0 or timeout <= 0:
            raise ValueError("budget must be nonnegative; costs and timeout must be positive and finite")
        predictions = _predictions(episode, backend, drugs)
        queried_f, queried_m = {}, {}
        for step in range(2 * len(drugs) + 1):
            spent = sum(row["cost"] for row in trace)
            remaining = budget - spent
            affordable_f = remaining >= 1.0 - 1e-9 and any(d not in queried_f for d in drugs)
            affordable_m = remaining >= lam - 1e-9 and any(d not in queried_m for d in mol)
            if not (affordable_f or affordable_m):
                stop_reason = "no_affordable_action"
                break
            observation = {
                "drugs": drugs, "predictions": predictions, "W": predictions,
                "prior": episode.get("prior", {}), "nn": episode.get("nn", {}),
                "sim": episode.get("sim", {}), "budget_left": max(0., remaining),
                "costs": {"f": 1.0, "m": lam}, "queried_f": queried_f,
                "queried_m": queried_m, "available_m": list(mol), "step": step,
            }
            available_seconds = timeout - candidate_seconds
            if available_seconds <= 0:
                raise subprocess.TimeoutExpired("candidate", timeout)
            call_started = time.monotonic()
            try:
                action = _choose(source, observation, available_seconds)
            finally:
                candidate_seconds += time.monotonic() - call_started
            if not isinstance(action, dict) or action.get("kind") not in ("f", "m", "stop"):
                raise ValueError("action must be an object with kind f, m or stop")
            kind = action["kind"]
            if kind == "stop":
                if set(action) not in ({"kind"}, {"kind", "drug"}) or action.get("drug") is not None:
                    raise ValueError("stop must not carry a drug or other payload")
                break
            if set(action) != {"kind", "drug"}:
                raise ValueError("query action must contain only kind and drug")
            drug = action["drug"]
            if not isinstance(drug, str) or drug not in drugs:
                raise ValueError("unknown drug")
            observed = queried_f if kind == "f" else queried_m
            if drug in observed:
                raise ValueError("duplicate query")
            if kind == "m" and drug not in mol:
                raise ValueError("molecular query unavailable")
            cost = 1.0 if kind == "f" else lam
            if cost > remaining + 1e-9:
                raise ValueError("query exceeds authoritative budget")
            value = labels[drug] if kind == "f" else mol[drug]
            before, before_id = dict(predictions), _model_id(backend)
            observed[drug] = _json_copy(value)
            event = {"step": step, "kind": kind, "drug": drug, "value": _json_copy(value),
                     "cost": cost, "model_before": before_id, "predictions_before": before}
            trace.append(event)
            diagnostics = backend.observe(kind, drug, _json_copy(value)) if backend is not None else {"updated": False}
            predictions = _predictions(episode, backend, drugs)
            event.update(model_after=_model_id(backend), predictions_after=dict(predictions),
                         update=_json_copy(diagnostics),
                         prediction_max_abs_change=max(abs(predictions[d] - before[d]) for d in drugs))
    except subprocess.TimeoutExpired:
        error = "timeout"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"[:1000]
    # Neither the child nor its returned object can set any of these quantities.
    return {
        **provenance,
        "episode_id": episode.get("episode_id") if isinstance(episode, dict) else None,
        "status": "invalid" if error else "ok", "error": error,
        "yield": None if error else sum(int(row["value"]) for row in trace if row["kind"] == "f"),
        "spent": sum(row["cost"] for row in trace),
        "f_used": sum(row["kind"] == "f" for row in trace),
        "m_used": sum(row["kind"] == "m" for row in trace),
        "trace": trace, "predictions": predictions, "stop_reason": "invalid" if error else stop_reason,
        "candidate_seconds": candidate_seconds, "wall_seconds": time.monotonic() - started,
    }


def _worker():
    try:
        request = json.loads(sys.stdin.read())
        namespace = {"__builtins__": SAFE_BUILTINS, **SAFE_NUMERIC}
        exec(compile(check_source(request["source"]), "<candidate>", "exec"), namespace)
        action = namespace["choose"](request["observation"])
        output = json.dumps({"ok": True, "action": action}, allow_nan=False)
    except Exception as exc:
        output = json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"[:1000]})
    sys.stdout.write(output)


if __name__ == "__main__" and sys.argv[1:] == ["--worker"]:
    _worker()
