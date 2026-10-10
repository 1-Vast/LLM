"""Independently reconstruct index-pattern diagnosis; no expression or network."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix

from .calibration_verify import RetainedFile, json_lines
from .calibration_v2_verify import uncovered


HERE = Path(__file__).resolve().parent
STAGE = HERE.parent / "calibration_v2"
DIAGNOSIS = STAGE / "diagnosis"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def group_patterns(matrix, rows, targets):
    """Pack bits over rows, including absent genes outside the endpoint panel."""
    packed = np.packbits(matrix[rows].toarray(), axis=0, bitorder="little")
    groups = {}
    keys = [packed[:, column].tobytes() for column in range(matrix.shape[1])]
    for column, key in enumerate(keys):
        groups.setdefault(key, set()).add(column)
    return [groups[keys[index]] for index in targets]


def verify():
    frozen = read(DIAGNOSIS / "FREEZE.json")
    for path, expected in frozen["sha256"].items():
        assert digest(STAGE / path) == expected
    protocol = read(DIAGNOSIS / "PROTOCOL.json")
    recorded = read(DIAGNOSIS / "RESULTS.json")
    endpoint = read(STAGE / "PROTOCOL.json")["endpoint"]
    assert protocol["new_network_calls"] == protocol["new_expression_value_reads"] == protocol["new_HVG_reads"] == 0
    ledger = json_lines(STAGE / "NETWORK.jsonl")+json_lines(STAGE / "CACHE_REUSE.jsonl")
    layouts = read(STAGE / "INDEX_LAYOUTS.json")
    groups = read(STAGE / "ROW_MANIFEST.json")["groups"]
    census = read(STAGE / "CENSUSES.json")
    original = read(STAGE / "RESULTS.json")
    summaries = []
    for file, jobs in layouts.items():
        names = read(STAGE / f"inputs/{file}_GENES.json")
        expected = [names.index(symbol) for symbol in endpoint["symbols"]]
        spans = []
        for entry in ledger:
            purpose = entry.get("purpose", entry.get("original_receipt", {}).get("purpose", ""))
            if entry["file"] != file or entry["status"] not in ("RETAINED", "REUSED") or not purpose.startswith("index_screen_"):
                continue
            body = (STAGE / entry["path"]).read_bytes()
            assert len(body) == entry["bytes"] and hashlib.sha256(body).hexdigest() == entry["sha256"]
            spans.append((entry["start"], body))
        source = RetainedFile(census[file]["file_bytes"], spans)
        indices, pointer = [], [0]
        for job in jobs:
            columns = np.frombuffer(b"".join(source.at(start, stop+1) for start, stop in job["indices"]), dtype="<i4")
            assert len(columns) == job["nnz"] == len(np.unique(columns))
            assert ((columns >= 0) & (columns < len(names))).all()
            indices.append(columns)
            pointer.append(pointer[-1]+len(columns))
        concatenated = np.concatenate(indices)
        matrix = csr_matrix((np.ones(len(concatenated), dtype=bool), concatenated, np.asarray(pointer)),
                            shape=(len(jobs), len(names)))
        matrix.sort_indices()
        row_lookup = {job["row"]: index for index, job in enumerate(jobs)}
        discovered = sorted(row for group in groups if group["file"] == file for row in group["discovery_rows"])
        holdout = {row for group in groups if group["file"] == file for row in group["holdout_rows"]}
        discovery = [row_lookup[row] for row in discovered]
        current = group_patterns(matrix, discovery, expected)
        complete = group_patterns(matrix, np.arange(len(jobs)), expected)
        competitors = [matching-{target} for matching, target in zip(current, expected)]
        available = set(range(len(jobs)))-set(discovery)-{row_lookup[row] for row in holdout}
        added, trace = [], []
        while any(competitors) and len(discovery)+len(added) < protocol["maximum_discovery_cells_per_file"]:
            alternatives = []
            for index in available:
                observed = set(indices[index])
                removed = [{rival for rival in rivals if (rival in observed) != (target in observed)}
                           for target, rivals in zip(expected, competitors)]
                score = sum((Fraction(len(gone), len(rivals)) for gone, rivals in zip(removed, competitors) if rivals), Fraction(0))
                if score:
                    key = f"{protocol['seed']}|{file}|{jobs[index]['row']}"
                    alternatives.append((-score, jobs[index]["nnz"]*4+8000, hashlib.sha256(key.encode()).hexdigest(), index, removed))
            if not alternatives:
                break
            winner = min(alternatives, key=lambda item: item[:4])
            index, removed = winner[3:]
            available.remove(index)
            added.append(index)
            trace.append(dict(row=jobs[index]["row"], separated_competitors=sum(map(len, removed)),
                              separated_endpoint_genes=sum(bool(item) for item in removed), presence_only_not_numerical_truth=True))
            competitors = [rivals-gone for rivals, gone in zip(competitors, removed)]
        augmented = group_patterns(matrix, discovery+added, expected)
        observed = next(item for item in recorded["files"] if item["file"] == file)
        assert observed["added_discovery_rows"] == [jobs[index]["row"] for index in added]
        assert observed["allocation_trace"] == trace
        assert observed["current_binary_unique_endpoint_genes"] == sum(len(item) == 1 for item in current)
        assert observed["full_pool_binary_unique_endpoint_genes"] == sum(len(item) == 1 for item in complete)
        assert observed["diagnostic_augmented_binary_unique_endpoint_genes"] == sum(len(item) == 1 for item in augmented)
        assert observed["index_pool_cells"] == len(jobs) and observed["source_genes"] == len(names)
        assert observed["added_discovery_cells"] == len(added) and observed["fixed_holdout_cells"] == len(holdout)
        numeric = next(item for item in original["files"] if item["file"] == file)
        for index, (target, a, b, c, record) in enumerate(zip(expected, current, complete, augmented, observed["endpoint_records"])):
            assert record["symbol"] == endpoint["symbols"][index] and record["source_gene_index"] == target
            assert record["binary_current_discovery_match_count"] == len(a)
            assert record["binary_full_pool_match_count"] == len(b)
            assert record["binary_diagnostic_augmented_match_count"] == len(c)
            assert record["current_binary_competitor_names"] == [names[column] for column in sorted(a-{target})]
            assert record["unresolved_full_pool_competitor_names"] == [names[column] for column in sorted(b-{target})]
            assert record["numeric_registered_discovery_match_count"] == numeric["endpoint_records"][index]["discovery_matching_source_gene_count"]
            assert record["registered_coordinate_passed"] == numeric["endpoint_records"][index]["passed"]
        cache = [(entry["start"], entry["end"]) for entry in ledger if entry["file"] == file and entry["status"] in ("RETAINED", "REUSED")]
        value_cost = uncovered([tuple(span) for index in added for span in jobs[index]["values"]], cache)
        offset = census[file]["layouts"]["obsm/X_hvg"]["offset"]
        hvg_cost = uncovered([(offset+jobs[index]["row"]*8000, offset+(jobs[index]["row"]+1)*8000-1) for index in added], cache)
        assert observed["additional_CSR_value_bytes_projected_only"] == value_cost
        assert observed["additional_HVG_bytes_projected_only"] == hvg_cost
        summaries.append(dict(file=file, retained_index_cells=len(jobs), current_binary_unique=sum(len(item) == 1 for item in current),
            full_pool_binary_unique=sum(len(item) == 1 for item in complete), augmented_binary_unique=sum(len(item) == 1 for item in augmented),
            additional_discovery_cells=len(added), projected_only_extra_bytes=value_cost+hvg_cost))
    projected = sum(summary["projected_only_extra_bytes"] for summary in summaries)
    assert recorded["additional_paired_body_bytes_projected_only"] == projected == 340_068
    assert recorded["new_network_calls"] == recorded["new_CSR_value_reads"] == recorded["new_HVG_reads"] == 0
    assert recorded["axis_certification"] is False and recorded["P06_released"] is False
    verdict = dict(schema="independent_index_discrimination_diagnosis_v1", status="PASS_INDEPENDENT_OFFLINE_RECONSTRUCTION",
        reconstructed=summaries, projected_only_extra_bytes=projected, new_network_calls=0, new_expression_reads=0,
        producer_imports=False, axis_gate_released=False, original_certificate_status=read(STAGE / "CERTIFICATE.json")["status"],
        independent_culture_validation=False, decision_gain=None, verifier_sha256=digest(Path(__file__)),
        diagnosis_results_sha256=digest(DIAGNOSIS / "RESULTS.json"))
    with (HERE / "DIAGNOSIS_VERIFIED.json").open("x", encoding="utf-8") as stream:
        json.dump(verdict, stream, indent=2)
        stream.write("\n")
    print(json.dumps(verdict))
    return verdict


if __name__ == "__main__":
    verify()
