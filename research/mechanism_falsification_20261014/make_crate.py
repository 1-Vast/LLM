"""Write ro-crate-metadata.json: an RO-Crate-style manifest of this study's files and the external assets it read.

Every local file carries its sha256. Every external asset carries its authentication status from ASSET_AUTH*.json
(VERIFIED against an upstream digest, LOCAL_DIGEST_ONLY, MISMATCH or ASSET_MISSING); the manifest does not upgrade
a status. The crate records what was read; it does not say the data are true.

    python research/mechanism_falsification_20261014/make_crate.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

STUDY = Path(__file__).resolve().parent
OUT = STUDY / "ro-crate-metadata.json"
SKIP = {"ro-crate-metadata.json", "__pycache__"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> None:
    graph = [{"@id": "ro-crate-metadata.json", "@type": "CreativeWork", "about": {"@id": "./"},
              "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"}},
             {"@id": "./", "@type": "Dataset", "name": "MAESTRO mechanism-falsification study, 2026-10-14",
              "description": "Contract repair, A0 data-feasibility census, conformal triage review and evidence-boundary benchmark. "
                             "No confirmatory experiment was run; no sealed outcome, paid call or new download was used.",
              "datePublished": "2026-10-14", "hasPart": []}]
    for path in sorted(p for p in STUDY.iterdir() if p.is_file() and p.name not in SKIP):
        graph[1]["hasPart"].append({"@id": path.name})
        graph.append({"@id": path.name, "@type": "File", "contentSize": path.stat().st_size, "sha256": sha256(path),
                      "digestRule": "lf_normalised"})
    for name in ("ASSET_AUTH.json", "ASSET_AUTH_LARGE.json"):
        for row in json.loads((STUDY / name).read_text(encoding="utf-8"))["assets"]:
            entry = {"@id": f"external:{row['path']}", "@type": "File", "contentSize": row.get("bytes"),
                     "authenticationStatus": row["status"], "source": name}
            for key in ("sha512", "sha256", "upstream_sha512"):
                if row.get(key):
                    entry[key] = row[key]
            graph.append(entry)
    OUT.write_text(json.dumps({"@context": "https://w3id.org/ro/crate/1.1/context", "@graph": graph}, indent=1) + "\n",
                   encoding="utf-8", newline="\n")
    print(f"{len(graph)} entries")


if __name__ == "__main__":
    main()
