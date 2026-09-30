"""Publish byte-verifiable follow-up receipts without rewriting local results."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 << 20), b""):
            value.update(block)
    return value.hexdigest()


def snapshot(source, output):
    source, output = source.resolve(), output.resolve()
    files = sorted(p for p in source.rglob("*") if p.is_file())
    if not files or output == source or source in output.parents:
        raise ValueError("publication_requires_separate_nonempty_source")
    output.mkdir(parents=True, exist_ok=False)
    records = []
    for original in files:
        relative = original.relative_to(source)
        # Large compressed call banks remain in the registered local archive.
        # Episode paths, tables and manifests are independently publishable.
        incomplete = original.parent.name in {"full", "probe"} and not (original.parent / "run_record.json").is_file()
        if original.suffix == ".gz" and (original.stat().st_size > (45 << 20) or incomplete):
            records.append({"local_file": str(original.relative_to(ROOT)), "published_file": None,
                            "encoding": "local_only_incomplete_stage" if incomplete else "local_only_large_compressed_bank",
                            "original_sha256": sha(original),
                            "original_bytes": original.stat().st_size, "published_bytes": 0})
            continue
        compress = original.stat().st_size > (2 << 20) and original.suffix != ".gz"
        target = output / (str(relative) + ".gz" if compress else relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        original_sha = sha(original)
        if compress:
            with original.open("rb") as stream, target.open("xb") as raw:
                with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
                    shutil.copyfileobj(stream, zipped, 4 << 20)
            restored = hashlib.sha256()
            with gzip.open(target, "rb") as stream:
                for block in iter(lambda: stream.read(4 << 20), b""):
                    restored.update(block)
            if restored.hexdigest() != original_sha:
                raise RuntimeError("published_compression_content_mismatch")
        else:
            with original.open("rb") as stream, target.open("xb") as dest:
                shutil.copyfileobj(stream, dest, 4 << 20)
            if sha(target) != original_sha:
                raise RuntimeError("published_copy_content_mismatch")
        if sha(original) != original_sha:
            raise RuntimeError("source_changed_during_publication")
        records.append({"local_file": str(original.relative_to(ROOT)),
                        "published_file": target.relative_to(output).as_posix(),
                        "encoding": "gzip_of_original_bytes" if compress else "original_bytes",
                        "original_sha256": original_sha, "published_sha256": sha(target),
                        "original_bytes": original.stat().st_size, "published_bytes": target.stat().st_size})
    (output / ".gitattributes").write_text("* -text whitespace=cr-at-eol\n*.txt -diff\n*.xml -diff\n", encoding="utf-8")
    manifest = {"created_utc": datetime.now(timezone.utc).isoformat(), "command": [sys.executable, *sys.argv],
                "git_parent": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "publisher_sha256": sha(Path(__file__)), "source": str(source.relative_to(ROOT)),
                "files": records, "note": "Original experiment files are retained. Published gzip copies decompress to exact original bytes. Compressed banks larger than 45 MiB and interrupted-stage banks stay local with full hashes; no truncated bank is presented as complete."}
    with (output / "manifest.json").open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"files": len(records), "published_bytes": sum(r["published_bytes"] for r in records)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    snapshot(arguments.source, arguments.out)
