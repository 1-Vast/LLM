"""Bounded sequential public-source retrieval; no response table inspection."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import requests

EPISODE = Path(__file__).resolve().parent
DEST = Path(r"D:\MAESTRO\data\external\conditional_interventions_20261030\dose")
RECEIPTS = EPISODE / "http_receipts.jsonl"
MAX_REQUESTS = 12
MAX_COMPLETED_BYTES = 50_000_000


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("name")
    parser.add_argument("--limit", type=int, default=2_000_000)
    args = parser.parse_args()
    prior = [json.loads(line) for line in RECEIPTS.read_text(encoding="utf-8").splitlines()] if RECEIPTS.exists() else []
    url = args.url
    DEST.mkdir(parents=True, exist_ok=True)
    for hop in range(6):
        if len(prior) >= MAX_REQUESTS:
            raise SystemExit("Request allocation exhausted")
        used = sum(row.get("completed_body_bytes", 0) for row in prior)
        if used >= MAX_COMPLETED_BYTES:
            raise SystemExit("Body allocation exhausted")
        if prior:
            time.sleep(max(0.0, prior[-1]["finished_unix"] + 1.05 - time.time()))
        row = {"request_number": len(prior) + 1, "url": url, "method": "GET", "started_unix": time.time(), "pass": 3}
        body = bytearray()
        limit = min(args.limit, MAX_COMPLETED_BYTES - used)
        try:
            with requests.get(url, timeout=(20, 45), allow_redirects=False, stream=True,
                              headers={"User-Agent": "MAESTRO-resource-admission/20261030", "Accept-Encoding": "identity"}) as response:
                row.update(status=response.status_code, headers=dict(response.headers))
                complete = True
                for chunk in response.iter_content(chunk_size=65536):
                    body.extend(chunk)
                    if len(body) > limit:
                        complete = False
                        break
                row["complete"] = complete
                row["received_body_bytes"] = len(body)
                row["completed_body_bytes"] = len(body) if complete else 0
                row["unknown_unread_body_bytes"] = not complete
                row["sha256_received"] = hashlib.sha256(body).hexdigest()
                name = args.name if hop == 0 else f"redirect{hop}_{args.name}"
                output = DEST / name
                output.write_bytes(body)
                row["saved_path"] = str(output)
                next_url = requests.compat.urljoin(url, response.headers.get("Location", "")) if response.is_redirect else None
        except requests.RequestException as error:
            row.update(error=repr(error), complete=False, completed_body_bytes=0,
                       received_body_bytes=len(body), unknown_partial_traffic=True)
            next_url = None
        row["finished_unix"] = time.time()
        with RECEIPTS.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        prior.append(row)
        print(json.dumps({k: v for k, v in row.items() if k != "headers"}, ensure_ascii=False))
        if not row.get("complete") or not next_url:
            break
        url = next_url


if __name__ == "__main__":
    main()
