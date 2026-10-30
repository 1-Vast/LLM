"""One fixed metadata-only overlap pass; never inspect response-field values."""
from pathlib import Path
import csv
import hashlib
import json
import time

here = Path(__file__).resolve().parent
dest = here / "dictionary_overlap_result.json"
assert not dest.exists(), "No automatic replay"
source = here.parents[1] / "tmp/extq1/GDSC2_fitted_dose_response.csv"
expected = "0883b3ef6e440603094c43c74044e1d333fce61e92e3efa374ea3a54f0b50302"
assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
allowed = ["DATASET","CELL_LINE_NAME","SANGER_MODEL_ID","COSMIC_ID","DRUG_ID","DRUG_NAME","MIN_CONC","MAX_CONC"]
cells = {"jurkat","hek293"}
drugs = {"dasatinib","dinaciclib","crizotinib"}
normalize = lambda s: s.casefold().translate(str.maketrans("", "", " -_"))
selected = set()
cell_names = set()
drug_names = set()
rows = 0
start_wall, start_cpu = time.monotonic(), time.process_time()
with source.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.reader(f)
    header = next(reader)
    indices = {name:header.index(name) for name in allowed if name in header}
    assert "CELL_LINE_NAME" in indices and "DRUG_NAME" in indices
    for row in reader:
        rows += 1
        if rows % 1000 == 0:
            assert time.process_time()-start_cpu < 60 and time.monotonic()-start_wall < 90
        c, d = row[indices["CELL_LINE_NAME"]], row[indices["DRUG_NAME"]]
        if normalize(c) in cells: cell_names.add(c)
        if normalize(d) in drugs: drug_names.add(d)
        if normalize(c) in cells and normalize(d) in drugs:
            selected.add(tuple(row[indices[k]] for k in indices))
assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
result = {"scope":"fixed metadata-only name overlap, not matched occupancy/functional qualification",
          "source_sha256":expected,"source_bytes":source.stat().st_size,"rows":rows,
          "accessed_columns":list(indices),"matched_cell_names":sorted(cell_names),
          "matched_drug_names":sorted(drug_names),
          "candidate_rows":[dict(zip(indices,row)) for row in sorted(selected)],
          "concentration_unit":"not certified by this CSV; requires original contract",
          "culture_clone_time_endpoint_and_intervention_error_match":False,
          "functional_response_fields_accessed":[],"scientific_effect_runs":0,
          "cpu_seconds":time.process_time()-start_cpu,"wall_seconds":time.monotonic()-start_wall}
raw = (json.dumps(result,indent=2)+"\n").encode()
assert len(raw) < 2000000
dest.write_bytes(raw)
print(raw.decode())
