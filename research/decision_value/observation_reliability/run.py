"""Freeze and execute a control-only audit after endpoint-axis authentication."""
import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import requests

from .noise import audit_groups


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def authenticated_axis():
    certificate_path = HERE / "axis/CERTIFICATE.json"
    if not certificate_path.is_file():
        raise ValueError("BLOCKED/ENDPOINT_AXIS_CERTIFICATE_MISSING")
    certificate = read(certificate_path)
    plan = read(HERE / "CONTROL_PLAN.json")
    if (certificate.get("status") != "PASS"
            or certificate.get("endpoint39_verified") is not True
            or certificate.get("source_revision") != plan["revision"]
            or certificate.get("endpoint_definition_sha256") != digest(HERE / "ENDPOINT.json")
            or not {row["file"] for row in plan["selected"]}.issubset(certificate.get("source_files", []))):
        raise ValueError("BLOCKED/ENDPOINT_AXIS_AUTHENTICATION")
    mapping = ROOT / certificate["mapping_file"]
    if digest(mapping) != certificate["mapping_sha256"]:
        raise ValueError("BLOCKED/AXIS_MAPPING_HASH_MISMATCH")
    for name, field in (("PROTOCOL.json", "protocol_sha256"), ("FREEZE.json", "freeze_sha256"), ("RESULTS.json", "results_sha256")):
        if certificate.get(field) != digest(HERE / "axis" / name):
            raise ValueError("BLOCKED/AXIS_CERTIFICATE_INPUT_HASH_MISMATCH")
    names = read(mapping)["names"]
    endpoint = read(HERE / "ENDPOINT.json")
    if (len(names) != 2000 or any(names[index] != symbol for index, symbol in zip(endpoint["coordinates"], endpoint["symbols"]))
            or any(certificate.get("per_file_endpoint39_verified", {}).get(file) is not True for file in certificate["source_files"])):
        raise ValueError("BLOCKED/AXIS_ENDPOINT_MEANING_MISMATCH")
    return certificate


def freeze():
    destination = HERE / "FREEZE.json"
    if destination.exists():
        raise FileExistsError(destination)
    certificate = authenticated_axis()
    paths = [HERE / name for name in ("PROTOCOL.json", "CONTROL_PLAN.json", "ENDPOINT.json",
        "noise.py", "run.py", "verify.py", "shadow.py", "test_reliability.py", "axis/CERTIFICATE.json")]
    paths.append(ROOT / certificate["mapping_file"])
    for name in ("PROTOCOL.json", "FREEZE.json", "RESULTS.json"):
        paths.append(HERE / "axis" / name)
    inputs = {path.relative_to(ROOT).as_posix(): digest(path) for path in paths}
    write(destination, dict(schema="control_only_noise_freeze_v1",
        frozen_at_utc=datetime.now(timezone.utc).isoformat(),
        before_250_control_RNA_read=True, inputs=inputs,
        prior_exposure="V3 and axis-authentication controls are known; selected audit cells were not read."))
    return destination


def fetch_rows(file, rows, plan):
    group = next(item for item in plan["selected"] if item["file"] == file)
    offset = group["exact_x_hvg_ranges"][0]["start"] - group["rows"][0] * 8000
    url = plan["source_url_template"].format(file=file)
    start, end = offset + rows[0] * 8000, offset + (rows[-1] + 1) * 8000 - 1
    with requests.get(url, params={"download": "true", "control_noise_span": f"{start}-{end}"},
            headers={"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"},
            stream=True, timeout=(20, 40)) as response:
        if response.status_code != 206 or not response.headers.get("Content-Range", "").startswith(f"bytes {start}-{end}/"):
            raise ValueError("exact_control_range_unavailable")
        blocks, size = [], 0
        for block in response.iter_content(65536):
            size += len(block)
            if size > end - start + 1:
                raise ValueError("control_range_exceeds_registered_size")
            blocks.append(block)
        payload = b"".join(blocks)
        if len(payload) != end - start + 1:
            raise ValueError("control_range_length_mismatch")
        receipt = dict(file=file, rows=rows, byte_start=start, byte_end=end,
            bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(),
            http_status=response.status_code, content_range=response.headers["Content-Range"],
            public_url=url, purpose="Previously registered DMSO reference cells only")
    return np.frombuffer(payload, dtype="<f4").reshape(len(rows), 2000).copy(), receipt


