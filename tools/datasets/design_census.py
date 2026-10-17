"""Design-only census of a long-format screening table: who was tested on what, never how it responded.

File summary
- Path: tools/datasets/design_census.py
- Purpose: before a protocol is frozen on a new domain, count contexts, dependence groups, items
  and measured pairs while reading only identifier and design columns. Outcome columns are
  never parsed, so the census cannot leak results into design choices.
- Core points:
  - ``--columns`` names the columns that may be read. The context, group and item columns must
    be among them. pandas ``usecols`` enforces this, so no other column is parsed.
  - ``--feature-header`` optionally reads only the header of a feature matrix. That counts the
    contexts that have pre-treatment features.
  - The output reports the read columns, the counts, the measured-pair rate and the digests of
    the input files, so a later run can prove it used the same bytes.
  - The ``beataml`` preset reproduces `research/context_transfer_20261017/census.py` on the Beat
    AML 2.0 curve-fit table (subject, RNA-seq sample, inhibitor).
- Interfaces: `census(table, columns, context, group, item, feature_header=None)`;
  `python -m tools.datasets.design_census TABLE --out census.json [--preset beataml]`.
- Depends on: pandas (the research extra).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PRESETS = {
    "beataml": {"columns": ["dbgap_subject_id", "dbgap_dnaseq_sample", "dbgap_rnaseq_sample", "inhibitor",
                            "type", "status", "paper_inclusion"],
                "context": "dbgap_rnaseq_sample", "group": "dbgap_subject_id", "item": "inhibitor"},
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def census(table, columns, context, group, item, feature_header=None, sep="\t") -> dict:
    import pandas as pd

    for name in (context, group, item):
        if name not in columns:
            raise ValueError(f"{name!r} must be one of the declared design columns")
    d = pd.read_csv(table, sep=sep, usecols=list(columns), dtype=str)
    out = {"read_columns": list(columns), "rows": int(len(d)), "contexts": int(d[context].nunique()),
           "groups": int(d[group].nunique()), "items": int(d[item].nunique())}
    if feature_header is not None:
        header = set(pd.read_csv(feature_header, sep=sep, nrows=0).columns.tolist())
        d = d[d[context].isin(header)]
        out["rows_with_features"] = int(len(d))
        out["contexts_with_features"] = int(d[context].nunique())
        out["groups_with_features"] = int(d[group].nunique())
    pairs = d.groupby([context, item]).size()
    per_item = d.groupby(item)[context].nunique()
    out["duplicate_pairs"] = int((pairs > 1).sum())
    out["measured_pair_rate"] = float(len(pairs) / max(d[context].nunique() * d[item].nunique(), 1))
    out["contexts_per_item"] = {"min": int(per_item.min()), "median": float(per_item.median()),
                                "max": int(per_item.max())}
    paths = [Path(table)] + ([Path(feature_header)] if feature_header is not None else [])
    out["sha256"] = {p.name: _sha256(p) for p in paths}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("table")
    ap.add_argument("--out", required=True)
    ap.add_argument("--preset", choices=sorted(PRESETS))
    ap.add_argument("--columns", nargs="+")
    ap.add_argument("--context")
    ap.add_argument("--group")
    ap.add_argument("--item")
    ap.add_argument("--feature-header")
    a = ap.parse_args(argv)
    cfg = dict(PRESETS[a.preset]) if a.preset else {}
    for key in ("columns", "context", "group", "item"):
        if getattr(a, key):
            cfg[key] = getattr(a, key)
    missing = [k for k in ("columns", "context", "group", "item") if k not in cfg]
    if missing:
        ap.error("missing " + ", ".join(missing))
    out = census(a.table, cfg["columns"], cfg["context"], cfg["group"], cfg["item"], a.feature_header)
    Path(a.out).write_bytes((json.dumps(out, indent=1) + "\n").encode("utf-8"))
    print(json.dumps({k: v for k, v in out.items() if k != "sha256"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
