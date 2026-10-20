"""Acquire the three official O'Neil supplements; verify bytes, never analyse responses."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.request
import zipfile

from tools.datasets.combination_screens import ONEIL_DIR

SOURCES = (
    (22503133, 39962566, 38829879, "d1b914b83d7ef475795731bec1d1e36e"),
    (22503127, 39962560, 1678111, "26c8ccbe68837d9c3bba967bb421e9fd"),
    (22503130, 39962563, 10430, "6992447cee5b60ee9f15efa209cc3bfe"),
)


def verify(path: Path, size: int, md5: str) -> dict:
    body = path.read_bytes()
    if len(body) != size or hashlib.md5(body).hexdigest() != md5:
        raise ValueError(f"Size/checksum mismatch: {path}")
    with zipfile.ZipFile(path) as archive:
        if "xl/workbook.xml" not in archive.namelist() or archive.testzip():
            raise ValueError(f"Invalid OOXML workbook: {path}")
    return dict(bytes=len(body), md5=md5, sha256=hashlib.sha256(body).hexdigest(), format="OOXML/xlsx")


def get(url: str, size: int | None = None) -> bytes:
    if size is not None:
        # Public range GETs avoid slow/stalled full-body transfers on this host.
        # Final published size/MD5, not the transfer method, authenticates the file.
        def part(start: int) -> bytes:
            end = min(start + 256 * 1024, size) - 1
            result = subprocess.run(
                ["curl.exe", "-sS", "-L", "--fail", "--retry", "2", "--retry-all-errors",
                 "--connect-timeout", "15", "--max-time", "80",
                 "--range", f"{start}-{end}", f"{url}?part={start}"],
                capture_output=True, check=True,
            )
            if len(result.stdout) != end - start + 1:
                raise ValueError(f"Incomplete range {start}-{end}: {url}")
            return result.stdout

        with ThreadPoolExecutor(max_workers=4) as pool:
            return b"".join(pool.map(part, range(0, size, 256 * 1024)))
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=90) as response:
                return response.read()
        except OSError:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ONEIL_DIR)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    receipts = []
    args.out.mkdir(parents=True, exist_ok=True)
    for article, file_id, size, md5 in SOURCES:
        metadata_path = args.out / f"figshare_{article}.json"
        if not args.verify_only:
            metadata_path.write_bytes(get(f"https://api.figshare.com/v2/articles/{article}"))
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        source = next(f for f in metadata["files"] if f["id"] == file_id)
        if source["size"] != size or source["computed_md5"] != md5:
            raise ValueError(f"Published metadata changed for {file_id}")
        path = args.out / source["name"]
        if not path.exists() and not args.verify_only:
            temporary = path.with_suffix(path.suffix + ".part")
            if temporary.exists():
                raise FileExistsError(temporary)
            temporary.write_bytes(get(source["download_url"], size))
            verify(temporary, size, md5)
            temporary.rename(path)
        receipts.append(dict(article=article, file_id=file_id, path=str(path.resolve()),
                             url=source["download_url"], version=metadata["version"],
                             exposure="exposed internal development", **verify(path, size, md5)))
    if not args.verify_only:
        (args.out / "SOURCE_RECEIPTS.json").write_text(json.dumps(receipts, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipts, indent=2))


if __name__ == "__main__":
    main()
