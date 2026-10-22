"""Inspect exact primary figure identities and retain two original images."""
import hashlib
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import re
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "log/20261022/chemical_genetics_qualification"
OUT = BASE / "graphics"
OUT.mkdir(exist_ok=False)
article = ET.parse(BASE / "sources/PAPER.xml").getroot()
archive_path = BASE / "workbook_identity/supplementaryFiles.raw.zip"
records = []
with zipfile.ZipFile(archive_path) as archive:
    for fig in article.iter("fig"):
        if fig.get("id") not in {"Fig5", "Fig11"}:
            continue
        refs = [g.attrib for g in fig.iter("graphic")]
        stems = {PurePosixPath(value).stem for g in refs for key, value in g.items()
                 if key.endswith("href")}
        candidates = []
        for member in archive.infolist():
            name = PurePosixPath(member.filename)
            if name.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                continue
            # Publisher representations add suffixes such as _HTML to a graphic stem.
            if not any(re.fullmatch(re.escape(stem) + r"(?:_HTML)?", name.stem) for stem in stems):
                continue
            data = archive.read(member)
            with Image.open(BytesIO(data)) as img:
                width, height = img.size
            candidates.append({"member": member.filename, "width": width, "height": height,
                               "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        record = {"id": fig.get("id"), "label": " ".join(fig.find("label").itertext()),
                  "graphic_references": refs, "candidates": candidates}
        if candidates:
            chosen = max(candidates, key=lambda item: item["width"] * item["height"])
            destination = OUT / PurePosixPath(chosen["member"]).name
            destination.write_bytes(archive.read(chosen["member"]))
            record["selected"] = {**chosen, "path": str(destination)}
        records.append(record)
result = {"scope": "PUBLIC_FIGURE_IDENTITY_AND_VISUAL_SOURCE_CHECK", "figures": records,
          "archive_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
          "http_requests": 0, "response_arrays_digitised": False}
(OUT / "INVENTORY.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
