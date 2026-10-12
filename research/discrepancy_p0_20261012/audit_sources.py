"""P0a: audit recorded conditions and repeat designs without scoring outcomes.

Only two public PRISM metadata files may be downloaded (25 MB each, at most).
Existing CXCL9 files are projected onto treatment/sample metadata; PE outcomes
are neither materialized nor analyzed. Old studies and receipts are not edited.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = HERE / "data"
RAW = ROOT / "data/external/prism_19q4/raw"
CXCL9 = ROOT / "research/dual_core_scientific_20261011/literature/datasets/cxcl9_2026"
OFFICIAL = ROOT / "research/budgeted_feedback_20261011/data/sources/prism_official.body"
PAPER = ROOT / "research/dual_core_scientific_20261011/literature/raw/active_mechanistic_2026.html"
PRISM_PAPER = HERE / "literature/raw/prism_paper_methods.body"
LIMIT = 25 * 1024 * 1024
SOURCES: list[dict] = []


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def source(path: Path, usage: str) -> dict:
    row = {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size,
           "sha256": sha256(path), "usage": usage}
    SOURCES.append(row)
    return row


def public_metadata(name: str, file_id: str) -> Path | None:
    """Cache an official-page-linked metadata file and preserve its original receipt."""
    local = RAW / name
    if local.exists():
        return local
    url = f"https://ndownloader.figshare.com/files/{file_id}"
    page = OFFICIAL.read_text(encoding="utf-8")
    if url not in page or name not in page:
        raise ValueError(f"Metadata not linked by retained official page: {name}")
    records_path = DATA / "NETWORK_SOURCES.json"
    records = json.loads(records_path.read_text(encoding="utf-8")) if records_path.exists() else []
    existing = next((r for r in records if r.get("name") == name and "sha256" in r), None)
    path = DATA / "sources" / name
    if existing is not None:
        if not path.exists() or sha256(path) != existing["sha256"]:
            raise ValueError(f"Cached source changed: {name}")
        return path
    row = {"name": name, "requested_url": url,
           "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
           "official_page_path": OFFICIAL.relative_to(ROOT).as_posix(),
           "official_page_sha256": sha256(OFFICIAL), "limit_bytes": LIMIT}
    try:
        request = Request(url, headers={"User-Agent": "MAESTRO-P0a-metadata-audit/1.0"})
        with urlopen(request, timeout=45) as response:
            body = response.read(LIMIT + 1)
            if len(body) > LIMIT:
                raise ValueError(f"Metadata exceeded {LIMIT} bytes: {name}")
            row.update(status=response.status, resolved_url=response.url.split("?")[0],
                       content_type=response.headers.get("Content-Type"),
                       etag=response.headers.get("ETag"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        columns = set(pd.read_csv(path, nrows=0).columns)
        required = {"row_name", "screen_id"} if "pooling" in name else {"column_name", "broad_id", "dose", "screen_id", "detection_plate"}
        if not required <= columns:
            raise ValueError(f"Unexpected metadata schema: {name}")
        row.update(path=path.relative_to(ROOT).as_posix(), bytes=len(body), sha256=sha256(path))
        print(f"Cached {name}: {len(body)} bytes", flush=True)
    except (URLError, OSError, ValueError) as error:
        row["error"] = str(error)
        path = None
    records.append(row)
    write_json(records_path, records)
    return path


def table(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    record = source(path, "metadata only; outcome columns excluded")
    frame = pd.read_csv(path, usecols=columns, keep_default_na=False, low_memory=False)
    record["columns_read"] = list(frame.columns)
    return frame


def exact_dose(frame: pd.DataFrame, screen: str | None = None) -> pd.DataFrame:
    dose = pd.to_numeric(frame["dose"], errors="coerce")
    keep = dose.eq(2.5)
    if screen is not None:
        keep &= frame["screen_id"].eq(screen)
    if "perturbation_type" in frame:
        keep &= frame["perturbation_type"].eq("experimental_treatment")
    return frame.loc[keep].copy()


def repeat_design(frame: pd.DataFrame, label: str, screen: str | None = None) -> dict:
    q = exact_dose(frame, screen)
    keys = ["broad_id", "dose", "screen_id", "compound_plate"]
    groups = q.groupby(keys, dropna=False).agg(
        metadata_rows=("column_name", "size"),
        detection_plates=("detection_plate", "nunique"),
        recorded_well_positions=("well", "nunique"))
    groups.reset_index().to_csv(DATA / f"{label}_REPLICATE_GROUPS.csv", index=False)
    tokens = q["detection_plate"].astype(str).str.extract(r"_(\d+)H_", expand=False).fillna("NOT_ENCODED")
    result = {"columns": list(frame.columns), "exactdose_experimental_rows": len(q),
              "condition_groups": len(groups), "distinct_broad_ids": q.broad_id.nunique(),
              "condition_group_keys": keys,
              "groups_with_different_recorded_wells": int(groups.recorded_well_positions.gt(1).sum()),
              "well_interpretation": "MTS010 replicate records can have different well positions; well is not part of the shared treatment-condition key",
              "detection_plates": q.detection_plate.nunique(),
              "compound_plates": q.compound_plate.nunique(),
              "groups_with_multiple_detection_plates": int(groups.detection_plates.gt(1).sum()),
              "metadata_rows_per_group": {str(k): int(v) for k, v in groups.metadata_rows.value_counts().sort_index().items()},
              "encoded_plate_time_tokens": {str(k): int(v) for k, v in tokens.value_counts().items()},
              "time_interpretation": "Identifier tokens only; not an independently validated elapsed-treatment-time field",
              "independent_culture_ids": False,
              "biological_repeat_count": None,
              "repeat_interpretation": "Treatment-plate repeats are supported by the paper; distinct detection-plate IDs alone do not prove independent culture starts"}
    if "detection_plate_scan_time" in q:
        result["detection_scan_time_nonempty"] = int(q.detection_plate_scan_time.ne("").sum())
        result["detection_scan_time_interpretation"] = "Instrument scan timestamp, not seeding/date/culture identity"
    return result


def pool_design(frame: pd.DataFrame) -> dict:
    return {"columns": list(frame.columns), "metadata_rows": len(frame),
            "rows_by_screen": {str(k): int(v) for k, v in frame.screen_id.value_counts().items()},
            "distinct_row_ids_by_screen": {str(k): int(v) for k, v in frame.groupby("screen_id").row_name.nunique().items()},
            "interpretation": "Line/pool availability metadata; not finite outcome availability or culture replication"}


def prism(primary_rep: Path | None, primary_pool: Path | None) -> dict:
    pri = table(RAW / "primary-screen-replicate-collapsed-treatment-info.csv")
    sec = table(RAW / "secondary-screen-replicate-collapsed-treatment-info.csv")
    prep = table(primary_rep) if primary_rep else None
    srep = table(RAW / "secondary-screen-replicate-treatment-info.csv")
    ppool = table(primary_pool) if primary_pool else None
    spool = table(RAW / "secondary-screen-pooling-info.csv")
    pcell = table(RAW / "primary-screen-cell-line-info.csv")
    scell = table(RAW / "secondary-screen-cell-line-info.csv")
    source(PRISM_PAPER, "original PRISM assay duration and independently treated plate design")
    paper = html.unescape(re.sub(r"<[^>]+>", " ", PRISM_PAPER.read_text(encoding="utf-8")))
    paper = re.sub(r"\s+", " ", paper)
    excerpts = {name: paper_excerpt(paper, phrase) for name, phrase in {
        "assay_repeats": "independently treated plates",
        "seeding": "at 1,250 cells/well in triplicate",
        "duration": "After a five-day incubation"}.items()}
    pq, sq = exact_dose(pri, "HTS"), exact_dose(sec)
    pids = set(pq.broad_id)
    overlap = sq.loc[sq.broad_id.isin(pids), ["broad_id", "dose", "screen_id", "column_name", "compound_plate"]]
    overlap.to_csv(DATA / "PRISM_PRIMARY_SECONDARY_ID_OVERLAP.csv", index=False)
    multi_screen = sq.groupby(["broad_id", "dose"]).screen_id.nunique()
    result = {"primary_collapsed": {"metadata_rows": len(pri), "exactdose_HTS_columns": len(pq),
                                   "unique_exactdose_HTS_columns": pq.column_name.nunique()},
              "primary_replicates": repeat_design(prep, "PRIMARY_HTS", "HTS") if prep is not None else {"status": "MISSING_METADATA"},
              "secondary_replicates": repeat_design(srep, "SECONDARY"),
              "primary_pool": pool_design(ppool) if ppool is not None else {"status": "MISSING_METADATA"},
              "secondary_pool": pool_design(spool),
              "cross_screen": {"secondary_exactdose_columns": len(sq),
                  "secondary_exactdose_columns_by_screen": {str(k): int(v) for k, v in sq.screen_id.value_counts().items()},
                  "exact_full_broad_id_overlap": len(pids & set(sq.broad_id)),
                  "same_drug_dose_multiple_secondary_screens": int(multi_screen.gt(1).sum()),
                  "cell_metadata_row_id_overlap": len(set(pcell.row_name) & set(scell.row_name)),
                  "identity_caveat": "ID equality only; compound salts/structures and cell culture continuity not independently resolved",
                  "cell_drug_complete_pairs": None,
                  "matching_time_culture_and_QC_complete_pairs": None},
              "published_protocol": {"paper_path": PRISM_PAPER.relative_to(ROOT).as_posix(),
                  "nominal_time_hours": 120 if excerpts["duration"] else None,
                  "paper_excerpts": excerpts,
                  "assay_plate_repeat_design": "Up to three independently treated assay plates per screen; one to three retained after QC",
                  "independent_culture_start_ids_verified": False,
                  "interpretation": "The publication supports repeated plate treatments and five-day incubation. Missing culture-start IDs limit hierarchy/variance claims, not the existence of assay repeats."},
              "primary_replicate_outcomes_local": (RAW / "primary-screen-logfold-change.csv").exists(),
              "primary_MFI_local": (RAW / "primary-screen-primary-mfi.csv").exists(),
              "secondary_replicate_outcomes_local": (RAW / "secondary-screen-logfold-change.csv").exists(),
              "readme": []}
    for name in ("primary-screen-readme.txt", "secondary-screen-readme.txt"):
        path = RAW / name
        source(path, "publisher assay and preprocessing description")
        text = path.read_text(encoding="utf-8")
        result["readme"].append({"path": path.relative_to(ROOT).as_posix(),
            "ComBat": "ComBat" in text, "median_collapse": "Median-collapse" in text,
            "MTS010_technical_redos": "Technical redos" in text})
    result["qualification"] = {
        "collapsed_functional_replay": "QUALIFIED_RETROSPECTIVE_POST_PUBLISHER_ENDPOINT",
        "repeat_assay_plate_design": "QUALIFIED_BY_PUBLISHED_METHODS" if all(excerpts.values()) else "NOT_EVALUABLE_WITHOUT_METHODS_SUPPORT",
        "primary_repeat_response_validation": "NOT_EVALUABLE_UNTIL_REPEAT_OUTCOMES_AND_QC_ARE_ADMITTED",
        "secondary_repeat_response_validation": "CONDITIONALLY_QUALIFIED_RETROSPECTIVE_ASSAY_REPEAT_REPLAY",
        "cross_screen_response_agreement": "CONDITIONALLY_QUALIFIED_ID_DOSE_NOMINAL_PROTOCOL_MATCH",
        "independent_culture_start_hierarchy": "UNRESOLVED",
        "biological_vs_technical_cause": "NON_IDENTIFIABLE",
        "reason": "Published independently treated assay plates support measurement repeats. Complete outcome/QC pairs remain unaudited; culture starts, drug-specific batch effects and target engagement are not independently identified; raw primary normalization isolation is unavailable"}
    return result


def paper_excerpt(text: str, phrase: str) -> str | None:
    position = text.lower().find(phrase.lower())
    return text[max(0, position - 120): position + 400] if position >= 0 else None


def cxcl9() -> dict:
    metadata = CXCL9 / "data/cxcl9_assay/metadata.md"
    source(metadata, "assay incubation, passage and inhibitor names")
    source(CXCL9 / "01_mechanistic_model/01_preparing_inputs.R", "replicate folding and outcome-dependent normalization audit; not executed")
    source(ROOT / "research/dual_core_scientific_20261011/literature/dataset_card.json", "historical card with endpoint terminology corrected in this audit")
    source(PAPER, "original paper Methods and replicate definition; no outcome extraction")
    text = html.unescape(re.sub(r"<[^>]+>", " ", PAPER.read_text(encoding="utf-8")))
    text = re.sub(r"\s+", " ", text)
    excerpts = {name: paper_excerpt(text, phrase) for name, phrase in {
        "supernatant": "retrieving the supernatant",
        "capture_beads": "Human CXCL9 (MIG) Capture Beads",
        "biological_replicates": "independent biological replicates with technical duplicates",
        "screenings": "two independent wet lab screenings",
        "context_specific_cytokine_doses": "at 10 and 1 ng/mL",
        "Cas3_assay": "Z-DEVD-R110"}.items()}
    frames, schema = [], []
    for name, passage in (("E3CA", "P12"), ("E3CB", "P14")):
        path = CXCL9 / f"data/cxcl9_assay/00_Raw_Data_{name}.csv"
        columns = list(pd.read_csv(path, nrows=0).columns)
        keep = [c for c in columns if c != "Fluorescent intensity (PE)"]
        frame = table(path, keep)
        frame["source_file"] = name
        frame["passage"] = passage
        frames.append(frame)
        schema.append({"file": name, "rows": len(frame), "columns": columns,
                       "outcome_columns_read": [], "passage": passage,
                       "Cas3_channel": any("cas" in c.lower() for c in columns)})
    values = pd.concat(frames, ignore_index=True)
    keys = ["source_file", "passage", "Cell line", "Sample", "Condition", "Cytokines",
            "Cytokine concentration (ng/mL)", "Inhibitors", "Inhibitor concentration (uM)"]
    design = values.groupby(keys, dropna=False).size().reset_index(name="bead_event_rows")
    design.to_csv(DATA / "CXCL9_SAMPLE_DESIGN.csv", index=False)
    per_duplicate = design.groupby(["source_file", "Condition"]).size()
    return {"endpoint": "24-hour culture-supernatant CXCL9 secretion measured by LEGENDplex capture-bead sandwich immunoassay and FACS PE",
        "historical_terminology_correction": "The old dataset card says intracellular and single-cell; original Methods identify secreted cytokine and capture-bead events. Old receipts are preserved.",
        "paper_path": PAPER.relative_to(ROOT).as_posix(), "paper_excerpts": excerpts,
        "raw_files": schema, "local_raw_contexts": sorted(values["Cell line"].unique().tolist()),
        "paper_reported_biological_screenings": 2 if excerpts["biological_replicates"] else None,
        "screen_file_candidates": 2, "sample_condition_records": len(design),
        "conditions_per_file_duplicate": {f"{f}|{s}": int(n) for (f, s), n in per_duplicate.items()},
        "cytokines": sorted(values.Cytokines.unique().tolist()),
        "inhibitors": sorted(values.Inhibitors.unique().tolist()),
        "cytokine_doses_recorded_ng_ml": sorted(values["Cytokine concentration (ng/mL)"].astype(str).unique().tolist()),
        "inhibitor_doses_recorded_um": sorted(values["Inhibitor concentration (uM)"].astype(str).unique().tolist()),
        "unit_interpretation": "source_file/passage candidates correspond to biological screenings; Condition Sample1/Sample2 are technical-duplicate candidates. Sample labels encode treatments, not independent units; bead events are nested.",
        "source_to_paper_repeat_mapping": "Supported by two source files, two documented passages and the paper's repeat definition; no explicit seeding/well/day key is supplied in the cached raw tables",
        "Cas3_condition_pairing": "NOT_EVALUABLE_IN_CACHED_RAW_FILES",
        "qualification": {
            "small_repeated_CXCL9_assay": "CONDITIONALLY_QUALIFIED_RETROSPECTIVE_BxPC3_REPLAY",
            "mechanism_discrimination_cell_loss_vs_signaling": "NOT_EVALUABLE_WITHOUT_PAIRED_Cas3_OR_VIABILITY",
            "general_context_transport": "NOT_ESTABLISHED_BY_SINGLE_RAW_CONTEXT_TWO_SCREENINGS",
            "reason": "A repeated measured secretion endpoint and factorial interventions exist; independently matched apoptosis/viability outcomes and broad context replication do not follow from this cache"},
        "legal_menu": "Reveal condition-level CXCL9 summaries from one declared screening; score commitments on the other screening. Preserve technical nesting; use fixed/raw-log scaling, never full-condition min-max input.",
        "limits": ["No response values were scored here", "No new external response file was downloaded",
                   "A target annotation or the supplied logic-ODE network is a prior, not mechanism truth",
                   "The inactive/positive-control condition cannot identify drug-specific target engagement by itself"]}


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    source(OFFICIAL, "retained official DepMap links authenticating metadata file IDs")
    primary_rep = public_metadata("primary-screen-replicate-treatment-info.csv", "20237712")
    primary_pool = public_metadata("primary-screen-pooling-info.csv", "20237721")
    result = {"schema": "maestro.discrepancy_p0.source_audit.v1",
              "scope": "P0a metadata, conditions and repeat design only; no model fitting, outcome scoring or LLM calls",
              "prism": prism(primary_rep, primary_pool), "cxcl9": cxcl9(),
              "script_sha256": sha256(Path(__file__)), "llm_api_calls": 0,
              "interpretation": "Source qualification is not a positive biological result or a deployment guarantee"}
    write_json(DATA / "SOURCE_AUDIT.json", result)
    write_json(DATA / "SOURCES.json", SOURCES)
    print(json.dumps({"audit": (DATA / "SOURCE_AUDIT.json").relative_to(ROOT).as_posix(),
                      "prism_qualification": result["prism"]["qualification"],
                      "cxcl9_qualification": result["cxcl9"]["qualification"]}, indent=2))


if __name__ == "__main__":
    main()
