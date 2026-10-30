"""Freeze metadata-only menu and ID roles before response inspection."""
from decimal import Decimal, localcontext
from pathlib import Path
import gzip
import hashlib
import json

HERE = Path(__file__).resolve().parent
path = HERE / "independent_metadata.json.gz"
rows = json.loads(gzip.decompress(path.read_bytes()))
rows = [r for r in rows if r["project"] == "2"]
drugs = sorted({r["drug"] for r in rows})
assert len(drugs) == 11
doses = {d: set() for d in drugs}
for row in rows:
    doses[row["drug"]].update(Decimal(q) for q in row["doses"])
with localcontext() as ctx:
    ctx.prec = 50
    selected = {d: min(doses[d], key=lambda q: (abs((q / Decimal("0.1")).ln()), q)) for d in drugs}
by_cell = {}
for row in rows:
    if selected[row["drug"]] in {Decimal(q) for q in row["doses"]}:
        by_cell.setdefault(row["cell"], {})[row["drug"]] = row["ref"]
cells = sorted(c for c, observations in by_cell.items() if len(observations) == 11)
assert len(cells) >= 200, "Metadata support gate not passed"


def bucket(prefix, cell, modulus):
    return int(hashlib.sha256((prefix + cell).encode("utf-8")).hexdigest(), 16) % modulus


records = []
for c in cells:
    records.append({"cell": c, "role": "train" if bucket("HFI-v1|", c, 10) < 7 else "development",
                    "inner_fold": bucket("HFI-inner-v1|", c, 5), "refs": by_cell[c]})
result = {"project": "2", "metadata_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
          "protocol_sha256": hashlib.sha256((HERE / "protocol_hfi_v1.md").read_bytes()).hexdigest(),
          "clarifications_sha256": hashlib.sha256((HERE / "protocol_clarifications.md").read_bytes()).hexdigest(),
          "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          "drugs": drugs, "doses_uM": {d: str(selected[d]) for d in drugs}, "cells": records,
          "metadata_eligible_cells": len(cells),
          "train_cells": sum(r["role"] == "train" for r in records),
          "development_cells": sum(r["role"] == "development" for r in records),
          "train_fold_counts": {str(i): sum(r["role"] == "train" and r["inner_fold"] == i for r in records) for i in range(5)},
          "response_values_accessed": False,
          "role_limit": "Deterministic archival development roles, not biological independence or fresh confirmation"}
with (HERE / "menu_roles_frozen.json").open("x", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
    f.write("\n")
print(json.dumps({k: result[k] for k in ["doses_uM", "metadata_eligible_cells", "train_cells", "development_cells"]}))
