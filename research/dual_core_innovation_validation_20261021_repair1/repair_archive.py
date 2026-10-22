"""Small DGM-inspired program archive; evaluation remains outside this module."""
import copy
import hashlib
import json
import math
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False,
                                    separators=(",", ":")).encode()).hexdigest()


def source_hash(source):
    return hashlib.sha256(source.encode()).hexdigest()


def checked_evidence(results):
    """Use for both selection and proposer evidence; a fault is never a zero."""
    if not results:
        raise ValueError("empty evaluation")
    episodes = []
    for index, result in enumerate(results):
        if not isinstance(result, dict):
            raise ValueError("evaluation must be an object")
        if result.get("status") != "ok" or result.get("error") is not None:
            raise ValueError(f"invalid evaluation {index}: {result.get('error')}")
        value = result.get("yield")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("yield must be a finite nonnegative number")
        if not math.isfinite(value) or value < 0:
            raise ValueError("yield must be a finite nonnegative number")
        if not isinstance(result.get("trace"), list):
            raise ValueError("missing authoritative action trace")
        for key in ("source_sha256", "evaluation_context_sha256"):
            value_hash = result.get(key)
            if (not isinstance(value_hash, str) or len(value_hash) != 64
                    or any(c not in "0123456789abcdef" for c in value_hash)):
                raise ValueError(f"missing or malformed {key}")
        episodes.append({"episode_id": result.get("episode_id", str(index)),
                         "yield": float(value), "trace": copy.deepcopy(result["trace"]),
                         "source_sha256": result["source_sha256"],
                         "evaluation_context_sha256": result["evaluation_context_sha256"]})
    ids = [x["episode_id"] for x in episodes]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate episode ID")
    evidence = {"episodes": episodes,
                "mean_yield": sum(x["yield"] for x in episodes) / len(episodes)}
    # Full finite JSON check also prevents an unusable prompt from being stored.
    evidence["sha256"] = digest(evidence)
    return evidence


def _behavior(evidence):
    """Dedupe action sequences, not changing model IDs, scores, or wall time."""
    return [{"episode_id": e["episode_id"],
             "actions": [{"kind": t.get("kind"), "drug": t.get("drug")}
                         for t in e["trace"]]}
            for e in evidence["episodes"]]


def _check_source(evidence, expected):
    if any(e["source_sha256"] != expected for e in evidence["episodes"]):
        raise ValueError("evaluation source does not match the candidate program")


def _contexts(evidence):
    return [e["evaluation_context_sha256"] for e in evidence["episodes"]]


