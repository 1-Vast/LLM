"""Stream rows from an .xlsx worksheet with the standard library only.

File summary
- Path: research/certified_discovery/xlsx.py
- Purpose: read the O'Neil 2016 supplementary workbooks without adding a spreadsheet
  dependency to the maestro environment.
- Core points: shared strings are resolved once; rows are streamed with iterparse and cleared,
  so a 229 MB sheet never sits in memory; cell positions come from the cell reference, so blank
  cells keep their column.
- Interfaces: `iter_rows(path, sheet=1)` yields lists of strings or None.
- Depends on: standard library only.
"""
from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterator

_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_LETTERS = re.compile(r"[A-Z]+")


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return ["".join(t.text or "" for t in item.iter(_NS + "t")) for item in root.iter(_NS + "si")]


def _column(reference: str) -> int:
    number = 0
    for letter in _LETTERS.match(reference).group(0):
        number = number * 26 + ord(letter) - 64
    return number - 1


def iter_rows(path: str | Path, sheet: int = 1) -> Iterator[list[str | None]]:
    """Yield each worksheet row as a list indexed by column position."""
    with zipfile.ZipFile(path) as archive:
        strings = _shared_strings(archive)
        with archive.open(f"xl/worksheets/sheet{sheet}.xml") as handle:
            for _, element in ET.iterparse(handle, events=("end",)):
                if element.tag != _NS + "row":
                    continue
                cells: dict[int, str | None] = {}
                for cell in element.iter(_NS + "c"):
                    value = cell.find(_NS + "v")
                    if value is None:
                        inline = cell.find(_NS + "is")
                        text = None if inline is None else "".join(t.text or "" for t in inline.iter(_NS + "t"))
                    elif cell.get("t") == "s":
                        text = strings[int(value.text)]
                    else:
                        text = value.text
                    cells[_column(cell.get("r"))] = text
                width = max(cells) + 1 if cells else 0
                yield [cells.get(index) for index in range(width)]
                element.clear()
