"""Case-memory tool package with shared streaming file hashes."""
from __future__ import annotations

import hashlib
from pathlib import Path


def sha256(path: Path) -> str:
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def md5(path: Path) -> str:
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "md5").hexdigest()
