"""Tally observed common-endpoint geometry; never analyze count values."""
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import re
import time

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "sources/u1c-per-sample-junction-counts.txt.gz"
OUTPUT = HERE / "junction_identity_geometry.json"
EXPECTED = "db9993810abeef492132729cbd1b64c13f51a6a21da6eb1e461cfff32cc066f5"
assert not OUTPUT.exists(), "Single metadata projection"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
syntax = re.compile(r"^(chr[0-9A-Za-z_.]+):([+-]):([0-9]+):([0-9]+)$")
gene_syntax = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
missing_gene = {"", "-", ".", "NA", "N/A"}
genes = defaultdict(set)
coordinates = {}
stats, orientation = Counter(), Counter()
start = time.monotonic()
with gzip.open(SOURCE, "rt", encoding="utf-8") as stream:
    header = stream.readline().rstrip("\r\n").split("\t")
    expected_header = json.loads((HERE / "junction_header_audit.json").read_text())["headers"]
    assert header == expected_header
    for line in stream:
        stats["records"] += 1
        if stats["records"] % 1000 == 0 and time.monotonic() - start > 1800:
            raise TimeoutError("Metadata scan exceeded1800s")
        # The third string is opaque and unused: no count token is projected/converted.
        fields = line.split("\t", 2)
        if len(fields) != 3:
            stats["malformed_identity_record"] += 1
            continue
        gene, jid = fields[0].strip(), fields[1].strip()
        match = syntax.fullmatch(jid)
        if not match:
            stats["unparsed_junction_id"] += 1
            continue
        chrom, strand, first, second = match.groups()
        first, second = int(first), int(second)
        if first <= 0 or second <= 0 or first == second:
            stats["invalid_coordinate_identity"] += 1
            continue
        genes[jid].add(gene)
        coordinates[jid] = (chrom, strand, first, second)
first_groups, second_groups = defaultdict(set), defaultdict(set)
for jid, labels in genes.items():
    if len(labels) != 1:
        stats["junction_ids_with_multiple_gene_labels"] += 1
        continue
    gene = next(iter(labels))
    if gene in missing_gene or not gene_syntax.fullmatch(gene):
        stats["junction_ids_without_single_simple_gene_label"] += 1
        continue
    chrom, strand, first, second = coordinates[jid]
    stats["unambiguous_junction_ids"] += 1
    orientation[strand + ("/first_lt_second" if first < second else "/first_gt_second")] += 1
    first_groups[(gene, chrom, strand, first)].add(second)
    second_groups[(gene, chrom, strand, second)].add(first)


def summarize(groups):
    sizes = Counter(len(others) for others in groups.values())
    return {"observed_groups": len(groups), "one_distinct_other_endpoint": sizes[1],
            "two_distinct_other_endpoints": sizes[2],
            "at_least_three_distinct_other_endpoints": sum(n for size, n in sizes.items() if size >= 3)}


result = {"scope": "Identity geometry only; no count/PSI/effect/coverage value projected or used",
          "source_sha256": EXPECTED, "metadata_counts": dict(stats),
          "unique_parsed_junction_ids": len(genes), "coordinate_order_by_strand": dict(orientation),
          "shared_first_coordinate": summarize(first_groups),
          "shared_second_coordinate": summarize(second_groups),
          "elapsed_seconds": round(time.monotonic() - start, 3),
          "limits": ["Groups overlap and are not independent biological samples or eligible events",
                     "Coordinate order is not relabelled donor/acceptor without export-convention authentication",
                     "Observed pooled-sample identity universe may be treatment informed",
                     "No closure, baseline support, read quality, missing-branch or invariant-drug-action claim"]}
OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
