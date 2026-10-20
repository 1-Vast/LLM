"""Writes EVIDENCE_MANIFEST.json: hashes/sizes of the sources read, outputs, scripts, and a digest of the closed study folders at write time."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; HERE = Path(__file__).parent
def h(p):
    m = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): m.update(b)
    return m.hexdigest()
D = ROOT/"data/external/beataml2_20261017"
src = sorted(D.glob("*"))
J = ROOT/"data/external/gdsc_combinations/jaaks2022_figshare"
out = {"label": "qualification only; exposed released development data; no independent confirmation; nothing opened beyond the listed files",
       "sources_read": {p.name: {"bytes": p.stat().st_size, "sha256": h(p)} for p in src if p.is_file()},
       "jaaks_metadata_only": {p.name: p.stat().st_size for p in [J/"Glossary.xlsx", J/"Original screen_All tissues_fitted data.csv"] if p.exists()},
       "columns_read_from_beataml_raw": ["dbgap_subject_id","dbgap_dnaseq_sample","dbgap_rnaseq_sample","inhibitor","run_index","inhibitor_panel","plate_num","replicate","well_concentration","normalized_viability (replicate-noise only, part 1)","time_of_read","passed_qc"],
       "not_opened": ["old G/F", "unacquired C", "consumed held-out A/T", "ALMANAC and sealed PRISM tiers", "Beat AML expression and WES payloads (identity checked, values not analysed)"],
       "scripts_and_outputs": {p.name: h(p) for p in sorted(HERE.glob("*")) if p.is_file() and p.name not in ("EVIDENCE_MANIFEST.json","__pycache__")},
       "known_defects": {"feasibility.py": "M3/M4 and 'separability' are invalid by construction (battery residual against a ridge that contains the battery is ~0, so the sample-offset term is 0 and M3==M1, M4==M2); superseded by parts 2-4 and not used for any conclusion. The file is kept unchanged.",
                         "feasibility3.py": "readout_time block is not an assay duration: time_of_read is a per-well variable with 30+ values per drug, so the 24/72 h split is meaningless and unused. potency LODO correlation sign is a leave-one-out artefact; in-sample corr 0.03.",
                         "feasibility4.py": "first run returned NaN correlation (a drug absent from one half); fixed by pandas nan-safe corr, same pre-declared statistic."}}
closed = {}
for name in ["functional_rule_revision_20261020","self_improving_virtual_cell_20261020","innovation_validation_20261020","innovation_validation_repair1_20261020","procedure_inheritance_20261020","procedure_inheritance_20261020_audit1"]:
    d = ROOT/"research"/name
    if d.is_dir():
        m = hashlib.sha256(); n = 0
        for p in sorted(d.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts:
                m.update(str(p.relative_to(d)).encode()); m.update(h(p).encode()); n += 1
        closed[name] = {"files": n, "digest": m.hexdigest()}
out["closed_studies_digest_at_write_time"] = closed
out["closed_studies_note"] = "digest taken at the end of this session, not before it; this session wrote nothing into these folders (only the new folder and registry pointer lines)."
json.dump(out, open(HERE/"EVIDENCE_MANIFEST.json","w"), indent=1)
print(len(out["sources_read"]), "sources", len(closed), "closed")
