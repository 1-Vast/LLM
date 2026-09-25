"""One way to open the agent's local SQLite stores.

File summary
- Path: src/agent/storage.py
- Purpose: give the case, evidence and memory stores a single connection helper that
  commits on success, rolls back on error, and always closes.
- Core points:
  - `with sqlite3.connect(...)` commits but leaves the connection open until garbage
    collection; on Windows an open handle keeps the database file locked, so a run
    directory could not be removed or moved while the process lived.
  - Row access is opt-in, so a store that reads rows positionally keeps plain tuples.
- Interfaces: `connect`
- Depends on: (standard library only)
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


@contextmanager
def connect(path: Path, *, rows: bool = True) -> Iterator[sqlite3.Connection]:
    """Yield a connection inside one transaction and close it afterwards."""

    connection = sqlite3.connect(path)
    if rows:
        connection.row_factory = sqlite3.Row
    try:
        with connection:
            yield connection
    finally:
        connection.close()