def execute(output):
    # Guard and frozen inputs are checked before creating any network request.
    certificate = authenticated_axis()
    frozen = read(HERE / "FREEZE.json")
    for path, expected in frozen["inputs"].items():
        if digest(ROOT / path) != expected:
            raise ValueError("frozen_noise_input_changed:" + path)
    protocol, plan, endpoint = [read(HERE / name) for name in ("PROTOCOL.json", "CONTROL_PLAN.json", "ENDPOINT.json")]
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    jobs = []
    for file in sorted({row["file"] for row in plan["selected"]}):
        rows = sorted(row for group in plan["selected"] if group["file"] == file for row in group["rows"])
        if len(rows) != len(set(rows)):
            raise ValueError("duplicate_registered_control_row")
        spans = []
        for row in rows:
            if spans and row == spans[-1][-1] + 1:
                spans[-1].append(row)
            else:
                spans.append([row])
        jobs.extend((file, span) for span in spans)
    matrices, receipts, failures = {}, [], []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [(file, rows, pool.submit(fetch_rows, file, rows, plan)) for file, rows in jobs]
        for file, rows, future in futures:
            try:
                values, receipt = future.result()
            except Exception as error:
                failures.append(dict(file=file, rows=rows, error=str(error)))
                continue
            receipts.append(receipt)
            for row, vector in zip(rows, values):
                matrices[(file, row)] = vector
    if failures:
        write(output / "FAILED.json", dict(status="BLOCKED/CONTROL_DOWNLOAD", failures=failures,
            completed_receipts=receipts, downloaded_body_bytes=sum(item["bytes"] for item in receipts)))
        raise ValueError("registered_control_ranges_incomplete")
    transferred = sum(item["bytes"] for item in receipts)
    if transferred != plan["planned_control_rna_bytes"] or transferred > protocol["control_RNA_byte_cap"]:
        raise ValueError("registered_control_payload_budget_mismatch")
    groups = [np.stack([matrices[(group["file"], row)] for row in group["rows"]]) for group in plan["selected"]]
    if any(not np.isfinite(group).all() for group in groups):
        raise ValueError("nonfinite_control_expression")
    arrays = {f"group_{index}": values for index, values in enumerate(groups)}
    np.savez_compressed(output / "CONTROLS.npz", **arrays)
    coordinates = endpoint["coordinates"]
    metadata = [{key: group[key] for key in ("file", "cell_name", "plate", "sample", "rows", "selected_cells")}
        for group in plan["selected"]]
    result = audit_groups([group[:, coordinates] for group in groups], endpoint["weights"], metadata,
        bootstrap_draws=protocol["bootstrap_draws"], seed=protocol["seed"])
    for row, values in zip(result["groups"], groups):
        # Keep the old different-endpoint proxy distinct from the scalar variance.
        legacy = float(np.var(values, axis=0, ddof=1).mean() / len(values))
        row["legacy_mean_2000gene_control_mean_variance"] = legacy
        row["scalar_to_legacy_different_endpoint_ratio"] = row["scalar_sample_mean_variance"] / legacy if legacy > 0 else None
    result.update(status="COMPLETED_CONTROL_NOISE_AUDIT_ONLY", axis_certificate=certificate,
        control_RNA_bytes=transferred, source_range_reads=len(receipts), treated_RNA_bytes=0,
        independent_culture_count=None, decision_gain=None, P2_release=False,
        all32_correction=[dict(group_index=row["group_index"], cells=row["cells"],
            variance_understatement_if_divided_by32=1-row["cells"] / 32) for row in result["groups"] if row["cells"] != 32])
    write(output / "RESULTS.json", result)
    write(output / "DOWNLOADS.json", receipts)
    write(output / "RUN_RECEIPT.json", dict(status="PASS_CONTROL_AUDIT", freeze_sha256=digest(HERE / "FREEZE.json"),
        outputs={path.name: digest(path) for path in output.iterdir() if path.is_file()},
        claim="Conditional control-cell sampling only; no A/B biological transfer or decision benefit."))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["freeze", "run"])
    parser.add_argument("--out", type=Path, default=ROOT / "outputs/decision_value/observation_reliability")
    args = parser.parse_args()
    result = str(freeze()) if args.phase == "freeze" else execute(args.out)
    print(result if isinstance(result, str) else json.dumps({key: result[key] for key in ("status", "control_RNA_bytes", "source_range_reads", "P2_release")}))


if __name__ == "__main__":
    main()