class Archive:
    """Retain valid distinct exploration branches; promotion is a separate gate.

    Counts describe search evaluations ingested by add(), including failed and
    behavior-duplicate candidates. Check needs_evaluation() BEFORE running a
    source. Reusing already computed results in promote() adds no compute.
    suite_id identifies one fixed ordered evaluation suite for this archive.
    """
    def __init__(self, *, mode="inherit", min_gain=0.0, suite_id="development"):
        if mode not in ("inherit", "restart"):
            raise ValueError("unknown mode")
        if not math.isfinite(min_gain) or min_gain < 0:
            raise ValueError("min_gain must be nonnegative")
        self.mode, self.min_gain, self.suite_id = mode, min_gain, suite_id
        self.nodes, self.attempts, self.promotions = {}, [], []
        self.root_id = self.deployed_id = None
        self.episode_ids = None
        self.episode_contexts = None

    @property
    def evaluation_count(self):
        return sum(x["episode_evaluations"] for x in self.attempts)

    @property
    def evaluated_candidates(self):
        return len(self.attempts)

    def needs_evaluation(self, source):
        return source_hash(source) not in {x["source_sha256"] for x in self.attempts}

    def add(self, source, results, parent_id=None):
        code_hash = source_hash(source)
        previous = next((x for x in self.attempts if x["source_sha256"] == code_hash), None)
        if previous:
            if results is not None:
                raise ValueError("duplicate source: check needs_evaluation before evaluating")
            return {"status": "duplicate_source", "id": previous.get("id"), "accepted": False}
        if self.root_id is None:
            if parent_id is not None:
                raise ValueError("initial program cannot inherit")
        elif parent_id not in self.nodes:
            raise ValueError("parent must be a retained valid program")
        elif self.mode == "restart" and parent_id != self.root_id:
            raise ValueError("restart control cannot inherit an evolved program")
        if results is None:
            raise ValueError("new source requires evaluation")
        attempt = {"source_sha256": code_hash, "parent_id": parent_id,
                   "episode_evaluations": len(results), "status": "invalid"}
        self.attempts.append(attempt)
        try:
            evidence = checked_evidence(results)
            _check_source(evidence, code_hash)
            episode_ids = [x["episode_id"] for x in evidence["episodes"]]
            if self.episode_ids is not None and episode_ids != self.episode_ids:
                raise ValueError("archive candidates must use the same ordered episode suite")
            if self.episode_contexts is not None and _contexts(evidence) != self.episode_contexts:
                raise ValueError("archive candidates must use the same evaluation contexts")
        except ValueError as exc:
            attempt["error"] = str(exc)
            raise
        self.episode_ids = episode_ids
        self.episode_contexts = _contexts(evidence)
        behavior_hash = digest(_behavior(evidence))
        previous = next((n for n in self.nodes.values()
                         if n["behavior_sha256"] == behavior_hash), None)
        if previous:
            attempt.update(status="duplicate_behavior", id=previous["id"])
            return {"status": "duplicate_behavior", "id": previous["id"], "accepted": False}
        node_id = "p" + str(len(self.nodes))
        self.nodes[node_id] = {
            "id": node_id, "source": source, "source_sha256": code_hash,
            "parent_id": parent_id, "behavior_sha256": behavior_hash,
            "evidence": evidence, "mean_yield": evidence["mean_yield"],
            "generation": 0 if parent_id is None else self.nodes[parent_id]["generation"] + 1,
            "parent_selections": 0,
        }
        attempt.update(status="added", id=node_id)
        if self.root_id is None:
            self.root_id = self.deployed_id = node_id
        return {"status": "added", "id": node_id, "accepted": node_id == self.deployed_id}

    def select_parent(self):
        if self.root_id is None:
            raise ValueError("archive is empty")
        if self.mode == "restart":
            node = self.nodes[self.root_id]
        else:
            # Deterministic exploration: under-selected branches precede score.
            node = min(self.nodes.values(), key=lambda n: (
                n["parent_selections"],
                sum(child["parent_id"] == n["id"] for child in self.nodes.values()),
                -n["mean_yield"], n["id"]))
        node["parent_selections"] += 1
        return copy.deepcopy(node)

    def lineage(self, node_id):
        path = []
        while node_id is not None:
            node = self.nodes[node_id]
            path.append(node_id)
            node_id = node["parent_id"]
        return path[::-1]

    def promote(self, node_id, validation_results, incumbent_results):
        """Strict positive paired mean gain gate; no claim of significance.

        Caller controls data isolation. Reused search data MUST be reported as
        development selection, not independent validation. Comparators must be
        results from the CURRENT deployed program on identical episodes.
        """
        if node_id not in self.nodes:
            raise ValueError("unknown candidate")
        candidate = checked_evidence(validation_results)
        incumbent = checked_evidence(incumbent_results)
        _check_source(candidate, self.nodes[node_id]["source_sha256"])
        _check_source(incumbent, self.nodes[self.deployed_id]["source_sha256"])
        if ([x["episode_id"] for x in candidate["episodes"]] !=
                [x["episode_id"] for x in incumbent["episodes"]]):
            raise ValueError("promotion requires paired identical episode IDs")
        if _contexts(candidate) != _contexts(incumbent):
            raise ValueError("promotion requires paired identical evaluation contexts")
        gain = candidate["mean_yield"] - incumbent["mean_yield"]
        accepted = node_id != self.deployed_id and gain > self.min_gain
        record = {"candidate_id": node_id, "incumbent_id": self.deployed_id,
                  "gain": gain, "min_gain": self.min_gain, "accepted": accepted,
                  "candidate_evidence_sha256": candidate["sha256"],
                  "incumbent_evidence_sha256": incumbent["sha256"]}
        self.promotions.append(record)
        if accepted:
            self.deployed_id = node_id
        return copy.deepcopy(record)

    def save(self, path):
        Path(path).write_text(json.dumps({"version": 1, **self.__dict__},
                                        indent=2, sort_keys=True, allow_nan=False) + "\n",
                              encoding="utf-8")

    @classmethod
    def load(cls, path):
        state = json.loads(Path(path).read_text(encoding="utf-8"))
        if state.pop("version") != 1:
            raise ValueError("unsupported archive version")
        archive = cls(mode=state["mode"], min_gain=state["min_gain"], suite_id=state["suite_id"])
        archive.__dict__.update(state)
        if archive.nodes and (archive.root_id not in archive.nodes or archive.deployed_id not in archive.nodes):
            raise ValueError("corrupt root or deployment ID")
        for node_id, node in archive.nodes.items():
            if node["id"] != node_id:
                raise ValueError("corrupt archive ID")
            if source_hash(node["source"]) != node["source_sha256"]:
                raise ValueError("corrupt archived source")
            evidence = copy.deepcopy(node["evidence"])
            evidence_hash = evidence.pop("sha256")
            if digest(evidence) != evidence_hash or digest(_behavior(evidence)) != node["behavior_sha256"]:
                raise ValueError("corrupt archived evidence or behavior")
            _check_source(evidence, node["source_sha256"])
            if ([e["episode_id"] for e in evidence["episodes"]] != archive.episode_ids
                    or _contexts(evidence) != archive.episode_contexts):
                raise ValueError("corrupt archived evaluation suite")
            score = sum(e["yield"] for e in evidence["episodes"]) / len(evidence["episodes"])
            if score != node["mean_yield"] or score != evidence["mean_yield"]:
                raise ValueError("corrupt archived score")
            seen, current = set(), node_id
            while current is not None:
                if current in seen or current not in archive.nodes:
                    raise ValueError("corrupt archive ancestry")
                seen.add(current)
                parent = archive.nodes[current]["parent_id"]
                if parent is None and current != archive.root_id:
                    raise ValueError("corrupt archive root")
                current = parent
            if node["generation"] != len(seen) - 1:
                raise ValueError("corrupt archive generation")
            if archive.mode == "restart" and node_id != archive.root_id and node["parent_id"] != archive.root_id:
                raise ValueError("restart archive contains inherited lineage")
        return archive
