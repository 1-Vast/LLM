"""Research-program environment.  The evaluator, outcome access, action legality and resource accounting live HERE, outside editable code.

A program is Python source defining run(env).  It may call only the public methods below.  Labels and measured states are private to the episode and
reachable only through paid queries.  Cost: a functional query costs 1.0 unit, a molecular query costs `lam` units, total budget is `budget` units.
Yield = number of DISTINCT drugs whose functional label was queried and is positive (confirmed positives count once).
"""
from __future__ import annotations
import ast, builtins, math, time
import numpy as np

ALLOWED_BUILTINS = {n: getattr(builtins, n) for n in
                    ["len", "range", "min", "max", "sum", "sorted", "abs", "round", "float", "int", "list", "dict", "set", "tuple", "enumerate",
                     "zip", "any", "all", "bool", "reversed", "isinstance", "str", "ValueError", "Exception", "StopIteration"]}
FORBIDDEN_CALLS = {"open", "eval", "exec", "compile", "getattr", "setattr", "delattr", "globals", "locals", "vars", "dir", "type", "input", "__import__"}


class BudgetError(RuntimeError):
    pass


class Episode:
    def __init__(self, drugs, W, prior, nn, sim, labels, mol=None, lam=0.5, budget=5.0):
        self.drugs = list(drugs)
        self.W = dict(W); self.prior = dict(prior); self.nn = dict(nn)
        self._sim = sim; self._labels = dict(labels); self._mol = dict(mol or {})
        self.lam = float(lam); self._budget = float(budget); self._spent = 0.0
        self._f = {}; self._m = {}; self.trace = []

    # ---- public API ------------------------------------------------------
    def left(self):
        return self._budget - self._spent

    def sim(self, a, b):
        return float(self._sim[a][b])

    def queried(self):
        return dict(self._f)

    def query_f(self, d):
        if d not in self._labels:
            raise ValueError("unavailable action")
        if d in self._f:
            return self._f[d]                       # re-reading a recorded label is free and creates no new information
        if self.left() < 1.0 - 1e-9:
            raise BudgetError("functional query exceeds budget")
        self._spent += 1.0; self._f[d] = int(self._labels[d]); self.trace.append(("f", d, self._f[d]))
        return self._f[d]

    def has_mol(self):
        return bool(self._mol) and self.lam < 1e9

    def query_m(self, d):
        if not self.has_mol() or d not in self._mol:
            raise ValueError("molecular query unavailable")
        if d in self._m:
            return self._m[d]
        if self.left() < self.lam - 1e-9:
            raise BudgetError("molecular query exceeds budget")
        self._spent += self.lam; self._m[d] = dict(self._mol[d]); self.trace.append(("m", d, round(self._m[d]["score"], 3)))
        return self._m[d]

    # ---- evaluator-side ---------------------------------------------------
    def result(self):
        hits = sum(v for v in self._f.values())
        return {"yield": int(hits), "f_used": len(self._f), "m_used": len(self._m), "spent": self._spent, "trace": self.trace}


def check_source(src: str):
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal, ast.AsyncFunctionDef, ast.Await)):
            raise ValueError(f"forbidden syntax {type(n).__name__}")
        if isinstance(n, ast.Attribute) and n.attr.startswith("_"):
            raise ValueError("private attribute access")
        if isinstance(n, ast.Name) and (n.id.startswith("__") or n.id in FORBIDDEN_CALLS):
            raise ValueError(f"forbidden name {n.id}")
    if not any(isinstance(n, ast.FunctionDef) and n.name == "run" for n in tree.body):
        raise ValueError("program must define run(env)")
    return tree


def _worker(src, ep_kwargs, q):
    try:
        ep = Episode(**ep_kwargs)
        ns = {"__builtins__": ALLOWED_BUILTINS, "math": math, "np": np}
        exec(compile(check_source(src), "<program>", "exec"), ns)
        try:
            ns["run"](ep)
            err = None
        except BudgetError as e:
            err = None                                   # attempting to overspend simply ends the episode
        r = ep.result(); r["error"] = err
        q.put(r)
    except Exception as e:                               # a failing program yields whatever it spent so far
        try:
            r = ep.result()
        except Exception:
            r = {"yield": 0, "f_used": 0, "m_used": 0, "spent": 0.0, "trace": []}
        r["error"] = f"{type(e).__name__}: {e}"
        q.put(r)


def run_program(src: str, ep_kwargs: dict, timeout=60.0, tries=3):
    """Run one program episode in a fresh interpreter (imports only numpy) so a hung or hostile program cannot affect the study process.
    A runner/process failure (empty or unreadable worker output) is an infrastructure fault, not a program result: it is retried and, if it persists,
    reported as error 'runner:...' so that callers can refuse to score it."""
    import pickle, subprocess, sys
    from pathlib import Path
    last = "runner"
    for _ in range(tries):
        try:
            cp = subprocess.run([sys.executable, str(Path(__file__)), "--worker"], input=pickle.dumps((src, ep_kwargs)), capture_output=True, timeout=timeout)
            return pickle.loads(cp.stdout)
        except subprocess.TimeoutExpired:
            return {"yield": 0, "f_used": 0, "m_used": 0, "spent": 0.0, "trace": [], "error": "timeout"}
        except Exception as e:
            last = f"runner: {type(e).__name__}"
    return {"yield": 0, "f_used": 0, "m_used": 0, "spent": 0.0, "trace": [], "error": last}


if __name__ == "__main__" and len(__import__("sys").argv) > 1 and __import__("sys").argv[1] == "--worker":
    import pickle, sys, queue
    src, kw = pickle.loads(sys.stdin.buffer.read())
    q = queue.Queue(); _worker(src, kw, q)
    sys.stdout.buffer.write(pickle.dumps(q.get()))
