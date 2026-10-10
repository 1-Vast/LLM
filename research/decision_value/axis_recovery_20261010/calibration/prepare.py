"""Metadata-only qualification and first-stage index-screen freeze."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

import h5py
import numpy as np
import pyarrow.parquet as pq

try:
    from .storage import HERE, ROOT, CAP, REVISION, Source, physical_spans, merge_adjacent, sha, read_rows, write
except ImportError:
    from storage import HERE, ROOT, CAP, REVISION, Source, physical_spans, merge_adjacent, sha, read_rows, write

COLS = ("drugname_drugconc", "plate", "sample", "pass_filter", "cell_name", "cell_line")


def copy_input(source, name):
    target = HERE / "inputs" / name
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(source.read_bytes())
    return dict(path=target.relative_to(HERE).as_posix(), sha256=sha(target), bytes=target.stat().st_size,
                original_path=source.relative_to(ROOT).as_posix())


def text(values):
    return [item.decode() if isinstance(item, bytes) else str(item) for item in values]


def prepare():
    started=time.monotonic()
    if (HERE / "INDEX_FREEZE.json").exists(): raise FileExistsError("Index freeze already exists")
    records = [copy_input(source, name) for source, name in [
        (HERE.parent / "informative/SELECTION.json", "SELECTION.json"),
        (HERE.parent / "design/EXCLUSIONS.json", "EXCLUSIONS.json"),
        (ROOT / "research/decision_value/observation_reliability/ENDPOINT.json", "ENDPOINT.json"),
        (ROOT / "research/decision_value/observation_reliability/CONTROL_PLAN.json", "CONTROL_PLAN.json"),
        (ROOT / "research/decision_value/observation_reliability/literature/SOURCE_QUALIFICATION.json", "SOURCE_QUALIFICATION.json"),
        (ROOT / "research/decision_value/observation_reliability/literature/sources/tahoe_sample_parquet.parquet", "SAMPLES.parquet"),
    ]]
    selection = json.loads((HERE / "inputs/SELECTION.json").read_text())
    exclusions = json.loads((HERE / "inputs/EXCLUSIONS.json").read_text())
    endpoint = json.loads((HERE / "inputs/ENDPOINT.json").read_text())
    samples = pq.read_table(HERE / "inputs/SAMPLES.parquet").to_pandas().set_index("sample", verify_integrity=True)
    qualification = json.loads((HERE / "inputs/SOURCE_QUALIFICATION.json").read_text())
    if sha(HERE / "inputs/SAMPLES.parquet") != qualification["sample_metadata_sha256"]:
        raise RuntimeError("official_sample_metadata_hash_mismatch")
    noise = json.loads((HERE / "inputs/CONTROL_PLAN.json").read_text())
    excluded_rows = {(g["file"], int(row)) for g in noise["selected"] for row in g["rows"]}
    groups, censuses, layouts, genes_by_file, codes, seeds = [], {}, {}, {}, {}, {}
    for file in ("c44.h5ad", "c45.h5ad"):
        seed_bytes = subprocess.check_output(["git", "show", "91b0c10:research/astra/zeroshot_context_20261007/census/" + file + ".json"], cwd=ROOT)
        seed_path = HERE / "inputs" / (file + "_CENSUS_SEED.json")
        seed_path.write_bytes(seed_bytes)
        seeds[file] = dict(path=seed_path.relative_to(HERE).as_posix(), sha256=sha(seed_path), git_commit="91b0c10")
        seed = json.loads(seed_bytes)
        if seed["revision"] != REVISION: raise RuntimeError("wrong_census_revision")
        source = Source(file, seed["file_bytes"], network=True)
        print("Qualifying exact source metadata: " + file, flush=True)
        with h5py.File(source, "r") as h5:
            names = text(h5["var/gene_name"][:])
            if len(names) != len(set(names)) or len(names) != int(h5['X'].attrs['shape'][1]):
                raise RuntimeError("source_gene_names_not_unique_or_shape_disagrees")
            names_path = HERE / "inputs" / (file + "_GENES.json")
            if names_path.exists():
                if json.loads(names_path.read_text()) != names: raise RuntimeError("source_gene_dictionary_changed")
            else:
                write(names_path, names)
            if any(names.count(gene) != 1 for gene in endpoint["symbols"]):
                raise RuntimeError("missing_or_duplicated_endpoint_source_symbol")
            genes_by_file[file] = dict(path=names_path.relative_to(HERE).as_posix(), sha256=sha(names_path), count=len(names))
            cat, values = {}, {}
            for col in COLS:
                obj = h5["obs"][col]["codes"]
                layout = seed["code_layouts"][col]
                if obj.dtype.str != layout["dtype"] or obj.shape != tuple(layout["shape"]) or obj.id.get_offset() != layout["offset"]:
                    raise RuntimeError("actual_metadata_layout_disagrees_with_seed")
                cat[col] = text(h5["obs"][col]["categories"][:])
                if cat[col] != seed["categories"][col]: raise RuntimeError("category_seed_mismatch")
                body = source.fetch(layout["offset"], layout["offset"]+layout["storage_bytes"]-1, "QC_sample_condition_code_metadata")
                values[col] = np.frombuffer(body, dtype=obj.dtype)
                if hashlib.sha256(body).hexdigest() != seed["codes_sha256"][col]:
                    raise RuntimeError("metadata_code_seed_hash_mismatch")
            code_path = HERE / "inputs" / (file + "_CODES.npz")
            np.savez_compressed(code_path, **values)
            codes[file] = dict(path=code_path.relative_to(HERE).as_posix(), sha256=sha(code_path))
            hvg = h5["obsm/X_hvg"]
            if hvg.chunks is not None or hvg.compression or hvg.shape != (seed["n_cells"], 2000) or hvg.dtype.str != "<f4":
                raise RuntimeError("unsupported_actual_hvg_layout")
            pointer = h5["X/indptr"]
            pieces = [source.fetch(a, b, "CSR_row_pointer_metadata") for a, b in physical_spans(pointer, 0, pointer.shape[0])]
            ptr = np.frombuffer(b"".join(pieces), dtype=pointer.dtype)
            if len(ptr) != seed["n_cells"]+1 or np.any(np.diff(ptr) < 0):
                raise RuntimeError("invalid_CSR_pointer_metadata")
            ptr_path = HERE / "inputs" / (file + "_POINTERS.npy")
            np.save(ptr_path, ptr, allow_pickle=False)
            censuses[file] = dict(file=file, source_revision=REVISION, file_bytes=seed["file_bytes"],
                n_cells=seed["n_cells"], categories=cat, code_layouts=seed["code_layouts"],
                source_gene_count=len(names), codes_sha256=seed["codes_sha256"],
                layouts={"obsm/X_hvg": dict(shape=list(hvg.shape), dtype=hvg.dtype.str, offset=hvg.id.get_offset(), chunks=None, compression=None),
                         "X/indptr": dict(shape=list(pointer.shape), dtype=pointer.dtype.str, chunks=list(pointer.chunks)),
                         "X/indices": dict(shape=list(h5['X/indices'].shape), dtype=h5['X/indices'].dtype.str, chunks=list(h5['X/indices'].chunks)),
                         "X/data": dict(shape=list(h5['X/data'].shape), dtype=h5['X/data'].dtype.str, chunks=list(h5['X/data'].chunks))},
                pointer_path=ptr_path.relative_to(HERE).as_posix(), pointer_sha256=sha(ptr_path),
                metadata_axis_certifies_hidden_HVG_order=False)
            selected = [g for g in selection["selected"] if g["file"] == file]
            if not 1 <= len(selected) <= 4: raise RuntimeError("condition_count_out_of_bounds")
            jobs = []
            for number, g in enumerate(selected):
                if g["label"] in exclusions["excluded_exact_sentinel_labels"]:
                    raise RuntimeError("protected_sentinel_label")
                mask = ((values['drugname_drugconc'] == cat['drugname_drugconc'].index(g['label']))
                        & (values['plate'] == cat['plate'].index(g['plate']))
                        & (values['pass_filter'] == cat['pass_filter'].index('full'))
                        & (values['cell_line'] == cat['cell_line'].index(g['cell_line_id'])))
                rows = [int(row) for row in np.flatnonzero(mask)
                        if (file, int(row)) not in excluded_rows
                        and cat['sample'][int(values['sample'][row])] not in exclusions['excluded_pooled_sample_ids']]
                observed_samples = sorted({cat['sample'][int(values['sample'][row])] for row in rows})
                if observed_samples != sorted(g['official_pooled_sample_ids']) or len(rows) < 50:
                    raise RuntimeError("selected_source_QC_or_sample_identity_insufficient")
                for sample in observed_samples:
                    record = samples.loc[sample]
                    if record['plate'] != g['plate'] or record['drugname_drugconc'] != g['label']:
                        raise RuntimeError("official_sample_condition_join_mismatch")
                group = dict(file=file, condition_id=f"{file}:{number}", label=g['label'], plate=g['plate'],
                    samples=observed_samples, cell_line_id=g['cell_line_id'], full_qc_available=len(rows),
                    eligible_rows=rows, discovery_quota=16, holdout_quota=16,
                    holdout_relation="disjoint_cells_same_source_sample; not independent culture validation",
                    official_sample_join_verified=True, global_exposure_hours=24,
                    timing_scope="global v2 Methods provenance; no separate per-well timing measurements")
                groups.append(group)
                for row in rows:
                    a, b = int(ptr[row]), int(ptr[row+1])
                    jobs.append(dict(row=row, condition_id=group['condition_id'], indices=physical_spans(h5['X/indices'], a, b),
                                     values=physical_spans(h5['X/data'], a, b), nnz=b-a))
            layouts[file] = jobs
    metadata_bytes = sum(row.get("bytes", 0) for row in read_rows(HERE / "NETWORK.jsonl"))
    screen_bytes = sum(b-a+1 for jobs in layouts.values() for a,b in merge_adjacent([span for job in jobs for span in job['indices']]))
    max_values = sum(sum(sorted((job['nnz']*np.dtype(censuses[g['file']]['layouts']['X/data']['dtype']).itemsize
        for job in layouts[g['file']] if job['condition_id']==g['condition_id']), reverse=True)[:32]) for g in groups)
    hvg_bytes = len(groups)*32*8000
    projected = metadata_bytes + screen_bytes + max_values + hvg_bytes + 2_000_000
    if projected > CAP: raise RuntimeError("finite_stage_projected_response_cap_exceeded")
    write(HERE / "SOURCES.json", dict(schema="calibration_source_inputs_v1", inputs=records, census_seeds=seeds,
        gene_dictionaries=genes_by_file, code_arrays=codes, helper_original_sha256=sha(ROOT/'research/decision_value/observation_reliability/axis/audit.py')))
    write(HERE / "CENSUSES.json", censuses)
    write(HERE / "QC_ROWS.json", dict(schema="frozen_index_screen_full_QC_rows_v1", groups=groups,
        exclusions=exclusions, protected_rows_overlap=[], protected_samples_overlap=[], protected_labels_overlap=[]))
    write(HERE / "INDEX_LAYOUTS.json", layouts)
    network=read_rows(HERE/'NETWORK.jsonl')
    write(HERE/'METADATA_TIMING.json',dict(schema='calibration_metadata_timing_v1',
        current_attempt_elapsed_seconds=time.monotonic()-started,
        first_record_UTC=network[0].get('utc') if network else None,
        last_record_UTC=network[-1].get('utc') if network else None,
        body_bytes=metadata_bytes,not_a_model_speed_benchmark=True,
        restart_disclosed_in='METADATA_READ_AMENDMENT.json'))
    write(HERE / "PROTOCOL.json", dict(schema="two_stage_informative_axis_calibration_v1", source_repo="arcinstitute/State-Tahoe-Filtered",
        source_revision=REVISION, source_files=list(censuses), selected_conditions=len(groups), endpoint=endpoint,
        transform="log1p(stored normalized X) once; no additional normalization", absolute_tolerance=1e-5,
        discovery_min_nonzero=2, holdout_min_nonzero=1, quota_per_role_condition=16, max_paired_cells=256,
        metadata_preparation_body_bytes=metadata_bytes, planned_index_screen_bytes=screen_bytes,
        worst_case_selected_value_bytes=max_values, planned_HVG_bytes=hvg_bytes,
        reserved_future_metadata_and_fail_body_bytes=2_000_000, projected_total_response_bytes=projected,
        total_response_body_cap_bytes=CAP, index_screen_scope="CSR indices only for all frozen eligible calibration cells; expression-derived presence exposure",
        selection_rule="Reserve holdout index coverage with inverse-frequency exact rational greedy scoring and SHA256 ties, leaving two occurrences/gene for discovery; greedily cover discovery; fill quotas with hashes. Frozen screen.py defines complete semantics.",
        hash_seed="p05r-informative-cell-allocation-v1", summary_statistics_selection_is_outcome_guided=True,
        calendar_source_time="24h global protocol-time provenance from frozen SOURCE_QUALIFICATION input",
        final_acceptance="All39 unique discovery matches against all actual sourcegenes and informative holdout in EACH c44+c45; no shared order inference",
        checkpoint_axis_certified=False, full2000_axis_certified=False, P06_sentinel_RNA_read=False,
        agent_or_decision_effectiveness_test=False, production_promotion_allowed=False,
        runtime_stages=["metadata", "parent-reviewed index screen", "paired row freeze", "parent-reviewed raw values/HVG", "independent offline verification"]))
    for old, new in [('NETWORK.jsonl', 'METADATA_NETWORK.jsonl'), ('CACHE_REUSE.jsonl', 'METADATA_CACHE_REUSE.jsonl')]:
        (HERE/new).write_bytes((HERE/old).read_bytes() if (HERE/old).exists() else b'')
    files = [path for path in HERE.rglob('*') if path.is_file() and '__pycache__' not in path.parts and path.name not in ['INDEX_FREEZE.json','NETWORK.jsonl','CACHE_REUSE.jsonl']]
    write(HERE / "INDEX_FREEZE.json", dict(schema="index_presence_screen_freeze_v1", expression_values_and_HVG_read=False,
        sha256={path.relative_to(HERE).as_posix():sha(path) for path in sorted(files)}))
    print(json.dumps(dict(status="INDEX_FREEZE_READY_FOR_PARENT_REVIEW", metadata_bytes=metadata_bytes,
        index_screen_bytes=screen_bytes, worst_case_total_bytes=projected, full_QC_cells=sum(len(g['eligible_rows']) for g in groups))), flush=True)


if __name__ == "__main__":
    prepare()
