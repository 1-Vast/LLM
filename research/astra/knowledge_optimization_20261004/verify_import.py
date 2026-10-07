"""Verify the supplied archive, preserved freezes and saved campaign accounting.

This command reads receipts rather than rerunning outcome analyses or changing
the delivered verification file. Byte differences are reported, never refrozen.
"""
from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile


ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "research/astra/knowledge_transfer_20261004"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit(archive: Path) -> dict:
    differences = []
    checked = 0
    with zipfile.ZipFile(archive) as bundle:
        for item in bundle.infolist():
            if item.is_dir():
                continue
            path = PurePosixPath(item.filename)
            target = ROOT.joinpath(*path.parts).resolve()
            if path.is_absolute() or ".." in path.parts or not target.is_relative_to(STUDY):
                raise ValueError("Unexpected archive entry: " + item.filename)
            if not target.is_file() or target.read_bytes() != bundle.read(item):
                differences.append(item.filename)
            checked += 1
    if differences:
        raise ValueError("Archive byte mismatches: " + ", ".join(differences))
    split = json.loads((ROOT / "research/astra/confirmation_campaign_20261004/protocol/partition.json").read_text(encoding="utf-8"))["split"]
    stages = {}
    for stage in ("", "context", "interaction"):
        folder = STUDY / stage
        freeze = json.loads((folder / "freeze.json").read_text(encoding="utf-8"))
        newline_variations = []
        for name, expected in freeze["files"].items():
            source = (ROOT / name).resolve()
            if not source.is_relative_to(ROOT):
                raise ValueError("Freeze path outside checkout")
            raw = source.read_bytes()
            if digest(raw) != expected:
                if source.suffix not in (".py", ".md", ".json") or digest(raw.replace(b"\r\n", b"\n")) != expected:
                    raise ValueError("Unexplained frozen dependency difference: " + name)
                newline_variations.append({"path": name, "recorded_sha256": expected,
                                           "checkout_sha256": digest(raw), "comparison": "LF-equivalent, raw bytes differ"})
        per_line = defaultdict(list)
        count = 0
        with (folder / "results/campaigns.jsonl").open(encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                count += 1
                allowed = set(split[row["tissue"]]["HD"])
                if not set(row["history_lines"]) <= allowed or row["line"] in row["history_lines"]:
                    raise ValueError("Historical information boundary violated")
                group = "HD" if row["phase"] == "HD" else "E"
                if row["line"] not in split[row["tissue"]][group]:
                    raise ValueError("Target partition mismatch")
                if not len(row["screens"]) + len(row["verifies"]) == row["spent"] <= row["cap"]:
                    raise ValueError("Measurement accounting mismatch")
                if not set(row["verifies"]) <= set(row["screen_hits"]) <= set(row["screens"]):
                    raise ValueError("Illegal verification")
                if row["confirmed"] != len(set(row["verification_hits"]) & set(row["screen_hits"])):
                    raise ValueError("Confirmation count mismatch")
                if group == "E":
                    per_line[(row["regime"], row["arm"], row["tissue"], row["line"])].append(row["confirmed"])
        totals = defaultdict(float)
        for (regime, arm, tissue, sidm), values in per_line.items():
            totals[regime, arm] += sum(values) / len(values)
        summary = json.loads((folder / "results/summary.json").read_text(encoding="utf-8"))
        for regime, result in summary.items():
            for name, expected in result["totals"].items():
                if not stage:
                    arm = "C_mean" if name == "C_mean" else result["choices"]["simple"] if name == "simple_selected" else f'{name}:{result["choices"][name]:g}'
                else:
                    arm = "simple" if name == "simple" else f'{name}:{result["choices"][name]:g}'
                if abs(totals[regime, arm] - expected) > 1e-9:
                    raise ValueError("Reported total mismatch: " + name)
        stages[stage or "graph"] = {"records": count, "freeze_entries": len(freeze["files"]),
                                    "raw_byte_variations": newline_variations, "receipt_totals_match": True}
    return {"archive": str(archive.resolve()), "archive_sha256": digest(archive.read_bytes()),
            "archive_files_exact": checked, "stages": stages,
            "scope": "Receipt accounting; no model replay, independent-measurement or biological certification"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ROOT / "research/MAESTRO_biological_knowledge_20261004.zip")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output and args.output.exists():
        raise FileExistsError("Refusing to replace existing receipt")
    result = json.dumps(audit(args.archive), indent=2) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
