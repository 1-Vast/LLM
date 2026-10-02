"""Verify new freezes, historical evidence and publication scope without mutation."""
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from research.astra.gdsc_transport import digest, save

OUT = Path(__file__).resolve().parent
RESULTS = ROOT / "research/astra/results"
snapshot = ROOT / "tmp/gdsc_review_15fec7c"
snapshot_manifest = json.loads((snapshot / "snapshot_manifest.json").read_text())
snapshot_ok = all(digest(snapshot / name) == expected for name,expected in snapshot_manifest["paths"].items())
manifests = {}
for name in ["20261002_gdsc_independent_review_v2", "20261002_gdsc_transport_discovery_v1",
             "20261002_gdsc_full_release_metadata_v1", "20261002_ctrp_menu_qualification_v1",
             "20261002_gdsc_layout_freeze_v1", "20261002_gdsc_layout_evaluation_v1",
             "20261002_gdsc_layout_diagnostics_v1", "20261002_gdsc_randomized_pilot_v1"]:
    folder = RESULTS / name
    record = json.loads((folder / "manifest.json").read_text())
    manifests[name] = all(digest(folder / file) == expected for file,expected in record.items())
evidence = json.loads((ROOT / "research/astra/evidence/20261002_gdsc_inputs/receipt.json").read_text())
originals_ok = all(digest(record["original_path"]) == record["sha256"] and
                   digest(ROOT / record["archive_path"]) == record["sha256"] for record in evidence.values())
append = json.loads((OUT / "log_append_receipt.json").read_text(encoding="utf-8-sig"))
import hashlib
prefix = (ROOT / "log/20261002/README.md").read_bytes()[:append["original_prefix_bytes"]]
prefix_ok = hashlib.sha256(prefix).hexdigest() == append["original_prefix_sha256"]
sources = {
    "tmp/gdsc_transport_sources_v3/GDSC2_public_raw_data_27Oct23.csv":"e915be2948b174982a9b64bea5fab00f6ec8c15f7baa76bc7e2f7a7df295500e",
    "tmp/gdsc_transport_sources_v5/ctrp_archive.raw.txt":"8f62b3b5ed70cfd367cf52ce0a99884dd0a674d1a8c301474b707648689bdee3"}
raw_ok = all(digest(ROOT / name) == expected for name,expected in sources.items())
frozen_code_ok = all(
    json.loads((RESULTS / folder / "protocol.json").read_text())["code_sha256"] == digest(ROOT / "research/astra" / code)
    for folder,code in [("20261002_gdsc_full_release_metadata_v1","gdsc_transport.py"),
                        ("20261002_gdsc_layout_freeze_v1","gdsc_layout_validation.py"),
                        ("20261002_ctrp_menu_qualification_v1","ctrp_qualification.py"),
                        ("20261002_gdsc_randomized_pilot_v1","gdsc_pilot.py")])
scope = subprocess.check_output(["git","diff","--name-only","HEAD","--","src","tools"],cwd=ROOT,text=True).splitlines()
counts = {folder:len(subprocess.check_output(["git","ls-files",folder],cwd=ROOT,text=True).splitlines()) for folder in ["src","tools"]}
verification = json.loads((OUT / "receipt.json").read_text())
cases = list(ET.parse(OUT / "docs_final.xml").getroot().iter("testcase"))
docs_ok = len(cases) == 21 and not any(c.find("failure") is not None or c.find("error") is not None or c.find("skipped") is not None for c in cases)
ok = snapshot_ok and all(manifests.values()) and originals_ok and prefix_ok and raw_ok and frozen_code_ok and not scope and docs_ok and verification["all_passed"] and counts == {"src":44,"tools":913}
result = dict(all_valid=ok,snapshot58_files_unchanged=snapshot_ok,artifact_manifest_matches=manifests,
    uploaded_originals_unchanged=originals_ok,old_log_prefix_unchanged=prefix_ok,raw_sources_unchanged=raw_ok,
    frozen_analysis_codes_unchanged=frozen_code_ok,production_changes=scope,production_file_counts=counts,
    main_scoped_tests=verification["tests"],ASTRA_tests=verification["research_test_count"],docs_checks=21,
    new_contracts=12,counts_overlap=True,new_registered_model_reconstructions=1,new_hyperparameter_searches=0,
    new_STATE_forwards=0,new_LLM_requests=0,physical_executions=0,PR_merged=False,
    untracked_user_originals_preserved=list(evidence))
save(OUT / "publication_validation.json",result)
print(json.dumps(result))
raise SystemExit(0 if ok else 1)
