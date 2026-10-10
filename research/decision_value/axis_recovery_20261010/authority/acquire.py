"""Bounded public authority search: retained bodies, no expression or messages."""
import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
CAP = 5_000_000


def fetch(spec, budget):
    name, url = spec
    path = HERE / "sources" / name
    old = budget["records"].get(name)
    if old is not None: return old
    received, pieces = 0, []
    record = dict(name=name, public_url=url)
    try:
        with requests.get(url, timeout=(15, 35), stream=True, headers={"User-Agent": "MAESTRO-axis-authority-audit/1"}) as response:
            record["http_status"] = response.status_code
            for chunk in response.iter_content(65536):
                received += len(chunk)
                with budget["lock"]:
                    budget["all_received"] += len(chunk)
                    if response.status_code == 200:
                        budget["successful"] += len(chunk)
                    if budget["successful"] > CAP:
                        raise RuntimeError("successful_body_cap_exceeded")
                if received > 1_500_000: raise RuntimeError("single_source_cap_exceeded")
                pieces.append(chunk)
            value = b"".join(pieces)
            path.write_bytes(value)
            record.update(status="retained" if response.status_code == 200 else "failed_HTTP_retained",
                          bytes=received, sha256=hashlib.sha256(value).hexdigest(), path=path.relative_to(HERE).as_posix())
    except Exception as exc:
        record.update(status="failed", error_type=type(exc).__name__, received_bytes_before_failure=received,
                      error=str(exc) if isinstance(exc, RuntimeError) else "Network request failed; signed redirects are not recorded.")
    with budget["lock"]:
        budget["records"][name] = record
    return record


def run(specs):
    (HERE / "sources").mkdir(parents=True, exist_ok=True)
    path = HERE / "RECEIPTS.json"
    previous = json.loads(path.read_text()) if path.exists() else {}
    budget = dict(lock=threading.Lock(), records={row["name"]: row for row in previous.get("records", [])},
                  successful=previous.get("successful_body_bytes", 0), all_received=previous.get("known_all_received_body_bytes", 0))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda spec: fetch(spec, budget), specs))
    out = dict(schema="public_axis_authority_receipts_v1", successful_body_cap_bytes=CAP,
               successful_body_bytes=budget["successful"], known_all_received_body_bytes=budget["all_received"],
               records=list(budget["records"].values()), expression_data_requested=False, maintainer_messages_sent=False)
    path.write_text(json.dumps(out, indent=2)+"\n", encoding="utf-8")
    for record in results: print(json.dumps({k: record.get(k) for k in ("name", "http_status", "status", "bytes", "error_type")}), flush=True)


if __name__ == "__main__":
    dataset_rev = "fdf87abece385feea6fa5e9944ab46e173b6af50"
    model_rev = "ca6b751972493f8448e3256d1340ae70ad43e1e7"
    run([
        ("DATASET_INFO.json", f"https://huggingface.co/api/datasets/arcinstitute/State-Tahoe-Filtered/revision/{dataset_rev}"),
        ("DATASET_TREE.json", f"https://huggingface.co/api/datasets/arcinstitute/State-Tahoe-Filtered/tree/{dataset_rev}?recursive=true&limit=100"),
        ("MODEL_INFO.json", f"https://huggingface.co/api/models/arcinstitute/ST-HVG-Tahoe/revision/{model_rev}"),
        ("MODEL_TREE.json", f"https://huggingface.co/api/models/arcinstitute/ST-HVG-Tahoe/tree/{model_rev}?recursive=true&limit=100"),
        ("STATE_REPO.json", "https://api.github.com/repos/ArcInstitute/state"),
        ("STATE_TREE.json", "https://api.github.com/repos/ArcInstitute/state/git/trees/main?recursive=1"),
        ("STATE_ISSUE279.json", "https://api.github.com/repos/ArcInstitute/state/issues/279"),
        ("STATE_ISSUE279_COMMENTS.json", "https://api.github.com/repos/ArcInstitute/state/issues/279/comments?per_page=100"),
    ])
