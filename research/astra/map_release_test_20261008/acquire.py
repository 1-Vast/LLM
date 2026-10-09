"""Acquire revision-pinned official MAP/STATE assets with per-file receipts."""
import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data/external/map_release_20261008"
REV = "5a9a80f44f7ce32ce57059933ef0d735d7c10ce5"
ASSETS = {
    "mapkg_encoder_v3.pt": {"drive": "18vL792x-g81SWCpzPvgUbHq3jbR45ttx"},
    "epoch_3.pt": {"drive": "13VTBSY3PXw1jU6y1ngGKF12hb_qvlKfr"},
    "gene_symbol_to_embedding_ESM2.pt": {"drive": "1unE_thvEPznBeKcLakzFueB9KW9jky47"},
    "se600m.safetensors": {
        "url": f"https://huggingface.co/arcinstitute/SE-600M/resolve/{REV}/model.safetensors",
        "bytes": 2860276816,
        "sha256": "3ebec58bd9e9c07f0a76de25b900dad13d015768fbff1e68e5dcbdfb3b2245de"},
    "protein_embeddings.pt": {
        "url": f"https://huggingface.co/arcinstitute/SE-600M/resolve/{REV}/protein_embeddings.pt",
        "bytes": 410886729,
        "sha256": "a210e1cc7901513999b2bca3836ba9e2f203cd008be4e9a9d6412a2267de9748"},
}


def download(item):
    name, spec = item
    dest = OUT / name
    receipt = {"name": name, "source": spec, "path": str(dest)}
    try:
        if dest.exists():
            receipt.update(status="existing", bytes=dest.stat().st_size,
                           sha256=hashlib.file_digest(dest.open("rb"), "sha256").hexdigest())
            if spec.get("sha256") and receipt["sha256"] != spec["sha256"]:
                raise ValueError("Existing asset hash mismatch")
            return receipt
        session = requests.Session()
        if "drive" in spec:
            url = f"https://drive.google.com/uc?export=download&id={spec['drive']}"
            r = session.get(url, timeout=40)
            fields = dict(re.findall(r'<input[^>]+name="([^"]+)"[^>]+value="([^"]*)"', r.text))
            action = re.search(r'<form[^>]+action="([^"]+)"', r.text)
            if not action or "confirm" not in fields:
                raise RuntimeError(f"Drive confirmation unavailable: HTTP{r.status_code}")
            url = unescape(action.group(1))
            r = session.get(url, params=fields, stream=True, timeout=(30, 60))
        else:
            r = session.get(spec["url"], stream=True, timeout=(30, 60))
        receipt["http_status"] = r.status_code
        r.raise_for_status()
        if "text/html" in r.headers.get("Content-Type", ""):
            raise RuntimeError("Asset request returned HTML rather than checkpoint bytes")
        receipt["content_disposition"] = r.headers.get("Content-Disposition")
        temporary = dest.with_suffix(dest.suffix + ".partial")
        digest, size, started, last = hashlib.sha256(), 0, time.monotonic(), time.monotonic()
        with temporary.open("wb") as handle:
            for chunk in r.iter_content(4 * 1024 * 1024):
                if not chunk:
                    continue
                handle.write(chunk)
                digest.update(chunk)
                size += len(chunk)
                if time.monotonic() - last >= 20:
                    print(name, round(size / 1e6), "MB", flush=True)
                    last = time.monotonic()
        if spec.get("bytes") and size != spec["bytes"]:
            raise ValueError("Downloaded byte count mismatch")
        if spec.get("sha256") and digest.hexdigest() != spec["sha256"]:
            raise ValueError("Published SHA256 mismatch")
        temporary.rename(dest)
        receipt.update(status="downloaded", bytes=size, sha256=digest.hexdigest(),
                       seconds=time.monotonic() - started,
                       integrity="Published LFS digest" if spec.get("sha256") else "Local digest; official Drive listing has no published SHA256")
        print(name, "complete", size, flush=True)
    except Exception as exc:
        receipt.update(status="blocked", error=f"{type(exc).__name__}: {exc}")
        print(name, receipt["error"], flush=True)
    finally:
        (OUT / f"{name}.receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return receipt


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        receipts = list(pool.map(download, ASSETS.items()))
    (OUT / "ACQUISITION.json").write_text(json.dumps(receipts, indent=2), encoding="utf-8")
    print(json.dumps(receipts, indent=2))


if __name__ == "__main__":
    main()
