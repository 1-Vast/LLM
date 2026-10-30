"""One metadata-only pass over HTS001; count values are never accessed."""
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
import csv
import hashlib
import json
import time
import psutil

here = Path(__file__).resolve().parent
out = here / "metadata_result.json"
assert not out.exists(), "No automatic replay"
source = here / "sources/root/hts001_raw.body"
start, cpu = time.monotonic(), time.process_time()
process = psutil.Process()
peak = 0


def guard():
    global peak
    mem = process.memory_info()
    peak = max(peak, getattr(mem, "peak_wset", mem.rss))
    assert peak <= 256 * 1024**2
    assert time.monotonic() - start <= 90 and time.process_time() - cpu <= 60


raw = source.read_bytes()
assert len(raw) == 3039472 and hashlib.md5(raw).hexdigest() == "a5959a38166685707e840369ce34d74d"
sha = hashlib.sha256(raw).hexdigest()
del raw
allowed = ["upid","well","time","cell.line","drug1","drug1.conc","drug1.units","expt.id"]
traces = defaultdict(list)
conditions = defaultdict(set)
identities = {name:set() for name in allowed if name not in ["well","time"]}
trace_conditions = {}
rows = 0
conflicts = []
with source.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.reader(f)
    header = next(reader)
    missing = [n for n in allowed if n not in header]
    assert not missing, {"missing":missing,"header":header}
    index = {n:header.index(n) for n in allowed}
    for row in reader:
        rows += 1
        if rows % 500 == 0: guard()
        m = {n:row[i] for n,i in index.items()}
        for n,values in identities.items(): values.add(m[n])
        key = (m["expt.id"],m["upid"],m["well"])
        condition = tuple(m[n] for n in ["expt.id","cell.line","drug1","drug1.conc","drug1.units"])
        if key in trace_conditions and trace_conditions[key] != condition:
            conflicts.append({"trajectory":key,"row":rows})
        trace_conditions[key] = condition
        traces[key].append(Decimal(m["time"]))
        conditions[condition].add(key)

gaps, sizes, pre72, duplicate_times = Counter(), Counter(), Counter(), 0
all_times = set()
triplets = 0
qualified_traces = 0
for times in traces.values():
    ordered = sorted(set(times))
    duplicate_times += len(times)-len(ordered)
    all_times.update(ordered)
    sizes[len(ordered)] += 1
    window = [t for t in ordered if 0 <= t < 72]
    pre72[len(window)] += 1
    hits = 0
    for a,b,c in zip(window,window[1:],window[2:]):
        if b-a == c-b and b>a: hits += 1
    triplets += hits
    qualified_traces += hits > 0
    for a,b in zip(ordered,ordered[1:]): gaps[str(b-a)] += 1
guard()
assert hashlib.sha256(source.read_bytes()).hexdigest() == sha
result = {"scope":"Metadata qualification; not count/noise/kinetic/biological validation",
          "source_bytes":source.stat().st_size,"source_sha256":sha,"source_md5":"a5959a38166685707e840369ce34d74d",
          "rows":rows,"header":header,"accessed_columns":allowed,"count_value_accesses":0,
          "identities":{n:sorted(v) for n,v in identities.items()},
          "trajectory_count":len(traces),"condition_count":len(conditions),
          "wells_per_condition_histogram":dict(Counter(len(v) for v in conditions.values())),
          "time_grid":list(map(str,sorted(all_times))),"time_gap_histogram":dict(gaps),
          "points_per_trajectory_histogram":dict(sizes),"pre72_points_per_trajectory_histogram":dict(pre72),
          "duplicate_trajectory_time_metadata_rows":duplicate_times,"metadata_condition_conflicts":conflicts,
          "equal_gap_pre72_consecutive_triplets":triplets,"trajectories_with_equal_gap_pre72_triplet":qualified_traces,
          "independent_cultures_verified":False,"drug_replacement_72h":"repository-description-level; per-well time certification not established",
          "cpu_seconds":time.process_time()-cpu,"wall_seconds":time.monotonic()-start,"peak_working_set_bytes":peak,
          "enforcement":"cooperative CPU/wall/observed historical peak working set checks, not OS hard limits",
          "protocol_sha256":hashlib.sha256((here/'metadata_protocol.md').read_bytes()).hexdigest(),
          "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
body = (json.dumps(result,indent=2)+"\n").encode()
assert len(body) <= 5_000_000
out.write_bytes(body)
print(json.dumps({k:result[k] for k in ["rows","trajectory_count","condition_count","wells_per_condition_histogram","points_per_trajectory_histogram","pre72_points_per_trajectory_histogram","duplicate_trajectory_time_metadata_rows","metadata_condition_conflicts","equal_gap_pre72_consecutive_triplets","peak_working_set_bytes","cpu_seconds"]}))
