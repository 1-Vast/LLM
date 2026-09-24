"""A dependency-free reader for the release tables that ship as .xlsx.

File summary
- Path: src/evaluation/xlsx.py
- Purpose: read the local supplementary releases (PISA, GDSC2, kinobeads) without adding a
  third-party dependency, so case construction stays reproducible in the recorded
  environment. ``openpyxl`` is not installed and installing it would add an unrecorded
  dependency to every future reproduction of these numbers.
- Core points:
  - An .xlsx file is a zip of XML parts; sheets are streamed with ``iterparse`` so a
    172 MB worksheet is read without loading it into memory as a tree.
  - Cell values keep their declared type: a shared string, an inline string, a boolean or
    a number. A cell with no value is ``None`` rather than an empty string, because a
    missing measurement and an empty label are different facts.
  - Nothing here interprets a table. A caller that wants a measurement must name the
    sheet, the column and the row key it reads, which is what keeps provenance checkable.
- Interfaces: `Workbook`, `column_index`, `sheet_digest`
- Depends on: (standard library only)
"""
from __future__ import annotations

import hashlib
import re
import zipfile
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Iterator
from xml.etree.ElementTree import iterparse

_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_LETTERS = re.compile(r"[A-Z]+")


def column_index(reference: str) -> int:
    """Zero-based column index of a cell reference such as ``BK12``."""

    match = _LETTERS.match(reference)
    if match is None:
        raise ValueError(f"'{reference}' is not a cell reference.")
    value = 0
    for character in match.group(0):
        value = value * 26 + (ord(character) - 64)
    return value - 1


class Workbook:
    """One .xlsx file, opened lazily, with its sheets addressable by name.

    ``member`` reads a workbook that lives inside another archive, which is how the
    supplementary releases arrive. The bytes are read from the outer archive rather than
    unpacked to disk, so the provenance stays the digest of the file that was downloaded
    and no derived copy has to be kept in step with it.
    """

    def __init__(self, path: Path | str, *, member: str | None = None):
        self.path = Path(path)
        self.member = member
        if member is None:
            self._zip = zipfile.ZipFile(self.path)
        else:
            with zipfile.ZipFile(self.path) as outer:
                if member not in outer.namelist():
                    raise KeyError(f"'{self.path.name}' has no member '{member}'.")
                payload = outer.read(member)
            self._zip = zipfile.ZipFile(BytesIO(payload))
        self._shared: list[str] | None = None
        self._sheets = self._sheet_parts()

    def close(self) -> None:
        self._zip.close()

    def __enter__(self) -> "Workbook":
        return self

    def __exit__(self, *_exception) -> None:
        self.close()

    @property
    def sheet_names(self) -> tuple[str, ...]:
        return tuple(self._sheets)

    def _sheet_parts(self) -> dict[str, str]:
        workbook = self._zip.read("xl/workbook.xml").decode("utf-8")
        relations = self._zip.read("xl/_rels/workbook.xml.rels").decode("utf-8")
        targets: dict[str, str] = {}
        for element in re.finditer(r"<Relationship\b[^>]*>", relations):
            tag = element.group(0)
            identifier = re.search(r'Id="([^"]+)"', tag)
            target = re.search(r'Target="([^"]+)"', tag)
            if identifier and target:
                targets[identifier.group(1)] = target.group(1)
        parts: dict[str, str] = {}
        for element in re.finditer(r"<sheet\b[^>]*/>", workbook):
            tag = element.group(0)
            name = re.search(r'name="([^"]+)"', tag)
            identifier = re.search(r'r:id="([^"]+)"', tag)
            if name is None or identifier is None:
                continue
            target = targets.get(identifier.group(1))
            if target is None:
                continue
            target = target.lstrip("/")
            if not target.startswith("xl/"):
                target = str(PurePosixPath("xl") / target)
            parts[_unescape(name.group(1))] = target
        return parts

    def _shared_strings(self) -> list[str]:
        if self._shared is not None:
            return self._shared
        strings: list[str] = []
        if "xl/sharedStrings.xml" in self._zip.namelist():
            with self._zip.open("xl/sharedStrings.xml") as handle:
                for _event, element in iterparse(handle, events=("end",)):
                    if element.tag == _MAIN + "si":
                        strings.append("".join(node.text or "" for node in element.iter(_MAIN + "t")))
                        element.clear()
        self._shared = strings
        return strings

    def rows(self, sheet: str) -> Iterator[list[object | None]]:
        """Stream one sheet as lists of cell values, padded to the widest cell seen in the row."""

        if sheet not in self._sheets:
            raise KeyError(f"Workbook '{self.path.name}' has no sheet '{sheet}'.")
        shared = self._shared_strings()
        with self._zip.open(self._sheets[sheet]) as handle:
            for _event, element in iterparse(handle, events=("end",)):
                if element.tag != _MAIN + "row":
                    continue
                values: dict[int, object | None] = {}
                for cell in element.findall(_MAIN + "c"):
                    reference = cell.get("r")
                    if reference is None:
                        continue
                    values[column_index(reference)] = _cell_value(cell, shared)
                element.clear()
                if not values:
                    yield []
                    continue
                width = max(values) + 1
                yield [values.get(position) for position in range(width)]

    def sha256(self) -> str:
        """Digest of the file on disk, so a table can be cited by its bytes."""

        return sheet_digest(self.path)


def sheet_digest(path: Path | str, *, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()


def _cell_value(cell, shared: list[str]) -> object | None:
    kind = cell.get("t")
    if kind == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(_MAIN + "t"))
    value = cell.find(_MAIN + "v")
    if value is None or value.text is None:
        return None
    text = value.text
    if kind == "s":
        index = int(text)
        return shared[index] if 0 <= index < len(shared) else None
    if kind == "b":
        return text == "1"
    if kind in ("str", "e"):
        return text
    try:
        return float(text)
    except ValueError:
        return text


def _unescape(value: str) -> str:
    return (
        value.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&apos;", "'")
    )
